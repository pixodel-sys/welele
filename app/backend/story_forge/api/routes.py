"""
Welele Story Forge™ — Application API Boundary
Decoupled narrative engine endpoints for Headless Harness and Creator UI.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends
from .schemas import (
    CreateStoryRequest,
    StorySummaryResponse,
    StartSessionRequest,
    SessionResponse,
    SubmitInputRequest,
    CurrentActionResponse,
    ForgeCycleResponse,
    IntelligenceProjectionResponse
)
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    DependencyStatus,
    ChronologyEvent,
    ProductionDecision,
    ForgeCompletionAssessment,
    MilestoneEnum,
    AuthorityMode,
    SkillEnum
)
from ..repository import InMemoryStoryForgeRepository, StoryForgeRepository
from ..orchestrator import StoryForgeKernel, ForgeJudge
from ..adapters import LLMReasoningAdapter, HttpLLMProvider, MockReasoningAdapter

logger = logging.getLogger("welele.story_forge.api")
router = APIRouter(prefix="/forge", tags=["Story Forge Narrative Engine"])

# Global shared repository instance for application lifecycle
_repo: StoryForgeRepository = InMemoryStoryForgeRepository()


def _get_configured_adapter():
    """
    Returns the reasoning adapter for the Kernel.
    In testing / mock mode: uses MockReasoningAdapter.
    In live application: strictly requires real HttpLLMProvider (Gemini);
    fails fast if provider is unconfigured.
    """
    if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("STORY_FORGE_USE_MOCK_ADAPTER", "0").lower() in ("1", "true"):
        return MockReasoningAdapter()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured for live Story Forge.")
        raise HTTPException(
            status_code=503,
            detail="Story Forge Live Provider unavailable: GEMINI_API_KEY is not configured in environment."
        )

    try:
        provider = HttpLLMProvider()
        return LLMReasoningAdapter(provider=provider, temperature=0.2)
    except Exception as err:
        logger.error("HttpLLMProvider initialization failed: %s", err)
        raise HTTPException(
            status_code=503,
            detail=f"Story Forge Live Provider failed to initialize: {err}"
        )


def get_repository() -> StoryForgeRepository:
    return _repo


def get_kernel(repo: StoryForgeRepository = Depends(get_repository)) -> StoryForgeKernel:
    adapter = _get_configured_adapter()
    return StoryForgeKernel(repository=repo, reasoning_adapter=adapter)


def get_judge(repo: StoryForgeRepository = Depends(get_repository)) -> ForgeJudge:
    return ForgeJudge(repository=repo)


# -----------------------------------------------------------------------------
# 1. Story Lifecycle Endpoints
# -----------------------------------------------------------------------------

@router.post("/stories", response_model=StoryState)
def create_forge_story(
    req: CreateStoryRequest,
    repo: StoryForgeRepository = Depends(get_repository)
):
    story_id = req.story_id or str(uuid4())
    state = repo.create_story(
        story_id=story_id,
        title=req.title,
        owner_id=req.owner_id,
        digital_ip_id=req.digital_ip_id,
        logline=req.logline,
        primary_language=req.primary_language
    )
    return state


@router.get("/stories", response_model=List[StorySummaryResponse])
def list_forge_stories(
    repo: StoryForgeRepository = Depends(get_repository)
):
    stories = repo.list_stories()
    return [StorySummaryResponse(**s) for s in stories]


@router.get("/stories/{story_id}", response_model=StorySummaryResponse)
def get_story_summary(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    story = repo.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")
    return StorySummaryResponse(**story)


@router.get("/stories/{story_id}/state", response_model=StoryState)
def get_current_story_state(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    state = repo.get_current_state(story_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' state not found")
    return state


@router.get("/stories/{story_id}/dependencies", response_model=List[Dependency])
def list_story_dependencies(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    return repo.get_dependencies(story_id)


@router.get("/stories/{story_id}/trace", response_model=List[ForgeTransition])
def get_story_trace(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    return repo.get_transitions(story_id)


@router.get("/stories/{story_id}/completion", response_model=ForgeCompletionAssessment)
@router.post("/stories/{story_id}/completion-assessment", response_model=ForgeCompletionAssessment)
def get_or_assess_completion(
    story_id: str,
    judge: ForgeJudge = Depends(get_judge)
):
    try:
        return judge.assess(story_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stories/{story_id}/intelligence", response_model=IntelligenceProjectionResponse)
def get_story_intelligence(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository),
    judge: ForgeJudge = Depends(get_judge)
):
    """
    Projects grounded story intelligence directly from canonical state, dependencies,
    and Judge invariants. Zero secondary LLM hallucination.
    """
    state = repo.get_current_state(story_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    assessment = judge.assess(story_id)
    deps = repo.get_dependencies(story_id)
    events = repo.get_events(story_id)
    prod_decisions = repo.get_production_decisions(story_id)

    unresolved_deps = [
        d for d in deps
        if d.status not in (DependencyStatus.RESOLVED, DependencyStatus.DELIBERATELY_UNKNOWN, DependencyStatus.DEFERRED)
    ]
    resolved_count = len(deps) - len(unresolved_deps)

    protagonists = [c.name for c in state.characters.values() if c.role.value == "PROTAGONIST"]
    antagonists = [c.name for c in state.characters.values() if c.role.value == "ANTAGONIST"]
    supporting = [c.name for c in state.characters.values() if c.role.value not in ("PROTAGONIST", "ANTAGONIST")]

    core_understanding = {
        "title": state.title,
        "logline": state.logline,
        "protagonists": protagonists,
        "antagonists": antagonists,
        "supporting_characters": supporting,
        "chronology_anchors_count": len(events),
        "narrative_plants_count": len(state.plants),
        "production_decisions_count": len(prod_decisions),
    }

    strengths: List[str] = []
    if MilestoneEnum.M0_PREMISE_LOCK in assessment.satisfied_milestones:
        strengths.append("Premise locked: Core story premise and logline are canonically defined.")
    if MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK in assessment.satisfied_milestones:
        strengths.append("Dramatic engine locked: Core protagonist motivation and opposing counterforce are established.")
    if len(events) >= 6:
        strengths.append("Episodic spine complete: All 6 canonical chronology anchors are sequenced.")
    elif len(events) > 0:
        strengths.append(f"Chronology spine progressing: {len(events)} of 6 canonical anchors committed.")
    if len(state.plants) > 0:
        strengths.append(f"Narrative plants active: {len(state.plants)} physical props/secrets anchored in canon.")

    unresolved_risks: List[str] = []
    for inv in assessment.missing_invariants:
        if "COUNTERFORCE" in inv:
            unresolved_risks.append("Missing counterforce: Opposing force or rival entity is undefined in canon.")
        elif "PROTAGONIST_MOTIVATION" in inv:
            unresolved_risks.append("Undefined protagonist motivation: Protagonist lacks a clear dramatic driving goal.")
        elif "SIX_CHRONOLOGY" in inv:
            unresolved_risks.append(f"Incomplete episodic arc: Spine requires 6 anchors (currently {len(events)}/6).")
        elif "RELATIONSHIP" in inv:
            unresolved_risks.append("Relational tension unmapped: Conflict dynamics between core characters are unestablished.")
        elif "WORLD_RULES" in inv:
            unresolved_risks.append("Supernatural/world mechanics unanchored: Rules governing arena consequences are missing.")

    for dep in unresolved_deps[:3]:
        unresolved_risks.append(f"Open dependency [{dep.dependency_type.value}]: {dep.description}")

    next_needed: List[Dict[str, Any]] = []
    for dep in unresolved_deps[:5]:
        next_needed.append({
            "dependency_id": dep.id,
            "key": dep.dependency_key,
            "type": dep.dependency_type.value,
            "target": dep.target_entity,
            "description": dep.description,
            "priority_score": dep.priority_score,
            "suggested_skill": dep.suggested_skill
        })

    return IntelligenceProjectionResponse(
        story_id=story_id,
        state_version=state.state_version,
        current_milestone=assessment.current_milestone.value if assessment.current_milestone else None,
        target_milestone=assessment.target_milestone.value,
        satisfied_milestones=[m.value for m in assessment.satisfied_milestones],
        readiness_status=assessment.status.value,
        core_understanding=core_understanding,
        strengths=strengths,
        unresolved_risks=unresolved_risks,
        missing_invariants=assessment.missing_invariants,
        next_needed_decisions=next_needed,
        total_dependencies=len(deps),
        resolved_dependencies_count=resolved_count
    )


# -----------------------------------------------------------------------------
# 2. Session Lifecycle & Interactive Input Endpoints
# -----------------------------------------------------------------------------

@router.post("/stories/{story_id}/sessions", response_model=SessionResponse)
def start_forge_session(
    story_id: str,
    req: StartSessionRequest,
    repo: StoryForgeRepository = Depends(get_repository),
    kernel: StoryForgeKernel = Depends(get_kernel)
):
    state = repo.get_current_state(story_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    session = repo.create_session(
        story_id=story_id,
        creator_id=req.creator_id,
        session_id=req.session_id
    )

    # Ingest raw premise if provided upon session start
    if req.initial_premise:
        transition, new_state, q = kernel.process_cycle(
            story_id=story_id,
            session_id=session["id"],
            trace_id=session["active_trace_id"],
            creator_input=req.initial_premise
        )
        repo.update_session(session["id"], {
            "current_action": transition.authority_mode.value,
            "current_question": q,
            "current_proposal": transition.proposal,
            "active_dependency_id": transition.active_dependency_id
        })
        session = repo.get_session(session["id"])

    curr_state = repo.get_current_state(story_id)
    return SessionResponse(
        id=session["id"],
        story_id=session["story_id"],
        creator_id=session["creator_id"],
        session_status=session["session_status"],
        active_trace_id=session["active_trace_id"],
        current_action=AuthorityMode(session.get("current_action", "ASK")),
        current_question=session.get("current_question"),
        active_dependency_id=session.get("active_dependency_id"),
        state_version=curr_state.state_version if curr_state else 1,
        created_at=session["created_at"],
        updated_at=session["updated_at"]
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session_status(
    session_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    story_id = session["story_id"]
    curr_state = repo.get_current_state(story_id)

    return SessionResponse(
        id=session["id"],
        story_id=session["story_id"],
        creator_id=session["creator_id"],
        session_status=session["session_status"],
        active_trace_id=session["active_trace_id"],
        current_action=AuthorityMode(session.get("current_action", "ASK")),
        current_question=session.get("current_question"),
        active_dependency_id=session.get("active_dependency_id"),
        state_version=curr_state.state_version if curr_state else 1,
        created_at=session["created_at"],
        updated_at=session["updated_at"]
    )


@router.get("/sessions/{session_id}/current", response_model=CurrentActionResponse)
def get_current_action(
    session_id: str,
    repo: StoryForgeRepository = Depends(get_repository)
):
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    story_id = session["story_id"]
    state = repo.get_current_state(story_id)
    deps = repo.get_dependencies(story_id)

    unresolved = [
        d for d in deps
        if d.status.value in ("DETECTED", "ACTIVE", "ASSESSED", "PRIORITISED")
    ]

    action = AuthorityMode(session.get("current_action", "ASK"))
    question = session.get("current_question")
    proposal = session.get("current_proposal")

    active_dep = None
    if session.get("active_dependency_id"):
        for d in deps:
            if d.id == session["active_dependency_id"]:
                active_dep = d
                break

    return CurrentActionResponse(
        session_id=session_id,
        story_id=story_id,
        state_version=state.state_version if state else 1,
        action=action,
        skill=SkillEnum(active_dep.suggested_skill) if active_dep and active_dep.suggested_skill in [s.value for s in SkillEnum] else SkillEnum.EXCAVATOR,
        question=question,
        proposal=proposal,
        active_dependency_key=active_dep.dependency_key if active_dep else None,
        active_dependency_description=active_dep.description if active_dep else None,
        unresolved_dependencies_count=len(unresolved),
        is_paused=session.get("session_status") == "PAUSED",
        requires_creator=(action in (AuthorityMode.ASK, AuthorityMode.PROPOSE))
    )


@router.post("/sessions/{session_id}/input", response_model=ForgeCycleResponse)
def submit_session_input(
    session_id: str,
    req: SubmitInputRequest,
    repo: StoryForgeRepository = Depends(get_repository),
    kernel: StoryForgeKernel = Depends(get_kernel)
):
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    story_id = session["story_id"]
    trace_id = session["active_trace_id"]

    new_events = []
    if req.event_headline:
        new_events.append(
            ChronologyEvent(
                story_id=story_id,
                event_sequence=len(repo.get_events(story_id)) + 1,
                headline=req.event_headline,
                description=req.event_description or req.event_headline,
                participants=req.participants
            )
        )

    # Process explicit proposal decisions (ACCEPT, REJECT, MODIFY)
    creator_resp = req.creator_response
    if req.proposal_action == "ACCEPT":
        creator_resp = creator_resp or "Accepted proposal by creator."
    elif req.proposal_action == "REJECT":
        creator_resp = creator_resp or "Proposal rejected by creator. Please re-evaluate alternative narrative direction."

    transition, new_state, next_question = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input=req.creator_input,
        creator_response=creator_resp,
        new_events=new_events
    )

    repo.update_session(session_id, {
        "current_action": transition.authority_mode.value,
        "current_question": next_question,
        "current_proposal": transition.proposal,
        "active_dependency_id": transition.active_dependency_id
    })

    deps = repo.get_dependencies(story_id)
    unresolved = len([
        d for d in deps
        if d.status.value in ("DETECTED", "ACTIVE", "ASSESSED", "PRIORITISED")
    ])

    return ForgeCycleResponse(
        story_id=story_id,
        session_id=session_id,
        state_version=new_state.state_version,
        action=transition.authority_mode,
        active_question=next_question,
        transition=transition,
        current_state=new_state,
        unresolved_dependencies_count=unresolved
    )
