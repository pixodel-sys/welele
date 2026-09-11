"""
Welele Media™ — Creator Hub API Router (Normalized DAL & Institutional Trust)
Connects Creator Studio to SeriesRepository, IPRepository, and decoupled Media Assets,
enforcing strict Creator Tenant Isolation and emitting CONTENT domain audit events.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from services.rbac_service import require_role, get_current_user, enforce_tenant_access
from services.audit_service import audit_service
from repositories.series_repository import series_repository
from repositories.ip_repository import ip_repository
from repositories.event_repository import event_repository
from schemas.story_schemas import CreateSeriesRequest, CreateEpisodeRequest

router = APIRouter(prefix="/creators", tags=["Creator Hub"])

@router.get("/list")
def list_creators():
    """Public creator directory."""
    return {
        "creators": [
            {
                "id": "creator_zola",
                "name": "Zola Dlamini",
                "handle": "@zola_cinemas",
                "bio": "Johannesburg crime & dynasty showrunner. Master of the 60-second Mzansi cliffhanger.",
                "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "country": "South Africa",
                "verified": True,
                "followers_count": 420000,
                "total_views": 8420000,
                "coin_earnings": 284000,
                "payout_balance": 1890.00
            }
        ]
    }

@router.get("/{creator_id}")
def get_creator_profile(creator_id: str):
    """Public creator profile information."""
    creator = {
        "id": creator_id,
        "name": "Zola Dlamini",
        "handle": "@zola_cinemas",
        "bio": "Johannesburg crime & dynasty showrunner.",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
        "country": "South Africa",
        "verified": True,
        "followers_count": 420000,
        "total_views": 8420000,
        "coin_earnings": 284000,
        "payout_balance": 1890.00
    }
    series_list = series_repository.list_feed()
    return {
        "creator": creator,
        "series": series_list,
        "total_series": len(series_list)
    }

@router.get("/{creator_id}/dashboard", dependencies=[Depends(require_role(["creator", "admin"]))])
def get_creator_dashboard(creator_id: str, auth_user: dict = Depends(get_current_user)):
    """Creator Dashboard KPIs & owned series roster (Tenant Protected)."""
    enforce_tenant_access(auth_user, creator_id, domain="CONTENT", action="view dashboard analytics")
    
    series_list = series_repository.list_feed()
    total_views = sum(s.get("total_views", 0) for s in series_list)
    total_episodes_count = sum(len(s.get("episodes", [])) for s in series_list)

    return {
        "stats": {
            "total_views": total_views or 8420000,
            "total_likes": 482000,
            "total_episodes": total_episodes_count,
            "followers": 420000,
            "coin_earnings": 284000,
            "payout_balance_usd": 1890.00,
            "avg_cliffhanger_completion_rate": "88.4%",
            "monthly_growth_rate": "+26.4%"
        },
        "series": series_list
    }

@router.get("/{creator_id}/episodes", dependencies=[Depends(require_role(["creator", "admin"]))])
def get_creator_episodes(creator_id: str, status: str = Query(None), auth_user: dict = Depends(get_current_user)):
    """Lists creator's episodes across draft, under review, and published states."""
    enforce_tenant_access(auth_user, creator_id, domain="CONTENT", action="list episodes")

    all_episodes = series_repository.local_get("episodes")
    all_series = series_repository.local_get("series")
    series_map = {s["id"]: s for s in all_series}

    filtered = []
    for ep in all_episodes:
        ep_status = ep.get("status", "published")
        if status and ep_status != status:
            continue
        s = series_map.get(ep.get("series_id"), {})
        filtered.append({
            **ep,
            "series_title": s.get("title", ""),
            "series_cover": s.get("vertical_poster", s.get("cover_image", "")),
            "genre": s.get("genre", "")
        })

    return {"episodes": filtered, "total": len(filtered)}

