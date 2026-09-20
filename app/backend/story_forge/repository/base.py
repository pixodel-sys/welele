"""
Welele Story Forge™ — Repository Protocol
Persistence interface decoupling narrative engine from storage backend.
"""

from typing import Protocol, List, Optional, Dict, Any
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    DependencyStatus,
    ChronologyEvent,
    ProductionDecision,
    ForgeCompletionAssessment
)


class ConcurrencyError(Exception):
    """Raised when an update conflicts with a newer state version."""
    pass


class StoryForgeRepository(Protocol):
    """
    Core persistence boundary contract.
    """

    def create_story(
        self,
        story_id: str,
        title: str,
        owner_id: str,
        digital_ip_id: Optional[str] = None,
        logline: Optional[str] = None,
        primary_language: str = "isiZulu"
    ) -> StoryState:
        ...

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        ...

    def list_stories(self) -> List[Dict[str, Any]]:
        ...

    def save_state(self, state: StoryState) -> StoryState:
        """
        Persists a new state version. Must enforce optimistic concurrency:
        reject write if current database version > state.previous_state_version.
        """
        ...

    def get_current_state(self, story_id: str) -> Optional[StoryState]:
        ...

    def get_state_by_version(self, story_id: str, version: int) -> Optional[StoryState]:
        ...

    def save_transition(self, transition: ForgeTransition) -> ForgeTransition:
        """
        Persists an immutable Forge transition to the trace.
        """
        ...

    def get_transitions(self, story_id: str, trace_id: Optional[str] = None) -> List[ForgeTransition]:
        ...

    def save_dependency(self, dependency: Dependency) -> Dependency:
        ...

    def get_dependencies(
        self,
        story_id: str,
        status: Optional[DependencyStatus] = None
    ) -> List[Dependency]:
        ...

    def get_dependency_by_key(self, story_id: str, key: str) -> Optional[Dependency]:
        ...

    def save_event(self, event: ChronologyEvent) -> ChronologyEvent:
        ...

    def get_events(self, story_id: str, state_version: Optional[int] = None) -> List[ChronologyEvent]:
        ...

    def create_session(
        self,
        story_id: str,
        creator_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        ...

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        ...

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ...

    def save_production_decision(self, decision: ProductionDecision) -> ProductionDecision:
        ...

    def get_production_decisions(self, story_id: str) -> List[ProductionDecision]:
        ...

    def save_completion_assessment(
        self,
        assessment: ForgeCompletionAssessment
    ) -> ForgeCompletionAssessment:
        ...
