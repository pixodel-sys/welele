"""
Welele Media™ — Double-Entry Financial Ledger Tests (GAP-002 & GAP-003)
Validates: Atomic balance checks, double-entry audit records, and idempotency key deduplication.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.ledger_repository import ledger_repository

def test_atomic_double_entry_ledger():
    print("\n--- Running Double-Entry Financial Ledger Tests ---")

    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    # 1. Onboarding Wallet Creation (100 Base + 25 Bonus)
    wallet = ledger_repository.get_or_create_wallet(test_user_id)
    assert wallet["coin_balance"] == 100
    assert wallet["bonus_coins"] == 25
    balance = ledger_repository.get_balance(test_user_id)
    assert balance["total_usable_coins"] == 125
    print(f"[PASS] Wallet Onboarding: Initialized wallet for {test_user_id} with 125 total usable coins (100 Base + 25 Bonus).")

    # 2. Debit Coins Atomic (Bonus coins deducted first)
    success, msg, entry = ledger_repository.debit_coins_atomic(
        user_id=test_user_id,
        amount=15,
        transaction_type="EPISODE_UNLOCK",
        reference_id="ep_bt_3",
        idempotency_key=f"idemp_test_1_{test_user_id}",
        description="Unlocked Episode 3"
    )
    assert success is True
    assert entry["amount"] == -15
    assert entry["balance_before"] == 125
    assert entry["balance_after"] == 110

    new_bal = ledger_repository.get_balance(test_user_id)
    assert new_bal["bonus_coins"] == 10 # 25 - 15 = 10
    assert new_bal["coin_balance"] == 100
    print(f"[PASS] Atomic Debit: Debited 15 coins from bonus balance (Remaining: 10 Bonus, 100 Base).")

    # 3. Idempotency Key Deduplication
    idemp_key = f"idemp_repeat_{test_user_id}"
    ok1, _, e1 = ledger_repository.debit_coins_atomic(
        user_id=test_user_id,
        amount=10,
        transaction_type="EPISODE_UNLOCK",
        reference_id="ep_bt_4",
        idempotency_key=idemp_key
    )
    assert ok1 is True

    # Replay with same idempotency key
    ok2, msg2, e2 = ledger_repository.debit_coins_atomic(
        user_id=test_user_id,
        amount=10,
        transaction_type="EPISODE_UNLOCK",
        reference_id="ep_bt_4",
        idempotency_key=idemp_key
    )
    assert ok2 is True
    assert e1["id"] == e2["id"]
    assert "Idempotent" in msg2

    # Balance must NOT have decreased a second time
    bal_after_idemp = ledger_repository.get_balance(test_user_id)
    assert bal_after_idemp["total_usable_coins"] == 100 # 110 - 10 = 100
    print(f"[PASS] Idempotency: Duplicate transaction replay with key '{idemp_key}' safely resolved without double-debiting.")

    # 4. Insufficient Balance Gate
    ok_fail, fail_msg, _ = ledger_repository.debit_coins_atomic(
        user_id=test_user_id,
        amount=500,
        transaction_type="EPISODE_UNLOCK",
        reference_id="ep_bt_99"
    )
    assert ok_fail is False
    assert "Insufficient" in fail_msg
    print(f"[PASS] Balance Gate: Overdraw of 500 coins safely rejected ({fail_msg}).")

    print("=======================================================")
    print("ALL DOUBLE-ENTRY FINANCIAL LEDGER TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_atomic_double_entry_ledger()