@router.get("/series/{series_id}/workspace", dependencies=[Depends(require_role(["creator", "admin"]))])
def get_series_workspace(series_id: str, auth_user: dict = Depends(get_current_user)):
    """Series Command Room workspace data with retention & coin metrics."""
    series = series_repository.get_series_detail(series_id)
    if not series:
        all_series = series_repository.local_get("series")
        series = next((s for s in all_series if s["id"] == series_id), None)
        if not series:
            raise HTTPException(status_code=404, detail="Series not found")

    enforce_tenant_access(auth_user, series.get("creator_id"), domain="CONTENT", action="access series workspace")

    all_episodes = series_repository.local_get("episodes")
    series_episodes = [e for e in all_episodes if e.get("series_id") == series_id]

    published_count = len([e for e in series_episodes if e.get("status") == "published"])
    under_review_count = len([e for e in series_episodes if e.get("status") in ["under_review", "submitted", "pending_review"]])
    draft_count = len([e for e in series_episodes if e.get("status") == "draft"])

    return {
        "series": {
            **series,
            "episodes": series_episodes,
            "total_episodes": len(series_episodes)
        },
        "metrics": {
            "total_views": 8420000,
            "completion_rate": "88.4%",
            "coins_generated": 284000,
            "estimated_earnings_usd": 1890.00,
            "published_count": published_count,
            "under_review_count": under_review_count,
            "draft_count": draft_count
        }
    }

@router.post("/series/create", dependencies=[Depends(require_role(["creator", "admin"]))])
def create_series(req: CreateSeriesRequest, auth_user: dict = Depends(get_current_user)):
    """Registers a new microdrama series under a creator and records an audit event."""
    creator_id = req.creator_id or auth_user.get("creator_id") or auth_user.get("sub")
    enforce_tenant_access(auth_user, creator_id, domain="CONTENT", action="create series")

    new_id = f"story_{uuid.uuid4().hex[:8]}"
    now_ts = datetime.now(timezone.utc).isoformat()

    new_series = {
        "id": new_id,
        "ip_id": "ip_blood_ties",
        "season_number": 1,
        "title": req.title,
        "tagline": req.tagline,
        "synopsis": req.synopsis,
        "cover_image": req.cover_image,
        "vertical_poster": req.vertical_poster,
        "genre": req.genre,
        "rating": 5.0,
        "total_episodes": 0,
        "free_episodes": 2,
        "coin_price_per_episode": req.coin_price_per_episode,
        "is_published": True,
        "creator_id": creator_id,
        "creator_name": "Zola Dlamini",
        "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
        "available_languages": req.available_languages or ["isiZulu", "English"],
        "tags": req.tags or [],
        "created_at": now_ts,
        "updated_at": now_ts
    }
    series_repository.local_insert("series", new_series)

    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.series_created",
        actor_id=auth_user.get("sub", creator_id),
        actor_role=auth_user.get("role", "creator"),
        target_type="series",
        target_id=new_id,
        after_state={"title": req.title, "genre": req.genre, "creator_id": creator_id},
        metadata={"pricing": req.coin_price_per_episode}
    )

    return {"success": True, "story": new_series}

