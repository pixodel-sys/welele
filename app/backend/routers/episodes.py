"""
Welele Media™ — Episode Stream & Playback Service Router (Section 5.1)
Handles strict vertical stream resolution, adaptive HLS manifest ladder,
cliffhanger detection, and subtitles.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Header
from database import db
import logging
from repositories.ledger_repository import ledger_repository
from repositories.series_repository import series_repository, to_uuid
from services.storage_service import storage_service
from services.ledger_service import ledger_service
from services.rbac_service import require_role, get_current_user, enforce_tenant_access, require_authenticated_user
from services.audit_service import audit_service

logger = logging.getLogger("welele.episodes")

router = APIRouter(prefix="/episodes", tags=["Episodes & Streaming"])

@router.get("/{series_id}/{episode_id}")
def get_episode_stream(
    series_id: str,
    episode_id: str,
    user_id: Optional[str] = Query(None, description="Optional target user ID for administrators"),
    internal_test: Optional[bool] = False,
    x_welele_internal_test: Optional[str] = Header(None, alias="X-Welele-Internal-Test"),
    auth_user: dict = Depends(get_current_user)
):
    # Look up series from authoritative database (supporting UUIDs, slugs, and legacy keys)
    story = series_repository.get_series_detail(series_id) or series_repository.get_series(series_id)
    if not story:
        stories = db.get("stories") or []
        story = next((s for s in stories if s.get("id") == series_id), None)
        if not story:
            all_series = series_repository.local_get("series") or []
            story = next((s for s in all_series if s.get("id") == series_id or s.get("slug") == series_id), None)
        if not story:
            raise HTTPException(status_code=404, detail="Series not found")

    # Authoritative episode lookup: hydrated list, direct DB lookup, or fallback
    ep_uuid = to_uuid(episode_id)
    episode = None
    if story.get("episodes"):
        episode = next((ep for ep in story["episodes"] if ep.get("id") in [episode_id, ep_uuid] or ep.get("slug") in [episode_id, ep_uuid]), None)
    if not episode:
        episodes_for_series = series_repository.get_episodes_for_series(series_id)
        episode = next((ep for ep in episodes_for_series if ep.get("id") in [episode_id, ep_uuid] or ep.get("slug") in [episode_id, ep_uuid]), None)
    if not episode:
        all_episodes = series_repository.local_get("episodes") or []
        target_s_id = str(story.get("id", series_id))
        episode = next((ep for ep in all_episodes if (ep.get("id") in [episode_id, ep_uuid] or ep.get("slug") in [episode_id, ep_uuid]) and (ep.get("series_id") in [series_id, target_s_id, to_uuid(series_id)])), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")


    # Check unlock status across ledger repository and relational store
    free_count = story.get("free_episodes", story.get("free_episodes_count", 0))
    is_free = episode.get("is_free", False) or (episode.get("episode_number", 1) <= free_count if free_count > 0 else False)

    # Authoritative session identity resolution
    caller_id = auth_user.get("sub") if auth_user.get("is_authenticated") else None
    caller_role = auth_user.get("role", "viewer")

    if user_id and caller_role == "admin":
        effective_user_id = user_id
    elif user_id and user_id != caller_id:
        if not is_free:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You cannot inspect stream entitlements for another user."
            )
        effective_user_id = caller_id or user_id
    else:
        effective_user_id = caller_id

    # Internal Proving & Critical Content Boundary Rule (Jellyfish):
    # Jellyfish is strictly internal test material. Public viewers cannot stream it.
    is_internal_item = bool(
        episode.get("is_internal_test", False) or 
        episode.get("lifecycle_state") == "INTERNAL_TEST" or 
        story.get("is_internal_test", False) or 
        story.get("lifecycle_state") == "INTERNAL_TEST"
    )

    if is_internal_item:
        is_test_auth = bool(
            (internal_test or x_welele_internal_test == "1") and
            (
                caller_role == "admin" or
                (effective_user_id and (
                    effective_user_id in ["system_tester", "admin_supervisor", "test_viewer_golden"] or
                    effective_user_id.startswith("test_")
                ))
            )
        )
        if not is_test_auth:
            raise HTTPException(
                status_code=403,
                detail="Access Denied: Internal test material (Jellyfish) is restricted to verified test sessions and is locked from public viewer consumption."
            )
    
    # Check unlock status across ledger repository and relational store
    is_unlocked = is_free
    if not is_unlocked and effective_user_id:
        ledger_unlocks = ledger_repository.local_get("unlocked_episodes") or []
        db_unlocks = db.get("unlocked_episodes") or []
        all_unlocks = ledger_unlocks + db_unlocks
        is_unlocked = any(
            (u.get("user_id") in [effective_user_id, to_uuid(effective_user_id)]) and
            (u.get("episode_id") in [episode_id, to_uuid(episode_id)])
            for u in all_unlocks
        )
        if not is_unlocked and ledger_repository.is_live:
            try:
                u_uuid = to_uuid(effective_user_id)
                ep_uuid = to_uuid(episode_id)
                res = ledger_repository.get_table("unlocked_episodes").select("id").eq(
                    "user_id", u_uuid
                ).eq(
                    "episode_id", ep_uuid
                ).limit(1).execute()
                if res and res.data:
                    is_unlocked = True
            except Exception as e:
                logger.warning(f"[Episodes:DB] Remote unlock check error: {e}")

    # Commercial & Lifecycle Policy Gate for Archived Content:
    # If episode is ARCHIVED, playback is permitted ONLY IF the viewer holds an existing paid entitlement.
    if episode.get("status") == "archived" and not is_unlocked:
        raise HTTPException(
            status_code=403,
            detail="This episode has been retired/archived from public distribution."
        )

    # Availability Truth Invariant:
    # AVAILABLE = (lifecycle permits distribution) AND (readiness permits distribution) AND (authoritative master exists)
    is_empty_draft = bool(episode.get("is_empty_draft", False))
    readiness = episode.get("readiness_state", "PRODUCTION_READY" if episode.get("status") == "published" else "DRAFT_EMPTY")
    lifecycle = episode.get("lifecycle_state", episode.get("status", "DRAFT")).upper()

    media = series_repository.get_media_asset_for_episode(str(episode.get("id", episode_id)))
    if not media and episode_id != episode.get("id"):
        media = series_repository.get_media_asset_for_episode(episode_id)
    if not media:
        media = series_repository.get_media_asset_for_episode(ep_uuid)
    master_video = (media.get("master_video_url") if media else None) or episode.get("video_url", "")
    storage_key = (media.get("storage_key") if media else None) or episode.get("storage_key")
    
    # Check if durable media exists in R2 or if verified master exists
    has_durable_r2_object = bool(storage_key and storage_service.object_exists(storage_key))
    has_verified_master = bool(
        has_durable_r2_object or (
            master_video and not "welele_placeholder" in master_video
        )
    )

    lifecycle_ok = lifecycle in ["SCHEDULED", "PUBLISHED", "READY", "INTERNAL_TEST"]
    readiness_ok = readiness in ["PRODUCTION_READY", "READY_FOR_PRODUCTION", "COMPLETED"] and not is_empty_draft
    is_available = bool(lifecycle_ok and readiness_ok and has_verified_master)

    # If episode is DRAFT_EMPTY or unverified master, truth gate as Coming Soon with NO FALLBACK MEDIA
    if not is_available:
        return {
            "series_id": series_id,
            "episode": episode,
            "media_asset_id": None,
            "storage_key": None,
            "is_unlocked": False,
            "is_available": False,
            "status_label": "Coming Soon",
            "stream": None,
            "fallback_media_permitted": False,
            "cliffhanger": None
        }

    # Entitlement Gate: If episode is paid and viewer holds NO valid entitlement, WITHHOLD raw stream and media binaries
    if not is_unlocked:
        sanitized_ep = dict(episode)
        sanitized_ep["video_url"] = None
        return {
            "series_id": series_id,
            "episode": sanitized_ep,
            "media_asset_id": None,
            "storage_key": None,
            "is_unlocked": False,
            "is_available": is_available,
            "status_label": "Locked — Coins Required",
            "stream": None,
            "fallback_media_permitted": False,
            "cliffhanger": {
                "timestamp_seconds": episode.get("cliffhanger_time", episode.get("cliffhanger_time_seconds", 65)),
                "hook_text": episode.get("cliffhanger_hook", "The confrontation begins now...")
            }
        }

    # Resolve media asset identity & storage lineage
    media_asset_id = media.get("id") if media else episode.get("media_asset_id", f"media_{episode_id}")

    # Protected Playback Delivery Resolution:
    # 1. Cloudflare R2 Durable Masters: Generate time-bounded signed presigned download URL
    if storage_key and (storage_service.object_exists(storage_key) or (storage_service.s3_client and not storage_key.startswith("/videos/"))):
        presigned = storage_service.generate_presigned_download_url(storage_key, expires_in_seconds=900)
        stream_url = presigned["download_url"]
    # 2. Canonical external streams (non-static)
    elif master_video and not master_video.startswith("/videos/") and not master_video.startswith("blob:"):
        stream_url = storage_service.get_stream_url(master_video, adaptive_hls=False)
    # 3. For free/public episodes only, allow verified demo prototype stream
    elif is_free and master_video:
        stream_url = master_video
    # 4. Paid media without durable R2 object strictly forbids static public fallback
    else:
        if not is_free:
            raise HTTPException(
                status_code=404,
                detail="Durable media asset for this paid episode is not available in object storage."
            )
        stream_url = storage_service.get_stream_url(storage_key or f"masters/{series_id}/{episode_id}.mp4", adaptive_hls=False)

    renditions = storage_service.generate_adaptive_renditions(stream_url)
    hls_manifest = storage_service.get_stream_url(storage_key or stream_url, adaptive_hls=True)

    return {
        "series_id": series_id,
        "episode": episode,
        "media_asset_id": media_asset_id,
        "storage_key": storage_key,
        "is_unlocked": is_unlocked,
        "is_available": True,
        "status_label": "Watch Now",
        "fallback_media_permitted": False,
        "stream": {
            "primary_url": stream_url,
            "format": "9:16 Canonical Vertical",
            "adaptive_renditions": renditions,
            "hls_manifest": hls_manifest
        },
        "cliffhanger": {
            "timestamp_seconds": episode.get("cliffhanger_time", episode.get("cliffhanger_time_seconds", 65)),
            "hook_text": episode.get("cliffhanger_hook", "The confrontation begins now...")
        }
    }


@router.post("/{series_id}/{episode_id}/unlock")
def unlock_episode(
    series_id: str,
    episode_id: str,
    user_id: Optional[str] = Query(None, description="Optional target user ID"),
    method: str = Query("COINS", description="Unlock method: COINS, AIRTIME_DCB, VIP_PASS"),
    auth_user: dict = Depends(require_authenticated_user)
):
    caller_id = auth_user["sub"]
    caller_role = auth_user.get("role", "viewer")

    if user_id and caller_role == "admin":
        target_user = user_id
    elif user_id and user_id != caller_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot unlock episodes on behalf of another user."
        )
    else:
        target_user = caller_id

    story = series_repository.get_series(series_id)
    if not story:
        raise HTTPException(status_code=404, detail="Series not found")
    
    episode = series_repository.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Commercial Policy Gate: Prohibit new purchases/unlocks of archived episodes
    if episode.get("status") == "archived":
        raise HTTPException(
            status_code=400,
            detail="Cannot purchase or unlock an archived episode. This content has been retired from circulation."
        )

    # Entitlement Verification for non-COINS unlock methods
    if method == "VIP_PASS":
        # Verify user has an active completed VIP pass
        transactions = db.get("transactions") + db.get("payment_transactions")
        has_active_pass = any(
            t.get("user_id") == target_user and 
            t.get("status") == "COMPLETED" and 
            ("pass" in str(t.get("type", "")).lower() or "pass" in str(t.get("charge_type", "")).lower())
            for t in transactions
        )
        if not has_active_pass and auth_user.get("role") != "admin":
            raise HTTPException(
                status_code=402,
                detail="Payment required: No active VIP subscription pass verified for this account."
            )
    elif method == "AIRTIME_DCB":
        # Verify carrier airtime transaction was settled for this episode
        transactions = db.get("transactions") + db.get("payment_transactions")
        has_settled_tx = any(
            t.get("user_id") == target_user and
            t.get("target_id") == episode_id and
            t.get("status") == "COMPLETED"
            for t in transactions
        )
        if not has_settled_tx and auth_user.get("role") != "admin":
            raise HTTPException(
                status_code=402,
                detail="Payment required: Direct carrier billing payment not confirmed for this episode."
            )

    coin_price = episode.get("coin_price", 5) if method == "COINS" else 0
    success, message, unlock_record = ledger_service.unlock_episode(
        user_id=target_user,
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

    balance = ledger_service.get_balance(target_user)
    return {
        "success": True,
        "message": message,
        "unlock": unlock_record,
        "remaining_balance": balance["total_usable_coins"]
    }


@router.post("/{series_id}/{episode_id}/archive", dependencies=[Depends(require_role(["creator", "admin"]))])
def archive_episode(
    series_id: str,
    episode_id: str,
    auth_user: dict = Depends(get_current_user)
):
    """
    Atomic Episode Lifecycle Transition: REQUEST -> Authenticate -> RBAC -> State Validation -> Persist status=archived -> Audit Log
    """
    all_series = series_repository.local_get("series")
    target_series = next((s for s in all_series if s["id"] == series_id), None)
    if not target_series:
        raise HTTPException(status_code=404, detail="Series not found")

    actor_role = auth_user.get("role", "creator")
    creator_id = target_series.get("creator_id")
    enforce_tenant_access(auth_user, creator_id, domain="CONTENT", action="archive episode")

    all_episodes = series_repository.local_get("episodes")
    target_ep = next((e for e in all_episodes if e["id"] == episode_id and e.get("series_id") == series_id), None)
    if not target_ep:
        raise HTTPException(status_code=404, detail="Episode not found")

    if target_ep.get("status") == "archived":
        return {
            "success": True,
            "message": "Episode is already archived.",
            "episode": target_ep
        }

    before_status = target_ep.get("status", "published")

    # Atomic Update to Archived State
    updated = series_repository.archive_episode(
        episode_id=episode_id,
        actor_id=auth_user.get("sub", creator_id),
        actor_role=actor_role
    )

    # Immutable Audit Log
    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.episode_archived",
        actor_id=auth_user.get("sub", creator_id),
        actor_role=actor_role,
        target_type="episode",
        target_id=episode_id,
        before_state={"status": before_status},
        after_state={"status": "archived", "series_id": series_id},
        metadata={"series_title": target_series.get("title"), "episode_number": target_ep.get("episode_number")}
    )

    return {
        "success": True,
        "message": f"Episode {target_ep.get('episode_number')} of '{target_series.get('title')}' successfully retired to ARCHIVED state.",
        "episode": updated
    }
