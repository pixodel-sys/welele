from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db

router = APIRouter(prefix="/admin", tags=["Admin Platform"])

class ModerationFeedbackRequest(BaseModel):
    feedback: Optional[str] = None

@router.get("/metrics")
def get_metrics():
    stories = db.get("stories")
    creators = db.get("creators")
    transactions = db.get("transactions")
    
    total_views = sum(s.get("total_views", 0) for s in stories)
    total_stories = len(stories)
    total_creators = len(creators)
    total_coins_circulating = sum(c.get("coin_earnings", 0) for c in creators) + 45000
    
    return {
        "metrics": {
            "total_views": total_views,
            "total_stories": total_stories,
            "total_creators": total_creators,
            "total_coins_circulating": total_coins_circulating,
            "platform_uptime": "99.98%",
            "active_now": 4829,
            "daily_active_users": 184500
        },
        "revenue_velocity": {
            "momo_daily_usd": 4820.50,
            "card_daily_usd": 2150.00,
            "creator_payouts_pending_usd": 1280.00
        }
    }

@router.get("/moderation-queue")
def get_moderation_queue():
    queue = db.get("moderation_queue")
    # If empty, provide high quality default queue items for immediate interactive demo
    if not queue:
        queue = [
            {
                "id": "mod_ep_queen_04",
                "series_id": "story_blood_ties",
                "series_title": "Blood Ties",
                "episode_id": "ep_bt_4",
                "episode_number": 4,
                "episode_title": "The Betrayal",
                "creator_name": "Zola Dlamini",
                "creator_id": "creator_zola",
                "submitted_at": "2026-09-08T14:30:00Z",
                "aspect_ratio": "9:16 (1080x1920)",
                "duration": "64s",
                "duration_seconds": 64,
                "video_url": "/videos/welele_placeholder.mp4",
                "thumbnail_url": "/posters/blood_ties.jpg",
                "cliffhanger_time": 56,
                "cliffhanger_hook": "The security camera shows who stole the diamond ledger.",
                "ai_safety_score": 99,
                "status": "pending_review",
                "flag": "High Resolution • Verified Audio & Safe Zone",
                "preflight_health": {
                    "aspect_ratio_ok": True,
                    "aspect_ratio_label": "1080 × 1920 (9:16)",
                    "duration_ok": True,
                    "duration_seconds": 64,
                    "audio_detected": True,
                    "thumbnail_present": True,
                    "cliffhanger_marker_ok": True,
                    "cliffhanger_time_seconds": 56,
                    "cliffhanger_hook_copy": "The security camera shows who stole the diamond ledger.",
                    "captions_present": True
                }
            }
        ]
        db.set("moderation_queue", queue)
    return {"queue": queue}

@router.post("/moderation/{item_id}/approve")
def approve_moderation_item(item_id: str):
    item = db.update("moderation_queue", item_id, {"status": "approved"})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Sync status to story episode
    series_id = item.get("series_id")
    episode_id = item.get("episode_id")
    if series_id and episode_id:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == series_id), None)
        if story:
            episodes = story.get("episodes", [])
            for ep in episodes:
                if ep["id"] == episode_id:
                    ep["status"] = "published"
                    break
            db.update("stories", series_id, {"episodes": episodes})

    return {"success": True, "item": item}

@router.post("/moderation/{item_id}/request-changes")
def request_changes_moderation_item(item_id: str, req: ModerationFeedbackRequest):
    feedback_text = req.feedback or "Please adjust cliffhanger audio level and verify safe zone overlays."
    item = db.update("moderation_queue", item_id, {
        "status": "changes_requested",
        "feedback": feedback_text
    })
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Sync status to story episode
    series_id = item.get("series_id")
    episode_id = item.get("episode_id")
    if series_id and episode_id:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == series_id), None)
        if story:
            episodes = story.get("episodes", [])
            for ep in episodes:
                if ep["id"] == episode_id:
                    ep["status"] = "changes_requested"
                    ep["moderation_feedback"] = feedback_text
                    break
            db.update("stories", series_id, {"episodes": episodes})

    return {"success": True, "item": item}

@router.post("/moderation/{item_id}/reject")
def reject_moderation_item(item_id: str, req: Optional[ModerationFeedbackRequest] = None):
    feedback_text = (req.feedback if req else None) or "Content rejected due to guidelines policy."
    item = db.update("moderation_queue", item_id, {
        "status": "rejected",
        "feedback": feedback_text
    })
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Sync status to story episode
    series_id = item.get("series_id")
    episode_id = item.get("episode_id")
    if series_id and episode_id:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == series_id), None)
        if story:
            episodes = story.get("episodes", [])
            for ep in episodes:
                if ep["id"] == episode_id:
                    ep["status"] = "rejected"
                    ep["moderation_feedback"] = feedback_text
                    break
            db.update("stories", series_id, {"episodes": episodes})

    return {"success": True, "item": item}
