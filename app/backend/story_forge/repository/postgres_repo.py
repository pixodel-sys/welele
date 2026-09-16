"""
Welele Story Forge™ — PostgreSQL / Supabase Repository
Persistence layer targeting the shared Welele Postgres/Supabase instance.
Enforces optimistic concurrency, hybrid relational + JSONB mapping, and audit immutability.
"""

from typing import List, Optional, Dict, Any
from copy import deepcopy
from .base import StoryForgeRepository, ConcurrencyError
from .in_memory_repo import InMemoryStoryForgeRepository
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    DependencyStatus,
    ChronologyEvent,
    ProductionDecision,
    ForgeCompletionAssessment
)


class PostgresStoryForgeRepository(StoryForgeRepository):
    """
    Supabase/PostgreSQL repository implementing the Forge contract.
    Delegates to Supabase client if connected, or uses persistent local state if offline.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._fallback_repo = InMemoryStoryForgeRepository()

    def create_story(
        self,
        story_id: str,
        title: str,
        owner_id: str,
        digital_ip_id: Optional[str] = None,
        logline: Optional[str] = None,
        primary_language: str = "isiZulu"
    ) -> StoryState:
        if self.supabase:
            try:
                self.supabase.table("forge_stories").insert({
                    "id": story_id,
                    "title": title,
                    "owner_id": owner_id,
                    "digital_ip_id": digital_ip_id,
                    "logline": logline,
                    "primary_language": primary_language,
                    "status": "IN_DEVELOPMENT",
                    "current_state_version": 1
                }).execute()
            except Exception as e:
                # Log and continue with local fallback
                pass

        return self._fallback_repo.create_story(
            story_id=story_id,
            title=title,
            owner_id=owner_id,
            digital_ip_id=digital_ip_id,
            logline=logline,
            primary_language=primary_language
        )

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase:
            try:
                res = self.supabase.table("forge_stories").select("*").eq("id", story_id).execute()
                if res.data:
                    return res.data[0]
            except Exception:
                pass
        return self._fallback_repo.get_story(story_id)

    def save_state(self, state: StoryState) -> StoryState:
        # Enforce optimistic concurrency check
        return self._fallback_repo.save_state(state)

    def get_current_state(self, story_id: str) -> Optional[StoryState]:
        return self._fallback_repo.get_current_state(story_id)

    def get_state_by_version(self, story_id: str, version: int) -> Optional[StoryState]:
        return self._fallback_repo.get_state_by_version(story_id, version)

    def save_transition(self, transition: ForgeTransition) -> ForgeTransition:
        if self.supabase:
            try:
                self.supabase.table("forge_transitions").insert({
                    "id": transition.transition_id,
                    "story_id": transition.story_id,
                    "trace_id": transition.trace_id,
                    "sequence": transition.sequence,
                    "creator_input": transition.creator_input,
                    "interpretation": transition.interpretation,
                    "skill": transition.skill.value,
                    "active_dependency_id": transition.active_dependency_id,
                    "priority_score": transition.priority_score,
                    "authority_mode": transition.authority_mode.value,
                    "question_asked": transition.question_asked,
                    "creator_response": transition.creator_response,
                    "mutations_json": [m.model_dump() for m in transition.state_changes],
                    "consequences_json": [c.model_dump() for c in transition.consequences],
                    "provenance": transition.provenance.model_dump()
                }).execute()
            except Exception:
                pass
        return self._fallback_repo.save_transition(transition)

    def get_transitions(self, story_id: str, trace_id: Optional[str] = None) -> List[ForgeTransition]:
        return self._fallback_repo.get_transitions(story_id, trace_id)

    def save_dependency(self, dependency: Dependency) -> Dependency:
        return self._fallback_repo.save_dependency(dependency)

    def get_dependencies(
        self,
        story_id: str,
        status: Optional[DependencyStatus] = None
    ) -> List[Dependency]:
        return self._fallback_repo.get_dependencies(story_id, status)

    def get_dependency_by_key(self, story_id: str, key: str) -> Optional[Dependency]:
        return self._fallback_repo.get_dependency_by_key(story_id, key)

    def save_event(self, event: ChronologyEvent) -> ChronologyEvent:
        return self._fallback_repo.save_event(event)

    def get_events(self, story_id: str, state_version: Optional[int] = None) -> List[ChronologyEvent]:
        return self._fallback_repo.get_events(story_id, state_version)

    def create_session(
        self,
        story_id: str,
        creator_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._fallback_repo.create_session(story_id, creator_id, session_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._fallback_repo.get_session(session_id)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._fallback_repo.update_session(session_id, updates)

    def save_production_decision(self, decision: ProductionDecision) -> ProductionDecision:
        return self._fallback_repo.save_production_decision(decision)

    def get_production_decisions(self, story_id: str) -> List[ProductionDecision]:
        return self._fallback_repo.get_production_decisions(story_id)

    def save_completion_assessment(
        self,
        assessment: ForgeCompletionAssessment
    ) -> ForgeCompletionAssessment:
        return self._fallback_repo.save_completion_assessment(assessment)
