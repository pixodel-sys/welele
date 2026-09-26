"""
Welele Media™ — Admin Platform API Router (Normalized DAL & Trust Oversight)
Handles metrics, content moderation queue, auditable episode approval workflows,
and exposes append-only Institutional Trust audit inspection endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service
from repositories.series_repository import series_repository
from repositories.telemetry_repository import telemetry_repository
from services.evidence_projection_service import evidence_projection_service

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

    if updated:
        series_id = updated.get("series_id")
        if series_id:
            all_series = series_repository.local_get("series")
            target_s = next((s for s in all_series if s["id"] == series_id), None)
            if target_s:
                ep_num = updated.get("episode_number", 1)
                curr_count = target_s.get("total_episodes", 0)
                if ep_num > curr_count:
                    series_repository.local_update("series", "id", series_id, {"total_episodes": ep_num})

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


# ============================================================================
# PROJECT 40 BEHAVIOURAL EVIDENCE & OBSERVABILITY ENDPOINT (PHASE 3A)
# ============================================================================

@router.get("/project40-funnel")
def get_project40_funnel(
    series_id: Optional[str] = Query(None),
    episode_id: Optional[str] = Query(None),
    environment: str = Query("production", description="production, staging, test, or all"),
    is_test: Optional[bool] = Query(None),
    days: Optional[int] = Query(None)
):
    """
    Phase B & Phase 3A Harmonization:
    Authoritative Content Evidence Projection & Audience Evidence API.
    Delegates directly to evidence_projection_service.build_content_projection()
    so that there is strictly ONE canonical derivation path from the Unified Event Spine.
    """
    # 1. Derive Canonical ContentEvidenceProjection
    proj = evidence_projection_service.build_content_projection(
        target_id=episode_id or series_id or "ALL",
        series_id=series_id,
        episode_id=episode_id,
        environment=environment,
        is_test=is_test,
        days=days
    )

    # 2. Build 11-step funnel representation directly from canonical projection metrics
    total_entered = proj.entered_sessions_count or proj.provenance.source_session_count
    base = max(1, total_entered)

    funnel_steps = [
        {"step": 1, "key": "ENTERED", "label": "Entered", "sessions": total_entered, "conversion_pct": 100.0 if total_entered > 0 else 0.0},
        {"step": 2, "key": "DISCOVERED", "label": "Discovered", "sessions": len(proj.discovered_breakdown) if proj.discovered_breakdown else (1 if proj.impressions > 0 else 0), "conversion_pct": round((min(base, proj.impressions) / float(base)) * 100, 1)},
        {"step": 3, "key": "SELECTED", "label": "Selected", "sessions": proj.selected_sessions_count or (1 if proj.selected_breakdown else 0), "conversion_pct": round((proj.selected_sessions_count / float(base)) * 100, 1)},
        {"step": 4, "key": "WATCHED", "label": "Watched", "sessions": proj.starts, "conversion_pct": round((proj.starts / float(base)) * 100, 1)},
        {"step": 5, "key": "CONTINUED", "label": "Content Continued (25%+)", "sessions": proj.milestones.reached_25_pct, "conversion_pct": round((proj.milestones.reached_25_pct / float(base)) * 100, 1)},
        {"step": 6, "key": "ENGAGED", "label": "Engaged", "sessions": 1 if (proj.reactions_count + proj.comments_count) > 0 else 0, "conversion_pct": round(((1 if (proj.reactions_count + proj.comments_count) > 0 else 0) / float(base)) * 100, 1)},
        {"step": 7, "key": "PAYWALL", "label": "Paywall", "sessions": proj.paywall_presentations, "conversion_pct": round((proj.paywall_presentations / float(base)) * 100, 1)},
        {"step": 8, "key": "PAYMENT_ATTEMPT", "label": "Payment Attempt", "sessions": proj.unlock_attempts, "conversion_pct": round((proj.unlock_attempts / float(base)) * 100, 1)},
        {"step": 9, "key": "PAID", "label": "Paid", "sessions": proj.unlock_successes, "conversion_pct": round((proj.unlock_successes / float(base)) * 100, 1)},
        {"step": 10, "key": "CONTINUED_POST_PAY", "label": "Episode Progression", "sessions": proj.post_pay_progression_sessions_count, "conversion_pct": round((proj.post_pay_progression_sessions_count / float(base)) * 100, 1)},
        {"step": 11, "key": "RETURNED", "label": "Returned", "sessions": proj.returned_sessions_count, "conversion_pct": round((proj.returned_sessions_count / float(base)) * 100, 1)}
    ]

    total_watched = proj.starts
    dropoff_breakdown = {
        "started": total_watched,
        "reached_25": proj.milestones.reached_25_pct,
        "reached_50": proj.milestones.reached_50_pct,
        "reached_75": proj.milestones.reached_75_pct,
        "reached_90": proj.milestones.reached_90_pct,
        "stopped_before_25": max(0, total_watched - proj.milestones.reached_25_pct),
        "stopped_25_to_50": max(0, proj.milestones.reached_25_pct - proj.milestones.reached_50_pct),
        "stopped_50_to_75": max(0, proj.milestones.reached_50_pct - proj.milestones.reached_75_pct),
        "stopped_75_to_90": max(0, proj.milestones.reached_75_pct - proj.milestones.reached_90_pct),
        "completed_90_plus": proj.milestones.reached_90_pct
    }

    # 3. Expose canonical projection directly while providing backwards-compatible funnel fields
    return {
        "projection": proj.model_dump(),
        "provenance": {
            "zero_synthetic_data": proj.provenance.zero_synthetic_data,
            "environment_filter": proj.provenance.environment_filter,
            "total_events_evaluated": proj.provenance.source_event_count,
            "test_events_excluded": proj.provenance.test_events_excluded,
            "canary_events_excluded": proj.provenance.canary_events_excluded,
            "legacy_events_quarantined": proj.provenance.legacy_events_quarantined,
            "has_data": proj.provenance.has_data,
            "confidence_tier": proj.provenance.confidence_tier.value,
            "confidence_disclosure": proj.provenance.confidence_disclosure,
            "timestamp": proj.provenance.calculation_timestamp,
            "projection_version": proj.provenance.projection_version,
            "methodology_version": proj.provenance.methodology_version
        },
        "funnel": funnel_steps,
        "dropoff_milestones": dropoff_breakdown,
        "engagement_metrics": {
            "reactions_count": proj.reactions_count,
            "comments_count": proj.comments_count
        },
        "discovered_breakdown": proj.discovered_breakdown,
        "selected_breakdown": proj.selected_breakdown,
        # Enhanced canonical evidence attributes
        "hook_3s": {
            "count": proj.hook_3s_retained_count,
            "pct": proj.hook_3s_retention_pct
        },
        "hook_10s": {
            "count": proj.hook_10s_retained_count,
            "pct": proj.hook_10s_retention_pct
        },
        "continuation_intent": proj.next_episode_intent_count,
        "completions": proj.completions,
        "completion_rate_pct": proj.completion_rate_pct,
        "rewatches": proj.rewatches,
        "technical_disruptions": proj.technical_disruptions.model_dump(),
        "retention_curve": [s.model_dump() for s in proj.retention_curve],
        "detected_anomalies": [a.model_dump() for a in proj.detected_anomalies]
    }
