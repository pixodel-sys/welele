"""
Welele Media™ — FinTech Concurrency, Cross-User Idempotency & Fail-Closed Test Suite
Tests:
1. Concurrent first credits for a user with no wallet (wallets.user_id unique invariant).
2. Concurrent duplicate requests for same user (database-level idempotency serialization).
3. Concurrent requests using same idempotency key targeting DIFFERENT users:
   - Verifies User B is rejected.
   - Verifies User B's wallet mutation is completely rolled back / never applied.
4. Unavailable RPC followed by recovery:
   - Verifies INITIATED payment event was durably recorded BEFORE external redemption succeeded.
   - Verifies RPC failure fails closed to NEEDS_RECONCILIATION.
   - Verifies recovery retry does not re-call Flash switch.
   - Verifies exactly one credit is granted.
5. Failed durable pre-record fails closed:
   - Verifies Flash switch is NEVER called if database pre-record fails.
"""

import os
import sys
import uuid
import random
import threading
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["ENVIRONMENT"] = "test"
os.environ["FLASH_MOCK_MODE"] = "true"
os.environ["FLASH_PIN_HMAC_SECRET"] = "test_fixture_hmac_secret_not_for_prod"

from services.commerce_service import commerce_service
from repositories.ledger_repository import ledger_repository
from services.payment_adapters.onevoucher_adapter import onevoucher_adapter


def test_concurrent_first_time_wallet_credits():
    """
    Case 1: Concurrency-safe first-time wallet creation.
    Simulates multiple concurrent threads crediting coins for a brand-new user simultaneously.
    Verifies that the unique wallets.user_id invariant is preserved and balances sum correctly.
    """
    new_user = f"user_concurrent_{uuid.uuid4().hex[:8]}"
    num_threads = 4
    coins_per_thread = 50
    results = []
    errors = []

    def worker(idx):
        try:
            ok, msg, entry = ledger_repository.credit_coins_atomic(
                user_id=new_user,
                base_coins=coins_per_thread,
                transaction_type="TOPUP_1VOUCHER",
                reference_id=f"ref_init_{idx}_{uuid.uuid4().hex[:6]}",
                idempotency_key=f"idemp_init_{idx}_{uuid.uuid4().hex[:6]}",
                description=f"Thread {idx} credit"
            )
            results.append((ok, entry))
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent first-time credits raised errors: {errors}"
    assert len(results) == num_threads, f"Expected {num_threads} successful credits"
    for ok, entry in results:
        assert ok is True

    # Initial onboarding bonus is 100 base coins, plus num_threads * coins_per_thread
    wallet = ledger_repository.get_or_create_wallet(new_user)
    expected_base = 100 + (num_threads * coins_per_thread)
    assert wallet["coin_balance"] == expected_base, (
        f"Wallet balance mismatch: got {wallet['coin_balance']}, expected {expected_base}"
    )


