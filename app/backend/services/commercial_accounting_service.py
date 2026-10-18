"""
Welele Media™ — Commercial Accounting Service (Workstream 6I-E)
Implements authoritative commercial-accounting layer:
- Contract resolution (Model A / Model B, effective versioning, fail-closed)
- Revenue event recording & permitted deduction processing
- Creator allocation & immutable append-only creator ledger
- Balance tracking (EARNED, SETTLED, AVAILABLE, PAID, HELD)
- Provider-neutral payout requests (STAGING ONLY — external rails NOT activated)
- Reproducible accounting statements
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional, Tuple

from schemas.commercial_accounting_schemas import (
    CommercialModel,
    AgreementStatus,
    RevenueEventSource,
    RevenueEventType,
    SettlementStatus,
    DeductionType,
    LedgerEntryType,
    LedgerStatus,
    PayoutStatus,
    CreatorBalances,
)
from repositories.commercial_accounting_repository import (
    commercial_accounting_repository,
    CommercialAccountingRepository,
    to_uuid
)
from services.audit_service import audit_service

logger = logging.getLogger("welele.commercial_accounting")


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


class CommercialAccountingService:
    def __init__(self, repository: Optional[CommercialAccountingRepository] = None):
        self.repo = repository or commercial_accounting_repository

    # --------------------------------------------------------------------------
    # 1. CONTRACT RESOLUTION (FAIL-CLOSED)
    # --------------------------------------------------------------------------

    def resolve_commercial_agreement_version(
        self,
        series_id: str,
        occurred_at: Optional[datetime] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
        """
        Resolves governing commercial agreement and effective contract version.
        Resolution Chain:
          Project/Series -> Commercial Agreement -> Effective Version -> Model & Schedule

        Fail-closed rules:
        - If no agreement exists for series: fails closed (returns None, None, error_reason).
        - If agreement is not ACTIVE: fails closed.
        - If no version covers occurred_at: fails closed (future version or expired version rejected).
        - NEVER defaults to 40% or 100% or copies coin values.
        """
        if not occurred_at:
            occurred_at = datetime.now(timezone.utc)
        elif occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        agreement = self.repo.get_commercial_agreement_by_series(series_id)
        if not agreement:
            return None, None, f"No commercial agreement found for series '{series_id}'"

        if agreement.get("status") != AgreementStatus.ACTIVE.value:
            return None, None, f"Commercial agreement '{agreement.get('agreement_reference')}' is not ACTIVE (status: {agreement.get('status')})"

        versions = self.repo.get_agreement_versions(agreement["id"])
        if not versions:
            return agreement, None, f"No contract versions registered for agreement '{agreement.get('agreement_reference')}'"

        matching_version = None
        for v in versions:
            ef_str = v.get("effective_from")
            et_str = v.get("effective_to")

            try:
                ef = datetime.fromisoformat(str(ef_str).replace("Z", "+00:00"))
            except Exception:
                continue

            et = None
            if et_str:
                try:
                    et = datetime.fromisoformat(str(et_str).replace("Z", "+00:00"))
                except Exception:
                    et = None

            # Condition: effective_from <= occurred_at < effective_to (or effective_to is None)
            if ef <= occurred_at:
                if et is None or occurred_at < et:
                    matching_version = v
                    break

        if not matching_version:
            return agreement, None, f"No effective contract version for agreement '{agreement.get('agreement_reference')}' at timestamp {occurred_at.isoformat()}"

        return agreement, matching_version, None

    # --------------------------------------------------------------------------
    # 2. CALCULATION OF CREATOR ALLOCATION
    # --------------------------------------------------------------------------

    def calculate_creator_allocation(
        self,
        version: Dict[str, Any],
        gross_amount: Decimal,
        deductions_list: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates Net Revenue and Creator Allocation from governing contract version.
        Rules:
        - Gross Revenue >= 0
        - Deductions >= 0
        - Deductions cannot exceed Gross Revenue (reject if deductions > gross)
        - Net Revenue = Gross Revenue - Deductions
        - Creator Share % is resolved from version schedule:
          * Model A: version creator_share_percentage (default 0.0000 unless explicit override)
          * Model B: version creator_share_percentage (e.g. 0.4000)
        """
        gross = _to_decimal(gross_amount)
        if gross < Decimal("0"):
            raise ValueError(f"Gross revenue cannot be negative: {gross}")

        total_deductions = Decimal("0.0000")
        processed_deductions = []

        if deductions_list:
            for d in deductions_list:
                amt = _to_decimal(d.get("amount", 0))
                if amt < Decimal("0"):
                    raise ValueError(f"Deduction amount cannot be negative: {amt}")
                total_deductions += amt
                processed_deductions.append({
                    "deduction_type": d.get("deduction_type", DeductionType.PAYMENT_PROCESSING_FEE.value),
                    "amount": _round_currency(amt),
                    "contractual_basis": d.get("contractual_basis", "Contractual deduction"),
                    "source_reference": d.get("source_reference"),
                    "metadata": d.get("metadata", {})
                })

        if total_deductions > gross:
            raise ValueError(f"Total deductions ({total_deductions}) cannot exceed gross revenue ({gross})")

        net_revenue = gross - total_deductions
        creator_share_pct = _to_decimal(version.get("creator_share_percentage", "0.0000"))
        welele_share_pct = _to_decimal(version.get("welele_share_percentage", "1.0000"))

        creator_amount = _round_currency(net_revenue * creator_share_pct)
        welele_amount = _round_currency(net_revenue * welele_share_pct)

        return {
            "gross_revenue": _round_currency(gross),
            "total_deductions": _round_currency(total_deductions),
            "deductions": processed_deductions,
            "net_revenue": _round_currency(net_revenue),
            "commercial_model": version.get("commercial_model"),
            "creator_share_percentage": creator_share_pct,
            "welele_share_percentage": welele_share_pct,
            "creator_amount": creator_amount,
            "welele_amount": welele_amount
        }

    # --------------------------------------------------------------------------
    # 3. COMMERCIAL EVENT PROCESSING & LEDGER RECORDING
    # --------------------------------------------------------------------------

    def process_commercial_event(
        self,
        series_id: Optional[str],
        episode_id: Optional[str],
        source: RevenueEventSource,
        source_transaction_id: str,
        event_type: RevenueEventType,
        gross_amount: Decimal,
        currency: str = "ZAR",
        occurred_at: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        deductions_list: Optional[List[Dict[str, Any]]] = None,
        creator_id_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authoritative Commercial Accounting Execution Flow:
        1. Verify Idempotency.
        2. Attempt Contract Resolution against Series.
        3. Fail-Closed check: if unresolved or gift without schedule, record event with exception, NO creator earnings.
        4. If resolved:
           - Record Revenue Event
           - Record Contractual Deductions
           - Append immutable Creator Ledger entry
           - Emit audit trail event
        """
        if not occurred_at:
            occurred_at = datetime.now(timezone.utc)
        elif occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)

        if not idempotency_key:
            idempotency_key = f"comm_evt_{uuid.uuid4().hex}"

        metadata = metadata or {}
        accounting_period = occurred_at.strftime("%Y-%m")

        # 1. Check Idempotency for existing Revenue Event
        existing_rev_event = self.repo.get_revenue_event_by_idempotency(idempotency_key)
        if existing_rev_event:
            ledger_entry = self.repo.get_creator_ledger_entry_by_idempotency(idempotency_key)
            return {
                "is_idempotent_replay": True,
                "revenue_event": existing_rev_event,
                "creator_ledger_entry": ledger_entry,
                "status": "RECORDED_PREVIOUSLY"
            }

        # 2. Check Gift Exception Rule (Requirement 12):
        # "Do not invent a gift revenue-share rule. If governing commercial schedule does not establish gift economics,
        # record commercial event + accounting exception, do NOT invent entitlement."
        is_gift = (source == RevenueEventSource.GIFT or event_type == RevenueEventType.GIFT_SENT)

        # 3. Contract Resolution
        agreement = None
        version = None
        resolution_error = None

        if series_id:
            agreement, version, resolution_error = self.resolve_commercial_agreement_version(series_id, occurred_at)
        else:
            resolution_error = "No series_id provided for commercial contract resolution."

        creator_id = creator_id_override or (agreement.get("creator_id") if agreement else None)

        # 4. Fail-Closed Commercial Control
        if resolution_error or not version or is_gift:
            reason = resolution_error or ("Gift economics not established in commercial schedule" if is_gift else "Unresolved agreement")
            rev_event = {
                "id": str(uuid.uuid4()),
                "project_id": series_id,
                "series_id": series_id,
                "episode_id": episode_id,
                "source": source.value if hasattr(source, "value") else str(source),
                "source_transaction_id": source_transaction_id,
                "event_type": event_type.value if hasattr(event_type, "value") else str(event_type),
                "gross_amount": float(gross_amount),
                "currency": currency,
                "occurred_at": occurred_at.isoformat(),
                "settled_at": occurred_at.isoformat(),
                "settlement_status": SettlementStatus.SETTLED.value,
                "commercial_agreement_version_id": None,
                "idempotency_key": idempotency_key,
                "metadata": {
                    **metadata,
                    "unresolved_commercial_allocation": True,
                    "accounting_exception": True,
                    "exception_reason": reason,
                    "fail_closed": True
                }
            }
            self.repo.insert_revenue_event(rev_event)

            logger.warning(
                f"[CommercialAccounting:FailClosed] Event recorded without creator allocation: "
                f"source={source}, series={series_id}, reason={reason}"
            )
            return {
                "is_idempotent_replay": False,
                "revenue_event": rev_event,
                "creator_ledger_entry": None,
                "unresolved_allocation": True,
                "reason": reason,
                "creator_earnings_credited": False
            }

        # 5. Calculate Allocation under Resolved Contract Version
        try:
            calc = self.calculate_creator_allocation(version, gross_amount, deductions_list)
        except Exception as e:
            logger.error(f"[CommercialAccounting:CalculationError] {e}")
            raise

        # 6. Record Revenue Event
        rev_event_id = str(uuid.uuid4())
        rev_event = {
            "id": rev_event_id,
            "project_id": series_id,
            "series_id": series_id,
            "episode_id": episode_id,
            "source": source.value if hasattr(source, "value") else str(source),
            "source_transaction_id": source_transaction_id,
            "event_type": event_type.value if hasattr(event_type, "value") else str(event_type),
            "gross_amount": float(calc["gross_revenue"]),
            "currency": currency,
            "occurred_at": occurred_at.isoformat(),
            "settled_at": occurred_at.isoformat(),
            "settlement_status": SettlementStatus.SETTLED.value,
            "commercial_agreement_version_id": version["id"],
            "idempotency_key": idempotency_key,
            "metadata": {
                **metadata,
                "agreement_reference": agreement.get("agreement_reference"),
                "version_number": version.get("version_number"),
                "commercial_model": version.get("commercial_model"),
                "net_revenue": float(calc["net_revenue"])
            }
        }
        self.repo.insert_revenue_event(rev_event)

        # 7. Record Deductions
        for d in calc["deductions"]:
            deduction_record = {
                "id": str(uuid.uuid4()),
                "revenue_event_id": rev_event_id,
                "deduction_type": d["deduction_type"],
                "amount": float(d["amount"]),
                "currency": currency,
                "contractual_basis": d["contractual_basis"],
                "source_reference": d.get("source_reference"),
                "metadata": d.get("metadata", {})
            }
            self.repo.insert_revenue_deduction(deduction_record)

        # 8. Append Creator Ledger Entry (Authoritative Financial Record)
        ledger_entry = {
            "id": str(uuid.uuid4()),
            "creator_id": creator_id or agreement.get("creator_id"),
            "project_id": series_id,
            "series_id": series_id,
            "revenue_event_id": rev_event_id,
            "commercial_agreement_version_id": version["id"],
            "entry_type": LedgerEntryType.EARNING.value,
            "gross_revenue": float(calc["gross_revenue"]),
            "deductions": float(calc["total_deductions"]),
            "net_revenue": float(calc["net_revenue"]),
            "allocation_percentage": float(calc["creator_share_percentage"]),
            "creator_amount": float(calc["creator_amount"]),
            "currency": currency,
            "accounting_period": accounting_period,
            "status": LedgerStatus.SETTLED.value,
            "reversal_of_ledger_id": None,
            "idempotency_key": idempotency_key,
            "metadata": {
                "source": source.value if hasattr(source, "value") else str(source),
                "agreement_reference": agreement.get("agreement_reference"),
                "commercial_model": version.get("commercial_model"),
                "episode_id": episode_id
            }
        }
        self.repo.insert_creator_ledger_entry(ledger_entry)

        # 9. Audit Event Emission
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="creator_commercial_accounting.earning_recorded",
            actor_id="system",
            actor_role="commercial_accounting",
            target_type="creator_ledger",
            target_id=ledger_entry["id"],
            after_state={
                "creator_id": ledger_entry["creator_id"],
                "creator_amount": ledger_entry["creator_amount"],
                "currency": currency,
                "commercial_model": version.get("commercial_model"),
                "agreement_reference": agreement.get("agreement_reference")
            },
            metadata={
                "revenue_event_id": rev_event_id,
                "idempotency_key": idempotency_key
            }
        )

        return {
            "is_idempotent_replay": False,
            "revenue_event": rev_event,
            "creator_ledger_entry": ledger_entry,
            "calculation": calc,
            "creator_earnings_credited": True
        }

    # --------------------------------------------------------------------------
    # 4. EPISODE UNLOCK CONVENIENCE WRAPPER
    # --------------------------------------------------------------------------

    def process_episode_unlock(
        self,
        series_id: str,
        episode_id: str,
        viewer_id: str,
        coin_price: int,
        source_transaction_id: str,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Called upon successful atomic viewer coin debit.
        Converts episode unlock to commercial accounting consequence.
        Note: Coin value in ZAR is determined by standard nominal rate (e.g. R0.13 per coin, or R0.65 for 5 coins)
        or direct coin monetary valuation schedule.
        """
        # Nominal gross monetary valuation: 5 coins = R0.65 (R0.13 per coin)
        gross_zar = Decimal(str(coin_price)) * Decimal("0.1300")

        # Invariant: No contractual deduction applied unless explicitly established by applicable schedule
        if not idempotency_key:
            idemp = f"unl_{uuid.uuid5(uuid.NAMESPACE_DNS, f'{series_id}:{episode_id}:{viewer_id}:{source_transaction_id}').hex}"
        else:
            idemp = idempotency_key[:128]

        return self.process_commercial_event(
            series_id=series_id,
            episode_id=episode_id,
            source=RevenueEventSource.EPISODE_UNLOCK,
            source_transaction_id=source_transaction_id,
            event_type=RevenueEventType.COIN_UNLOCK,
            gross_amount=gross_zar,
            currency="ZAR",
            idempotency_key=idemp,
            metadata={
                "viewer_id": viewer_id,
                "coins_spent": coin_price,
                "coin_price": coin_price
            },
            deductions_list=None
        )

    # --------------------------------------------------------------------------
    # 5. BALANCE REPORTING & STATES
    # --------------------------------------------------------------------------

    def get_creator_balances(self, creator_id: str, currency: str = "ZAR") -> CreatorBalances:
        """
        Calculates authoritative creator balances from immutable creator_ledger and creator_payouts.
        Balances:
        - EARNED: All positive earnings regardless of status (excluding reversals).
        - SETTLED: Settled earnings minus completed adjustments/reversals.
        - AVAILABLE: Settled earnings minus pending payout holds.
        - PAID: Confirmed externally settled payouts (remains 0.0000 in 6I-E!).
        - HELD: Funds held for pending payout requests or review.
        """
        ledger = self.repo.get_creator_ledger(creator_id)
        payouts = self.repo.get_creator_payouts(creator_id)

        earned = Decimal("0.0000")
        settled = Decimal("0.0000")
        held = Decimal("0.0000")
        paid = Decimal("0.0000")
        disputed = Decimal("0.0000")
        reversed_amt = Decimal("0.0000")

        for entry in ledger:
            if entry.get("currency", "ZAR") != currency:
                continue

            amt = _to_decimal(entry.get("creator_amount", 0))
            entry_type = entry.get("entry_type")
            status = entry.get("status")

            if entry_type == LedgerEntryType.EARNING.value:
                earned += amt
                if status in [LedgerStatus.SETTLED.value, LedgerStatus.AVAILABLE.value]:
                    settled += amt
                elif status == LedgerStatus.HELD.value:
                    held += amt
                elif status == LedgerStatus.DISPUTED.value:
                    disputed += amt
            elif entry_type in [LedgerEntryType.REVERSAL.value, LedgerEntryType.REFUND.value, LedgerEntryType.CHARGEBACK.value]:
                reversed_amt += abs(amt)
                settled -= abs(amt)
            elif entry_type == LedgerEntryType.PAYOUT_HOLD.value:
                held += abs(amt)
                settled -= abs(amt)

        # Pending payouts hold funds from available
        pending_payout_total = sum(
            _to_decimal(p.get("requested_amount", 0))
            for p in payouts
            if p.get("status") in [PayoutStatus.PENDING.value, PayoutStatus.PROCESSING.value, PayoutStatus.HELD.value]
            and p.get("currency", "ZAR") == currency
        )

        available = max(Decimal("0.0000"), settled - pending_payout_total)

        # Invariant: PAID remains 0.0000 unless settled external confirmation exists
        paid = sum(
            _to_decimal(p.get("requested_amount", 0))
            for p in payouts
            if p.get("status") in [PayoutStatus.PAID.value, PayoutStatus.SETTLED.value]
            and p.get("currency", "ZAR") == currency
        )

        return CreatorBalances(
            creator_id=creator_id,
            currency=currency,
            earned=_round_currency(earned),
            settled=_round_currency(settled),
            available=_round_currency(available),
            paid=_round_currency(paid),
            held=_round_currency(held + pending_payout_total),
            disputed=_round_currency(disputed),
            reversed=_round_currency(reversed_amt)
        )

    # --------------------------------------------------------------------------
    # 6. PAYOUT REQUEST (DELEGATED TO CREATOR PAYOUT SERVICE)
    # --------------------------------------------------------------------------

    def request_payout(
        self,
        creator_id: str,
        requested_amount: Decimal,
        currency: str = "ZAR",
        payout_method: str = "Bank EFT",
        account_details: str = "Default Account",
        idempotency_key: Optional[str] = None,
        allow_legacy_shadow: bool = False
    ) -> Dict[str, Any]:
        """
        Delegates payout creation to CreatorPayoutService (6I-G.2).
        Enforces authoritative balance validation, creator ledger allocations,
        and append-only immutability.
        """
        from services.creator_payout_service import creator_payout_service
        return creator_payout_service.request_payout(
            creator_id=creator_id,
            requested_amount=requested_amount,
            currency=currency,
            payout_method=payout_method,
            account_details=account_details,
            idempotency_key=idempotency_key
        )


    # --------------------------------------------------------------------------
    # 7. ADDITIVE ADJUSTMENTS & REVERSALS (APPEND-ONLY)
    # --------------------------------------------------------------------------

    def record_adjustment(
        self,
        creator_id: str,
        original_ledger_id: str,
        adjustment_type: LedgerEntryType,
        amount: Decimal,
        currency: str = "ZAR",
        reason: str = "Adjustment",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an additive reversal or adjustment entry.
        Never mutates the historical financial entry.
        """
        adj_amt = _to_decimal(amount)
        if adj_amt <= Decimal("0"):
            raise ValueError("Adjustment amount must be positive.")

        if not idempotency_key:
            idempotency_key = f"adj_{uuid.uuid4().hex}"

        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")

        # Negative amount for deductions/reversals from creator
        signed_amount = -abs(adj_amt)

        ledger_entry = {
            "id": str(uuid.uuid4()),
            "creator_id": creator_id,
            "project_id": None,
            "series_id": None,
            "revenue_event_id": None,
            "commercial_agreement_version_id": None,
            "entry_type": adjustment_type.value if hasattr(adjustment_type, "value") else str(adjustment_type),
            "gross_revenue": 0.0000,
            "deductions": 0.0000,
            "net_revenue": 0.0000,
            "allocation_percentage": 0.0000,
            "creator_amount": float(signed_amount),
            "currency": currency,
            "accounting_period": period,
            "status": LedgerStatus.SETTLED.value,
            "reversal_of_ledger_id": original_ledger_id,
            "idempotency_key": idempotency_key,
            "metadata": {
                "reason": reason,
                "original_ledger_id": original_ledger_id
            }
        }
        self.repo.insert_creator_ledger_entry(ledger_entry)
        return ledger_entry

    # --------------------------------------------------------------------------
    # 8. STATEMENTS GENERATION (REPRODUCIBLE FROM ACCOUNTING RECORDS)
    # --------------------------------------------------------------------------

    def generate_statement(
        self,
        creator_id: str,
        accounting_period: str,
        currency: str = "ZAR"
    ) -> Dict[str, Any]:
        """
        Generates or reproduces an auditable creator statement from the underlying ledger.
        """
        entries = self.repo.get_creator_ledger(creator_id, accounting_period=accounting_period)
        payouts = self.repo.get_creator_payouts(creator_id)

        gross_revenue = Decimal("0.0000")
        total_deductions = Decimal("0.0000")
        net_revenue = Decimal("0.0000")
        total_earnings = Decimal("0.0000")
        total_adjustments = Decimal("0.0000")

        lines = []
        for e in entries:
            if e.get("currency", "ZAR") != currency:
                continue

            entry_type = e.get("entry_type")
            c_amt = _to_decimal(e.get("creator_amount", 0))

            if entry_type == LedgerEntryType.EARNING.value:
                gross_revenue += _to_decimal(e.get("gross_revenue", 0))
                total_deductions += _to_decimal(e.get("deductions", 0))
                net_revenue += _to_decimal(e.get("net_revenue", 0))
                total_earnings += c_amt
                lines.append({
                    "statement_id": "",
                    "ledger_entry_id": e.get("id"),
                    "line_type": "EARNING",
                    "project_id": e.get("project_id"),
                    "series_id": e.get("series_id"),
                    "description": f"Content Earning ({e.get('metadata', {}).get('agreement_reference', 'Standard')})",
                    "amount": float(c_amt)
                })
            elif entry_type in [LedgerEntryType.REVERSAL.value, LedgerEntryType.REFUND.value, LedgerEntryType.CHARGEBACK.value, LedgerEntryType.ADJUSTMENT.value]:
                total_adjustments += c_amt
                lines.append({
                    "statement_id": "",
                    "ledger_entry_id": e.get("id"),
                    "line_type": "ADJUSTMENT",
                    "project_id": e.get("project_id"),
                    "series_id": e.get("series_id"),
                    "description": f"Adjustment: {e.get('metadata', {}).get('reason', 'Ledger adjustment')}",
                    "amount": float(c_amt)
                })

        total_payouts = Decimal("0.0000")
        closing_balance = total_earnings + total_adjustments - total_payouts

        existing_stmt = self.repo.get_statement(creator_id, accounting_period, currency)
        statement_id = existing_stmt["id"] if existing_stmt else str(uuid.uuid4())
        for l in lines:
            l["statement_id"] = statement_id

        statement = {
            "id": statement_id,
            "creator_id": creator_id,
            "accounting_period": accounting_period,
            "currency": currency,
            "opening_balance": 0.0000,
            "gross_revenue": float(_round_currency(gross_revenue)),
            "total_deductions": float(_round_currency(total_deductions)),
            "net_revenue": float(_round_currency(net_revenue)),
            "total_earnings": float(_round_currency(total_earnings)),
            "total_adjustments": float(_round_currency(total_adjustments)),
            "total_payouts": float(_round_currency(total_payouts)),
            "closing_balance": float(_round_currency(closing_balance)),
            "status": "FINALIZED",
            "lines": lines
        }
        self.repo.upsert_statement(statement)
        self.repo.insert_statement_lines(lines)
        return statement


# Singleton instance
commercial_accounting_service = CommercialAccountingService()
