"""
Welele Story Forge™ — Reasoning Adapter Contracts v0.1
Defines structured ReasoningRequest and ReasoningDecision models.
Enforces the boundary: 'The Adapter reasons. The Kernel governs.'
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Protocol
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
from ..models import (
    SkillEnum,
    AuthorityMode,
    StateMutation,
    ProductionDecision,
    CharacterRole,
    StateStatus,
    KnowledgeStatus
)


class ForgeObjective(str, Enum):
    RESOLVE_DEPENDENCY = "RESOLVE_DEPENDENCY"
    INTERPRET_INPUT = "INTERPRET_INPUT"
    ASSESS_COMPLETION = "ASSESS_COMPLETION"
    DISCOVER_PLANTS = "DISCOVER_PLANTS"


# --- Context Slices (Assembled deliberately by the Kernel, preventing whole-database dumps) ---

class StoryContext(BaseModel):
    story_id: str
    title: str
    logline: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None


class DependencyContext(BaseModel):
    id: str
    dependency_key: str
    dependency_type: str
    target_entity: str
    description: str
    status: str
    priority_score: float
    suggested_skill: str


class EntityContext(BaseModel):
    name: str
    role: str
    status: str
    core_motivation: Optional[str] = None
    secret_desire: Optional[str] = None
    fatal_flaw: Optional[str] = None
    relationships: List[Dict[str, Any]] = Field(default_factory=list)


class EventContext(BaseModel):
    event_sequence: int
    story_time: Optional[str] = None
    headline: str
    description: str
    participants: List[str] = Field(default_factory=list)
    location: Optional[str] = None


class KnowledgeContext(BaseModel):
    character_name: str
    fact_key: str
    status: str
    confidence: float = 1.0


class PlantContext(BaseModel):
    element_code: str
    description: str
    intended_payoff: str
    payoff_status: str


# --- Structured Reasoning Request ---

class ReasoningRequest(BaseModel):
    """
    Context assembly supplied by the Kernel to the Reasoning Adapter.
    Contains ONLY the context necessary for the reasoning task.
    """
    story_id: str
    state_version: int
    story_context: StoryContext
    active_dependency: Optional[DependencyContext] = None
    relevant_entities: List[EntityContext] = Field(default_factory=list)
    relevant_events: List[EventContext] = Field(default_factory=list)
    relevant_knowledge: List[KnowledgeContext] = Field(default_factory=list)
    relevant_plants: List[PlantContext] = Field(default_factory=list)
    available_skills: List[SkillEnum] = Field(default_factory=lambda: list(SkillEnum))
    allowed_authority_modes: List[AuthorityMode] = Field(default_factory=lambda: list(AuthorityMode))
    objective: ForgeObjective = ForgeObjective.RESOLVE_DEPENDENCY
    creator_input: Optional[str] = None
    creator_response: Optional[str] = None
    request_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- Structured Reasoning Decision ---

class ReasoningDecision(BaseModel):
    """
    Structured outcome returned by the Reasoning Adapter.
    Treated strictly as untrusted advice/proposals until validated and committed by the Kernel.
    """
    action: AuthorityMode
    dependency_id: Optional[str] = None
    skill: SkillEnum
    question: Optional[str] = None
    proposal: Optional[str] = None
    proposed_mutations: List[StateMutation] = Field(default_factory=list)
    production_decision: Optional[ProductionDecision] = None
    rationale: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Advisory confidence metadata only; not operational")
    requires_creator: bool = False
    assumptions: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    adapter_name: str = "MockReasoningAdapter"
    adapter_version: str = "0.1.0"

    @model_validator(mode="after")
    def validate_action_semantics(self):
        """
        Enforces semantic contract rules per action type.
        """
        act = self.action

        if act == AuthorityMode.ASK:
            if not self.question or not self.question.strip():
                raise ValueError("When action is ASK, exactly one non-empty primary question must be formulated.")
            if not self.requires_creator:
                raise ValueError("When action is ASK, requires_creator must be True.")

        elif act == AuthorityMode.INFER:
            if self.question and self.question.strip():
                raise ValueError("When action is INFER, question must be None (creator question is not permitted).")
            if self.requires_creator:
                raise ValueError("When action is INFER, requires_creator must be False.")

        elif act == AuthorityMode.PROPOSE:
            if not self.proposal and not self.proposed_mutations:
                raise ValueError("When action is PROPOSE, a proposal or proposed mutations must be provided.")
            if not self.requires_creator:
                raise ValueError("When action is PROPOSE, requires_creator must be True for creator sign-off.")

        elif act == AuthorityMode.RECORD_PRODUCTION_DECISION:
            if self.question and self.question.strip():
                raise ValueError("When action is RECORD_PRODUCTION_DECISION, question must be None.")
            if not self.production_decision:
                raise ValueError("When action is RECORD_PRODUCTION_DECISION, production_decision payload is required.")

        elif act == AuthorityMode.STOP:
            if self.question and self.question.strip():
                raise ValueError("When action is STOP, question must be None.")
            if self.requires_creator:
                raise ValueError("When action is STOP, requires_creator must be False.")

        return self


# --- Protocol Contract ---

class ReasoningAdapter(Protocol):
    """
    Core reasoning contract.
    The adapter receives a structured request and returns a structured decision.
    Zero direct access to database, filesystem, or state mutation.
    """
    def reason(self, request: ReasoningRequest) -> ReasoningDecision:
        ...
