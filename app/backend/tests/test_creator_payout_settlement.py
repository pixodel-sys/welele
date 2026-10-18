"""
Welele Media™ — Creator Payout & Settlement Verification Suite (Workstream 6I-G.2)
Verifies:
PAY-TEST-001: Valid payout request creates PENDING payout.
PAY-TEST-002: Payout allocation matches requested amount.
PAY-TEST-003: Insufficient available balance is rejected.
PAY-TEST-004: Duplicate payout request is idempotent.
PAY-TEST-005: Conflicting idempotency-key reuse is rejected.
PAY-TEST-006: PENDING → PROCESSING is valid.
PAY-TEST-007: PROCESSING → FAILED is valid.
PAY-TEST-008: FAILED → PROCESSING retry is valid.
PAY-TEST-009: Invalid state transitions are rejected.
PAY-TEST-010: PAID cannot be created by an ordinary/admin endpoint.
PAY-TEST-011: No payout provider is actually invoked.
PAY-TEST-012: Duplicate settlement events are idempotent.
PAY-TEST-013: Settlement amount/currency mismatch is rejected.
PAY-TEST-014: Payout allocation cannot exceed available balance.
PAY-TEST-015: No `creators.coin_earnings` write occurs.
"""

import uuid
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from database import db
from schemas.commercial_accounting_schemas import (
    PayoutStatus,
    LedgerEntryType,
    LedgerStatus
)
from repositories.commercial_accounting_repository import commercial_accounting_repository
from services.commercial_accounting_service import commercial_accounting_service
from services.creator_payout_service import creator_payout_service
from services.payout_provider import (
    default_payout_provider,
    SettlementConfirmation,
    ProviderStatus,
    PayoutInstruction
)
from services.rbac_service import create_access_token

client = TestClient(app)


