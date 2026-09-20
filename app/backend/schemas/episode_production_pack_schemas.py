"""
Welele Media™ — Episode Production Pack Canonical Schemas (Phase 3 Downstream Production Layer)
Authoritative flow: Digital IP → Story Package (M3) → Series → Episode → Episode Blueprint → Episode Production Pack.

Core Invariants:
  1. Translates authoritative Episode Blueprint into coordinated 5-track Production Units.
  2. Zero narrative mutation: Cannot rewrite characters, world rules, logline, chronology, or blueprint.
  3. Strict Provenance Governance: Supported classes (CANON, DERIVED, PROPOSED, PRODUCTION_DECISION, UNKNOWN).
  4. Production Decision ≠ Canon: Operational choices remain PRODUCTION_DECISION and never escalate to CANON.
  5. Sparse-input honesty: Missing information remains UNKNOWN or NOT_SPECIFIED.
  6. Distinct artifact_lineage_hash separate from upstream source_lineage_hash.
"""

from enum import Enum
import hashlib
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PackReadinessState(str, Enum):
    DRAFT = "DRAFT"
    INCOMPLETE = "INCOMPLETE"
    COORDINATED = "COORDINATED"
    READY_FOR_PRODUCTION = "READY_FOR_PRODUCTION"
    IN_PRODUCTION = "IN_PRODUCTION"
    COMPLETED = "COMPLETED"


class ProductionProvenance(str, Enum):
    CANON = "CANON"
    DERIVED = "DERIVED"
    PROPOSED = "PROPOSED"
    PRODUCTION_DECISION = "PRODUCTION_DECISION"
    UNKNOWN = "UNKNOWN"


class VideoTrackSpecification(BaseModel):
    """Track 1: Visual production specification for a single Production Unit."""
    framing: str = Field(default="9:16 Vertical Framing", description="Camera framing: Close-Up, Wide, OTS, Low-Angle")
    camera_direction: str = Field(default="Static eye-level", description="Camera movement or angle direction")
    visual_action: str = Field(description="Visual physical action occurring on screen")
    environment: str = Field(description="Visual location, set context, and atmospheric physical details")
    lighting: str = Field(default="NOT_SPECIFIED", description="Lighting setup, practicals, or color temperature")
    visual_continuity: str = Field(default="Maintains visual look from previous unit", description="Visual continuity markers")
    required_visual_elements: List[str] = Field(default_factory=list, description="Must-have physical visual assets or marks")
    visual_prompt: Optional[str] = Field(default=None, description="Detailed visual rendering/prompt specification")
    negative_constraints: List[str] = Field(default_factory=list, description="Visual negative prompt/anti-patterns")
    timing_start_seconds: Optional[int] = Field(default=None)
    timing_end_seconds: Optional[int] = Field(default=None)
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="blueprint.beat_sequence")


class DialogueTrackSpecification(BaseModel):
    """Track 2: Spoken dialogue specification for a single Production Unit."""
    speaker: str = Field(default="UNKNOWN", description="Speaking character or UNKNOWN")
    dialogue: str = Field(default="NOT_SPECIFIED", description="Spoken dialogue text or NOT_SPECIFIED")
    delivery_intention: str = Field(default="NOT_SPECIFIED", description="Subtext or emotional delivery intent")
    emotion: str = Field(default="NOT_SPECIFIED", description="Vocal emotion: defiant, whispering, frantic")
    language: str = Field(default="isiZulu", description="Primary spoken language")
    dialect: Optional[str] = Field(default=None, description="Specific dialect or vernacular nuance")
    timing_start_seconds: Optional[int] = Field(default=None)
    timing_end_seconds: Optional[int] = Field(default=None)
    context: str = Field(default="Scene conversation", description="Dramatic dialogue context")
    continuity: str = Field(default="Continuous character voice", description="Vocal continuity notes")
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="story_package.dialogues")


class NarrationTrackSpecification(BaseModel):
    """Track 3: Voiceover/narration specification for a single Production Unit."""
    narration_text: Optional[str] = Field(default=None, description="Narration line or None if unscripted")
    timing_start_seconds: Optional[int] = Field(default=None)
    timing_end_seconds: Optional[int] = Field(default=None)
    narrator_characteristics: str = Field(default="NOT_SPECIFIED", description="Narrator persona / characteristics")
    tone: str = Field(default="NOT_SPECIFIED", description="Vocal narration tone")
    purpose: str = Field(default="NOT_SPECIFIED", description="Expository or thematic purpose")
    relationship_to_visuals: str = Field(default="Synchronous with visual action", description="Visual synchronization")
    relationship_to_dialogue: str = Field(default="Does not overlap dialogue", description="Dialogue clearance")
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="blueprint.hook")


class AmbienceTrackSpecification(BaseModel):
    """Track 4: Foley and environmental ambience specification for a single Production Unit."""
    location_ambience: str = Field(default="NOT_SPECIFIED", description="Ambient room tone or outdoor soundbed")
    environmental_sound: str = Field(default="NOT_SPECIFIED", description="Specific background environmental layers")
    action_sfx: List[str] = Field(default_factory=list, description="Specific physical sound effects triggered by action")
    transitions: str = Field(default="Cut soundbed with scene", description="Audio transition description")
    intensity: int = Field(default=5, ge=1, le=10, description="Ambience audio intensity 1-10")
    timing_start_seconds: Optional[int] = Field(default=None)
    timing_end_seconds: Optional[int] = Field(default=None)
    continuity: str = Field(default="Maintains soundbed continuity", description="Audio continuity notes")
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="blueprint.location_ref")


