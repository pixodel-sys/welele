"""
Welele Media™ — Viewer Telemetry Models (Phase 6 Measurement Layer)
Defines the conceptual event spine (OPEN → WATCH → CONTINUE → REACT → RETURN → PAY),
controlled event taxonomy, event provenance, failure isolation, and the 10 Telemetry Integrity Checks.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EventSpineFamily(str, Enum):
    """The 6 foundational behavioural spine families."""
    OPEN = "OPEN"
    WATCH = "WATCH"
    CONTINUE = "CONTINUE"
    REACT = "REACT"
    RETURN = "RETURN"
    PAY = "PAY"


class ViewerEventType(str, Enum):
    """Controlled implementation event taxonomy mapped strictly beneath the spine families."""
    # OPEN
    APP_OPEN = "APP_OPEN"
    FEED_IMPRESSION = "FEED_IMPRESSION"
    CONTENT_OPENED = "CONTENT_OPENED"

    # WATCH
    PLAYBACK_STARTED = "PLAYBACK_STARTED"
    PLAYBACK_PROGRESS = "PLAYBACK_PROGRESS"
    PLAYBACK_PAUSED = "PLAYBACK_PAUSED"
    PLAYBACK_RESUMED = "PLAYBACK_RESUMED"
    PLAYBACK_COMPLETED = "PLAYBACK_COMPLETED"
    BUFFER_STARTED = "BUFFER_STARTED"
    BUFFER_RESOLVED = "BUFFER_RESOLVED"
    STALL_DETECTED = "STALL_DETECTED"
    BITRATE_ADAPTED = "BITRATE_ADAPTED"

    # INTERACT
    SCRUB_SEEKED = "SCRUB_SEEKED"
    AUDIO_TOGGLED = "AUDIO_TOGGLED"
    CAPTION_TOGGLED = "CAPTION_TOGGLED"
    FULLSCREEN_TOGGLED = "FULLSCREEN_TOGGLED"

    # CONTINUE
    NEXT_EPISODE_SELECTED = "NEXT_EPISODE_SELECTED"
    GATED_CONTENT_PRESENTED = "GATED_CONTENT_PRESENTED"

    # REACT
    REACTION_ADDED = "REACTION_ADDED"
    REACTION_REMOVED = "REACTION_REMOVED"
    COMMENT_SUBMITTED = "COMMENT_SUBMITTED"
    SHARE_INITIATED = "SHARE_INITIATED"

    # RETURN
    SESSION_RETURNED = "SESSION_RETURNED"

    # PAY
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CONTENT_UNLOCKED = "CONTENT_UNLOCKED"


class EventSource(str, Enum):
    """Measurement provenance: distinguishes browser-reported events from server-confirmed events."""
    CLIENT = "CLIENT"
    SERVER = "SERVER"


class TelemetryCheckCategory(str, Enum):
    EVENT_IDENTITY_GAP = "EVENT_IDENTITY_GAP"
    CONTENT_LINEAGE_GAP = "CONTENT_LINEAGE_GAP"
    SESSION_GAP = "SESSION_GAP"
    TEMPORAL_GAP = "TEMPORAL_GAP"
    PLAYBACK_GAP = "PLAYBACK_GAP"
    CONTINUATION_GAP = "CONTINUATION_GAP"
    REACTION_GAP = "REACTION_GAP"
    RETURN_GAP = "RETURN_GAP"
    PAYMENT_GAP = "PAYMENT_GAP"
    FAILURE_ISOLATION_GAP = "FAILURE_ISOLATION_GAP"
    OTHER = "OTHER"


class TelemetrySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


class TelemetryResolutionType(str, Enum):
    EXISTING_CONFIGURATION = "EXISTING_CONFIGURATION"
    EXISTING_PRODUCT_DECISION = "EXISTING_PRODUCT_DECISION"
    NEW_PRODUCT_DECISION = "NEW_PRODUCT_DECISION"
    CLIENT_BUFFERING_FIX = "CLIENT_BUFFERING_FIX"
    SCHEMA_NORMALIZATION = "SCHEMA_NORMALIZATION"
    DEFERRED = "DEFERRED"


class ViewerTelemetryEvent(BaseModel):
    """
    Authoritative immutable event record representing a factual viewer action.
    Telemetry records facts, never analytical interpretations or subjective deductions.
    """
    event_id: str = Field(description="Unique deterministic or UUID event identifier")
    event_family: EventSpineFamily = Field(description="Spine family: OPEN, WATCH, CONTINUE, REACT, RETURN, PAY")
    event_type: ViewerEventType = Field(description="Concrete implementation event type")
    occurred_at: str = Field(description="ISO 8601 UTC timestamp of occurrence")
    session_id: str = Field(description="Unique viewing session identifier")
    viewer_id: Optional[str] = Field(default=None, description="Authenticated viewer identity if available")
    anonymous_id: Optional[str] = Field(default=None, description="Anonymous device/browser identifier")
    content_type: str = Field(default="EPISODE", description="Target entity type: EPISODE, SERIES")
    content_id: str = Field(description="ID of target episode or series")
    series_id: Optional[str] = Field(default=None, description="Associated parent series ID")
    episode_id: Optional[str] = Field(default=None, description="Associated episode ID")
    position_seconds: float = Field(default=0.0, description="Exact playback timestamp in seconds")
    duration_seconds: float = Field(default=0.0, description="Total duration of content in seconds")
    milestone_pct: Optional[int] = Field(default=None, description="25, 50, 75, 90, 100 for milestone progress")
    event_source: EventSource = Field(default=EventSource.CLIENT, description="CLIENT or SERVER provenance")
    event_version: str = Field(default="1.0", description="Telemetry schema contract version")
    source: Optional[str] = Field(default=None, description="Referrer/entry context, e.g. DISCOVERY_FEED, VERTICAL_PLAYER")
    environment: str = Field(default="production", description="Runtime environment: production, staging, test")
    is_test: bool = Field(default=False, description="Flag indicating automated test, canary, or internal test session")
    technical_context: Optional[Dict[str, Any]] = Field(default=None, description="Factual network & playback conditions: connection_type, buffer_health_sec, bitrate, etc.")
    cohort_context: Optional[Dict[str, Any]] = Field(default=None, description="Non-prescriptive cohort context: viewer_tier, entry_rail, referrer, device_class")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Bounded event-specific factual context")
    ingested_at: Optional[str] = Field(default=None, description="ISO 8601 UTC timestamp of backend ingestion")


class TelemetryIntegrityCheckResult(BaseModel):
    """Result of one of the 10 formal Telemetry Integrity Checks."""
    check_id: str = Field(description="Check number 1-10")
    check_name: str = Field(description="Formal check name")
    status: str = Field(description="PASSED, WARNING, or FAILED")
    verification_type: str = Field(default="MACHINE", description="MACHINE or MACHINE_AND_OBSERVATION")
    findings: str = Field(description="Empirical findings from telemetry verification")
    evidence_details: Dict[str, Any] = Field(default_factory=dict)


class TelemetryBreakpoint(BaseModel):
    """Formal telemetry breakpoint recorded during empirical validation."""
    breakpoint_id: str
    stage: str
    description: str
    category: TelemetryCheckCategory
    severity: TelemetrySeverity
    blocking: bool = False
    resolution: Optional[str] = None
    resolution_type: Optional[TelemetryResolutionType] = None
    architecture_change_required: bool = False


class TelemetryReworkEntry(BaseModel):
    """Formal record of adjustments required for telemetry ingestion and failure isolation."""
    rework_id: str
    area: str
    observation: str
    intervention: str
    outcome: str
    repeatable: bool = False


class TelemetryEvidencePackage(BaseModel):
    """
    Complete empirical evidence package from Phase 6 Telemetry Test.
    Records actual Isibusiso S1 E1 event trace and integrity verification.
    """
    package_id: str
    specimen_title: str = "Isibusiso"
    specimen_episode: str = "Episode 1 — The Midnight Sovereign"
    session_id: str
    schema_version: str = "1.0"
    event_taxonomy_spine: List[str] = ["OPEN", "WATCH", "CONTINUE", "REACT", "RETURN", "PAY"]
    deduplication_strategy: str = "Deterministic event_id lookup + (session_id, content_id, milestone) guard"
    failure_isolation_status: str = "VERIFIED_NON_BLOCKING"
    payment_exercise_status: str = "NOT_EXERCISED"
    payment_exercise_reason: str = "Isibusiso S1 E1 is not monetized in this test."
    recorded_event_trace: List[ViewerTelemetryEvent] = Field(default_factory=list)
    integrity_checks: List[TelemetryIntegrityCheckResult] = Field(default_factory=list)
    breakpoint_ledger: List[TelemetryBreakpoint] = Field(default_factory=list)
    rework_ledger: List[TelemetryReworkEntry] = Field(default_factory=list)
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    compiled_at: str
