"""
Welele Media™ — Viewer Experience & Validation Models (Phase 5 Empirical Viewer Test)
Data contracts for empirical viewer validation, asset identity chain tracking,
breakpoint recording, rework logging, and the 7 Viewer Experience Checks.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ViewerCheckCategory(str, Enum):
    DISCOVERY_GAP = "DISCOVERY_GAP"
    IDENTITY_GAP = "IDENTITY_GAP"
    MEDIA_GAP = "MEDIA_GAP"
    PLAYBACK_GAP = "PLAYBACK_GAP"
    UI_GAP = "UI_GAP"
    CONTINUATION_GAP = "CONTINUATION_GAP"
    CONTENT_STATE_GAP = "CONTENT_STATE_GAP"
    PERFORMANCE_GAP = "PERFORMANCE_GAP"
    MOBILE_COMPATIBILITY_GAP = "MOBILE_COMPATIBILITY_GAP"
    OTHER = "OTHER"


class ViewerSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


class ViewerResolutionType(str, Enum):
    EXISTING_CONFIGURATION = "EXISTING_CONFIGURATION"
    EXISTING_PRODUCT_DECISION = "EXISTING_PRODUCT_DECISION"
    NEW_PRODUCT_DECISION = "NEW_PRODUCT_DECISION"
    CONTENT_FIX = "CONTENT_FIX"
    PRODUCTION_FIX = "PRODUCTION_FIX"
    ARCHITECTURE_FIX = "ARCHITECTURE_FIX"
    TOOL_WORKAROUND = "TOOL_WORKAROUND"
    DEFERRED = "DEFERRED"


class ViewerBreakpoint(BaseModel):
    """Formal viewer breakpoint recorded during empirical validation."""
    breakpoint_id: str = Field(description="Unique breakpoint identifier, e.g. VBP-01-CONTROLS")
    stage: str = Field(description="Viewer stage: DISCOVERY, IDENTITY, PLAYBACK, HOOK, CLIFFHANGER, CONTINUATION")
    description: str = Field(description="Empirical description of the issue encountered by the viewer")
    category: ViewerCheckCategory
    severity: ViewerSeverity
    blocking: bool = Field(default=False)
    resolution: Optional[str] = Field(default=None, description="Resolution description")
    resolution_type: Optional[ViewerResolutionType] = Field(default=None)
    architecture_change_required: bool = Field(default=False)


class ViewerReworkEntry(BaseModel):
    """Formal record of rework or adjustments required for viewer delivery."""
    rework_id: str = Field(description="Unique rework identifier, e.g. VW-RWK-01")
    area: str = Field(description="Affected area: MOBILE, PLAYER_CONTROLS, CONTINUATION_GATE, UI_LAYOUT")
    observation: str = Field(description="Empirical observation triggering intervention")
    intervention: str = Field(description="Specific adjustment made")
    outcome: str = Field(description="Outcome after intervention")
    repeatable: bool = Field(default=False)


class ViewerExperienceCheckResult(BaseModel):
    """Result of one of the 7 formal Viewer Experience Checks."""
    check_id: str = Field(description="Check number 1-7")
    check_name: str = Field(description="Formal check title")
    status: str = Field(description="PASSED, WARNING, or FAILED")
    verification_type: str = Field(default="MACHINE", description="MACHINE or MACHINE_AND_HUMAN")
    findings: str = Field(description="Empirical findings from viewer observation")
    evidence_details: Dict[str, Any] = Field(default_factory=dict)


class MediaAssetIdentityChain(BaseModel):
    """Authoritative asset identity chain from Episode to delivered media."""
    episode_id: str
    series_id: str
    story_package_id: str
    production_pack_id: str
    media_asset_id: str
    storage_key: str
    delivery_stream_url: str
    content_hash: str
    source_lineage_hash: str
    is_authoritative_master: bool
    is_placeholder: bool = False


class HumanObservationRecord(BaseModel):
    """Genuine record of empirical human viewer observation (not synthesized by machine)."""
    observer_id: str = Field(default="human_observer_01")
    environment: str = Field(description="Desktop Chrome, Android Chrome, iPhone Safari, Mobile-Constrained")
    hesitation_points: List[str] = Field(default_factory=list)
    initial_understanding: str = Field(description="Observer's description of what was happening")
    hook_reaction_notes: str = Field(description="Reaction to royal birthmark reveal within 0-15s")
    cliffhanger_reaction_notes: str = Field(description="Reaction to armed standoff cutoff at second 88")
    continuation_action_taken: str = Field(description="Observed action at episode end")
    continuation_willingness: str = Field(description="Willing / Unwilling / Uncertain / Looked for Ep 2")
    confusing_elements_noted: List[str] = Field(default_factory=list)


class ViewerEvidencePackage(BaseModel):
    """
    Complete empirical evidence package from Phase 5 Viewer Test.
    Combines machine-verifiable validation with genuine human observation.
    """
    package_id: str
    episode_id: str
    series_id: str
    title_display_name: str
    episode_display_title: str
    test_environment: str = Field(default="Welele Web/Mobile Vertical Viewer")
    device_matrix: List[Dict[str, str]] = Field(default_factory=list)
    
    # Core Evidence Artifacts
    media_identity_chain: MediaAssetIdentityChain
    experience_checks: List[ViewerExperienceCheckResult] = Field(default_factory=list)
    breakpoint_ledger: List[ViewerBreakpoint] = Field(default_factory=list)
    rework_ledger: List[ViewerReworkEntry] = Field(default_factory=list)
    
    # Episode 2 Availability Audit
    episode_2_state_behavior: Dict[str, Any] = Field(default_factory=dict)
    
    # Human Viewer Observation
    human_observations: List[HumanObservationRecord] = Field(default_factory=list)
    
    # Summary
    overall_status: str = Field(default="VIEWER_VALIDATION_COMPLETED")
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    compiled_at: str