def test_duplicate_concurrent_requests_idempotency_same_user():
    """
    Case 2: Database-level idempotency under concurrent duplicate requests for the same user.
    Multiple threads submit the exact same voucher/idempotency key at the same instant.
    Verifies that exactly ONE credit succeeds in granting coins, while duplicates receive
    idempotent replay (0 coins granted), preventing double-crediting.
    """
    test_user = f"user_race_{uuid.uuid4().hex[:8]}"
    shared_pin = f"11112222{random.randint(1000, 9999)}0050"  # R50 = 250 coins
    shared_ref = f"WL-RACE-{uuid.uuid4().hex[:8].upper()}"

    redemption_results = []
    redemption_errors = []

    def redeem_worker():
        try:
            ok, msg, data = commerce_service.redeem_1voucher(
                user_id=test_user,
                voucher_pin=shared_pin,
                idempotency_key=shared_ref
            )
            redemption_results.append((ok, msg, data))
        except Exception as e:
            redemption_errors.append(e)

    threads = [threading.Thread(target=redeem_worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(redemption_errors) == 0, f"Errors in concurrent redemption: {redemption_errors}"
    assert len(redemption_results) == 3

    total_coins_granted_now = sum(r[2].get("coins_granted", 0) for r in redemption_results)
    assert total_coins_granted_now == 250, (
        f"Expected exactly 250 coins granted across race responses, got {total_coins_granted_now}"
    )

    initial_grants = [r for r in redemption_results if r[2].get("status") in ("SETTLED", "SUCCESS")]
    replays = [r for r in redemption_results if r[2].get("status") == "ALREADY_PROCESSED"]
    assert len(initial_grants) == 1, f"Expected 1 initial grant, got {len(initial_grants)}"
    assert len(replays) == 2, f"Expected 2 replays, got {len(replays)}"

    wallet = ledger_repository.get_or_create_wallet(test_user)
    assert wallet["coin_balance"] == 350  # 100 base + 250 voucher


def test_cross_user_idempotency_collision_fails_and_rolls_back():
    """
    Case 3: Concurrent requests using the same idempotency key targeting DIFFERENT users.
    A malicious or duplicate request attempts to reuse User A's idempotency key for User B.
    Verifies:
      1. User A's credit succeeds.
      2. User B's credit fails with an idempotency collision error.
      3. User B's wallet mutation is completely rolled back / never mutated.
      4. User B receives 0 coins and User B has no ledger entry for that key.
    """
    user_a = f"user_a_{uuid.uuid4().hex[:8]}"
    user_b = f"user_b_{uuid.uuid4().hex[:8]}"
    shared_key = f"idemp_cross_{uuid.uuid4().hex[:12]}"

    # Initialize User B's wallet to known baseline (100 base + 25 bonus)
    wallet_b_before = ledger_repository.get_or_create_wallet(user_b)
    initial_balance_b = wallet_b_before["coin_balance"]

    # 1. User A executes credit with shared_key
    ok_a, msg_a, entry_a = ledger_repository.credit_coins_atomic(
        user_id=user_a,
        base_coins=200,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="ref_user_a",
        idempotency_key=shared_key,
        description="User A valid credit"
    )
    assert ok_a is True
    assert entry_a["amount"] == 200

    # 2. User B concurrently attempts to execute credit with the EXACT SAME shared_key
    with pytest.raises(RuntimeError) as exc_info:
        ledger_repository.credit_coins_atomic(
            user_id=user_b,
            base_coins=200,
            transaction_type="TOPUP_1VOUCHER",
            reference_id="ref_user_b",
            idempotency_key=shared_key,
            description="User B conflicting credit"
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_info.value)
    assert user_a in str(exc_info.value)

    # 3. Verify User B's wallet was NEVER mutated / credited
    wallet_b_after = ledger_repository.get_or_create_wallet(user_b)
    assert wallet_b_after["coin_balance"] == initial_balance_b, (
        f"User B wallet was modified despite rejected idempotency! Expected {initial_balance_b}, got {wallet_b_after['coin_balance']}"
    )

    # 4. Verify no ledger entry exists for User B with shared_key
    ledger_b = [l for l in ledger_repository.local_get("coin_ledger") if l.get("user_id") == user_b and l.get("idempotency_key") == shared_key]
    assert len(ledger_b) == 0, f"User B has illegal ledger entries: {ledger_b}"


def test_rpc_unavailable_fail_closed_and_recovery():
    """
    Case 4: Unavailable RPC followed by recovery.
    Verifies:
      a. The original payment event is durably recorded as INITIATED BEFORE external redemption could succeed.
      b. An RPC outage fails closed, transitions event to NEEDS_RECONCILIATION.
      c. Client retry recovers safely: Flash switch is NOT called a second time (called exactly once total).
      d. Exactly one credit is granted across the entire lifecycle.
    """
    test_user = f"user_recon_{uuid.uuid4().hex[:8]}"
    pin = f"99887766{random.randint(1000, 9999)}0100"  # R100 = 500 coins
    idemp_ref = f"WL-FAILCLOSED-{uuid.uuid4().hex[:8].upper()}"

    events_before_call = []
    call_count = {"flash": 0}
    original_execute = onevoucher_adapter.execute_redemption

    def tracked_execute(*args, **kwargs):
        call_count["flash"] += 1
        # Verification a: Check that payment_events contains the INITIATED record BEFORE Flash responds
        recorded_events = commerce_service.local_get("payment_events") or []
        init_ev = next((e for e in recorded_events if e.get("idempotency_key") == idemp_ref), None)
        assert init_ev is not None, "CRITICAL: INITIATED payment event was NOT durably recorded before Flash execution!"
        assert init_ev["processing_status"] == "INITIATED"
        events_before_call.append(init_ev)
        return original_execute(*args, **kwargs)

    # Step A: Simulate RPC outage during redemption
    with patch.object(onevoucher_adapter, "execute_redemption", side_effect=tracked_execute):
        with patch.object(
            ledger_repository,
            "credit_coins_atomic",
            side_effect=RuntimeError("CRITICAL FINTECH HALT: fn_credit_coins_atomic RPC unavailable (connection refused)")
        ):
            ok, msg, data = commerce_service.redeem_1voucher(
                user_id=test_user,
                voucher_pin=pin,
                idempotency_key=idemp_ref
            )

            assert ok is False, "Redemption should fail when atomic credit fails"
            assert data.get("status") == "NEEDS_RECONCILIATION"
            assert call_count["flash"] == 1, "Flash must have been called exactly once"
            assert len(events_before_call) == 1, "INITIATED event must have been recorded before Flash execution"

    # Verify payment event in ledger is flagged as NEEDS_RECONCILIATION
    events = commerce_service.local_get("payment_events")
    failed_event = next((e for e in events if e.get("idempotency_key") == idemp_ref), None)
    assert failed_event is not None
    assert failed_event["processing_status"] == "NEEDS_RECONCILIATION"
    assert failed_event["amount_fiat"] == 100.0
    assert failed_event["coins_grant"] == 500

    # Step B: Subsequent retry when RPC functionality is restored
    # The client retries with the same reference and PIN.
    # Flash must NOT be called a second time.
    with patch.object(onevoucher_adapter, "execute_redemption", side_effect=tracked_execute):
        ok2, msg2, data2 = commerce_service.redeem_1voucher(
            user_id=test_user,
            voucher_pin=pin,
            idempotency_key=idemp_ref
        )

        assert ok2 is True, f"Recovery retry should succeed: {msg2}"
        assert data2.get("status") in ("SETTLED", "RECONCILED")
        assert data2.get("coins_granted") == 500
        # Verification c: Flash call count MUST STILL BE 1 (Flash was NOT called again!)
        assert call_count["flash"] == 1, f"Flash switch was called {call_count['flash']} times; must not be re-called on recovery!"

    # Verification d: Exactly one credit in coin_ledger
    ledger_entries = [
        l for l in ledger_repository.local_get("coin_ledger")
        if l.get("user_id") == test_user and l.get("transaction_type") == "TOPUP_1VOUCHER"
    ]
    assert len(ledger_entries) == 1, f"Expected exactly 1 ledger entry, got {len(ledger_entries)}"
    assert ledger_entries[0]["amount"] == 500

    # Wallet has: 100 welcome bonus + 500 voucher coins = 600
    wallet = ledger_repository.get_or_create_wallet(test_user)
    assert wallet["coin_balance"] == 600


def test_failed_pre_record_fails_closed_without_calling_flash():
    """
    Case 5: If the initial INITIATED payment event cannot be durably recorded in the database,
    redemption MUST FAIL CLOSED immediately and NEVER call the external Flash switch.
    """
    test_user = f"user_fail_pre_{uuid.uuid4().hex[:8]}"
    pin = "1111222233334444"
    idemp_ref = f"WL-PREFAIL-{uuid.uuid4().hex[:8].upper()}"

    flash_called = False
    def mock_flash(*args, **kwargs):
        nonlocal flash_called
        flash_called = True
        return True, "SUCCESS", {"status": "SUCCESS"}

    from unittest.mock import PropertyMock
    with patch.object(type(commerce_service), "is_live", new_callable=PropertyMock, return_value=True):
        mock_table = MagicMock()
        mock_table.insert.side_effect = RuntimeError("Database connection pool exhausted")
        with patch.object(commerce_service, "get_table", return_value=mock_table):
            with patch.object(onevoucher_adapter, "execute_redemption", side_effect=mock_flash):
                ok, msg, data = commerce_service.redeem_1voucher(
                    user_id=test_user,
                    voucher_pin=pin,
                    idempotency_key=idemp_ref
                )

                assert ok is False
                assert data.get("status") == "FAILED_PRE_RECORD"
                # Flash must NEVER have been called!
                assert flash_called is False, "CRITICAL VULNERABILITY: Flash switch was called despite pre-record failure!"


def test_same_key_different_request_parameter_mismatch_fails():
    """
    Case 6: Same key with different request parameters (amount, transaction_type, reference).
    A subsequent request attempting to reuse the same idempotency key with conflicting parameters
    must FAIL CLOSED with an idempotency parameter mismatch exception.
    """
    test_user = f"user_mismatch_{uuid.uuid4().hex[:8]}"
    shared_key = f"idemp_mismatch_{uuid.uuid4().hex[:10]}"

    # Step 1: Initial credit of 100 coins
    ok1, msg1, entry1 = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="ref_orig",
        idempotency_key=shared_key
    )
    assert ok1 is True
    assert entry1["amount"] == 100

    # Step 2: Identical replay must succeed
    ok_replay, msg_replay, entry_replay = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="ref_orig",
        idempotency_key=shared_key
    )
    assert ok_replay is True
    assert msg_replay == "Idempotent credit already processed"

    # Step 3: Same key with DIFFERENT amount (200 coins) must FAIL
    with pytest.raises(RuntimeError) as exc_amount:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=200,
            transaction_type="TOPUP_1VOUCHER",
            reference_id="ref_orig",
            idempotency_key=shared_key
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_amount.value)
    assert "amount" in str(exc_amount.value).lower()

    # Step 4: Same key with DIFFERENT transaction type must FAIL
    with pytest.raises(RuntimeError) as exc_type:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=100,
            transaction_type="AIRTIME_PASS",
            reference_id="ref_orig",
            idempotency_key=shared_key
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_type.value)
    assert "transaction_type" in str(exc_type.value).lower()

    # Step 5: Same key with DIFFERENT reference_id must FAIL
    with pytest.raises(RuntimeError) as exc_ref:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=100,
            transaction_type="TOPUP_1VOUCHER",
            reference_id="ref_different",
            idempotency_key=shared_key
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_ref.value)
    assert "reference_id" in str(exc_ref.value).lower()

    # Step 6: Same key with EMPTY reference_id must FAIL (cannot bypass mismatch)
    with pytest.raises(RuntimeError) as exc_empty_ref:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=100,
            transaction_type="TOPUP_1VOUCHER",
            reference_id="",
            idempotency_key=shared_key
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_empty_ref.value)
    assert "reference_id" in str(exc_empty_ref.value).lower()

    # Step 7: Same key with NULL (None) reference_id must FAIL (cannot bypass mismatch)
    with pytest.raises(RuntimeError) as exc_none_ref:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=100,
            transaction_type="TOPUP_1VOUCHER",
            reference_id=None,
            idempotency_key=shared_key
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_none_ref.value)
    assert "reference_id" in str(exc_none_ref.value).lower()

    # Step 8: Original entry with NO reference (empty / NULL)
    # Verifies:
    #   a. NULL vs empty string normalization/equivalence on replay
    #   b. Supplying a new reference when original had none is strictly rejected
    key_no_ref = f"idemp_noref_{uuid.uuid4().hex[:10]}"
    ok_init, msg_init, entry_init = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=50,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="",
        idempotency_key=key_no_ref
    )
    assert ok_init is True
    assert entry_init["amount"] == 50
    assert (entry_init.get("reference_id") or "") == ""

    # Replay with empty string must succeed
    ok_rep1, msg_rep1, entry_rep1 = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=50,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="",
        idempotency_key=key_no_ref
    )
    assert ok_rep1 is True
    assert msg_rep1 == "Idempotent credit already processed"

    # Replay with None (NULL) must succeed (NULL and empty string are equivalent)
    ok_rep2, msg_rep2, entry_rep2 = ledger_repository.credit_coins_atomic(
        user_id=test_user,
        base_coins=50,
        transaction_type="TOPUP_1VOUCHER",
        reference_id=None,
        idempotency_key=key_no_ref
    )
    assert ok_rep2 is True
    assert msg_rep2 == "Idempotent credit already processed"

    # Replay with a newly supplied reference must FAIL (missing ref is not a wildcard)
    with pytest.raises(RuntimeError) as exc_new_ref:
        ledger_repository.credit_coins_atomic(
            user_id=test_user,
            base_coins=50,
            transaction_type="TOPUP_1VOUCHER",
            reference_id="late_supplied_ref_123",
            idempotency_key=key_no_ref
        )
    assert "CRITICAL IDEMPOTENCY VIOLATION" in str(exc_new_ref.value)
    assert "reference_id" in str(exc_new_ref.value).lower()


