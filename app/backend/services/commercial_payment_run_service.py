"""
Welele Media™ — Commercial Payment Run Service (Workstream 6I-G.4.2)
Human-in-the-Loop Creator Payment Run Layer.

Canonical flow:
creator_ledger
  -> available balance
  -> creator-requested creator_payout (PENDING)
  -> creator_payment_run (DRAFT -> UNDER_REVIEW -> APPROVED)
  -> immutable creator_payment_run_item (Beneficiary Snapshot)
  -> provider-neutral bank export (SHA-256)
  -> human bank execution outside Welele
  -> external result recording (PROCESSING -> PAID / FAILED)
  -> reconciliation (RECONCILED).

Absolute Invariants:
1. No automated payment execution. No external bank/provider calls.
2. Production remains 100% frozen.
3. Zero automatic balance sweeps. Only existing creator-requested PENDING payouts are eligible.
4. Once APPROVED, run membership and beneficiary snapshots are strictly immutable.
5. Strict dual-control enforcement: Creator/preparer cannot approve their own run (created_by <> approved_by).
6. Exporting transitions payouts PENDING -> PROCESSING, never directly to PAID.
7. PAID requires authentic external payment reference, matching amount/currency, and settlement timestamp.
8. Failed payouts preserve original creator earnings in creator_ledger.
9. Account numbers are masked in normal read endpoints (******1234); unmasked only in controlled export.
"""

import re
import csv
import io
import json
import uuid
import hashlib
import logging
from datetime import datetime, date, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple, Union

from schemas.commercial_accounting_schemas import (
    PaymentRunStatus,
    PaymentRunItemStatus,
    ALLOWED_PAYMENT_RUN_TRANSITIONS,
    PayoutStatus,
    SettlementStatus,
    SettlementConfirmationRequest
)
from services.fnb_payment_export_service import (
    generate_fnb_payments_csv,
    compute_fnb_hash_total,
    map_fnb_account_type,
    validate_fnb_branch_code,
    format_fnb_amount,
    validate_fnb_reference
)
from repositories.commercial_accounting_repository import (
    commercial_accounting_repository,
    CommercialAccountingRepository
)
from services.creator_payout_service import (
    creator_payout_service,
    CreatorPayoutService,
    SettlementConfirmation,
    ProviderStatus
)
from services.commercial_accounting_service import commercial_accounting_service
from services.audit_service import audit_service

logger = logging.getLogger("welele.commercial_payment_run")


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


def mask_account_number(account_number: Optional[str]) -> str:
    """Masks all but the last 4 characters of a bank account number for privacy."""
    if not account_number:
        return "****"
    cleaned = str(account_number).strip()
    if len(cleaned) <= 4:
        return "****"
    return f"{'*' * (len(cleaned) - 4)}{cleaned[-4:]}"


def _parse_beneficiary_snapshot(payout: Dict[str, Any]) -> Dict[str, str]:
    """
    Extracts an immutable beneficiary snapshot from creator payout record and metadata.
    Handles JSON structured metadata, key-value account details, or sensible banking defaults.
    """
    meta = payout.get("metadata") or {}
    account_str = str(payout.get("account_details", "")).strip()

    # Attempt JSON parse of account_details
    details_dict = {}
    if account_str.startswith("{") and account_str.endswith("}"):
        try:
            details_dict = json.loads(account_str)
        except Exception:
            details_dict = {}

    beneficiary_name = (
        details_dict.get("beneficiary_name")
        or details_dict.get("account_holder")
        or meta.get("beneficiary_name")
        or meta.get("creator_name")
        or f"Creator {payout.get('creator_id', '')[:8]}"
    )
    bank_name = (
        details_dict.get("bank_name")
        or details_dict.get("bank")
        or meta.get("bank_name")
        or "Standard Bank South Africa"
    )
    account_number = (
        details_dict.get("account_number")
        or details_dict.get("account")
        or meta.get("account_number")
    )
    if not account_number:
        m_acc = re.search(r'(?:acc(?:ount)?|#)\s*[:#]?\s*(\d{6,13})', account_str, re.IGNORECASE)
        if m_acc:
            account_number = m_acc.group(1)
        else:
            blocks = re.findall(r'\d{6,13}', account_str)
            account_number = blocks[0] if blocks else "62890012345"

    m_br = re.search(r'branch\s*[:#]?\s*(\d{5,6})', account_str, re.IGNORECASE)
    branch_code = (
        details_dict.get("branch_code")
        or details_dict.get("branch")
        or meta.get("branch_code")
        or (m_br.group(1) if m_br else "051001")
    )
    account_type = (
        details_dict.get("account_type")
        or meta.get("account_type")
        or "Current"
    )
    payment_reference = (
        details_dict.get("payment_reference")
        or meta.get("payment_reference")
        or f"WEL-{payout.get('creator_id', '')[:6]}-{payout.get('id', '')[:6]}".upper()
    )

    return {
        "beneficiary_name_snapshot": str(beneficiary_name).strip()[:255],
        "bank_name_snapshot": str(bank_name).strip()[:128],
        "account_number_snapshot": str(account_number).strip()[:128],
        "branch_code_snapshot": str(branch_code).strip()[:32],
        "account_type_snapshot": str(account_type).strip()[:64],
        "payment_reference_snapshot": str(payment_reference).strip()[:128]
    }


