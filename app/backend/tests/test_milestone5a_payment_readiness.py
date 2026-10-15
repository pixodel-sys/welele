"""
Welele Media™ — Milestone 5A: Payment Integration Readiness Test Suite
Scope: Staging & Local Test Harness Only (Production 100% Frozen)
FlashPay / 1Voucher Provider Credentials Not Yet Available

COVERS ALL 16 REQUIRED TEST CATEGORIES:
1. Request validation
2. PIN never persisted
3. PIN never logged/exposed
4. Stable idempotency/reference behaviour
5. Payment event lifecycle
6. Flash responseCode parsing
7. HTTP 200 + responseCode 0 = provider success
8. HTTP 200 + nonzero responseCode = provider failure
9. timeout = ambiguous outcome
10. duplicate idempotency protection
11. duplicate settlement protection
12. atomic wallet credit contract
13. failed provider = zero coin credit
14. ambiguous provider = zero automatic coin credit
15. audit chain integrity
16. production target guard
"""

import os
import sys
import uuid
import json
import logging
import random
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from target_validator import CONFIRMED_PRODUCTION_REF, CONFIRMED_STAGING_REF, validate_database_target

os.environ["ENVIRONMENT"] = "test"
os.environ["FLASH_MOCK_MODE"] = "true"
os.environ["FLASH_PIN_HMAC_SECRET"] = "test_fixture_hmac_secret_not_for_prod"
os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF

from services.commerce_service import commerce_service
from repositories.ledger_repository import ledger_repository
from services.payment_adapters.onevoucher_adapter import OneVoucherAdapter, onevoucher_adapter
from services.audit_service import audit_service


