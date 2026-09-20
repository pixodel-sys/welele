"""
Welele Media™ — Telemetry Repository (Phase 6 Measurement Layer)
Provides normalized persistence, session event sequencing, deduplication lookup,
and milestone emission tracking for Viewer Telemetry Events.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository


class TelemetryRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def save_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Persists a validated telemetry event to the canonical event ledger."""
        if not event_dict.get("ingested_at"):
            event_dict["ingested_at"] = datetime.now(timezone.utc).isoformat()
        
        saved = self.local_insert("viewer_telemetry_events", event_dict)
        return saved

    def find_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Finds an event by its unique deterministic or UUID identifier for deduplication."""
        events = self.local_get("viewer_telemetry_events") or []
        return next((e for e in events if e.get("event_id") == event_id), None)

    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns all events for a given session sorted chronologically by occurred_at."""
        events = self.local_get("viewer_telemetry_events") or []
        session_events = [e for e in events if e.get("session_id") == session_id]
        session_events.sort(key=lambda x: x.get("occurred_at", ""))
        return session_events

    def has_milestone_been_emitted(
        self,
        session_id: str,
        content_id: str,
        milestone_pct: int
    ) -> bool:
        """
        Milestone once-per-session guard:
        Checks if a specific milestone (e.g. 25, 50, 75, 90, 100) has already been emitted
        for the given content item within the session.
        """
        events = self.local_get("viewer_telemetry_events") or []
        return any(
            e.get("session_id") == session_id and
            e.get("content_id") == content_id and
            e.get("event_type") == "PLAYBACK_PROGRESS" and
            e.get("milestone_pct") == milestone_pct
            for e in events
        )

    def get_previous_sessions_for_viewer(
        self,
        viewer_id: Optional[str] = None,
        anonymous_id: Optional[str] = None,
        exclude_session_id: Optional[str] = None
    ) -> List[str]:
        """Returns distinct prior session IDs recorded for this viewer or device."""
        events = self.local_get("viewer_telemetry_events") or []
        prior_sessions = set()
        for e in events:
            if exclude_session_id and e.get("session_id") == exclude_session_id:
                continue
            
            matches_viewer = viewer_id and e.get("viewer_id") == viewer_id
            matches_anon = anonymous_id and e.get("anonymous_id") == anonymous_id
            if matches_viewer or matches_anon:
                prior_sessions.add(e.get("session_id"))
        return list(prior_sessions)

    def list_all_events(self) -> List[Dict[str, Any]]:
        """Returns all recorded telemetry events."""
        return self.local_get("viewer_telemetry_events") or []

    def list_events(
        self,
        episode_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns telemetry events optionally filtered by episode_id or session_id."""
        events = self.local_get("viewer_telemetry_events") or []
        if episode_id:
            events = [e for e in events if e.get("episode_id") == episode_id or e.get("content_id") == episode_id]
        if session_id:
            events = [e for e in events if e.get("session_id") == session_id or e.get("client_session_id") == session_id]
        return events


telemetry_repository = TelemetryRepository()
