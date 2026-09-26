"""
Welele Media™ — Evidence Projections Schemas (Phase B)
Defines rebuildable, disposable, and versioned materialized views projected strictly from
the authoritative immutable Unified Event Spine.

Governing Axioms:
1. Projections are non-canonical, read-only derived views.
2. Every projection carries full provenance metadata (versions, counts, timestamps, lineage).
3. Any projection can be wiped and bit-for-bit rebuilt from raw events.
4. No heuristic labels; drops are classified as RETENTION_ANOMALY with explicit correlation.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class RetentionAnomalyType(str, Enum):
    """Factual classification of detected retention drops."""
    RETENTION_ANOMALY_CLEAN_PLAYBACK = "RETENTION_ANOMALY_CLEAN_PLAYBACK"
    RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION = "RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION"


class ConfidenceTier(str, Enum):
    """
    Versioned policy for graduated evidence confidence based on sample size.
    INSUFFICIENT (N < 10) -> PRELIMINARY (10 <= N < 30) -> DEVELOPING (30 <= N < 100) -> ESTABLISHED (N >= 100)
    """
    INSUFFICIENT = "INSUFFICIENT"
    PRELIMINARY = "PRELIMINARY"
    DEVELOPING = "DEVELOPING"
    ESTABLISHED = "ESTABLISHED"


class ProvenanceEnvelope(BaseModel):
    """
    Authoritative provenance metadata required on every projected evidence output.
    Guarantees historical reproducibility and calculation transparency.
    """
    projection_version: str = Field(default="1.0.0", description="SemVer of projection schema contract")
    methodology_version: str = Field(default="2026.1", description="Version of derivation algorithm logic")
    calculation_timestamp: str = Field(description="ISO-8601 UTC timestamp when projection was compiled")
    source_event_count: int = Field(description="Total raw immutable events ingested in this projection run")
    source_session_count: int = Field(description="Total unique sessions contributing to this projection")
    source_event_window: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Bounding time interval {start_time, end_time} of included source events"
    )
    confidence_tier: ConfidenceTier = Field(description="Graduated confidence policy tier")
    confidence_disclosure: str = Field(description="Honest statement of uncertainty based on sample density")
    rebuildable: bool = Field(default=True, description="Strict invariant: projection is 100% rebuildable from spine")
    zero_synthetic_data: bool = Field(default=True, description="Strict invariant: zero synthetic/mocked numbers")
    environment_filter: str = Field(default="production", description="Queried environment boundary")
    test_events_excluded: int = Field(default=0, description="Total non-production/quarantined events excluded")
    canary_events_excluded: int = Field(default=0, description="Explicit canary/test events excluded")
    legacy_events_quarantined: int = Field(default=0, description="Legacy/untrusted provenance events quarantined")
    has_data: bool = Field(default=False, description="Whether genuine evidence was evaluated")


class MilestoneReachSummary(BaseModel):
    reached_25_pct: int = 0
    reached_50_pct: int = 0
    reached_75_pct: int = 0
    reached_90_pct: int = 0
    reached_100_pct: int = 0


class TechnicalDisruptionSummary(BaseModel):
    total_buffer_events: int = 0
    total_stall_events: int = 0
    sessions_with_disruptions: int = 0
    stall_ratio_pct: float = 0.0


class RetentionTimecodeSample(BaseModel):
    second: int
    active_viewers: int
    retention_pct: float
    stalls_at_interval: int = 0
    is_cliffhanger_window: bool = False


class RetentionAnomalyRecord(BaseModel):
    anomaly_id: str
    second_start: int
    second_end: int
    retention_delta_pct: float
    classification: RetentionAnomalyType
    stalls_in_window: int
    sample_size: int
    confidence_tier: ConfidenceTier
    description: str


class ContentEvidenceProjection(BaseModel):
    """
    Materialized read-only Content Performance Matrix for an Episode or Series.
    Compiled exclusively from raw immutable ViewerTelemetryEvents.
    """
    projection_id: str
    target_entity_type: str = "EPISODE"
    target_id: str
    series_id: Optional[str] = None
    episode_id: Optional[str] = None
    provenance: ProvenanceEnvelope

    # The 12-Metric Empirical Performance Funnel
    impressions: int = 0
    starts: int = 0
    hook_3s_retained_count: int = 0
    hook_3s_retention_pct: float = 0.0
    hook_10s_retained_count: int = 0
    hook_10s_retention_pct: float = 0.0
    milestones: MilestoneReachSummary = Field(default_factory=MilestoneReachSummary)
    completions: int = 0
    completion_rate_pct: float = 0.0
    rewatches: int = 0
    next_episode_intent_count: int = 0
    paywall_presentations: int = 0
    unlock_attempts: int = 0
    unlock_successes: int = 0
    unlock_conversion_pct: float = 0.0
    technical_disruptions: TechnicalDisruptionSummary = Field(default_factory=TechnicalDisruptionSummary)

    # Granular Retention Curve & Disambiguated Anomalies
    retention_curve: List[RetentionTimecodeSample] = Field(default_factory=list)
    detected_anomalies: List[RetentionAnomalyRecord] = Field(default_factory=list)

    # Optional content discovery & selection metadata projected from spine
    discovered_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    selected_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    reactions_count: int = 0
    comments_count: int = 0
    entered_sessions_count: int = 0
    selected_sessions_count: int = 0
    post_pay_progression_sessions_count: int = 0
    returned_sessions_count: int = 0


class ViewerEvidenceProjection(BaseModel):
    """
    Factual behavioral summary of a specific viewer or anonymous device session history.
    Strictly observational; contains ZERO inferred persona tags or subjective taste ratings.
    """
    projection_id: str
    viewer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    provenance: ProvenanceEnvelope

    total_sessions: int = 0
    total_play_time_seconds: float = 0.0
    episodes_started: int = 0
    episodes_completed: int = 0
    overall_completion_ratio: float = 0.0
    unique_series_sampled: List[str] = Field(default_factory=list)
    continuation_actions: int = 0
    paywall_encounters: int = 0
    unlocks_completed: int = 0
    explicit_reactions_count: int = 0
    comments_submitted_count: int = 0
    shares_initiated_count: int = 0
