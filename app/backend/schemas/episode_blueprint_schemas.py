"""
Welele Media™ — Episode Blueprint Canonical Schemas (Phase 2 Downstream Planning Layer)
Authoritative flow: Digital IP → Story Package (M3) → Series → Episode → Episode Blueprint.

Core Invariants:
  1. Executable dramatic projection of an Episode; does NOT create new Story State canon.
  2. Inherits CANON via references; explicit DERIVED dramatic structure, PROPOSED elements, PRODUCTION DECISIONS.
  3. Strict sparse-input honesty: Missing data is explicitly UNKNOWN / NOT_SPECIFIED.
  4. Unique artifact_lineage_hash separate from upstream source_lineage_hash.
  5. Never duplicates Character Bible or lore; maintains reference integrity.
"""

from enum import Enum
import hashlib
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BlueprintProvenance(str, Enum):
    CANON = "CANON"
    DERIVED = "DERIVED"
    PROPOSED = "PROPOSED"
    PRODUCTION_DECISION = "PRODUCTION_DECISION"
    UNKNOWN = "UNKNOWN"



class BlueprintStatus(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class BeatType(str, Enum):
    HOOK = "HOOK"
    SETUP = "SETUP"
    ESCALATION = "ESCALATION"
    CONFLICT = "CONFLICT"
    REVELATION = "REVELATION"
    EMOTIONAL_MOVEMENT = "EMOTIONAL_MOVEMENT"
    CLIMAX = "CLIMAX"
    CLIFFHANGER = "CLIFFHANGER"
    NEXT_EPISODE_SETUP = "NEXT_EPISODE_SETUP"


class BlueprintDramaticObjective(BaseModel):
    """Dramatic goal, counterforce, dramatic question, and stakes for this episode."""
    episode_objective: str = Field(description="Primary overarching dramatic objective of the episode")
    protagonist_objective: str = Field(description="Active goal pursued by the central protagonist")
    opposing_objective: str = Field(description="Counter-goal pursued by opposing force/antagonist")
    dramatic_question: str = Field(description="Core dramatic question driving audience engagement")
    stakes: str = Field(description="What is lost if protagonist fails in this episode")
    ending_state: str = Field(description="Dramatic outcome state at end of episode")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.DERIVED)
    source_path: str = Field(default="story_package.thematic_premise")


class BlueprintCharacterArc(BaseModel):
    """Episode-specific character trajectory referencing canonical character without duplicating lore."""
    character_id_ref: Optional[str] = Field(default=None, description="Canonical character ID reference in Character Bible")
    character_name_ref: str = Field(description="Name of the character")
    role_in_episode: str = Field(description="Role in this episode: Protagonist, Antagonist, Catalyst, Confidant")
    objective: str = Field(description="Character's specific objective in this episode")
    knowledge_state: str = Field(description="What this character knows / does not know entering this episode")
    emotional_state_at_start: str = Field(description="Emotional baseline at episode beginning")
    emotional_movement: str = Field(description="Emotional shift across the episode")
    state_change: str = Field(description="Tangible state change by episode close")
    relationships_affected: List[str] = Field(default_factory=list, description="Relationships shifted or strained")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.DERIVED)


class BlueprintBeat(BaseModel):
    """Single dramatic beat in the executable 9-beat microdrama structure."""
    beat_id: str = Field(description="Unique beat identifier, e.g. beat_ep1_01")
    sequence: int = Field(ge=1, le=20, description="Sequential ordering 1-9+")
    beat_type: BeatType = Field(description="Dramatic category of the beat")
    purpose: str = Field(description="Why this beat exists in the dramatic economy")
    narrative_action: str = Field(description="What actually happens on screen")
    participating_characters: List[str] = Field(default_factory=list, description="Characters involved in this beat")
    location_ref: str = Field(default="UNKNOWN", description="Canonical location reference or UNKNOWN")
    timing_start_seconds: Optional[int] = Field(default=None, description="Start timestamp in seconds")
    timing_end_seconds: Optional[int] = Field(default=None, description="End timestamp in seconds")
    continuity_dependencies: List[str] = Field(default_factory=list, description="Prior events/plants required")
    state_changes: List[str] = Field(default_factory=list, description="Story/character state mutations caused by beat")
    downstream_production_implications: List[str] = Field(default_factory=list, description="Specific set, lighting, props implications")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.DERIVED)
    source_path: str = Field(default="story_package.beats")


class BlueprintHook(BaseModel):
    """Opening hook mechanism capturing viewer attention in first 5-15 seconds."""
    narrative_event: str = Field(description="Opening incident / visual shock / crisis")
    attention_mechanism: str = Field(description="Why this captures viewer curiosity/empathy in vertical feed")
    timing_seconds: int = Field(default=15, description="Hook duration / window in seconds")
    participating_characters: List[str] = Field(default_factory=list)
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.CANON)
    source_path: str = Field(default="story_package.beats[0]")


