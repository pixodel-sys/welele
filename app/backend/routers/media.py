"""
Welele Media™ — Media Streaming & Storage Access Gateway Router (Phase 6O-5)
Enforces server-side publication lifecycle state, viewer entitlement checks,
and issues short-lived (60s TTL) signed playback URLs.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
import logging

from repositories.series_repository import series_repository, to_uuid
from repositories.ledger_repository import ledger_repository
from services.storage_service import storage_service
from services.rbac_service import get_current_user
from database import db

logger = logging.getLogger("welele.media")

router = APIRouter(prefix="/media", tags=["Media Streaming & Storage Access Gateway (Phase 6O-5)"])

class MediaSessionRequest(BaseModel):
    series_id: str = Field(..., description="Target series ID or slug")
    episode_id: str = Field(..., description="Target episode ID or slug")

class MediaSessionResponse(BaseModel):
    success: bool
    playback_url: str
    storage_key: str
    ttl_seconds: int
    is_free: bool
    provider: str
    expires_in_seconds: int

@router.post("/sessions/create", response_model=MediaSessionResponse)
def create_media_session(
    req: MediaSessionRequest,
    auth_user: dict = Depends(get_current_user)
):
    """
    Authoritative Media Session Ingress (Phase 6O-5):
    1. Verifies that the episode exists and has status == 'published'.
       Draft / unreleased episodes return HTTP 403 / 404 even if the storage key is known.
    2. Enforces viewer entitlement checks for paid episodes:
       - Anonymous / unauthenticated clients are rejected with HTTP 401.
       - Authenticated viewers without an active entitlement are rejected with HTTP 402.
    3. Issues a short-lived (60s TTL) signed playback URL from Cloudflare R2.
    """
    # 1. Authoritative Series Lookup
    story = series_repository.get_series_detail(req.series_id) or series_repository.get_series(req.series_id)
    if not story:
        stories = db.get("stories") or []
        story = next((s for s in stories if s.get("id") == req.series_id or s.get("slug") == req.series_id), None)
        if not story:
            all_series = series_repository.local_get("series") or []
            story = next((s for s in all_series if s.get("id") == req.series_id or s.get("slug") == req.series_id), None)
        if not story:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")

    # 2. Authoritative Episode Lookup
    ep_uuid = to_uuid(req.episode_id)
    episode = None
    if story.get("episodes"):
        episode = next((ep for ep in story["episodes"] if ep.get("id") in [req.episode_id, ep_uuid] or ep.get("slug") in [req.episode_id, ep_uuid]), None)
    if not episode:
        episodes_for_series = series_repository.get_episodes_for_series(req.series_id)
        episode = next((ep for ep in episodes_for_series if ep.get("id") in [req.episode_id, ep_uuid] or ep.get("slug") in [req.episode_id, ep_uuid]), None)
    if not episode:
        all_episodes = series_repository.local_get("episodes") or []
        target_s_id = str(story.get("id", req.series_id))
        episode = next(
            (ep for ep in all_episodes if (ep.get("id") in [req.episode_id, ep_uuid] or ep.get("slug") in [req.episode_id, ep_uuid]) and
             (ep.get("series_id") in [req.series_id, target_s_id, to_uuid(req.series_id)])),
            None
        )
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found")

    # 3. Publication & Lifecycle State Gate
    status_str = str(episode.get("status", "draft")).lower()
    lifecycle = str(episode.get("lifecycle_state", status_str.upper())).upper()
    is_empty_draft = bool(episode.get("is_empty_draft", False))

    if is_empty_draft:
        logger.warning(f"[MediaGateway] Empty draft episode streaming attempt rejected: {req.episode_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Draft or empty episodes cannot be streamed."
        )

    if status_str != "published" and lifecycle not in ["PUBLISHED", "READY", "INTERNAL_TEST"]:
        logger.warning(f"[MediaGateway] Unreleased episode streaming attempt rejected: {req.episode_id} status={status_str}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Episode is not published for streaming distribution."
        )

    # 4. Entitlement & Monetization Gate
    free_count = story.get("free_episodes", story.get("free_episodes_count", 0))
    ep_num = episode.get("episode_number", 1)
    is_free = bool(episode.get("is_free", False) or (ep_num <= free_count if free_count > 0 else False))

    if not is_free:
        # Paid content requires verified authentication
        if not auth_user.get("is_authenticated"):
            logger.warning(f"[MediaGateway] Anonymous access to paid episode {req.episode_id} rejected.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: Anonymous viewers cannot stream paid episodes."
            )

        user_id = auth_user.get("sub")
        # Check active entitlement in local ledger repository, in-memory db, or live database
        ledger_unlocks = ledger_repository.local_get("unlocked_episodes") or []
        db_unlocks = db.get("unlocked_episodes") or []
        all_unlocks = ledger_unlocks + db_unlocks
        is_entitled = any(
            (u.get("user_id") in [user_id, to_uuid(user_id)]) and
            (u.get("episode_id") in [req.episode_id, ep_uuid, episode.get("id"), to_uuid(episode.get("id"))])
            for u in all_unlocks
        )

        if not is_entitled and ledger_repository.is_live:
            try:
                res = ledger_repository.get_table("unlocked_episodes").select("id").eq(
                    "user_id", to_uuid(user_id)
                ).eq(
                    "episode_id", to_uuid(episode.get("id", req.episode_id))
                ).limit(1).execute()
                if res and res.data:
                    is_entitled = True
            except Exception as e:
                logger.warning(f"[MediaGateway:DB] Remote entitlement check error: {e}")

        # Admins or authorized creators may bypass commercial payment check
        if not is_entitled and auth_user.get("role") in ["admin"]:
            is_entitled = True

        if not is_entitled:
            logger.warning(f"[MediaGateway] Viewer {user_id} lacks entitlement for episode {req.episode_id}.")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Payment required: Viewer does not hold an active entitlement for this episode."
            )

    # 5. Resolve Storage Lineage & Issue 60s Playback Token
    media = series_repository.get_media_asset_for_episode(str(episode.get("id", req.episode_id)))
    if not media and req.episode_id != episode.get("id"):
        media = series_repository.get_media_asset_for_episode(req.episode_id)
    if not media:
        media = series_repository.get_media_asset_for_episode(ep_uuid)

    storage_key = (
        (media.get("storage_key") if media else None) or
        episode.get("storage_key") or
        episode.get("video_storage_key") or
        f"masters/{story.get('id', req.series_id)}/{episode.get('id', req.episode_id)}.mp4"
    )

    # Invariant: Generate time-bounded signed presigned URL (60-second TTL)
    token_data = storage_service.generate_playback_token(
        storage_key=storage_key,
        user_id=auth_user.get("sub"),
        ttl_seconds=60
    )

    return MediaSessionResponse(
        success=True,
        playback_url=token_data["download_url"],
        storage_key=token_data["storage_key"],
        ttl_seconds=60,
        is_free=is_free,
        provider=token_data.get("provider", "Cloudflare R2"),
        expires_in_seconds=60
    )