def test_negative_base_amount_rejected():
    """
    Case 7: Negative base amount rejected.
    Verifies that credit_coins_atomic rejects negative base_coins without mutating wallet or ledger.
    """
    user = f"user_neg_base_{uuid.uuid4().hex[:8]}"
    initial_balance = ledger_repository.get_balance(user)["total_usable_coins"]
    entries_before = len([l for l in ledger_repository.local_get("coin_ledger") if l.get("user_id") == user])

    ok, msg, entry = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=-50,
        bonus_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        idempotency_key=f"idemp_neg_base_{uuid.uuid4().hex[:8]}"
    )
    assert ok is False
    assert "base coins cannot be negative" in msg.lower()
    assert entry == {}

    # Verify wallet remains unchanged
    balance_after = ledger_repository.get_balance(user)["total_usable_coins"]
    assert balance_after == initial_balance

    # Verify no new ledger entry created
    entries_after = len([l for l in ledger_repository.local_get("coin_ledger") if l.get("user_id") == user])
    assert entries_after == entries_before


def test_negative_bonus_amount_rejected():
    """
    Case 8: Negative bonus amount rejected.
    Verifies that credit_coins_atomic rejects negative bonus_coins without mutating wallet or ledger.
    """
    user = f"user_neg_bonus_{uuid.uuid4().hex[:8]}"
    initial_balance = ledger_repository.get_balance(user)["total_usable_coins"]
    entries_before = len([l for l in ledger_repository.local_get("coin_ledger") if l.get("user_id") == user])

    ok, msg, entry = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        bonus_coins=-50,
        transaction_type="TOPUP_1VOUCHER",
        idempotency_key=f"idemp_neg_bonus_{uuid.uuid4().hex[:8]}"
    )
    assert ok is False
    assert "bonus coins cannot be negative" in msg.lower()
    assert entry == {}

    balance_after = ledger_repository.get_balance(user)["total_usable_coins"]
    assert balance_after == initial_balance

    entries_after = len([l for l in ledger_repository.local_get("coin_ledger") if l.get("user_id") == user])
    assert entries_after == entries_before


