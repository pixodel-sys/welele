from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from database import db
from services.recommendation_service import recommendation_service

router = APIRouter(prefix="/stories", tags=["Stories & Episodes"])

@router.get("/feed")
def get_feed(genre: Optional[str] = None, language: Optional[str] = None):
    stories = db.get("stories")
    
    if genre and genre != "All":
        stories = [s for s in stories if genre.lower() in s.get("genre", "").lower()]
        
    if language and language != "All":
        stories = [s for s in stories if language.lower() in [l.lower() for l in s.get("available_languages", [])]]
        
    ranked_stories = recommendation_service.score_stories(stories)
    return {"stories": ranked_stories, "total": len(ranked_stories)}

@router.get("/trending")
def get_trending():
    stories = db.get("stories")
    trending = [s for s in stories if s.get("is_trending")]
    return {"trending": trending}

@router.get("/{story_id}")
def get_story_detail(story_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == story_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.get("/{story_id}/episodes/{episode_id}")
def get_episode(story_id: str, episode_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == story_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    episode = next((ep for ep in story.get("episodes", []) if ep["id"] == episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {"story": story, "episode": episode}

@router.post("/like/{story_id}")
def like_story(story_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == story_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    new_likes = story.get("total_likes", 0) + 1
    db.update("stories", story_id, {"total_likes": new_likes})
    return {"success": True, "total_likes": new_likes}
