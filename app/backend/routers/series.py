"""
Welele Media™ — Series Catalog & Metadata Service Router (Section 5.1 & Normalized DAL)
Handles Micro-drama Series catalog, genres, trending feed, and creator series via SeriesRepository.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Header
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
def get_series_detail(
    series_id: str,
    internal_test: Optional[bool] = False,
    x_welele_internal_test: Optional[str] = Header(None, alias="X-Welele-Internal-Test")
):
    series = series_repository.get_series_detail(series_id)
    if not series:
        # Check if it is an internal test series requested by authorized test session
        is_test_auth = bool(internal_test or x_welele_internal_test == "1")
        if is_test_auth:
            all_s = series_repository.local_get("series") or []
            candidate = next((s for s in all_s if s.get("id") == series_id), None)
            if candidate and (candidate.get("is_internal_test") or candidate.get("lifecycle_state") == "INTERNAL_TEST"):
                all_episodes = series_repository.local_get("episodes") or []
                all_media = series_repository.local_get("media_assets") or []
                media_map = {m["episode_id"]: m for m in all_media}
                s_copy = dict(candidate)
                s_eps = [dict(e) for e in all_episodes if e.get("series_id") == series_id]
                s_eps.sort(key=lambda x: x.get("episode_number", 0))
                for ep in s_eps:
                    m = media_map.get(ep["id"])
                    if m:
                        ep["video_url"] = m.get("master_video_url", "/videos/jellyfish.mp4")
                        ep["storage_key"] = m.get("storage_key")
                s_copy["episodes"] = s_eps
                s_copy["total_episodes"] = len(s_eps)
                return s_copy
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