def test_zero_total_credit_rejected():
    """
    Case 9: Zero or negative total credit rejected.
    """
    user = f"user_zero_credit_{uuid.uuid4().hex[:8]}"
    initial_balance = ledger_repository.get_balance(user)["total_usable_coins"]

    ok, msg, entry = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=0,
        bonus_coins=0,
        transaction_type="TOPUP_1VOUCHER",
        idempotency_key=f"idemp_zero_{uuid.uuid4().hex[:8]}"
    )
    assert ok is False
    assert "greater than zero" in msg.lower()
    assert entry == {}

    balance_after = ledger_repository.get_balance(user)["total_usable_coins"]
    assert balance_after == initial_balance


def test_null_user_and_invalid_transaction_type_rejected():
    """
    Case 10: Null user_id and invalid/missing transaction_type rejected.
    """
    # Null / empty user_id
    ok_user, msg_user, entry_user = ledger_repository.credit_coins_atomic(
        user_id="",
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER"
    )
    assert ok_user is False
    assert "user id" in msg_user.lower()

    # Invalid transaction_type
    user = f"user_tx_type_{uuid.uuid4().hex[:8]}"
    ok_type, msg_type, entry_type = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        transaction_type="FORGED_INVALID_TYPE"
    )
    assert ok_type is False
    assert "invalid transaction type" in msg_type.lower()

    # Empty transaction_type
    ok_empty_type, msg_empty_type, entry_empty_type = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        transaction_type="   "
    )
    assert ok_empty_type is False
    assert "transaction type" in msg_empty_type.lower()

    # Purchase type without idempotency key rejected
    ok_no_key, msg_no_key, _ = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        transaction_type="TOPUP_1VOUCHER",
        idempotency_key=None
    )
    assert ok_no_key is False
    assert "idempotency_key" in msg_no_key.lower()


