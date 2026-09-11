"""
Welele Media™ — Episode Stream & Playback Service Router (Section 5.1)
Handles strict 9:16 vertical stream resolution, adaptive HLS manifest ladder,
cliffhanger detection, and subtitles.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from database import db
from repositories.ledger_repository import ledger_repository
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
    
    # Check unlock status across ledger repository and relational store
    is_free = episode.get("is_free", False) or episode.get("episode_number", 1) <= story.get("free_episodes_count", 3)
    ledger_unlocks = ledger_repository.local_get("unlocked_episodes") or []
    db_unlocks = db.get("unlocked_episodes") or []
    all_unlocks = ledger_unlocks + db_unlocks
    is_unlocked = is_free or any(u.get("user_id") == user_id and u.get("episode_id") == episode_id for u in all_unlocks)

    # Resolve media asset identity & storage lineage
    all_media = series_repository.local_get("media_assets")
    media = next((m for m in all_media if m.get("episode_id") == episode_id), None)
    media_asset_id = media.get("id") if media else episode.get("media_asset_id", f"media_{episode_id}")
    storage_key = media.get("storage_key") if media else episode.get("storage_key", f"masters/{series_id}/{episode_id}.mp4")

    # Authoritative stream resolution hierarchy:
    # 1. Development Seed Media: Bundled demo media (/videos/...) for seeded prototype catalog
    # 2. Production Masters: Physical binaries in Object Storage (R2 / local store via storage_key)
    # 3. Canonical External CDN Streams
    master_video = (media.get("master_video_url") if media else None) or episode.get("video_url", "")

    if master_video and (master_video.startswith("/videos/") or master_video.startswith("/media/")):
        stream_url = master_video
    elif storage_key and storage_service.get_stored_binary(storage_key) is not None:
        stream_url = storage_service.get_stream_url(storage_key, adaptive_hls=False)
    elif master_video and not master_video.startswith("blob:"):
        stream_url = storage_service.get_stream_url(master_video, adaptive_hls=False)
    else:
        stream_url = storage_service.get_stream_url(storage_key or f"masters/{series_id}/{episode_id}.mp4", adaptive_hls=False)


    renditions = storage_service.generate_adaptive_renditions(stream_url)
    hls_manifest = storage_service.get_stream_url(storage_key or stream_url, adaptive_hls=True)


    return {
        "series_id": series_id,
        "episode": episode,
        "media_asset_id": media_asset_id,
        "storage_key": storage_key,
        "is_unlocked": is_unlocked,
        "stream": {
            "primary_url": stream_url,
            "format": "9:16 Canonical Vertical",
            "adaptive_renditions": renditions,
            "hls_manifest": hls_manifest
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
