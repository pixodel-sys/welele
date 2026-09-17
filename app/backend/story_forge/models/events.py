"""
Welele Story Forge™ — Unified Narrative & Chronology Events Model
Single canonical representation of 'What happened?' across narrative, time, and consequence layers.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone
from .state import StateStatus


class ChronologyEvent(BaseModel):
    """
    Unified narrative and chronology event.
    Acts as both the causal anchor ('What happened?') and the temporal spine.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    story_id: str
    state_version: int = 1
    event_sequence: int  # 1-indexed narrative sequence
    anchor_type: Optional[str] = None  # e.g. INCITING_DISRUPTION, POINT_OF_NO_RETURN, MIDPOINT_REVELATION, DARK_NIGHT, CLIMAX, RESOLUTION
    story_time: Optional[str] = None  # e.g., "Day 1, 14:00" or "Present Day - Morning"
    headline: str
    description: str
    location: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    causal_antecedents: List[str] = Field(default_factory=list)  # UUIDs of prior events causing this
    consequences: List[str] = Field(default_factory=list)
    event_status: StateStatus = StateStatus.FACT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
