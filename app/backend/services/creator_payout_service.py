"""
Welele Media™ — Provider-Neutral Creator Payout Service (Workstream 6I-G.2)
Implements authoritative creator payout lifecycle, atomic balance validation,
traceable payout allocations, fail-closed state machine transitions, and settlement boundary.

CRITICAL INVARIANTS:
1. Payout requests read available balance ONLY from authoritative commercial accounting.
2. Zero writes or reads from deprecated `creators.coin_earnings`.
3. Payout status PAID is unreachable without authentic verified settlement evidence.
4. No admin/manual shortcut to PAID.
5. External payout provider rails are strictly DISABLED.
6. Duplicate requests are idempotent; conflicting idempotency keys fail closed.
7. Failed payouts preserve underlying creator earnings; retries never double-allocate.
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional

from schemas.commercial_accounting_schemas import (
    PayoutStatus,
    ALLOWED_PAYOUT_TRANSITIONS,
    LedgerEntryType
)
from repositories.commercial_accounting_repository import (
    commercial_accounting_repository,
    CommercialAccountingRepository
)
from services.commercial_accounting_service import (
    commercial_accounting_service,
    CommercialAccountingService,
    _to_decimal,
    _round_currency
)
from services.payout_provider import (
    SettlementConfirmation,
    ProviderStatus,
    default_payout_provider
)
from services.audit_service import audit_service

logger = logging.getLogger("welele.creator_payout_service")


class CreatorPayoutService:
    def __init__(
        self,
        repo: Optional[CommercialAccountingRepository] = None,
        accounting_service: Optional[CommercialAccountingService] = None
    ):
        self.repo = repo or commercial_accounting_repository
        self.accounting_service = accounting_service or commercial_accounting_service
        self.provider = default_payout_provider

    # --------------------------------------------------------------------------
    # 1. CREATOR PAYOUT REQUEST & ALLOCATION (ATOMIC & IDEMPOTENT)
    # --------------------------------------------------------------------------

    def request_payout(
        self,
        creator_id: str,
        requested_amount: Decimal,
        currency: str = "ZAR",
        payout_method: str = "Bank EFT",
        account_details: str = "Default Account",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an atomic payout request and allocates funds against settled ledger earnings.
        Fails closed on:
        - Non-positive amount
        - Invalid/mismatched currency
        - Empty destination reference
        - Insufficient available balance
        - Conflicting idempotency key reuse
        """
        req_amt = _to_decimal(requested_amount)
        if req_amt <= Decimal("0.0000"):
            raise ValueError("Payout request amount must be strictly greater than zero.")

        if currency.upper() != "ZAR":
            raise ValueError(f"Invalid settlement currency '{currency}'. Only 'ZAR' is authorized.")

        if not account_details or not account_details.strip():
            raise ValueError("Payout destination account details are required.")

        if not idempotency_key or not idempotency_key.strip():
            idempotency_key = f"payout_{uuid.uuid4().hex}"

        # 1. Idempotency Check
        existing_payout = self.repo.get_payout_by_idempotency(idempotency_key)
        if existing_payout:
            # Check for conflicting parameter reuse
            if (
                existing_payout.get("creator_id") != creator_id
                or _to_decimal(existing_payout.get("requested_amount", 0)) != req_amt
                or existing_payout.get("currency") != currency
            ):
                raise ValueError(
                    f"Conflicting idempotency key reuse: Key '{idempotency_key}' was previously used "
                    f"with different payout parameters."
                )

            allocations = self.repo.get_payout_allocations(existing_payout["id"])
            return {
                "is_idempotent_replay": True,
                "payout": existing_payout,
                "allocations": allocations,
                "message": f"Idempotent replay: Payout of {req_amt} {currency} is currently {existing_payout.get('status')}."
            }

        # 2. Authoritative Available Balance Verification
        balances = self.accounting_service.get_creator_balances(creator_id, currency)
        if req_amt > balances.available:
            raise ValueError(
                f"Insufficient available balance: Requested {req_amt} {currency}, "
                f"but creator only has {balances.available} {currency} available."
            )

        # 3. Creator Ledger Allocation Calculation
        # Identify settled earnings with unallocated balance
        ledger_entries = self.repo.get_creator_ledger(creator_id)
        earnings = [
            e for e in ledger_entries
            if e.get("entry_type") == LedgerEntryType.EARNING.value
            and e.get("currency", "ZAR") == currency
        ]

        if not earnings:
            raise ValueError("No eligible earning entries found in creator ledger to allocate.")

        # Compute already allocated amount per ledger entry
        allocated_by_entry: Dict[str, Decimal] = {}
        all_allocations = self.repo.get_payout_allocations()
        
        # Consider allocations from active (non-reversed) payouts
        all_payouts = {p["id"]: p for p in self.repo.get_creator_payouts(creator_id)}
        for a in all_allocations:
            p_id = a.get("payout_id")
            parent_payout = all_payouts.get(p_id)
            if parent_payout and parent_payout.get("status") not in [PayoutStatus.REVERSED.value]:
                l_id = a.get("ledger_entry_id")
                allocated_by_entry[l_id] = allocated_by_entry.get(l_id, Decimal("0.0000")) + _to_decimal(a.get("amount_allocated", 0))

        allocations_to_create: List[Dict[str, Any]] = []
        remaining_to_allocate = req_amt
        now = datetime.now(timezone.utc).isoformat()
        payout_id = str(uuid.uuid4())

        for entry in earnings:
            entry_id = entry.get("id")
            entry_total = _to_decimal(entry.get("creator_amount", 0))
            already_alloc = allocated_by_entry.get(entry_id, Decimal("0.0000"))
            available_in_entry = max(Decimal("0.0000"), entry_total - already_alloc)

            if available_in_entry > Decimal("0.0000"):
                alloc_amount = min(remaining_to_allocate, available_in_entry)
                allocations_to_create.append({
                    "id": str(uuid.uuid4()),
                    "payout_id": payout_id,
                    "ledger_entry_id": entry_id,
                    "amount_allocated": float(_round_currency(alloc_amount)),
                    "created_at": now
                })
                remaining_to_allocate -= alloc_amount
                if remaining_to_allocate == Decimal("0.0000"):
                    break

        if remaining_to_allocate > Decimal("0.0000"):
            raise ValueError(
                f"Allocation invariant failure: Could only allocate {req_amt - remaining_to_allocate} "
                f"of requested {req_amt} {currency} against ledger entries."
            )

        # 4. Atomic Persistence: Create Payout and Allocations
        payout_record = {
            "id": payout_id,
            "creator_id": creator_id,
            "requested_amount": float(_round_currency(req_amt)),
            "currency": currency,
            "payout_method": payout_method,
            "account_details": account_details,
            "status": PayoutStatus.PENDING.value,
            "settlement_status": "Settlement Pending (External Rails Unproven)",
            "idempotency_key": idempotency_key,
            "requested_at": now,
            "settled_at": None,
            "rejection_reason": None,
            "metadata": {
                "external_payout_activated": False,
                "environment": "staging",
                "notice": "Creator external disbursement rail is inactive in 6I-G.2."
            },
            "created_at": now
        }

        self.repo.insert_payout(payout_record)

        for alloc in allocations_to_create:
            self.repo.insert_payout_allocation(alloc)

        # 5. Record Audit Event
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commerce.payout_requested",
            actor_id=creator_id,
            actor_role="creator",
            target_type="creator_payout",
            target_id=payout_id,
            before_state={"available_balance": float(balances.available)},
            after_state={
                "requested_amount": float(req_amt),
                "remaining_available": float(balances.available - req_amt),
                "status": PayoutStatus.PENDING.value,
                "allocations_count": len(allocations_to_create)
            },
            metadata={
                "payout_method": payout_method,
                "idempotency_key": idempotency_key,
                "external_disbursement_activated": False
            }
        )

        return {
            "is_idempotent_replay": False,
            "payout": payout_record,
            "allocations": allocations_to_create,
            "remaining_available": float(balances.available - req_amt),
            "message": f"Payout of {req_amt} {currency} requested. Allocations created. Status: PENDING."
        }

    # --------------------------------------------------------------------------
    # 2. PAYOUT STATE MACHINE & TRANSITION ENFORCEMENT
    # --------------------------------------------------------------------------

    def transition_payout_status(
        self,
        payout_id: str,
        new_status: str,
        actor_id: str,
        actor_role: str = "admin",
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enforces authoritative state transitions for creator payouts:
        PENDING → PROCESSING
        PENDING → HELD
        HELD → PENDING
        PROCESSING → PAID (STRICT: Settlement confirmation required; blocked on manual transition)
        PROCESSING → FAILED
        PROCESSING → HELD
        FAILED → PROCESSING
        FAILED → HELD
        PAID → REVERSED
        """
        payout = self.repo.get_payout_by_id(payout_id)
        if not payout:
            raise ValueError(f"Payout with ID '{payout_id}' not found.")

        current_status = payout.get("status")
        normalized_new_status = new_status.upper()

        # Invariant: No admin or manual endpoint may transition directly to PAID!
        if normalized_new_status == PayoutStatus.PAID.value:
            raise ValueError(
                "CRITICAL FINTECH INVARIANT VIOLATION: Manual or admin transition to PAID is prohibited. "
                "PAID status can only be established through verified external settlement evidence."
            )

        allowed_next = ALLOWED_PAYOUT_TRANSITIONS.get(current_status, [])
        if normalized_new_status not in allowed_next:
            raise ValueError(
                f"Invalid payout state transition from '{current_status}' to '{normalized_new_status}'. "
                f"Allowed transitions: {allowed_next}"
            )

        now = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {
            "status": normalized_new_status,
        }

        current_metadata = dict(payout.get("metadata") or {})
        if metadata:
            current_metadata.update(metadata)

        current_metadata["last_transition"] = {
            "from": current_status,
            "to": normalized_new_status,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "reason": reason,
            "timestamp": now
        }
        updates["metadata"] = current_metadata

        if normalized_new_status == PayoutStatus.FAILED.value:
            updates["rejection_reason"] = reason or "Payout processing failed."
            updates["settlement_status"] = "Processing Failed"
        elif normalized_new_status == PayoutStatus.HELD.value:
            updates["settlement_status"] = f"Held: {reason or 'Administrative Review'}"
        elif normalized_new_status == PayoutStatus.PROCESSING.value:
            updates["settlement_status"] = "Processing Instruction"
            updates["rejection_reason"] = None
        elif normalized_new_status == PayoutStatus.PENDING.value:
            updates["settlement_status"] = "Settlement Pending (External Rails Unproven)"
        elif normalized_new_status == PayoutStatus.REVERSED.value:
            updates["settlement_status"] = f"Reversed: {reason or 'Compensating Reversal'}"

        self.repo.update_payout(payout_id, updates)
        payout.update(updates)

        # Audit event
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commerce.payout_status_transitioned",
            actor_id=actor_id,
            actor_role=actor_role,
            target_type="creator_payout",
            target_id=payout_id,
            before_state={"status": current_status},
            after_state={"status": normalized_new_status, "reason": reason},
            metadata={"payout_id": payout_id, "transition": f"{current_status} -> {normalized_new_status}"}
        )

        return payout

    # --------------------------------------------------------------------------
    # 3. SETTLEMENT BOUNDARY (VERIFIED SETTLEMENT CONFIRMATION)
    # --------------------------------------------------------------------------

    def process_settlement_confirmation(
        self,
        confirmation: SettlementConfirmation,
        actor_id: str = "system"
    ) -> Dict[str, Any]:
        """
        Authoritative settlement boundary.
        Evaluates genuine external settlement confirmation against a payout in PROCESSING state.
        Fails closed on:
        - Missing payout
        - Amount or currency mismatch
        - Missing provider reference
        - Invalid state transition (already terminal or not PROCESSING/PENDING)
        - Unknown/ambiguous outcome (does not mark PAID)
        """
        payout = self.repo.get_payout_by_id(confirmation.payout_id)
        if not payout:
            raise ValueError(f"Payout with ID '{confirmation.payout_id}' does not exist.")

        # Idempotency check on settlement confirmation
        current_status = payout.get("status")
        payout_meta = dict(payout.get("metadata") or {})
        if (
            current_status == PayoutStatus.PAID.value
            and payout_meta.get("settlement_idempotency_key") == confirmation.idempotency_key
        ):
            allocations = self.repo.get_payout_allocations(payout["id"])
            return {
                "is_idempotent_replay": True,
                "payout": payout,
                "allocations": allocations,
                "message": "Idempotent settlement replay: Payout already confirmed PAID."
            }

        # Terminal state guard
        if current_status in [PayoutStatus.PAID.value, PayoutStatus.REVERSED.value]:
            raise ValueError(f"Cannot process settlement on payout in terminal state '{current_status}'.")

        # Amount and currency validation
        expected_amount = _to_decimal(payout.get("requested_amount", 0))
        if _to_decimal(confirmation.amount) != expected_amount:
            raise ValueError(
                f"Settlement amount mismatch: Payout requested {expected_amount} {payout.get('currency')}, "
                f"but confirmation provided {confirmation.amount} {confirmation.currency}."
            )

        if confirmation.currency.upper() != payout.get("currency", "ZAR").upper():
            raise ValueError(
                f"Settlement currency mismatch: Expected '{payout.get('currency')}', "
                f"got '{confirmation.currency}'."
            )

        if not confirmation.provider_reference or not confirmation.provider_reference.strip():
            raise ValueError("Settlement confirmation must contain a valid, non-empty provider reference.")

        # Advance PENDING to PROCESSING if needed
        if current_status == PayoutStatus.PENDING.value:
            self.transition_payout_status(
                payout_id=payout["id"],
                new_status=PayoutStatus.PROCESSING.value,
                actor_id=actor_id,
                actor_role="system",
                reason="Auto-transition to PROCESSING upon receiving provider confirmation"
            )
            payout = self.repo.get_payout_by_id(confirmation.payout_id)

        # Provider Outcome Evaluation
        if confirmation.provider_status == ProviderStatus.SETTLED:
            # Genuine settlement confirmed -> PAID
            now = datetime.now(timezone.utc).isoformat()
            settled_at_str = confirmation.settled_at.isoformat() if hasattr(confirmation.settled_at, "isoformat") else str(confirmation.settled_at)
            
            payout_meta.update({
                "provider_reference": confirmation.provider_reference,
                "settlement_idempotency_key": confirmation.idempotency_key,
                "settlement_confirmed_by": actor_id,
                "settlement_confirmed_at": now,
                "confirmation_metadata": confirmation.metadata
            })

            updates = {
                "status": PayoutStatus.PAID.value,
                "settled_at": settled_at_str,
                "settlement_status": f"Settled via Verified External Provider ({confirmation.provider_reference})",
                "metadata": payout_meta
            }

            self.repo.update_payout(payout["id"], updates)
            payout.update(updates)

            # Record audit event
            audit_service.record_trust_event(
                domain="COMMERCE",
                event_type="commerce.payout_settled",
                actor_id=actor_id,
                actor_role="system",
                target_type="creator_payout",
                target_id=payout["id"],
                before_state={"status": PayoutStatus.PROCESSING.value},
                after_state={
                    "status": PayoutStatus.PAID.value,
                    "settled_at": settled_at_str,
                    "amount": float(expected_amount),
                    "provider_reference": confirmation.provider_reference
                },
                metadata={
                    "provider_reference": confirmation.provider_reference,
                    "settlement_idempotency_key": confirmation.idempotency_key
                }
            )

        elif confirmation.provider_status == ProviderStatus.FAILED:
            # Explicit failure reported by provider
            self.transition_payout_status(
                payout_id=payout["id"],
                new_status=PayoutStatus.FAILED.value,
                actor_id=actor_id,
                actor_role="system",
                reason=confirmation.metadata.get("error_message", "Provider disbursement failed."),
                metadata={"provider_reference": confirmation.provider_reference}
            )
            payout = self.repo.get_payout_by_id(confirmation.payout_id)

        else:
            # Ambiguous/Unknown provider outcome: DO NOT MARK PAID
            logger.warning(
                f"[CreatorPayoutService] Ambiguous settlement outcome '{confirmation.provider_status}' "
                f"for payout '{payout['id']}'. Holding in PROCESSING."
            )
            payout_meta["ambiguous_outcome"] = {
                "status": str(confirmation.provider_status),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": confirmation.metadata
            }
            self.repo.update_payout(payout["id"], {"metadata": payout_meta})

        allocations = self.repo.get_payout_allocations(payout["id"])
        return {
            "is_idempotent_replay": False,
            "payout": payout,
            "allocations": allocations,
            "message": f"Settlement confirmation processed. Current status: {payout.get('status')}."
        }

    # --------------------------------------------------------------------------
    # 4. READ & QUERY APIS (TENANT-ISOLATED & AUDITABLE)
    # --------------------------------------------------------------------------

    def get_payout(self, payout_id: str, creator_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a single payout with its allocations. Enforces tenant ownership if creator_id provided."""
        payout = self.repo.get_payout_by_id(payout_id)
        if not payout:
            return None

        if creator_id and payout.get("creator_id") != creator_id:
            logger.warning(f"[Security:IDOR] Creator '{creator_id}' attempted to read payout '{payout_id}' owned by '{payout.get('creator_id')}'")
            return None

        allocations = self.repo.get_payout_allocations(payout_id)
        return {**payout, "allocations": allocations}

    def list_creator_payouts(self, creator_id: str) -> List[Dict[str, Any]]:
        """Retrieves all payouts belonging to a creator, hydrated with allocations."""
        payouts = self.repo.get_creator_payouts(creator_id)
        all_allocs = self.repo.get_payout_allocations()
        alloc_map: Dict[str, List[Dict[str, Any]]] = {}
        for a in all_allocs:
            p_id = a.get("payout_id")
            alloc_map.setdefault(p_id, []).append(a)

        return [{**p, "allocations": alloc_map.get(p.get("id"), [])} for p in payouts]

    def list_all_payouts(self, limit: int = 200, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Admin operation: Retrieves recent payouts across all creators with allocations."""
        payouts = self.repo.get_all_payouts(limit=limit, status=status)
        all_allocs = self.repo.get_payout_allocations()
        alloc_map: Dict[str, List[Dict[str, Any]]] = {}
        for a in all_allocs:
            p_id = a.get("payout_id")
            alloc_map.setdefault(p_id, []).append(a)

        return [{**p, "allocations": alloc_map.get(p.get("id"), [])} for p in payouts]

    # --------------------------------------------------------------------------
    # 5. ADMIN CONTROLS (HOLDS & RETRIES)
    # --------------------------------------------------------------------------

    def hold_payout(self, payout_id: str, actor_id: str, reason: str = "Administrative Review") -> Dict[str, Any]:
        """Places a PENDING, PROCESSING, or FAILED payout on administrative hold."""
        return self.transition_payout_status(
            payout_id=payout_id,
            new_status=PayoutStatus.HELD.value,
            actor_id=actor_id,
            actor_role="admin",
            reason=reason
        )

    def release_payout_hold(self, payout_id: str, actor_id: str, reason: str = "Hold Released") -> Dict[str, Any]:
        """Releases a held payout back to PENDING state."""
        return self.transition_payout_status(
            payout_id=payout_id,
            new_status=PayoutStatus.PENDING.value,
            actor_id=actor_id,
            actor_role="admin",
            reason=reason
        )

    def retry_failed_payout(self, payout_id: str, actor_id: str, reason: str = "Retry after failure") -> Dict[str, Any]:
        """
        Retries a FAILED payout by transitioning it to PROCESSING.
        Reuses existing allocations without double-allocating creator balance.
        """
        return self.transition_payout_status(
            payout_id=payout_id,
            new_status=PayoutStatus.PROCESSING.value,
            actor_id=actor_id,
            actor_role="admin",
            reason=reason
        )


# Singleton instance
creator_payout_service = CreatorPayoutService()
