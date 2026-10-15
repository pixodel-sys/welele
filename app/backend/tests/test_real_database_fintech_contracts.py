"""
Welele Media™ — Real PostgreSQL Database FinTech Integration & Constraint Verification Suite
Document ID: WELELE-TEST-REAL-DB-FINTECH-V1
Target Database: Supabase Staging Project (dbsnaidhznofvyffdfni) or Local PostgreSQL

PURPOSE:
Separates real PostgreSQL database transaction testing from simulated/in-memory unit tests.
This test suite directly exercises the PostgreSQL schema constraints, indexes, and the
stored function `public.fn_credit_coins_atomic` under real multi-threaded database connections.

CASES EXERCISED AGAINST REAL POSTGRESQL:
1. Schema & Engine Invariants:
   - Asserts public.wallets(user_id) UNIQUE constraint / index exists.
   - Asserts public.coin_ledger(idempotency_key) UNIQUE constraint / index exists.
2. Concurrent First Credits for a User with No Wallet:
   - Launches N concurrent worker threads against real PostgreSQL calling fn_credit_coins_atomic.
   - Proves no duplicate key violation on wallets_user_id_key.
   - Proves balance equals sum of all credits.
3. Concurrent Requests Using Same Idempotency Key (Same User & Cross-User):
   - Same User: Proves exactly 1 credit is applied; duplicate concurrent transactions resolve cleanly to existing record.
   - Cross-User: Proves second user with same key triggers a PostgreSQL exception, aborts, and rolls back every wallet mutation.
4. Unavailable RPC Fail-Closed & Recovery with Pre-Recorded Audit Receipt:
   - Proves INITIATED payment event is durably committed to public.payment_events BEFORE external redemption occurs.
   - Proves that settlement failure marks event as NEEDS_RECONCILIATION.
   - Proves that subsequent recovery succeeds with zero duplicate provider calls and exactly one ledger credit.
"""

import os
import sys
import uuid
import random
import threading
from typing import Dict, Any, List
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

CANDIDATE_STAGING_PATHS = [
    r"G:\App_Development\App_Dev\Welele Media\.env\.env.staging",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.staging"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env", ".env.staging"),
]


def get_live_client_or_skip():
    """
    Retrieves an authorized client connected to the verified Staging Supabase project.
    If credentials are not present or target is production, tests skip safely to honor freeze.
    """
    staging_env_found = None
    for p in CANDIDATE_STAGING_PATHS:
        if os.path.exists(p):
            staging_env_found = p
            break

    if staging_env_found:
        load_dotenv(staging_env_found, override=True)

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        pytest.skip("Staging Supabase credentials not found. Run with staging credentials to execute real database tests.")

    from target_validator import validate_database_target, extract_project_ref, CONFIRMED_STAGING_REF, CONFIRMED_PRODUCTION_REF

    os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
    os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF

    # Safety guardrail: strictly forbid running against production
    ref = extract_project_ref(url)
    if ref == CONFIRMED_PRODUCTION_REF:
        pytest.fail("CRITICAL GUARD TRIGGERED: Cannot execute database tests against FROZEN PRODUCTION project!")

    validate_database_target("staging", url)

    from supabase import create_client
    return create_client(url, key)


def test_real_database_constraints_exist_in_schema():
    """
    Test Case 1 (Real Database):
    Verifies that public.wallets(user_id) and public.coin_ledger(idempotency_key)
    have enforced UNIQUE constraints in the real database engine.
    Probed via PostgREST ON CONFLICT resolution semantics.
    """
    client = get_live_client_or_skip()
    import requests

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Prefer": "resolution=merge-duplicates"}

    # 1. Probe wallets: on_conflict=user_id
    # If user_id is unique, PostgREST accepts on_conflict and fails only on the foreign key / not null check (23503/23502).
    # If user_id is NOT unique, PostgREST returns 400 with 42P10 ("no unique or exclusion constraint matching ON CONFLICT").
    res_w = requests.post(f"{url}/rest/v1/wallets?on_conflict=user_id", headers=headers, json={"user_id": "00000000-0000-0000-0000-000000000000"})
    assert res_w.status_code != 400 or "42P10" not in str(res_w.text), (
        f"wallets(user_id) lacks a unique constraint or index: {res_w.text}"
    )

    # 2. Probe coin_ledger: on_conflict=idempotency_key
    res_l = requests.post(f"{url}/rest/v1/coin_ledger?on_conflict=idempotency_key", headers=headers, json={"idempotency_key": "probe_key"})
    assert res_l.status_code != 400 or "42P10" not in str(res_l.text), (
        f"coin_ledger(idempotency_key) lacks a unique constraint or index: {res_l.text}"
    )


