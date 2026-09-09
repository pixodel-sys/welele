"""
Welele Media™ — Series Catalog & Metadata Service Router (Section 5.1)
Handles Micro-drama Series catalog, genres, trending feed, and creator series.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from database import db
from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/series", tags=["Series & Catalog"])

@router.get("")
@router.get("/feed")
def get_series_feed(genre: Optional[str] = None, language: Optional[str] = None):
    stories = db.get("stories")
    
    if genre and genre != "All":
        stories = [s for s in stories if genre.lower() in s.get("genre", "").lower()]
        
    if language and language != "All":
        stories = [s for s in stories if language.lower() in [l.lower() for l in s.get("available_languages", [])]]
        
    ranked_stories = recommendation_service.score_stories(stories)
    return {"series": ranked_stories, "stories": ranked_stories, "total": len(ranked_stories)}

@router.get("/trending")
def get_trending_series():
    stories = db.get("stories")
    trending = [s for s in stories if s.get("is_trending")]
    return {"trending": trending, "total": len(trending)}

@router.get("/{series_id}")
def get_series_detail(series_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == series_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Series not found")
    return story

@router.post("/{series_id}/like")
def like_series(series_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == series_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Series not found")
    
    new_likes = story.get("total_likes", 0) + 1
    db.update("stories", series_id, {"total_likes": new_likes})
    return {"success": True, "total_likes": new_likes}
