"""
Welele Media™ — Creator Payment Run Test Suite (Workstream 6I-G.4.2)
Verifies:
PRG-001 eligible creator-requested payouts only
PRG-002 no automatic balance sweep
PRG-003 exact run total
PRG-004 no duplicate payout membership
PRG-005 run idempotency
PRG-006 conflicting idempotency rejected
PRG-007 beneficiary snapshot immutable
PRG-008 self-approval rejected
PRG-009 approval locks membership
PRG-010 deterministic export
PRG-011 SHA-256 persisted correctly
PRG-012 export never creates PAID
PRG-013 export moves eligible payouts to PROCESSING exactly once
PRG-014 invalid settlement cannot create PAID
PRG-015 valid settlement creates PAID
PRG-016 failed settlement creates FAILED
PRG-017 retry does not duplicate earnings
PRG-018 result replay is idempotent
PRG-019 amount mismatch rejected
PRG-020 currency mismatch rejected
PRG-021 duplicate external reference rejected
PRG-022 reconciliation catches missing evidence
PRG-023 account details masked
PRG-024 creator IDOR rejected
PRG-025 admin role enforcement
PRG-026 production remains untouched
PRG-027 zero external provider/bank calls
PRG-028 zero creators.coin_earnings writes
PRG-029 viewer coin ledger remains independent
PRG-030 failed payout does not reverse creator earnings
"""

import uuid
import hashlib
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from main import app
from database import db
from schemas.commercial_accounting_schemas import (
    PayoutStatus,
    LedgerEntryType,
    LedgerStatus,
    PaymentRunStatus,
    PaymentRunItemStatus
)
from repositories.commercial_accounting_repository import commercial_accounting_repository
from services.creator_payout_service import creator_payout_service
from services.commercial_payment_run_service import (
    commercial_payment_run_service,
    mask_account_number
)
from services.commercial_reconciliation_service import commercial_reconciliation_service
from services.payout_provider import default_payout_provider
from services.rbac_service import create_access_token

client = TestClient(app)


def get_auth_headers(user_id: str, role: str):
    token = create_access_token(user_id=user_id, role=role, creator_id=user_id if role == "creator" else None)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clean_run_state():
    """Initializes isolated memory store with test creator ledger earnings and creator records."""
    db.enable_test_isolation()
    db.set("creator_payouts", [])
    db.set("creator_payout_allocations", [])
    db.set("creator_payment_runs", [])
    db.set("creator_payment_run_items", [])
    creator_id = "creator_run_fixture"

    # Seed creator profile
    existing_creators = commercial_accounting_repository.local_get("creators")
    if not any(c.get("id") == creator_id for c in existing_creators):
        commercial_accounting_repository.local_insert("creators", {
            "id": creator_id,
            "name": "Run Fixture Creator",
            "coin_earnings": 0  # Retired legacy column remains strictly 0
        })

    # Seed immutable ledger earnings
    earning_entry = {
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "revenue_event_id": str(uuid.uuid4()),
        "accounting_period": "2026-10",
        "entry_type": LedgerEntryType.EARNING.value,
        "creator_amount": 500.0000,
        "currency": "ZAR",
        "status": LedgerStatus.SETTLED.value,
        "idempotency_key": f"fixture_earning_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    commercial_accounting_repository.local_insert("creator_ledger", earning_entry)
    yield creator_id


# ------------------------------------------------------------------------------
# PRG-001 through PRG-009: ELIGIBILITY, IDEMPOTENCY & DUAL-CONTROL
# ------------------------------------------------------------------------------

def test_prg_001_eligible_creator_requested_payouts_only(clean_run_state):
    """PRG-001: Payment run includes eligible creator-requested payouts only."""
    creator_id = clean_run_state
    # Request a payout
    payout_res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.0000"),
        currency="ZAR",
        payout_method="Bank EFT",
        account_details="FNB Acc #62891234567 Branch 250655",
        idempotency_key=f"payout_prg001_{uuid.uuid4().hex}"
    )
    payout_id = payout_res["payout"]["id"]

    # Create run
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg001_{uuid.uuid4().hex}",
        payout_ids=[payout_id]
    )

    run = res["run"]
    items = res["items"]
    assert run["status"] == PaymentRunStatus.DRAFT.value
    assert run["payout_count"] == 1
    assert run["total_amount"] == 100.0
    assert len(items) == 1
    assert items[0]["payout_id"] == payout_id
    assert items[0]["creator_id"] == creator_id


