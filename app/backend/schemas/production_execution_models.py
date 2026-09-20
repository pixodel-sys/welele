"""
Welele Media™ — Production Execution & Evidence Models (Phase 4 Empirical Production Test)
Data contracts for empirical production execution, breakpoint tracking, rework recording,
and the 10 Production Integrity Checks.
"""

from enum import Enum
import hashlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BreakpointCategory(str, Enum):
    INFORMATION_GAP = "INFORMATION_GAP"
    TRANSLATION_GAP = "TRANSLATION_GAP"
    CONTINUITY_GAP = "CONTINUITY_GAP"
    PRODUCTION_GAP = "PRODUCTION_GAP"
    TOOL_GAP = "TOOL_GAP"


class BreakpointSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BLOCKING = "BLOCKING"


class ResolutionType(str, Enum):
    EXISTING_CANON = "EXISTING_CANON"
    EXISTING_PRODUCTION_DECISION = "EXISTING_PRODUCTION_DECISION"
    NEW_PRODUCTION_DECISION = "NEW_PRODUCTION_DECISION"
    MANUAL_PRODUCTION_WORK = "MANUAL_PRODUCTION_WORK"
    ARCHITECTURE_FIX = "ARCHITECTURE_FIX"
    TOOL_WORKAROUND = "TOOL_WORKAROUND"
    DEFERRED = "DEFERRED"


class ProductionBreakpoint(BaseModel):
    """Formal production breakpoint recorded during empirical execution."""
    breakpoint_id: str = Field(description="Unique breakpoint identifier, e.g. bp_01_foley")
    production_unit: str = Field(description="Referenced production unit, e.g. unit_ep1_01")
    track: str = Field(description="Track affected: VIDEO, DIALOGUE, NARRATION, AMBIENCE, MUSIC, ASSEMBLY")
    description: str = Field(description="Empirical description of the issue or gap encountered")
    category: BreakpointCategory
    source_reference: str = Field(description="Upstream source reference path")
    severity: BreakpointSeverity
    blocking: bool = Field(default=False)
    resolution: Optional[str] = Field(default=None, description="Resolution description")
    resolution_type: Optional[ResolutionType] = Field(default=None)
    architecture_change_required: bool = Field(default=False)


class ProductionReworkEntry(BaseModel):
    """Formal record of rework required during production execution."""
    rework_id: str = Field(description="Unique rework identifier, e.g. rwk_ep1_01")
    unit_id: str = Field(description="Affected production unit")
    track: str = Field(description="Affected track")
    reason: str = Field(description="Reason why initial production output required rework")
    origin: str = Field(description="Origin: SPECIFICATION_GAP, TOOL_LIMITATION, CREATIVE_POLISH")
    effort_description: str = Field(description="Effort or time spent on rework")
    result: str = Field(description="Outcome after rework")
    repeatable: bool = Field(default=False, description="Whether this issue is expected to repeat across episodes")


class UnitSufficiencyStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    SUFFICIENT_WITH_PRODUCTION_DECISION = "SUFFICIENT_WITH_PRODUCTION_DECISION"
    INSUFFICIENT = "INSUFFICIENT"
    BLOCKED = "BLOCKED"


class UnitSufficiencyEvaluation(BaseModel):
    """Evaluation of an individual unit's production sufficiency."""
    unit_id: str
    sequence: int
    status: UnitSufficiencyStatus
    track_readiness: Dict[str, str] = Field(default_factory=dict)
    production_decisions_required: List[str] = Field(default_factory=list)
    notes: str = Field(default="")


class ProductionIntegrityCheckResult(BaseModel):
    """Result of one of the 10 Production Integrity Checks."""
    check_id: str = Field(description="Check number 1-10")
    check_name: str = Field(description="Formal check title")
    status: str = Field(description="PASSED, WARNING, or FAILED")
    findings: str = Field(description="Empirical findings from production observation")
    evidence_details: Dict[str, Any] = Field(default_factory=dict)


class AssembledUnitMaster(BaseModel):
    """Assembled assets and mix parameters for an executed unit."""
    unit_id: str
    sequence: int
    duration_seconds: int
    video_asset_spec: Dict[str, Any]
    dialogue_mix_spec: Dict[str, Any]
    narration_mix_spec: Optional[Dict[str, Any]] = None
    ambience_mix_spec: Dict[str, Any]
    music_mix_spec: Dict[str, Any]
    sync_status: str = Field(default="SYNCHRONIZED")


class EpisodeMasterManifest(BaseModel):
    """Complete manifest of the assembled episode master."""
    manifest_id: str
    episode_id: str
    series_id: str
    story_package_id: str
    blueprint_id: str
    production_pack_id: str
    aspect_ratio: str = Field(default="9:16 Vertical (1080x1920)")
    total_duration_seconds: int
    total_units_executed: int
    assembled_units: List[AssembledUnitMaster] = Field(default_factory=list)
    overall_production_status: str = Field(default="PRODUCTION_TEST_COMPLETED")
    assembled_at: str


class Phase4EvidencePackage(BaseModel):
    """
    Complete empirical evidence package from Phase 4 production test.
    """
    package_id: str
    episode_id: str
    series_id: str
    production_status: str = Field(default="PRODUCTION_TEST_COMPLETED")
    
    # Core Empirical Evidence Artifacts
    master_manifest: EpisodeMasterManifest
    breakpoint_ledger: List[ProductionBreakpoint] = Field(default_factory=list)
    rework_ledger: List[ProductionReworkEntry] = Field(default_factory=list)
    unit_sufficiency_reports: List[UnitSufficiencyEvaluation] = Field(default_factory=list)
    production_integrity_checks: List[ProductionIntegrityCheckResult] = Field(default_factory=list)
    
    # Statistical Summary
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    architecture_findings: List[str] = Field(default_factory=list)
    compiled_at: str
