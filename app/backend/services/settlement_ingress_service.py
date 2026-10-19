"""
Welele Media™ — Authoritative Settlement Ingress Service (Phase 6O-4)
Enforces the strict, non-negotiable boundary between external payment gateways
and the protected 6I Commercial Accounting Engine.

Governing Principles (Accepted 6O Revised & 6O.1 Corrections):
1. External settlement reference must be non-null and idempotent.
2. Valid environment-appropriate settlement proof must be cryptographically verified.
3. Settlement status must be terminal 'SETTLED'.
4. is_simulation must be False.
5. Ingress caller must be an authorized gateway or certified test fixture.
6. Environment != settlement authenticity. Staging does not make an event authoritative.
7. Mock or simulated drivers can NEVER invoke authoritative 6I accounting.
"""

import hmac
import hashlib
import uuid
import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from config import settings
from schemas.commercial_accounting_schemas import RevenueEventSource, RevenueEventType
from services.commercial_accounting_service import commercial_accounting_service
from services.audit_service import audit_service

class SettlementIngressError(ValueError):
    """Raised when an ingress payload fails authoritative settlement criteria."""
    pass

class SettlementIngressService:
    AUTHORITATIVE_CALLERS = {"gateway_telco_dcb", "gateway_card_paystack", "gateway_eft_ozow", "gateway_1voucher", "test_harness_authoritative"}

    @staticmethod
    def verify_settlement_proof(gateway: str, external_ref: str, proof_signature: Optional[str], amount: Decimal) -> bool:
        """
        Cryptographically verifies the gateway settlement proof appropriate to the environment.
        Uses HMAC-SHA256 signature verification over external_ref and amount against the gateway secret.
        """
        if not proof_signature:
            return False

        secret = getattr(settings, "PAYMENT_GATEWAY_WEBHOOK_SECRET", None) or getattr(settings, "JWT_SECRET", "welele_settlement_key_authoritative")
        expected_payload = f"{gateway}:{external_ref}:{amount:.2f}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), expected_payload, hashlib.sha256).hexdigest()

        return hmac.compare_digest(proof_signature, expected_sig)

    @classmethod
    def generate_settlement_proof(cls, gateway: str, external_ref: str, amount: Decimal) -> str:
        """Generates an authentic settlement proof signature for certified gateway webhooks."""
        secret = getattr(settings, "PAYMENT_GATEWAY_WEBHOOK_SECRET", None) or getattr(settings, "JWT_SECRET", "welele_settlement_key_authoritative")
        payload = f"{gateway}:{external_ref}:{amount:.2f}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def process_authoritative_settlement(
        self,
        caller_service_id: str,
        series_id: str,
        episode_id: Optional[str],
        source: RevenueEventSource,
        external_settlement_ref: str,
        settlement_status: str,
        is_simulation: bool,
        gross_amount: Decimal,
        currency: str = "ZAR",
        settlement_proof: Optional[str] = None,
        gateway_name: str = "telco_dcb",
        occurred_at: Optional[datetime.datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates the 5 mandatory settlement invariants before submitting to 6I accounting.
        Fails closed with SettlementIngressError on any invariant violation.
        """
        # Invariant 5: Authorized Ingress Caller
        if caller_service_id not in self.AUTHORITATIVE_CALLERS:
            audit_service.record_trust_event(
                domain="COMMERCE",
                event_type="commerce.settlement_rejected",
                actor_id=caller_service_id,
                actor_role="unauthorized_caller",
                target_type="settlement_ingress",
                target_id=external_settlement_ref or "none",
                metadata={"reason": "Unauthorized caller service attempted 6I accounting ingress"}
            )
            raise SettlementIngressError(f"Caller '{caller_service_id}' is not an authorized settlement ingress caller.")

        # Invariant 1: Valid External Settlement Reference
        if not external_settlement_ref or not str(external_settlement_ref).strip():
            raise SettlementIngressError("External settlement reference is required, non-null, and cannot be empty.")

        # Invariant 4: is_simulation MUST be False
        if is_simulation is not False:
            raise SettlementIngressError("Simulated or mock transactions cannot enter authoritative 6I accounting (is_simulation must be False).")

        # Invariant 3: Settlement Status MUST be SETTLED
        if str(settlement_status).upper() != "SETTLED":
            raise SettlementIngressError(f"Settlement status must be 'SETTLED', got '{settlement_status}'.")

        # Invariant 6 & 2: Environment != Authenticity; Cryptographic Settlement Proof Required
        # Controlled test fixtures in test mode can supply certified test signatures
        if not self.verify_settlement_proof(gateway_name, external_settlement_ref, settlement_proof, gross_amount):
            raise SettlementIngressError("Invalid or missing cryptographic settlement proof for gateway transaction.")

        # Invariant 1 (Cont): Idempotency check via external_settlement_ref
        idempotency_key = f"settlement_{gateway_name}_{external_settlement_ref}"
        
        event_metadata = dict(metadata or {})
        event_metadata.update({
            "external_settlement_ref": external_settlement_ref,
            "settlement_status": "SETTLED",
            "is_simulation": False,
            "settlement_proof_verified": True,
            "gateway": gateway_name,
            "ingress_caller": caller_service_id
        })

        # Submit to Protected 6I Accounting Engine
        accounting_result = commercial_accounting_service.process_commercial_event(
            series_id=series_id,
            episode_id=episode_id,
            source=source,
            source_transaction_id=external_settlement_ref,
            event_type=RevenueEventType.AIRTIME_CHARGE if source == RevenueEventSource.AIRTIME_UNLOCK else RevenueEventType.ORDER_FULFILLED,
            gross_amount=gross_amount,
            currency=currency,
            occurred_at=occurred_at,
            idempotency_key=idempotency_key,
            metadata=event_metadata
        )

        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commerce.settlement_ingressed",
            actor_id=caller_service_id,
            actor_role="authoritative_gateway",
            target_type="6i_commercial_accounting",
            target_id=external_settlement_ref,
            after_state={"status": "INGRESSED_INTO_6I", "gross_amount": float(gross_amount), "currency": currency},
            metadata=event_metadata
        )

        return {
            "status": "SETTLED_INGRESSED",
            "external_settlement_ref": external_settlement_ref,
            "is_simulation": False,
            "settlement_verified": True,
            "accounting_result": accounting_result
        }

settlement_ingress_service = SettlementIngressService()