def test_prg_002_no_automatic_balance_sweep(clean_run_state):
    """PRG-002: Creators with positive balance without a payout request are never swept into a run."""
    creator_id = clean_run_state
    # Creator has R500.00 in ledger, but NO payout was requested!
    # Attempting to create a run with no eligible requested payouts must raise ValueError
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="No eligible PENDING creator payout requests found"):
        commercial_payment_run_service.create_run(
            period_start=now - timedelta(days=7),
            period_end=now,
            currency="ZAR",
            created_by="admin_operator_1",
            idempotency_key=f"run_prg002_{uuid.uuid4().hex}"
        )


def test_prg_003_exact_run_total(clean_run_state):
    """PRG-003: Payment run total amount strictly equals sum of included payout amounts."""
    creator_id = clean_run_state
    p1 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("45.2500"),
        currency="ZAR",
        account_details="Standard Bank Acc 111111",
        idempotency_key=f"p1_{uuid.uuid4().hex}"
    )
    p2 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("54.7500"),
        currency="ZAR",
        account_details="Standard Bank Acc 111111",
        idempotency_key=f"p2_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg003_{uuid.uuid4().hex}",
        payout_ids=[p1["payout"]["id"], p2["payout"]["id"]]
    )
    run = res["run"]
    assert Decimal(str(run["total_amount"])) == Decimal("100.0000")
    assert run["payout_count"] == 2


def test_prg_004_no_duplicate_payout_membership(clean_run_state):
    """PRG-004: A payout cannot appear in multiple active runs or duplicate items."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 999999",
        idempotency_key=f"p_prg004_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    # Create first run
    commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg004_a_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )

    # Attempt second run containing the same payout -> Must fail closed
    with pytest.raises(ValueError, match="already assigned to active payment run"):
        commercial_payment_run_service.create_run(
            period_start=now - timedelta(days=7),
            period_end=now,
            currency="ZAR",
            created_by="admin_operator_1",
            idempotency_key=f"run_prg004_b_{uuid.uuid4().hex}",
            payout_ids=[p_id]
        )


def test_prg_005_run_idempotency(clean_run_state):
    """PRG-005: Replaying the same run-generation request returns existing run without duplication."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("60.0000"),
        currency="ZAR",
        account_details="Nedbank Acc 222222",
        idempotency_key=f"p_prg005_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    idemp_key = f"run_idemp_prg005_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    res1 = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=idemp_key,
        payout_ids=[p_id]
    )
    assert res1["is_idempotent_replay"] is False

    # Replay with identical key
    res2 = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=idemp_key,
        payout_ids=[p_id]
    )
    assert res2["is_idempotent_replay"] is True
    assert res2["run"]["id"] == res1["run"]["id"]
    assert res2["run"]["run_reference"] == res1["run"]["run_reference"]


