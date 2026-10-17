"""
Welele Media™ — Telemetry Repository (Phase 6 Measurement Layer)
Provides normalized persistence, session event sequencing, deduplication lookup,
and milestone emission tracking for Viewer Telemetry Events.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository
from repositories.series_repository import to_uuid

logger = logging.getLogger("welele.telemetry")

SENSITIVE_FIELD_SUBSTRINGS = (
    "token", "secret", "password", "key", "auth", "credential", "otp"
)

def _sanitize_metadata(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures sensitive authentication tokens or secrets are never persisted in telemetry."""
    sanitized = {}
    for k, v in meta.items():
        k_lower = str(k).lower()
        if any(sub in k_lower for sub in SENSITIVE_FIELD_SUBSTRINGS):
            continue
        if isinstance(v, dict):
            sanitized[k] = _sanitize_metadata(v)
        else:
            sanitized[k] = v
    return sanitized


class TelemetryRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def _map_to_db_payload(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a ViewerTelemetryEvent dict to the canonical public.telemetry_events schema:
        id UUID PRIMARY KEY,
        event_name VARCHAR(64) NOT NULL,
        user_id UUID REFERENCES public.users(id),
        session_id VARCHAR(64) NOT NULL,
        ip_id UUID REFERENCES public.digital_ips(id),
        series_id UUID REFERENCES public.series(id),
        episode_id UUID REFERENCES public.episodes(id),
        playback_second INT NOT NULL,
        region_code VARCHAR(8) NOT NULL,
        device_type VARCHAR(32) NOT NULL,
        metadata JSONB,
        created_at TIMESTAMPTZ NOT NULL
        """
        raw_event_id = event_dict.get("event_id") or event_dict.get("id") or str(uuid.uuid4())
        event_uuid = to_uuid(str(raw_event_id))

        event_name = str(event_dict.get("event_type") or event_dict.get("event_name") or "custom_event")[:64]
        session_id = str(event_dict.get("session_id") or "default_session")[:64]
        playback_second = int(float(event_dict.get("position_seconds") or event_dict.get("playback_second") or 0))

        region_code = str(
            event_dict.get("region_code") or
            (event_dict.get("metadata") or {}).get("region_code") or
            (event_dict.get("cohort_context") or {}).get("region_code") or
            "ZA"
        )[:8]

        device_type = str(
            (event_dict.get("metadata") or {}).get("device_class") or
            event_dict.get("source") or
            "mobile_pwa"
        )[:32]

        series_uuid = None
        if event_dict.get("series_id"):
            raw_s = str(event_dict["series_id"])
            target_s_uuid = to_uuid(raw_s)
            if self.is_live:
                try:
                    s_res = self.get_table("series").select("id").eq("id", target_s_uuid).limit(1).execute()
                    if s_res and s_res.data:
                        series_uuid = s_res.data[0]["id"]
                except Exception:
                    series_uuid = None
            else:
                series_uuid = target_s_uuid

        episode_uuid = None
        ep_id = event_dict.get("episode_id") or (event_dict.get("content_id") if event_dict.get("content_type") == "EPISODE" else None)
        if ep_id:
            raw_ep = str(ep_id)
            target_ep_uuid = to_uuid(raw_ep)
            if self.is_live:
                try:
                    ep_res = self.get_table("episodes").select("id").eq("id", target_ep_uuid).limit(1).execute()
                    if ep_res and ep_res.data:
                        episode_uuid = ep_res.data[0]["id"]
                except Exception:
                    episode_uuid = None
            else:
                episode_uuid = target_ep_uuid

        ip_uuid = None
        if event_dict.get("ip_id"):
            target_ip_uuid = to_uuid(str(event_dict["ip_id"]))
            if self.is_live:
                try:
                    ip_res = self.get_table("digital_ips").select("id").eq("id", target_ip_uuid).limit(1).execute()
                    if ip_res and ip_res.data:
                        ip_uuid = ip_res.data[0]["id"]
                except Exception:
                    ip_uuid = None
            else:
                ip_uuid = target_ip_uuid

        user_uuid = None
        raw_uid = event_dict.get("user_id") or event_dict.get("viewer_id")
        if raw_uid and self.is_live:
            try:
                target_u_uuid = to_uuid(str(raw_uid))
                u_res = self.get_table("users").select("id").eq("id", target_u_uuid).limit(1).execute()
                if u_res and u_res.data:
                    user_uuid = u_res.data[0]["id"]
            except Exception:
                user_uuid = None

        merged_meta = dict(event_dict.get("metadata") or {})
        for spine_key in (
            "event_id", "event_family", "event_type", "occurred_at", "ingested_at",
            "session_id", "viewer_id", "anonymous_id", "content_type", "content_id",
            "series_id", "episode_id", "position_seconds", "duration_seconds",
            "milestone_pct", "event_source", "event_version", "source", "environment",
            "is_test", "technical_context", "cohort_context"
        ):
            if spine_key in event_dict and spine_key not in merged_meta:
                merged_meta[spine_key] = event_dict[spine_key]

        sanitized_meta = _sanitize_metadata(merged_meta)
        created_at = event_dict.get("occurred_at") or datetime.now(timezone.utc).isoformat()

        return {
            "id": event_uuid,
            "event_name": event_name,
            "user_id": user_uuid,
            "session_id": session_id,
            "ip_id": ip_uuid,
            "series_id": series_uuid,
            "episode_id": episode_uuid,
            "playback_second": playback_second,
            "region_code": region_code,
            "device_type": device_type,
            "metadata": sanitized_meta,
            "created_at": created_at
        }

    def _map_db_row_to_event(self, row: Dict[str, Any]) -> Dict[str, Any]:
        meta = row.get("metadata") or {}
        event = dict(meta)
        event["id"] = str(row.get("id"))
        event["event_id"] = meta.get("event_id") or str(row.get("id"))
        event["event_type"] = meta.get("event_type") or row.get("event_name")
        event["session_id"] = row.get("session_id") or meta.get("session_id")
        event["series_id"] = str(row.get("series_id")) if row.get("series_id") else meta.get("series_id")
        event["episode_id"] = str(row.get("episode_id")) if row.get("episode_id") else meta.get("episode_id")
        event["position_seconds"] = meta.get("position_seconds", float(row.get("playback_second", 0)))
        event["occurred_at"] = meta.get("occurred_at") or row.get("created_at")
        event["ingested_at"] = meta.get("ingested_at") or row.get("created_at")
        return event

    def save_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Persists a validated telemetry event to the canonical event ledger and PostgreSQL."""
        if not event_dict.get("ingested_at"):
            event_dict["ingested_at"] = datetime.now(timezone.utc).isoformat()
        
        saved = self.local_insert("telemetry_events", event_dict)

        if self.is_live:
            try:
                db_payload = self._map_to_db_payload(event_dict)
                self.get_table("telemetry_events").insert(db_payload).execute()
            except Exception as e:
                # Telemetry failure must never break viewer playback
                logger.warning(f"[TelemetryRepository] Telemetry PostgreSQL persistence isolated warning: {e}")

        return saved

    def _get_all_events(self) -> List[Dict[str, Any]]:
        """Returns unified telemetry events from local storage, prioritizing canonical telemetry_events."""
        te = self.local_get("telemetry_events") or []
        vte = self.local_get("viewer_telemetry_events") or []
        seen_ids = set()
        unified = []
        for e in list(te) + list(vte):
            eid = e.get("event_id") or e.get("id")
            if eid:
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
            unified.append(e)
        return unified

    def find_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Finds an event by its unique deterministic or UUID identifier for deduplication."""
        events = self._get_all_events()
        local_match = next((e for e in events if e.get("event_id") == event_id or e.get("id") == event_id), None)
        if local_match:
            return local_match

        if self.is_live:
            try:
                target_uuid = to_uuid(str(event_id))
                res = self.get_table("telemetry_events").select("*").eq("id", target_uuid).limit(1).execute()
                if res and res.data:
                    return self._map_db_row_to_event(res.data[0])
            except Exception as e:
                logger.warning(f"[TelemetryRepository] find_event_by_id remote lookup failed: {e}")

        return None

    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns all events for a given session sorted chronologically by occurred_at."""
        events = self._get_all_events()
        session_events = [e for e in events if e.get("session_id") == session_id or e.get("client_session_id") == session_id]

        if self.is_live:
            try:
                res = self.get_table("telemetry_events").select("*").eq("session_id", session_id).order("created_at").execute()
                if res and res.data:
                    seen = {e.get("event_id") or e.get("id") for e in session_events}
                    for r in res.data:
                        mapped = self._map_db_row_to_event(r)
                        mid = mapped.get("event_id") or mapped.get("id")
                        if mid not in seen:
                            session_events.append(mapped)
                            seen.add(mid)
            except Exception as e:
                logger.warning(f"[TelemetryRepository] get_session_events remote lookup failed: {e}")

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
        events = self._get_all_events()
        return any(
            (e.get("session_id") == session_id or e.get("client_session_id") == session_id) and
            (e.get("content_id") == content_id or e.get("episode_id") == content_id) and
            (e.get("event_type") == "PLAYBACK_PROGRESS" or e.get("event_name") == "PLAYBACK_PROGRESS") and
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
        events = self._get_all_events()
        prior_sessions = set()
        for e in events:
            sess = e.get("session_id") or e.get("client_session_id")
            if exclude_session_id and sess == exclude_session_id:
                continue
            
            matches_viewer = viewer_id and (e.get("viewer_id") == viewer_id or e.get("user_id") == viewer_id)
            matches_anon = anonymous_id and e.get("anonymous_id") == anonymous_id
            if matches_viewer or matches_anon:
                if sess:
                    prior_sessions.add(sess)
        return list(prior_sessions)

    def list_all_events(self) -> List[Dict[str, Any]]:
        """Returns all recorded telemetry events."""
        return self._get_all_events()

    def list_events(
        self,
        episode_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns telemetry events optionally filtered by episode_id or session_id."""
        events = self._get_all_events()
        if episode_id:
            events = [e for e in events if e.get("episode_id") == episode_id or e.get("content_id") == episode_id]
        if session_id:
            events = [e for e in events if e.get("session_id") == session_id or e.get("client_session_id") == session_id]
        return events

    def get_events_for_episode(self, episode_id: str) -> List[Dict[str, Any]]:
        """Returns all events associated with a specific episode."""
        events = self._get_all_events()
        return [e for e in events if e.get("episode_id") == episode_id or e.get("content_id") == episode_id]

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
