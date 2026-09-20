"""
Welele Media™ — Audience Telemetry & Event Spine Repository (GAP-004)
Ingests viewing heartbeats, calculates real retention drop-off heatmaps, and tracks paywall conversion.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict
from .base_repository import BaseRepository
from schemas.telemetry_schemas import TelemetryEventPayload, EpisodeRetentionResponse, RetentionDataPoint

class EventRepository(BaseRepository):
    def ingest_event(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            event_name = payload.get("event_name", "heartbeat")
            user_id = payload.get("user_id")
            session_id = payload.get("session_id", "sess_default")
            ip_id = payload.get("ip_id")
            series_id = payload.get("series_id")
            episode_id = payload.get("episode_id")
            playback_second = payload.get("playback_second", 0)
            region_code = payload.get("region_code", "ZA")
            device_type = payload.get("device_type", "mobile_pwa")
            metadata = payload.get("metadata", {})
        else:
            event_name = payload.event_name
            user_id = payload.user_id
            session_id = payload.session_id
            ip_id = payload.ip_id
            series_id = payload.series_id
            episode_id = payload.episode_id
            playback_second = payload.playback_second
            region_code = payload.region_code
            device_type = payload.device_type
            metadata = payload.metadata

        # Ensure IP ID lineage is preserved (resolve from series if not supplied)
        if not ip_id and series_id:
            from .series_repository import series_repository
            s = series_repository.get_series_detail(series_id)
            if not s:
                all_s = series_repository.local_get("series")
                s = next((x for x in all_s if x.get("id") == series_id), None)
            if s:
                ip_id = s.get("ip_id")

        event_record = {
            "id": f"evt_{uuid.uuid4().hex[:10]}",
            "event_name": event_name,
            "user_id": user_id,
            "session_id": session_id,
            "ip_id": ip_id,
            "series_id": series_id,
            "episode_id": episode_id,
            "playback_second": playback_second,
            "region_code": region_code,
            "device_type": device_type,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.local_insert("telemetry_events", event_record)
        return event_record

    def get_events_for_episode(self, episode_id: str) -> List[Dict[str, Any]]:
        all_events = self.local_get("telemetry_events")
        return [e for e in all_events if e.get("episode_id") == episode_id]

    def get_episode_retention(self, series_id: str, episode_id: str) -> EpisodeRetentionResponse:
        legacy_events = self.local_get("telemetry_events") or []
        phase6_events = self.local_get("viewer_telemetry_events") or []
        
        # Combine matching events for the episode
        ep_events = [e for e in legacy_events if e.get("episode_id") == episode_id]
        if not ep_events and not episode_id:
            ep_events = [e for e in legacy_events if e.get("series_id") == series_id]

        # Also incorporate Phase 6 playback events if present
        p6_ep_events = [e for e in phase6_events if e.get("episode_id") == episode_id or (not episode_id and e.get("series_id") == series_id)]

        # Calculate max playback second reached per unique session
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

        # Phase 3A: Zero synthetic data policy. If zero real sessions exist, report zero.
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

        # Real empirical geo distribution
        region_counts = defaultdict(int)
        for e in ep_events:
            reg = e.get("region_code") or "ZA"
            region_counts[reg] += 1
        for e in p6_ep_events:
            reg = (e.get("metadata") or {}).get("region_code") or "ZA"
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

event_repository = EventRepository()
