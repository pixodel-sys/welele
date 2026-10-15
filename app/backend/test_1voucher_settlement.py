"""
Welele Media™ — 1Voucher by FlashPay Settlement & Ledger Resilience Test Suite
Tests Flash Partner API v4 Contract Compliance:
- OAuth 2.0 token management & caching (validity 3600s).
- Endpoint contracts (/aggregation/4.0/1voucher/redeem).
- Parameter contracts (reference, accountNumber, pin, amount in integer cents).
- Full voucher redemption (amount = 0).
- Response code verification (responseCode == 0).
- Documented error codes (2401, 2402, 2405).
- Idempotency via reference reuse on retries/timeouts.
- Double-entry ledger journalizing and keyed HMAC-SHA256 PIN hash uniqueness.
- Production fail-safe guardrail (refusal to silently fall back to mock mode in production).
- PIN confidentiality guard (raw PIN never stored in events, receipts, or logs).

EXECUTION ENVIRONMENT CLARIFICATION:
- Provider Calls: Simulated via Flash Partner API v4 Contract Simulator (Mock Mode: True).
  Live Flash switch network calls are NOT executed because Flash sandbox credentials have not yet been received.
- Database Operations: Executed against the isolated repository test store (ENVIRONMENT=test).
  Staging PostgreSQL database (dbsnaidhznofvyffdfni) remains unwritten.
"""

import os
import sys
import uuid
import random
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure test environment variables are active before backend modules load config.py
os.environ["ENVIRONMENT"] = "test"
os.environ["FLASH_MOCK_MODE"] = "true"
os.environ["FLASH_PIN_HMAC_SECRET"] = "test_fixture_hmac_secret_not_for_prod"

from services.commerce_service import commerce_service
from repositories.ledger_repository import ledger_repository
from services.payment_adapters.onevoucher_adapter import onevoucher_adapter, OneVoucherAdapter, COINS_PER_ZAR


def test_01_oauth2_token_acquisition_and_caching():
    """Verifies Flash v4 OAuth 2.0 Bearer token acquisition and in-memory TTL caching (Section 1.1)."""
    ok_tok, token = onevoucher_adapter.token_manager.get_token()
    assert ok_tok is True, "Token acquisition should succeed"
    assert token is not None and len(token) > 10, "Token should be non-empty string"

    # Second call must return the exact same cached token without re-requesting
    ok_tok2, token2 = onevoucher_adapter.token_manager.get_token()
    assert ok_tok2 is True
    assert token == token2, "Token must be retrieved from cache within TTL window"


def test_02_full_voucher_redemption_amount_zero_and_coin_conversion():
    """Verifies Section 2.3.3.1 full voucher redemption (amount=0) and R1.00 = 5 coins conversion."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    ref = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        phone_number="27821234567",
        idempotency_key=ref
    )

    assert ok is True, f"Redemption failed: {msg}"
    assert data["status"] == "SETTLED"
    assert data["amount_zar"] == 50.0   # Converted from 5000 cents
    assert data["coins_granted"] == 250 # 50 ZAR * 5 coins/ZAR = 250 coins
    assert data["masked_pin"] == "************0050"


def test_03_double_entry_ledger_atomic_journalizing():
    """Verifies atomic double-entry balance incrementation upon successful redemption."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    ledger_repository.get_or_create_wallet(test_user)
    initial_balance = ledger_repository.get_balance(test_user)["total_usable_coins"]

    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    ref = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref
    )
    assert ok is True

    new_balance = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert new_balance == initial_balance + 250, "Wallet must be credited with exactly 250 coins"


def test_04_payment_events_audit_receipt_persistence():
    """Verifies that an immutable receipt is recorded in payment_events linked to the ledger."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    ref = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref
    )
    assert ok is True

    events = commerce_service.get_payment_events()
    event = next((e for e in events if e.get("id") == data["event_id"]), None)
    assert event is not None, "Receipt must exist in payment_events"
    assert event["provider"] == "1voucher_flash"
    assert event["processing_status"] == "SUCCESS"
    assert event["ledger_transaction_id"] == data["ledger_transaction_id"]


def test_05_idempotency_replay_with_same_reference():
    """Verifies Flash v4 Section 1.2.2 retry idempotency: replaying same reference returns ALREADY_PROCESSED."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    ref = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    # First attempt
    ok1, msg1, data1 = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref
    )
    assert ok1 is True
    bal1 = ledger_repository.get_balance(test_user)["total_usable_coins"]

    # Replay with same reference
    ok2, msg2, data2 = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref
    )
    assert ok2 is True
    assert data2["status"] == "ALREADY_PROCESSED"
    assert data2["coins_granted"] == 0, "Duplicate submission must return 0 coins_granted"
    assert data2["coins_credited_now"] == 0, "Duplicate submission must return 0 coins_credited_now"
    assert data2["original_coins_granted"] == 250, "Original grant must be preserved for audit"
    bal2 = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal2 == bal1, "Balance must NOT increase on duplicate reference submission"


