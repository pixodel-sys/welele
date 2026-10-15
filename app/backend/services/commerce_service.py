"""
Welele Media™ — Commercial Settlement Service (P0/P1)
Orchestrates payment webhooks, provider normalization, cryptographic validation,
payment_events audit persistence, idempotency deduplication, and Double-Entry Ledger journalizing.
"""

import os
import sys
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("welele.commerce")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.ledger_repository import ledger_repository
from repositories.base_repository import BaseRepository
from services.payment_adapters.base_adapter import BasePaymentAdapter, NormalizedPaymentEvent
from services.payment_adapters.vodacom_dcb_adapter import VodacomDCBAdapter
from services.payment_adapters.peach_payments_adapter import PeachPaymentsAdapter
from services.payment_adapters.mtn_momo_adapter import MTNMomoAdapter
from services.payment_adapters.onevoucher_adapter import OneVoucherAdapter, onevoucher_adapter

class CommerceService(BaseRepository):
    def __init__(self):
        super().__init__()
        self._adapters: Dict[str, BasePaymentAdapter] = {
            "vodacom_dcb": VodacomDCBAdapter(),
            "peach_payments": PeachPaymentsAdapter(),
            "mtn_momo": MTNMomoAdapter(),
            "1voucher": onevoucher_adapter,
            "1voucher_flash": onevoucher_adapter,
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

        from services.audit_service import audit_service
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commerce.payment_received",
            actor_id=event.user_id,
            actor_role="viewer",
            target_type="wallet",
            target_id=event.user_id,
            after_state={"coins_granted": event.coins_grant, "amount_fiat": event.amount_fiat, "currency": event.currency},
            metadata={"provider": provider_id, "provider_tx": event.provider_transaction_id, "ledger_tx": ledger_tx_id}
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
        ledger_transaction_id: Optional[str] = None,
        pin_hash: Optional[str] = None
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
            "pin_hash": pin_hash,
            "normalized_payload": event.model_dump(),
            "processing_status": processing_status,
            "idempotency_key": idempotency_key,
            "ledger_transaction_id": ledger_transaction_id,
            "received_at": datetime.now(timezone.utc).isoformat()
        }
        self.local_insert("payment_events", pe_record)
        if self.is_live:
            try:
                self.get_table("payment_events").insert(pe_record).execute()
            except Exception as e:
                if "pin_hash" in str(e).lower():
                    logger.warning(f"[CommerceService:DB] payment_events remote insert error (retrying without pin_hash): {e}")
                    pe_compat = dict(pe_record)
                    pe_compat.pop("pin_hash", None)
                    try:
                        self.get_table("payment_events").insert(pe_compat).execute()
                    except Exception as e2:
                        logger.warning(f"[CommerceService:DB] payment_events remote retry error: {e2}")
                else:
                    logger.warning(f"[CommerceService:DB] payment_events remote insert error: {e}")
        return pe_record

    def _update_payment_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        updated = self.local_update("payment_events", "id", event_id, updates)
        if self.is_live:
            try:
                self.get_table("payment_events").update(updates).eq("id", event_id).execute()
            except Exception as e:
                logger.warning(f"[CommerceService:DB] payment_events remote update error: {e}")
        return updated

    def get_payment_events(self, limit: int = 50) -> list:
        if self.is_live:
            try:
                res = self.get_table("payment_events").select("*").order("received_at", desc=True).limit(limit).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommerceService:DB] get_payment_events remote error: {e}")
        return self.local_get("payment_events")[:limit]

    def _recover_uncredited_voucher(
        self,
        event_dict: Dict[str, Any],
        user_id: str,
        cleaned_pin: str,
        adapter: OneVoucherAdapter
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Safely recovers and credits coins for a voucher that succeeded at Flash
        but previously failed before ledger journalizing, without re-calling Flash switch.
        """
        coins_to_grant = int(event_dict.get("coins_grant") or 0)
        amount_fiat = float(event_dict.get("amount_fiat") or 0.0)
        ref_id = event_dict.get("provider_transaction_id") or event_dict.get("idempotency_key")
        masked_pin = adapter.mask_pin(cleaned_pin)

        ok_ledger, msg_ledger, ledger_entry = ledger_repository.credit_coins_atomic(
            user_id=user_id,
            base_coins=coins_to_grant,
            bonus_coins=0,
            transaction_type="TOPUP_1VOUCHER",
            reference_id=ref_id,
            idempotency_key=f"recov_{event_dict.get('idempotency_key')}",
            description=f"Recovered 1Voucher {masked_pin} for R{amount_fiat:.2f}"
        )
        if not ok_ledger or not ledger_entry:
            return False, f"Reconciliation retry failed to credit wallet: {msg_ledger}", {
                "event_id": event_dict["id"],
                "status": "NEEDS_RECONCILIATION"
            }

        ledger_tx_id = ledger_entry.get("id")
        self._update_payment_event(event_dict["id"], {
            "processing_status": "SUCCESS",
            "ledger_transaction_id": ledger_tx_id
        })

        from services.audit_service import audit_service
        audit_service.record_trust_event(
            domain="COMMERCE",
            event_type="commerce.1voucher_reconciled",
            actor_id=user_id,
            actor_role="viewer",
            target_type="wallet",
            target_id=user_id,
            after_state={"coins_granted": coins_to_grant, "amount_fiat": amount_fiat},
            metadata={"provider": "1voucher_flash", "recovered_from_event": event_dict["id"], "ledger_tx": ledger_tx_id}
        )

        return True, "1Voucher recovered and credited successfully", {
            "event_id": event_dict["id"],
            "ledger_transaction_id": ledger_tx_id,
            "coins_granted": coins_to_grant,
            "coins_credited_now": coins_to_grant,
            "original_coins_granted": coins_to_grant,
            "amount_zar": amount_fiat,
            "masked_pin": masked_pin,
            "reference": ref_id,
            "user_id": user_id,
            "status": "SETTLED"
        }

    def redeem_1voucher(
        self,
        user_id: str,
        voucher_pin: str,
        phone_number: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Synchronously redeems 1Voucher PIN against Flash switch, enforces idempotency,
        records payment_events receipt, and journals coins into double-entry ledger.
        Safely recovers from partial failure without duplicate credit or double switch calls.
        """
        adapter = self._adapters.get("1voucher_flash")
        if not adapter or not isinstance(adapter, OneVoucherAdapter):
            adapter = onevoucher_adapter

        cleaned_pin = adapter.clean_pin(voucher_pin)
        pin_hash = adapter.hash_pin(cleaned_pin)
        idemp = idempotency_key or f"1v_idemp_{uuid.uuid4().hex[:12]}"

        with self._lock:
            # 1. Idempotency & Reconciliation Check (Remote Database & Local Store)
            if self.is_live:
                try:
                    res = self.get_table("payment_events").select("*").or_(
                        f"idempotency_key.eq.{idemp},pin_hash.eq.{pin_hash}"
                    ).execute()
                    if res and res.data:
                        for ev in res.data:
                            # CRITICAL CROSS-USER CHECK: An idempotency key or voucher hash cannot be claimed by another user
                            if ev.get("user_id") and ev.get("user_id") != user_id:
                                logger.error(f"[CommerceService:SECURITY] Cross-user redemption collision on event {ev.get('id')}")
                                return False, "Voucher PIN or reference is already registered to a different account", {
                                    "status": "FORBIDDEN_CROSS_USER",
                                    "error_code": "IDEMPOTENCY_CROSS_USER_COLLISION"
                                }
                            if ev.get("processing_status") == "SUCCESS":
                                return True, "1Voucher already cleared successfully", {
                                    "event_id": ev["id"],
                                    "status": "ALREADY_PROCESSED",
                                    "ledger_transaction_id": ev.get("ledger_transaction_id"),
                                    "coins_granted": 0,
                                    "coins_credited_now": 0,
                                    "original_coins_granted": ev.get("coins_grant", 0),
                                    "amount_zar": float(ev.get("amount_fiat") or 0.0),
                                    "reference": ev.get("provider_transaction_id") or idemp
                                }
                            elif ev.get("processing_status") == "NEEDS_RECONCILIATION":
                                return self._recover_uncredited_voucher(ev, user_id, cleaned_pin, adapter)
                except Exception as e:
                    logger.warning(f"[CommerceService:DB] Remote idempotency check error: {e}")

            events = self.local_get("payment_events") or []
            for e in events:
                if (e.get("idempotency_key") == idemp or (pin_hash and e.get("pin_hash") == pin_hash)):
                    # CRITICAL CROSS-USER CHECK (Local):
                    if e.get("user_id") and e.get("user_id") != user_id:
                        return False, "Voucher PIN or reference is already registered to a different account", {
                            "status": "FORBIDDEN_CROSS_USER",
                            "error_code": "IDEMPOTENCY_CROSS_USER_COLLISION"
                        }
                    if e.get("processing_status") == "SUCCESS":
                        return True, "1Voucher already cleared successfully", {
                            "event_id": e["id"],
                            "status": "ALREADY_PROCESSED",
                            "ledger_transaction_id": e.get("ledger_transaction_id"),
                            "coins_granted": 0,
                            "coins_credited_now": 0,
                            "original_coins_granted": e.get("coins_grant", 0),
                            "amount_zar": float(e.get("amount_fiat") or 0.0),
                            "reference": e.get("provider_transaction_id") or idemp
                        }
                    elif e.get("processing_status") == "NEEDS_RECONCILIATION":
                        return self._recover_uncredited_voucher(e, user_id, cleaned_pin, adapter)

            # 2. Record in-flight INITIATED event before provider call
            initiated_pe = {
                "id": f"pe_{uuid.uuid4().hex[:10]}",
                "provider": "1voucher_flash",
                "provider_transaction_id": None,
                "event_type": "voucher.redemption.initiated",
                "user_id": user_id,
                "amount_fiat": 0.0,
                "currency": "ZAR",
                "coins_grant": 0,
                "signature_verified": True,
                "payload_hash": pin_hash,
                "pin_hash": pin_hash,
                "normalized_payload": {"reference": idemp, "user_id": user_id, "masked_pin": adapter.mask_pin(cleaned_pin)},
                "processing_status": "INITIATED",
                "idempotency_key": idemp,
                "ledger_transaction_id": None,
                "received_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("payment_events", initiated_pe)
            if self.is_live:
                try:
                    self.get_table("payment_events").insert(initiated_pe).execute()
                except Exception as e:
                    logger.critical(f"[CommerceService:FAIL_CLOSED] Failed to durably record initiated payment event: {e}")
                    # CRITICAL FINTECH INVARIANT: If the database receipt cannot be durably established BEFORE calling
                    # the external provider, redemption MUST FAIL CLOSED to prevent un-reconcilable money movement.
                    self.local_delete("payment_events", "id", initiated_pe["id"])
                    return False, "Database error: Unable to record transaction receipt before provider redemption", {
                        "status": "FAILED_PRE_RECORD",
                        "error": str(e)
                    }

            # 3. Execute redemption against Flash switch / sandbox simulator
            ok, msg, tx_data = adapter.execute_redemption(
                voucher_pin=cleaned_pin,
                user_id=user_id,
                phone_number=phone_number,
                reference=idemp
            )

            if not ok:
                norm_event = adapter.normalize_payload(tx_data, signature_verified=True)
                norm_event.user_id = user_id
                self._update_payment_event(initiated_pe["id"], {
                    "processing_status": "PROVIDER_DECLINED",
                    "normalized_payload": norm_event.model_dump(),
                    "provider_transaction_id": norm_event.provider_transaction_id
                })
                return False, msg, tx_data

            # 4. Normalize successful event
            event = adapter.normalize_payload(tx_data, signature_verified=True)
            event.user_id = user_id

            # 5. Double-Entry Accounting Journal Posting
            try:
                ok_ledger, msg_ledger, ledger_entry = ledger_repository.credit_coins_atomic(
                    user_id=user_id,
                    base_coins=event.coins_grant,
                    bonus_coins=0,
                    transaction_type="TOPUP_1VOUCHER",
                    reference_id=event.provider_transaction_id,
                    idempotency_key=idemp,
                    description=f"Redeemed 1Voucher {tx_data.get('masked_pin', '')} for R{event.amount_fiat:.2f}"
                )
            except Exception as e:
                ok_ledger = False
                msg_ledger = str(e)
                ledger_entry = None

            if not ok_ledger or not ledger_entry:
                logger.critical(
                    f"[CommerceService:CRITICAL] Flash redemption succeeded for voucher {tx_data.get('masked_pin')}, "
                    f"but ledger crediting failed: {msg_ledger}. Flagging event {initiated_pe['id']} for reconciliation."
                )
                self._update_payment_event(initiated_pe["id"], {
                    "provider_transaction_id": event.provider_transaction_id,
                    "amount_fiat": event.amount_fiat,
                    "coins_grant": event.coins_grant,
                    "normalized_payload": event.model_dump(),
                    "processing_status": "NEEDS_RECONCILIATION"
                })
                return False, "1Voucher redeemed successfully at provider, but wallet crediting encountered an error. Queued for automatic reconciliation.", {
                    "event_id": initiated_pe["id"],
                    "status": "NEEDS_RECONCILIATION",
                    "reference": event.provider_transaction_id,
                    "amount_zar": event.amount_fiat,
                    "coins_grant": event.coins_grant,
                    "masked_pin": tx_data.get("masked_pin")
                }

            if msg_ledger == "Idempotent credit already processed":
                return True, "1Voucher already cleared successfully", {
                    "event_id": initiated_pe["id"],
                    "status": "ALREADY_PROCESSED",
                    "ledger_transaction_id": ledger_entry.get("id"),
                    "coins_granted": 0,
                    "coins_credited_now": 0,
                    "original_coins_granted": event.coins_grant,
                    "amount_zar": event.amount_fiat,
                    "reference": event.provider_transaction_id or idemp
                }

            ledger_tx_id = ledger_entry.get("id")

            # 6. Record canonical audit receipt in payment_events
            self._update_payment_event(initiated_pe["id"], {
                "provider_transaction_id": event.provider_transaction_id,
                "amount_fiat": event.amount_fiat,
                "coins_grant": event.coins_grant,
                "normalized_payload": event.model_dump(),
                "processing_status": "SUCCESS",
                "ledger_transaction_id": ledger_tx_id
            })

            from services.audit_service import audit_service
            audit_service.record_trust_event(
                domain="COMMERCE",
                event_type="commerce.1voucher_redeemed",
                actor_id=user_id,
                actor_role="viewer",
                target_type="wallet",
                target_id=user_id,
                after_state={"coins_granted": event.coins_grant, "amount_fiat": event.amount_fiat, "currency": event.currency},
                metadata={"provider": "1voucher_flash", "masked_pin": tx_data.get("masked_pin"), "provider_tx": event.provider_transaction_id, "ledger_tx": ledger_tx_id}
            )

            return True, msg, {
                "event_id": initiated_pe["id"],
                "ledger_transaction_id": ledger_tx_id,
                "coins_granted": event.coins_grant,
                "coins_credited_now": event.coins_grant,
                "original_coins_granted": event.coins_grant,
                "amount_zar": event.amount_fiat,
                "masked_pin": tx_data.get("masked_pin"),
                "reference": event.provider_transaction_id,
                "user_id": user_id,
                "status": "SETTLED"
            }

commerce_service = CommerceService()

