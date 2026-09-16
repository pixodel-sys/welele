"""
Welele Story Forge™ — Dependency Engine Domain Models
First-class control objects for tracking unresolved narrative requirements.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone


class DependencyType(str, Enum):
    NARRATIVE = "NARRATIVE"
    CHARACTER = "CHARACTER"
    CAUSAL = "CAUSAL"
    TEMPORAL = "TEMPORAL"
    KNOWLEDGE = "KNOWLEDGE"
    PRODUCTION = "PRODUCTION"
    CANON = "CANON"


class DependencyStatus(str, Enum):
    DETECTED = "DETECTED"
    ASSESSED = "ASSESSED"
    PRIORITISED = "PRIORITISED"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    DELIBERATELY_UNKNOWN = "DELIBERATELY_UNKNOWN"
    DEFERRED = "DEFERRED"


class PriorityWeights(BaseModel):
    weight_impact: float = 1.0
    weight_urgency: float = 1.0
    weight_risk: float = 1.0
    weight_leverage: float = 1.0
    weight_cost: float = 1.0


class PriorityComponents(BaseModel):
    impact: int = Field(default=5, ge=1, le=10, description="Narrative disruption or magnitude")
    urgency: int = Field(default=5, ge=1, le=10, description="Blocks immediate story progression")
    risk: int = Field(default=5, ge=1, le=10, description="Contradiction or continuity hazard")
    leverage: int = Field(default=5, ge=1, le=10, description="Unlocks downstream dependencies")
    cost: int = Field(default=2, ge=1, le=10, description="Cognitive or complexity burden")


class Dependency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str
    dependency_key: str  # Unique slug, e.g. "CHAR_MOTIVATION_NKOSINATHI"
    dependency_type: DependencyType
    status: DependencyStatus = DependencyStatus.DETECTED
    target_entity: str  # e.g. "Nkosinathi" or "Event #1"
    description: str
    components: PriorityComponents = Field(default_factory=PriorityComponents)
    priority_score: float = 0.0
    priority_rationale: Optional[str] = None
    suggested_skill: str = "EXCAVATOR"
    resolved_by_transition_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DependencyAssessment(BaseModel):
    dependency_id: str
    components: PriorityComponents
    calculated_score: float
    rationale: str
    recommended_skill: str