def test_06_pin_hmac_uniqueness_guard_duplicate_rejection():
    """Verifies keyed HMAC-SHA256 uniqueness blocks reuse of the same PIN under a different reference."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    ref1 = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"
    ref2 = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    # First redemption succeeds
    ok1, _, _ = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref1
    )
    assert ok1 is True
    bal1 = ledger_repository.get_balance(test_user)["total_usable_coins"]

    # Second redemption with different reference but SAME PIN must be blocked
    ok2, _, data2 = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_r50,
        idempotency_key=ref2
    )
    assert ok2 is True
    assert data2["status"] == "ALREADY_PROCESSED"
    assert data2["coins_granted"] == 0, "Replayed PIN must return 0 coins_granted"
    assert data2["coins_credited_now"] == 0, "Replayed PIN must return 0 coins_credited_now"
    assert data2["original_coins_granted"] == 250
    bal2 = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal2 == bal1, "Balance must NOT increase when PIN has already been settled"


def test_07_flash_error_2401_voucher_already_used():
    """Verifies Flash switch error code 2401 (Voucher Already Used) is properly mapped and logged."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_used = "1111222233339999"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_used,
        idempotency_key=f"WL-FAIL-{uuid.uuid4().hex[:6]}"
    )
    assert ok is False
    assert data.get("responseCode") == 2401
    assert "already been used" in msg


def test_08_flash_error_2402_voucher_not_found():
    """Verifies Flash switch error code 2402 (Voucher Could Not Be Found) is properly mapped."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_not_found = "1111222233338888"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_not_found,
        idempotency_key=f"WL-FAIL-{uuid.uuid4().hex[:6]}"
    )
    assert ok is False
    assert data.get("responseCode") == 2402
    assert "could not be found" in msg


def test_09_flash_error_2405_voucher_expired():
    """Verifies Flash switch error code 2405 (Voucher Expired) is properly mapped."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    pin_expired = "1111222233337777"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_expired,
        idempotency_key=f"WL-FAIL-{uuid.uuid4().hex[:6]}"
    )
    assert ok is False
    assert data.get("responseCode") == 2405
    assert "expired" in msg


def test_10_flash_reference_character_validation():
    """Verifies Section 2.3.3.1 character restrictions ('Only -,.,= and alphanumeric characters allowed')."""
    assert onevoucher_adapter.validate_reference("WL-VALID.2026=123") is True
    assert onevoucher_adapter.validate_reference("INVALID REFERENCE WITH SPACES") is False
    assert onevoucher_adapter.validate_reference("INVALID_SPECIAL_CHARS!@#") is False


