"""
Welele Story Forge™ — Collaborative Story Director (Gate 2.1)
The Story Reasoning LLM acts as the Conversational Director & Writers' Room Partner.
Responsibilities:
- Understand complete narrative context
- Absorb multi-fact responses holistically
- Propose/infer facts with explicit status distinction
- Recognize revisions/contradictions
- Decide what creative question matters next (grounded in dramatic stakes, not machine dependencies)
- Zero ontology leakage to creator.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from ..models import StoryState, CharacterRole, StateStatus, KnowledgeStatus, ConstraintStatus, StoryConstraint
from ..models.transition import StateMutation, MutationType
from .models import (
    FactStatus,
    ExtractedFact,
    RevisionRecord,
    CollaborativeReasoningOutput
)
from ..adapters.providers.base import LLMProvider, LLMInvalidOutputError
from ..adapters.providers.mock_provider import MockLLMProvider

logger = logging.getLogger("welele.story_forge.collaborative.director")

COLLABORATIVE_DIRECTOR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "llm_understanding": {
            "type": "string",
            "description": "Comprehensive narrative interpretation of what the creator communicated, subtext, and dramatic tension"
        },
        "extracted_facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["CHARACTER", "MOTIVATION", "SECRET", "FLAW", "RELATIONSHIP", "KNOWLEDGE", "EVENT", "STAKES", "OBSTACLE", "PLANT"]
                    },
                    "target_entity": {"type": "string"},
                    "statement": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["INFERRED", "PROPOSED", "CREATOR_CONFIRMED"]
                    },
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "raw_evidence": {"type": "string"}
                },
                "required": ["category", "target_entity", "statement", "status", "confidence"],
                "additionalProperties": False
            },
            "description": "All narrative facts extracted from the creator's input"
        },
        "proposed_mutations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "target_path": {"type": "string"},
                    "mutation_type": {"type": "string", "enum": ["CREATE", "UPDATE", "DELETE", "STATUS_CHANGE"]},
                    "new_value": {},
                    "rationale": {"type": "string"}
                },
                "required": ["target_path", "mutation_type", "new_value", "rationale"],
                "additionalProperties": False
            },
            "description": "Concrete state mutations proposed for Forge truth validation and commitment"
        },
        "revisions_detected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "entity_or_topic": {"type": "string"},
                    "previous_fact": {"type": "string"},
                    "revised_fact": {"type": "string"},
                    "revision_type": {
                        "type": "string",
                        "enum": ["FACTUAL_CONTRADICTION", "MATERIAL_STORY_DECISION"]
                    },
                    "material_consequences": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "reconciliation_action": {"type": "string"}
                },
                "required": ["entity_or_topic", "previous_fact", "revised_fact"],
                "additionalProperties": False
            },
            "description": "Detected revisions, factual contradictions, or material story decisions altering narrative trajectory"
        },
        "what_remains_unclear": {
            "type": "string",
            "description": "Genuinely missing dramatic/story elements needed for narrative depth (or empty/none if story is concluded)"
        },
        "why_it_matters_to_the_story": {
            "type": "string",
            "description": "The dramatic and screenwriting reason why the next question or conclusion is appropriate"
        },
        "conversational_action": {
            "type": "string",
            "enum": ["ASK_QUESTION", "CONCLUDE_STORY", "SYNTHESIZE_AND_CONTINUE"],
            "description": "The appropriate next conversational move based on semantic understanding of creator context. Use CONCLUDE_STORY if the creator declares an ending boundary. Not every turn requires a question."
        },
        "is_story_concluded": {
            "type": "boolean",
            "description": "True if the creator has bounded or completed the story arc, false otherwise"
        },
        "next_conversational_move": {
            "type": "string",
            "description": "Natural, evocative creative question for the creator ending with a single '?' if ASK_QUESTION; empty or concluding synthesis if CONCLUDE_STORY"
        }
    },
    "required": [
        "llm_understanding",
        "extracted_facts",
        "proposed_mutations",
        "revisions_detected",
        "what_remains_unclear",
        "why_it_matters_to_the_story",
        "conversational_action",
        "is_story_concluded",
        "next_conversational_move"
    ],
    "additionalProperties": False
}


class CollaborativeStoryDirector:
    """
    Directs the creative storytelling conversation in partnership with the human creator.
    """
    FORBIDDEN_ONTOLOGY_TERMS = [
        "counterforce",
        "dependency",
        "dependencies",
        "required state",
        "canon",
        "invariant",
        "invariants",
        "mutation",
        "mutations",
        "knowledge state",
        "chronology anchor",
        "chronology dependency",
        "deficiency",
        "deficiencies",
        "state version",
        "entity resolution"
    ]

    FORBIDDEN_THERAPEUTIC_PATTERNS = [
        "how do you feel",
        "how did you feel",
        "what do you feel",
        "what did you feel",
        "how does that make you feel",
        "as the creator, how do you feel",
        "as a writer, how do you feel",
        "how do you personally feel",
        "your personal feelings"
    ]

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        temperature: float = 0.3
    ):
        self.provider = provider or MockLLMProvider()
        self.temperature = temperature

    def evaluate(
        self,
        story_state: StoryState,
        creator_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        story_synopsis: Optional[str] = None
    ) -> CollaborativeReasoningOutput:
        """
        Processes creator input, absorbs all narrative facts, detects revisions,
        and determines the next natural storytelling inquiry.
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            story_state=story_state,
            creator_input=creator_input,
            conversation_history=conversation_history or [],
            story_synopsis=story_synopsis
        )

        try:
            raw_response = self.provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=COLLABORATIVE_DIRECTOR_SCHEMA,
                temperature=self.temperature
            )
        except Exception as e:
            logger.error(f"[CollaborativeDirector] Provider execution error: {str(e)}")
            raise

        return self._validate_and_build_output(raw_response, creator_input)

    def _build_system_prompt(self) -> str:
        return (
            "You are the Lead Story Reasoner and Writers' Room Partner in the Welele Story Forge™.\n"
            "You are an empathetic, sharp, and highly intelligent screenwriting collaborator.\n\n"
            "CONVERSATIONAL ACTION AUTHORITY:\n"
            "The architecture is:\n"
            "  CREATOR -> STORY REASONING LAYER -> [ASK | SYNTHESIZE | CONCLUDE] -> FORGE -> CANONICAL STATE\n"
            "- Story Reasoning is the authority on conversational intent.\n"
            "- Forge is the authority on story truth and canonical state integrity.\n"
            "- Every creator input produces exactly ONE semantically determined conversational outcome. A question is optional.\n"
            "- Forge may validate and reconcile the consequences of the conversational decision, but MUST NOT manufacture an investigative question when Story Reasoning has determined that no question is warranted.\n"
            "- Forge does not keep the conversation running merely because it still has things it could ask.\n\n"
            "THE THREE CONVERSATIONAL ACTIONS:\n"
            "1. 'ASK_QUESTION': Genuinely unresolved dramatic stakes or unexplored consequences require inquiry.\n"
            "   - Must be a focused screenwriting question targeting in-world choices, actions, obstacles, or consequences.\n"
            "   - PROHIBIT META-THERAPEUTIC FILLER: NEVER turn the creator into the subject of therapy or talk-show interviewing "
            "(e.g. NEVER ask 'How do you feel about what Sizwe said?' or 'What were your feelings when writing this?').\n"
            "2. 'SYNTHESIZE_AND_CONTINUE': The creator makes a material narrative choice or resolves a beat (e.g. 'He doesn't reveal himself').\n"
            "   - Reconcile consequences in state, summarize the fallout, and continue without interrogating if no question is warranted.\n"
            "   - A question is optional; do NOT force a question when the creator has given a definitive beat statement.\n"
            "3. 'CONCLUDE_STORY': The creator explicitly declares an ending or establishes a story boundary (e.g. 'Roll credits. Dark screen. The end.', 'That\\'s the end of the story.').\n"
            "   - Respect the boundary immediately. Set conversational_action = 'CONCLUDE_STORY', is_story_concluded = true, and next_conversational_move = null.\n"
            "   - Do NOT manufacture another scene. Do NOT ask another question.\n"
            "   - Even if Forge state has unresolved dependencies, Story Reasoning CLOSES the conversation. Forge records truth without overriding the creator's boundary.\n\n"
            "SEMANTIC UNDERSTANDING VS LEXICAL DETECTION:\n"
            "- In-Story Dialogue vs Creator Boundary:\n"
            "  * '\"Stop. This is the end,\" she said.' is IN-STORY CHARACTER DIALOGUE. It is NOT CONCLUDE_STORY. Do not stop the conversation.\n"
            "  * 'That\\'s the end of the story.' is a CREATOR BOUNDARY. Respect it. Stop the conversation.\n"
            "  * Lexical coincidence (words like 'stop', 'end', 'kill', 'leave', 'finish', 'goodbye' in character dialogue or plot events) must NEVER trigger a stop.\n\n"
            "PRIME DIRECTIVES FOR TRUTH & PRECEDENCE:\n"
            "- TRIPARTITE INFORMATION MODEL: Creator Canon (confirmed) vs. Reasonable Interpretation (inferred) vs. Speculative Proposals (conditional suggestions). Never invent canon silently.\n"
            "- STORY-VERSION PRECEDENCE: Later/stronger story decisions (e.g. seven-day reveal condition) supersede earlier drafts/notes (e.g. 30-day deadline). Never retrieve superseded conditions as active reality.\n"
            "- ENTITY & ATTRIBUTE GROUNDING: Character identities, genders, and pronouns in canonical state are invariant truth (e.g. Sizwe is male, 'he/him', never 'she').\n"
            "- ANTI-INVENTION LOCK: Never introduce ungrounded events, scenes, characters, or melodrama into your questions (e.g. no 'packed-club scene', 'ghost from his past', or 'death warrant').\n"
            "- ZERO ONTOLOGY LEAKAGE: Never use machine words: 'counterforce', 'dependency', 'canon', 'invariant', 'mutation', 'knowledge state', 'deficiency', 'schema'."
        )

    def _build_user_prompt(
        self,
        story_state: StoryState,
        creator_input: str,
        conversation_history: List[Dict[str, str]],
        story_synopsis: Optional[str]
    ) -> str:
        parts: List[str] = []
        parts.append("### STORY STATE & CONTEXT")
        parts.append(f"Title: {story_state.title}")
        if story_state.logline:
            parts.append(f"Logline: {story_state.logline}")
        if story_synopsis:
            parts.append(f"Original Creator Synopsis:\n{story_synopsis}")

        # Persistent Authoritative Document Context
        if getattr(story_state, "story_document_context", None):
            parts.append(f"\n### AUTHORITATIVE STORY DOCUMENT CONTEXT / TREATMENT NOTES\n{story_state.story_document_context.strip()}")

        if story_state.characters:
            parts.append("\n### ESTABLISHED CHARACTERS & CANONICAL ATTRIBUTES")
            for name, c in story_state.characters.items():
                gender_str = c.gender or (c.attributes.get("gender") if isinstance(c.attributes, dict) else None)
                pronoun_str = c.pronouns or (c.attributes.get("pronouns") if isinstance(c.attributes, dict) else None)
                identity_meta = []
                if gender_str:
                    identity_meta.append(f"Gender: {gender_str}")
                if pronoun_str:
                    identity_meta.append(f"Pronouns: {pronoun_str}")
                meta_suffix = f" [{', '.join(identity_meta)}]" if identity_meta else ""
                
                parts.append(f"- {name} (Role: {c.role.value if hasattr(c.role, 'value') else c.role}){meta_suffix}:")
                if c.aliases:
                    parts.append(f"  * Aliases: {', '.join(c.aliases)}")
                if c.summary:
                    parts.append(f"  * Summary: {c.summary}")
                if c.core_motivation:
                    parts.append(f"  * Motivation: {c.core_motivation}")
                if c.secret_desire:
                    parts.append(f"  * Secret Desire: {c.secret_desire}")
                if c.fatal_flaw:
                    parts.append(f"  * Flaw: {c.fatal_flaw}")
                if c.relationships:
                    for rel in c.relationships:
                        parts.append(f"  * Relationship with {rel.target_character}: {rel.relation_type} ({rel.dynamic or 'no dynamic noted'})")

        # Story Constraints & Version Precedence
        if getattr(story_state, "constraints", None):
            active_c = [c for c in story_state.constraints if c.status == ConstraintStatus.ACTIVE]
            superseded_c = [c for c in story_state.constraints if c.status == ConstraintStatus.SUPERSEDED]
            if active_c:
                parts.append("\n### ACTIVE STORY CONSTRAINTS & DEADLINES (CURRENT PRECEDENCE)")
                for c in active_c:
                    parts.append(f"- [{c.category}] {c.description} (ACTIVE - AUTHORITATIVE)")
            if superseded_c:
                parts.append("\n### SUPERSEDED HISTORICAL CONDITIONS (DO NOT CITE AS CURRENT REALITY)")
                for c in superseded_c:
                    parts.append(f"- [{c.category}] {c.description} (SUPERSEDED by later decision)")

        if story_state.knowledge_states:
            parts.append("\n### CHARACTER KNOWLEDGE STATES")
            for k in story_state.knowledge_states:
                parts.append(f"- {k.character_name} knows: {k.fact_key} (status: {k.status.value})")

        if conversation_history:
            parts.append("\n### RECENT CONVERSATION HISTORY")
            for turn in conversation_history[-4:]:
                parts.append(f"{turn.get('speaker', 'Creator')}: {turn.get('text', '')}")

        parts.append("\n### LATEST CREATOR INPUT")
        parts.append(f"\"{creator_input}\"")

        parts.append("\n### INSTRUCTIONS")
        parts.append(
            "1. Extract ALL factual statements, motivations, secrets, flaws, relationships, knowledge states, and events.\n"
            "2. Identify any revisions or material story decisions altering trajectory (record in `revisions_detected` with `revision_type` and `material_consequences`).\n"
            "3. Respect Story-Version Precedence: active later decisions take priority over superseded earlier notes.\n"
            "4. Ground all character pronouns and attributes in canonical character state (never drift or guess).\n"
            "5. Determine the conversational_action: 'ASK_QUESTION', 'SYNTHESIZE_AND_CONTINUE', or 'CONCLUDE_STORY'.\n"
            "   - If creator declared an ending boundary ('Roll credits. The end.' / 'That is the end of the story.'), choose 'CONCLUDE_STORY' and set next_conversational_move to null.\n"
            "   - If character is speaking in-story ('Stop. This is the end, she said.'), this is narrative dialogue, NOT an ending boundary.\n"
            "   - If a material choice is made ('Sizwe doesn't reveal himself'), choose 'SYNTHESIZE_AND_CONTINUE' and do NOT force a question.\n"
            "   - If a genuine unresolved dilemma requires creator choice, choose 'ASK_QUESTION' with a grounded question.\n"
            "   - NEVER ask meta-therapeutic questions ('How do you feel about what Sizwe said?').\n"
            "6. Formulate the conversational response according to conversational_action."
        )
        return "\n".join(parts)

    def _validate_and_build_output(
        self,
        raw_data: Dict[str, Any],
        creator_input: str
    ) -> CollaborativeReasoningOutput:
        # Validate extracted facts
        extracted_facts: List[ExtractedFact] = []
        for f in raw_data.get("extracted_facts", []):
            extracted_facts.append(
                ExtractedFact(
                    category=f.get("category", "CHARACTER"),
                    target_entity=f.get("target_entity", "Unknown"),
                    statement=f.get("statement", ""),
                    status=FactStatus(f.get("status", "INFERRED")),
                    confidence=float(f.get("confidence", 1.0)),
                    raw_evidence=f.get("raw_evidence", creator_input)
                )
            )

        # Validate mutations
        proposed_mutations: List[StateMutation] = []
        for m in raw_data.get("proposed_mutations", []):
            proposed_mutations.append(
                StateMutation(
                    target_path=m.get("target_path", ""),
                    mutation_type=MutationType(m.get("mutation_type", "UPDATE")),
                    new_value=m.get("new_value"),
                    rationale=m.get("rationale", "")
                )
            )

        # Validate revisions
        revisions: List[RevisionRecord] = []
        for r in raw_data.get("revisions_detected", []):
            revisions.append(
                RevisionRecord(
                    entity_or_topic=r.get("entity_or_topic", ""),
                    previous_fact=r.get("previous_fact", ""),
                    revised_fact=r.get("revised_fact", ""),
                    revision_type=r.get("revision_type", "FACTUAL_CONTRADICTION"),
                    material_consequences=r.get("material_consequences", []),
                    reconciliation_action=r.get("reconciliation_action", "REVISED_IN_STATE")
                )
            )

        # Validate conversational action and next question
        conv_action = raw_data.get("conversational_action", "ASK_QUESTION")
        is_concluded = bool(raw_data.get("is_story_concluded", False)) or (conv_action == "CONCLUDE_STORY")
        raw_next_move = raw_data.get("next_conversational_move")
        next_move: Optional[str] = None

        if is_concluded or conv_action == "CONCLUDE_STORY":
            conv_action = "CONCLUDE_STORY"
            is_concluded = True
            # For conclude, next question is explicitly None
            next_move = None
        elif conv_action == "SYNTHESIZE_AND_CONTINUE":
            # For synthesis, a question is optional
            if raw_next_move and raw_next_move.strip():
                clean_m = raw_next_move.strip()
                next_move = clean_m if clean_m.lower() not in ("none", "null", "") else None
        else:
            # ASK_QUESTION
            if raw_next_move and raw_next_move.strip():
                clean_m = raw_next_move.strip()
                if not clean_m.endswith("?"):
                    clean_m = clean_m + "?"
                next_move = clean_m

        if next_move:
            lower_q = next_move.lower()
            found_forbidden = [term for term in self.FORBIDDEN_ONTOLOGY_TERMS if term in lower_q]
            if found_forbidden:
                raise LLMInvalidOutputError(
                    message=f"Story-First Architectural Lock violation in next_conversational_move: contains forbidden terms {found_forbidden}",
                    provider=self.provider.provider_name if hasattr(self.provider, "provider_name") else "unknown",
                    model=self.provider.model_name if hasattr(self.provider, "model_name") else "unknown"
                )

            found_therapeutic = [term for term in self.FORBIDDEN_THERAPEUTIC_PATTERNS if term in lower_q]
            if found_therapeutic:
                raise LLMInvalidOutputError(
                    message=f"Meta-Therapeutic Trap violation in next_conversational_move: contains creator-directed therapeutic questioning {found_therapeutic}",
                    provider=self.provider.provider_name if hasattr(self.provider, "provider_name") else "unknown",
                    model=self.provider.model_name if hasattr(self.provider, "model_name") else "unknown"
                )

        return CollaborativeReasoningOutput(
            llm_understanding=raw_data.get("llm_understanding", ""),
            extracted_facts=extracted_facts,
            proposed_mutations=proposed_mutations,
            revisions_detected=revisions,
            what_remains_unclear=raw_data.get("what_remains_unclear", ""),
            why_it_matters_to_the_story=raw_data.get("why_it_matters_to_the_story", ""),
            conversational_action=conv_action,
            is_story_concluded=is_concluded,
            next_conversational_move=next_move
        )