def _simulate_trigger_update(old_record, new_record):
    """Offline Python simulation of PostgreSQL fn_guard_payment_events_settlement trigger logic."""
    if old_record.get("processing_status") in ("SUCCESS", "SETTLED_DISPUTED"):
        protected_fields = [
            "amount_fiat", "coins_grant", "currency",
            "provider_transaction_id", "idempotency_key", "pin_hash"
        ]
        for f in protected_fields:
            if new_record.get(f) != old_record.get(f):
                raise RuntimeError(f"CRITICAL FINTECH INVARIANT: Core financial parameters of a settled payment_event cannot be modified: {f}")

    if old_record.get("processing_status") == "SUCCESS":
        if new_record.get("processing_status") not in ("SUCCESS", "SETTLED_DISPUTED"):
            raise RuntimeError(f"CRITICAL FINTECH INVARIANT: A SUCCESS payment event cannot transition to {new_record.get('processing_status')}")

    if old_record.get("processing_status") == "SETTLED_DISPUTED":
        if new_record.get("processing_status") != "SETTLED_DISPUTED":
            raise RuntimeError(f"CRITICAL FINTECH INVARIANT: A SETTLED_DISPUTED payment event cannot be reverted or changed to {new_record.get('processing_status')}")


def test_settled_payment_event_immutability_offline_simulation():
    """
    Case 11: A SUCCESS payment cannot have protected financial fields modified,
    and cannot be reverted to non-success status.
    (Simulates database trigger fn_guard_payment_events_settlement offline)
    """
    success_event = {
        "id": "pe_test_success_1",
        "processing_status": "SUCCESS",
        "amount_fiat": 100.0,
        "coins_grant": 500,
        "currency": "ZAR",
        "provider_transaction_id": "fl_tx_12345",
        "idempotency_key": "WL-IDEMP-01",
        "pin_hash": "a" * 64,
        "metadata": {"notes": "initial"}
    }

    # 1. Modifying amount_fiat must FAIL
    with pytest.raises(RuntimeError) as exc_amount:
        _simulate_trigger_update(success_event, dict(success_event, amount_fiat=200.0))
    assert "amount_fiat" in str(exc_amount.value)

    # 2. Modifying coins_grant must FAIL
    with pytest.raises(RuntimeError) as exc_coins:
        _simulate_trigger_update(success_event, dict(success_event, coins_grant=1000))
    assert "coins_grant" in str(exc_coins.value)

    # 3. Modifying provider_transaction_id must FAIL
    with pytest.raises(RuntimeError) as exc_tx:
        _simulate_trigger_update(success_event, dict(success_event, provider_transaction_id="fl_forged"))
    assert "provider_transaction_id" in str(exc_tx.value)

    # 4. Modifying idempotency_key must FAIL
    with pytest.raises(RuntimeError) as exc_idemp:
        _simulate_trigger_update(success_event, dict(success_event, idempotency_key="WL-FORGED"))
    assert "idempotency_key" in str(exc_idemp.value)

    # 5. Modifying pin_hash must FAIL
    with pytest.raises(RuntimeError) as exc_pin:
        _simulate_trigger_update(success_event, dict(success_event, pin_hash="b" * 64))
    assert "pin_hash" in str(exc_pin.value)

    # 6. Reverting SUCCESS to INITIATED must FAIL
    with pytest.raises(RuntimeError) as exc_rev:
        _simulate_trigger_update(success_event, dict(success_event, processing_status="INITIATED"))
    assert "SUCCESS payment event cannot transition to INITIATED" in str(exc_rev.value)

    # 7. Transitioning SUCCESS to SETTLED_DISPUTED is ALLOWED
    disputed = dict(success_event, processing_status="SETTLED_DISPUTED")
    _simulate_trigger_update(success_event, disputed)


