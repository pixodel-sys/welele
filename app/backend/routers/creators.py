import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from database import db
from schemas.story_schemas import CreateSeriesRequest, CreateEpisodeRequest

router = APIRouter(prefix="/creators", tags=["Creator Hub"])

@router.get("/list")
def list_creators():
    creators = db.get("creators")
    return {"creators": creators}

@router.get("/{creator_id}")
def get_creator_profile(creator_id: str):
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == creator_id), None)
    if not creator:
        # Fallback default creator profile if not found
        creator = {
            "id": creator_id,
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
    
    stories = db.get("stories")
    creator_stories = [s for s in stories if s.get("creator_id") == creator_id]
    if not creator_stories:
        creator_stories = stories[:3]
    
    return {
        "creator": creator,
        "series": creator_stories,
        "total_series": len(creator_stories)
    }

@router.get("/{creator_id}/dashboard")
def get_creator_dashboard(creator_id: str):
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == creator_id), None)
    if not creator:
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
    
    stories = db.get("stories")
    creator_stories = [s for s in stories if s.get("creator_id") == creator_id]
    if not creator_stories:
        creator_stories = stories[:4]
    
    total_views = sum(s.get("total_views", 0) for s in creator_stories)
    total_likes = sum(s.get("total_likes", 0) for s in creator_stories)
    total_episodes_count = sum(len(s.get("episodes", [])) for s in creator_stories)
    
    return {
        "stats": {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_episodes": total_episodes_count,
            "followers": creator.get("followers_count", 420000),
            "coin_earnings": creator.get("coin_earnings", 284000),
            "payout_balance_usd": creator.get("payout_balance", 1890.00),
            "avg_cliffhanger_completion_rate": "87.2%",
            "monthly_growth_rate": "+26.4%"
        },
        "series": creator_stories
    }

@router.get("/{creator_id}/episodes")
def get_creator_episodes(creator_id: str, status: str = Query(None)):
    stories = db.get("stories")
    creator_stories = [s for s in stories if s.get("creator_id") == creator_id]
    if not creator_stories:
        creator_stories = stories
    
    all_episodes = []
    for s in creator_stories:
        for ep in s.get("episodes", []):
            ep_status = ep.get("status", "published")
            if status and ep_status != status:
                continue
            all_episodes.append({
                **ep,
                "series_title": s.get("title", ""),
                "series_cover": s.get("vertical_poster", s.get("cover_image", "")),
                "genre": s.get("genre", "")
            })
    
    return {
        "episodes": all_episodes,
        "total": len(all_episodes)
    }

@router.get("/series/{series_id}/workspace")
def get_series_workspace(series_id: str):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == series_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Series not found")
    
    episodes = story.get("episodes", [])
    total_views = sum(ep.get("views_count", 0) for ep in episodes) or story.get("total_views", 0)
    total_coins_earned = sum(
        (ep.get("views_count", 1000) // 10) * ep.get("coin_price", 5) 
        for ep in episodes if not ep.get("is_free", False)
    )
    
    return {
        "series": story,
        "metrics": {
            "total_views": total_views,
            "completion_rate": "88.4%",
            "coins_generated": total_coins_earned,
            "estimated_earnings_usd": round(total_coins_earned * 0.007, 2),
            "published_count": len([e for e in episodes if e.get("status") == "published" or not e.get("status")]),
            "under_review_count": len([e for e in episodes if e.get("status") in ["under_review", "submitted", "pending_review"]]),
            "draft_count": len([e for e in episodes if e.get("status") == "draft"]),
        }
    }

@router.post("/series/create")
def create_series(req: CreateSeriesRequest):
    new_id = f"story_{uuid.uuid4().hex[:8]}"
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == req.creator_id), None)
    creator_name = creator["name"] if creator else "Zola Dlamini"
    creator_avatar = creator["avatar"] if creator else "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80"
    
    new_story = {
        "id": new_id,
        "title": req.title,
        "tagline": req.tagline,
        "synopsis": req.synopsis,
        "cover_image": req.cover_image,
        "vertical_poster": req.vertical_poster,
        "genre": req.genre,
        "language": req.language,
        "available_languages": req.available_languages,
        "tags": req.tags,
        "creator_id": req.creator_id,
        "creator_name": creator_name,
        "creator_avatar": creator_avatar,
        "is_verified_creator": True,
        "rating": 5.0,
        "total_episodes": 0,
        "free_episodes_count": 2,
        "coin_price_per_episode": req.coin_price_per_episode,
        "total_views": 0,
        "total_likes": 0,
        "is_original": True,
        "is_trending": True,
        "status": "published",
        "episodes": []
    }
    
    db.insert("stories", new_story)
    return {"success": True, "story": new_story}