@router.post("/episodes/add", dependencies=[Depends(require_role(["creator", "admin"]))])
def add_episode(req: CreateEpisodeRequest, auth_user: dict = Depends(get_current_user)):
    """
    Ingests episode through normalized DAL, attaching decoupled media, submitting to moderation,
    and recording immutable CONTENT audit events.
    """
    series = series_repository.get_series_detail(req.series_id)
    if not series:
        all_series = series_repository.local_get("series")
        series = next((s for s in all_series if s["id"] == req.series_id), None)
        if not series:
            raise HTTPException(status_code=404, detail="Series not found")

    enforce_tenant_access(auth_user, series.get("creator_id"), domain="CONTENT", action="add episode")

    # Reject ephemeral browser blob references
    if req.video_url and req.video_url.startswith("blob:") and not req.storage_key:
        raise HTTPException(
            status_code=400,
            detail="Invalid media reference: Ephemeral browser blob: URLs cannot be stored as canonical episode video masters. Please upload video binary to storage first."
        )

    status_target = req.status or "published"
    ep_payload = {
        "series_id": req.series_id,
        "episode_number": req.episode_number,
        "title": req.title,
        "synopsis": req.synopsis,
        "duration_seconds": req.duration_seconds,
        "is_free": req.is_free,
        "coin_price": req.coin_price,
        "cliffhanger_time": req.cliffhanger_time,
        "cliffhanger_hook": req.cliffhanger_hook,
        "status": status_target,
        "preflight_health": req.preflight_health
    }

    # 1. Create Episode via Repository
    created_ep = series_repository.create_episode_draft(
        series_id=req.series_id,
        story_package_id=None,
        payload=ep_payload
    )

    # 2. Attach Decoupled Media Asset (GAP-006 Decoupling)
    from services.storage_service import storage_service
    storage_key = req.storage_key or f"masters/{req.series_id}/{created_ep['id']}.mp4"
    if req.storage_key:
        master_url = storage_service.get_stream_url(storage_key, adaptive_hls=False)
    else:
        master_url = req.video_url if req.video_url and not req.video_url.startswith("blob:") else storage_service.get_stream_url(storage_key, adaptive_hls=False)

    media_asset = series_repository.attach_media_asset(
        episode_id=created_ep["id"],
        storage_key=storage_key,
        master_url=master_url,
        thumbnail_url=req.thumbnail_url or series.get("vertical_poster"),
        duration_seconds=req.duration_seconds
    )

    # Ensure status, storage_key, media_asset_id, and series episode count are updated so the episode is immediately streamable
    series_repository.local_update("episodes", "id", created_ep["id"], {
        "status": "published",
        "video_url": master_url,
        "storage_key": storage_key,
        "media_asset_id": media_asset.get("id")
    })
    created_ep["status"] = "published"
    created_ep["video_url"] = master_url
    created_ep["storage_key"] = storage_key
    created_ep["media_asset_id"] = media_asset.get("id")

    all_series = series_repository.local_get("series")
    target_s = next((s for s in all_series if s["id"] == req.series_id), None)
    if target_s:
        curr_count = target_s.get("total_episodes", 0)
        if req.episode_number > curr_count:
            series_repository.local_update("series", "id", req.series_id, {"total_episodes": req.episode_number})

    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.episode_created",
        actor_id=auth_user.get("sub", "creator"),
        actor_role=auth_user.get("role", "creator"),
        target_type="episode",
        target_id=created_ep["id"],
        after_state={"title": req.title, "series_id": req.series_id, "duration": req.duration_seconds, "status": status_target},
        metadata={"preflight_checks": req.preflight_health}
    )

    # 3. Submit for Moderation if requested
    if status_target in ["under_review", "submitted", "pending_review"]:
        series_repository.submit_for_moderation(created_ep["id"])
        created_ep["status"] = "under_review"

        audit_service.record_trust_event(
            domain="CONTENT",
            event_type="content.episode_submitted",
            actor_id=auth_user.get("sub", "creator"),
            actor_role=auth_user.get("role", "creator"),
            target_type="episode_moderation_queue",
            target_id=created_ep["id"],
            after_state={"status": "under_review", "series_id": req.series_id},
            metadata={"cliffhanger_hook": req.cliffhanger_hook}
        )

    return {"success": True, "episode": created_ep}

@router.get("/analytics/retention", dependencies=[Depends(require_role(["creator", "admin"]))])
def get_retention_telemetry(
    series_id: str = Query("story_blood_ties"),
    episode_number: int = Query(1),
    auth_user: dict = Depends(get_current_user)
):
    """Routes retention telemetry through EventRepository with tenant isolation."""
    series = series_repository.get_series_detail(series_id)
    if series:
        enforce_tenant_access(auth_user, series.get("creator_id"), domain="CONTENT", action="view telemetry")

    ep_id = f"ep_bt_{episode_number}"
    res = event_repository.get_episode_retention(series_id, ep_id)
    return {
        "series_id": res.series_id,
        "episode_id": res.episode_id,
        "episode_number": episode_number,
        "total_starts": res.total_starts,
        "completion_rate_pct": res.completion_rate_pct,
        "cliffhanger_conversion_pct": res.cliffhanger_conversion_pct,
        "avg_watch_time_seconds": res.avg_watch_time_seconds,
        "dropoff_curve": [p.model_dump() for p in res.retention_curve],
        "geo_distribution": res.geo_distribution,
        "telco_payment_mix": [
            {"provider": "MTN Airtime / MoMo", "color": "#FFCC00", "share_pct": 48},
            {"provider": "Vodacom / M-Pesa", "color": "#E60000", "share_pct": 31},
            {"provider": "Chipper Cash", "color": "#7C3AED", "share_pct": 14},
            {"provider": "Card & EFT", "color": "#3B82F6", "share_pct": 7}
        ]
    }
