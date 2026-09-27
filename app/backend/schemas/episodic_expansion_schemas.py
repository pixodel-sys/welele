"""
Welele Media™ — Episodic Expansion & Living State Contracts
Defines the authoritative boundary between:
CANON → EPISODIC STATE → EPISODE DELTA → PRODUCTION PACK

Invariants:
1. Strict Provenance: CANON, DERIVED, PROPOSED, EPISODIC_FACT, PRODUCTION_DECISION.
2. Narrative Independence: Narrative expansion handles dramatic units; production handles physical timing (e.g. 90s).
3. Zero Silent Mutation: Episodic events cannot mutate macro Story Forge Canon.
4. Living Character Knowledge: Characters can only act upon what they have witnessed or been told.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
import hashlib
import json


class EpisodicProvenance(str, Enum):
    CANON = "CANON"                          # Established directly in Story Forge Bible
    DERIVED = "DERIVED"                      # Logically inferred from canon rules/lore
    PROPOSED = "PROPOSED"                    # Creative candidate under consideration
    EPISODIC_FACT = "EPISODIC_FACT"          # Event occurred in previous episode; true for future episodes, never retroactively alters Forge Canon
    PRODUCTION_DECISION = "PRODUCTION_DECISION"  # Framing, camera, lighting, sound design choices


class NarrativeBeat(BaseModel):
    """Format-agnostic dramatic story beat."""
    beat_id: str
    headline: str
    dramatic_action: str
    characters_present: List[str]
    location: str
    conflict_type: str                       # e.g., 'INTERPERSONAL', 'STATUS_INVERSION', 'REVELATION', 'TACTICAL'
    knowledge_revealed: Dict[str, List[str]] = Field(default_factory=dict, description="Character -> list of newly learned facts")
    plants_referenced: List[str] = Field(default_factory=list)
    new_plants_established: List[str] = Field(default_factory=list)
    stakes_delta: str
    provenance: EpisodicProvenance = Field(default=EpisodicProvenance.DERIVED)


class CharacterKnowledgeSnapshot(BaseModel):
    """Exact inventory of what a character knows at a given episode boundary."""
    character_name: str
    known_facts: List[str] = Field(default_factory=list)
    secrets_held: List[str] = Field(default_factory=list)
    current_emotional_state: str = Field(default="Composed")
    current_objective: str = Field(default="Protect family interest")
    provenance: EpisodicProvenance = Field(default=EpisodicProvenance.EPISODIC_FACT)


class EpisodicDelta(BaseModel):
    """Material changes enacted by an episode upon the story universe."""
    episode_number: int
    unresolved_cliffhanger: str
    immediate_consequences: List[str] = Field(default_factory=list)
    new_knowledge_distribution: Dict[str, List[str]] = Field(default_factory=dict)
    relationship_shifts: List[Dict[str, str]] = Field(default_factory=list) # e.g. [{"source": "Bhekisisa", "target": "Nandi", "new_dynamic": "Terrified suspicion"}]
    guest_characters_introduced: List[Dict[str, Any]] = Field(default_factory=list)
    new_plants_staged: List[str] = Field(default_factory=list)
    plants_cashed_out: List[str] = Field(default_factory=list)
    provenance: EpisodicProvenance = Field(default=EpisodicProvenance.EPISODIC_FACT)


class EpisodicStateSnapshot(BaseModel):
    """The living world state at a specific episode boundary (before Episode N begins)."""
    story_id: str
    episode_number: int
    canon_lineage_hash: str
    cumulative_state_hash: str
    character_states: Dict[str, CharacterKnowledgeSnapshot] = Field(default_factory=dict)
    active_unresolved_plants: List[str] = Field(default_factory=list)
    current_social_arena_state: str
    previous_episode_cliffhanger: Optional[str] = None
    historical_deltas: List[EpisodicDelta] = Field(default_factory=list)
    is_story_resolved: bool = Field(default=False, description="True when the central macro conflict reaches definitive resolution")
    resolution_rationale: Optional[str] = Field(default=None, description="Detailed explanation of why the story concluded naturally")


class EpisodeContract(BaseModel):
    """
    Authoritative Contract for an expanded episode.
    Covers narrative, state delta, continuity, production and provenance.
    """
    story_id: str
    episode_number: int
    title: str
    logline: str
    opening_hook: str
    midpoint_escalation: str
    closing_cliffhanger: str
    beats: List[NarrativeBeat]
    state_delta: EpisodicDelta
    upstream_state_hash: str
    resulting_state_hash: str
    provenance_audit: Dict[str, EpisodicProvenance]
    ai_readiness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_series_climax_or_resolution: bool = Field(default=False)
    resolution_justification: Optional[str] = None

