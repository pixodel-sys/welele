"""
Welele Media™ — Story Review™ API Router
Creator-Facing Story Assistant & IP Pipeline Intake Layer

Governing Principle:
"Same intelligence infrastructure where appropriate. Different product, different audience, different authority, different exposure."

Story Review™ helps independent creators diagnose, improve, structure, and prepare their stories
for submission to the Welele IP Pipeline ("Submit for Greenlight").
It does NOT expose internal Story Forge™ internals (e.g. dependency queues, raw JSON mutations, Forge Judge rules).
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from repositories.base_repository import BaseRepository
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service
from story_forge.adapters.providers.http_provider import HttpLLMProvider

router = APIRouter(prefix="/review", tags=["Story Review™ (Creator Gateway)"])


# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------

class StoryDraftPayload(BaseModel):
    draft_id: Optional[str] = None
    creator_id: Optional[str] = "creator_zola"
    creator_name: Optional[str] = "Zola Dlamini"
    title: str = Field(..., min_length=1, description="Story or series working title")
    logline: str = Field(default="", description="High-concept hook or 1-2 sentence premise")
    target_format: str = Field(default="VERTICAL_MICRODRAMA", description="e.g. VERTICAL_MICRODRAMA, SHORT_SERIES, FEATURE")
    tone: Optional[str] = "Supernatural Crime Drama"
    themes: Optional[List[str]] = Field(default_factory=list)
    protagonist_name: Optional[str] = ""
    protagonist_want: Optional[str] = ""
    protagonist_need: Optional[str] = ""
    counterforce_or_antagonist: Optional[str] = ""
    world_setting: Optional[str] = ""
    episode_hooks: Optional[List[str]] = Field(default_factory=list)
    full_draft_text: Optional[str] = ""
    version: int = 1


class DimensionEvaluation(BaseModel):
    score: int = Field(..., ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    critique: str = ""


class ActionableTip(BaseModel):
    title: str
    description: str
    impact_area: str  # e.g., "Premise", "Character", "Pacing", "Budget"


class ChecklistItem(BaseModel):
    item: str
    passed: bool
    recommendation: str


class StoryReviewDiagnosticResponse(BaseModel):
    draft_id: Optional[str] = None
    readiness_score: int = Field(..., ge=0, le=100)
    readiness_tier: str  # "READY_FOR_SUBMISSION" | "SOLID_FOUNDATION" | "NEEDS_REVISION"
    evaluation_mode: str = Field(default="BASELINE_HEURISTIC", description="'AI_ASSISTED' or 'BASELINE_HEURISTIC'")
    premise_and_hook: DimensionEvaluation
    character_tension: DimensionEvaluation
    episodic_structure: DimensionEvaluation
    production_feasibility: DimensionEvaluation
    actionable_tips: List[ActionableTip]
    submission_checklist: List[ChecklistItem]
    pitch_summary: str
    evaluated_at: str


class PitchSubmitRequest(BaseModel):
    draft_id: Optional[str] = None
    creator_id: Optional[str] = "creator_zola"
    creator_name: Optional[str] = "Zola Dlamini"
    title: str
    logline: str
    target_format: str = "VERTICAL_MICRODRAMA"
    pitch_package: Dict[str, Any] = Field(default_factory=dict)
    diagnostic_score: int = 0
    creator_notes: Optional[str] = ""


class CreatorSubmissionResponse(BaseModel):
    submission_id: str
    creator_id: str
    creator_name: str
    title: str
    status: str
    submitted_at: str
    diagnostic_summary: Dict[str, Any]
    submission_package: Dict[str, Any]
    message: str


# -----------------------------------------------------------------------------
# Story Review Repository Layer
# -----------------------------------------------------------------------------

class StoryReviewRepository(BaseRepository):
    def get_drafts(self, creator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        drafts = self.local_get("story_drafts") or []
        if creator_id:
            return [d for d in drafts if d.get("creator_id") == creator_id]
        return drafts

    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        drafts = self.local_get("story_drafts") or []
        for d in drafts:
            if d.get("id") == draft_id:
                return d
        return None

    def save_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        draft_id = draft_data.get("id") or draft_data.get("draft_id") or f"draft_{uuid.uuid4().hex[:10]}"
        draft_data["id"] = draft_id
        now = datetime.now(timezone.utc).isoformat()
        draft_data["updated_at"] = now
        if "created_at" not in draft_data:
            draft_data["created_at"] = now

        existing = self.get_draft(draft_id)
        if existing:
            self.local_update("story_drafts", "id", draft_id, draft_data)
        else:
            self.local_insert("story_drafts", draft_data)
        return draft_data

    def get_submissions(self, creator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        subs = self.local_get("creator_submissions") or []
        if creator_id:
            return [s for s in subs if s.get("creator_id") == creator_id]
        return subs

    def get_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        subs = self.local_get("creator_submissions") or []
        for s in subs:
            if s.get("submission_id") == submission_id:
                return s
        return None

    def find_submission_by_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        if not draft_id:
            return None
        subs = self.local_get("creator_submissions") or []
        for s in subs:
            if s.get("draft_id") == draft_id:
                return s
        return None

    def upsert_submission(self, sub_data: Dict[str, Any]) -> Dict[str, Any]:
        existing = None
        if sub_data.get("submission_id"):
            existing = self.get_submission(sub_data["submission_id"])
        elif sub_data.get("draft_id"):
            existing = self.find_submission_by_draft(sub_data["draft_id"])

        if existing:
            sub_id = existing["submission_id"]
            sub_data["submission_id"] = sub_id
            self.local_update("creator_submissions", "submission_id", sub_id, sub_data)
            return sub_data
        else:
            if not sub_data.get("submission_id"):
                sub_data["submission_id"] = f"sub_{uuid.uuid4().hex[:12]}"
            self.local_insert("creator_submissions", sub_data)
            return sub_data

    def create_submission(self, sub_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.upsert_submission(sub_data)


story_review_repo = StoryReviewRepository()


# -----------------------------------------------------------------------------
# Creator-Facing Diagnostic Evaluation Engine
# -----------------------------------------------------------------------------

def evaluate_story_draft(draft: StoryDraftPayload) -> StoryReviewDiagnosticResponse:
    """
    Evaluates a story draft across 4 creator dimensions:
    1. Premise & Hook
    2. Character Tension
    3. Episodic Structure
    4. Production Feasibility
    Produces a 0-100 Submission Readiness Score, actionable feedback, and checklist.
    """
    # Check if real LLM provider is available
    llm_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("STORY_FORGE_LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if llm_api_key and llm_api_key not in ("mock-key", ""):
        try:
            provider = HttpLLMProvider()
            system_prompt = (
                "You are the Welele Media Story Review™ AI Editorial Coach. "
                "Your role is to help independent screenwriters and creators refine their vertical microdrama stories "
                "before submitting them to the Welele IP Pipeline for Greenlight review.\n"
                "Evaluate the draft encouragingly but rigorously across 4 dimensions:\n"
                "1. Premise & Hook (clarity, curiosity gap, high-concept vertical appeal)\n"
                "2. Character Tension (want vs need, stakes, internal & external counterforces)\n"
                "3. Episodic Structure (cliffhanger momentum, pacing for 60-90s episodes)\n"
                "4. Production Feasibility (contained locations, budget realism, cast size)\n\n"
                "Provide a 0-100 readiness_score, dimension scores (0-100), strengths, critique, actionable tips, and checklist."
            )

            user_prompt = f"""
