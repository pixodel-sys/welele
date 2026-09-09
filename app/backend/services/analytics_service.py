"""
Welele Media™ — Analytics & Telemetry Signal Correlation Service (P2)
Separates technical playback noise (buffering, bitrate, network drops) from true audience narrative drops.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.event_repository import event_repository

class AnalyticsService:
    def analyze_episode_performance(
        self,
        series_id: str,
        episode_id: str
    ) -> Dict[str, Any]:
        """
        Calculates empirical retention metrics and correlates playback signals.
        """
        raw_retention_raw = event_repository.get_episode_retention(series_id, episode_id)
        raw_retention = raw_retention_raw.model_dump() if hasattr(raw_retention_raw, "model_dump") else raw_retention_raw
        events = event_repository.get_events_for_episode(episode_id)

        total_sessions = max(raw_retention.get("total_starts", 0), 1)
        curve = raw_retention.get("retention_curve", [])

        # Correlate technical metrics across sessions
        buffering_events = [e for e in events if e.get("event_name") in ["buffer_start", "rebuffering", "stall"]]
        buffering_ratio = len(buffering_events) / float(total_sessions)

        # Detect candidate drop-off intervals (>12% drop between consecutive timecode samples)
        detected_drops = []
        for i in range(1, len(curve)):
            prev = curve[i - 1]
            curr = curve[i]
            prev_pct = prev.get("retention_pct", 0) if isinstance(prev, dict) else prev.retention_pct
            curr_pct = curr.get("retention_pct", 0) if isinstance(curr, dict) else curr.retention_pct
            drop_delta = prev_pct - curr_pct
            if drop_delta >= 12.0:
                # Correlate with buffering signals at this time window
                t_start = prev.get("second", 0) if isinstance(prev, dict) else prev.second
                t_end = curr.get("second", 0) if isinstance(curr, dict) else curr.second
                window_buffers = [b for b in buffering_events if t_start <= b.get("playback_second", 0) <= t_end]

                is_technical_anomaly = len(window_buffers) > (0.25 * total_sessions)
                classification = "TECHNICAL_BUFFERING" if is_technical_anomaly else "CONFIRMED_NARRATIVE_DROP"

                detected_drops.append({
                    "time_range": f"{t_start}s–{t_end}s",
                    "start_second": t_start,
                    "end_second": t_end,
                    "drop_percentage": round(drop_delta, 1),
                    "classification": classification,
                    "confidence_score": 0.88 if not is_technical_anomaly else 0.45,
                    "sample_size": total_sessions
                })

        return {
            "series_id": series_id,
            "episode_id": episode_id,
            "total_views": total_sessions,
            "average_watch_time": raw_retention.get("average_watch_time", 0),
            "cliffhanger_conversion_pct": raw_retention.get("cliffhanger_conversion_pct", 0),
            "technical_health": {
                "buffering_ratio": round(buffering_ratio, 3),
                "is_healthy": buffering_ratio < 0.08
            },
            "retention_curve": curve,
            "detected_drops": detected_drops
        }

analytics_service = AnalyticsService()