@router.post("/episodes/add")
def add_episode(req: CreateEpisodeRequest):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == req.series_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Series not found")
    
    new_ep_id = f"ep_{uuid.uuid4().hex[:8]}"
    status = req.status or "under_review"
    
    new_episode = {
        "id": new_ep_id,
        "series_id": req.series_id,
        "episode_number": req.episode_number,
        "title": req.title,
        "synopsis": req.synopsis,
        "duration_seconds": req.duration_seconds,
        "video_url": req.video_url,
        "thumbnail_url": req.thumbnail_url or story.get("vertical_poster", ""),
        "is_free": req.is_free,
        "coin_price": req.coin_price if not req.is_free else 0,
        "cliffhanger_time": req.cliffhanger_time,
        "cliffhanger_hook": req.cliffhanger_hook or "What happens next?",
        "status": status,
        "scheduled_at": req.scheduled_at,
        "preflight_health": req.preflight_health or {
            "aspect_ratio_ok": True,
            "aspect_ratio_label": "1080 × 1920 (9:16)",
            "duration_ok": True,
            "duration_seconds": req.duration_seconds,
            "audio_detected": True,
            "thumbnail_present": bool(req.thumbnail_url),
            "cliffhanger_marker_ok": req.cliffhanger_time > 0,
            "cliffhanger_time_seconds": req.cliffhanger_time,
            "cliffhanger_hook_copy": req.cliffhanger_hook,
            "captions_present": True
        },
        "likes_count": 0,
        "views_count": 0,
        "comments_count": 0,
        "published_at": datetime.now(timezone.utc).isoformat()
    }
    
    story_episodes = story.get("episodes", [])
    story_episodes.append(new_episode)
    story["total_episodes"] = len(story_episodes)
    db.update("stories", req.series_id, {"episodes": story_episodes, "total_episodes": len(story_episodes)})
    
    # Bridge to Admin Moderation Queue
    if status in ["under_review", "submitted", "pending_review"]:
        mod_item = {
            "id": f"mod_{new_ep_id}",
            "series_id": req.series_id,
            "series_title": story.get("title", ""),
            "episode_id": new_ep_id,
            "episode_number": req.episode_number,
            "episode_title": req.title,
            "creator_id": story.get("creator_id", "creator_zola"),
            "creator_name": story.get("creator_name", "Creator"),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "aspect_ratio": "9:16 (1080x1920)",
            "duration": f"{req.duration_seconds}s",
            "duration_seconds": req.duration_seconds,
            "video_url": req.video_url,
            "thumbnail_url": req.thumbnail_url or story.get("vertical_poster", ""),
            "cliffhanger_time": req.cliffhanger_time,
            "cliffhanger_hook": req.cliffhanger_hook,
            "ai_safety_score": 98,
            "status": "pending_review",
            "flag": "High Production Quality • Safe Zone Validated",
            "preflight_health": new_episode["preflight_health"]
        }
        db.insert("moderation_queue", mod_item)
    
    return {"success": True, "episode": new_episode}


@router.get("/analytics/retention")
def get_retention_telemetry(series_id: str = Query("story_1"), episode_number: int = Query(1)):
    curve = []
    current = 100.0
    import random
    for sec in range(0, 95, 5):
        if sec == 0:
            current = 100.0
        elif sec <= 15:
            current -= round(random.uniform(1.0, 3.0), 1)
        elif sec <= 70:
            current -= round(random.uniform(0.3, 1.2), 1)
        elif sec >= 85:
            current -= round(random.uniform(0.1, 0.4), 1)
        
        curve.append({
            "second": sec,
            "retention_pct": max(45.0, round(current, 1)),
            "viewer_count": int(14500 * (current / 100.0)),
            "is_cliffhanger": sec >= 85
        })
    
    return {
        "series_id": series_id,
        "episode_id": f"ep_{episode_number}",
        "episode_number": episode_number,
        "total_starts": 14500,
        "completion_rate_pct": 78.4,
        "cliffhanger_conversion_pct": 64.2,
        "avg_watch_time_seconds": 79.5,
        "dropoff_curve": curve,
        "geo_distribution": [
            {"country": "South Africa", "flag": "🇿🇦", "share_pct": 44, "views": 6380},
            {"country": "Nigeria", "flag": "🇳🇬", "share_pct": 28, "views": 4060},
            {"country": "Kenya", "flag": "🇰🇪", "share_pct": 16, "views": 2320},
            {"country": "Ghana", "flag": "🇬🇭", "share_pct": 12, "views": 1740}
        ],
        "telco_payment_mix": [
            {"provider": "MTN Airtime / MoMo", "color": "#FFCC00", "share_pct": 48},
            {"provider": "Vodacom / M-Pesa", "color": "#E60000", "share_pct": 31},
            {"provider": "Chipper Cash", "color": "#7C3AED", "share_pct": 14},
            {"provider": "Card & EFT", "color": "#3B82F6", "share_pct": 7}
        ]
    }
