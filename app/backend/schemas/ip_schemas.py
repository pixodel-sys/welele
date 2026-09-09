"""
Welele Media™ — Digital IP Engine Schemas (Pydantic v2)
Covers Canonical Digital IPs, Story Worlds, Character Bibles, Rights Ledger, and Story Forge Packages.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StoryWorldSchema(BaseModel):
    world_name: str = Field(..., description="Name of the narrative universe/setting")
    geographical_setting: str = Field(..., description="e.g. Alexandra & Sandton, Johannesburg")
    time_period: str = Field(default="Contemporary")
    mythology_and_rules: str = Field(..., description="Rules of power, family, corruption, and legacy")
    cultural_context: str = Field(..., description="Vernacular, traditions, and societal tensions")

class CharacterBibleSchema(BaseModel):
    id: Optional[str] = None
    name: str
    role: str = Field(..., description="protagonist | antagonist | confidant | catalyst")
    archetype: str
    secret_motivation: str
    fatal_flaw: str
    signature_quote: Optional[str] = None
    avatar_url: Optional[str] = None

class RightsSplitSchema(BaseModel):
    beneficiary_user_id: str
    stakeholder_role: str = Field(..., description="Showrunner | Lead Writer | Director | Co-Producer")
    royalty_split_pct: float = Field(..., ge=0.01, le=100.0)
    territory: str = "GLOBAL"
    medium: str = "ALL_MEDIA"
    contract_ref: str

class CreateIPRequest(BaseModel):
    title: str
    franchise_code: str
    logline: str
    synopsis: str
    genre: str
    primary_language: str = "isiZulu"
    master_owner_id: str
    story_world: Optional[StoryWorldSchema] = None
    characters: Optional[List[CharacterBibleSchema]] = []
    rights_splits: Optional[List[RightsSplitSchema]] = []

class IPResponse(BaseModel):
    id: str
    title: str
    franchise_code: str
    logline: str
    synopsis: str
    genre: str
    primary_language: str
    master_owner_id: str
    global_valuation_usd: float = 0.0
    status: str = "active"
    series_count: int = 0
    created_at: str

class IPDetailResponse(BaseModel):
    ip: IPResponse
    story_world: Optional[StoryWorldSchema] = None
    characters: List[CharacterBibleSchema] = []
    rights_ledger: List[RightsSplitSchema] = []
    series: List[Dict[str, Any]] = []
    story_packages: List[Dict[str, Any]] = []

class StoryForgePackageCreateRequest(BaseModel):
    ip_id: str
    creator_id: str
    package_title: str
    story_world_id: Optional[str] = None
    character_ids: Optional[List[str]] = []
    episode_target: Optional[int] = 1
    version: str = "v1.0.0"
    target_duration_seconds: int = 90
    beats: List[Dict[str, Any]]
    dialogues: List[Dict[str, Any]]
    cliffhanger_prompt: str
    ai_model_used: Optional[str] = "gemini-1.5-flash"
    human_approved: bool = True
    lineage_hash: Optional[str] = None
