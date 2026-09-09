"""
Welele Media™ — Commercial Settlement Service (P0/P1)
Orchestrates payment webhooks, provider normalization, cryptographic validation,
payment_events audit persistence, idempotency deduplication, and Double-Entry Ledger journalizing.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.ledger_repository import ledger_repository
from repositories.base_repository import BaseRepository
from services.payment_adapters.base_adapter import BasePaymentAdapter, NormalizedPaymentEvent
from services.payment_adapters.vodacom_dcb_adapter import VodacomDCBAdapter
from services.payment_adapters.peach_payments_adapter import PeachPaymentsAdapter
from services.payment_adapters.mtn_momo_adapter import MTNMomoAdapter

class CommerceService(BaseRepository):
    def __init__(self):
        super().__init__()
        self._adapters: Dict[str, BasePaymentAdapter] = {
            "vodacom_dcb": VodacomDCBAdapter(),
            "peach_payments": PeachPaymentsAdapter(),
            "mtn_momo": MTNMomoAdapter()
        }

    def get_adapter(self, provider_id: str) -> Optional[BasePaymentAdapter]:
        return self._adapters.get(provider_id)

    def process_webhook(
        self,
        provider_id: str,
        raw_body: bytes,
        raw_json: Dict[str, Any],
        signature_header: Optional[str]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Processes an incoming provider webhook through normalization, audit receipt, and double-entry ledger.
        """
        adapter = self.get_adapter(provider_id)
        if not adapter:
            return False, f"Unsupported payment provider '{provider_id}'", {}

        # 1. Signature Verification
        is_verified = adapter.verify_signature(raw_body, signature_header)
        if not is_verified:
            # Still record invalid attempt in payment_events for audit/security inspection
            event_norm = adapter.normalize_payload(raw_json, signature_verified=False)
            self._record_payment_event(event_norm, processing_status="FAILED_SIGNATURE")
            return False, "Invalid cryptographic HMAC webhook signature", {}

        # 2. Normalize Payload
        event = adapter.normalize_payload(raw_json, signature_verified=True)

        # 3. Check Idempotency on provider transaction ID
        idempotency_key = f"pay_{provider_id}_{event.provider_transaction_id}"
        events = self.local_get("payment_events")
        existing_event = next((e for e in events if e.get("idempotency_key") == idempotency_key and e.get("processing_status") == "SUCCESS"), None)
        if existing_event:
            return True, "Idempotent payment already cleared", {
                "event_id": existing_event["id"],
                "status": "ALREADY_PROCESSED",
                "ledger_transaction_id": existing_event.get("ledger_transaction_id")
            }

        # 4. Check if payment failed at provider
        if event.status != "SUCCESS":
            pe = self._record_payment_event(event, processing_status="PROVIDER_FAILED", idempotency_key=idempotency_key)
            return False, f"Provider reported failed transaction: {event.status}", {"event_id": pe["id"]}

        # 5. Double-Entry Accounting Journal Posting
        # Account 1000 (Gateway Clearing Asset) DEBIT
        # Account 2000 (Viewer Coin Liability) CREDIT
        ok, msg, ledger_entry = ledger_repository.credit_coins_atomic(
            user_id=event.user_id,
            base_coins=event.coins_grant,
            bonus_coins=0,
            transaction_type=f"TOPUP_{provider_id.upper()}",
            reference_id=event.provider_transaction_id,
            idempotency_key=idempotency_key,
            description=f"Settled {event.currency} {event.amount_fiat:.2f} via {provider_id}"
        )

        ledger_tx_id = ledger_entry.get("id") if ledger_entry else None

        # 6. Record canonical audit receipt in payment_events (Amendment 3)
        pe = self._record_payment_event(
            event=event,
            processing_status="SUCCESS",
            idempotency_key=idempotency_key,
            ledger_transaction_id=ledger_tx_id
        )

        # 7. If payment target is instant episode unlock, execute unlock
        if event.target_type == "EPISODE_UNLOCK" and event.target_id:
            ledger_repository.unlock_episode_record(
                user_id=event.user_id,
                episode_id=event.target_id,
                story_id=raw_json.get("series_id", "series_unknown"),
                unlock_method=f"DIRECT_{provider_id.upper()}",
                coins_spent=0
            )

        return True, "Payment settled successfully", {
            "event_id": pe["id"],
            "ledger_transaction_id": ledger_tx_id,
            "coins_granted": event.coins_grant,
            "user_id": event.user_id,
            "status": "SETTLED"
        }

    def _record_payment_event(
        self,
        event: NormalizedPaymentEvent,
        processing_status: str,
        idempotency_key: Optional[str] = None,
        ledger_transaction_id: Optional[str] = None
    ) -> Dict[str, Any]:
        pe_record = {
            "id": f"pe_{uuid.uuid4().hex[:10]}",
            "provider": event.provider,
            "provider_transaction_id": event.provider_transaction_id,
            "event_type": event.event_type,
            "user_id": event.user_id,
            "amount_fiat": event.amount_fiat,
            "currency": event.currency,
            "coins_grant": event.coins_grant,
            "signature_verified": event.signature_verified,
            "payload_hash": event.raw_payload_hash,
            "normalized_payload": event.model_dump(),
            "processing_status": processing_status,
            "idempotency_key": idempotency_key,
            "ledger_transaction_id": ledger_transaction_id,
            "received_at": datetime.now(timezone.utc).isoformat()
        }
        self.local_insert("payment_events", pe_record)
        return pe_record

    def get_payment_events(self, limit: int = 50) -> list:
        return self.local_get("payment_events")[:limit]

commerce_service = CommerceService()
