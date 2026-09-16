"""
Welele Story Forge™ — Domain State Models
Canonical StoryState, CharacterState, KnowledgeState, and World Models.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone


class StateStatus(str, Enum):
    """
    Core Truth Status:
    FACT: Established canonical truth
    UNKNOWN: Intentionally not established
    UNRESOLVED: Must be resolved before safe story progression
    """
    FACT = "FACT"
    UNKNOWN = "UNKNOWN"
    UNRESOLVED = "UNRESOLVED"


class CharacterRole(str, Enum):
    PROTAGONIST = "PROTAGONIST"
    ANTAGONIST = "ANTAGONIST"
    CONFIDANT = "CONFIDANT"
    CATALYST = "CATALYST"
    SUPPORTING = "SUPPORTING"
    UNRESOLVED = "UNRESOLVED"


class CharacterRelationship(BaseModel):
    target_character: str
    relation_type: str  # e.g. "SIBLING", "FIANCE", "BETRAYER", "RIVAL"
    status: StateStatus = StateStatus.FACT
    dynamic: Optional[str] = None
    tension_level: int = Field(default=5, ge=1, le=10)


class CharacterState(BaseModel):
    name: str
    role: CharacterRole = CharacterRole.UNRESOLVED
    archetype: Optional[str] = None
    core_motivation: Optional[str] = None
    secret_desire: Optional[str] = None
    fatal_flaw: Optional[str] = None
    status: StateStatus = StateStatus.FACT
    relationships: List[CharacterRelationship] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeStatus(str, Enum):
    KNOWS = "KNOWS"
    BELIEVES = "BELIEVES"
    DOES_NOT_KNOW = "DOES_NOT_KNOW"
    SUSPECTS = "SUSPECTS"


class KnowledgeState(BaseModel):
    character_name: str
    fact_key: str
    status: KnowledgeStatus = KnowledgeStatus.KNOWS
    source_event_id: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    story_time_recorded: Optional[str] = None


class NarrativePlant(BaseModel):
    element_code: str = ""
    plant_name: Optional[str] = None
    description: str
    introduced_event_id: Optional[str] = None
    intended_payoff: Optional[str] = None
    payoff_status: str = "PLANTED"  # PLANTED, PAID_OFF, ABANDONED, SUBVERTED
    payoff_event_id: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.element_code and self.plant_name:
            self.element_code = self.plant_name
        elif not self.plant_name and self.element_code:
            self.plant_name = self.element_code


class WorldSetting(BaseModel):
    primary_location: str = "Johannesburg & Environs"
    geography: List[str] = Field(default_factory=list)
    rules_and_lore: List[str] = Field(default_factory=list)
    cultural_context: Optional[str] = None


class StoryState(BaseModel):
    """
    Authoritative canonical state snapshot for a Story Forge story version.
    """
    story_id: str
    state_version: int = 1
    previous_state_version: Optional[int] = None
    source_transition_id: Optional[str] = None
    title: str = "Untitled Story"
    logline: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None
    world: WorldSetting = Field(default_factory=WorldSetting)
    characters: Dict[str, CharacterState] = Field(default_factory=dict)
    knowledge_states: List[KnowledgeState] = Field(default_factory=list)
    plants: List[NarrativePlant] = Field(default_factory=list)
    raw_creator_notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_character(self, name: str) -> Optional[CharacterState]:
        return self.characters.get(name)

    def count_unresolved(self) -> int:
        count = 0
        for char in self.characters.values():
            if char.status == StateStatus.UNRESOLVED or char.role == CharacterRole.UNRESOLVED:
                count += 1
            for rel in char.relationships:
                if rel.status == StateStatus.UNRESOLVED:
                    count += 1
        return count