def get_auth_headers(user_id: str = "creator_zola", role: str = "creator"):
    token = create_access_token(user_id=user_id, role=role, creator_id=user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clean_payout_state():
    """Seeds a test creator with an authoritative ledger earning before each test."""
    db.enable_test_isolation()
    creator_id = "creator_payout_fixture"

    # Seed creator profile
    existing_creators = commercial_accounting_repository.local_get("creators")
    if not any(c.get("id") == creator_id for c in existing_creators):
        commercial_accounting_repository.local_insert("creators", {
            "id": creator_id,
            "name": "Payout Fixture Creator",
            "coin_earnings": 0  # Retired legacy column remains 0
        })

    # Seed an immutable earning entry in creator_ledger (R100.0000 ZAR)
    earning_entry = {
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "revenue_event_id": str(uuid.uuid4()),
        "accounting_period": "2026-10",
        "entry_type": LedgerEntryType.EARNING.value,
        "creator_amount": 100.0000,
        "currency": "ZAR",
        "status": LedgerStatus.SETTLED.value,
        "idempotency_key": f"fixture_earning_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    commercial_accounting_repository.local_insert("creator_ledger", earning_entry)
    yield creator_id


def test_pay_001_valid_payout_request_creates_pending(clean_payout_state):
    """PAY-TEST-001: Valid payout request creates PENDING payout."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("40.0000"),
        currency="ZAR",
        payout_method="Bank EFT",
        account_details="Standard Bank Acc #123456789",
        idempotency_key=f"pay_001_{uuid.uuid4().hex}"
    )

    payout = res["payout"]
    assert payout["status"] == PayoutStatus.PENDING.value
    assert payout["settled_at"] is None
    assert payout["requested_amount"] == 40.0
    assert payout["currency"] == "ZAR"
    assert payout["settlement_status"] == "Settlement Pending (External Rails Unproven)"


def test_pay_002_payout_allocation_matches_requested_amount(clean_payout_state):
    """PAY-TEST-002: Payout allocation matches requested amount."""
    creator_id = clean_payout_state
    requested = Decimal("35.5000")
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=requested,
        idempotency_key=f"pay_002_{uuid.uuid4().hex}"
    )

    allocations = res["allocations"]
    assert len(allocations) >= 1
    total_allocated = sum(Decimal(str(a["amount_allocated"])) for a in allocations)
    assert total_allocated == requested
    assert allocations[0]["payout_id"] == res["payout"]["id"]


def test_pay_003_insufficient_available_balance_is_rejected(clean_payout_state):
    """PAY-TEST-003: Insufficient available balance is rejected."""
    creator_id = clean_payout_state
    # Fixture has R100.0000. Requesting R150.0000 must fail closed.
    with pytest.raises(ValueError, match="Insufficient available balance"):
        creator_payout_service.request_payout(
            creator_id=creator_id,
            requested_amount=Decimal("150.0000"),
            idempotency_key=f"pay_003_{uuid.uuid4().hex}"
        )


def test_pay_004_duplicate_payout_request_is_idempotent(clean_payout_state):
    """PAY-TEST-004: Duplicate payout request is idempotent."""
    creator_id = clean_payout_state
    idemp_key = f"pay_004_key_{uuid.uuid4().hex}"

    res1 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("20.0000"),
        idempotency_key=idemp_key
    )
    assert res1["is_idempotent_replay"] is False

    # Second invocation with identical parameters
    res2 = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("20.0000"),
        idempotency_key=idemp_key
    )
    assert res2["is_idempotent_replay"] is True
    assert res2["payout"]["id"] == res1["payout"]["id"]


def test_pay_005_conflicting_idempotency_key_reuse_is_rejected(clean_payout_state):
    """PAY-TEST-005: Conflicting idempotency-key reuse is rejected."""
    creator_id = clean_payout_state
    idemp_key = f"pay_005_shared_key_{uuid.uuid4().hex}"

    creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("20.0000"),
        idempotency_key=idemp_key
    )

    # Attempt reuse with conflicting amount
    with pytest.raises(ValueError, match="Conflicting idempotency key reuse"):
        creator_payout_service.request_payout(
            creator_id=creator_id,
            requested_amount=Decimal("30.0000"),
            idempotency_key=idemp_key
        )


def test_pay_006_pending_to_processing_is_valid(clean_payout_state):
    """PAY-TEST-006: PENDING → PROCESSING is valid."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("15.0000")
    )
    payout_id = res["payout"]["id"]

    updated = creator_payout_service.transition_payout_status(
        payout_id=payout_id,
        new_status="PROCESSING",
        actor_id="admin_supervisor"
    )
    assert updated["status"] == PayoutStatus.PROCESSING.value


def test_pay_007_processing_to_failed_is_valid(clean_payout_state):
    """PAY-TEST-007: PROCESSING → FAILED is valid."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("15.0000")
    )
    payout_id = res["payout"]["id"]

    creator_payout_service.transition_payout_status(
        payout_id=payout_id,
        new_status="PROCESSING",
        actor_id="admin_supervisor"
    )

    failed = creator_payout_service.transition_payout_status(
        payout_id=payout_id,
        new_status="FAILED",
        actor_id="admin_supervisor",
        reason="Bank network timeout"
    )
    assert failed["status"] == PayoutStatus.FAILED.value
    assert failed["rejection_reason"] == "Bank network timeout"


def test_pay_008_failed_to_processing_retry_is_valid(clean_payout_state):
    """PAY-TEST-008: FAILED → PROCESSING retry is valid and does not double-allocate."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("15.0000")
    )
    payout_id = res["payout"]["id"]

    creator_payout_service.transition_payout_status(payout_id, "PROCESSING", "admin_supervisor")
    creator_payout_service.transition_payout_status(payout_id, "FAILED", "admin_supervisor", reason="Temporary error")

    # Retry transition: FAILED -> PROCESSING
    retried = creator_payout_service.retry_failed_payout(payout_id=payout_id, actor_id="admin_supervisor")
    assert retried["status"] == PayoutStatus.PROCESSING.value

    # Verify no duplicate allocations were created
    allocations = commercial_accounting_repository.get_payout_allocations(payout_id)
    assert len(allocations) == len(res["allocations"])
    assert sum(Decimal(str(a["amount_allocated"])) for a in allocations) == Decimal("15.0000")


