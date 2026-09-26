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

    def get_events_for_episode(self, episode_id: str) -> List[Dict[str, Any]]:
        """Returns all events associated with a specific episode (checking both legacy and canonical storage)."""
        events_p6 = self.local_get("viewer_telemetry_events") or []
        events_legacy = self.local_get("telemetry_events") or []
        
        matches = [e for e in events_p6 if e.get("episode_id") == episode_id or e.get("content_id") == episode_id]
        legacy_matches = [e for e in events_legacy if e.get("episode_id") == episode_id]
        return matches + legacy_matches

    def get_episode_retention(self, series_id: str, episode_id: str):
        """
        Calculates empirical retention curve directly from recorded telemetry events
        (supporting both canonical viewer_telemetry_events and historical events).
        """
        from collections import defaultdict
        from schemas.telemetry_schemas import EpisodeRetentionResponse, RetentionDataPoint

        legacy_events = self.local_get("telemetry_events") or []
        phase6_events = self.local_get("viewer_telemetry_events") or []

        ep_events = [e for e in legacy_events if e.get("episode_id") == episode_id]
        if not ep_events and not episode_id:
            ep_events = [e for e in legacy_events if e.get("series_id") == series_id]

        p6_ep_events = [
            e for e in phase6_events 
            if e.get("episode_id") == episode_id or (not episode_id and e.get("series_id") == series_id)
        ]

        session_max_sec = defaultdict(int)
        for e in ep_events:
            sess = e.get("session_id", "default")
            sec = e.get("playback_second", 0)
            if sec > session_max_sec[sess]:
                session_max_sec[sess] = sec

        for e in p6_ep_events:
            sess = e.get("session_id", "default")
            sec = int(e.get("position_seconds", 0))
            if sec > session_max_sec[sess]:
                session_max_sec[sess] = sec

        total_sessions = len(session_max_sec)

        if total_sessions == 0:
            return EpisodeRetentionResponse(
                series_id=series_id,
                episode_id=episode_id,
                total_starts=0,
                completion_rate_pct=0.0,
                cliffhanger_conversion_pct=0.0,
                avg_watch_time_seconds=0.0,
                retention_curve=[],
                geo_distribution=[]
            )

        cliffhanger_hits = len([s for s, max_s in session_max_sec.items() if max_s >= 60])
        unlock_hits = (
            len([e for e in ep_events if e.get("event_name") == "unlock_completed"]) +
            len([e for e in p6_ep_events if e.get("event_type") == "CONTENT_UNLOCKED"])
        )

        curve_points: List[RetentionDataPoint] = []
        for sec in range(0, 95, 5):
            active_count = len([s for s, max_s in session_max_sec.items() if max_s >= sec])
            retention_pct = round((active_count / float(total_sessions)) * 100.0, 1)
            curve_points.append(RetentionDataPoint(
                second=sec,
                retention_pct=retention_pct,
                viewer_count=active_count,
                is_cliffhanger=(sec >= 65)
            ))

        region_counts = defaultdict(int)
        for e in ep_events:
            reg = e.get("region_code") or "ZA"
            region_counts[reg] += 1
        for e in p6_ep_events:
            reg = (e.get("metadata") or {}).get("region_code") or (e.get("cohort_context") or {}).get("region_code") or "ZA"
            region_counts[reg] += 1

        total_geo_events = sum(region_counts.values()) or 1
        flags = {"ZA": "🇿🇦", "NG": "🇳🇬", "KE": "🇰🇪", "GH": "🇬🇭"}
        names = {"ZA": "South Africa", "NG": "Nigeria", "KE": "Kenya", "GH": "Ghana"}
        geo_dist = [
            {
                "country": names.get(reg, reg),
                "flag": flags.get(reg, "🌍"),
                "share_pct": round((cnt / float(total_geo_events)) * 100, 1),
                "views": cnt
            }
            for reg, cnt in region_counts.items()
        ]

        return EpisodeRetentionResponse(
            series_id=series_id,
            episode_id=episode_id,
            total_starts=total_sessions,
            completion_rate_pct=round((curve_points[-1].viewer_count / float(total_sessions)) * 100.0, 1),
            cliffhanger_conversion_pct=round((unlock_hits / float(cliffhanger_hits)) * 100.0, 1) if cliffhanger_hits > 0 else 0.0,
            avg_watch_time_seconds=round(sum(session_max_sec.values()) / float(total_sessions), 1),
            retention_curve=curve_points,
            geo_distribution=geo_dist
        )


telemetry_repository = TelemetryRepository()
