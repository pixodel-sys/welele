"""
Welele Media™ — Series Catalog & Metadata Service Router (Section 5.1 & Normalized DAL)
Handles Micro-drama Series catalog, genres, trending feed, and creator series via SeriesRepository.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from repositories.series_repository import series_repository
from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/series", tags=["Series & Catalog"])

@router.get("")
@router.get("/feed")
def get_series_feed(genre: Optional[str] = None, language: Optional[str] = None):
    series_list = series_repository.list_feed(genre=genre, language=language)
    ranked_series = recommendation_service.score_stories(series_list)
    return {"series": ranked_series, "stories": ranked_series, "total": len(ranked_series)}

@router.get("/trending")
def get_trending_series():
    series_list = series_repository.list_feed()
    trending = [s for s in series_list if s.get("is_trending")]
    return {"trending": trending, "total": len(trending)}

@router.get("/{series_id}")
def get_series_detail(series_id: str):
    series = series_repository.get_series_detail(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series

@router.post("/{series_id}/like")
def like_series(series_id: str):
    series = series_repository.get_series_detail(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    new_likes = series.get("total_likes", 0) + 1
    series_repository.local_update("series", "id", series_id, {"total_likes": new_likes})
    return {"success": True, "total_likes": new_likes}