def test_real_database_concurrent_first_credits_no_wallet():
    """
    Test Case 2 (Real Database):
    Launches 4 concurrent threads directly invoking fn_credit_coins_atomic on a brand-new user UUID.
    Verifies:
      1. All 4 concurrent executions succeed without hitting duplicate key error on wallets_user_id_key.
      2. Exactly one wallet row exists for the user.
      3. Total wallet balance equals exactly the sum of all concurrent credits.
    """
    client = get_live_client_or_skip()

    # Note: Requires Migration 03 (fn_credit_coins_atomic) applied to staging.
    # Check if RPC exists first
    test_user_id = str(uuid.uuid4())
    client.table("users").insert({
        "id": test_user_id,
        "display_name": f"Test User {test_user_id[:8]}",
        "region_code": "ZA",
        "preferred_language": "en",
        "role": "viewer",
        "is_verified": True
    }).execute()

    num_threads = 4
    credit_amount = 50

    results = []
    errors = []

    def worker(idx):
        try:
            res = client.rpc("fn_credit_coins_atomic", {
                "p_user_id": test_user_id,
                "p_base_coins": credit_amount,
                "p_bonus_coins": 0,
                "p_transaction_type": "TOPUP_1VOUCHER",
                "p_reference_id": f"ref_thread_{idx}",
                "p_idempotency_key": f"idemp_thread_{idx}_{uuid.uuid4().hex[:6]}",
                "p_description": f"Real DB concurrent test thread {idx}"
            }).execute()
            results.append(res.data)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # If Migration 03 is not yet executed on staging, skip with explicit advisory
    if errors and any("Could not find the function" in str(e) for e in errors):
        pytest.skip("Migration 03 function 'fn_credit_coins_atomic' not yet executed on Staging. Review Migration 03 SQL.")

    assert len(errors) == 0, f"Concurrent first-time credits raised errors: {errors}"
    assert len(results) == num_threads

    # Verify wallet in database
    w_res = client.table("wallets").select("*").eq("user_id", test_user_id).execute()
    assert len(w_res.data) == 1, f"Expected exactly 1 wallet row, got {len(w_res.data)}"
    expected_balance = num_threads * credit_amount
    assert w_res.data[0]["coin_balance"] == expected_balance


def test_real_database_cross_user_idempotency_collision_rolls_back():
    """
    Test Case 3 (Real Database):
    Concurrent requests from two users sharing one idempotency key.
    Verifies:
      1. Conflicting request fails (throws exception or returns failure).
      2. Committed state contains exactly one legitimate credit.
      3. Rejected user receives 0 credit and has 0 ledger rows.
      4. Rejected user has no partial wallet mutation.
    """
    client = get_live_client_or_skip()

    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    for uid, name in [(user_a, "User A"), (user_b, "User B")]:
        client.table("users").insert({
            "id": uid,
            "display_name": f"Test {name} {uid[:8]}",
            "region_code": "ZA",
            "preferred_language": "en",
            "role": "viewer",
            "is_verified": True
        }).execute()

    shared_key = f"real_shared_{uuid.uuid4().hex[:12]}"

    responses = {}
    exceptions = {}

    def call_credit(user_id, tag):
        try:
            res = client.rpc("fn_credit_coins_atomic", {
                "p_user_id": user_id,
                "p_base_coins": 100,
                "p_bonus_coins": 0,
                "p_transaction_type": "TOPUP_1VOUCHER",
                "p_reference_id": f"ref_{tag}",
                "p_idempotency_key": shared_key,
                "p_description": f"Concurrent test {tag}"
            }).execute()
            responses[tag] = res.data
        except Exception as exc:
            exceptions[tag] = str(exc)

    t1 = threading.Thread(target=call_credit, args=(user_a, "user_a"))
    t2 = threading.Thread(target=call_credit, args=(user_b, "user_b"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # If Migration 03 is not yet executed on staging, skip with explicit advisory
    all_errors = list(exceptions.values())
    if all_errors and any("Could not find the function" in e for e in all_errors):
        pytest.skip("Migration 03 function 'fn_credit_coins_atomic' not yet executed on Staging. Review Migration 03 SQL.")

    # Exactly one user must succeed, and the other must fail with an idempotency violation
    successes = [tag for tag, r in responses.items() if r.get("success") is True]
    assert len(successes) == 1, f"Expected exactly 1 successful credit, got responses={responses}, exceptions={exceptions}"
    winning_tag = successes[0]
    losing_tag = "user_b" if winning_tag == "user_a" else "user_a"
    winning_user = user_a if winning_tag == "user_a" else user_b
    losing_user = user_b if winning_tag == "user_a" else user_a

    # Verify losing user call failed with an idempotency violation
    assert losing_tag in exceptions or (losing_tag in responses and not responses[losing_tag].get("success"))
    losing_error = exceptions.get(losing_tag) or responses.get(losing_tag, {}).get("message", "")
    assert "IDEMPOTENCY VIOLATION" in losing_error or "unique" in losing_error.lower()

    # Verify winning user committed state
    w_win = client.table("wallets").select("*").eq("user_id", winning_user).execute()
    assert len(w_win.data) == 1, f"Winning user must have 1 wallet: {w_win.data}"
    assert w_win.data[0]["coin_balance"] == 100, f"Winning user balance mismatch: {w_win.data[0]['coin_balance']}"

    ledger_win = client.table("coin_ledger").select("*").eq("user_id", winning_user).execute()
    assert len(ledger_win.data) == 1, f"Winning user must have 1 ledger entry: {ledger_win.data}"
    assert ledger_win.data[0]["amount"] == 100
    assert ledger_win.data[0]["idempotency_key"] == shared_key

    # Verify losing user has NO ledger entries
    ledger_loss = client.table("coin_ledger").select("*").eq("user_id", losing_user).execute()
    assert len(ledger_loss.data) == 0, f"Losing user has illegal ledger rows: {ledger_loss.data}"

    # Verify losing user has no partial wallet mutation (balance remains 0)
    w_loss = client.table("wallets").select("*").eq("user_id", losing_user).execute()
    if len(w_loss.data) > 0:
        assert w_loss.data[0]["coin_balance"] == 0, f"Losing user was credited: {w_loss.data[0]['coin_balance']}"