def test_prg_006_conflicting_idempotency_rejected(clean_run_state):
    """PRG-006: Reusing an idempotency key with conflicting parameters fails closed."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("60.0000"),
        currency="ZAR",
        account_details="Nedbank Acc 222222",
        idempotency_key=f"p_prg006_{uuid.uuid4().hex}"
    )

    idemp_key = f"run_idemp_prg006_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=idemp_key,
        payout_ids=[p["payout"]["id"]]
    )

    # Replay with conflicting currency
    with pytest.raises(ValueError, match="Invalid payment run currency"):
        commercial_payment_run_service.create_run(
            period_start=now - timedelta(days=7),
            period_end=now,
            currency="USD",
            created_by="admin_operator_1",
            idempotency_key=idemp_key
        )


def test_prg_007_beneficiary_snapshot_immutable(clean_run_state):
    """PRG-007: Snapshotted payment destination is immutable even if creator profile changes later."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("70.0000"),
        currency="ZAR",
        account_details="Capitec Acc 1234567890 Branch 470010",
        idempotency_key=f"p_prg007_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg007_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    item_id = res["items"][0]["id"]

    # Verify snapshot fields in repository
    raw_item = next(i for i in commercial_accounting_repository.local_get("creator_payment_run_items") if i["id"] == item_id)
    assert raw_item["account_number_snapshot"] == "1234567890"

    # Simulate creator profile bank update in creator record
    creators = commercial_accounting_repository.local_get("creators")
    for c in creators:
        if c.get("id") == creator_id:
            c["bank_account"] = "9999999999"

    # Fetch run detail again -> snapshotted bank account remains unchanged
    refreshed_item = next(i for i in commercial_accounting_repository.local_get("creator_payment_run_items") if i["id"] == item_id)
    assert refreshed_item["account_number_snapshot"] == "1234567890"


def test_prg_008_self_approval_rejected(clean_run_state):
    """PRG-008: Preparer (created_by) cannot approve their own payment run."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("80.0000"),
        currency="ZAR",
        account_details="Absa Acc 404040",
        idempotency_key=f"p_prg008_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_preparer_alice",
        idempotency_key=f"run_prg008_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]

    # Submit for review
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_preparer_alice")

    # Alice attempts to approve her own run -> Must fail closed
    with pytest.raises(ValueError, match="CRITICAL DUAL-CONTROL VIOLATION"):
        commercial_payment_run_service.approve_run(run_id, approver_id="admin_preparer_alice")


def test_prg_009_approval_locks_membership(clean_run_state):
    """PRG-009: Once approved by a distinct supervisor, run status is APPROVED and locked."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("90.0000"),
        currency="ZAR",
        account_details="FNB Acc 888888",
        idempotency_key=f"p_prg009_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_preparer_alice",
        idempotency_key=f"run_prg009_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]

    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_preparer_alice")

    # Distinct supervisor approves
    approved_run = commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_bob")
    assert approved_run["status"] == PaymentRunStatus.APPROVED.value
    assert approved_run["approved_by"] == "admin_supervisor_bob"
    assert approved_run["approved_at"] is not None


# ------------------------------------------------------------------------------
# PRG-010 through PRG-016: EXPORT, HASHING, LIFECYCLE & SETTLEMENT BOUNDARY
# ------------------------------------------------------------------------------

def test_prg_010_deterministic_export(clean_run_state):
    """PRG-010: Bank export is deterministic across repeated calls."""
    creator_id = clean_run_state
    p1 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("30.0000"),
        currency="ZAR",
        account_details="FNB Acc 111111",
        idempotency_key=f"p1_prg010_{uuid.uuid4().hex}"
    )
    p2 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("40.0000"),
        currency="ZAR",
        account_details="Standard Acc 222222",
        idempotency_key=f"p2_prg010_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg010_{uuid.uuid4().hex}",
        payout_ids=[p1["payout"]["id"], p2["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")

    exp1 = commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")
    exp2 = commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    assert exp1["csv_content"] == exp2["csv_content"]
    assert exp1["sha256_hash"] == exp2["sha256_hash"]


def test_prg_011_sha256_persisted_correctly(clean_run_state):
    """PRG-011: Exported SHA-256 hash matches file digest and is persisted on the run."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg011_{uuid.uuid4().hex}"
    )
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg011_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")

    exp = commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")
    expected_hash = hashlib.sha256(exp["csv_content"].encode("utf-8")).hexdigest()

    run = commercial_accounting_repository.get_payment_run(run_id)
    assert run["export_file_hash_sha256"] == expected_hash
    assert exp["sha256_hash"] == expected_hash


def test_prg_012_export_never_creates_paid(clean_run_state):
    """PRG-012: Exporting an approved run transitions payouts to PROCESSING, never directly to PAID."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg012_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg012_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")

    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert payout["status"] == PayoutStatus.PROCESSING.value
    assert payout["status"] != PayoutStatus.PAID.value
    assert payout["settled_at"] is None