class BlueprintCliffhanger(BaseModel):
    """Closing cliffhanger mechanism driving paywall conversion / next-episode transition."""
    narrative_event: str = Field(description="The unresolved climax / revelation triggering the cliffhanger")
    unresolved_question: str = Field(description="Specific high-stakes question left hanging")
    consequence: str = Field(description="Immediate catastrophic/transformative consequence pending")
    affected_characters: List[str] = Field(default_factory=list)
    timing_seconds: int = Field(default=88, description="Timestamp where cliffhanger triggers")
    next_episode_dependency: str = Field(description="Narrative hook carried into next episode")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.CANON)
    source_path: str = Field(default="story_package.beats[-1]")


class BlueprintEmotionalTrajectory(BaseModel):
    """Explicit emotional trajectory proving dramatic change across the episode."""
    starting_state: str = Field(description="Initial emotional state of protagonist/ensemble")
    pressure_context: str = Field(description="External or internal pressure forcing action")
    escalation_point: str = Field(description="Point where stakes escalate beyond return")
    emotional_turn_trigger: str = Field(description="Specific catalyst triggering the emotional shift")
    emotional_shift: str = Field(description="Movement from start emotion to end emotion")
    resulting_behavior: str = Field(description="New behavior or decision resulting from shift")
    ending_state: str = Field(description="Final emotional posture heading into next episode")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.DERIVED)


class BlueprintContinuityContext(BaseModel):
    """Inherited upstream continuity state stored strictly as references and mutations."""
    previous_episode_id_ref: Optional[str] = Field(default=None, description="Preceding episode ID")
    starting_character_states: Dict[str, str] = Field(default_factory=dict, description="Character state at start")
    starting_knowledge_states: Dict[str, str] = Field(default_factory=dict, description="What each character knows")
    starting_relationship_states: Dict[str, str] = Field(default_factory=dict, description="Dynamic between key characters")
    active_plants: List[str] = Field(default_factory=list, description="Narrative plants active from Story Package")
    plants_activated_in_episode: List[str] = Field(default_factory=list, description="Plants paid off or advanced here")
    expected_payoffs: List[str] = Field(default_factory=list, description="Payoffs targeted for future episodes")
    chronology_anchor_ref: Optional[int] = Field(default=None, description="Anchor number in Story Package spine")
    chronology_anchor_name: Optional[str] = Field(default=None, description="Anchor name in Story Package spine")
    world_rules_refs: List[str] = Field(default_factory=list, description="Referenced world/customary rules")
    episode_state_mutations: List[str] = Field(default_factory=list, description="State mutations created in this episode")
    ending_state_passed_forward: Optional[str] = Field(default=None, description="State passed to next episode")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.CANON)


class BlueprintCompletenessAudit(BaseModel):
    """Strict evaluation of blueprint completeness and sparse-input honesty."""
    is_complete: bool = Field(default=False)
    is_sparse_draft: bool = Field(default=False)
    has_hook: bool = Field(default=False)
    has_cliffhanger: bool = Field(default=False)
    has_emotional_movement: bool = Field(default=False)
    has_character_arcs: bool = Field(default=False)
    has_all_beats: bool = Field(default=False)
    missing_required_elements: List[str] = Field(default_factory=list)
    unbacked_sparse_fields: List[str] = Field(default_factory=list)
    audited_at: str = Field(description="ISO-8601 audit timestamp")


class EpisodeBlueprintModel(BaseModel):
    """
    Authoritative Downstream Episode Blueprint.
    Bridges 'What is this episode?' with 'What do we need to produce this episode?'
    """
    id: str = Field(description="Unique blueprint ID, e.g. bp_series_123_ep1_v1")
    episode_id: str = Field(description="Authoritative parent Episode ID")
    series_id: str = Field(description="Parent Series ID")
    story_package_id: str = Field(description="Authoritative upstream M3 Story Package ID")
    ip_id: str = Field(description="Authoritative root Digital IP ID")
    season_number: int = Field(default=1, ge=1)
    episode_number: int = Field(ge=1)
    blueprint_version: str = Field(default="1.0.0")
    status: BlueprintStatus = Field(default=BlueprintStatus.DRAFT)
    
    # Executable Dramatic Structure
    dramatic_objective: BlueprintDramaticObjective
    character_arcs: List[BlueprintCharacterArc] = Field(default_factory=list)
    beat_sequence: List[BlueprintBeat] = Field(default_factory=list)
    hook: BlueprintHook
    cliffhanger: BlueprintCliffhanger
    emotional_trajectory: BlueprintEmotionalTrajectory
    continuity_context: BlueprintContinuityContext
    completeness_audit: BlueprintCompletenessAudit

    # Governance & Provenance
    forge_configuration_id: str = Field(default="CFG-001")
    source_lineage_hash: str = Field(description="Upstream Story Package lineage hash")
    artifact_lineage_hash: str = Field(description="Unique SHA-256 hash representing this Blueprint's identity")
    provenance: BlueprintProvenance = Field(default=BlueprintProvenance.DERIVED)
    created_at: str
    updated_at: str

    @classmethod
    def compute_artifact_hash(
        cls,
        episode_id: str,
        blueprint_version: str,
        source_lineage_hash: str,
        dramatic_objective_text: str
    ) -> str:
        """Deterministic SHA-256 hash identifying this specific Blueprint artifact."""
        payload = f"{episode_id}|{blueprint_version}|{source_lineage_hash}|{dramatic_objective_text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
