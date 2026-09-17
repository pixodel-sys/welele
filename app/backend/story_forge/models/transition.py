"""
Welele Story Forge™ — Forge Transition & State Mutation Contracts
Immutable audit record of narrative evolution cycles and state transformations.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone


class SkillEnum(str, Enum):
    EXCAVATOR = "EXCAVATOR"
    CONNECTOR = "CONNECTOR"
    CHALLENGER = "CHALLENGER"
    PROPAGATOR = "PROPAGATOR"
    CONTINUITY_ENGINE = "CONTINUITY_ENGINE"
    PRIORITISER = "PRIORITISER"
    FORGER = "FORGER"
    ORCHESTRATOR = "ORCHESTRATOR"
    FORGE_JUDGE = "FORGE_JUDGE"


class AuthorityMode(str, Enum):
    """
    Creative Authority Principles:
    ASK: Creator ownership is strictly required (return exactly 1 question).
    INFER: Safe and supported inference from canon.
    PROPOSE: Candidate resolution proposed, awaiting creator sign-off.
    RECORD_PRODUCTION_DECISION: Narrative resolved, physical staging deferred.
    STOP: Endpoint or pause state reached.
    """
    ASK = "ASK"
    INFER = "INFER"
    PROPOSE = "PROPOSE"
    RECORD_PRODUCTION_DECISION = "RECORD_PRODUCTION_DECISION"
    STOP = "STOP"


class MutationType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"


class StateMutation(BaseModel):
    mutation_id: str = Field(default_factory=lambda: str(uuid4()))
    target_path: str  # e.g., "characters.Nkosinathi.core_motivation" or "chronology.events"
    old_value: Optional[Any] = None
    new_value: Any
    mutation_type: MutationType = MutationType.UPDATE
    rationale: Optional[str] = None


class Consequence(BaseModel):
    consequence_id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    impacted_entity: str
    derived_mutation: Optional[StateMutation] = None
    new_dependency_detected: Optional[str] = None


class Provenance(BaseModel):
    creator_id: Optional[str] = None
    session_id: Optional[str] = None
    adapter_name: str = "MockReasoningAdapter"
    adapter_version: str = "0.1.0"
    confidence: float = 1.0
    assumptions: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state_version_before: int = 1
    state_version_after: int = 2


class ForgeTransition(BaseModel):
    """
    Immutable audit record for a single Forge cycle.
    Once committed, this record is permanent.
    """
    transition_id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str
    trace_id: str
    sequence: int  # 1-indexed progression in the trace
    creator_input: Optional[str] = None
    interpretation: str
    skill: SkillEnum
    active_dependency_id: Optional[str] = None
    priority_score: Optional[float] = None
    authority_mode: AuthorityMode
    question_asked: Optional[str] = None
    proposal: Optional[str] = None
    creator_response: Optional[str] = None
    state_changes: List[StateMutation] = Field(default_factory=list)
    rejected_mutations: List[StateMutation] = Field(default_factory=list)
    consequences: List[Consequence] = Field(default_factory=list)
    validation_status: str = "VALID"
    validation_errors: List[str] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
