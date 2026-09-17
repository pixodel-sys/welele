"""
Welele Story Forge™ — LLM Reasoning Adapter v0.1
Intelligence boundary adapter connecting the Frozen Kernel to structured LLM reasoning.

Architectural Rule:
"The LLM is not Story Forge. The LLM is one replaceable reasoning component.
The durable asset is: Canonical Story State + Dependency Engine + Propagation +
Validation + Knowledge + Chronology + Trace + Completion Judge."

The LLM proposes. The Forge Kernel governs.
"""

from typing import Dict, Any, Optional, List
import time
import logging
import uuid
from pydantic import ValidationError

from .contracts import (
    ReasoningAdapter,
    ReasoningRequest,
    ReasoningDecision,
    ForgeObjective
)
from ..models import (
    SkillEnum,
    AuthorityMode,
    StateMutation,
    MutationType,
    ProductionDecision,
    ProductionAspect
)
from .providers.base import (
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMInvalidOutputError,
    ProviderErrorType
)
from .providers.mock_provider import MockLLMProvider

logger = logging.getLogger("welele.story_forge.llm_adapter")


# Standard JSON Schema for LLM Structured Output
REASONING_DECISION_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["ASK", "INFER", "PROPOSE", "RECORD_PRODUCTION_DECISION", "STOP"],
            "description": "Selected narrative authority action"
        },
        "dependency_id": {
            "type": ["string", "null"],
            "description": "Active dependency ID being addressed"
        },
        "skill": {
            "type": "string",
            "enum": [s.value for s in SkillEnum],
            "description": "Narrative reasoning skill invoked"
        },
        "question": {
            "type": ["string", "null"],
            "description": "Exactly ONE primary question if action is ASK; null otherwise"
        },
        "proposal": {
            "type": ["string", "null"],
            "description": "Creative proposal summary if action is PROPOSE or INFER; null otherwise"
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
            "description": "List of proposed state mutations (untrusted advice for Kernel validation)"
        },
        "production_decision": {
            "type": ["object", "null"],
            "properties": {
                "aspect": {"type": "string", "enum": [a.value for a in ProductionAspect]},
                "decision": {"type": "string"},
                "rationale": {"type": "string"},
                "constraint_flag": {"type": "boolean"}
            },
            "required": ["aspect", "decision", "rationale", "constraint_flag"],
            "additionalProperties": False,
            "description": "Production decision payload if action is RECORD_PRODUCTION_DECISION"
        },
        "rationale": {
            "type": "string",
            "description": "Justification for the chosen action and reasoning step"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Advisory confidence score (metadata only)"
        },
        "requires_creator": {
            "type": "boolean",
            "description": "True if action is ASK or PROPOSE; False for INFER, RECORD_PRODUCTION_DECISION, STOP"
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Explicit narrative assumptions made during reasoning"
        },
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Citations of established events, facts, or characters in current state"
        }
    },
    "required": [
        "action",
        "skill",
        "rationale",
        "confidence",
        "requires_creator",
        "assumptions",
        "evidence"
    ],
    "additionalProperties": False
}


