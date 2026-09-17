"""
Welele Media™ — Series & Episode Architecture Canonical Schemas
Defines strict downstream artifact contracts:
  Story Package (Upstream Canonical Authority - M3)
      ↓
  Series (Downstream Container referencing Upstream IP + Story Package)
      ↓
  Episode (Downstream Unit referencing Series + Story Package + Continuity Anchors)

Governance Invariants:
  1. Distinguishes upstream source_lineage_hash from downstream own artifact_lineage_hash.
  2. M3 Story Package is the existing upstream authority; zero secondary certification.
  3. References existing Episode Production Pack without new certification authorities.
  4. PACK_COORDINATED denotes structural coordination, NOT production/distribution readiness.
  5. Continuity inheritance is stored as references to upstream/previous state + episode-specific mutations.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import hashlib
import json

from schemas.production_schemas import ProvenanceType, GovernedState


class SeriesLifecycleState(str, Enum):
    DRAFT = "DRAFT"
    IN_PRODUCTION = "IN_PRODUCTION"
    READY_FOR_DISTRIBUTION = "READY_FOR_DISTRIBUTION"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class EpisodeLifecycleState(str, Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    UNDER_REVIEW = "UNDER_REVIEW"
    READY_FOR_DISTRIBUTION = "READY_FOR_DISTRIBUTION"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class EpisodeReadinessState(str, Enum):
    DRAFT_EMPTY = "DRAFT_EMPTY"              # Sparse / no production data yet
    BEAT_OUTLINED = "BEAT_OUTLINED"          # Narrative beats exist in story package
    PACK_COORDINATED = "PACK_COORDINATED"    # Structural 5-track pack coordinated (NOT production-ready)
    PRODUCTION_READY = "PRODUCTION_READY"    # Verified masters, audio mix, and QC passed


class ContinuityReference(BaseModel):
    """
    References to upstream chronology spine and previous episode state.
    Contains zero duplicated story lore.
    """
    anchor_number_ref: Optional[int] = None
    anchor_name_ref: Optional[str] = None
    previous_episode_id_ref: Optional[str] = None
    carried_forward_state_ref: Optional[str] = None
    active_plant_refs: List[str] = Field(default_factory=list)
    episode_state_mutations: List[str] = Field(default_factory=list)
    provenance: ProvenanceType = ProvenanceType.CANON
    source_path: str = "story_package.continuity_bible"


class ReadinessAudit(BaseModel):
    """
    Honest, non-false technical audit of episode completeness.
    """
    is_empty_draft: bool = True
    has_story_package_ref: bool = True
    has_production_pack_ref: bool = False
    has_media_asset_ref: bool = False
    has_master_video: bool = False
    has_subtitles: bool = False
    missing_elements: List[str] = Field(default_factory=list)
    readiness_state: EpisodeReadinessState = EpisodeReadinessState.DRAFT_EMPTY
    audited_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SeriesModel(BaseModel):
    id: str
    ip_id: str
    story_package_id: str
    season_number: int = 1
    title: str
    tagline: Optional[str] = None
    synopsis: Optional[str] = None
    genre: Optional[str] = None
    primary_language: str = "isiZulu"
    format: str = "9:16 Vertical Microdrama"
    target_duration_seconds: int = 90
    total_episodes: int = 0
    lifecycle_state: SeriesLifecycleState = SeriesLifecycleState.DRAFT
    forge_configuration_id: str = "CFG-001"
    source_lineage_hash: str                  # Upstream Story Package SHA-256 hash
    artifact_lineage_hash: str                # Downstream Series own cryptographic identity
    provenance: ProvenanceType = ProvenanceType.CANON
    chronology_spine_anchor_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def compute_artifact_hash(cls, ip_id: str, story_package_id: str, season_number: int, source_hash: str) -> str:
        payload = f"SERIES::{ip_id}::{story_package_id}::S{season_number}::{source_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class EpisodeModel(BaseModel):
    id: str
    series_id: str
    ip_id: str
    story_package_id: str
    episode_number: int
    title: str
    synopsis: Optional[str] = None
    duration_seconds: int = 90
    lifecycle_state: EpisodeLifecycleState = EpisodeLifecycleState.DRAFT
    readiness_state: EpisodeReadinessState = EpisodeReadinessState.DRAFT_EMPTY
    continuity_reference: ContinuityReference
    production_pack_id: Optional[str] = None
    media_asset_id: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_empty_draft: bool = True
    readiness_audit: ReadinessAudit
    forge_configuration_id: str = "CFG-001"
    source_lineage_hash: str                  # Upstream Story Package SHA-256 hash
    artifact_lineage_hash: str                # Downstream Episode own cryptographic identity
    provenance: ProvenanceType = ProvenanceType.CANON
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def compute_artifact_hash(cls, series_id: str, episode_number: int, source_hash: str, pack_id: Optional[str] = None) -> str:
        payload = f"EPISODE::{series_id}::E{episode_number}::{pack_id or 'NO_PACK'}::{source_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Request / DTO Schemas
class CreateSeriesFromPackageRequest(BaseModel):
    ip_id: str
    story_package_id: str
    season_number: int = 1
    custom_title: Optional[str] = None


class CreateDownstreamEpisodeRequest(BaseModel):
    series_id: str
    episode_number: int
    custom_title: Optional[str] = None
    is_empty_draft: bool = True
    link_existing_production_pack: bool = True
    media_asset_id: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
