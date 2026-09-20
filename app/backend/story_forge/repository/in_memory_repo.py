"""
Welele Story Forge™ — In-Memory Repository
Thread-safe, deterministic in-memory storage implementation for testing and benchmark replay.
"""

from typing import List, Optional, Dict, Any
from copy import deepcopy
from threading import Lock
from uuid import uuid4
from datetime import datetime, timezone
from .base import StoryForgeRepository, ConcurrencyError
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    DependencyStatus,
    ChronologyEvent,
    ProductionDecision,
    ForgeCompletionAssessment
)


class InMemoryStoryForgeRepository(StoryForgeRepository):
    def __init__(self):
        self._lock = Lock()
        self._stories: Dict[str, Dict[str, Any]] = {}
        self._states: Dict[str, Dict[int, StoryState]] = {}  # story_id -> {version: StoryState}
        self._current_versions: Dict[str, int] = {}
        self._transitions: Dict[str, List[ForgeTransition]] = {}  # story_id -> List[ForgeTransition]
        self._dependencies: Dict[str, Dict[str, Dependency]] = {}  # story_id -> {dep_key: Dependency}
        self._events: Dict[str, List[ChronologyEvent]] = {}  # story_id -> List[ChronologyEvent]
        self._sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session dict
        self._production_decisions: Dict[str, Dict[str, ProductionDecision]] = {}
        self._completions: Dict[str, List[ForgeCompletionAssessment]] = {}

    def create_story(
        self,
        story_id: str,
        title: str,
        owner_id: str,
        digital_ip_id: Optional[str] = None,
        logline: Optional[str] = None,
        primary_language: str = "isiZulu"
    ) -> StoryState:
        with self._lock:
            self._stories[story_id] = {
                "id": story_id,
                "title": title,
                "owner_id": owner_id,
                "digital_ip_id": digital_ip_id,
                "logline": logline,
                "primary_language": primary_language,
                "status": "IN_DEVELOPMENT",
                "current_state_version": 1
            }
            initial_state = StoryState(
                story_id=story_id,
                state_version=1,
                title=title,
                logline=logline
            )
            self._states[story_id] = {1: deepcopy(initial_state)}
            self._current_versions[story_id] = 1
            self._transitions[story_id] = []
            self._dependencies[story_id] = {}
            self._events[story_id] = []
            self._production_decisions[story_id] = {}
            self._completions[story_id] = []
            return initial_state

    def get_story(self, story_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            story = self._stories.get(story_id)
            return deepcopy(story) if story else None

    def list_stories(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [deepcopy(s) for s in self._stories.values()]

    def save_state(self, state: StoryState) -> StoryState:
        with self._lock:
            story_id = state.story_id
            curr_ver = self._current_versions.get(story_id, 0)

            # Optimistic Concurrency Check
            if state.previous_state_version is not None:
                if state.previous_state_version != curr_ver:
                    raise ConcurrencyError(
                        f"Stale state write rejected! Current version is {curr_ver}, "
                        f"attempted mutation against previous version {state.previous_state_version}."
                    )
            elif curr_ver > 0 and state.state_version < curr_ver:
                raise ConcurrencyError(
                    f"State version {state.state_version} cannot be less than current version {curr_ver}."
                )

            if story_id not in self._states:
                self._states[story_id] = {}

            self._states[story_id][state.state_version] = deepcopy(state)
            self._current_versions[story_id] = state.state_version
            if story_id in self._stories:
                self._stories[story_id]["current_state_version"] = state.state_version
            return deepcopy(state)

    def get_current_state(self, story_id: str) -> Optional[StoryState]:
        with self._lock:
            curr_ver = self._current_versions.get(story_id)
            if not curr_ver:
                return None
            return deepcopy(self._states[story_id].get(curr_ver))

    def get_state_by_version(self, story_id: str, version: int) -> Optional[StoryState]:
        with self._lock:
            states = self._states.get(story_id, {})
            state = states.get(version)
            return deepcopy(state) if state else None

    def save_transition(self, transition: ForgeTransition) -> ForgeTransition:
        with self._lock:
            story_id = transition.story_id
            if story_id not in self._transitions:
                self._transitions[story_id] = []
            self._transitions[story_id].append(deepcopy(transition))
            return deepcopy(transition)

    def get_transitions(self, story_id: str, trace_id: Optional[str] = None) -> List[ForgeTransition]:
        with self._lock:
            transitions = self._transitions.get(story_id, [])
            if trace_id:
                transitions = [t for t in transitions if t.trace_id == trace_id]
            # Return sorted by sequence
            return deepcopy(sorted(transitions, key=lambda t: t.sequence))

    def save_dependency(self, dependency: Dependency) -> Dependency:
        with self._lock:
            story_id = dependency.story_id
            if story_id not in self._dependencies:
                self._dependencies[story_id] = {}
            self._dependencies[story_id][dependency.dependency_key] = deepcopy(dependency)
            return deepcopy(dependency)

    def get_dependencies(
        self,
        story_id: str,
        status: Optional[DependencyStatus] = None
    ) -> List[Dependency]:
        with self._lock:
            deps = list(self._dependencies.get(story_id, {}).values())
            if status:
                deps = [d for d in deps if d.status == status]
            return deepcopy(sorted(deps, key=lambda d: d.priority_score, reverse=True))

    def get_dependency_by_key(self, story_id: str, key: str) -> Optional[Dependency]:
        with self._lock:
            dep = self._dependencies.get(story_id, {}).get(key)
            return deepcopy(dep) if dep else None

    def save_event(self, event: ChronologyEvent) -> ChronologyEvent:
        with self._lock:
            story_id = event.story_id
            if story_id not in self._events:
                self._events[story_id] = []
            # Upsert by event_id or sequence
            existing = [e for e in self._events[story_id] if e.event_id == event.event_id]
            if existing:
                self._events[story_id] = [e if e.event_id != event.event_id else deepcopy(event) for e in self._events[story_id]]
            else:
                self._events[story_id].append(deepcopy(event))
            return deepcopy(event)

    def get_events(self, story_id: str, state_version: Optional[int] = None) -> List[ChronologyEvent]:
        with self._lock:
            events = self._events.get(story_id, [])
            if state_version is not None:
                events = [e for e in events if e.state_version == state_version]
            return deepcopy(sorted(events, key=lambda e: e.event_sequence))

    def create_session(
        self,
        story_id: str,
        creator_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            sid = session_id or str(uuid4())
            trace_id = f"trace-{sid[:8]}"
            sess = {
                "id": sid,
                "story_id": story_id,
                "creator_id": creator_id,
                "session_status": "ACTIVE",
                "active_trace_id": trace_id,
                "current_action": "ASK",
                "current_question": None,
                "active_dependency_id": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self._sessions[sid] = deepcopy(sess)
            return deepcopy(sess)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            sess = self._sessions.get(session_id)
            return deepcopy(sess) if sess else None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            if session_id not in self._sessions:
                return None
            sess = self._sessions[session_id]
            sess.update(updates)
            sess["updated_at"] = datetime.now(timezone.utc).isoformat()
            return deepcopy(sess)

    def save_production_decision(self, decision: ProductionDecision) -> ProductionDecision:
        with self._lock:
            story_id = decision.story_id
            if story_id not in self._production_decisions:
                self._production_decisions[story_id] = {}
            self._production_decisions[story_id][decision.decision_key] = deepcopy(decision)
            return deepcopy(decision)

    def get_production_decisions(self, story_id: str) -> List[ProductionDecision]:
        with self._lock:
            return deepcopy(list(self._production_decisions.get(story_id, {}).values()))

    def save_completion_assessment(
        self,
        assessment: ForgeCompletionAssessment
    ) -> ForgeCompletionAssessment:
        with self._lock:
            story_id = assessment.story_id
            if story_id not in self._completions:
                self._completions[story_id] = []
            self._completions[story_id].append(deepcopy(assessment))
            return deepcopy(assessment)