def test_11_pin_format_validation_16_digits():
    """Verifies that non-16-digit input is rejected before communicating with switch."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    ok, msg, _ = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin="12345",
        idempotency_key=f"WL-SHORT-{uuid.uuid4().hex[:6]}"
    )
    assert ok is False
    assert "16 numeric digits" in msg


def test_12_production_fail_safe_mock_guard():
    """Verifies that in production mode, missing Flash credentials raises RuntimeError rather than falling back to mock."""
    old_env = os.environ.get("ENVIRONMENT")
    old_acc = os.environ.get("FLASH_ACCOUNT_NUMBER")
    old_cid = os.environ.get("FLASH_CLIENT_ID")
    old_csec = os.environ.get("FLASH_CLIENT_SECRET")

    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ.pop("FLASH_ACCOUNT_NUMBER", None)
        os.environ.pop("FLASH_CLIENT_ID", None)
        os.environ.pop("FLASH_CLIENT_SECRET", None)

        with pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION HALT"):
            OneVoucherAdapter()
    finally:
        if old_env: os.environ["ENVIRONMENT"] = old_env
        else: os.environ["ENVIRONMENT"] = "test"
        if old_acc: os.environ["FLASH_ACCOUNT_NUMBER"] = old_acc
        if old_cid: os.environ["FLASH_CLIENT_ID"] = old_cid
        if old_csec: os.environ["FLASH_CLIENT_SECRET"] = old_csec


def test_13_raw_pin_never_in_audit_or_response():
    """Confirms that the plain-text PIN is NEVER returned in response payloads, event records, or ledger descriptions."""
    test_user = f"viewer_test_{uuid.uuid4().hex[:6]}"
    secret_pin = "1111222233334444"
    ref = f"WL-REF-{uuid.uuid4().hex[:8].upper()}"

    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=secret_pin,
        idempotency_key=ref
    )
    assert ok is True

    # 1. Check returned transaction payload
    data_str = str(data)
    assert secret_pin not in data_str, "Raw PIN must not exist in returned transaction data"
    assert data.get("masked_pin") == "************4444"

    # 2. Check payment_events record
    events = commerce_service.get_payment_events()
    event = next((e for e in events if e.get("id") == data["event_id"]), None)
    assert event is not None
    event_str = str(event)
    assert secret_pin not in event_str, "Raw PIN must not exist in payment_events record"

    # 3. Check coin_ledger description
    ledger = ledger_repository.local_get("coin_ledger")
    entry = next((l for l in ledger if l.get("id") == data["ledger_transaction_id"]), None)
    assert entry is not None
    assert secret_pin not in entry.get("description", ""), "Raw PIN must not exist in ledger description"
    assert "************4444" in entry.get("description", "")


def test_14_api_router_authenticated_endpoint_flow():
    """Verifies the complete FastAPI HTTP /api/payments/1voucher/redeem endpoint with RBAC bearer token and idempotency."""
    from fastapi.testclient import TestClient
    from main import app
    from services.rbac_service import create_access_token

    client = TestClient(app)

    # 1. Issue viewer JWT
    test_viewer = f"viewer_http_{uuid.uuid4().hex[:6]}"
    token = create_access_token(user_id=test_viewer, role="viewer")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Test format rejection via HTTP
    bad_res = client.post("/api/payments/1voucher/redeem", json={"voucher_pin": "1234"}, headers=auth_headers)
    assert bad_res.status_code == 400
    assert "16 numeric digits" in str(bad_res.json())

    # 3. Test successful HTTP redemption
    pin_r50 = f"11112222{random.randint(1000, 9999)}0050"
    client_ref = f"WL-HTTP-{uuid.uuid4().hex[:8].upper()}"
    good_res = client.post(
        "/api/payments/1voucher/redeem",
        json={"voucher_pin": pin_r50, "idempotency_key": client_ref},
        headers=auth_headers
    )
    assert good_res.status_code == 200
    res_data = good_res.json()
    assert res_data["success"] is True
    assert res_data["transaction"]["coins_granted"] == 250
    assert res_data["transaction"]["amount_zar"] == 50.0

    # 4. Test HTTP replay idempotency
    replay_res = client.post(
        "/api/payments/1voucher/redeem",
        json={"voucher_pin": pin_r50, "idempotency_key": client_ref},
        headers=auth_headers
    )
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    assert replay_data["transaction"]["status"] == "ALREADY_PROCESSED"
    assert replay_data["transaction"]["coins_granted"] == 0
    assert replay_data["transaction"]["coins_credited_now"] == 0


def test_15_pin_secret_fail_closed():
    """Verifies that hash_pin fails closed (raises RuntimeError) when HMAC secrets are missing outside test mode."""
    old_env = os.environ.get("ENVIRONMENT")
    old_secret = os.environ.get("FLASH_PIN_HMAC_SECRET")
    old_sec_key = os.environ.get("SECRET_KEY")

    try:
        os.environ["ENVIRONMENT"] = "staging"
        os.environ.pop("FLASH_PIN_HMAC_SECRET", None)
        os.environ.pop("SECRET_KEY", None)

        with pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION HALT"):
            onevoucher_adapter.hash_pin("1111222233334444")
    finally:
        if old_env: os.environ["ENVIRONMENT"] = old_env
        else: os.environ["ENVIRONMENT"] = "test"
        if old_secret: os.environ["FLASH_PIN_HMAC_SECRET"] = old_secret
        if old_sec_key: os.environ["SECRET_KEY"] = old_sec_key


def test_16_mock_mode_prohibited_in_production():
    """Verifies that FLASH_MOCK_MODE=true in production raises RuntimeError."""
    old_env = os.environ.get("ENVIRONMENT")
    old_mock = os.environ.get("FLASH_MOCK_MODE")
    old_acc = os.environ.get("FLASH_ACCOUNT_NUMBER")
    old_cid = os.environ.get("FLASH_CLIENT_ID")
    old_csec = os.environ.get("FLASH_CLIENT_SECRET")

    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["FLASH_ACCOUNT_NUMBER"] = "PROD_ACC_123"
        os.environ["FLASH_CLIENT_ID"] = "PROD_CLIENT_123"
        os.environ["FLASH_CLIENT_SECRET"] = "PROD_SECRET_123"
        os.environ["FLASH_MOCK_MODE"] = "true"

        with pytest.raises(RuntimeError, match="Mock payment simulation in production is strictly prohibited"):
            OneVoucherAdapter()
    finally:
        if old_env: os.environ["ENVIRONMENT"] = old_env
        else: os.environ["ENVIRONMENT"] = "test"
        if old_mock: os.environ["FLASH_MOCK_MODE"] = old_mock
        else: os.environ.pop("FLASH_MOCK_MODE", None)
        if old_acc: os.environ["FLASH_ACCOUNT_NUMBER"] = old_acc
        else: os.environ.pop("FLASH_ACCOUNT_NUMBER", None)
        if old_cid: os.environ["FLASH_CLIENT_ID"] = old_cid
        else: os.environ.pop("FLASH_CLIENT_ID", None)
        if old_csec: os.environ["FLASH_CLIENT_SECRET"] = old_csec
        else: os.environ.pop("FLASH_CLIENT_SECRET", None)
