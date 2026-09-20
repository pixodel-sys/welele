"""
Welele Media™ — Production Bible & Episode Production Pack Canonical Schemas
Defines strict hierarchical artifact contracts:
  Story Package (Authoritative Story Truth)
     ↓
  Production Bible (Reusable Title-Level Production Specification - 10 Sections)
     ↓
  Episode Production Pack (Episode-Specific Execution Specification - 5 Coordinated Tracks)

Every atomic element preserves provenance classification:
  - CANON: Direct authoritative truth from Story Package.
  - DERIVED: Deterministically/logically formatted from canon without inventing lore.
  - GENERATED: Engine-synthesized execution proposals (shotlist, audio design, score).
  - PRODUCTION_DECISION: Explicit physical/budget/technical constraints.

Governed Missing Information States:
  - UNKNOWN: Information about the story world or character not present in canon.
  - NOT_SPECIFIED: Creative/production parameters unprovided in upstream data.
  - DEFERRED: Decisions intentionally postponed to on-set or post-production teams.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ProvenanceType(str, Enum):
    CANON = "CANON"                          # Direct authoritative truth from Story Package
    DERIVED = "DERIVED"                      # Deterministically/logically derived from canon
    GENERATED = "GENERATED"                  # Engine-synthesized execution specification
    PRODUCTION_DECISION = "PRODUCTION_DECISION"  # Explicit operational/technical standard


class GovernedState(str, Enum):
    UNKNOWN = "UNKNOWN"
    NOT_SPECIFIED = "NOT_SPECIFIED"
    DEFERRED = "DEFERRED"


class CanonMutationError(Exception):
    """Raised when downstream generation attempts to mutate upstream canonical truth."""
    pass


class ProvenanceEscalationError(Exception):
    """Raised when downstream elements attempt unauthorized escalation to CANON."""
    pass


# =============================================================================
# 1. PRODUCTION BIBLE SCHEMAS (10 Canonical Sections)
# =============================================================================

class TitleIdentity(BaseModel):
    """Section 1: Title Identity"""
    title: str
    franchise_code: str
    format: str = "9:16 Vertical Microdrama"
    target_duration_seconds: int = 90
    primary_language: str = "NOT_SPECIFIED"
    secondary_languages: List[str] = Field(default_factory=lambda: ["NOT_SPECIFIED"])
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.title_identity"


class CreativeDNA(BaseModel):
    """Section 2: Creative DNA"""
    logline: str
    thematic_premise: str
    genre_taxonomy: str
    tonal_anchors: List[str]
    dramatic_engine: str
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.creative_dna"


class CharacterProductionEntry(BaseModel):
    """Section 3: Character Production Entry with Audited Provenance Boundaries"""
    name: str
    role: str
    archetype: str = "NOT_SPECIFIED"
    core_motivation: str = "NOT_SPECIFIED"
    fatal_flaw: str = "NOT_SPECIFIED"
    signature_dialogue: str = "NOT_SPECIFIED"
    # Story-truth fields are CANON
    canon_provenance: ProvenanceType = ProvenanceType.CANON
    canon_source_path: str = "story_package.characters"

    # Execution/wardrobe styling derived from narrative context
    visual_key: str = "DEFERRED"
    wardrobe_palette: str = "DEFERRED"
    costume_distress_rules: str = "DEFERRED"
    derived_provenance: ProvenanceType = ProvenanceType.DERIVED

    # Technical casting/dialect guidance set by production policy
    casting_spec: str = "DEFERRED"
    dialect_guidance: str = "DEFERRED"
    production_decision_provenance: ProvenanceType = ProvenanceType.PRODUCTION_DECISION

    provenance: ProvenanceType = ProvenanceType.CANON  # Overall anchor class


class LocationProductionEntry(BaseModel):
    """Section 4: Location Production Entry"""
    location_name: str
    setting_type: str = "NOT_SPECIFIED"
    spatial_layout: str = "NOT_SPECIFIED"
    lighting_conditions: str = "NOT_SPECIFIED"
    soundstage_vs_practical_criteria: str = "DEFERRED"
    provenance: ProvenanceType = ProvenanceType.DERIVED
    source_path: str = "story_package.locations"
    derivation_notes: str = "Derived from story package narrative settings into shooting stage parameters."


class SupernaturalWorldRule(BaseModel):
    """Section 5: Supernatural & World Rules"""
    rule_key: str
    law_description: str
    narrative_impact: str
    inviolability: str = "STRICT_CANON"
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.inviolable_rules"


class VisualLanguage(BaseModel):
    """Section 6: Visual Language"""
    aspect_ratio: str = "9:16 Vertical (1080x1920 Native)"
    framing_protocols: List[str]
    lighting_grammar: str = "DEFERRED"
    color_palette: List[Dict[str, str]] = Field(default_factory=list)
    lut_specifications: str = "DEFERRED"
    camera_and_lens_package: List[Dict[str, str]] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.PRODUCTION_DECISION
    source_path: str = "production_standards.visual_grammar"


class AudioLanguage(BaseModel):
    """Section 7: Audio Language"""
    vernacular_matrix: Dict[str, str] = Field(default_factory=dict)
    foley_architecture: List[Dict[str, str]] = Field(default_factory=list)
    score_signature: Dict[str, Any] = Field(default_factory=dict)
    dialogue_mix_standard: str = "-14 LUFS (Standard)"
    provenance: ProvenanceType = ProvenanceType.PRODUCTION_DECISION
    source_path: str = "production_standards.audio_mastering"


class ContinuityBible(BaseModel):
    """Section 8: Continuity Bible"""
    chronology_spine: List[Dict[str, Any]] = Field(default_factory=list)
    narrative_plants_and_payoffs: List[Dict[str, Any]] = Field(default_factory=list)
    prop_and_costume_locks: List[Dict[str, str]] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.chronology_and_plants"


class ProductionConstraint(BaseModel):
    """Section 9: Production Constraints"""
    budget_tier: str = "Tier 1 Standard"
    practical_sets_max: int = 2
    cast_density_per_scene_max: int = 3
    safety_and_stunt_limits: List[str] = Field(default_factory=lambda: ["DEFERRED"])
    shooting_block_protocol: str = "DEFERRED"
    provenance: ProvenanceType = ProvenanceType.PRODUCTION_DECISION
    source_path: str = "production_guidelines.constraints"


class PromptConstitution(BaseModel):
    """Section 10: Prompt Constitution (Inviolable Generative Guardrails)"""
    governing_laws: List[str]
    forbidden_mutations: List[str]
    aspect_ratio_enforcement: str = "9:16 Vertical Native Only"
    canon_override_rule: str = "CANON_OVERRIDES_PROMPT_CONVENIENCE"
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "creative_constitution.v1"


class ProductionBibleModel(BaseModel):
    """
    Canonical 10-Section Production Bible Contract.
    Reusable title-level production specification derived from Story Package.
    """
    id: str
    ip_id: str
    story_package_id: str
    bible_title: str
    version: str = "1.0.0"
    forge_configuration_id: str = "CFG-001"
    lineage_hash: str

    # 10 Canonical Sections
    section_1_title_identity: TitleIdentity
    section_2_creative_dna: CreativeDNA
    section_3_character_bible: List[CharacterProductionEntry]
    section_4_location_bible: List[LocationProductionEntry]
    section_5_world_rules: List[SupernaturalWorldRule]
    section_6_visual_language: VisualLanguage
    section_7_audio_language: AudioLanguage
    section_8_continuity_bible: ContinuityBible
    section_9_production_constraints: ProductionConstraint
    section_10_prompt_constitution: PromptConstitution

    created_at: str


# =============================================================================
# 2. EPISODE PRODUCTION PACK SCHEMAS (5 Coordinated Tracks)
# =============================================================================

class EpisodeBeat(BaseModel):
    beat_number: int
    label: str
    timestamp_start_s: int
    timestamp_end_s: int
    intensity: int = Field(ge=1, le=10)
    action_summary: str
    cliffhanger_trigger: bool = False
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.beats"


class TrackVideo(BaseModel):
    """Track 1: VIDEO (Visuals, Camera Motion, 9:16 Framing, Lighting & Blocking)"""
    scene_descriptions: List[Dict[str, Any]]
    camera_direction: List[Dict[str, str]] = Field(default_factory=list)
    lighting_execution: str = "DEFERRED"
    provenance: ProvenanceType = ProvenanceType.GENERATED
    source_path: str = "generator.track_video"
    derivation_notes: str = "Generated from episode beats and visual language grammar."


class TrackDialogue(BaseModel):
    """Track 2: DIALOGUE (Exact Lines, Subtext, Delivery Tone & Vernacular Cadence)"""
    dialogue_lines: List[Dict[str, Any]] = Field(default_factory=list)
    vernacular_subtext_notes: List[str] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.dialogue"
    derivation_notes: str = "Verbatim spoken lines sourced from Story Package; subtext derived from character motivation."


class TrackNarration(BaseModel):
    """Track 3: NARRATION (Voice-over, Internal Monologue, Audio Hooks)"""
    has_narration: bool = False
    opening_hook_vo: Optional[str] = None
    internal_monologues: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.DERIVED
    source_path: str = "story_package.thematic_premise"
    derivation_notes: str = "Voiceover hooks synthesized from logline and dramatic engine."


class TrackAmbience(BaseModel):
    """Track 4: AMBIENCE (Room Tone, Foley Cues & Environmental Audio SFX)"""
    room_tone: str = "NOT_SPECIFIED"
    foley_events: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.GENERATED
    source_path: str = "generator.track_ambience"
    derivation_notes: str = "Generated sound design timeline synchronized to scene events."


class TrackMusic(BaseModel):
    """Track 5: MUSIC (Score Stems, BPM, Tension Curve & Cliffhanger Silence Cut)"""
    score_theme: str = "NOT_SPECIFIED"
    tempo_bpm: Optional[int] = None
    instrumentation: List[str] = Field(default_factory=list)
    stems_progression: List[Dict[str, Any]] = Field(default_factory=list)
    paywall_cut_behavior: str = "ABRUPT_SILENCE_AT_CLIFFHANGER"
    provenance: ProvenanceType = ProvenanceType.GENERATED
    source_path: str = "generator.track_music"
    derivation_notes: str = "Generated musical arrangement aligned to dramatic intensity curve."


class FiveCoordinatedTracks(BaseModel):
    video: TrackVideo
    dialogue: TrackDialogue
    narration: TrackNarration
    ambience: TrackAmbience
    music: TrackMusic


class NarrativeContinuity(BaseModel):
    prerequisites: List[str] = Field(default_factory=list)
    narrative_state_start: str = "NOT_SPECIFIED"
    state_mutations: List[str] = Field(default_factory=list)
    active_plants: List[str] = Field(default_factory=list)
    carried_forward_to_next_ep: str = "NOT_SPECIFIED"
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.narrative_continuity"


class EpisodeProductionPackModel(BaseModel):
    """
    Canonical Episode Production Pack Contract.
    Episode-specific execution specification derived from Production Bible + Episode Architecture.
    """
    id: str
    production_bible_id: str
    ip_id: str
    episode_number: int
    title: str
    duration_seconds: int = 90
    cliffhanger_prompt: str
    story_brief: str
    beats: List[EpisodeBeat]
    narrative_continuity: NarrativeContinuity
    five_tracks: FiveCoordinatedTracks
    forge_configuration_id: str = "CFG-001"
    lineage_hash: str
    created_at: str


# =============================================================================
# 3. PROVENANCE HONESTY & CANON IMMUTABILITY VALIDATORS
# =============================================================================

def validate_downstream_mutation(upstream_package: Dict[str, Any], downstream_payload: Dict[str, Any]) -> None:
    """
    Guarantees that downstream production generation never mutates upstream Story Package canon.
    Rejects mutations to characters, motivations, relationships, world rules, chronology, or premise.
    """
    protected_fields = [
        "logline", "thematic_premise", "genre", "primary_language",
        "characters", "inviolable_rules", "chronology_spine", "plants", "cliffhanger_prompt"
    ]

    for field in protected_fields:
        if field in downstream_payload:
            upstream_val = upstream_package.get(field)
            downstream_val = downstream_payload.get(field)
            if upstream_val is not None and downstream_val != upstream_val:
                raise CanonMutationError(
                    f"CANON_MUTATION_REJECTED: Downstream payload attempted unauthorized alteration of '{field}' "
                    f"from '{upstream_val}' to '{downstream_val}'. Canon is immutable."
                )


def validate_provenance_escalation(element_provenance: ProvenanceType, source_provenance: Optional[ProvenanceType]) -> None:
    """
    Ensures that authority only flows downstream.
    GENERATED and DERIVED elements cannot be escalated to CANON without an authoritative upstream source.
    """
    if element_provenance == ProvenanceType.CANON:
        if source_provenance not in (ProvenanceType.CANON, None):
            raise ProvenanceEscalationError(
                f"PROVENANCE_ESCALATION_REJECTED: Cannot promote element from source '{source_provenance}' to 'CANON'. "
                f"Authority cannot flow upstream."
            )


def verify_traceability(model_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies that every non-empty atomic field answers:
    - What is this?
    - Where did it come from? (source_path)
    - Provenance classification (provenance)
    - Derivation rationale (derivation_notes if DERIVED/GENERATED)
    """
    missing_trace = []

    def check_node(node: Any, path: str):
        if isinstance(node, dict):
            if "provenance" in node:
                prov = node.get("provenance")
                src = node.get("source_path") or node.get("canon_source_path")
                if not src and prov in (ProvenanceType.CANON, ProvenanceType.DERIVED):
                    missing_trace.append(f"{path}: missing source_path for provenance '{prov}'")
            for k, v in node.items():
                check_node(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                check_node(item, f"{path}[{i}]")

    check_node(model_dict, "")
    return {
        "is_traceable": len(missing_trace) == 0,
        "violations": missing_trace
    }


# =============================================================================
# 4. REQUEST / RESPONSE SCHEMAS
# =============================================================================

class ProductionBibleCreateRequest(BaseModel):
    ip_id: str
    story_package_id: Optional[str] = None
    version: str = "1.0.0"


class EpisodeProductionPackCreateRequest(BaseModel):
    ip_id: str
    production_bible_id: Optional[str] = None
    episode_number: int = 1
