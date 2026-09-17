"""
Welele Story Forge™ — Excavator Narrative Information Extraction Engine
Locks Enforced:
- LOCK 1: Natural narrative is first-class input and may satisfy multiple requirements in one response.
- LOCK 4: Narrative extraction does not equal canon (EXTRACT -> PROPOSE -> RECONCILE -> VALIDATE -> COMMIT).
- LOCK 6: Explicit endings are first-class information.
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from uuid import uuid4

from ..models.state import StoryState, CharacterState, CharacterRole, StateStatus
from ..models.transition import StateMutation, MutationType
from ..models.events import ChronologyEvent
from .entity_registry import EntityRegistry, ResolutionOutcome


class NarrativeExtractionResult:
    def __init__(
        self,
        raw_input: str,
        proposed_mutations: List[StateMutation],
        proposed_events: List[ChronologyEvent],
        explicit_ending_detected: bool = False,
        ending_text: Optional[str] = None,
        extracted_character_names: Optional[List[str]] = None,
        ambiguities: Optional[List[str]] = None
    ):
        self.raw_input = raw_input
        self.proposed_mutations = proposed_mutations
        self.proposed_events = proposed_events
        self.explicit_ending_detected = explicit_ending_detected
        self.ending_text = ending_text
        self.extracted_character_names = extracted_character_names or []
        self.ambiguities = ambiguities or []


class NarrativeExtractor:
    """
    The Excavator narrative interpretation component.
    Extracts narrative facts, candidate entities, relationships, motivations,
    temporal beats, outcomes and explicit termination signals from natural creator text.
    """

    EXPLICIT_ENDING_PATTERNS = [
        r"\b(?:that\s+is|that's|this\s+is)\s+(?:the\s+)?end\b",
        r"\bthe\s+end\.?$",
        r"\b(?:story\s+)?concludes?\b",
        r"\b(?:that\s+)?concludes\s+the\s+story\b",
        r"\bnothing(?:\s+more)?\s*[,.]\s*that['’]?s\s+the\s+ending\b",
        r"\bthe\s+story\s+reaches\s+its\s+final\s+conclusion\b",
        r"\bpermanently\s+settled\b"
    ]

    CHRONOLOGY_MARKERS = [
        # (Anchor Type, Regex pattern, Default description label)
        ("INCITING_DISRUPTION", r"\b(?:destroys?|disrupts?|kills?|dies?|murdered|discovers?|finds?|arrives?|stumbles?|fired|evicted)\b", "Inciting Disruption"),
        ("POINT_OF_NO_RETURN", r"\b(?:leaves?|departs?|travels?|crosses?|enters?|commits?|decides?|vows?|escapes?)\b", "Point of No Return"),
        ("MIDPOINT_REVELATION", r"\b(?:struggles?|discovers?|reveals?|uncovers?|confronts?|betrays?|twist|secret)\b", "Midpoint Shift"),
        ("DARK_NIGHT", r"\b(?:cornered|hopeless|fails?|loses?|trapped|abandoned|grief|ruin|rock\s+bottom)\b", "Dark Night / Low Point"),
        ("CLIMAX", r"\b(?:reunites?|showdown|confrontation|battle|stands?|sacrifices?|dies?|final\s+confrontation)\b", "Climax Confrontation"),
        ("RESOLUTION", r"\b(?:peace|happy|settles?|reconciles?|rebuilt|saved|returns?|new\s+beginning|resolution)\b", "Dramatic Resolution")
    ]

    @classmethod
    def detect_explicit_ending(cls, text: str) -> Tuple[bool, Optional[str]]:
        """Detects whether creator explicitly indicated story termination."""
        for pat in cls.EXPLICIT_ENDING_PATTERNS:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return True, match.group(0)
        return False, None

    @classmethod
    def split_into_narrative_sentences(cls, text: str) -> List[str]:
        """Splits natural paragraph into narrative sentences, filtering out pure meta-commentary."""
        raw_sentences = re.split(r'[.!?]+\s*', text)
        clean = []
        for s in raw_sentences:
            s_str = s.strip()
            if not s_str:
                continue
            # Filter meta chatter like "That is the end" or "I just told you the whole story"
            is_pure_meta = any(re.search(pat, s_str, re.IGNORECASE) for pat in [
                r"^(?:that\s+is|that's)\s+(?:the\s+)?end$",
                r"^i\s+just\s+told\s+you",
                r"^nothing\s*$"
            ])
            if not is_pure_meta:
                clean.append(s_str)
        return clean

    @classmethod
    def extract(
        cls,
        text: str,
        current_state: StoryState,
        existing_events_count: int = 0
    ) -> NarrativeExtractionResult:
        """
        Extracts narrative proposals from natural creator response.
        Proposes mutations and events without directly committing to canonical state.
        """
        proposed_mutations: List[StateMutation] = []
        proposed_events: List[ChronologyEvent] = []
        extracted_names: List[str] = []
        ambiguities: List[str] = []

        is_ending, ending_match = cls.detect_explicit_ending(text)
        sentences = cls.split_into_narrative_sentences(text)

        # ---------------------------------------------------------------------
        # 1. Entity & Character Extraction
        # ---------------------------------------------------------------------
        # Extract potential character tokens (capitalized nouns, core kinship/roles)
        role_indicators = [
            ("mother", CharacterRole.PROTAGONIST, "Protect family and secure livelihood"),
            ("father", CharacterRole.PROTAGONIST, "Protect family and legacy"),
            ("protagonist", CharacterRole.PROTAGONIST, "Overcome central story obstacle"),
            ("family", CharacterRole.SUPPORTING, "Survive and stay united"),
            ("creditor", CharacterRole.ANTAGONIST, "Demand unpayable debt"),
            ("rival", CharacterRole.ANTAGONIST, "Defeat protagonist and claim domain"),
            ("boss", CharacterRole.ANTAGONIST, "Enforce corporate compliance"),
            ("sister", CharacterRole.CONFIDANT, "Support protagonist"),
            ("brother", CharacterRole.CONFIDANT, "Support protagonist")
        ]

        text_lower = text.lower()

        # Check if lead character exists or needs definition
        has_protagonist = any(c.role == CharacterRole.PROTAGONIST for c in current_state.characters.values())

        for indicator, default_role, default_mot in role_indicators:
            pattern = r'\b' + re.escape(indicator) + r's?\b'
            if re.search(pattern, text_lower):
                char_name = indicator.capitalize()

                # If entity already exists, resolve canonically
                res = EntityRegistry.resolve_entity(current_state, char_name, role_hint=default_role)

                if res.outcome == ResolutionOutcome.AMBIGUOUS:
                    ambiguities.append(res.ambiguity_reason or f"Ambiguous reference to {char_name}")
                elif res.outcome == ResolutionOutcome.NEW:
                    # Propose new character creation
                    extracted_names.append(char_name)
                    role_to_assign = default_role
                    if default_role == CharacterRole.PROTAGONIST and has_protagonist:
                        role_to_assign = CharacterRole.SUPPORTING

                    # Derive context motivation if sentence provides one
                    derived_mot = default_mot
                    for s in sentences:
                        if indicator in s.lower():
                            derived_mot = s.strip()
                            break

                    proposed_mutations.append(
                        StateMutation(
                            target_path=f"characters.{char_name}",
                            mutation_type=MutationType.CREATE,
                            new_value={
                                "character_id": str(uuid4()),
                                "name": char_name,
                                "role": role_to_assign.value,
                                "status": StateStatus.FACT.value,
                                "core_motivation": derived_mot,
                                "fatal_flaw": "Vulnerability revealed under extreme pressure"
                            },
                            rationale=f"Extracted from creator response: '{indicator}' in story context"
                        )
                    )
                elif res.outcome == ResolutionOutcome.MATCH and res.character:
                    # If motivation is missing, update it
                    if not res.character.core_motivation:
                        for s in sentences:
                            if indicator in s.lower():
                                proposed_mutations.append(
                                    StateMutation(
                                        target_path=f"characters.{res.character_key}.core_motivation",
                                        mutation_type=MutationType.UPDATE,
                                        new_value=s.strip(),
                                        rationale="Extracted core motivation from creator narrative"
                                    )
                                )
                                break

        # Check candidate proper nouns and named tokens against existing canonical characters (LOCK 2 & LOCK 3)
        common_stop_words = {
            "the", "then", "there", "their", "eventually", "despite", "that", "this",
            "when", "after", "before", "if", "because", "although", "while", "and", "but",
            "however", "meanwhile", "soon", "later", "suddenly", "finally", "once",
            "since", "every", "everyone", "nothing", "something", "everything", "leaves",
            "struggles", "destroys", "reunite", "dies", "confronts", "refuses"
        }
        tokens = re.findall(r'\b[A-Za-z]{3,}\b', text)
        for tok in tokens:
            if tok.lower() in common_stop_words:
                continue
            if current_state.characters:
                res = EntityRegistry.resolve_entity(current_state, tok)
                if res.outcome == ResolutionOutcome.AMBIGUOUS:
                    reason = res.ambiguity_reason or f"Ambiguous reference to '{tok}'"
                    if reason not in ambiguities:
                        ambiguities.append(reason)

        # ---------------------------------------------------------------------
        # 2. Chronology Anchor & Event Extraction
        # ---------------------------------------------------------------------
        # Convert narrative sentences into chronological anchors
        seq = existing_events_count + 1

        for sentence in sentences:
            s_clean = sentence.strip()
            if len(s_clean) < 10:
                continue

            # Determine best anchor type match
            matched_anchor = "EVENT_PROGRESSION"
            for anchor_type, pattern, _ in cls.CHRONOLOGY_MARKERS:
                if re.search(pattern, s_clean, re.IGNORECASE):
                    matched_anchor = anchor_type
                    break

            # If explicit ending was declared in/around this sentence
            if is_ending and (sentence == sentences[-1] or "happy" in s_clean.lower() or "peace" in s_clean.lower() or "dies" in s_clean.lower()):
                matched_anchor = "RESOLUTION"

            headline = s_clean[:60] + ("..." if len(s_clean) > 60 else "")
            proposed_events.append(
                ChronologyEvent(
                    event_id=str(uuid4()),
                    story_id=current_state.story_id,
                    state_version=current_state.state_version + 1,
                    event_sequence=seq,
                    anchor_type=matched_anchor,
                    headline=headline,
                    description=s_clean,
                    event_status=StateStatus.FACT
                )
            )
            seq += 1

        # ---------------------------------------------------------------------
        # 3. Explicit Ending Anchor if ending was declared
        # ---------------------------------------------------------------------
        if is_ending:
            # Propose explicit ending flag in StoryState
            proposed_mutations.append(
                StateMutation(
                    target_path="explicit_ending_declared",
                    mutation_type=MutationType.UPDATE,
                    new_value=True,
                    rationale="Creator explicitly declared story ending"
                )
            )

        return NarrativeExtractionResult(
            raw_input=text,
            proposed_mutations=proposed_mutations,
            proposed_events=proposed_events,
            explicit_ending_detected=is_ending,
            ending_text=ending_match,
            extracted_character_names=extracted_names,
            ambiguities=ambiguities
        )
