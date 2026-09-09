"""
Welele Media™ — Audience Intelligence & Evidence Router (P2)
Exposes endpoints for diagnostic evidence, versioned recommendations, and Story Forge contextual guidance.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from services.intelligence_service import intelligence_service
from services.analytics_service import analytics_service

router = APIRouter(prefix="/intelligence", tags=["Audience & Story Intelligence (P2)"])

@router.get("/diagnostics/{series_id}/{episode_id}")
def get_episode_diagnostics(series_id: str, episode_id: str, ip_id: Optional[str] = "ip_blood_ties"):
    """
    Generates and persists an immutable diagnostic evidence artifact from retention signals.
    """
    result = intelligence_service.generate_episode_diagnostic_evidence(
        ip_id=ip_id or "ip_blood_ties",
        series_id=series_id,
        episode_id=episode_id
    )
    return result

@router.get("/recommendations/{series_id}")
def get_series_recommendations(series_id: str):
    """
    Returns all actionable, confidence-gated narrative recommendations for a series.
    """
    recs = intelligence_service.get_recommendations_for_series(series_id)
    return {
        "series_id": series_id,
        "total_active_recommendations": len(recs),
        "recommendations": recs
    }

@router.get("/story-forge-context/{series_id}")
def get_story_forge_context(series_id: str):
    """
    Returns latest intelligence recommendations formatted for direct injection into Story Forge AI prompts.
    """
    context = intelligence_service.get_story_forge_context(series_id)
    return context