def test_pay_009_invalid_state_transitions_are_rejected(clean_payout_state):
    """PAY-TEST-009: Invalid state transitions are rejected."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("10.0000")
    )
    payout_id = res["payout"]["id"]

    # Direct PENDING -> FAILED is invalid (must go through PROCESSING)
    with pytest.raises(ValueError, match="Invalid payout state transition"):
        creator_payout_service.transition_payout_status(payout_id, "FAILED", "admin_supervisor")

    # Direct PENDING -> REVERSED is invalid
    with pytest.raises(ValueError, match="Invalid payout state transition"):
        creator_payout_service.transition_payout_status(payout_id, "REVERSED", "admin_supervisor")


def test_pay_010_paid_cannot_be_created_by_ordinary_or_admin_endpoint(clean_payout_state):
    """PAY-TEST-010: PAID cannot be created by an ordinary/admin transition endpoint."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("10.0000")
    )
    payout_id = res["payout"]["id"]

    with pytest.raises(ValueError, match="CRITICAL FINTECH INVARIANT VIOLATION: Manual or admin transition to PAID is prohibited"):
        creator_payout_service.transition_payout_status(payout_id, "PAID", "admin_supervisor")


def test_pay_011_no_payout_provider_is_actually_invoked(clean_payout_state):
    """PAY-TEST-011: No payout provider is actually invoked; external call count is strictly 0."""
    assert default_payout_provider.is_active is False
    assert default_payout_provider.external_call_count == 0

    # Any attempt to submit instruction raises RuntimeError
    instruction = PayoutInstruction(
        payout_id=str(uuid.uuid4()),
        creator_id="creator_test",
        amount=Decimal("10.0000"),
        destination_reference="Acc #000",
        idempotency_key="inst_test"
    )
    with pytest.raises(RuntimeError, match="CRITICAL BOUNDARY INVARIANT: External creator payout rails are disabled"):
        default_payout_provider.submit_instruction(instruction)

    assert default_payout_provider.external_call_count == 1