class MusicTrackSpecification(BaseModel):
    """Track 5: Score and musical motif specification for a single Production Unit."""
    cue: str = Field(default="NOT_SPECIFIED", description="Score cue identifier or theme name")
    dramatic_purpose: str = Field(default="NOT_SPECIFIED", description="Dramatic purpose of music in this unit")
    emotional_purpose: str = Field(default="NOT_SPECIFIED", description="Target emotional state evoked by score")
    style_instrumentation: str = Field(default="NOT_SPECIFIED", description="Instrumentation and genre style where known")
    intensity: int = Field(default=5, ge=1, le=10, description="Musical intensity level 1-10")
    entry_seconds: Optional[int] = Field(default=None, description="Cue entry timestamp")
    exit_seconds: Optional[int] = Field(default=None, description="Cue exit timestamp")
    recurring_musical_continuity: Optional[str] = Field(default=None, description="Leitmotif or recurring theme reference")
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="story_package.audio_language")


class ProductionUnit(BaseModel):
    """
    Core Production Unit coordinating all 5 production tracks around a discrete Blueprint Beat.
    """
    unit_id: str = Field(description="Unique unit identifier, e.g. unit_ep1_01")
    sequence: int = Field(ge=1, le=20, description="Sequential ordering 1-9+")
    episode_id: str = Field(description="Parent Episode ID")
    blueprint_beat_ref: str = Field(description="Referenced Blueprint Beat ID, e.g. beat_ep1_01")
    story_purpose: str = Field(description="Story purpose inherited from Blueprint beat")
    location_ref: str = Field(default="UNKNOWN", description="Canonical location reference")
    character_refs: List[str] = Field(default_factory=list, description="Characters involved in this unit")
    estimated_duration_seconds: int = Field(default=10, ge=1)
    timing_start_seconds: Optional[int] = Field(default=None)
    timing_end_seconds: Optional[int] = Field(default=None)
    continuity_refs: List[str] = Field(default_factory=list, description="Inherited continuity references")
    production_status: str = Field(default="COORDINATED")
    
    # 5 Coordinated Tracks
    video_track: VideoTrackSpecification
    dialogue_track: DialogueTrackSpecification
    narration_track: NarrationTrackSpecification
    ambience_track: AmbienceTrackSpecification
    music_track: MusicTrackSpecification

    # Explicit Production Decisions
    production_decisions: List[Dict[str, Any]] = Field(default_factory=list, description="Explicit production decisions")

    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    source_path: str = Field(default="blueprint.beat_sequence")


class PackReadinessAudit(BaseModel):
    """Machine-readable Production Pack readiness audit."""
    readiness_state: PackReadinessState
    is_sparse_draft: bool = Field(default=False)
    unit_count: int = Field(ge=0)
    missing_video_instructions: List[str] = Field(default_factory=list)
    missing_dialogue: List[str] = Field(default_factory=list)
    missing_narration: List[str] = Field(default_factory=list)
    missing_ambience: List[str] = Field(default_factory=list)
    missing_music: List[str] = Field(default_factory=list)
    missing_character_refs: List[str] = Field(default_factory=list)
    missing_locations: List[str] = Field(default_factory=list)
    missing_continuity: List[str] = Field(default_factory=list)
    unresolved_decisions: List[str] = Field(default_factory=list)
    missing_media_masters: List[str] = Field(default_factory=list)
    timing_conflicts: List[str] = Field(default_factory=list)
    track_drift_warnings: List[str] = Field(default_factory=list)
    classification_breakdown: Dict[str, int] = Field(default_factory=dict, description="Counts of UNKNOWN, NOT_SPECIFIED, DEFERRED, UNRESOLVED, READY")
    audited_at: str = Field(description="ISO-8601 audit timestamp")


class EpisodeProductionPackModel(BaseModel):
    """
    Authoritative Downstream Episode Production Pack.
    Translates an Episode Blueprint into an executable 5-track production specification.
    """
    id: str = Field(description="Unique Production Pack ID, e.g. epp_series_123_ep1_v1")
    pack_version: str = Field(default="1.0.0")
    episode_id: str = Field(description="Authoritative parent Episode ID")
    series_id: str = Field(description="Parent Series ID")
    story_package_id: str = Field(description="Authoritative upstream Story Package ID")
    ip_id: str = Field(description="Authoritative root Digital IP ID")
    blueprint_id: str = Field(description="Authoritative source Episode Blueprint ID")
    blueprint_version: str = Field(default="1.0.0", description="Source Blueprint version")
    season_number: int = Field(default=1, ge=1)
    episode_number: int = Field(ge=1)
    
    # 5-Track Coordinated Units
    production_units: List[ProductionUnit] = Field(default_factory=list)
    
    # Governance & Readiness
    readiness_state: PackReadinessState = Field(default=PackReadinessState.COORDINATED)
    readiness_audit: PackReadinessAudit
    forge_configuration_id: str = Field(default="CFG-001")
    source_lineage_hash: str = Field(description="Upstream Story Package lineage hash")
    artifact_lineage_hash: str = Field(description="Unique SHA-256 hash identifying this Production Pack")
    provenance: ProductionProvenance = Field(default=ProductionProvenance.DERIVED)
    created_at: str
    updated_at: str

    @classmethod
    def compute_artifact_hash(
        cls,
        blueprint_id: str,
        blueprint_version: str,
        source_lineage_hash: str,
        unit_count: int
    ) -> str:
        """Deterministic SHA-256 hash identifying this specific Production Pack artifact."""
        payload = f"{blueprint_id}|{blueprint_version}|{source_lineage_hash}|{unit_count}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