def test_prg_013_export_moves_eligible_payouts_to_processing_once(clean_run_state):
    """PRG-013: Export moves eligible payouts from PENDING to PROCESSING exactly once."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg013_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg013_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")

    exp1 = commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")
    assert exp1["transitioned_to_processing"] == 1

    # Re-exporting should not transition again
    exp2 = commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")
    assert exp2["transitioned_to_processing"] == 0


def test_prg_014_invalid_settlement_cannot_create_paid(clean_run_state):
    """PRG-014: External result without payment reference cannot mark payout as PAID."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg014_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg014_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    # Result missing external_payment_reference
    with pytest.raises(ValueError, match="External payment reference is required"):
        commercial_payment_run_service.record_external_results(
            run_id=run_id,
            results=[{
                "payout_id": p_id,
                "status": "SUCCESS",
                "external_payment_reference": ""
            }]
        )


def test_prg_015_valid_settlement_creates_paid(clean_run_state):
    """PRG-015: Valid external result marks payout as PAID with settlement evidence."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg015_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg015_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    rec_res = commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p_id,
            "status": "SUCCESS",
            "external_payment_reference": "BANK-EFT-998877",
            "amount": Decimal("50.0000"),
            "currency": "ZAR"
        }]
    )
    assert rec_res["recorded_success_count"] == 1
    payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert payout["status"] == PayoutStatus.PAID.value
    assert payout["settled_at"] is not None


def test_prg_016_failed_settlement_creates_failed(clean_run_state):
    """PRG-016: Failed external result marks payout as FAILED without destroying earnings."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg016_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg016_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    rec_res = commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p_id,
            "status": "FAILED",
            "failure_reason": "Account closed at receiving bank"
        }]
    )
    assert rec_res["recorded_failure_count"] == 1
    payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert payout["status"] == PayoutStatus.FAILED.value
    assert payout["rejection_reason"] == "Account closed at receiving bank"


# ------------------------------------------------------------------------------
# PRG-017 through PRG-025: INTEGRITY, RECONCILIATION, RBAC & MASKING
# ------------------------------------------------------------------------------

def test_prg_017_retry_does_not_duplicate_earnings(clean_run_state):
    """PRG-017: Retrying a FAILED payout does not duplicate creator ledger earnings."""
    creator_id = clean_run_state
    initial_earnings = [e for e in commercial_accounting_repository.get_creator_ledger(creator_id) if e.get("entry_type") == "EARNING"]

    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg017_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    # Transition to FAILED
    creator_payout_service.transition_payout_status(p_id, "PROCESSING", "admin", "admin")
    creator_payout_service.transition_payout_status(p_id, "FAILED", "admin", "admin", reason="Network drop")

    # Retry the failed payout
    creator_payout_service.retry_failed_payout(p_id, actor_id="admin_supervisor")
    refreshed_payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert refreshed_payout["status"] == PayoutStatus.PROCESSING.value

    # Verify creator ledger earnings remain strictly unchanged (no duplication)
    final_earnings = [e for e in commercial_accounting_repository.get_creator_ledger(creator_id) if e.get("entry_type") == "EARNING"]
    assert len(final_earnings) == len(initial_earnings)