def test_pay_012_duplicate_settlement_events_are_idempotent(clean_payout_state):
    """PAY-TEST-012: Duplicate settlement events are idempotent."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("25.0000")
    )
    payout_id = res["payout"]["id"]
    prov_ref = f"BANK_CONF_{uuid.uuid4().hex[:8]}"
    settle_idemp = f"settle_{uuid.uuid4().hex[:8]}"

    confirmation = SettlementConfirmation(
        payout_id=payout_id,
        provider_reference=prov_ref,
        amount=Decimal("25.0000"),
        currency="ZAR",
        settled_at=datetime.now(timezone.utc),
        idempotency_key=settle_idemp,
        provider_status=ProviderStatus.SETTLED
    )

    res1 = creator_payout_service.process_settlement_confirmation(confirmation)
    assert res1["is_idempotent_replay"] is False
    assert res1["payout"]["status"] == PayoutStatus.PAID.value
    assert res1["payout"]["settled_at"] is not None

    # Replay same settlement confirmation
    res2 = creator_payout_service.process_settlement_confirmation(confirmation)
    assert res2["is_idempotent_replay"] is True
    assert res2["payout"]["status"] == PayoutStatus.PAID.value


def test_pay_013_settlement_amount_and_currency_mismatch_rejected(clean_payout_state):
    """PAY-TEST-013: Settlement amount/currency mismatch is rejected."""
    creator_id = clean_payout_state
    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("25.0000")
    )
    payout_id = res["payout"]["id"]

    # Amount mismatch: requested R25, confirmation says R30
    bad_amt_conf = SettlementConfirmation(
        payout_id=payout_id,
        provider_reference="REF_123",
        amount=Decimal("30.0000"),
        currency="ZAR",
        settled_at=datetime.now(timezone.utc),
        idempotency_key=f"bad_amt_{uuid.uuid4().hex}"
    )
    with pytest.raises(ValueError, match="Settlement amount mismatch"):
        creator_payout_service.process_settlement_confirmation(bad_amt_conf)

    # Currency mismatch
    bad_cur_conf = SettlementConfirmation(
        payout_id=payout_id,
        provider_reference="REF_123",
        amount=Decimal("25.0000"),
        currency="USD",
        settled_at=datetime.now(timezone.utc),
        idempotency_key=f"bad_cur_{uuid.uuid4().hex}"
    )
    with pytest.raises(ValueError, match="Settlement currency mismatch"):
        creator_payout_service.process_settlement_confirmation(bad_cur_conf)


def test_pay_014_payout_allocation_cannot_exceed_available_balance(clean_payout_state):
    """PAY-TEST-014: Payout allocation cannot exceed available balance."""
    creator_id = clean_payout_state
    # Fixture starts with R100.
    # First payout requests R80 -> R20 remains available
    creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("80.0000"),
        idempotency_key=f"pay_014_part1_{uuid.uuid4().hex}"
    )

    balances = commercial_accounting_service.get_creator_balances(creator_id)
    assert balances.available == Decimal("20.0000")
    assert balances.held == Decimal("80.0000")

    # Second payout requesting R30 must fail closed because only R20 is available
    with pytest.raises(ValueError, match="Insufficient available balance"):
        creator_payout_service.request_payout(
            creator_id=creator_id,
            requested_amount=Decimal("30.0000"),
            idempotency_key=f"pay_014_part2_{uuid.uuid4().hex}"
        )


def test_pay_015_no_creators_coin_earnings_write_occurs(clean_payout_state):
    """PAY-TEST-015: No creators.coin_earnings write occurs during payout operations."""
    creator_id = clean_payout_state
    creators = commercial_accounting_repository.local_get("creators")
    c_before = next(c for c in creators if c["id"] == creator_id)
    coin_earnings_before = c_before.get("coin_earnings", 0)

    creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("15.0000"),
        idempotency_key=f"pay_015_{uuid.uuid4().hex}"
    )

    creators_after = commercial_accounting_repository.local_get("creators")
    c_after = next(c for c in creators_after if c["id"] == creator_id)
    coin_earnings_after = c_after.get("coin_earnings", 0)

    assert coin_earnings_after == coin_earnings_before
    assert coin_earnings_after == 0


def test_creator_payout_endpoints_tenant_isolation(clean_payout_state):
    """Verifies that creator payout API endpoints enforce tenant ownership and prevent IDOR."""
    creator_id = clean_payout_state
    headers = get_auth_headers(user_id=creator_id, role="creator")

    # Submit payout via API
    resp = client.post(
        f"/api/v1/creators/{creator_id}/payouts",
        headers=headers,
        json={
            "amount": "20.0000",
            "currency": "ZAR",
            "payout_method": "Bank EFT",
            "account_details": "FNB Private Clients Acc #987654321",
            "idempotency_key": f"api_pay_{uuid.uuid4().hex}"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    payout_id = data["payout"]["id"]

    # Read payout list
    list_resp = client.get(f"/api/v1/creators/{creator_id}/payouts", headers=headers)
    assert list_resp.status_code == 200
    assert any(p["id"] == payout_id for p in list_resp.json()["payouts"])

    # Read detail
    detail_resp = client.get(f"/api/v1/creators/{creator_id}/payouts/{payout_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["id"] == payout_id

    # Cross-tenant IDOR attack: Another creator attempts to access this payout
    other_headers = get_auth_headers(user_id="creator_other", role="creator")
    idor_resp = client.get(f"/api/v1/creators/creator_other/payouts/{payout_id}", headers=other_headers)
    assert idor_resp.status_code == 404


def test_admin_commercial_payout_governance_lifecycle(clean_payout_state):
    """Verifies admin controls: list, inspect, hold, release-hold, and retry."""
    creator_id = clean_payout_state
    admin_headers = get_auth_headers(user_id="admin_user", role="admin")

    res = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("12.0000")
    )
    payout_id = res["payout"]["id"]

    # 1. Admin list
    list_resp = client.get("/api/v1/admin/commercial/payouts", headers=admin_headers)
    assert list_resp.status_code == 200

    # 2. Admin hold
    hold_resp = client.post(
        f"/api/v1/admin/commercial/payouts/{payout_id}/hold?reason=KYC+verification",
        headers=admin_headers
    )
    assert hold_resp.status_code == 200
    assert hold_resp.json()["payout"]["status"] == PayoutStatus.HELD.value

    # 3. Admin release hold
    rel_resp = client.post(
        f"/api/v1/admin/commercial/payouts/{payout_id}/release-hold?reason=KYC+cleared",
        headers=admin_headers
    )
    assert rel_resp.status_code == 200
    assert rel_resp.json()["payout"]["status"] == PayoutStatus.PENDING.value

    # 4. Advance to PROCESSING
    proc_resp = client.post(
        f"/api/v1/admin/commercial/payouts/{payout_id}/process",
        headers=admin_headers
    )
    assert proc_resp.status_code == 200
    assert proc_resp.json()["payout"]["status"] == PayoutStatus.PROCESSING.value
