"""
Welele Media™ — Viewer Telemetry Router (Phase 6 Measurement Layer)
Provides high-integrity, non-blocking ingestion of Viewer Telemetry Events,
session event reconstruction, and empirical validation reports.
"""

from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from repositories.telemetry_repository import telemetry_repository
from schemas.telemetry_schemas import TelemetryEventPayload, EpisodeRetentionResponse
from schemas.viewer_telemetry_models import ViewerTelemetryEvent, TelemetryEvidencePackage
from schemas.projection_models import ContentEvidenceProjection, ViewerEvidenceProjection
from services.viewer_telemetry_service import viewer_telemetry_service
from services.evidence_projection_service import evidence_projection_service

router = APIRouter(prefix="/telemetry", tags=["Viewer Telemetry & Event Spine"])


# ---------------------------------------------------------------------------
# Phase 6 Authoritative Telemetry Endpoints
# ---------------------------------------------------------------------------

@router.post("/events")
def ingest_telemetry_event(event: ViewerTelemetryEvent):
    """
    Ingests a single factual viewer telemetry event with idempotency and milestone guards.
    """
    result = viewer_telemetry_service.record_event(event)
    return result


@router.post("/batch")
def ingest_telemetry_batch(events: List[ViewerTelemetryEvent]):
    """
    Ingests a batch of queued client telemetry events with identical per-event validation.
    """
    result = viewer_telemetry_service.record_batch(events)
    return result


@router.get("/sessions/{session_id}", response_model=List[ViewerTelemetryEvent])
def get_session_telemetry(session_id: str):
    """
    Returns the chronologically ordered event trail for a viewing session.
    """
    return viewer_telemetry_service.get_session_events(session_id)


@router.get("/validation/isibusiso", response_model=TelemetryEvidencePackage)
def validate_isibusiso_telemetry():
    """
    Runs the controlled Phase 6 Telemetry Integrity Test on Isibusiso S1 E1.
    """
    return viewer_telemetry_service.execute_isibusiso_telemetry_validation()


# ---------------------------------------------------------------------------
# Phase B: Materialized Evidence Projection Endpoints
# ---------------------------------------------------------------------------

@router.get("/projections/content/{content_id}", response_model=ContentEvidenceProjection)
def get_content_evidence_projection(content_id: str, series_id: Optional[str] = Query(None)):
    """
    Returns the rebuildable Content Performance Matrix with full provenance.
    """
    return evidence_projection_service.build_content_projection(target_id=content_id, series_id=series_id)


@router.get("/projections/viewer/{session_or_viewer_id}", response_model=ViewerEvidenceProjection)
def get_viewer_evidence_projection(session_or_viewer_id: str):
    """
    Returns observational viewer evidence without persona guessing.
    """
    return evidence_projection_service.build_viewer_projection(
        viewer_id=session_or_viewer_id,
        anonymous_id=session_or_viewer_id
    )


# ---------------------------------------------------------------------------
# Deprecated Compatibility Endpoints (Rerouted through Unified Spine Storage)
# ---------------------------------------------------------------------------

@router.post("/events/track")
def track_legacy_event(payload: TelemetryEventPayload, background_tasks: BackgroundTasks):
    """
    Deprecated compatibility alias: saves to telemetry storage.
    """
    background_tasks.add_task(telemetry_repository.local_insert, "telemetry_events", payload.model_dump())
    return {"status": "accepted", "event": payload.event_name}


@router.get("/retention/{series_id}/{episode_id}", response_model=EpisodeRetentionResponse)
def get_legacy_retention(series_id: str, episode_id: str):
    """
    Unified retention endpoint backed by telemetry_repository.
    """
    return telemetry_repository.get_episode_retention(series_id, episode_id)