def test_settled_disputed_payment_event_immutability_offline_simulation():
    """
    Case 12: A SETTLED_DISPUTED payment cannot have financial fields modified
    and cannot be reverted to SUCCESS or any other status.
    """
    disputed_event = {
        "id": "pe_test_disputed_1",
        "processing_status": "SETTLED_DISPUTED",
        "amount_fiat": 100.0,
        "coins_grant": 500,
        "currency": "ZAR",
        "provider_transaction_id": "fl_tx_12345",
        "idempotency_key": "WL-IDEMP-01",
        "pin_hash": "a" * 64,
        "metadata": {"dispute_ref": "DISP-999"}
    }

    # 1. Attempting to revert SETTLED_DISPUTED to SUCCESS must FAIL
    with pytest.raises(RuntimeError) as exc_rev:
        _simulate_trigger_update(disputed_event, dict(disputed_event, processing_status="SUCCESS"))
    assert "SETTLED_DISPUTED payment event cannot be reverted" in str(exc_rev.value)

    # 2. Attempting to change to NEEDS_RECONCILIATION must FAIL
    with pytest.raises(RuntimeError) as exc_recon:
        _simulate_trigger_update(disputed_event, dict(disputed_event, processing_status="NEEDS_RECONCILIATION"))
    assert "SETTLED_DISPUTED payment event cannot be reverted" in str(exc_recon.value)

    # 3. Attempting to tamper with financial field on disputed record must FAIL
    with pytest.raises(RuntimeError) as exc_amt:
        _simulate_trigger_update(disputed_event, dict(disputed_event, amount_fiat=0.0))
    assert "amount_fiat" in str(exc_amt.value)


