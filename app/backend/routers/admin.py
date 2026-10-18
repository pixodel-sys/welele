"""
Welele Media™ — Admin Platform API Router (Normalized DAL & Trust Oversight)
Handles metrics, content moderation queue, auditable episode approval workflows,
and exposes append-only Institutional Trust audit inspection endpoints.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service
from repositories.series_repository import series_repository
from services.evidence_projection_service import evidence_projection_service
from services.commercial_reconciliation_service import commercial_reconciliation_service
from services.commercial_payment_run_service import commercial_payment_run_service

router = APIRouter(prefix="/admin", tags=["Admin Platform"], dependencies=[Depends(require_role(["admin", "admin_operator", "admin_supervisor", "finance"]))])

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

# -----------------------------------------------------------------------------
# Workstream 6I-F.1: Commercial Operations & Reconciliation Endpoints
# -----------------------------------------------------------------------------

@router.get("/commercial/reconciliation")
def get_commercial_reconciliation(
    period: Optional[str] = Query(None, description="Accounting period e.g. 2026-10"),
    limit: int = Query(500, description="Max events to scan")
):
    """
    Executes authoritative 3-way commercial reconciliation across viewer debits,
    revenue events, and creator ledger entries. Detects calculation and allocation discrepancies.
    """
    report = commercial_reconciliation_service.reconcile_chain(period=period, limit=limit)
    return report

@router.get("/commercial/exceptions")
def get_commercial_exceptions(
    series_id: Optional[str] = Query(None, description="Optional series filter"),
    limit: int = Query(100, description="Max exceptions to retrieve")
):
    """
    Lists active commercial accounting exceptions (e.g. uncontracted series, unestablished gifts).
    """
    exceptions = commercial_reconciliation_service.get_unresolved_exceptions(series_id=series_id, limit=limit)
    return {
        "total_exceptions": len(exceptions),
        "exceptions": exceptions
    }

@router.post("/commercial/exceptions/{event_id}/reprocess")
def reprocess_commercial_exception(
    event_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Attempts controlled fail-closed re-resolution of an unresolved commercial exception.
    Posts additive creator ledger entry only if governing commercial agreement has been established.
    """
    actor_id = user.get("sub", "admin_supervisor")
    result = commercial_reconciliation_service.reprocess_exception(
        revenue_event_id=event_id,
        actor_id=actor_id
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("reason") or result.get("error") or "Exception re-processing failed closed."
        )
    return result

@router.get("/commercial/summary")
def get_commercial_summary():
    """
    Returns platform-wide commercial KPIs, gross volume, creator allocations,
    pending payout obligations, and reconciliation health status.
    """
    kpis = commercial_reconciliation_service.get_commercial_kpis()
    return kpis


# ------------------------------------------------------------------------------
# Workstream 6I-G.2: Admin Commercial Payout Governance & Settlement Operations
# ------------------------------------------------------------------------------

@router.get("/commercial/payouts")
def list_commercial_payouts(
    limit: int = Query(100),
    status: Optional[str] = Query(None)
):
    """Admin: Lists creator payouts across all creators with allocations."""
    from services.creator_payout_service import creator_payout_service
    payouts = creator_payout_service.list_all_payouts(limit=limit, status=status)
    return {
        "total": len(payouts),
        "payouts": payouts
    }


