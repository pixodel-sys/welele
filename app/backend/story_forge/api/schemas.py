"""
Welele Story Forge™ — Application-Facing API Schemas v0.1
Defines stable Request/Response DTOs for Headless Harness and Creator UI clients.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    ChronologyEvent,
    ProductionDecision,
    ForgeCompletionAssessment,
    AuthorityMode,
    SkillEnum
)


# --- Story DTOs ---

class CreateStoryRequest(BaseModel):
    story_id: Optional[str] = None
    title: str
    owner_id: str
    digital_ip_id: Optional[str] = None
    logline: Optional[str] = None
    primary_language: str = "isiZulu"


class StorySummaryResponse(BaseModel):
    id: str
    title: str
    owner_id: str
    digital_ip_id: Optional[str] = None
    logline: Optional[str] = None
    primary_language: str
    status: str
    current_state_version: int


# --- Session DTOs ---

class StartSessionRequest(BaseModel):
    creator_id: str
    session_id: Optional[str] = None
    initial_premise: Optional[str] = None
    creative_objective: Optional[str] = None
    production_objective: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    story_id: str
    creator_id: str
    session_status: str
    active_trace_id: str
    current_action: AuthorityMode
    current_question: Optional[str] = None
    active_dependency_id: Optional[str] = None
    state_version: int
    created_at: str
    updated_at: str


class SubmitInputRequest(BaseModel):
    creator_input: Optional[str] = None
    creator_response: Optional[str] = None
    proposal_action: Optional[str] = Field(default=None, description="ACCEPT, REJECT, or MODIFY for PROPOSE authority mode")
    event_headline: Optional[str] = None
    event_description: Optional[str] = None
    participants: List[str] = Field(default_factory=list)


class CurrentActionResponse(BaseModel):
    session_id: str
    story_id: str
    state_version: int
    action: AuthorityMode
    skill: SkillEnum
    question: Optional[str] = None
    proposal: Optional[str] = None
    active_dependency_key: Optional[str] = None
    active_dependency_description: Optional[str] = None
    unresolved_dependencies_count: int
    is_paused: bool = False
    requires_creator: bool = False


class ForgeCycleResponse(BaseModel):
    story_id: str
    session_id: str
    state_version: int
    action: AuthorityMode
    active_question: Optional[str] = None
    transition: ForgeTransition
    current_state: StoryState
    unresolved_dependencies_count: int


class IntelligenceProjectionResponse(BaseModel):
    story_id: str
    state_version: int
    current_milestone: Optional[str] = None
    target_milestone: str
    satisfied_milestones: List[str]
    readiness_status: str
    core_understanding: Dict[str, Any]
    strengths: List[str]
    unresolved_risks: List[str]
    missing_invariants: List[str]
    next_needed_decisions: List[Dict[str, Any]]
    total_dependencies: int
    resolved_dependencies_count: int
