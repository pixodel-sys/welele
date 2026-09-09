"""
Welele Media™ — Audience Telemetry & Event Ingestion Router (GAP-004)
High-throughput event tracking bus and SQL retention curve aggregation.
"""

from fastapi import APIRouter, BackgroundTasks, Query
from repositories.event_repository import event_repository
from schemas.telemetry_schemas import TelemetryEventPayload, EpisodeRetentionResponse

router = APIRouter(prefix="/events", tags=["Audience Telemetry & Event Spine"])

@router.post("/track")
def track_event(payload: TelemetryEventPayload, background_tasks: BackgroundTasks):
    """
    Asynchronously ingests viewing telemetry beacons (episode_started, heartbeat, cliffhanger_reached, unlock).
    """
    background_tasks.add_task(event_repository.ingest_event, payload)
    return {"status": "accepted", "event": payload.event_name}

@router.get("/retention/{series_id}/{episode_id}", response_model=EpisodeRetentionResponse)
def get_retention_telemetry(series_id: str, episode_id: str):
    """
    Returns aggregated retention drop-off heatmaps and cliffhanger conversion % calculated from event logs.
    """
    return event_repository.get_episode_retention(series_id, episode_id)