@router.get("/commercial/payouts/{payout_id}")
def get_commercial_payout_detail(payout_id: str):
    """Admin: Inspects specific creator payout details and underlying ledger allocations."""
    from services.creator_payout_service import creator_payout_service
    payout = creator_payout_service.get_payout(payout_id=payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout record not found.")
    return payout


@router.post("/commercial/payouts/{payout_id}/hold")
def hold_commercial_payout(
    payout_id: str,
    reason: str = Query("Administrative review"),
    user: dict = Depends(get_current_user)
):
    """Admin: Places a payout request on administrative hold (PENDING/PROCESSING/FAILED -> HELD)."""
    from services.creator_payout_service import creator_payout_service
    actor_id = user.get("sub", "admin_supervisor")
    try:
        updated = creator_payout_service.hold_payout(payout_id=payout_id, actor_id=actor_id, reason=reason)
        return {"success": True, "payout": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/payouts/{payout_id}/release-hold")
def release_commercial_payout_hold(
    payout_id: str,
    reason: str = Query("Hold released"),
    user: dict = Depends(get_current_user)
):
    """Admin: Releases a held payout request back to PENDING state (HELD -> PENDING)."""
    from services.creator_payout_service import creator_payout_service
    actor_id = user.get("sub", "admin_supervisor")
    try:
        updated = creator_payout_service.release_payout_hold(payout_id=payout_id, actor_id=actor_id, reason=reason)
        return {"success": True, "payout": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/payouts/{payout_id}/retry")
def retry_commercial_payout(
    payout_id: str,
    reason: str = Query("Retry after failure"),
    user: dict = Depends(get_current_user)
):
    """Admin: Retries a FAILED payout, transitioning to PROCESSING without double-allocating creator balance."""
    from services.creator_payout_service import creator_payout_service
    actor_id = user.get("sub", "admin_supervisor")
    try:
        updated = creator_payout_service.retry_failed_payout(payout_id=payout_id, actor_id=actor_id, reason=reason)
        return {"success": True, "payout": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/payouts/{payout_id}/process")
def process_commercial_payout(
    payout_id: str,
    reason: str = Query("Instruction initiated"),
    user: dict = Depends(get_current_user)
):
    """Admin: Advances a PENDING payout to PROCESSING state."""
    from services.creator_payout_service import creator_payout_service
    actor_id = user.get("sub", "admin_supervisor")
    try:
        updated = creator_payout_service.transition_payout_status(
            payout_id=payout_id,
            new_status="PROCESSING",
            actor_id=actor_id,
            actor_role="admin",
            reason=reason
        )
        return {"success": True, "payout": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/payouts/settle")
def process_settlement_evidence(
    req: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """
    Settlement boundary handler: Accepts genuine external settlement confirmation.
    Transitions PROCESSING -> PAID ONLY upon valid, authenticated settlement proof.
    Direct/manual shortcuts to PAID without valid settlement proof are strictly rejected.
    """
    from services.creator_payout_service import creator_payout_service
    from services.payout_provider import SettlementConfirmation, ProviderStatus
    from decimal import Decimal

    actor_id = user.get("sub", "settlement_worker")
    try:
        raw_amt = req.get("amount")
        if raw_amt is None:
            raise ValueError("Settlement confirmation missing required 'amount' field.")

        confirmation = SettlementConfirmation(
            payout_id=req["payout_id"],
            provider_reference=req["provider_reference"],
            amount=Decimal(str(raw_amt)),
            currency=req.get("currency", "ZAR"),
            settled_at=datetime.fromisoformat(req["settled_at"]) if req.get("settled_at") else datetime.now(timezone.utc),
            idempotency_key=req["idempotency_key"],
            provider_status=ProviderStatus(req.get("provider_status", "SETTLED")),
            metadata=req.get("metadata", {})
        )
        res = creator_payout_service.process_settlement_confirmation(
            confirmation=confirmation,
            actor_id=actor_id
        )
        return res
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# WORKSTREAM 6I-G.4.2: CREATOR PAYMENT RUN ADMINISTRATION ENDPOINTS
# ==============================================================================

@router.post("/commercial/runs")
def create_payment_run(
    req: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """
    Admin Operator: Prepares a new draft payment run grouping eligible creator payouts.
    Only PENDING creator-requested payouts can be included.
    Zero automatic balance sweeps. Idempotent.
    """
    user_role = user.get("role", "viewer")
    if user_role not in ["admin", "admin_operator", "finance"]:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Role '{user_role}' is not authorized to create payment runs. Required: admin_operator or finance."
        )

    actor_id = user.get("sub", "admin_operator")
    try:
        p_start_raw = req.get("period_start")
        p_end_raw = req.get("period_end")
        if not p_start_raw or not p_end_raw:
            raise ValueError("period_start and period_end are required fields.")

        period_start = datetime.fromisoformat(str(p_start_raw).replace("Z", "+00:00"))
        period_end = datetime.fromisoformat(str(p_end_raw).replace("Z", "+00:00"))
        currency = req.get("currency", "ZAR")
        idempotency_key = req.get("idempotency_key")
        metadata = req.get("metadata", {})
        payout_ids = req.get("payout_ids")

        res = commercial_payment_run_service.create_run(
            period_start=period_start,
            period_end=period_end,
            currency=currency,
            created_by=actor_id,
            idempotency_key=idempotency_key,
            metadata=metadata,
            payout_ids=payout_ids
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/commercial/runs")
def list_payment_runs(
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Admin: Lists payment runs with status, totals, and audit summaries."""
    runs = commercial_payment_run_service.list_runs(limit=limit, status=status)
    return {"runs": runs, "count": len(runs)}


@router.get("/commercial/runs/exceptions")
def list_payment_run_exceptions(
    user: dict = Depends(get_current_user)
):
    """Admin: Reconciles all payment runs and returns actionable reconciliation exceptions."""
    all_runs = commercial_payment_run_service.list_runs(limit=100)
    exceptions_by_run = []
    for r in all_runs:
        rec = commercial_payment_run_service.reconcile_run(r["id"])
        if not rec.get("is_clean"):
            exceptions_by_run.append(rec)
    return {
        "exceptions_count": len(exceptions_by_run),
        "unreconciled_runs": exceptions_by_run
    }


@router.get("/commercial/runs/{run_id}")
def get_payment_run_detail(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Admin: Retrieves payment run details and immutable snapshot items.
    Account numbers are masked by default (e.g. ******1234) for privacy.
    """
    run_detail = commercial_payment_run_service.get_run(run_id=run_id, mask_sensitive=True)
    if not run_detail:
        raise HTTPException(status_code=404, detail=f"Payment run '{run_id}' not found.")
    return run_detail


@router.post("/commercial/runs/{run_id}/submit-review")
def submit_payment_run_for_review(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """Admin Operator: Submits a DRAFT payment run for supervisor review (DRAFT -> UNDER_REVIEW)."""
    actor_id = user.get("sub", "admin_operator")
    try:
        updated = commercial_payment_run_service.submit_for_review(run_id=run_id, actor_id=actor_id)
        return {"success": True, "run": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/runs/{run_id}/approve")
def approve_payment_run(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Admin Supervisor / Authorized Finance: Approves a payment run (UNDER_REVIEW -> APPROVED).
    Dual-Control Enforcement: The preparer (created_by) CANNOT approve their own run.
    Membership and amounts become strictly immutable once approved.
    """
    user_role = user.get("role", "viewer")
    if user_role not in ["admin", "admin_supervisor", "finance"]:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Role '{user_role}' is not authorized to approve payment runs. Required: admin_supervisor or finance."
        )

    actor_id = user.get("sub", "admin_supervisor")
    try:
        updated = commercial_payment_run_service.approve_run(run_id=run_id, approver_id=actor_id)
        return {"success": True, "run": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/runs/{run_id}/cancel")
def cancel_payment_run(
    run_id: str,
    reason: str = Query("Administrative cancellation"),
    user: dict = Depends(get_current_user)
):
    """Admin: Cancels an unexported payment run and releases payouts back to unbatched PENDING."""
    actor_id = user.get("sub", "admin_operator")
    try:
        updated = commercial_payment_run_service.cancel_run(run_id=run_id, actor_id=actor_id, reason=reason)
        return {"success": True, "run": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/commercial/runs/{run_id}/export")
def export_payment_run(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Controlled Bank Export: Generates deterministic provider-neutral CSV bank instructions.
    Calculates and persists SHA-256 hash.
    Transitions included payouts from PENDING -> PROCESSING.
    Exporting does NOT mean executed; does NOT mean PAID.
    """
    actor_id = user.get("sub", "admin_operator")
    try:
        export_data = commercial_payment_run_service.export_run(
            run_id=run_id,
            actor_id=actor_id,
            export_format="csv"
        )
        return Response(
            content=export_data["csv_content"],
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={export_data['file_name']}",
                "X-Export-SHA256": export_data["sha256_hash"],
                "X-FNB-Hash-Total": str(export_data.get("fnb_hash_total") or ""),
                "X-Payout-Count": str(export_data["payout_count"]),
                "X-Total-Amount": str(export_data["total_amount"])
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/runs/{run_id}/results")
def record_payment_run_external_results(
    run_id: str,
    batch: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """
    Admin: Ingests verified external bank execution results.
    Success: PROCESSING -> PAID (requires valid external payment ref, matching amount, settled_at).
    Failed: PROCESSING -> FAILED (preserves creator earnings in creator_ledger).
    """
    actor_id = user.get("sub", "admin_operator")
    try:
        results = batch.get("results")
        if not results or not isinstance(results, list):
            raise ValueError("Field 'results' must be a non-empty list of external execution results.")

        res = commercial_payment_run_service.record_external_results(
            run_id=run_id,
            results=results,
            actor_id=actor_id,
            idempotency_key=batch.get("idempotency_key")
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/commercial/runs/{run_id}/reconcile")
def reconcile_payment_run(
    run_id: str,
    user: dict = Depends(get_current_user)
):
    """Admin: Executes forensic reconciliation of a payment run across all accounting layers."""
    try:
        res = commercial_payment_run_service.reconcile_run(run_id=run_id)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


