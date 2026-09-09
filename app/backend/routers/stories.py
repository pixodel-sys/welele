"""
Welele Media™ — Legacy Stories & Episodes Compatibility Router
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from repositories.series_repository import series_repository
from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/stories", tags=["Stories & Episodes (Legacy Alias)"])

@router.get("/feed")
def get_feed(genre: Optional[str] = None, language: Optional[str] = None):
    series_list = series_repository.list_feed(genre=genre, language=language)
    ranked_series = recommendation_service.score_stories(series_list)
    return {"stories": ranked_series, "series": ranked_series, "total": len(ranked_series)}

@router.get("/trending")
def get_trending():
    series_list = series_repository.list_feed()
    trending = [s for s in series_list if s.get("is_trending")]
    return {"trending": trending}

@router.get("/{story_id}")
def get_story_detail(story_id: str):
    series = series_repository.get_series_detail(story_id)
    if not series:
        raise HTTPException(status_code=404, detail="Story not found")
    return series

@router.get("/{story_id}/episodes/{episode_id}")
def get_episode(story_id: str, episode_id: str):
    series = series_repository.get_series_detail(story_id)
    if not series:
        raise HTTPException(status_code=404, detail="Story not found")

    episode = next((ep for ep in series.get("episodes", []) if ep["id"] == episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {"story": series, "series": series, "episode": episode}

@router.post("/like/{story_id}")
def like_story(story_id: str):
    series = series_repository.get_series_detail(story_id)
    if not series:
        raise HTTPException(status_code=404, detail="Story not found")

    new_likes = series.get("total_likes", 0) + 1
    series_repository.local_update("series", "id", story_id, {"total_likes": new_likes})
    return {"success": True, "total_likes": new_likes}