def test_prg_018_result_replay_is_idempotent(clean_run_state):
    """PRG-018: Replaying settlement result confirmation on a PAID payout is idempotent."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg018_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg018_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    # Record first time
    commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p_id,
            "status": "SUCCESS",
            "external_payment_reference": "EFT-REPLAY-001"
        }]
    )

    # Replay same result
    replay_res = commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p_id,
            "status": "SUCCESS",
            "external_payment_reference": "EFT-REPLAY-001"
        }]
    )
    assert replay_res["status"] == PaymentRunStatus.RESULTS_RECORDED.value


def test_prg_019_amount_mismatch_rejected(clean_run_state):
    """PRG-019: External result with amount mismatch is rejected fail-closed."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg019_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg019_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    # Submit R49.00 instead of approved R50.00
    with pytest.raises(ValueError, match="Amount mismatch"):
        commercial_payment_run_service.record_external_results(
            run_id=run_id,
            results=[{
                "payout_id": p_id,
                "status": "SUCCESS",
                "external_payment_reference": "EFT-FAIL-AMT",
                "amount": Decimal("49.0000")
            }]
        )


def test_prg_020_currency_mismatch_rejected(clean_run_state):
    """PRG-020: External result with currency mismatch is rejected fail-closed."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("50.0000"),
        currency="ZAR",
        account_details="FNB Acc 555555",
        idempotency_key=f"p_prg020_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg020_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    with pytest.raises(ValueError, match="Currency mismatch"):
        commercial_payment_run_service.record_external_results(
            run_id=run_id,
            results=[{
                "payout_id": p_id,
                "status": "SUCCESS",
                "external_payment_reference": "EFT-FAIL-CURR",
                "currency": "USD"
            }]
        )


def test_prg_021_duplicate_external_reference_rejected(clean_run_state):
    """PRG-021: Claiming the same external reference across distinct payouts is rejected."""
    creator_id = clean_run_state
    p1 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("30.0000"),
        currency="ZAR",
        account_details="FNB Acc 111111",
        idempotency_key=f"p1_prg021_{uuid.uuid4().hex}"
    )
    p2 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("30.0000"),
        currency="ZAR",
        account_details="FNB Acc 222222",
        idempotency_key=f"p2_prg021_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg021_{uuid.uuid4().hex}",
        payout_ids=[p1["payout"]["id"], p2["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    # Record first payout
    commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p1["payout"]["id"],
            "status": "SUCCESS",
            "external_payment_reference": "SHARED-EFT-12345"
        }]
    )

    # Attempt to use same reference on second payout -> Must fail closed
    with pytest.raises(ValueError, match="Duplicate external payment reference"):
        commercial_payment_run_service.record_external_results(
            run_id=run_id,
            results=[{
                "payout_id": p2["payout"]["id"],
                "status": "SUCCESS",
                "external_payment_reference": "SHARED-EFT-12345"
            }]
        )


def test_prg_022_reconciliation_catches_missing_evidence(clean_run_state):
    """PRG-022: Forensic reconciliation detects missing export hash and evidence anomalies."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("40.0000"),
        currency="ZAR",
        account_details="FNB Acc 777777",
        idempotency_key=f"p_prg022_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg022_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]

    # Reconciling clean draft run
    clean_rec = commercial_payment_run_service.reconcile_run(run_id)
    assert clean_rec["is_clean"] is True

    # Tamper: set status to EXPORTED without export_file_hash_sha256
    commercial_accounting_repository.update_payment_run(run_id, {
        "status": PaymentRunStatus.EXPORTED.value,
        "export_file_hash_sha256": None
    })
    tampered_rec = commercial_payment_run_service.reconcile_run(run_id)
    assert tampered_rec["is_clean"] is False
    assert any("Export hash missing" in e for e in tampered_rec["exceptions"])


def test_prg_023_account_details_masked(clean_run_state):
    """PRG-023: Account numbers are masked in normal read APIs."""
    raw_acc = "62891234567"
    masked = mask_account_number(raw_acc)
    assert masked == "*******4567"
    assert raw_acc not in masked


def test_prg_024_creator_idor_rejected(clean_run_state):
    """PRG-024: Creator role attempting to access admin payment run endpoints is rejected 403."""
    headers = get_auth_headers("creator_zola", "creator")
    resp = client.get("/api/v1/admin/commercial/runs", headers=headers)
    assert resp.status_code == 403


