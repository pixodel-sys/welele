"""
Welele Media™ — Episode Stream & Playback Service Router (Section 5.1)
Handles strict 9:16 vertical stream resolution, adaptive HLS manifest ladder,
cliffhanger detection, and subtitles.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from database import db
from repositories.series_repository import series_repository
from services.storage_service import storage_service
from services.ledger_service import ledger_service

router = APIRouter(prefix="/episodes", tags=["Episodes & Streaming"])

@router.get("/{series_id}/{episode_id}")
def get_episode_stream(
    series_id: str,
    episode_id: str,
    user_id: Optional[str] = "user_sa_01"
):
    story = series_repository.get_series_detail(series_id)
    if not story:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == series_id), None)
        if not story:
            raise HTTPException(status_code=404, detail="Series not found")
    
    episode = next((ep for ep in story.get("episodes", []) if ep["id"] == episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Check unlock status
    is_free = episode.get("is_free", False) or episode.get("episode_number", 1) <= story.get("free_episodes_count", 3)
    unlocks = db.get("unlocked_episodes")
    is_unlocked = is_free or any(u.get("user_id") == user_id and u.get("episode_id") == episode_id for u in unlocks)

    # Resolve edge CDN URL and adaptive renditions
    video_raw = episode.get("video_url", "")
    stream_url = storage_service.get_stream_url(video_raw, adaptive_hls=False)
    renditions = storage_service.generate_adaptive_renditions(video_raw)

    return {
        "series_id": series_id,
        "episode": episode,
        "is_unlocked": is_unlocked,
        "stream": {
            "primary_url": stream_url,
            "format": "9:16 Canonical Vertical",
            "adaptive_renditions": renditions,
            "hls_manifest": storage_service.get_stream_url(video_raw, adaptive_hls=True)
        },
        "cliffhanger": {
            "timestamp_seconds": episode.get("cliffhanger_time", 65),
            "hook_text": episode.get("cliffhanger_hook", "The confrontation begins now...")
        }
    }

@router.post("/{series_id}/{episode_id}/unlock")
def unlock_episode(
    series_id: str,
    episode_id: str,
    user_id: str = Query(..., description="User ID"),
    method: str = Query("COINS", description="Unlock method: COINS, AIRTIME_DCB, VIP_PASS")
):
    story = series_repository.get_series_detail(series_id)
    if not story:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == series_id), None)
        if not story:
            raise HTTPException(status_code=404, detail="Series not found")
    
    episode = next((ep for ep in story.get("episodes", []) if ep["id"] == episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    coin_price = episode.get("coin_price", 5) if method == "COINS" else 0
    success, message, unlock_record = ledger_service.unlock_episode(
        user_id=user_id,
        episode_id=episode_id,
        story_id=series_id,
        unlock_method=method,
        coin_price=coin_price
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Credit creator royalty split
    creator_id = story.get("creator_id")
    if creator_id:
        creators = db.get("creators")
        creator = next((c for c in creators if c["id"] == creator_id), None)
        if creator:
            new_coins = creator.get("coin_earnings", 0) + coin_price
            db.update("creators", creator_id, {"coin_earnings": new_coins})

    balance = ledger_service.get_balance(user_id)
    return {
        "success": True,
        "message": message,
        "unlock": unlock_record,
        "remaining_balance": balance["total_usable_coins"]
    }
