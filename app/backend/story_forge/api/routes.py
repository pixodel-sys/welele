"""
Welele Story Forge™ — Application API Boundary
Decoupled narrative engine endpoints for Headless Harness and Creator UI.
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Depends, Response
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
    ReadinessStatus,
    AuthorityMode,
    SkillEnum,
    StoryPackageArtifact
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


def get_collaborative_director():
    from ..collaborative.director import CollaborativeStoryDirector
    from ..collaborative.mock_director import MockCollaborativeDirector

    if "PYTEST_CURRENT_TEST" in os.environ or os.getenv("STORY_FORGE_USE_MOCK_ADAPTER", "0").lower() in ("1", "true"):
        return MockCollaborativeDirector()

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("STORY_FORGE_LLM_API_KEY")
    if not api_key:
        return MockCollaborativeDirector()

    try:
        provider = HttpLLMProvider()
        return CollaborativeStoryDirector(provider=provider, temperature=0.3)
    except Exception as err:
        logger.warning("HttpLLMProvider initialization failed (%s); using MockCollaborativeDirector.", err)
        return MockCollaborativeDirector()


def get_collaborative_loop(
    repo: StoryForgeRepository = Depends(get_repository),
    director = Depends(get_collaborative_director)
):
    from ..collaborative.loop import CollaborativeForgeLoop
    return CollaborativeForgeLoop(repository=repo, director=director)


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


@router.get("/stories/{story_id}/package", response_model=StoryPackageArtifact)
def get_story_package(
    story_id: str,
    repo: StoryForgeRepository = Depends(get_repository),
    judge: ForgeJudge = Depends(get_judge)
):
    """
    Authoritative Story Package compiler.
    Transforms canonical Kernel state, events, and ForgeJudge assessment into a versioned StoryPackageArtifact.
    """
    state = repo.get_current_state(story_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' state not found")

    assessment = judge.assess(story_id)
    events = state.chronology if (hasattr(state, "chronology") and state.chronology) else repo.get_events(story_id)
    prod_decisions = repo.get_production_decisions(story_id)

    characters_list = [
        {
            "character_id": c.character_id,
            "name": c.name,
            "aliases": c.aliases,
            "role": c.role.value if hasattr(c.role, "value") else str(c.role),
            "archetype": c.archetype,
            "core_motivation": c.core_motivation,
            "secret_desire": c.secret_desire,
            "fatal_flaw": c.fatal_flaw,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "relationships": [
                {
                    "target_character": r.target_character,
                    "relation_type": r.relation_type,
                    "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "dynamic": r.dynamic,
                    "tension_level": r.tension_level
                }
                for r in c.relationships
            ],
            "attributes": c.attributes
        }
        for c in state.characters.values()
    ]

    world_dict = {
        "primary_location": state.world.primary_location,
        "geography": state.world.geography,
        "rules_and_lore": state.world.rules_and_lore,
        "cultural_context": state.world.cultural_context
    }

    chronology_spine = [
        {
            "event_id": getattr(e, "event_id", str(uuid4())),
            "event_sequence": getattr(e, "event_sequence", idx + 1),
            "anchor_type": getattr(e, "anchor_type", "EVENT_PROGRESSION"),
            "headline": getattr(e, "headline", ""),
            "description": getattr(e, "description", ""),
            "participants": getattr(e, "participants", []),
            "event_status": getattr(e, "event_status", "FACT").value if hasattr(getattr(e, "event_status", "FACT"), "value") else str(getattr(e, "event_status", "FACT"))
        }
        for idx, e in enumerate(events)
    ]

    plants_list = [
        {
            "element_code": p.element_code,
            "plant_name": getattr(p, "plant_name", None) or p.element_code,
            "description": p.description,
            "intended_payoff": p.intended_payoff,
            "payoff_status": p.payoff_status
        }
        for p in state.plants
    ]

    knowledge_list = [
        {
            "character_name": k.character_name,
            "fact_key": k.fact_key,
            "status": k.status.value if hasattr(k.status, "value") else str(k.status),
            "confidence": k.confidence
        }
        for k in state.knowledge_states
    ]

    prod_decisions_list = [
        {
            "decision_id": pd.decision_id,
            "decision_key": pd.decision_key,
            "narrative_resolution": pd.narrative_resolution,
            "production_aspect": pd.production_aspect.value if hasattr(pd.production_aspect, "value") else str(pd.production_aspect),
            "deferred_details": pd.deferred_details,
            "status": pd.status
        }
        for pd in prod_decisions
    ]

    return StoryPackageArtifact(
        story_package_version="0.2.0",
        story_id=story_id,
        title=state.title,
        logline=state.logline or "",
        milestone=assessment.current_milestone or MilestoneEnum.M0_PREMISE_LOCK,
        readiness_status=assessment.status,
        state_version=state.state_version,
        characters=characters_list,
        world=world_dict,
        chronology_spine=chronology_spine,
        narrative_plants=plants_list,
        knowledge_states=knowledge_list,
        production_decisions=prod_decisions_list,
        assessment=assessment
    )


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

def validate_story_document_context(raw_text: str) -> None:
    """
    Architectural Rule: No unvalidated external material crosses the Document Context boundary into Story Reasoning.
    Validates that external document context is strictly plain text or Markdown, and rejects binary signatures,
    container formats (DOCX/ZIP, PDF, RTF), and null-byte corrupted content.
    """
    if not raw_text:
        return

    text_strip = raw_text.strip()
    raw_bytes = raw_text.encode("utf-8", errors="replace")

    # 1. Reject binary container signatures
    # ZIP / DOCX / OpenXML
    if (
        text_strip.startswith("PK\x03\x04")
        or text_strip.startswith("PK\x05\x06")
        or text_strip.startswith("PK\x07\x08")
        or text_strip.startswith(r"PK\x03\x04")
        or text_strip.startswith(r"PK\u0003\u0004")
        or (text_strip.startswith("PK") and "[Content_Types].xml" in text_strip)
        or raw_bytes.startswith(b"PK\x03\x04")
        or raw_bytes.startswith(b"\x50\x4b\x03\x04")
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported binary document format (DOCX/ZIP signature detected). Story Forge currently supports plain text notes (.txt) and Markdown (.md) only. Binary documents cannot cross into Story Reasoning."
        )

    # PDF signature
    if text_strip.startswith("%PDF") or raw_bytes.startswith(b"%PDF") or raw_bytes.startswith(b"\x25\x50\x44\x46"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported binary document format (PDF signature detected). Story Forge currently supports plain text notes (.txt) and Markdown (.md) only. Binary documents cannot cross into Story Reasoning."
        )

    # RTF signature
    if text_strip.startswith("{\\rtf") or raw_bytes.startswith(b"{\\rtf"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported document format (RTF signature detected). Story Forge currently supports plain text notes (.txt) and Markdown (.md) only."
        )

    # Legacy OLE / Microsoft Office Compound Document
    if raw_bytes.startswith(b"\xd0\xcf\x11\xe0"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported legacy binary document format (DOC signature detected). Story Forge currently supports plain text notes (.txt) and Markdown (.md) only."
        )

    # 2. Reject null bytes or non-text binary controls
    if "\x00" in raw_text or b"\x00" in raw_bytes:
        raise HTTPException(
            status_code=400,
            detail="Corrupted document context: null bytes detected. Document context must be clean UTF-8 plain text (.txt) or Markdown (.md)."
        )

    # Non-printable character density check
    non_printable = sum(1 for ch in raw_text[:1024] if ord(ch) < 32 and ch not in ("\t", "\n", "\r"))
    if non_printable > 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid document context: Non-printable control characters detected. Document context must be clean plain text (.txt) or Markdown (.md)."
        )


@router.post("/stories/{story_id}/sessions", response_model=SessionResponse)
def start_forge_session(
    story_id: str,
    req: StartSessionRequest,
    response: Response,
    repo: StoryForgeRepository = Depends(get_repository),
    collab_loop = Depends(get_collaborative_loop)
):
    # Enforce architectural rule: No unvalidated external material crosses the Document Context boundary into Story Reasoning
    if req.story_document_context and req.story_document_context.strip():
        validate_story_document_context(req.story_document_context)

    t_start = time.perf_counter()
    state = repo.get_current_state(story_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")

    session = repo.create_session(
        story_id=story_id,
        creator_id=req.creator_id,
        session_id=req.session_id
    )
    t_ingest_done = time.perf_counter()
    ingestion_ms = round((t_ingest_done - t_start) * 1000, 2)

    llm_ms = 0.0
    reconciliation_ms = 0.0

    # Ingest document notes or raw premise upon session start
    # Principle: Context Before Interrogation — Document context is ingested as narrative background to understand, not as a checklist of form fields
    premise_to_ingest = None
    if req.story_document_context and req.story_document_context.strip():
        state.story_document_context = req.story_document_context.strip()
        repo.save_state(state)
        repo.update_session(session["id"], {"story_document_context": req.story_document_context.strip()})
        premise_to_ingest = (
            f"[EXISTING STORY NOTES & TREATMENT CONTEXT]:\n{req.story_document_context.strip()}\n\n"
            f"[PREMISE / LOGLINE]: {req.initial_premise or (state.logline if state and state.logline else state.title if state else '')}"
        )
    elif req.initial_premise:
        premise_to_ingest = req.initial_premise
    elif state and state.logline:
        premise_to_ingest = state.logline
    elif state and state.title:
        premise_to_ingest = state.title

    if premise_to_ingest:
        t_cycle_start = time.perf_counter()
        transition, new_state, trace, q = collab_loop.process_cycle(
            story_id=story_id,
            creator_input=premise_to_ingest,
            conversation_history=[],
            story_synopsis=state.logline if state else None,
            session_id=session["id"],
            trace_id=session["active_trace_id"]
        )
        t_cycle_end = time.perf_counter()
        cycle_total_ms = round((t_cycle_end - t_cycle_start) * 1000, 2)

        # Compute breakdown: LLM duration vs Forge state & dependency reconciliation
        llm_ms = getattr(trace, "llm_duration_ms", None) or getattr(trace, "latency_ms", None) or round(cycle_total_ms * 0.85, 2)
        reconciliation_ms = max(0.0, round(cycle_total_ms - llm_ms, 2))

        repo.update_session(session["id"], {
            "current_action": transition.authority_mode.value,
            "current_question": q,
            "current_proposal": transition.proposal,
            "active_dependency_id": transition.active_dependency_id
        })
        session = repo.get_session(session["id"])

    t_total_end = time.perf_counter()
    backend_total_ms = round((t_total_end - t_start) * 1000, 2)

    # Expose timing breakdown via HTTP headers for client instrumentation
    response.headers["X-Forge-Ingestion-Ms"] = str(ingestion_ms)
    response.headers["X-Forge-LLM-Ms"] = str(llm_ms)
    response.headers["X-Forge-Reconciliation-Ms"] = str(reconciliation_ms)
    response.headers["X-Forge-Backend-Total-Ms"] = str(backend_total_ms)
    response.headers["Access-Control-Expose-Headers"] = "X-Forge-Ingestion-Ms, X-Forge-LLM-Ms, X-Forge-Reconciliation-Ms, X-Forge-Backend-Total-Ms"

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
            if d.id == session["active_dependency_id"] and d.status.value in ("DETECTED", "ACTIVE", "ASSESSED", "PRIORITISED"):
                active_dep = d
                break

    # Read active dependency without mutating session state during observational GET
    if not active_dep and unresolved:
        from ..engine import DependencyEngine
        dep_engine = DependencyEngine()
        active_dep = dep_engine.prioritise(deps)

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
        requires_creator=bool(question) or (action in (AuthorityMode.ASK, AuthorityMode.PROPOSE))
    )


@router.post("/sessions/{session_id}/input", response_model=ForgeCycleResponse)
def submit_session_input(
    session_id: str,
    req: SubmitInputRequest,
    repo: StoryForgeRepository = Depends(get_repository),
    collab_loop = Depends(get_collaborative_loop)
):
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    story_id = session["story_id"]
    trace_id = session["active_trace_id"]
    state = repo.get_current_state(story_id)
    if state and not state.story_document_context and session.get("story_document_context"):
        state.story_document_context = session.get("story_document_context")
        repo.save_state(state)

    # Process explicit proposal decisions (ACCEPT, REJECT, MODIFY)
    creator_resp = (req.creator_response or req.creator_input or "").strip()
    if req.proposal_action == "ACCEPT":
        creator_resp = creator_resp or "Accepted proposal by creator."
    elif req.proposal_action == "REJECT":
        creator_resp = creator_resp or "Proposal rejected by creator. Please re-evaluate alternative narrative direction."

    # Assemble recent conversation history from existing transitions
    transitions = repo.get_transitions(story_id)
    conv_history = []
    for t in transitions[-6:]:
        if t.question_asked:
            conv_history.append({"speaker": "StoryForge", "text": t.question_asked})
        if t.creator_response:
            conv_history.append({"speaker": "Creator", "text": t.creator_response})

    transition, new_state, trace, next_question = collab_loop.process_cycle(
        story_id=story_id,
        creator_input=creator_resp,
        conversation_history=conv_history,
        story_synopsis=state.logline if state else None,
        session_id=session_id,
        trace_id=trace_id
    )

    deps = repo.get_dependencies(story_id)
    unresolved_deps = [
        d for d in deps
        if d.status.value in ("DETECTED", "ACTIVE", "ASSESSED", "PRIORITISED")
    ]

    # Session state represents the creator's next pending action:
    # Conversational Action Authority: Story Reasoning is the authority on conversational intent.
    # Forge does not keep the conversation running merely because it still has open dependencies.
    if transition.authority_mode == AuthorityMode.STOP or getattr(new_state, "explicit_ending_declared", False):
        session_action = AuthorityMode.STOP.value
        session_status = "COMPLETED"
    elif next_question:
        session_action = AuthorityMode.ASK.value
        session_status = "ACTIVE"
    elif transition.authority_mode == AuthorityMode.PROPOSE:
        session_action = AuthorityMode.PROPOSE.value
        session_status = "ACTIVE"
    elif len(unresolved_deps) == 0:
        session_action = AuthorityMode.STOP.value
        session_status = "COMPLETED"
    else:
        session_action = transition.authority_mode.value
        session_status = "ACTIVE"

    repo.update_session(session_id, {
        "session_status": session_status,
        "current_action": session_action,
        "current_question": next_question,
        "current_proposal": transition.proposal,
        "active_dependency_id": transition.active_dependency_id
    })

    return ForgeCycleResponse(
        story_id=story_id,
        session_id=session_id,
        state_version=new_state.state_version,
        action=AuthorityMode(session_action),
        active_question=next_question,
        transition=transition,
        current_state=new_state,
        unresolved_dependencies_count=len(unresolved_deps)
    )
