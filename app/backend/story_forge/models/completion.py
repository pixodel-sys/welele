"""
Welele Story Forge™ — Completion & Production Decision Models
Boundary definitions between completed narrative architecture and deferred physical production.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone


class ProductionAspect(str, Enum):
    LOCATION = "LOCATION"
    STUNT = "STUNT"
    CASTING = "CASTING"
    CHOREOGRAPHY = "CHOREOGRAPHY"
    VFX = "VFX"
    BUDGET_TIER = "BUDGET_TIER"
    SOUND = "SOUND"


class ProductionDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str
    decision_key: str
    narrative_resolution: str
    production_aspect: ProductionAspect
    deferred_details: str
    status: str = "RECORDED"  # RECORDED, COMMITTED, RESOLVED_IN_PREPROD
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MilestoneEnum(str, Enum):
    M0_PREMISE_LOCK = "PREMISE_LOCK"
    M1_DRAMATIC_ENGINE_LOCK = "DRAMATIC_ENGINE_LOCK"
    M2_EPISODIC_ARC_LOCK = "EPISODIC_ARC_LOCK"
    M3_FORGE_COMPLETE = "FORGE_COMPLETE"


class ReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    PREMISE_LOCK = "PREMISE_LOCK"
    DRAMATIC_ENGINE_LOCK = "DRAMATIC_ENGINE_LOCK"
    EPISODIC_ARC_LOCK = "EPISODIC_ARC_LOCK"
    DEPENDENCIES_RESOLVED = "DEPENDENCIES_RESOLVED"
    FORGE_COMPLETE = "FORGE_COMPLETE"


class ForgeCompletionAssessment(BaseModel):
    """
    Evaluation standard (Completion Contract v0.2):
    If this Story Package were handed to a competent production team tomorrow,
    is there any unresolved narrative, structural, continuity or production-critical
    dependency that would force them to invent a story decision?
    """
    assessment_id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str
    assessed_state_version: int
    status: ReadinessStatus
    current_milestone: Optional[MilestoneEnum] = None
    target_milestone: MilestoneEnum = MilestoneEnum.M3_FORGE_COMPLETE
    satisfied_milestones: List[MilestoneEnum] = Field(default_factory=list)
    missing_invariants: List[str] = Field(default_factory=list)
    synthesized_dependencies: List[str] = Field(default_factory=list)
    unresolved_narrative_count: int = 0
    unresolved_causal_count: int = 0
    unresolved_temporal_count: int = 0
    production_decisions_count: int = 0
    blocking_dependencies: List[str] = Field(default_factory=list)
    assessment_notes: Optional[str] = None
    assessed_by: str = "FORGE_JUDGE"
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