class LLMReasoningAdapter(ReasoningAdapter):
    """
    LLM-powered reasoning adapter adhering to the ReasoningAdapter contract.
    Transforms ReasoningRequest into disciplined structured prompts and validates
    LLM output strictly into ReasoningDecision.
    """
    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        adapter_name: str = "LLMReasoningAdapter",
        adapter_version: str = "0.1.0",
        temperature: float = 0.2,
        timeout_seconds: float = 30.0
    ):
        self.provider = provider or MockLLMProvider()
        self.adapter_name = adapter_name
        self.adapter_version = adapter_version
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds

    def reason(self, request: ReasoningRequest) -> ReasoningDecision:
        """
        Execute one reasoning cycle given deliberate Kernel context.
        Raises LLMProviderError or ValueError on malformed/invalid output.
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(request)

        logger.info(
            f"[StoryForgeLLM] Starting reasoning cycle: request_id={request_id} story_id={request.story_id} "
            f"dep={request.active_dependency.dependency_key if request.active_dependency else 'NONE'} "
            f"provider={self.provider.provider_name} model={self.provider.model_name}"
        )

        # Allow self-correcting retry loop for live LLM providers
        max_attempts = 2 if not type(self.provider).__name__ == "MockLLMProvider" else 1
        current_user_prompt = user_prompt
        last_exception = None

        for attempt in range(max_attempts):
            try:
                raw_response_dict = self.provider.generate_structured(
                    system_prompt=system_prompt,
                    user_prompt=current_user_prompt,
                    response_schema=REASONING_DECISION_JSON_SCHEMA,
                    temperature=self.temperature,
                    timeout_seconds=self.timeout_seconds
                )
            except LLMProviderError as pe:
                logger.error(f"[StoryForgeLLM] Provider error in request_id={request_id}: {pe.message}")
                raise

            latency_ms = round((time.time() - start_time) * 1000, 2)

            try:
                # Validate structured decision
                decision = self._validate_and_build_decision(
                    raw_data=raw_response_dict,
                    request=request,
                    latency_ms=latency_ms,
                    request_id=request_id
                )
                logger.info(
                    f"[StoryForgeLLM] Reasoning cycle complete: request_id={request_id} action={decision.action.value} "
                    f"skill={decision.skill.value} requires_creator={decision.requires_creator} latency={latency_ms}ms"
                )
                return decision
            except LLMInvalidOutputError as val_err:
                last_exception = val_err
                if attempt < max_attempts - 1:
                    logger.warning(f"[StoryForgeLLM] Decision validation failed (attempt {attempt+1}): {val_err.message}. Retrying with correction.")
                    current_user_prompt = (
                        f"{user_prompt}\n\n"
                        f"[CRITICAL CORRECTION REQUIRED]: Your previous output was rejected with error: {val_err.message}. "
                        "Ensure you output strictly compliant JSON with exactly ONE question mark if choosing ASK."
                    )
                    continue
                raise

        if last_exception:
            raise last_exception

    def _build_system_prompt(self) -> str:
        return (
            "You are the Welele Story Forge™ Intelligence Component.\n"
            "You provide narrative reasoning to the Forge Kernel without owning canonical state, persistence, or validation.\n\n"
            "CRITICAL ARCHITECTURAL CONSTRAINTS:\n"
            "1. You do not own canonical story state. The Kernel validates, propagates, and commits all state.\n"
            "2. The Kernel provides ONLY deliberate context slices. Do NOT assume facts not in the context.\n"
            "3. You must select EXACTLY ONE action from:\n"
            "   - ASK: Formulate exactly ONE concise question for the human creator ending with a single '?'. `requires_creator = true`. No state mutations.\n"
            "   - INFER: Safe deduction from established evidence. `requires_creator = false`. Propose state mutations.\n"
            "   - PROPOSE: Creative proposal requiring creator approval. `requires_creator = true`.\n"
            "   - RECORD_PRODUCTION_DECISION: Concrete production/filming choice. `requires_creator = false`. Requires production_decision payload.\n"
            "   - STOP: Recommend stopping development cycle. `requires_creator = false`. `question = null`.\n"
            "4. Never include multiple questions or numbered lists when choosing ASK. The question string must contain exactly ONE single question mark '?'.\n"
            "5. The Completion Judge remains sole authority on Forge completion. You may recommend STOP, not declare completion.\n"
            "6. Return ONLY a valid JSON object strictly conforming to the requested schema."
        )

    def _build_user_prompt(self, request: ReasoningRequest) -> str:
        parts: List[str] = []

        # 1. Story Material
        st = request.story_context
        parts.append("### 1. STORY CONTEXT")
        parts.append(f"- Title: {st.title}")
        if st.logline:
            parts.append(f"- Logline: {st.logline}")
        if st.theme:
            parts.append(f"- Theme: {st.theme}")
        if st.tone:
            parts.append(f"- Tone: {st.tone}")
        parts.append(f"- Objective: {request.objective.value}")
        parts.append(f"- Canonical State Version: v{request.state_version}")

        # 2. Active Dependency
        dep = request.active_dependency
        parts.append("\n### 2. ACTIVE DEPENDENCY")
        if dep:
            parts.append(f"- Dependency ID: {dep.id}")
            parts.append(f"- Key: {dep.dependency_key}")
            parts.append(f"- Type: {dep.dependency_type}")
            parts.append(f"- Target Entity: {dep.target_entity}")
            parts.append(f"- Description: {dep.description}")
            parts.append(f"- Priority Score: {dep.priority_score}")
            parts.append(f"- Suggested Skill: {dep.suggested_skill}")
        else:
            parts.append("- None (No unresolved dependencies)")

        # 3. Relevant Entities / Characters
        if request.relevant_entities:
            parts.append("\n### 3. RELEVANT CHARACTERS")
            for ent in request.relevant_entities:
                parts.append(f"- {ent.name} ({ent.role}, Status: {ent.status}):")
                if ent.core_motivation:
                    parts.append(f"  * Motivation: {ent.core_motivation}")
                if ent.secret_desire:
                    parts.append(f"  * Secret Desire: {ent.secret_desire}")
                if ent.fatal_flaw:
                    parts.append(f"  * Fatal Flaw: {ent.fatal_flaw}")
                if ent.relationships:
                    parts.append(f"  * Relationships: {ent.relationships}")

        # 4. Relevant Chronology Events
        if request.relevant_events:
            parts.append("\n### 4. RELEVANT CHRONOLOGY EVENTS")
            for ev in request.relevant_events:
                parts.append(f"- Event #{ev.event_sequence} [{ev.story_time or 'TBD'}]: {ev.headline} — {ev.description}")

        # 5. Relevant Knowledge States
        if request.relevant_knowledge:
            parts.append("\n### 5. RELEVANT KNOWLEDGE STATES")
            for kn in request.relevant_knowledge:
                parts.append(f"- {kn.character_name} -> {kn.fact_key} (Status: {kn.status})")

        # 6. Relevant Narrative Plants
        if request.relevant_plants:
            parts.append("\n### 6. RELEVANT NARRATIVE PLANTS")
            for pl in request.relevant_plants:
                parts.append(f"- Plant [{pl.element_code}]: {pl.description} (Intended Payoff: {pl.intended_payoff}, Status: {pl.payoff_status})")

        # 7. Creator Input / Response
        if request.creator_response:
            parts.append("\n### 7. LATEST CREATOR RESPONSE")
            parts.append(f"Creator says: \"{request.creator_response}\"")
        elif request.creator_input:
            parts.append("\n### 7. INITIAL CREATOR INPUT")
            parts.append(f"Input: \"{request.creator_input}\"")

        parts.append("\n### 8. INSTRUCTION")
        parts.append(
            "Analyze the active dependency against the established canonical state and return your structured reasoning decision.\n"
            "- Character Mutations: Use canonical character name as target path (e.g. 'characters.CharacterName') with 'name' and 'role' fields.\n"
            "- Creator Response Handling: If the creator response resolves the active dependency, use INFER to commit state changes. If it provides contextual lore without resolving the specific dramatic requirement, use ASK to formulate a focused clarifying question offering clear options based on the newly supplied context."
        )

        return "\n".join(parts)

    def _validate_and_build_decision(
        self,
        raw_data: Dict[str, Any],
        request: ReasoningRequest,
        latency_ms: float,
        request_id: str
    ) -> ReasoningDecision:
        """
        Validates raw dictionary into a strictly conforming ReasoningDecision.
        Enforces one-question semantics and provenance.
        """
        # Parse mutations
        mutations_raw = raw_data.get("proposed_mutations") or []
        parsed_mutations: List[StateMutation] = []
        for m in mutations_raw:
            try:
                parsed_mutations.append(
                    StateMutation(
                        target_path=m["target_path"],
                        mutation_type=MutationType(m["mutation_type"]),
                        new_value=m["new_value"],
                        rationale=m["rationale"]
                    )
                )
            except Exception as me:
                raise LLMInvalidOutputError(
                    message=f"Invalid proposed mutation structure: {str(me)}",
                    provider=self.provider.provider_name,
                    model=self.provider.model_name
                )

        # Parse production decision
        prod_dec_raw = raw_data.get("production_decision")
        parsed_prod_dec: Optional[ProductionDecision] = None
        if prod_dec_raw:
            try:
                aspect_val = prod_dec_raw.get("production_aspect") or prod_dec_raw.get("aspect")
                parsed_prod_dec = ProductionDecision(
                    story_id=request.story_id,
                    decision_key=prod_dec_raw.get("decision_key") or f"DEC_{aspect_val}_{request_id}",
                    narrative_resolution=prod_dec_raw.get("narrative_resolution") or prod_dec_raw.get("decision", ""),
                    production_aspect=ProductionAspect(aspect_val),
                    deferred_details=prod_dec_raw.get("deferred_details") or prod_dec_raw.get("rationale", "")
                )
            except Exception as pe:
                raise LLMInvalidOutputError(
                    message=f"Invalid production decision structure: {str(pe)}",
                    provider=self.provider.provider_name,
                    model=self.provider.model_name
                )

        # Action and Skill enum parsing
        try:
            action = AuthorityMode(raw_data.get("action"))
        except (ValueError, TypeError):
            raise LLMInvalidOutputError(
                message=f"Unknown or invalid action: '{raw_data.get('action')}'",
                provider=self.provider.provider_name,
                model=self.provider.model_name
            )

        try:
            skill = SkillEnum(raw_data.get("skill"))
        except (ValueError, TypeError):
            raise LLMInvalidOutputError(
                message=f"Unknown or invalid skill: '{raw_data.get('skill')}'",
                provider=self.provider.provider_name,
                model=self.provider.model_name
            )

        question = raw_data.get("question")
        # Semantic check: Disallow multiple questions in ASK
        if action == AuthorityMode.ASK and question:
            # Count question marks or numbered sub-questions
            q_count = question.count("?")
            if q_count > 1 or "\n1." in question or "\n-" in question:
                raise LLMInvalidOutputError(
                    message=f"ASK action must contain exactly one question, found {q_count} or multiple list items: '{question}'",
                    provider=self.provider.provider_name,
                    model=self.provider.model_name
                )

        # Semantic check: Disallow committed mutations during ASK
        if action == AuthorityMode.ASK and parsed_mutations:
            raise LLMInvalidOutputError(
                message="ASK action cannot commit or propose state mutations before receiving creator response.",
                provider=self.provider.provider_name,
                model=self.provider.model_name
            )

        try:
            decision = ReasoningDecision(
                action=action,
                dependency_id=raw_data.get("dependency_id") or (request.active_dependency.id if request.active_dependency else None),
                skill=skill,
                question=question,
                proposal=raw_data.get("proposal"),
                proposed_mutations=parsed_mutations,
                production_decision=parsed_prod_dec,
                rationale=raw_data.get("rationale", ""),
                confidence=float(raw_data.get("confidence", 1.0)),
                requires_creator=bool(raw_data.get("requires_creator", False)),
                assumptions=list(raw_data.get("assumptions", [])),
                evidence=list(raw_data.get("evidence", [])),
                adapter_name=self.adapter_name,
                adapter_version=self.adapter_version
            )
        except ValidationError as ve:
            raise LLMInvalidOutputError(
                message=f"ReasoningDecision semantic schema violation: {str(ve)}",
                provider=self.provider.provider_name,
                model=self.provider.model_name
            )

        return decision