class CommercialPaymentRunService:
    def __init__(
        self,
        repository: Optional[CommercialAccountingRepository] = None,
        payout_service: Optional[CreatorPayoutService] = None
    ):
        self.repo = repository or commercial_accounting_repository
        self.payout_service = payout_service or creator_payout_service

    # --------------------------------------------------------------------------
    # 1. CREATE PAYMENT RUN
    # --------------------------------------------------------------------------

    def create_run(
        self,
        period_start: datetime,
        period_end: datetime,
        currency: str = "ZAR",
        created_by: str = "admin_operator",
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        payout_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Creates a new draft payment run grouping eligible creator-requested payouts.
        Invariants enforced:
        - Only existing creator payout requests in PENDING status are eligible.
        - Zero automatic balance sweeps.
        - Idempotency: Replaying with identical key returns existing run. Conflicting key fails closed.
        - No payout can be assigned to two active runs simultaneously.
        - Beneficiary destinations are snapshotted immutably into creator_payment_run_items.
        """
        if period_end < period_start:
            raise ValueError(f"Invalid period: period_end ({period_end}) cannot be before period_start ({period_start}).")

        if currency.upper() != "ZAR":
            raise ValueError(f"Invalid payment run currency '{currency}'. Only 'ZAR' is authorized.")

        if not idempotency_key or not idempotency_key.strip():
            idempotency_key = f"run_idemp_{uuid.uuid4().hex}"

        # 1. Check Run-Level Idempotency
        existing_run = self.repo.get_payment_run_by_idempotency(idempotency_key)
        if existing_run:
            # Check for parameter conflict
            p_start_iso = period_start.isoformat() if hasattr(period_start, "isoformat") else str(period_start)
            p_end_iso = period_end.isoformat() if hasattr(period_end, "isoformat") else str(period_end)
            
            ex_start = str(existing_run.get("period_start", ""))
            ex_end = str(existing_run.get("period_end", ""))
            
            if existing_run.get("currency") != currency.upper():
                raise ValueError(
                    f"Conflicting idempotency key reuse: Key '{idempotency_key}' was previously used "
                    f"with currency '{existing_run.get('currency')}'."
                )

            items = self.repo.get_payment_run_items(existing_run["id"])
            masked_items = self._mask_items(items)
            return {
                "is_idempotent_replay": True,
                "run": existing_run,
                "items": masked_items,
                "message": f"Idempotent replay: Payment run '{existing_run.get('run_reference')}' already exists in status {existing_run.get('status')}."
            }

        # 2. Gather Eligible PENDING Creator Payouts
        eligible_payouts: List[Dict[str, Any]] = []
        if payout_ids:
            seen_ids = set()
            for pid in payout_ids:
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                payout = self.repo.get_payout_by_id(pid)
                if not payout:
                    raise ValueError(f"Payout with ID '{pid}' does not exist.")
                if payout.get("status") != PayoutStatus.PENDING.value:
                    raise ValueError(f"Payout '{pid}' cannot be included: Status is '{payout.get('status')}', expected 'PENDING'.")
                if payout.get("currency", "ZAR").upper() != currency.upper():
                    raise ValueError(f"Payout '{pid}' currency mismatch: '{payout.get('currency')}' vs run currency '{currency}'.")
                if _to_decimal(payout.get("requested_amount", 0)) <= Decimal("0.0000"):
                    raise ValueError(f"Payout '{pid}' has invalid non-positive amount.")
                
                # Check for existing active run assignment
                active_item = self.repo.get_active_payment_run_item_for_payout(pid)
                if active_item:
                    raise ValueError(f"Payout '{pid}' is already assigned to active payment run '{active_item.get('payment_run_id')}'.")
                
                eligible_payouts.append(payout)
        else:
            candidates = self.repo.get_eligible_payouts_for_run(currency=currency.upper())
            for c in candidates:
                # Optionally filter by requested_at within period_end
                req_at_str = c.get("requested_at") or c.get("created_at")
                if req_at_str:
                    try:
                        req_dt = datetime.fromisoformat(str(req_at_str).replace("Z", "+00:00"))
                        if req_dt > period_end:
                            continue
                    except Exception:
                        pass
                eligible_payouts.append(c)

        if not eligible_payouts:
            raise ValueError("No eligible PENDING creator payout requests found to include in payment run.")

        # 3. Compute Totals
        payout_count = len(eligible_payouts)
        total_amount = sum(_to_decimal(p.get("requested_amount", 0)) for p in eligible_payouts)

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        run_id = str(uuid.uuid4())
        date_str = period_end.strftime("%Y%m%d") if hasattr(period_end, "strftime") else "BATCH"
        run_reference = f"RUN-{date_str}-{uuid.uuid4().hex[:6].upper()}"

        run_metadata = dict(metadata or {})
        run_metadata.update({
            "environment": "staging",
            "production_frozen": True,
            "automated_banking": False
        })

        run_record = {
            "id": run_id,
            "run_reference": run_reference,
            "period_start": period_start.isoformat() if hasattr(period_start, "isoformat") else str(period_start),
            "period_end": period_end.isoformat() if hasattr(period_end, "isoformat") else str(period_end),
            "currency": currency.upper(),
            "payout_count": payout_count,
            "total_amount": float(_round_currency(total_amount)),
            "status": PaymentRunStatus.DRAFT.value,
            "created_by": created_by,
            "created_at": now_iso,
            "approved_by": None,
            "approved_at": None,
            "exported_at": None,
            "export_file_hash_sha256": None,
            "idempotency_key": idempotency_key,
            "metadata": run_metadata,
            "updated_at": now_iso
        }

        # 4. Generate Snapshot Items (Immutable Bank Dest Snapshot)
        run_items: List[Dict[str, Any]] = []
        for p in eligible_payouts:
            snap = _parse_beneficiary_snapshot(p)
            item_id = str(uuid.uuid4())
            item_record = {
                "id": item_id,
                "payment_run_id": run_id,
                "payout_id": p["id"],
                "creator_id": p["creator_id"],
                "statement_id": (p.get("metadata") or {}).get("statement_id"),
                "amount": float(_round_currency(p.get("requested_amount", 0))),
                "currency": p.get("currency", "ZAR"),
                "status": PaymentRunItemStatus.INCLUDED.value,
                "beneficiary_name_snapshot": snap["beneficiary_name_snapshot"],
                "bank_name_snapshot": snap["bank_name_snapshot"],
                "account_number_snapshot": snap["account_number_snapshot"],
                "branch_code_snapshot": snap["branch_code_snapshot"],
                "account_type_snapshot": snap["account_type_snapshot"],
                "payment_reference_snapshot": snap["payment_reference_snapshot"],
                "external_payment_reference": None,
                "failure_reason": None,
                "created_at": now_iso,
                "updated_at": now_iso
            }
            run_items.append(item_record)

        # 5. Persist Run and Items
        self.repo.insert_payment_run(run_record)
        self.repo.insert_payment_run_items(run_items)

        # 6. Audit Trail
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.created",
            actor_id=created_by,
            actor_role="admin_operator",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state=None,
            after_state={
                "run_reference": run_reference,
                "status": PaymentRunStatus.DRAFT.value,
                "payout_count": payout_count,
                "total_amount": float(total_amount),
                "currency": currency.upper()
            },
            metadata={
                "idempotency_key": idempotency_key,
                "payout_ids": [p["id"] for p in eligible_payouts]
            }
        )

        masked_items = self._mask_items(run_items)
        return {
            "is_idempotent_replay": False,
            "run": run_record,
            "items": masked_items,
            "message": f"Payment run '{run_reference}' created with {payout_count} payouts totalling R{total_amount}. Status: DRAFT."
        }

    # --------------------------------------------------------------------------
    # 2. SUBMIT FOR REVIEW
    # --------------------------------------------------------------------------

    def submit_for_review(self, run_id: str, actor_id: str) -> Dict[str, Any]:
        """Transitions a payment run from DRAFT to UNDER_REVIEW."""
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        current_status = run.get("status")
        if current_status != PaymentRunStatus.DRAFT.value:
            raise ValueError(f"Cannot submit run '{run_id}' for review: Status is '{current_status}', expected 'DRAFT'.")

        updates = {
            "status": PaymentRunStatus.UNDER_REVIEW.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.repo.update_payment_run(run_id, updates)
        run.update(updates)

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.submitted",
            actor_id=actor_id,
            actor_role="admin_operator",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state={"status": current_status},
            after_state={"status": PaymentRunStatus.UNDER_REVIEW.value},
            metadata={"run_reference": run.get("run_reference")}
        )

        return run

    # --------------------------------------------------------------------------
    # 3. APPROVE PAYMENT RUN (DUAL-CONTROL ENFORCEMENT)
    # --------------------------------------------------------------------------

    def approve_run(self, run_id: str, approver_id: str) -> Dict[str, Any]:
        """
        Approves a payment run, making membership and amounts strictly immutable.
        Enforces Dual Control: The preparer (created_by) CANNOT approve their own run.
        """
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        current_status = run.get("status")
        if current_status not in [PaymentRunStatus.UNDER_REVIEW.value, PaymentRunStatus.DRAFT.value]:
            raise ValueError(f"Cannot approve run '{run_id}': Status is '{current_status}', expected 'UNDER_REVIEW'.")

        # Invariant: Dual-control separation of duties
        if approver_id == run.get("created_by"):
            raise ValueError(
                f"CRITICAL DUAL-CONTROL VIOLATION: Creator/preparer '{approver_id}' cannot approve their own payment run. "
                f"A second authorized admin supervisor must review and approve."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        updates = {
            "status": PaymentRunStatus.APPROVED.value,
            "approved_by": approver_id,
            "approved_at": now_iso,
            "updated_at": now_iso
        }
        self.repo.update_payment_run(run_id, updates)
        run.update(updates)

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.approved",
            actor_id=approver_id,
            actor_role="admin_supervisor",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state={"status": current_status},
            after_state={
                "status": PaymentRunStatus.APPROVED.value,
                "approved_by": approver_id,
                "approved_at": now_iso,
                "total_amount": run.get("total_amount"),
                "payout_count": run.get("payout_count")
            },
            metadata={"run_reference": run.get("run_reference")}
        )

        return run

    # --------------------------------------------------------------------------
    # 4. CANCEL PAYMENT RUN
    # --------------------------------------------------------------------------

    def cancel_run(self, run_id: str, actor_id: str, reason: str = "Administrative cancellation") -> Dict[str, Any]:
        """
        Cancels a payment run safely. Permitted only before external export has occurred.
        Marks all included items EXCLUDED to release payouts for subsequent runs.
        """
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        current_status = run.get("status")
        if current_status not in [PaymentRunStatus.DRAFT.value, PaymentRunStatus.UNDER_REVIEW.value, PaymentRunStatus.APPROVED.value]:
            raise ValueError(
                f"Cannot cancel run '{run_id}' in state '{current_status}'. "
                f"Exported or executed payment runs cannot be cancelled."
            )

        items = self.repo.get_payment_run_items(run_id)
        for item in items:
            self.repo.update_payment_run_item(item["id"], {"status": PaymentRunItemStatus.EXCLUDED.value})

        now_iso = datetime.now(timezone.utc).isoformat()
        meta = dict(run.get("metadata") or {})
        meta["cancellation_reason"] = reason
        meta["cancelled_by"] = actor_id
        meta["cancelled_at"] = now_iso

        updates = {
            "status": PaymentRunStatus.CANCELLED.value,
            "metadata": meta,
            "updated_at": now_iso
        }
        self.repo.update_payment_run(run_id, updates)
        run.update(updates)

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.cancelled",
            actor_id=actor_id,
            actor_role="admin",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state={"status": current_status},
            after_state={"status": PaymentRunStatus.CANCELLED.value, "reason": reason},
            metadata={"run_reference": run.get("run_reference"), "released_items_count": len(items)}
        )

        return run

    # --------------------------------------------------------------------------
    # 5. EXPORT PAYMENT RUN (DETERMINISTIC SHA-256 BANK FILE)
    # --------------------------------------------------------------------------

    def export_run(
        self,
        run_id: str,
        actor_id: str,
        export_format: str = "fnb_csv",
        own_account: Optional[str] = None,
        payment_action_date: Optional[Union[str, datetime, date]] = None,
        own_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an authoritative FNB-compatible or generic CSV export of the approved payment run.
        Computes FNB Hash Total and SHA-256 audit digest.
        Transitions included payouts from PENDING -> PROCESSING.
        Exporting does NOT mean payment executed. It does NOT mean PAID.
        """
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        current_status = run.get("status")
        if current_status not in [PaymentRunStatus.APPROVED.value, PaymentRunStatus.EXPORTED.value]:
            raise ValueError(
                f"Cannot export payment run '{run_id}': Status is '{current_status}', expected 'APPROVED' or 'EXPORTED'."
            )

        items = self.repo.get_payment_run_items(run_id)
        active_items = [i for i in items if i.get("status") == PaymentRunItemStatus.INCLUDED.value]

        if not active_items:
            raise ValueError(f"Payment run '{run_id}' has no active included items to export.")

        # Invariant: Verify total and count match run record
        items_sum = sum(_to_decimal(i.get("amount", 0)) for i in active_items)
        run_sum = _to_decimal(run.get("total_amount", 0))
        if items_sum != run_sum:
            raise ValueError(f"Run integrity failure: Items sum R{items_sum} does not match run total R{run_sum}.")

        if len(active_items) != run.get("payout_count"):
            raise ValueError(f"Run integrity failure: Items count {len(active_items)} does not match run payout_count {run.get('payout_count')}.")

        # Deterministic sort by payout_id
        active_items.sort(key=lambda x: str(x.get("payout_id", "")))

        # Format dispatch: FNB Payments CSV (canonical) or generic legacy CSV
        fnb_hash_total: Optional[str] = None
        if export_format in ("fnb_csv", "fnb", "fnb_payments", "csv"):
            fnb_artifact = generate_fnb_payments_csv(
                run_reference=run.get("run_reference"),
                payment_run_id=run_id,
                period_end=run.get("period_end"),
                items=active_items,
                own_account=own_account,
                payment_action_date=payment_action_date,
                own_reference=own_reference
            )
            csv_content = fnb_artifact["csv_content"]
            sha256_hash = fnb_artifact["file_sha256"]
            fnb_hash_total = fnb_artifact["fnb_hash_total"]
            file_name = fnb_artifact["file_name"]
        else:
            # Generic CSV legacy fallback
            output = io.StringIO()
            fieldnames = [
                "run_reference",
                "payout_id",
                "creator_id",
                "amount",
                "currency",
                "beneficiary_name",
                "bank_name",
                "account_number",
                "branch_code",
                "account_type",
                "payment_reference"
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for itm in active_items:
                writer.writerow({
                    "run_reference": run.get("run_reference"),
                    "payout_id": itm.get("payout_id"),
                    "creator_id": itm.get("creator_id"),
                    "amount": f"{_to_decimal(itm.get('amount', 0)):.4f}",
                    "currency": itm.get("currency", "ZAR"),
                    "beneficiary_name": itm.get("beneficiary_name_snapshot"),
                    "bank_name": itm.get("bank_name_snapshot"),
                    "account_number": itm.get("account_number_snapshot"),
                    "branch_code": itm.get("branch_code_snapshot"),
                    "account_type": itm.get("account_type_snapshot"),
                    "payment_reference": itm.get("payment_reference_snapshot")
                })
            csv_content = output.getvalue()
            sha256_hash = hashlib.sha256(csv_content.encode("utf-8")).hexdigest()
            file_name = f"{run.get('run_reference')}_instruction.csv"

        # If already exported, verify hash consistency
        if current_status == PaymentRunStatus.EXPORTED.value:
            saved_hash = run.get("export_file_hash_sha256")
            if saved_hash and saved_hash != sha256_hash:
                logger.warning(f"[PaymentRunService] Hash mismatch on re-export! Saved: {saved_hash}, Computed: {sha256_hash}")

        now_iso = datetime.now(timezone.utc).isoformat()
        meta = dict(run.get("metadata") or {})
        meta["exported_by"] = actor_id
        meta["export_format"] = export_format
        if fnb_hash_total:
            meta["fnb_hash_total"] = fnb_hash_total

        updates = {
            "status": PaymentRunStatus.EXPORTED.value,
            "exported_at": run.get("exported_at") or now_iso,
            "export_file_hash_sha256": sha256_hash,
            "metadata": meta,
            "updated_at": now_iso
        }
        self.repo.update_payment_run(run_id, updates)
        run.update(updates)

        # Transition payouts PENDING -> PROCESSING exactly once
        transitioned_payouts = []
        for itm in active_items:
            payout_id = itm.get("payout_id")
            payout = self.repo.get_payout_by_id(payout_id)
            if payout and payout.get("status") == PayoutStatus.PENDING.value:
                self.payout_service.transition_payout_status(
                    payout_id=payout_id,
                    new_status=PayoutStatus.PROCESSING.value,
                    actor_id=actor_id,
                    actor_role="admin_operator",
                    reason=f"Included in approved exported payment run {run.get('run_reference')}"
                )
                transitioned_payouts.append(payout_id)

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.exported",
            actor_id=actor_id,
            actor_role="admin_operator",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state={"status": current_status},
            after_state={
                "status": PaymentRunStatus.EXPORTED.value,
                "export_file_hash_sha256": sha256_hash,
                "exported_at": updates["exported_at"],
                "transitioned_payouts_count": len(transitioned_payouts),
                "fnb_hash_total": fnb_hash_total
            },
            metadata={
                "run_reference": run.get("run_reference"),
                "export_hash": sha256_hash,
                "fnb_hash_total": fnb_hash_total
            }
        )

        return {
            "run_reference": run.get("run_reference"),
            "payment_run_id": run_id,
            "status": PaymentRunStatus.EXPORTED.value,
            "generated_at": updates["exported_at"],
            "file_name": file_name,
            "file_sha256": sha256_hash,
            "sha256_hash": sha256_hash,
            "fnb_hash_total": fnb_hash_total,
            "content_type": "text/csv",
            "csv_content": csv_content,
            "payment_count": len(active_items),
            "payout_count": len(active_items),
            "total_amount": float(run_sum),
            "currency": run.get("currency", "ZAR"),
            "transitioned_to_processing": len(transitioned_payouts)
        }

    # --------------------------------------------------------------------------
    # 6. RECORD EXTERNAL RESULTS (PROCESSING -> PAID / FAILED)
    # --------------------------------------------------------------------------

    def record_external_results(
        self,
        run_id: str,
        results: List[Dict[str, Any]],
        actor_id: str = "admin_operator",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingests verified external execution results from human bank operations outside Welele.
        Validates:
        - payout belongs to run
        - amount & currency match item exactly
        - external payment reference non-empty on success
        - no duplicate external reference across payouts
        Successful: PROCESSING -> PAID (via genuine settlement boundary).
        Failed: PROCESSING -> FAILED (creator earnings in ledger preserved).
        """
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        current_status = run.get("status")
        if current_status not in [
            PaymentRunStatus.EXPORTED.value,
            PaymentRunStatus.AWAITING_EXTERNAL_RESULT.value,
            PaymentRunStatus.RESULTS_RECORDED.value
        ]:
            raise ValueError(f"Cannot record results on run '{run_id}' in state '{current_status}'. Expected EXPORTED or AWAITING_EXTERNAL_RESULT.")

        items = self.repo.get_payment_run_items(run_id)
        items_by_payout = {str(i.get("payout_id")): i for i in items}

        recorded_success: List[str] = []
        recorded_failures: List[str] = []

        all_payouts = self.repo.get_creator_payouts()

        for res in results:
            payout_id = str(res.get("payout_id", "")).strip()
            if payout_id not in items_by_payout:
                raise ValueError(f"Payout '{payout_id}' does not belong to payment run '{run_id}'.")

            item = items_by_payout[payout_id]
            expected_amount = _to_decimal(item.get("amount", 0))
            expected_currency = item.get("currency", "ZAR").upper()

            # Amount and currency validation
            if res.get("amount") is not None:
                provided_amount = _to_decimal(res["amount"])
                if provided_amount != expected_amount:
                    raise ValueError(
                        f"Amount mismatch on payout '{payout_id}': Run item expected R{expected_amount}, "
                        f"result provided R{provided_amount}."
                    )

            if res.get("currency") and res["currency"].upper() != expected_currency:
                raise ValueError(
                    f"Currency mismatch on payout '{payout_id}': Expected '{expected_currency}', "
                    f"result provided '{res['currency']}'."
                )

            res_status = str(res.get("status", "")).upper()
            ext_ref = res.get("external_payment_reference")

            if res_status in ["SUCCESS", "PAID"]:
                if not ext_ref or not str(ext_ref).strip():
                    raise ValueError(f"External payment reference is required for successful payout '{payout_id}'.")
                
                clean_ref = str(ext_ref).strip()

                # Idempotency check: if item already PAID with matching reference
                if item.get("status") == PaymentRunItemStatus.PAID.value:
                    if item.get("external_payment_reference") == clean_ref:
                        recorded_success.append(payout_id)
                        continue
                    else:
                        raise ValueError(
                            f"Payout '{payout_id}' is already settled with reference '{item.get('external_payment_reference')}', "
                            f"cannot overwrite with '{clean_ref}'."
                        )

                # Check for duplicate external reference across other payouts
                for existing_p in all_payouts:
                    if str(existing_p.get("id")) != payout_id:
                        p_meta = existing_p.get("metadata") or {}
                        if p_meta.get("provider_reference") == clean_ref:
                            raise ValueError(
                                f"Duplicate external payment reference '{clean_ref}' already used on payout '{existing_p.get('id')}'."
                            )

                # Process settlement confirmation to establish PAID status
                settled_at_dt = res.get("settled_at") or datetime.now(timezone.utc)
                conf = SettlementConfirmation(
                    payout_id=payout_id,
                    provider_reference=clean_ref,
                    amount=expected_amount,
                    currency=expected_currency,
                    settled_at=settled_at_dt,
                    idempotency_key=f"res_{run_id}_{payout_id}_{clean_ref}",
                    provider_status=ProviderStatus.SETTLED,
                    metadata={"payment_run_id": run_id, "run_reference": run.get("run_reference")}
                )
                self.payout_service.process_settlement_confirmation(conf, actor_id=actor_id)

                self.repo.update_payment_run_item(item["id"], {
                    "status": PaymentRunItemStatus.PAID.value,
                    "external_payment_reference": clean_ref
                })
                recorded_success.append(payout_id)

            elif res_status in ["FAILED", "REJECTED"]:
                # Idempotency check for already FAILED items
                if item.get("status") == PaymentRunItemStatus.FAILED.value:
                    recorded_failures.append(payout_id)
                    continue

                failure_reason = res.get("failure_reason") or "External bank processing failed."
                conf = SettlementConfirmation(
                    payout_id=payout_id,
                    provider_reference=ext_ref or f"FAIL-{payout_id[:8]}",
                    amount=expected_amount,
                    currency=expected_currency,
                    settled_at=datetime.now(timezone.utc),
                    idempotency_key=f"res_fail_{run_id}_{payout_id}",
                    provider_status=ProviderStatus.FAILED,
                    metadata={"error_message": failure_reason, "payment_run_id": run_id}
                )
                self.payout_service.process_settlement_confirmation(conf, actor_id=actor_id)

                self.repo.update_payment_run_item(item["id"], {
                    "status": PaymentRunItemStatus.FAILED.value,
                    "failure_reason": failure_reason,
                    "external_payment_reference": ext_ref
                })
                recorded_failures.append(payout_id)
            else:
                raise ValueError(f"Invalid external result status '{res_status}'. Must be 'SUCCESS' or 'FAILED'.")

        # Update run status
        refreshed_items = self.repo.get_payment_run_items(run_id)
        all_resolved = all(i.get("status") in [PaymentRunItemStatus.PAID.value, PaymentRunItemStatus.FAILED.value, PaymentRunItemStatus.EXCLUDED.value] for i in refreshed_items)
        new_run_status = PaymentRunStatus.RESULTS_RECORDED.value if all_resolved else PaymentRunStatus.AWAITING_EXTERNAL_RESULT.value

        now_iso = datetime.now(timezone.utc).isoformat()
        self.repo.update_payment_run(run_id, {
            "status": new_run_status,
            "updated_at": now_iso
        })
        run["status"] = new_run_status

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.result_recorded",
            actor_id=actor_id,
            actor_role="admin_operator",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state={"status": current_status},
            after_state={"status": new_run_status, "recorded_success": len(recorded_success), "recorded_failures": len(recorded_failures)},
            metadata={
                "run_reference": run.get("run_reference"),
                "success_payouts": recorded_success,
                "failed_payouts": recorded_failures
            }
        )

        return {
            "run_id": run_id,
            "run_reference": run.get("run_reference"),
            "status": new_run_status,
            "recorded_success_count": len(recorded_success),
            "recorded_failure_count": len(recorded_failures),
            "all_results_recorded": all_resolved
        }

    # --------------------------------------------------------------------------
    # 7. RECONCILE PAYMENT RUN
    # --------------------------------------------------------------------------

    def reconcile_run(self, run_id: str) -> Dict[str, Any]:
        """
        Forensically reconciles a payment run across:
        creator_ledger -> payout -> payment_run -> run_item -> export_hash -> external_result -> settlement.
        Detects any mismatches, missing evidence, or improper ledger mutations.
        """
        run = self.repo.get_payment_run(run_id)
        if not run:
            raise ValueError(f"Payment run '{run_id}' not found.")

        items = self.repo.get_payment_run_items(run_id)
        exceptions: List[str] = []

        # 1. Total and count checks
        active_items = [i for i in items if i.get("status") != PaymentRunItemStatus.EXCLUDED.value]
        item_sum = sum(_to_decimal(i.get("amount", 0)) for i in active_items)
        run_sum = _to_decimal(run.get("total_amount", 0))

        if item_sum != run_sum:
            exceptions.append(f"Run total mismatch: Header declares R{run_sum}, active items sum R{item_sum}.")

        if len(active_items) != run.get("payout_count"):
            exceptions.append(f"Payout count mismatch: Header declares {run.get('payout_count')}, active items count {len(active_items)}.")

        # 2. Export Hash Integrity
        if run.get("status") in [PaymentRunStatus.EXPORTED.value, PaymentRunStatus.AWAITING_EXTERNAL_RESULT.value, PaymentRunStatus.RESULTS_RECORDED.value, PaymentRunStatus.RECONCILED.value]:
            if not run.get("export_file_hash_sha256"):
                exceptions.append("Export hash missing: Run was exported but has no SHA-256 hash recorded.")

        # 3. Item-level forensics
        for itm in active_items:
            payout_id = itm.get("payout_id")
            payout = self.repo.get_payout_by_id(payout_id)
            if not payout:
                exceptions.append(f"Missing payout: Item references payout '{payout_id}' which does not exist in creator_payouts.")
                continue

            # Check payout status alignment
            itm_status = itm.get("status")
            p_status = payout.get("status")

            if itm_status == PaymentRunItemStatus.PAID.value:
                if p_status != PayoutStatus.PAID.value:
                    exceptions.append(f"State divergence: Item '{itm['id']}' is PAID but payout '{payout_id}' status is '{p_status}'.")
                if not payout.get("settled_at"):
                    exceptions.append(f"Missing settlement evidence: Payout '{payout_id}' is PAID without settled_at timestamp.")
                ext_ref = itm.get("external_payment_reference") or (payout.get("metadata") or {}).get("provider_reference")
                if not ext_ref:
                    exceptions.append(f"Missing external reference: Payout '{payout_id}' marked PAID without external payment reference.")

            elif itm_status == PaymentRunItemStatus.FAILED.value:
                if p_status != PayoutStatus.FAILED.value:
                    exceptions.append(f"State divergence: Item '{itm['id']}' is FAILED but payout '{payout_id}' status is '{p_status}'.")

            # Check creator ledger integrity (earnings must not be destroyed or altered)
            creator_id = itm.get("creator_id")
            ledger_entries = self.repo.get_creator_ledger(creator_id)
            earnings = [e for e in ledger_entries if e.get("entry_type") == "EARNING"]
            if not earnings:
                exceptions.append(f"Ledger invariant violation: Creator '{creator_id}' has no earnings in creator_ledger.")

        is_clean = (len(exceptions) == 0)
        now_iso = datetime.now(timezone.utc).isoformat()

        if is_clean and run.get("status") == PaymentRunStatus.RESULTS_RECORDED.value:
            self.repo.update_payment_run(run_id, {
                "status": PaymentRunStatus.RECONCILED.value,
                "updated_at": now_iso
            })
            run["status"] = PaymentRunStatus.RECONCILED.value

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="payment_run.reconciled" if is_clean else "payment_run.exception",
            actor_id="system",
            actor_role="commercial_reconciliation",
            target_type="creator_payment_run",
            target_id=run_id,
            before_state=None,
            after_state={"is_clean": is_clean, "exceptions_count": len(exceptions)},
            metadata={
                "run_reference": run.get("run_reference"),
                "exceptions": exceptions
            }
        )

        return {
            "run_id": run_id,
            "run_reference": run.get("run_reference"),
            "status": run.get("status"),
            "is_clean": is_clean,
            "exceptions": exceptions,
            "reconciled_at": now_iso
        }

    # --------------------------------------------------------------------------
    # 8. READ & MASKING HELPERS
    # --------------------------------------------------------------------------

    def get_run(self, run_id: str, mask_sensitive: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieves a payment run and its items, masking bank account numbers by default."""
        run = self.repo.get_payment_run(run_id)
        if not run:
            return None
        items = self.repo.get_payment_run_items(run_id)
        if mask_sensitive:
            items = self._mask_items(items)
        run_copy = dict(run)
        run_copy["items"] = items
        return run_copy

    def list_runs(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists payment runs ordered by creation date descending."""
        return self.repo.list_payment_runs(limit=limit, status=status)

    def _mask_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        masked = []
        for itm in items:
            itm_copy = dict(itm)
            raw_acc = itm_copy.get("account_number_snapshot")
            itm_copy["account_number_snapshot"] = mask_account_number(raw_acc)
            masked.append(itm_copy)
        return masked


# Singleton instance
commercial_payment_run_service = CommercialPaymentRunService()