def test_allowed_reconciliation_metadata_changes_succeed():
    """
    Case 13: Legitimate reconciliation updates (notes, audit metadata, dispute info)
    are permitted on settled records.
    """
    success_event = {
        "id": "pe_test_success_1",
        "processing_status": "SUCCESS",
        "amount_fiat": 100.0,
        "coins_grant": 500,
        "currency": "ZAR",
        "provider_transaction_id": "fl_tx_12345",
        "idempotency_key": "WL-IDEMP-01",
        "pin_hash": "a" * 64,
        "metadata": {"notes": "initial"},
        "dispute_reason": None
    }

    # Updating metadata is permitted
    updated = dict(success_event, metadata={"notes": "reconciled with Flash batch 404"})
    _simulate_trigger_update(success_event, updated)

    # Updating dispute details on SETTLED_DISPUTED is permitted
    disputed_event = dict(success_event, processing_status="SETTLED_DISPUTED")
    updated_dispute = dict(disputed_event, dispute_reason="Chargeback reported by user bank")
    _simulate_trigger_update(disputed_event, updated_dispute)


def test_repository_replay_handling_does_not_apply_credit_twice():
    """
    Case 14: Verifies that idempotent replay does not apply a second credit or append duplicate rows
    in either offline/local mode or live RPC mode.
    """
    user = f"user_replay_double_{uuid.uuid4().hex[:8]}"
    shared_key = f"idemp_rep_double_{uuid.uuid4().hex[:8]}"

    bal_before = ledger_repository.get_balance(user)["total_usable_coins"]

    # Initial credit
    ok1, msg1, entry1 = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        bonus_coins=50,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="ref_replay",
        idempotency_key=shared_key
    )
    assert ok1 is True
    assert msg1 == "Credit executed successfully"

    bal1 = ledger_repository.get_balance(user)["total_usable_coins"]
    assert bal1 == bal_before + 150

    ledger_rows_1 = [l for l in ledger_repository.local_get("coin_ledger") if l.get("idempotency_key") == shared_key]
    assert len(ledger_rows_1) == 1

    # Replay
    ok2, msg2, entry2 = ledger_repository.credit_coins_atomic(
        user_id=user,
        base_coins=100,
        bonus_coins=50,
        transaction_type="TOPUP_1VOUCHER",
        reference_id="ref_replay",
        idempotency_key=shared_key
    )
    assert ok2 is True
    assert msg2 == "Idempotent credit already processed"

    # Wallet balance MUST NOT have changed
    bal2 = ledger_repository.get_balance(user)["total_usable_coins"]
    assert bal2 == bal1, f"Balance increased on replay! Expected {bal1}, got {bal2}"

    # Coin ledger MUST NOT have a second row
    ledger_rows_2 = [l for l in ledger_repository.local_get("coin_ledger") if l.get("idempotency_key") == shared_key]
    assert len(ledger_rows_2) == 1, f"Duplicate ledger row appended on replay! Found {len(ledger_rows_2)}"