Title: {draft.title}
Logline: {draft.logline}
Target Format: {draft.target_format}
Tone: {draft.tone}
Protagonist: {draft.protagonist_name}
Want: {draft.protagonist_want}
Need: {draft.protagonist_need}
Counterforce: {draft.counterforce_or_antagonist}
World Setting: {draft.world_setting}
Episode Hooks: {draft.episode_hooks}
Full Draft / Notes:
{draft.full_draft_text}
"""

            response_schema = {
                "type": "object",
                "properties": {
                    "readiness_score": {"type": "integer"},
                    "readiness_tier": {"type": "string"},
                    "premise_and_hook": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "critique": {"type": "string"}
                        },
                        "required": ["score", "strengths", "critique"]
                    },
                    "character_tension": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "critique": {"type": "string"}
                        },
                        "required": ["score", "strengths", "critique"]
                    },
                    "episodic_structure": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "critique": {"type": "string"}
                        },
                        "required": ["score", "strengths", "critique"]
                    },
                    "production_feasibility": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "critique": {"type": "string"}
                        },
                        "required": ["score", "strengths", "critique"]
                    },
                    "actionable_tips": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "impact_area": {"type": "string"}
                            },
                            "required": ["title", "description", "impact_area"]
                        }
                    },
                    "submission_checklist": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {"type": "string"},
                                "passed": {"type": "boolean"},
                                "recommendation": {"type": "string"}
                            },
                            "required": ["item", "passed", "recommendation"]
                        }
                    },
                    "pitch_summary": {"type": "string"}
                },
                "required": [
                    "readiness_score", "readiness_tier", "premise_and_hook", "character_tension",
                    "episodic_structure", "production_feasibility", "actionable_tips", "submission_checklist", "pitch_summary"
                ]
            }

            res = provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=response_schema,
                temperature=0.3,
                timeout_seconds=25.0
            )

            now = datetime.now(timezone.utc).isoformat()
            raw_tier = res.get("readiness_tier", "")
            score = res.get("readiness_score", 75)
            if raw_tier in ("READY_FOR_SUBMISSION", "SOLID_FOUNDATION", "NEEDS_REVISION"):
                tier = raw_tier
            else:
                tier = "READY_FOR_SUBMISSION" if score >= 80 else ("SOLID_FOUNDATION" if score >= 60 else "NEEDS_REVISION")

            return StoryReviewDiagnosticResponse(
                draft_id=draft.draft_id,
                readiness_score=score,
                readiness_tier=tier,
                evaluation_mode="AI_ASSISTED",
                premise_and_hook=DimensionEvaluation(**res.get("premise_and_hook", {})),
                character_tension=DimensionEvaluation(**res.get("character_tension", {})),
                episodic_structure=DimensionEvaluation(**res.get("episodic_structure", {})),
                production_feasibility=DimensionEvaluation(**res.get("production_feasibility", {})),
                actionable_tips=[ActionableTip(**t) for t in res.get("actionable_tips", [])],
                submission_checklist=[ChecklistItem(**c) for c in res.get("submission_checklist", [])],
                pitch_summary=res.get("pitch_summary", f"A vertical microdrama concept for '{draft.title}'."),
                evaluated_at=now
            )
        except Exception as e:
            print(f"[StoryReview] Live LLM diagnostic fallback due to: {e}")

    # Robust Heuristic Evaluation Fallback
    has_title = bool(draft.title and len(draft.title.strip()) > 2)
    has_logline = bool(draft.logline and len(draft.logline.strip()) > 15)
    has_protagonist = bool(draft.protagonist_name and len(draft.protagonist_name.strip()) > 1)
    has_want = bool(draft.protagonist_want and len(draft.protagonist_want.strip()) > 5)
    has_need = bool(draft.protagonist_need and len(draft.protagonist_need.strip()) > 5)
    has_counterforce = bool(draft.counterforce_or_antagonist and len(draft.counterforce_or_antagonist.strip()) > 2)
    has_world = bool(draft.world_setting and len(draft.world_setting.strip()) > 5)
    hooks_count = len(draft.episode_hooks or [])
    draft_len = len(draft.full_draft_text or "")

    # Dimension 1: Premise & Hook (0-100)
    premise_score = 40
    premise_strengths = []
    if has_title:
        premise_score += 20
        premise_strengths.append(f"Distinctive title: '{draft.title}'")
    if has_logline:
        premise_score += 35
        premise_strengths.append("Clear logline establishes core narrative curiosity gap.")
    else:
        premise_score = min(premise_score, 50)
    if draft.tone:
        premise_score += 5
        premise_strengths.append(f"Defined tone: {draft.tone}")
    premise_score = min(100, premise_score)
    premise_critique = "Sharpen the central mystery or dramatic stakes in the first 10 seconds of episode 1." if premise_score < 80 else "Strong high-concept hook with immediate viewer intrigue."

    # Dimension 2: Character Tension (0-100)
    char_score = 30
    char_strengths = []
    if has_protagonist:
        char_score += 20
        char_strengths.append(f"Identifiable central protagonist ({draft.protagonist_name}).")
    if has_want and has_need:
        char_score += 30
        char_strengths.append("Clear Want vs Need internal-external polarity.")
    if has_counterforce:
        char_score += 20
        char_strengths.append(f"Grounded opposing counterforce ({draft.counterforce_or_antagonist}).")
    char_score = min(100, char_score)
    char_critique = "Deepen the emotional cost if the protagonist fails to overcome the counterforce." if char_score < 80 else "Compelling protagonist arc with strong internal-external tension."

    # Dimension 3: Episodic Structure (0-100)
    struct_score = 30
    struct_strengths = []
    if hooks_count >= 3:
        struct_score += 45
        struct_strengths.append(f"{hooks_count} episodic cliffhanger beats mapped.")
    elif hooks_count > 0:
        struct_score += 25
        struct_strengths.append(f"{hooks_count} episode beat identified.")
    if draft_len > 200:
        struct_score += 25
        struct_strengths.append("Sufficient scene progression detail for episodic serialization.")
    struct_score = min(100, struct_score)
    struct_critique = "Ensure every 60-90 second episode terminates on an unresolved dilemma or shocking reveal." if struct_score < 80 else "Excellent episodic pacing designed for vertical mobile engagement."

    # Dimension 4: Production Feasibility (0-100)
    prod_score = 50
    prod_strengths = ["Targeted at vertical 9:16 mobile microdrama format."]
    if has_world:
        prod_score += 30
        prod_strengths.append(f"Contained setting ({draft.world_setting}) keeps production nimble.")
    else:
        prod_critique = "Specify location containment to ensure rapid turnaround shooting."
    prod_score = min(100, prod_score)
    prod_critique = "Well-suited for low-to-medium budget microdrama production with controlled shoot days." if prod_score >= 80 else "Refine location requirements to maximize production efficiency."

    overall_readiness = int((premise_score * 0.3) + (char_score * 0.3) + (struct_score * 0.25) + (prod_score * 0.15))
    
    tier = "READY_FOR_SUBMISSION" if overall_readiness >= 80 else ("SOLID_FOUNDATION" if overall_readiness >= 60 else "NEEDS_REVISION")

    checklist = [
        ChecklistItem(item="High-Concept Logline", passed=has_logline, recommendation="Add a 1-2 sentence hook highlighting the stakes." if not has_logline else "Logline is crisp and engaging."),
        ChecklistItem(item="Protagonist Dilemma (Want vs Need)", passed=has_want and has_need, recommendation="Clarify what the protagonist wants vs what they truly need." if not (has_want and has_need) else "Clear internal conflict defined."),
        ChecklistItem(item="Grounded Counterforce / Antagonist", passed=has_counterforce, recommendation="Define the opposing character or systemic force." if not has_counterforce else "Opposing force active."),
        ChecklistItem(item="Episodic Cliffhangers (Min 3 beats)", passed=hooks_count >= 3, recommendation="Add at least 3 episode hook beats to prove serialization." if hooks_count < 3 else "Episodic momentum proven."),
        ChecklistItem(item="Contained Production World", passed=has_world, recommendation="Describe the primary shoot locations." if not has_world else "Setting clearly defined.")
    ]

    actionable_tips = [
        ActionableTip(
            title="Amplify Episode 1 Micro-Hook",
            description="In vertical drama, the opening 5 seconds must trigger an immediate question in the viewer's mind.",
            impact_area="Premise & Hook"
        ),
        ActionableTip(
            title="Heighten the Cost of Failure",
            description=f"Make sure {draft.protagonist_name or 'the protagonist'} has something irrecoverable to lose by Episode 3.",
            impact_area="Character Tension"
        ),
        ActionableTip(
            title="Location Efficiency",
            description="Group key scenes into 1-2 primary sets to streamline filming schedules and production budgets.",
            impact_area="Production Feasibility"
        )
    ]

    now = datetime.now(timezone.utc).isoformat()
    return StoryReviewDiagnosticResponse(
        draft_id=draft.draft_id,
        readiness_score=overall_readiness,
        readiness_tier=tier,
        evaluation_mode="BASELINE_HEURISTIC",
        premise_and_hook=DimensionEvaluation(score=premise_score, strengths=premise_strengths, critique=premise_critique),
        character_tension=DimensionEvaluation(score=char_score, strengths=char_strengths, critique=char_critique),
        episodic_structure=DimensionEvaluation(score=struct_score, strengths=struct_strengths, critique=struct_critique),
        production_feasibility=DimensionEvaluation(score=prod_score, strengths=prod_strengths, critique=prod_critique),
        actionable_tips=actionable_tips,
        submission_checklist=checklist,
        pitch_summary=f"Vertical microdrama pitch for '{draft.title}' by {draft.creator_name or 'Creator'}.",
        evaluated_at=now
    )


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.get("/drafts")
def list_story_drafts(creator_id: Optional[str] = "creator_zola"):
    """Lists persistent story drafts for the active creator."""
    return story_review_repo.get_drafts(creator_id)


@router.post("/drafts")
def save_story_draft(draft: StoryDraftPayload):
    """Saves or updates a persistent story draft in Story Review™."""
    data = draft.dict()
    saved = story_review_repo.save_draft(data)
    return {"success": True, "draft": saved}


@router.get("/drafts/{draft_id}")
def get_story_draft(draft_id: str):
    """Retrieves a single persistent story draft."""
    draft = story_review_repo.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Story draft not found")
    return draft


@router.post("/diagnose", response_model=StoryReviewDiagnosticResponse)
def diagnose_story(draft: StoryDraftPayload):
    """
    Generates a structured creator-facing diagnostic review.
    Evaluates Premise, Character Tension, Episodic Structure, and Production Feasibility.
    Calculates the 0-100 Submission Readiness Score without exposing Forge Judge internals.
    """
    return evaluate_story_draft(draft)


@router.post("/submit-pitch", response_model=CreatorSubmissionResponse)
def submit_pitch_for_greenlight(req: PitchSubmitRequest, auth_user: dict = Depends(get_current_user)):
    """
    IP Pipeline Intake Entry Point: Submits a creator's story pitch to Welele editorial review.
    Creates or updates a Creator Submission / Intake Record with status 'SUBMITTED_FOR_REVIEW'.
    Submission ≠ Greenlight. The submission is queued for Welele editorial intake and Forge development.
    Guarantees duplicate submission protection by deduplicating against draft_id.
    """
    now = datetime.now(timezone.utc).isoformat()
    existing = story_review_repo.find_submission_by_draft(req.draft_id) if req.draft_id else None
    
    submission_id = existing["submission_id"] if existing else f"sub_{uuid.uuid4().hex[:12]}"

    sub_record = {
        "submission_id": submission_id,
        "draft_id": req.draft_id,
        "creator_id": auth_user.get("sub", req.creator_id),
        "creator_name": req.creator_name,
        "title": req.title,
        "logline": req.logline,
        "target_format": req.target_format,
        "status": "SUBMITTED_FOR_REVIEW",
        "submitted_at": now,
        "diagnostic_summary": {
            "readiness_score": req.diagnostic_score,
            "evaluated_at": now
        },
        "submission_package": {
            "pitch_package": req.pitch_package,
            "creator_notes": req.creator_notes,
            "version": "1.0"
        },
        "decision_notes": existing.get("decision_notes") if existing else None,
        "intake_stage": "EDITORIAL_TRIAGE"
    }

    story_review_repo.upsert_submission(sub_record)

    # Emit Institutional Audit Event
    audit_service.record_trust_event(
        domain="IP",
        event_type="ip.creator_submission_created" if not existing else "ip.creator_submission_updated",
        actor_id=sub_record["creator_id"],
        actor_role=auth_user.get("role", "creator"),
        target_type="creator_submission",
        target_id=submission_id,
        after_state={"title": req.title, "status": "SUBMITTED_FOR_REVIEW", "readiness_score": req.diagnostic_score},
        metadata={"intake_stage": "EDITORIAL_TRIAGE", "target_format": req.target_format, "is_update": bool(existing)}
    )

    return CreatorSubmissionResponse(
        submission_id=submission_id,
        creator_id=sub_record["creator_id"],
        creator_name=req.creator_name,
        title=req.title,
        status="SUBMITTED_FOR_REVIEW",
        submitted_at=now,
        diagnostic_summary=sub_record["diagnostic_summary"],
        submission_package=sub_record["submission_package"],
        message="Story pitch successfully submitted to the Welele IP Pipeline for Greenlight review."
    )


@router.get("/submissions")
def list_submissions(creator_id: Optional[str] = None):
    """Lists creator submissions in the IP Pipeline (accessible by creator and admin intake)."""
    return story_review_repo.get_submissions(creator_id)


@router.get("/submissions/{submission_id}")
def get_submission_detail(submission_id: str):
    """Retrieves a specific creator submission intake record."""
    sub = story_review_repo.get_submission(submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission intake record not found")
    return sub