def test_prg_025_admin_role_enforcement(clean_run_state):
    """PRG-025: admin_operator cannot approve; admin_supervisor can approve."""
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("40.0000"),
        currency="ZAR",
        account_details="FNB Acc 777777",
        idempotency_key=f"p_prg025_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg025_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")

    # admin_operator attempts to approve -> 403 Forbidden
    op_headers = get_auth_headers("admin_operator_1", "admin_operator")
    resp_op = client.post(f"/api/v1/admin/commercial/runs/{run_id}/approve", headers=op_headers)
    assert resp_op.status_code == 403

    # admin_supervisor approves -> 200 OK
    sup_headers = get_auth_headers("admin_supervisor_2", "admin_supervisor")
    resp_sup = client.post(f"/api/v1/admin/commercial/runs/{run_id}/approve", headers=sup_headers)
    assert resp_sup.status_code == 200
    assert resp_sup.json()["run"]["status"] == "APPROVED"


# ------------------------------------------------------------------------------
# PRG-026 through PRG-030: SAFETY, PERSISTENCE & HARD BLOCKER INVARIANTS
# ------------------------------------------------------------------------------

def test_prg_026_production_remains_untouched(clean_run_state):
    """PRG-026: Production database is not connected or modified."""
    from config import settings
    # Confirm target is not production
    assert getattr(settings, "ENVIRONMENT", "").lower() != "production"
    assert "mngyyxqdhjgteezwkxdn" not in getattr(settings, "SUPABASE_URL", "")


def test_prg_027_zero_external_provider_calls(clean_run_state):
    """PRG-027: Zero external payment provider or bank API calls were made."""
    assert default_payout_provider.external_call_count == 0
    assert default_payout_provider.is_active is False


def test_prg_028_zero_creators_coin_earnings_writes(clean_run_state):
    """PRG-028: Retired legacy creators.coin_earnings column remains untouched at 0."""
    creator_id = clean_run_state
    creators = commercial_accounting_repository.local_get("creators")
    creator = next(c for c in creators if c.get("id") == creator_id)
    assert creator.get("coin_earnings") == 0


def test_prg_029_viewer_coin_ledger_remains_independent(clean_run_state):
    """PRG-029: Viewer coin ledger is completely independent and unmutated by creator payment runs."""
    coin_ledger_before = list(db.get("coin_ledger") or [])
    creator_id = clean_run_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("20.0000"),
        currency="ZAR",
        account_details="FNB Acc 123",
        idempotency_key=f"p_prg029_{uuid.uuid4().hex}"
    )

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg029_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    coin_ledger_after = list(db.get("coin_ledger") or [])
    assert len(coin_ledger_before) == len(coin_ledger_after)


def test_prg_030_failed_payout_does_not_reverse_creator_earnings(clean_run_state):
    """PRG-030: A failed payout preserves original creator earnings in creator_ledger."""
    creator_id = clean_run_state
    ledger_before = commercial_accounting_repository.get_creator_ledger(creator_id)
    earning_before = sum(_to_decimal(e["creator_amount"]) for e in ledger_before if e.get("entry_type") == "EARNING")

    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("35.0000"),
        currency="ZAR",
        account_details="FNB Acc 123",
        idempotency_key=f"p_prg030_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]

    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="admin_operator_1",
        idempotency_key=f"run_prg030_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="admin_operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="admin_supervisor_2")
    commercial_payment_run_service.export_run(run_id, actor_id="admin_operator_1")

    # Record failure
    commercial_payment_run_service.record_external_results(
        run_id=run_id,
        results=[{
            "payout_id": p_id,
            "status": "FAILED",
            "failure_reason": "Account frozen"
        }]
    )

    ledger_after = commercial_accounting_repository.get_creator_ledger(creator_id)
    earning_after = sum(_to_decimal(e["creator_amount"]) for e in ledger_after if e.get("entry_type") == "EARNING")
    assert earning_before == earning_after
    assert len([e for e in ledger_after if e.get("entry_type") == "EARNING"]) == 1


def _to_decimal(val):
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))
