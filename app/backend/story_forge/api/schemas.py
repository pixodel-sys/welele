"""
Welele Story Forge™ — Application-Facing API Schemas v0.1
Defines stable Request/Response DTOs for Headless Harness and Creator UI clients.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
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
    story_document_context: Optional[str] = None

    @field_validator("story_document_context")
    @classmethod
    def validate_document_context_input_integrity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_strip = v.strip()
        if not v_strip:
            return None

        # Architectural Rule: No unvalidated external material crosses the Document Context boundary into Story Reasoning
        raw_bytes = v.encode("utf-8", errors="replace")
        if (
            v_strip.startswith("PK\x03\x04")
            or v_strip.startswith("PK\x05\x06")
            or v_strip.startswith("PK\x07\x08")
            or v_strip.startswith(r"PK\x03\x04")
            or v_strip.startswith(r"PK\u0003\u0004")
            or (v_strip.startswith("PK") and "[Content_Types].xml" in v_strip)
            or raw_bytes.startswith(b"PK\x03\x04")
            or raw_bytes.startswith(b"\x50\x4b\x03\x04")
        ):
            raise ValueError("Unsupported binary document format (DOCX/ZIP signature detected). Story Forge accepts plain text (.txt) and Markdown (.md) notes only.")
        if v_strip.startswith("%PDF") or raw_bytes.startswith(b"%PDF") or raw_bytes.startswith(b"\x25\x50\x44\x46"):
            raise ValueError("Unsupported binary document format (PDF signature detected). Story Forge accepts plain text (.txt) and Markdown (.md) notes only.")
        if v_strip.startswith("{\\rtf") or raw_bytes.startswith(b"{\\rtf"):
            raise ValueError("Unsupported document format (RTF signature detected). Story Forge accepts plain text (.txt) and Markdown (.md) notes only.")
        if raw_bytes.startswith(b"\xd0\xcf\x11\xe0"):
            raise ValueError("Unsupported legacy binary document format (DOC signature detected). Story Forge accepts plain text (.txt) and Markdown (.md) notes only.")
        if "\x00" in v or b"\x00" in raw_bytes:
            raise ValueError("Corrupted document context: null bytes detected. Only clean UTF-8 plain text (.txt) or Markdown (.md) notes are supported.")
        non_printable = sum(1 for ch in v[:1024] if ord(ch) < 32 and ch not in ("\t", "\n", "\r"))
        if non_printable > 0:
            raise ValueError("Invalid document context: Non-printable control characters detected.")
        return v


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
