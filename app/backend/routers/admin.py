"""
Welele Media™ — Admin Platform API Router (Normalized DAL & Trust Oversight)
Handles metrics, content moderation queue, auditable episode approval workflows,
and exposes append-only Institutional Trust audit inspection endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service
from repositories.series_repository import series_repository

router = APIRouter(prefix="/admin", tags=["Admin Platform"], dependencies=[Depends(require_role(["admin"]))])

class ModerationFeedbackRequest(BaseModel):
    feedback: Optional[str] = None

@router.get("/metrics")
def get_metrics():
    series_list = series_repository.list_feed()
    all_episodes = series_repository.local_get("episodes")

    return {
        "metrics": {
            "total_views": 8420000,
            "total_stories": len(series_list),
            "total_episodes": len(all_episodes),
            "total_creators": 12,
            "total_coins_circulating": 329000,
            "platform_uptime": "99.99%",
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
    queue = series_repository.get_moderation_queue()
    return {"queue": queue}

@router.post("/moderation/{item_id}/approve")
def approve_moderation_item(item_id: str, user: dict = Depends(get_current_user)):
    episode_id = item_id.replace("mod_", "")
    reviewer_id = user.get("sub", "admin_supervisor")

    updated = series_repository.review_episode(
        episode_id=episode_id,
        decision="approved",
        reviewer_id=reviewer_id
    )
    if not updated:
        # Check if item_id matches direct episode
        updated = series_repository.review_episode(
            episode_id=item_id,
            decision="approved",
            reviewer_id=reviewer_id
        )

    # Record institutional trust audit events
    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.moderation_decision",
        actor_id=reviewer_id,
        actor_role="admin",
        target_type="episode",
        target_id=episode_id,
        before_state={"status": "under_review"},
        after_state={"status": "published", "moderation_decision": "approved", "reviewer_id": reviewer_id},
        metadata={"item_id": item_id, "action": "approve"}
    )

    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.publication",
        actor_id=reviewer_id,
        actor_role="admin",
        target_type="episode",
        target_id=episode_id,
        after_state={"status": "published", "is_live": True},
        metadata={"series_id": updated.get("series_id") if updated else None}
    )

    return {"success": True, "episode": updated, "status": "approved"}

@router.post("/moderation/{item_id}/request-changes")
def request_changes_moderation_item(item_id: str, req: ModerationFeedbackRequest, user: dict = Depends(get_current_user)):
    feedback_text = req.feedback or "Please adjust cliffhanger audio level and verify safe zone overlays."
    episode_id = item_id.replace("mod_", "")
    reviewer_id = user.get("sub", "admin_supervisor")

    updated = series_repository.review_episode(
        episode_id=episode_id,
        decision="changes_requested",
        feedback=feedback_text,
        reviewer_id=reviewer_id
    )

    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.moderation_decision",
        actor_id=reviewer_id,
        actor_role="admin",
        target_type="episode",
        target_id=episode_id,
        before_state={"status": "under_review"},
        after_state={"status": "changes_requested", "feedback": feedback_text},
        metadata={"item_id": item_id, "decision": "changes_requested"}
    )

    return {"success": True, "episode": updated, "status": "changes_requested", "feedback": feedback_text}

@router.post("/moderation/{item_id}/reject")
def reject_moderation_item(item_id: str, req: Optional[ModerationFeedbackRequest] = None, user: dict = Depends(get_current_user)):
    feedback_text = (req.feedback if req else None) or "Content rejected due to guidelines policy."
    episode_id = item_id.replace("mod_", "")
    reviewer_id = user.get("sub", "admin_supervisor")

    updated = series_repository.review_episode(
        episode_id=episode_id,
        decision="rejected",
        feedback=feedback_text,
        reviewer_id=reviewer_id
    )

    audit_service.record_trust_event(
        domain="CONTENT",
        event_type="content.moderation_decision",
        actor_id=reviewer_id,
        actor_role="admin",
        target_type="episode",
        target_id=episode_id,
        before_state={"status": "under_review"},
        after_state={"status": "rejected", "feedback": feedback_text},
        metadata={"item_id": item_id, "decision": "rejected"}
    )

    return {"success": True, "episode": updated, "status": "rejected", "feedback": feedback_text}

# ============================================================================
# INSTITUTIONAL TRUST AUDIT LEDGER ENDPOINTS
# ============================================================================

@router.get("/audit-logs")
def list_audit_logs(
    domain: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    actor_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    """Retrieves immutable append-only audit trail records."""
    logs = audit_service.list_audit_events(
        domain=domain,
        event_type=event_type,
        actor_id=actor_id,
        target_id=target_id,
        limit=limit
    )
    return {"logs": logs, "total": len(logs)}

@router.post("/audit-logs/verify-chain")
def verify_audit_chain():
    """Cryptographically verifies every block in the security audit ledger hash chain."""
    result = audit_service.verify_audit_chain_integrity()
    return {"verification": result}
