"""
Welele Media™ — MTN MoMo (Mobile Money) USSD Push Adapter
Normalizes MTN MoMo push callbacks and validates HMAC signatures.
"""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from .base_adapter import BasePaymentAdapter, NormalizedPaymentEvent

class MTNMomoAdapter(BasePaymentAdapter):
    SECRET_KEY = "welele_mtn_momo_secret_2026"

    @property
    def provider_id(self) -> str:
        return "mtn_momo"

    def verify_signature(self, payload: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header:
            return False
        expected = hmac.new(self.SECRET_KEY.encode('utf-8'), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header)

    def normalize_payload(self, raw_data: Dict[str, Any], signature_verified: bool) -> NormalizedPaymentEvent:
        raw_json = json.dumps(raw_data, sort_keys=True, separators=(',', ':'))
        raw_hash = hashlib.sha256(raw_json.encode('utf-8')).hexdigest()

        tx_id = raw_data.get("financialTransactionId") or raw_data.get("externalId") or raw_data.get("reference", "momo_tx")
        status_raw = raw_data.get("status", "SUCCESSFUL").upper()
        status = "SUCCESS" if status_raw in ["SUCCESSFUL", "SUCCESS", "COMPLETED"] else "FAILED"

        amount = float(raw_data.get("amount", 0.0))
        currency = raw_data.get("currency", "ZAR")
        user_id = raw_data.get("payer", {}).get("partyId", raw_data.get("user_id", "guest_user")) if isinstance(raw_data.get("payer"), dict) else raw_data.get("user_id", "guest_user")
        coins = int(raw_data.get("coins_grant", int(amount * 5)))

        return NormalizedPaymentEvent(
            provider=self.provider_id,
            provider_transaction_id=tx_id,
            event_type="MOMO_USSD_PUSH",
            amount_fiat=amount,
            currency=currency,
            user_id=user_id,
            coins_grant=coins,
            target_id=raw_data.get("target_id"),
            target_type=raw_data.get("target_type", "COINS"),
            raw_payload_hash=raw_hash,
            signature_verified=signature_verified,
            status=status
        )
