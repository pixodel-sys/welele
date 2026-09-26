"""
Welele Media™ — Audience Telemetry & Event Spine Repository (DEPRECATED - Phase A)
DEPRECATION NOTICE: This module is superseded by TelemetryRepository (Unified Event Spine).
All retention and event lookups now forward to TelemetryRepository.
"""

import warnings
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository
from .telemetry_repository import telemetry_repository
from schemas.telemetry_schemas import EpisodeRetentionResponse

class EventRepository(BaseRepository):
    def ingest_event(self, payload: Any) -> Dict[str, Any]:
        warnings.warn(
            "EventRepository.ingest_event is deprecated. Use ViewerTelemetryService.record_event instead.",
            DeprecationWarning,
            stacklevel=2
        )
        if hasattr(payload, "model_dump"):
            data = payload.model_dump()
        elif isinstance(payload, dict):
            data = dict(payload)
        else:
            data = vars(payload)
        return telemetry_repository.local_insert("telemetry_events", data)

    def get_events_for_episode(self, episode_id: str) -> List[Dict[str, Any]]:
        return telemetry_repository.get_events_for_episode(episode_id)

    def get_episode_retention(self, series_id: str, episode_id: str) -> EpisodeRetentionResponse:
        return telemetry_repository.get_episode_retention(series_id, episode_id)


event_repository = EventRepository()