def test_rpc_failure_does_not_fallback_to_sequential_financial_writes():
    """
    Case 15: Verifies that in live mode, RPC failure halts execution immediately
    (fail-closed) and NEVER falls back to non-atomic sequential REST writes to coin_ledger or wallets.
    """
    user = f"user_no_seq_{uuid.uuid4().hex[:8]}"
    mock_client = MagicMock()
    mock_client.rpc.side_effect = RuntimeError("PostgreSQL RPC connection reset by peer")

    from unittest.mock import PropertyMock
    with patch.object(type(ledger_repository), "is_live", new_callable=PropertyMock, return_value=True):
        with patch.object(ledger_repository, "get_client", return_value=mock_client):
            mock_table = MagicMock()
            with patch.object(ledger_repository, "get_table", return_value=mock_table):
                with pytest.raises(RuntimeError) as exc_halt:
                    ledger_repository.credit_coins_atomic(
                        user_id=user,
                        base_coins=100,
                        transaction_type="TOPUP_1VOUCHER",
                        idempotency_key=f"idemp_seq_{uuid.uuid4().hex[:8]}"
                    )
                assert "CRITICAL FINTECH HALT" in str(exc_halt.value)
                # Verify that get_table was NEVER called (no sequential REST insert attempted!)
                assert mock_table.insert.call_count == 0
                assert mock_table.update.call_count == 0


def test_sql_migration_03_static_contract_verification():
    """
    Case 16: Static verification of backend/migrations/03_payment_events_and_pin_hash_uniqueness.sql.
    Confirms that all required SQL constraints and validations are present in the SQL text.
    """
    sql_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "migrations",
        "03_payment_events_and_pin_hash_uniqueness.sql"
    )
    assert os.path.exists(sql_path), f"Migration 03 file missing at: {sql_path}"

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # 1. fn_guard_payment_events_settlement checks
    assert "IF OLD.processing_status IN ('SUCCESS', 'SETTLED_DISPUTED')" in sql
    assert "NEW.amount_fiat IS DISTINCT FROM OLD.amount_fiat" in sql
    assert "NEW.coins_grant IS DISTINCT FROM OLD.coins_grant" in sql
    assert "NEW.currency IS DISTINCT FROM OLD.currency" in sql
    assert "NEW.provider_transaction_id IS DISTINCT FROM OLD.provider_transaction_id" in sql
    assert "NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key" in sql
    assert "NEW.pin_hash IS DISTINCT FROM OLD.pin_hash" in sql
    assert "NEW.processing_status IS DISTINCT FROM 'SUCCESS'" in sql
    assert "NEW.processing_status IS DISTINCT FROM 'SETTLED_DISPUTED'" in sql

    # 2. fn_credit_coins_atomic input validation checks
    assert "IF p_user_id IS NULL THEN" in sql
    assert "IF p_base_coins IS NULL OR p_bonus_coins IS NULL THEN" in sql
    assert "IF p_base_coins < 0 OR p_bonus_coins < 0 THEN" in sql
    assert "IF v_total_credit <= 0" in sql
    assert "BTRIM(p_transaction_type) = ''" in sql
    assert "'TOPUP_1VOUCHER'" in sql
    assert "pg_advisory_xact_lock" in sql

    # 3. Transaction boundary
    assert "BEGIN;" in sql
    assert "COMMIT;" in sql

    # 3. Privileges
    assert "REVOKE ALL ON FUNCTION public.fn_credit_coins_atomic" in sql
    assert "GRANT EXECUTE ON FUNCTION public.fn_credit_coins_atomic" in sql
    assert "TO service_role" in sql