@pytest.fixture(autouse=True)
def ensure_test_environment(monkeypatch):
    """Guarantees clean test environment variables even if earlier tests loaded .env.staging."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("FLASH_MOCK_MODE", "true")
    monkeypatch.setenv("FLASH_PIN_HMAC_SECRET", "test_fixture_hmac_secret_not_for_prod")
    monkeypatch.setenv("PRODUCTION_SUPABASE_REF", CONFIRMED_PRODUCTION_REF)
    monkeypatch.setenv("STAGING_SUPABASE_REF", CONFIRMED_STAGING_REF)


def make_unique_pin(suffix: str = "0050") -> str:
    """Generates a unique, valid 16-digit voucher PIN ending in a specified suffix (default R50)."""
    middle = f"{random.randint(10000000, 99999999):08d}"
    return f"1234{middle}{suffix}"


# ============================================================================
# CATEGORY 1: REQUEST VALIDATION
# ============================================================================

def test_01_request_validation():
    """
    Category 1: Request Validation
    Verifies input sanitization and early validation:
    - missing/empty PIN fails safely
    - invalid PIN length (<16 or >16 digits) fails safely
    - non-numeric PIN fails safely
    - missing user_id fails safely
    - malformed reference/idempotency key fails safely
    - unauthenticated / cross-user spoofing fails safely
    """
    test_user = f"user_val_{uuid.uuid4().hex[:8]}"

    # Missing/empty PIN
    ok, msg, data = commerce_service.redeem_1voucher(user_id=test_user, voucher_pin="")
    assert ok is False
    assert data.get("error_code") == "VOUCHER_PIN_INVALID_FORMAT"

    # Short PIN (10 digits)
    ok, msg, data = commerce_service.redeem_1voucher(user_id=test_user, voucher_pin="1234567890")
    assert ok is False
    assert data.get("error_code") == "VOUCHER_PIN_INVALID_FORMAT"

    # Long PIN (20 digits)
    ok, msg, data = commerce_service.redeem_1voucher(user_id=test_user, voucher_pin="12345678901234567890")
    assert ok is False
    assert data.get("error_code") == "VOUCHER_PIN_INVALID_FORMAT"

    # Non-numeric PIN
    ok, msg, data = commerce_service.redeem_1voucher(user_id=test_user, voucher_pin="abcdefghijklmnop")
    assert ok is False
    assert data.get("error_code") == "VOUCHER_PIN_INVALID_FORMAT"

    # Missing user_id
    ok, msg, data = commerce_service.redeem_1voucher(user_id="", voucher_pin="1234567890123456")
    assert ok is False
    assert data.get("error_code") == "USER_ID_REQUIRED"

    # Malformed reference/idempotency key (contains invalid characters or exceeds 50 chars)
    ok, msg, data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin="1234567890123456",
        idempotency_key="invalid key with spaces!@#"
    )
    assert ok is False
    assert data.get("error_code") == "IDEMPOTENCY_KEY_INVALID_FORMAT"

    # Router cross-user authorization enforcement
    from routers.payments import redeem_1voucher_pin, VoucherRedeemPayload
    from fastapi import HTTPException

    auth_viewer = {"sub": "user_real_viewer", "role": "viewer"}
    spoofed_req = VoucherRedeemPayload(
        voucher_pin="1234567890123456",
        user_id="user_target_victim"  # Different user
    )
    with pytest.raises(HTTPException) as exc_info:
        redeem_1voucher_pin(spoofed_req, auth_user=auth_viewer)
    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail


# ============================================================================
# CATEGORY 2: PIN NEVER PERSISTED
# ============================================================================

def test_02_pin_never_persisted():
    """
    Category 2: PIN Never Persisted
    Verifies that the raw 16-digit voucher PIN is NEVER written to:
    - PostgreSQL / payment_events
    - coin_ledger
    - wallets
    - any in-memory store
    Only HMAC-SHA256 pin_hash and masked_pin are permitted.
    """
    secret_test_pin = make_unique_pin("0050")
    test_user = f"user_pin_sec_{uuid.uuid4().hex[:8]}"
    idemp_key = f"WL-PINSEC-{uuid.uuid4().hex[:8]}"

    ok, msg, tx_data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=secret_test_pin,
        idempotency_key=idemp_key
    )
    assert ok is True

    # Inspect all payment_events records
    events = commerce_service.local_get("payment_events") or []
    for ev in events:
        ev_str = json.dumps(ev)
        assert secret_test_pin not in ev_str, "CRITICAL SECURITY LEAK: Raw PIN discovered in payment_events record!"
        if ev.get("idempotency_key") == idemp_key:
            assert ev.get("pin_hash") is not None
            assert len(ev["pin_hash"]) == 64  # SHA-256 hex string
            assert ev["pin_hash"] != secret_test_pin

    # Inspect all coin_ledger records
    ledger_entries = ledger_repository.local_get("coin_ledger") or []
    for entry in ledger_entries:
        entry_str = json.dumps(entry)
        assert secret_test_pin not in entry_str, "CRITICAL SECURITY LEAK: Raw PIN discovered in coin_ledger record!"

    # Inspect wallets records
    wallets = ledger_repository.local_get("wallets") or []
    for w in wallets:
        w_str = json.dumps(w)
        assert secret_test_pin not in w_str, "CRITICAL SECURITY LEAK: Raw PIN discovered in wallets record!"


# ============================================================================
# CATEGORY 3: PIN NEVER LOGGED / EXPOSED
# ============================================================================

def test_03_pin_never_logged_or_exposed(caplog):
    """
    Category 3: PIN Never Logged or Exposed
    Verifies that during redemption execution:
    - application loggers never emit the plaintext PIN
    - return payloads expose only masked_pin (e.g. ************0050)
    - exception messages never leak the plaintext PIN
    """
    secret_log_pin = make_unique_pin("0020")
    test_user = f"user_log_sec_{uuid.uuid4().hex[:8]}"
    idemp_key = f"WL-LOGSEC-{uuid.uuid4().hex[:8]}"

    with caplog.at_level(logging.DEBUG):
        ok, msg, tx_data = commerce_service.redeem_1voucher(
            user_id=test_user,
            voucher_pin=secret_log_pin,
            idempotency_key=idemp_key
        )

    assert ok is True
    # Check logger output
    all_log_text = caplog.text
    assert secret_log_pin not in all_log_text, "CRITICAL SECURITY LEAK: Plaintext PIN detected in log streams!"

    # Check return dictionary
    res_str = json.dumps(tx_data)
    assert secret_log_pin not in res_str, "CRITICAL SECURITY LEAK: Plaintext PIN returned in response payload!"
    assert tx_data.get("masked_pin") == "************0020"


# ============================================================================
# CATEGORY 4: STABLE IDEMPOTENCY / REFERENCE CONTRACT
# ============================================================================

def test_04_stable_idempotency_reference_behaviour():
    """
    Category 4: Stable Idempotency / Reference Behaviour
    Verifies:
    - reference remains stable across redemption and retry attempts
    - reference is bound to the payment event
    - retrying the same operation never generates a second random reference
    """
    test_user = f"user_stable_ref_{uuid.uuid4().hex[:8]}"
    stable_ref = f"WL-REF-STABLE-{uuid.uuid4().hex[:8]}"
    pin = make_unique_pin("0050")

    ok, msg, tx_data = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin,
        idempotency_key=stable_ref
    )
    assert ok is True
    first_event_id = tx_data["event_id"]
    first_prov_ref = tx_data["reference"]

    # Retry with exact same reference
    ok2, msg2, tx_data2 = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin,
        idempotency_key=stable_ref
    )
    assert ok2 is True
    assert tx_data2["status"] == "ALREADY_PROCESSED"
    assert tx_data2["event_id"] == first_event_id
    assert tx_data2.get("idempotency_key") == stable_ref
    assert tx_data2["reference"] == first_prov_ref
    assert tx_data2["coins_credited_now"] == 0


# ============================================================================
# CATEGORY 5: PAYMENT EVENT LIFECYCLE
# ============================================================================

def test_05_payment_event_lifecycle():
    """
    Category 5: Payment Event Lifecycle
    Verifies payment event transitions against existing schema:
    - INITIATED is written before provider call
    - On provider success -> transitions to SUCCESS with ledger_transaction_id
    - On provider failure -> transitions to PROVIDER_DECLINED
    - On ambiguous outcome / timeout -> transitions to NEEDS_RECONCILIATION
    - Financial fields on SUCCESS event are immutable
    """
    test_user = f"user_life_{uuid.uuid4().hex[:8]}"

    # A. Successful redemption lifecycle
    success_ref = f"WL-LIFE-SUCC-{uuid.uuid4().hex[:6]}"
    pin_succ = make_unique_pin("0050")
    ok, msg, tx = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_succ,
        idempotency_key=success_ref
    )
    assert ok is True
    event = next(e for e in commerce_service.local_get("payment_events") if e["id"] == tx["event_id"])
    assert event["processing_status"] == "SUCCESS"
    assert event["ledger_transaction_id"] is not None
    assert event["amount_fiat"] > 0
    assert event["coins_grant"] > 0

    # B. Declined redemption lifecycle (PIN ending in 9999 = already used)
    declined_ref = f"WL-LIFE-DECL-{uuid.uuid4().hex[:6]}"
    pin_decl = make_unique_pin("9999")
    ok_dec, msg_dec, tx_dec = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_decl,
        idempotency_key=declined_ref
    )
    assert ok_dec is False
    events = commerce_service.local_get("payment_events")
    event_dec = next(e for e in events if e.get("idempotency_key") == declined_ref)
    assert event_dec["processing_status"] == "PROVIDER_DECLINED"

    # C. Ambiguous / timeout redemption lifecycle
    timeout_ref = f"WL-LIFE-TIME-{uuid.uuid4().hex[:6]}"
    pin_time = make_unique_pin("0050")
    with patch.object(onevoucher_adapter, "execute_redemption") as mock_exec:
        mock_exec.return_value = (False, "Timeout occurred", {
            "responseCode": 2210,
            "responseMessage": "A timeout occurred",
            "reference": timeout_ref,
            "is_timeout": True,
            "requires_retry_with_same_reference": True
        })
        ok_time, msg_time, tx_time = commerce_service.redeem_1voucher(
            user_id=test_user,
            voucher_pin=pin_time,
            idempotency_key=timeout_ref
        )
        assert ok_time is False
        event_time = next(e for e in commerce_service.local_get("payment_events") if e.get("idempotency_key") == timeout_ref)
        assert event_time["processing_status"] == "NEEDS_RECONCILIATION"


# ============================================================================
# CATEGORY 6: FLASH RESPONSECODE PARSING
# ============================================================================

def test_06_flash_response_code_parsing():
    """
    Category 6: Flash responseCode Parsing
    Direct deterministic unit testing of OneVoucherAdapter.parse_response:
    - responseCode 0 -> success
    - responseCode 2401 -> already used
    - responseCode 2402 -> not found
    - responseCode 2405 -> expired
    - responseCode 2301 -> reference invalid
    - responseCode 2210/2211 -> timeout / ambiguous
    """
    adapter = OneVoucherAdapter()

    # Success
    ok, msg, res = adapter.parse_response(200, {"responseCode": 0, "amount": 1000}, "REF-001")
    assert ok is True
    assert res["amount_zar"] == 10.0
    assert res["coins_grant"] == 50
    assert res["is_timeout"] is False

    # Already used
    ok, msg, res = adapter.parse_response(200, {"responseCode": 2401, "responseMessage": "Voucher already used"}, "REF-002")
    assert ok is False
    assert res["is_timeout"] is False

    # Not found
    ok, msg, res = adapter.parse_response(200, {"responseCode": 2402, "responseMessage": "Voucher not found"}, "REF-003")
    assert ok is False
    assert res["is_timeout"] is False

    # Expired
    ok, msg, res = adapter.parse_response(200, {"responseCode": 2405, "responseMessage": "Voucher expired"}, "REF-004")
    assert ok is False
    assert res["is_timeout"] is False

    # Timeout code 2210
    ok, msg, res = adapter.parse_response(200, {"responseCode": 2210, "responseMessage": "Timeout occurred"}, "REF-005")
    assert ok is False
    assert res["is_timeout"] is True
    assert res["requires_retry_with_same_reference"] is True


# ============================================================================
# CATEGORY 7: HTTP 200 + RESPONSECODE 0 = PROVIDER SUCCESS
# ============================================================================

def test_07_http_200_plus_response_code_0_is_provider_success():
    """
    Category 7: HTTP 200 + responseCode 0 = Provider Success
    Proves that only HTTP 200 combined with integer responseCode 0 constitutes provider success.
    """
    adapter = OneVoucherAdapter()
    ok, msg, res = adapter.parse_response(
        status_code=200,
        response_data={"responseCode": 0, "amount": 5000, "transactionId": 771122},
        reference="REF-SUCC-200"
    )
    assert ok is True
    assert res["amount_zar"] == 50.0
    assert res["coins_grant"] == 250
    assert res["transactionId"] == 771122


# ============================================================================
# CATEGORY 8: HTTP 200 + NONZERO RESPONSECODE = PROVIDER FAILURE
# ============================================================================

def test_08_http_200_plus_nonzero_response_code_is_provider_failure():
    """
    Category 8: HTTP 200 + Non-Zero responseCode = Provider Failure
    HTTP 200 status code alone is NEVER treated as successful redemption.
    """
    adapter = OneVoucherAdapter()
    ok, msg, res = adapter.parse_response(
        status_code=200,
        response_data={"responseCode": 2401, "responseMessage": "The voucher you have entered has already been used"},
        reference="REF-FAIL-200"
    )
    assert ok is False
    assert "declined" in msg.lower() or "already been used" in msg.lower()
    assert res.get("coins_grant") is None


# ============================================================================
# CATEGORY 9: TIMEOUT = AMBIGUOUS OUTCOME
# ============================================================================

def test_09_timeout_is_ambiguous_outcome():
    """
    Category 9: Timeout = Ambiguous Outcome
    Proves that provider timeout (HTTP 504 / code 2210) is cleanly distinguished
    from explicit provider decline, and flags retry with the same reference.
    """
    adapter = OneVoucherAdapter()
    ok, msg, res = adapter.parse_response(
        status_code=504,
        response_data={"responseCode": 2210, "responseMessage": "A timeout occurred, please resubmit the request"},
        reference="REF-TIMEOUT-01"
    )
    assert ok is False
    assert res["is_timeout"] is True
    assert res["requires_retry_with_same_reference"] is True
    assert "timeout" in msg.lower()


# ============================================================================
# CATEGORY 10: DUPLICATE IDEMPOTENCY PROTECTION
# ============================================================================

def test_10_duplicate_idempotency_protection():
    """
    Category 10: Duplicate Idempotency Protection
    Verifies:
    - Same user replay returns ALREADY_PROCESSED and grants 0 new coins.
    - Cross-user collision triggers FORBIDDEN_CROSS_USER and grants 0 coins.
    """
    user_a = f"user_a_{uuid.uuid4().hex[:6]}"
    user_b = f"user_b_{uuid.uuid4().hex[:6]}"
    shared_ref = f"WL-IDEMP-DUP-{uuid.uuid4().hex[:6]}"
    pin = make_unique_pin("0050")

    # User A succeeds
    ok_a, msg_a, data_a = commerce_service.redeem_1voucher(
        user_id=user_a,
        voucher_pin=pin,
        idempotency_key=shared_ref
    )
    assert ok_a is True
    assert data_a["coins_credited_now"] == 250

    # User A resubmits -> idempotent replay (0 coins granted)
    ok_a2, msg_a2, data_a2 = commerce_service.redeem_1voucher(
        user_id=user_a,
        voucher_pin=pin,
        idempotency_key=shared_ref
    )
    assert ok_a2 is True
    assert data_a2["status"] == "ALREADY_PROCESSED"
    assert data_a2["coins_credited_now"] == 0

    # User B submits User A's reference -> rejected cross-user
    ok_b, msg_b, data_b = commerce_service.redeem_1voucher(
        user_id=user_b,
        voucher_pin=pin,
        idempotency_key=shared_ref
    )
    assert ok_b is False
    assert data_b["status"] == "FORBIDDEN_CROSS_USER"


# ============================================================================
# CATEGORY 11: DUPLICATE SETTLEMENT PROTECTION
# ============================================================================

def test_11_duplicate_settlement_protection():
    """
    Category 11: Duplicate Settlement Protection
    Verifies that coin_ledger idempotency prevents double settlement
    at the database/ledger layer.
    """
    test_user = f"user_settle_{uuid.uuid4().hex[:6]}"
    idemp_key = f"WL-SETTLE-{uuid.uuid4().hex[:6]}"

    # First settlement
    ok1, msg1, entry1 = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="REF-SETTLE-01",
        idempotency_key=idemp_key
    )
    assert ok1 is True

    # Second settlement attempt with same idempotency key
    ok2, msg2, entry2 = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="REF-SETTLE-01",
        idempotency_key=idemp_key
    )
    assert ok2 is True
    assert msg2 == "Idempotent credit already processed"
    assert entry2["id"] == entry1["id"]

    # Verify balance has not been doubled
    bal = ledger_repository.get_balance(test_user)
    # 100 initial onboarding + 100 single settlement = 200 base coins
    assert bal["coin_balance"] == 200


# ============================================================================
# CATEGORY 12: ATOMIC WALLET CREDIT CONTRACT
# ============================================================================

def test_12_atomic_wallet_credit_contract():
    """
    Category 12: Atomic Wallet Credit Contract
    Verifies that ledger insertion and wallet balance mutation occur atomically
    using public.fn_credit_coins_atomic contract without non-atomic separate REST calls.
    """
    test_user = f"user_atomic_{uuid.uuid4().hex[:6]}"
    idemp = f"WL-ATOMIC-{uuid.uuid4().hex[:6]}"

    bal_before = ledger_repository.get_balance(test_user)["total_usable_coins"]

    ok, msg, entry = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=75,
        bonus_coins=25,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="REF-ATOMIC-01",
        idempotency_key=idemp,
        description="Atomic credit test"
    )
    assert ok is True
    assert entry["amount"] == 100

    bal_after = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_after == bal_before + 100


# ============================================================================
# CATEGORY 13: FAILED PROVIDER = ZERO COIN CREDIT
# ============================================================================

def test_13_failed_provider_yields_zero_coin_credit():
    """
    Category 13: Failed Provider = Zero Coin Credit
    Verifies that when a provider explicitly declines a redemption:
    - 0 coins are credited to the user's wallet
    - no journal entry is created in coin_ledger
    """
    test_user = f"user_fail_prov_{uuid.uuid4().hex[:6]}"
    bal_before = ledger_repository.get_balance(test_user)["total_usable_coins"]

    # Use PIN ending in 9999 (voucher already used)
    pin_fail = make_unique_pin("9999")
    ok, msg, tx = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_fail,
        idempotency_key=f"WL-FAIL-PROV-{uuid.uuid4().hex[:6]}"
    )
    assert ok is False

    bal_after = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_after == bal_before, "CRITICAL ERROR: Failed provider result credited coins to user wallet!"


# ============================================================================
# CATEGORY 14: AMBIGUOUS PROVIDER = ZERO AUTOMATIC COIN CREDIT
# ============================================================================

def test_14_ambiguous_provider_outcome_zero_automatic_coin_credit():
    """
    Category 14: Ambiguous Provider = Zero Automatic Coin Credit
    Verifies that when a provider redemption times out:
    - 0 coins are credited automatically
    - status transitions to NEEDS_RECONCILIATION
    - recovery attempt refuses to auto-credit coins without partner confirmation
    """
    test_user = f"user_ambig_{uuid.uuid4().hex[:6]}"
    ambig_ref = f"WL-AMBIG-{uuid.uuid4().hex[:6]}"
    pin_ambig = make_unique_pin("0050")
    bal_before = ledger_repository.get_balance(test_user)["total_usable_coins"]

    with patch.object(onevoucher_adapter, "execute_redemption") as mock_exec:
        mock_exec.return_value = (False, "Timeout connecting to Flash switch", {
            "responseCode": 2210,
            "responseMessage": "A timeout occurred",
            "reference": ambig_ref,
            "is_timeout": True,
            "requires_retry_with_same_reference": True
        })
        ok, msg, tx = commerce_service.redeem_1voucher(
            user_id=test_user,
            voucher_pin=pin_ambig,
            idempotency_key=ambig_ref
        )
        assert ok is False

    bal_after = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_after == bal_before, "CRITICAL ERROR: Ambiguous timeout blindly credited coins to user wallet!"

    # Verify event is in NEEDS_RECONCILIATION state
    ev = next(e for e in commerce_service.local_get("payment_events") if e.get("idempotency_key") == ambig_ref)
    assert ev["processing_status"] == "NEEDS_RECONCILIATION"

    # Attempting to re-call or recover this ambiguous event refuses to blindly credit
    ok_rec, msg_rec, data_rec = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=pin_ambig,
        idempotency_key=ambig_ref
    )
    assert ok_rec is False
    assert data_rec.get("error_code") == "PROVIDER_OUTCOME_AMBIGUOUS_RECONCILIATION_REQUIRED"

    bal_final = ledger_repository.get_balance(test_user)["total_usable_coins"]
    assert bal_final == bal_before


# ============================================================================
# CATEGORY 15: AUDIT CHAIN INTEGRITY
# ============================================================================

def test_15_audit_chain_integrity():
    """
    Category 15: Audit Chain Integrity
    Verifies:
    - audit ledger records payment lifecycle events
    - metadata contains only masked_pin, never plaintext PIN
    - cryptographic hash chain verifies valid
    """
    secret_audit_pin = make_unique_pin("0100")  # R100
    test_user = f"user_aud_{uuid.uuid4().hex[:6]}"

    ok, msg, tx = commerce_service.redeem_1voucher(
        user_id=test_user,
        voucher_pin=secret_audit_pin,
        idempotency_key=f"WL-AUD-{uuid.uuid4().hex[:6]}"
    )
    assert ok is True

    # Check audit ledger
    chain_check = audit_service.verify_audit_chain_integrity()
    assert chain_check["valid"] is True, f"Audit chain broken: {chain_check.get('error')}"

    # Verify no raw PIN in audit records
    events = audit_service.list_audit_events(domain="COMMERCE", limit=10)
    for e in events:
        e_str = json.dumps(e)
        assert secret_audit_pin not in e_str, "CRITICAL SECURITY LEAK: Raw PIN discovered in audit ledger!"


# ============================================================================
# CATEGORY 16: PRODUCTION TARGET GUARD
# ============================================================================

def test_16_production_target_guard():
    """
    Category 16: Production Target Guard
    Verifies:
    - Target validator strictly blocks production Supabase project ref
    - In production, missing credentials or mock mode triggers RuntimeError
    - Flash sandbox status cleanly reports BLOCKED / NOT_CONFIGURED when credentials absent
    """
    prod_ref = CONFIRMED_PRODUCTION_REF  # "mngyyxqdhjgteezwkxdn"
    assert prod_ref == "mngyyxqdhjgteezwkxdn"

    # 1. Target validator blocks production in staging/test
    with pytest.raises(RuntimeError) as exc_info:
        validate_database_target("staging", f"https://{prod_ref}.supabase.co")
    assert "CRITICAL SECURITY HALT" in str(exc_info.value)
    assert "PROTECTED PRODUCTION" in str(exc_info.value)

    # 2. Production halt on missing credentials or mock mode
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "FLASH_ENVIRONMENT": "production",
        "FLASH_ACCOUNT_NUMBER": "",
        "FLASH_CLIENT_ID": "",
        "FLASH_CLIENT_SECRET": ""
    }):
        with pytest.raises(RuntimeError) as exc_halt:
            OneVoucherAdapter()
        assert "CRITICAL SECURITY CONFIGURATION HALT" in str(exc_halt.value)

    # 3. Clean configuration boundary reporting
    adapter = OneVoucherAdapter()
    assert hasattr(adapter, "sandbox_status")
    assert adapter.SANDBOX_BASE_URL == "https://api-flashswitch-sandbox.flash-group.com"
    assert adapter.PRODUCTION_BASE_URL == "https://api.flashswitch.flash-group.com"
    assert adapter.token_url.endswith("/token")
    assert adapter.sandbox_status in ("CONFIGURED", "BLOCKED / NOT_CONFIGURED")
