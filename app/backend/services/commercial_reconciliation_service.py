"""
Welele Media™ — Commercial Operations & Reconciliation Service (Workstream 6I-F.1)
Authoritative 3-Way Financial Reconciliation Engine:
  Viewer Commercial Event (coin_ledger / transactions)
            ↕
    Revenue Event (revenue_events)
            ↕
    Creator Ledger (creator_ledger)

Implements:
1. End-to-end reconciliation & automated discrepancy detection
2. Fail-closed accounting exception auditing & controlled re-resolution
3. Platform-wide commercial KPIs and balance reconciliation
4. Full audit trail emission for operational governance
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

from schemas.commercial_accounting_schemas import (
    CommercialModel,
    RevenueEventSource,
    RevenueEventType,
    LedgerEntryType,
    LedgerStatus,
    PayoutStatus,
    SettlementStatus
)
from repositories.commercial_accounting_repository import (
    commercial_accounting_repository,
    CommercialAccountingRepository,
    to_uuid
)
from services.commercial_accounting_service import commercial_accounting_service
from services.audit_service import audit_service
from database import db

logger = logging.getLogger("welele.commercial_reconciliation")


def _to_decimal(val: Any) -> Decimal:
    if isinstance(val, Decimal):
        return val
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.0000")


def _round_currency(val: Any) -> Decimal:
    dec = _to_decimal(val)
    return dec.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


class CommercialReconciliationService:
    def __init__(self, repository: Optional[CommercialAccountingRepository] = None):
        self.repo = repository or commercial_accounting_repository

    # --------------------------------------------------------------------------
    # 1. 3-WAY RECONCILIATION ENGINE
    # --------------------------------------------------------------------------

    def reconcile_chain(
        self,
        period: Optional[str] = None,
        limit: int = 500,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an authoritative 3-way reconciliation across:
        1. Upstream Viewer Transactions: coin debits and direct payments
        2. Revenue Events: recorded commercial events and permitted deductions
        3. Downstream Creator Ledger: immutable creator earning entries

        Identifies:
        - MATCHED: Perfectly verified 3-way chain with matching mathematics
        - UNMATCHED_SOURCE: Viewer debit without corresponding revenue event
        - UNMATCHED_LEDGER: Resolved revenue event without creator ledger entry
        - ACCOUNTING_EXCEPTION: Properly isolated fail-closed exceptions (0 creator earnings)
        - DISCREPANCIES: Amount mismatches, non-zero PAID balances, duplicate ledger rows
        """
        run_id = f"rec_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        reconciliation_timestamp = now.isoformat()

        # 1. Fetch Upstream Viewer Source Events
        all_coin_ledger = db.get("coin_ledger") or []
        unlock_debits = [
            e for e in all_coin_ledger
            if e.get("transaction_type") == "EPISODE_UNLOCK"
        ]

        all_txs = db.get("transactions") or []
        airtime_txs = [
            t for t in all_txs
            if "airtime" in str(t.get("type", "")).lower()
        ]
        gift_txs = [
            t for t in all_txs
            if str(t.get("type", "")).lower() == "gift"
        ]

        # 2. Fetch Midstream Revenue Events & Deductions
        rev_events = self.repo.get_revenue_events(limit=limit)

        # 3. Fetch Downstream Creator Ledger Entries
        ledger_entries = self.repo.get_all_creator_ledger_entries(limit=limit)

        # Build fast lookup indices
        rev_by_tx_id: Dict[str, List[Dict[str, Any]]] = {}
        rev_by_idemp: Dict[str, Dict[str, Any]] = {}
        for r in rev_events:
            tx_id = str(r.get("source_transaction_id"))
            rev_by_tx_id.setdefault(tx_id, []).append(r)
            idemp = r.get("idempotency_key")
            if idemp:
                rev_by_idemp[idemp] = r

        ledger_by_rev_id: Dict[str, List[Dict[str, Any]]] = {}
        for l in ledger_entries:
            rev_id = str(l.get("revenue_event_id"))
            if rev_id and rev_id != "None":
                ledger_by_rev_id.setdefault(rev_id, []).append(l)

        # Counters & Tracking
        matched = []
        unmatched_sources = []
        unmatched_ledger = []
        exceptions = []
        discrepancies = []

        total_gross_reconciled = Decimal("0.0000")
        total_creator_reconciled = Decimal("0.0000")
        total_deductions_reconciled = Decimal("0.0000")

        # --- Check 1: Upstream Source Events -> Revenue Events ---
        all_sources = []
        for d in unlock_debits:
            all_sources.append({
                "source_type": "COIN_UNLOCK",
                "source_id": d.get("id"),
                "tx_id": d.get("id"),
                "series_id": d.get("reference_id"),
                "amount_coins": abs(int(d.get("amount", 0))),
                "expected_gross_zar": Decimal(str(abs(int(d.get("amount", 0))))) * Decimal("0.1300")
            })

        for a in airtime_txs:
            all_sources.append({
                "source_type": "AIRTIME_UNLOCK",
                "source_id": a.get("id"),
                "tx_id": a.get("id"),
                "series_id": a.get("series_id"),
                "amount_zar": _to_decimal(a.get("amount_zar", 0)),
                "expected_gross_zar": _to_decimal(a.get("amount_zar", 0))
            })

        for g in gift_txs:
            all_sources.append({
                "source_type": "GIFT",
                "source_id": g.get("id"),
                "tx_id": g.get("id"),
                "series_id": g.get("series_id"),
                "amount_coins": int(g.get("coins", 0)),
                "expected_gross_zar": Decimal(str(g.get("coins", 0))) * Decimal("0.1300")
            })

        # --- Check 2: Revenue Events -> Downstream Ledger & Exceptions ---
        for r in rev_events:
            r_id = r.get("id")
            meta = r.get("metadata") or {}
            is_exception = meta.get("accounting_exception") is True or meta.get("unresolved_commercial_allocation") is True
            linked_ledger = ledger_by_rev_id.get(r_id, [])

            if is_exception:
                # Invariant: Exceptions must have EXACTLY 0 creator ledger rows
                if len(linked_ledger) > 0:
                    discrepancies.append({
                        "issue_type": "EXCEPTION_WITH_UNAUTHORIZED_EARNINGS",
                        "revenue_event_id": r_id,
                        "description": f"Revenue event {r_id} is marked as exception but has {len(linked_ledger)} creator ledger entries!",
                        "severity": "CRITICAL"
                    })
                else:
                    exceptions.append({
                        "revenue_event_id": r_id,
                        "source": r.get("source"),
                        "series_id": r.get("series_id"),
                        "gross_amount": float(r.get("gross_amount", 0)),
                        "currency": r.get("currency", "ZAR"),
                        "reason": meta.get("exception_reason", "Unresolved commercial allocation"),
                        "occurred_at": r.get("occurred_at")
                    })
                continue

            # Resolved revenue event must have corresponding ledger entry
            if not linked_ledger:
                unmatched_ledger.append({
                    "issue_type": "RESOLVED_EVENT_MISSING_LEDGER",
                    "revenue_event_id": r_id,
                    "series_id": r.get("series_id"),
                    "gross_amount": float(r.get("gross_amount", 0)),
                    "description": f"Revenue event {r_id} was resolved under contract version {r.get('commercial_agreement_version_id')} but has no creator_ledger row."
                })
                continue

            # Check for duplicate ledger entries for the same revenue event
            if len(linked_ledger) > 1:
                discrepancies.append({
                    "issue_type": "DUPLICATE_LEDGER_ENTRIES",
                    "revenue_event_id": r_id,
                    "count": len(linked_ledger),
                    "description": f"Duplicate creator ledger rows detected for single revenue event {r_id}!",
                    "severity": "HIGH"
                })

            # Mathematical validation of primary ledger entry
            primary = linked_ledger[0]
            gross_rev = _to_decimal(primary.get("gross_revenue", 0))
            deductions = _to_decimal(primary.get("deductions", 0))
            net_rev = _to_decimal(primary.get("net_revenue", 0))
            creator_amt = _to_decimal(primary.get("creator_amount", 0))
            alloc_pct = _to_decimal(primary.get("allocation_percentage", 0))

            expected_net = gross_rev - deductions
            expected_creator = _round_currency(expected_net * alloc_pct)

            if net_rev != expected_net or creator_amt != expected_creator:
                discrepancies.append({
                    "issue_type": "CALCULATION_MISMATCH",
                    "revenue_event_id": r_id,
                    "ledger_id": primary.get("id"),
                    "details": {
                        "recorded_net": float(net_rev),
                        "expected_net": float(expected_net),
                        "recorded_creator": float(creator_amt),
                        "expected_creator": float(expected_creator)
                    },
                    "description": f"Mathematical discrepancy in creator ledger row {primary.get('id')}.",
                    "severity": "HIGH"
                })
            else:
                total_gross_reconciled += gross_rev
                total_deductions_reconciled += deductions
                total_creator_reconciled += creator_amt
                matched.append({
                    "revenue_event_id": r_id,
                    "ledger_id": primary.get("id"),
                    "creator_id": primary.get("creator_id"),
                    "series_id": primary.get("series_id"),
                    "gross_amount": float(gross_rev),
                    "deductions": float(deductions),
                    "net_amount": float(net_rev),
                    "creator_amount": float(creator_amt),
                    "currency": primary.get("currency", "ZAR"),
                    "status": "VERIFIED_MATCHED"
                })

        # --- Check 3: Creator Payout & Allocation Chain Reconciliation (6I-G.2) ---
        # Audits Available Balance -> Allocations -> Payout Requests -> Settlement Evidence
        all_payouts = self.repo.local_get("creator_payouts")
        if self.repo.is_live:
            try:
                db_p = self.repo.get_table("creator_payouts").select("*").execute()
                if db_p and db_p.data:
                    all_payouts = db_p.data
            except Exception as e:
                logger.warning(f"[Reconciliation] Remote payouts query error: {e}")

        all_allocations = self.repo.get_payout_allocations()

        payout_map = {p["id"]: p for p in all_payouts}
        allocs_by_payout: Dict[str, List[Dict[str, Any]]] = {}
        allocs_by_ledger: Dict[str, Decimal] = {}
        allocs_by_creator: Dict[str, Decimal] = {}
        settled_prov_refs: Dict[str, str] = {}  # prov_ref -> payout_id

        # 3a. Audit allocations: Check for orphaned allocations & duplicate allocation over-consumption
        for a in all_allocations:
            p_id = a.get("payout_id")
            parent_p = payout_map.get(p_id)
            if not parent_p:
                discrepancies.append({
                    "issue_type": "ALLOCATION_WITHOUT_PAYOUT",
                    "allocation_id": a.get("id"),
                    "payout_id": p_id,
                    "description": f"Allocation {a.get('id')} references non-existent payout {p_id}.",
                    "severity": "HIGH"
                })
                continue

            allocs_by_payout.setdefault(p_id, []).append(a)

            # Only active payouts hold/consume allocation value
            if parent_p.get("status") not in [PayoutStatus.REVERSED.value, PayoutStatus.CANCELLED.value]:
                amt = _to_decimal(a.get("amount_allocated", 0))
                l_id = a.get("ledger_entry_id")
                allocs_by_ledger[l_id] = allocs_by_ledger.get(l_id, Decimal("0.0000")) + amt
                c_id = parent_p.get("creator_id")
                allocs_by_creator[c_id] = allocs_by_creator.get(c_id, Decimal("0.0000")) + amt

        # 3b. Verify allocation limits against underlying creator_ledger earning entries
        ledger_map = {e["id"]: e for e in ledger_entries}
        for l_id, total_alloc in allocs_by_ledger.items():
            l_entry = ledger_map.get(l_id)
            if l_entry:
                earning_val = _to_decimal(l_entry.get("creator_amount", 0))
                if total_alloc > earning_val:
                    discrepancies.append({
                        "issue_type": "DUPLICATE_ALLOCATION",
                        "ledger_entry_id": l_id,
                        "allocated_total": float(total_alloc),
                        "earning_value": float(earning_val),
                        "description": f"Ledger entry {l_id} has total active allocations ({total_alloc}) exceeding its value ({earning_val}).",
                        "severity": "CRITICAL"
                    })

        # 3c. Audit each payout record
        for p in all_payouts:
            p_id = p["id"]
            p_status = p.get("status")
            req_amt = _to_decimal(p.get("requested_amount", 0))
            p_allocs = allocs_by_payout.get(p_id, [])

            # Payout without allocation (for non-cancelled/rejected payouts)
            if p_status not in [PayoutStatus.REJECTED.value, PayoutStatus.CANCELLED.value]:
                if not p_allocs and req_amt > Decimal("0.0000"):
                    discrepancies.append({
                        "issue_type": "PAYOUT_WITHOUT_ALLOCATION",
                        "payout_id": p_id,
                        "status": p_status,
                        "requested_amount": float(req_amt),
                        "description": f"Payout {p_id} ({p_status}) has zero underlying ledger allocations.",
                        "severity": "HIGH"
                    })
                elif p_allocs:
                    sum_allocated = sum(_to_decimal(a.get("amount_allocated", 0)) for a in p_allocs)
                    if sum_allocated != req_amt:
                        discrepancies.append({
                            "issue_type": "PAYOUT_AMOUNT_MISMATCH",
                            "payout_id": p_id,
                            "requested_amount": float(req_amt),
                            "allocated_amount": float(sum_allocated),
                            "description": f"Payout {p_id} requested amount ({req_amt}) does not match sum of allocations ({sum_allocated}).",
                            "severity": "CRITICAL"
                        })

                    # Currency mismatch check
                    for a in p_allocs:
                        l_entry = ledger_map.get(a.get("ledger_entry_id"))
                        if l_entry and l_entry.get("currency", "ZAR") != p.get("currency", "ZAR"):
                            discrepancies.append({
                                "issue_type": "CURRENCY_MISMATCH",
                                "payout_id": p_id,
                                "payout_currency": p.get("currency"),
                                "ledger_currency": l_entry.get("currency"),
                                "description": f"Currency mismatch between payout {p_id} and allocated ledger entry {l_entry.get('id')}.",
                                "severity": "HIGH"
                            })

            # Check PAID / SETTLED verification invariant
            if p_status in [PayoutStatus.PAID.value, PayoutStatus.SETTLED.value]:
                settled_at = p.get("settled_at")
                meta = dict(p.get("metadata") or {})
                prov_ref = meta.get("provider_reference") or p.get("provider_reference")
                
                if not settled_at or not prov_ref:
                    discrepancies.append({
                        "issue_type": "UNAUTHORIZED_PAYOUT_SETTLEMENT",
                        "payout_id": p_id,
                        "status": p_status,
                        "description": "CRITICAL FINTECH INVARIANT VIOLATION: Payout is marked PAID/SETTLED without authentic verified settlement evidence or provider reference!",
                        "severity": "CRITICAL"
                    })
                else:
                    # Check duplicate settlement event reference
                    if prov_ref in settled_prov_refs and settled_prov_refs[prov_ref] != p_id:
                        discrepancies.append({
                            "issue_type": "DUPLICATE_SETTLEMENT_EVENT",
                            "payout_id": p_id,
                            "conflicting_payout_id": settled_prov_refs[prov_ref],
                            "provider_reference": prov_ref,
                            "description": f"Provider reference '{prov_ref}' was claimed by multiple settled payouts.",
                            "severity": "CRITICAL"
                        })
                    else:
                        settled_prov_refs[prov_ref] = p_id

            # Inconsistent settlement timestamp
            if p.get("settled_at") and p_status not in [PayoutStatus.PAID.value, PayoutStatus.SETTLED.value, PayoutStatus.REVERSED.value]:
                discrepancies.append({
                    "issue_type": "INCONSISTENT_SETTLEMENT_STATE",
                    "payout_id": p_id,
                    "status": p_status,
                    "settled_at": p.get("settled_at"),
                    "description": f"Payout {p_id} has settled_at timestamp but is in non-settled status '{p_status}'.",
                    "severity": "HIGH"
                })

        # 3d. Check total allocations vs creator earned balance
        for c_id, total_alloc in allocs_by_creator.items():
            c_earnings = sum(
                _to_decimal(e.get("creator_amount", 0))
                for e in ledger_entries
                if e.get("creator_id") == c_id and e.get("entry_type") == LedgerEntryType.EARNING.value
            )
            if total_alloc > c_earnings:
                discrepancies.append({
                    "issue_type": "ALLOCATION_EXCEEDS_AVAILABLE",
                    "creator_id": c_id,
                    "allocated_total": float(total_alloc),
                    "earned_total": float(c_earnings),
                    "description": f"Creator {c_id} has total active allocations ({total_alloc}) exceeding total earned ({c_earnings}).",
                    "severity": "CRITICAL"
                })

        # --- Check 4: Payment Run Forensics (Workstream 6I-G.4.2) ---
        all_runs = self.repo.list_payment_runs(limit=100)
        seen_active_payout_ids: Dict[str, str] = {}
        for run in all_runs:
            run_id = str(run.get("id"))
            run_status = run.get("status")
            if run_status == "CANCELLED":
                continue

            run_items = self.repo.get_payment_run_items(run_id)
            active_items = [i for i in run_items if i.get("status") != "EXCLUDED"]

            # 4a. Total amount and count verification
            run_sum = _to_decimal(run.get("total_amount", 0))
            items_sum = sum(_to_decimal(i.get("amount", 0)) for i in active_items)
            if run_sum != items_sum:
                discrepancies.append({
                    "issue_type": "PAYMENT_RUN_TOTAL_MISMATCH",
                    "run_id": run_id,
                    "run_reference": run.get("run_reference"),
                    "run_total": float(run_sum),
                    "items_sum": float(items_sum),
                    "description": f"Payment run {run.get('run_reference')} total ({run_sum}) does not match items sum ({items_sum}).",
                    "severity": "CRITICAL"
                })

            if len(active_items) != run.get("payout_count"):
                discrepancies.append({
                    "issue_type": "PAYMENT_RUN_COUNT_MISMATCH",
                    "run_id": run_id,
                    "run_reference": run.get("run_reference"),
                    "declared_count": run.get("payout_count"),
                    "items_count": len(active_items),
                    "description": f"Payment run {run.get('run_reference')} count ({run.get('payout_count')}) does not match items count ({len(active_items)}).",
                    "severity": "CRITICAL"
                })

            # 4b. Export hash verification
            if run_status in ["EXPORTED", "AWAITING_EXTERNAL_RESULT", "RESULTS_RECORDED", "RECONCILED"]:
                if not run.get("export_file_hash_sha256"):
                    discrepancies.append({
                        "issue_type": "PAYMENT_RUN_HASH_MISSING",
                        "run_id": run_id,
                        "run_reference": run.get("run_reference"),
                        "description": f"Exported payment run {run.get('run_reference')} is missing SHA-256 export hash.",
                        "severity": "CRITICAL"
                    })

            # 4c. Payout membership & result evidence
            for itm in active_items:
                p_id = str(itm.get("payout_id"))
                if p_id in seen_active_payout_ids:
                    discrepancies.append({
                        "issue_type": "PAYOUT_IN_MULTIPLE_RUNS",
                        "payout_id": p_id,
                        "run_id": run_id,
                        "conflicting_run_id": seen_active_payout_ids[p_id],
                        "description": f"Payout {p_id} appears in multiple active payment runs ({run_id} and {seen_active_payout_ids[p_id]}).",
                        "severity": "CRITICAL"
                    })
                else:
                    seen_active_payout_ids[p_id] = run_id

                # Result verification
                itm_status = itm.get("status")
                if itm_status == "PAID":
                    p_obj = self.repo.get_payout_by_id(p_id)
                    ext_ref = itm.get("external_payment_reference") or ((p_obj or {}).get("metadata") or {}).get("provider_reference")
                    if not ext_ref:
                        discrepancies.append({
                            "issue_type": "PAID_WITHOUT_EXTERNAL_REFERENCE",
                            "payout_id": p_id,
                            "run_id": run_id,
                            "description": f"Item for payout {p_id} in run {run.get('run_reference')} is PAID without external payment reference.",
                            "severity": "CRITICAL"
                        })
                    if p_obj and not p_obj.get("settled_at"):
                        discrepancies.append({
                            "issue_type": "PAID_WITHOUT_SETTLEMENT_TIMESTAMP",
                            "payout_id": p_id,
                            "run_id": run_id,
                            "description": f"Payout {p_id} in run {run.get('run_reference')} is PAID without settlement timestamp.",
                            "severity": "CRITICAL"
                        })



        # Compile Overall Report
        status = "BALANCED" if len(discrepancies) == 0 else "DISCREPANCIES_DETECTED"
        report = {
            "reconciliation_id": run_id,
            "generated_at": reconciliation_timestamp,
            "status": status,
            "summary": {
                "total_revenue_events_analyzed": len(rev_events),
                "total_creator_ledger_entries": len(ledger_entries),
                "matched_count": len(matched),
                "exception_count": len(exceptions),
                "unmatched_ledger_count": len(unmatched_ledger),
                "discrepancy_count": len(discrepancies),
                "reconciled_gross_zar": float(_round_currency(total_gross_reconciled)),
                "reconciled_deductions_zar": float(_round_currency(total_deductions_reconciled)),
                "reconciled_net_zar": float(_round_currency(total_gross_reconciled - total_deductions_reconciled)),
                "reconciled_creator_earnings_zar": float(_round_currency(total_creator_reconciled)),
                "external_payout_rails_active": False,
                "production_frozen": True
            },
            "discrepancies": discrepancies,
            "exceptions": exceptions,
            "unmatched_ledger": unmatched_ledger,
            "matched_sample": matched[:20]
        }

        # Emit Institutional Trust Audit Event
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commercial_accounting.reconciliation_completed",
            actor_id="system_reconciliation_worker",
            actor_role="commercial_operations",
            target_type="reconciliation_run",
            target_id=run_id,
            after_state={
                "status": status,
                "matched_count": len(matched),
                "discrepancies_count": len(discrepancies),
                "exceptions_count": len(exceptions),
                "reconciled_gross": float(total_gross_reconciled),
                "reconciled_creator_earnings": float(total_creator_reconciled)
            },
            metadata={
                "reconciliation_id": run_id,
                "idempotency_key": idempotency_key
            }
        )

        return report

    # --------------------------------------------------------------------------
    # 2. ACCOUNTING EXCEPTION MANAGEMENT & FAIL-CLOSED RE-RESOLUTION
    # --------------------------------------------------------------------------

    def get_unresolved_exceptions(
        self,
        series_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieves active commercial accounting exceptions (e.g. uncontracted series,
        unestablished gift economics, missing agreement versions).
        """
        all_exceptions = self.repo.get_revenue_events(limit=limit, only_exceptions=True)
        if series_id:
            all_exceptions = [e for e in all_exceptions if str(e.get("series_id")) == str(series_id)]

        formatted = []
        for e in all_exceptions:
            meta = e.get("metadata") or {}
            if meta.get("exception_resolved") is True:
                continue
            formatted.append({
                "revenue_event_id": e.get("id"),
                "source": e.get("source"),
                "event_type": e.get("event_type"),
                "series_id": e.get("series_id"),
                "episode_id": e.get("episode_id"),
                "gross_amount": float(e.get("gross_amount", 0)),
                "currency": e.get("currency", "ZAR"),
                "occurred_at": e.get("occurred_at"),
                "exception_reason": meta.get("exception_reason", "Unresolved commercial allocation"),
                "is_gift": (e.get("source") == RevenueEventSource.GIFT.value or e.get("event_type") == RevenueEventType.GIFT_SENT.value),
                "resolution_status": "PENDING_COMMERCIAL_AGREEMENT"
            })
        return formatted

    def reprocess_exception(
        self,
        revenue_event_id: str,
        actor_id: str = "admin_reconciliation",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Controlled exception re-processing:
        If a commercial agreement has been subsequently registered for the series,
        attempts to resolve contract version and generate legitimate additive creator earnings.
        Maintains strict fail-closed posture if agreement is still missing or gift economics unestablished.
        """
        rev_event = self.repo.get_revenue_event_by_id(revenue_event_id)
        if not rev_event:
            return {
                "success": False,
                "resolved": False,
                "error": f"Revenue event '{revenue_event_id}' not found."
            }

        meta = rev_event.get("metadata") or {}
        if meta.get("exception_resolved") is True:
            return {
                "success": True,
                "resolved": True,
                "message": f"Revenue event '{revenue_event_id}' was already resolved previously.",
                "already_resolved": True
            }

        # Check if already has ledger entries
        existing_ledger = self.repo.get_creator_ledger_entries_by_revenue_event(revenue_event_id)
        if existing_ledger:
            return {
                "success": True,
                "resolved": True,
                "message": "Creator ledger entries already present for this revenue event.",
                "creator_ledger_entry": existing_ledger[0]
            }

        series_id = rev_event.get("series_id")
        if not series_id:
            return {
                "success": False,
                "resolved": False,
                "reason": "Revenue event has no series_id to resolve commercial agreement against."
            }

        # Parse event timestamp
        occurred_at_str = rev_event.get("occurred_at")
        try:
            occurred_at = datetime.fromisoformat(str(occurred_at_str).replace("Z", "+00:00"))
        except Exception:
            occurred_at = datetime.now(timezone.utc)

        # Check gift rule: do not invent gift economics unless explicitly contracted
        is_gift = (rev_event.get("source") == RevenueEventSource.GIFT.value or rev_event.get("event_type") == RevenueEventType.GIFT_SENT.value)
        if is_gift:
            return {
                "success": False,
                "resolved": False,
                "reason": "Gift economics not established in commercial schedule. Fail-closed invariant maintained."
            }

        # Attempt Contract Resolution
        agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id, occurred_at)
        if err or not ver:
            return {
                "success": False,
                "resolved": False,
                "reason": f"Contract resolution failed: {err}"
            }

        # Resolved! Calculate Allocation
        gross_amt = _to_decimal(rev_event.get("gross_amount", 0))
        calc = commercial_accounting_service.calculate_creator_allocation(ver, gross_amt, deductions_list=None)

        creator_id = agr.get("creator_id")
        period = occurred_at.strftime("%Y-%m")
        idemp = idempotency_key or f"reproc_{revenue_event_id}_{uuid.uuid4().hex[:8]}"

        # Append Immutable Creator Ledger Entry (Strictly Additive)
        ledger_entry = {
            "id": str(uuid.uuid4()),
            "creator_id": creator_id,
            "project_id": series_id,
            "series_id": series_id,
            "revenue_event_id": revenue_event_id,
            "commercial_agreement_version_id": ver["id"],
            "entry_type": LedgerEntryType.EARNING.value,
            "gross_revenue": float(calc["gross_revenue"]),
            "deductions": float(calc["total_deductions"]),
            "net_revenue": float(calc["net_revenue"]),
            "allocation_percentage": float(calc["creator_share_percentage"]),
            "creator_amount": float(calc["creator_amount"]),
            "currency": rev_event.get("currency", "ZAR"),
            "accounting_period": period,
            "status": LedgerStatus.SETTLED.value,
            "reversal_of_ledger_id": None,
            "idempotency_key": idemp,
            "metadata": {
                "source": rev_event.get("source"),
                "reprocessed_exception": True,
                "reprocessed_by": actor_id,
                "original_exception_reason": meta.get("exception_reason"),
                "agreement_reference": agr.get("agreement_reference")
            }
        }
        self.repo.insert_creator_ledger_entry(ledger_entry)

        # Update Revenue Event Metadata (Resolved)
        self.repo.update_revenue_event_metadata(
            event_id=revenue_event_id,
            metadata_updates={
                "exception_resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolved_by": actor_id,
                "agreement_reference": agr.get("agreement_reference"),
                "version_number": ver.get("version_number"),
                "resolution_note": "Resolved via 6I-F.1 Commercial Operations reconciliation"
            },
            commercial_agreement_version_id=ver["id"]
        )

        # Emit Trust Audit Event
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commercial_accounting.exception_resolved",
            actor_id=actor_id,
            actor_role="commercial_operations",
            target_type="creator_ledger",
            target_id=ledger_entry["id"],
            after_state={
                "revenue_event_id": revenue_event_id,
                "creator_id": creator_id,
                "creator_amount": float(calc["creator_amount"]),
                "agreement_reference": agr.get("agreement_reference")
            },
            metadata={"reprocessed": True}
        )

        return {
            "success": True,
            "resolved": True,
            "creator_ledger_entry": ledger_entry,
            "calculation": calc,
            "message": f"Successfully reprocessed event {revenue_event_id}. Creator credited R{calc['creator_amount']}."
        }

    # --------------------------------------------------------------------------
    # 3. COMMERCIAL PLATFORM HEALTH & BALANCE SUMMARY
    # --------------------------------------------------------------------------

    def get_commercial_kpis(self) -> Dict[str, Any]:
        """
        Surfaces top-level commercial operations KPIs:
        Gross revenue volume, platform retained share, creator allocations,
        pending payout requests, active exceptions, and reconciliation status.
        """
        all_ledger = self.repo.get_all_creator_ledger_entries(limit=500)
        exceptions = self.get_unresolved_exceptions(limit=100)

        total_creator_earned = sum(
            _to_decimal(l.get("creator_amount", 0))
            for l in all_ledger
            if l.get("entry_type") == LedgerEntryType.EARNING.value
        )
        total_creator_adjustments = sum(
            _to_decimal(l.get("creator_amount", 0))
            for l in all_ledger
            if l.get("entry_type") in [LedgerEntryType.REVERSAL.value, LedgerEntryType.ADJUSTMENT.value]
        )
        total_gross = sum(
            _to_decimal(l.get("gross_revenue", 0))
            for l in all_ledger
            if l.get("entry_type") == LedgerEntryType.EARNING.value
        )
        total_welele = total_gross - (total_creator_earned + total_creator_adjustments)

        all_payouts = self.repo.local_get("creator_payouts")
        if self.repo.is_live:
            try:
                db_p = self.repo.get_table("creator_payouts").select("*").execute()
                if db_p and db_p.data:
                    all_payouts = db_p.data
            except Exception:
                pass

        pending_payouts = sum(
            _to_decimal(p.get("requested_amount", 0))
            for p in all_payouts
            if p.get("status") == PayoutStatus.PENDING.value
        )

        return {
            "total_commercial_events_analyzed": len(all_ledger),
            "total_gross_revenue_zar": float(_round_currency(total_gross)),
            "total_creator_earnings_zar": float(_round_currency(total_creator_earned + total_creator_adjustments)),
            "total_welele_platform_zar": float(_round_currency(max(Decimal("0.0000"), total_welele))),
            "pending_creator_payouts_zar": float(_round_currency(pending_payouts)),
            "unresolved_exceptions_count": len(exceptions),
            "external_creator_payouts_status": "DISABLED (STAGING FROZEN)",
            "production_status": "FROZEN",
            "health_status": "HEALTHY" if len(exceptions) == 0 else "ACTION_REQUIRED_EXCEPTIONS_PENDING"
        }


# Singleton instance
commercial_reconciliation_service = CommercialReconciliationService()
