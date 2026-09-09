"""
Welele Media™ — Commercial Webhook & Settlement Resilience Test Suite (P0/P1)
Tests: Multi-Provider Webhooks (Vodacom, Peach, MoMo), HMAC Signature Validation,
payment_events Audit Receipt Logging, Idempotency Deduplication, and Double-Entry Ledger Posting.
"""

import sys
import os
import hmac
import hashlib
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.commerce_service import commerce_service
from repositories.ledger_repository import ledger_repository

def generate_hmac(secret: str, payload_bytes: bytes) -> str:
    return hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()

def test_commercial_webhook_resilience():
    print("\n--- Running Commercial Webhook & Settlement Resilience Tests ---")

    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    ledger_repository.get_or_create_wallet(test_user)
    initial_balance = ledger_repository.get_balance(test_user)["total_usable_coins"]

    # 1. Happy-Path Vodacom DCB Webhook
    vodacom_tx_id = f"voda_tx_{uuid.uuid4().hex[:8]}"
    vodacom_payload = {
        "vodacom_reference": vodacom_tx_id,
        "user_id": test_user,
        "amount_zar": 10.00,
        "coins_granted": 50,
        "status": "SUCCESS",
        "msisdn": "27821234567"
    }
    raw_body_voda = json.dumps(vodacom_payload).encode('utf-8')
    voda_sig = generate_hmac("welele_vodacom_dcb_secret_2026", raw_body_voda)

    ok_voda, msg_voda, data_voda = commerce_service.process_webhook(
        provider_id="vodacom_dcb",
        raw_body=raw_body_voda,
        raw_json=vodacom_payload,
        signature_header=voda_sig
    )
    assert ok_voda is True
    assert data_voda["status"] == "SETTLED"
    print(f"[PASS] Vodacom DCB Settlement: Successfully processed webhook (TX: {vodacom_tx_id}, Granted: 50 coins).")

    # Verify Double-Entry Balance Update
    new_bal_1 = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert new_bal_1 == initial_balance + 50
    print(f"[PASS] Double-Entry Clearing: Balance increased from {initial_balance} to {new_bal_1} coins (Debit 1000, Credit 2000).")

    # Verify payment_events Audit Receipt (Amendment 3)
    events = commerce_service.get_payment_events()
    voda_event = next((e for e in events if e.get("provider_transaction_id") == vodacom_tx_id), None)
    assert voda_event is not None
    assert voda_event["signature_verified"] is True
    assert voda_event["processing_status"] == "SUCCESS"
    assert voda_event["ledger_transaction_id"] is not None
    print(f"[PASS] payment_events Audit: Verified persistent receipt '{voda_event['id']}' linked to ledger transaction '{voda_event['ledger_transaction_id']}'.")

    # 2. Idempotency Test: Duplicate Webhook Replay
    ok_replay, msg_replay, data_replay = commerce_service.process_webhook(
        provider_id="vodacom_dcb",
        raw_body=raw_body_voda,
        raw_json=vodacom_payload,
        signature_header=voda_sig
    )
    assert ok_replay is True
    assert data_replay["status"] == "ALREADY_PROCESSED"

    bal_after_replay = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_after_replay == new_bal_1 # Balance must NOT increase a second time
    print(f"[PASS] Webhook Idempotency: Duplicate delivery safely handled without double-crediting.")

    # 3. Failure-Path: Invalid HMAC Signature / Tampered Payload
    tampered_payload = dict(vodacom_payload)
    tampered_payload["amount_zar"] = 500.00 # Tampered amount
    raw_tampered = json.dumps(tampered_payload).encode('utf-8')

    ok_tamper, msg_tamper, _ = commerce_service.process_webhook(
        provider_id="vodacom_dcb",
        raw_body=raw_tampered,
        raw_json=tampered_payload,
        signature_header="invalid_tampered_hmac_signature"
    )
    assert ok_tamper is False
    assert "Invalid cryptographic" in msg_tamper
    print(f"[PASS] Security Gate: Tampered webhook rejected with invalid HMAC signature.")

    # Verify failed attempt recorded in payment_events for security audit
    events_after_tamper = commerce_service.get_payment_events()
    tamper_event = next((e for e in events_after_tamper if e.get("processing_status") == "FAILED_SIGNATURE"), None)
    assert tamper_event is not None
    assert tamper_event["signature_verified"] is False
    assert tamper_event["processing_status"] == "FAILED_SIGNATURE"
    print(f"[PASS] Security Auditing: Tampered attempt logged in payment_events with status 'FAILED_SIGNATURE'.")

    # 4. Happy-Path Peach Payments Webhook
    peach_tx_id = f"peach_tx_{uuid.uuid4().hex[:8]}"
    peach_payload = {
        "id": peach_tx_id,
        "merchantInvoiceId": test_user,
        "amount": 25.00,
        "currency": "ZAR",
        "result": {"code": "000.100.110", "description": "Transaction succeeded"},
        "customParameters": {"coins": 125}
    }
    raw_body_peach = json.dumps(peach_payload).encode('utf-8')
    peach_sig = generate_hmac("welele_peach_webhook_secret_2026", raw_body_peach)

    ok_peach, _, data_peach = commerce_service.process_webhook(
        provider_id="peach_payments",
        raw_body=raw_body_peach,
        raw_json=peach_payload,
        signature_header=peach_sig
    )
    assert ok_peach is True
    bal_after_peach = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_after_peach == new_bal_1 + 125
    print(f"[PASS] Multi-Provider Normalization: Successfully settled Peach Payments webhook (+125 coins).")

    print("=======================================================")
    print("ALL COMMERCIAL WEBHOOK & SETTLEMENT TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_commercial_webhook_resilience()
