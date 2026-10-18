"""
Welele Media™ — Commercial Accounting Integration & Invariant Tests (Workstream 6I-E)
Validates:
1. Contract Resolution (Model A, Model B, effective dates, expired/future versions, fail-closed).
2. Calculation (Gross, Deductions, Net Revenue, deductions > gross rejected, Model A 0%, Model B share).
3. Ledger (Append-only, single creation, idempotency, additive reversals/refunds/chargebacks).
4. Integration (Episode unlock, airtime monetary amount, gifts without invented entitlement, failed unlock).
5. Balance States (Earned vs Available vs Paid, pending payouts do not equal paid).
6. Security (Tenant isolation, authenticated earnings access).
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient

from main import app
from database import db
from schemas.commercial_accounting_schemas import (
    CommercialModel,
    AgreementStatus,
    RevenueEventSource,
    RevenueEventType,
    LedgerEntryType,
    LedgerStatus,
    PayoutStatus,
    DeductionType
)
from repositories.commercial_accounting_repository import commercial_accounting_repository
from services.commercial_accounting_service import commercial_accounting_service
from services.rbac_service import create_access_token

client = TestClient(app)


def get_auth_headers(creator_id: str = "creator_zola", role: str = "creator"):
    token = create_access_token(user_id=creator_id, role=role, creator_id=creator_id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. CONTRACT RESOLUTION TESTS
# ==============================================================================

def test_contract_resolution_model_b_valid():
    """Valid Model B series (Blood Ties) resolves successfully."""
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id, now)

    assert err is None
    assert agr is not None
    assert ver is not None
    assert agr["commercial_model"] == CommercialModel.MODEL_B.value
    assert Decimal(str(ver["creator_share_percentage"])) == Decimal("0.4000")
    assert Decimal(str(ver["welele_share_percentage"])) == Decimal("0.6000")


def test_contract_resolution_model_a_valid():
    """Valid Model A series (Queen of Jozi) resolves with default 0% creator share."""
    series_id = "story_queen_of_jozi"
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id, now)

    assert err is None
    assert agr is not None
    assert ver is not None
    assert agr["commercial_model"] == CommercialModel.MODEL_A.value
    assert Decimal(str(ver["creator_share_percentage"])) == Decimal("0.0000")
    assert Decimal(str(ver["welele_share_percentage"])) == Decimal("1.0000")


def test_contract_resolution_expired_version_rejected():
    """Expired contract version must be rejected when event occurred after effective_to."""
    series_id = f"series_expired_{uuid.uuid4().hex[:6]}"
    agr_id = str(uuid.uuid4())
    
    # Insert expired agreement
    commercial_accounting_repository.insert_commercial_agreement({
        "id": agr_id,
        "project_id": series_id,
        "series_id": series_id,
        "creator_id": "creator_test",
        "agreement_reference": f"AGR-EXP-{uuid.uuid4().hex[:4]}",
        "title": "Expired Agreement",
        "commercial_model": "MODEL_B",
        "status": "ACTIVE"
    })
    
    # Version active only in 2024
    commercial_accounting_repository.insert_agreement_version({
        "agreement_id": agr_id,
        "version_number": 1,
        "effective_from": "2024-01-01T00:00:00Z",
        "effective_to": "2024-12-31T23:59:59Z",
        "commercial_model": "MODEL_B",
        "creator_share_percentage": 0.4000,
        "welele_share_percentage": 0.6000
    })

    event_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id, event_time)
    assert ver is None
    assert "No effective contract version" in err


def test_contract_resolution_future_version_not_selected():
    """Future contract version is not selected before its effective_from date."""
    series_id = f"series_future_{uuid.uuid4().hex[:6]}"
    agr_id = str(uuid.uuid4())
    
    commercial_accounting_repository.insert_commercial_agreement({
        "id": agr_id,
        "project_id": series_id,
        "series_id": series_id,
        "creator_id": "creator_test",
        "agreement_reference": f"AGR-FUT-{uuid.uuid4().hex[:4]}",
        "title": "Future Agreement",
        "commercial_model": "MODEL_B",
        "status": "ACTIVE"
    })
    
    # Version effective in 2028
    commercial_accounting_repository.insert_agreement_version({
        "agreement_id": agr_id,
        "version_number": 1,
        "effective_from": "2028-01-01T00:00:00Z",
        "effective_to": None,
        "commercial_model": "MODEL_B",
        "creator_share_percentage": 0.5000,
        "welele_share_percentage": 0.5000
    })

    event_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id, event_time)
    assert ver is None
    assert "No effective contract version" in err


def test_contract_resolution_missing_agreement_fails_closed():
    """Missing agreement fails closed: returns None, None, error message."""
    series_id = f"series_non_existent_{uuid.uuid4().hex}"
    agr, ver, err = commercial_accounting_service.resolve_commercial_agreement_version(series_id)
    assert agr is None
    assert ver is None
    assert "No commercial agreement found" in err


# ==============================================================================
# 2. CALCULATION TESTS
# ==============================================================================

def test_calculation_model_a_default_zero():
    """Model A default creator share is 0.0000; creator amount is R0.00."""
    version = {
        "commercial_model": "MODEL_A",
        "creator_share_percentage": Decimal("0.0000"),
        "welele_share_percentage": Decimal("1.0000")
    }
    gross = Decimal("100.0000")
    deductions = [{"amount": Decimal("5.0000"), "deduction_type": "PAYMENT_PROCESSING_FEE"}]
    calc = commercial_accounting_service.calculate_creator_allocation(version, gross, deductions)

    assert calc["gross_revenue"] == Decimal("100.0000")
    assert calc["total_deductions"] == Decimal("5.0000")
    assert calc["net_revenue"] == Decimal("95.0000")
    assert calc["creator_amount"] == Decimal("0.0000")
    assert calc["welele_amount"] == Decimal("95.0000")


def test_calculation_model_a_contractual_override():
    """Model A with explicit contractual override calculates specified creator percentage."""
    version = {
        "commercial_model": "MODEL_A",
        "creator_share_percentage": Decimal("0.1500"),  # 15% override
        "welele_share_percentage": Decimal("0.8500")
    }
    gross = Decimal("100.0000")
    deductions = [{"amount": Decimal("10.0000")}]
    calc = commercial_accounting_service.calculate_creator_allocation(version, gross, deductions)

    assert calc["net_revenue"] == Decimal("90.0000")
    assert calc["creator_amount"] == Decimal("13.5000")  # 90 * 0.15 = 13.5
    assert calc["welele_amount"] == Decimal("76.5000")  # 90 * 0.85 = 76.5


def test_calculation_model_b_contractual_share():
    """Model B calculates creator share from contract schedule: Net Revenue * share%."""
    version = {
        "commercial_model": "MODEL_B",
        "creator_share_percentage": Decimal("0.4000"),
        "welele_share_percentage": Decimal("0.6000")
    }
    gross = Decimal("200.0000")
    deductions = [{"amount": Decimal("20.0000")}]
    calc = commercial_accounting_service.calculate_creator_allocation(version, gross, deductions)

    assert calc["gross_revenue"] == Decimal("200.0000")
    assert calc["total_deductions"] == Decimal("20.0000")
    assert calc["net_revenue"] == Decimal("180.0000")
    assert calc["creator_amount"] == Decimal("72.0000")  # 180 * 0.40 = 72
    assert calc["welele_amount"] == Decimal("108.0000")  # 180 * 0.60 = 108


def test_calculation_deductions_greater_than_gross_rejected():
    """Deductions exceeding gross revenue must raise ValueError and be rejected."""
    version = {
        "commercial_model": "MODEL_B",
        "creator_share_percentage": Decimal("0.4000"),
        "welele_share_percentage": Decimal("0.6000")
    }
    gross = Decimal("50.0000")
    deductions = [{"amount": Decimal("60.0000")}]  # 60 > 50

    with pytest.raises(ValueError, match="cannot exceed gross revenue"):
        commercial_accounting_service.calculate_creator_allocation(version, gross, deductions)


# ==============================================================================
# 3. LEDGER TESTS
# ==============================================================================

def test_ledger_earning_created_once_and_append_only():
    """Creator earning is appended to creator_ledger with correct audit details."""
    creator_id = f"creator_ledg_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"  # Model B (40%)
    idemp_key = f"idemp_test_ledg_{uuid.uuid4().hex}"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="tx_001",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("10.0000"),
        currency="ZAR",
        idempotency_key=idemp_key,
        creator_id_override=creator_id
    )

    assert res["is_idempotent_replay"] is False
    assert res["creator_earnings_credited"] is True
    ledger_entry = res["creator_ledger_entry"]
    assert ledger_entry["creator_id"] == creator_id
    assert ledger_entry["creator_amount"] == 4.0000  # 10.0 * 0.40
    assert ledger_entry["entry_type"] == LedgerEntryType.EARNING.value


def test_ledger_duplicate_event_does_not_duplicate_earning():
    """Replaying event with identical idempotency_key returns cached result without second ledger write."""
    creator_id = f"creator_idemp_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    idemp_key = f"idemp_replay_{uuid.uuid4().hex}"

    res1 = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="tx_002",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("10.0000"),
        currency="ZAR",
        idempotency_key=idemp_key,
        creator_id_override=creator_id
    )
    assert res1["is_idempotent_replay"] is False

    # Second call with same idempotency key
    res2 = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="tx_002",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("10.0000"),
        currency="ZAR",
        idempotency_key=idemp_key,
        creator_id_override=creator_id
    )
    assert res2["is_idempotent_replay"] is True

    # Confirm only one ledger entry exists
    ledger_entries = commercial_accounting_repository.get_creator_ledger(creator_id)
    assert len(ledger_entries) == 1


def test_ledger_reversals_refunds_and_chargebacks_are_additive():
    """Reversal, refund, and chargeback are separate additive entries referencing original ledger ID."""
    creator_id = f"creator_rev_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    idemp_key = f"idemp_orig_{uuid.uuid4().hex}"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="tx_003",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("20.0000"),
        currency="ZAR",
        idempotency_key=idemp_key,
        creator_id_override=creator_id
    )
    orig_entry = res["creator_ledger_entry"]
    orig_id = orig_entry["id"]

    # Record Additive Reversal
    rev_entry = commercial_accounting_service.record_adjustment(
        creator_id=creator_id,
        original_ledger_id=orig_id,
        adjustment_type=LedgerEntryType.REVERSAL,
        amount=Decimal("8.0000"),
        reason="Viewer chargeback adjustment",
        idempotency_key=f"rev_{orig_id}"
    )

    assert rev_entry["entry_type"] == LedgerEntryType.REVERSAL.value
    assert rev_entry["reversal_of_ledger_id"] == orig_id
    assert rev_entry["creator_amount"] == -8.0000

    # Verify both rows persist and original was NOT mutated
    all_entries = commercial_accounting_repository.get_creator_ledger(creator_id)
    assert len(all_entries) == 2
    orig_check = next(e for e in all_entries if e["id"] == orig_id)
    assert orig_check["creator_amount"] == 8.0000  # Intact!


# ==============================================================================
# 4. INTEGRATION & COMMERCIAL EVENT TESTS
# ==============================================================================

def test_integration_airtime_uses_actual_monetary_amount():
    """Airtime charge uses actual monetary consideration (amount_zar), not coins_equivalent."""
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    creator_id = f"creator_air_{uuid.uuid4().hex[:6]}"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.AIRTIME_UNLOCK,
        source_transaction_id="air_tx_001",
        event_type=RevenueEventType.AIRTIME_CHARGE,
        gross_amount=Decimal("15.5000"),  # R15.50 actual monetary airtime charge
        currency="ZAR",
        idempotency_key=f"air_idemp_{uuid.uuid4().hex}",
        metadata={"coins_equivalent": 10},
        creator_id_override=creator_id
    )

    assert res["creator_earnings_credited"] is True
    rev_event = res["revenue_event"]
    assert rev_event["gross_amount"] == 15.5000
    ledger_entry = res["creator_ledger_entry"]
    assert ledger_entry["gross_revenue"] == 15.5000
    assert ledger_entry["creator_amount"] == float(Decimal("15.5000") * Decimal("0.4000"))


def test_integration_gift_does_not_invent_entitlement():
    """Gifts record commercial event with accounting exception and do NOT invent creator entitlement."""
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    creator_id = f"creator_gift_{uuid.uuid4().hex[:6]}"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.GIFT,
        source_transaction_id="gift_tx_001",
        event_type=RevenueEventType.GIFT_SENT,
        gross_amount=Decimal("13.0000"),
        currency="ZAR",
        idempotency_key=f"gift_idemp_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    assert res["creator_earnings_credited"] is False
    assert res["unresolved_allocation"] is True
    assert res["creator_ledger_entry"] is None
    assert "Gift economics not established" in res["reason"]


def test_integration_missing_commercial_agreement_fails_closed():
    """Series without commercial agreement records revenue event with accounting exception and creates NO earnings."""
    series_id = f"series_no_contract_{uuid.uuid4().hex}"
    creator_id = "creator_orphan"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="orphan_tx_001",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("5.0000"),
        currency="ZAR",
        idempotency_key=f"orphan_idemp_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    assert res["creator_earnings_credited"] is False
    assert res["unresolved_allocation"] is True
    assert res["creator_ledger_entry"] is None


def test_integration_episode_unlock_creates_accounting_event():
    """Calling process_episode_unlock creates revenue event, deductions, and creator ledger earning."""
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"  # Model B (40%)
    episode_id = "ep_bt_1"
    viewer_id = f"viewer_{uuid.uuid4().hex[:6]}"
    tx_id = f"tx_unlock_{uuid.uuid4().hex[:8]}"

    res = commercial_accounting_service.process_episode_unlock(
        series_id=series_id,
        episode_id=episode_id,
        viewer_id=viewer_id,
        coin_price=5,
        source_transaction_id=tx_id
    )

    assert res["creator_earnings_credited"] is True
    assert res["revenue_event"] is not None
    # 5 coins = R0.6500 gross, 0% deduction (no assumed percentage), Net Revenue = R0.6500, 40% Creator Share = R0.2600
    ledger = res["creator_ledger_entry"]
    assert ledger["gross_revenue"] == 0.6500
    assert ledger["deductions"] == 0.0000
    assert ledger["net_revenue"] == 0.6500
    assert ledger["creator_amount"] == 0.2600
    assert ledger["currency"] == "ZAR"
    assert ledger["status"] == LedgerStatus.SETTLED.value


# ==============================================================================
# 5. BALANCE & PAYOUT TESTS
# ==============================================================================

def test_balance_earned_differs_from_available():
    """Earned balance differs from Available balance when funds are held or payouts requested."""
    creator_id = f"creator_bal_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"  # Model B (40%)

    # Earn R40.00 (from R100 gross)
    commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="bal_tx_001",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("100.0000"),
        currency="ZAR",
        idempotency_key=f"bal_idemp_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    initial_balances = commercial_accounting_service.get_creator_balances(creator_id)
    assert initial_balances.earned == Decimal("40.0000")
    assert initial_balances.available == Decimal("40.0000")
    assert initial_balances.paid == Decimal("0.0000")

    # Request R15.00 payout
    commercial_accounting_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("15.0000"),
        currency="ZAR",
        payout_method="Bank EFT",
        account_details="Standard Bank",
        idempotency_key=f"payout_test_{uuid.uuid4().hex}"
    )

    # After payout request, Available decreases to R25.00, Earned remains R40.00, Paid remains R0.00
    updated_balances = commercial_accounting_service.get_creator_balances(creator_id)
    assert updated_balances.earned == Decimal("40.0000")
    assert updated_balances.available == Decimal("25.0000")
    assert updated_balances.held == Decimal("15.0000")
    assert updated_balances.paid == Decimal("0.0000")  # Paid CANNOT be claimed without settlement!


def test_payout_request_does_not_mean_paid():
    """A creator payout record remains in PENDING status; external rails remain unproven."""
    creator_id = f"creator_paystatus_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"

    # Credit earnings
    commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="pay_tx_001",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("50.0000"),
        currency="ZAR",
        idempotency_key=f"pay_idemp_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    res = commercial_accounting_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("10.0000"),
        currency="ZAR",
        payout_method="Capitec Pay",
        account_details="Capitec Account",
        idempotency_key=f"payout_stat_{uuid.uuid4().hex}"
    )

    payout = res["payout"]
    assert payout["status"] == PayoutStatus.PENDING.value
    assert payout["settlement_status"] == "Settlement Pending (External Rails Unproven)"
    assert payout["settled_at"] is None
    assert payout["metadata"]["external_payout_activated"] is False


def test_reproducible_statements():
    """Creator statements are reproducible directly from accounting ledger records."""
    creator_id = f"creator_stmt_{uuid.uuid4().hex[:6]}"
    series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
    now = datetime(2026, 10, 15, tzinfo=timezone.utc)
    period = "2026-10"

    # Event 1: R50 gross -> R20 creator
    commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_001",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="stmt_tx_001",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("50.0000"),
        currency="ZAR",
        occurred_at=now,
        idempotency_key=f"stmt_idemp_1_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    # Event 2: R30 gross -> R12 creator
    commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id="ep_002",
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id="stmt_tx_002",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("30.0000"),
        currency="ZAR",
        occurred_at=now,
        idempotency_key=f"stmt_idemp_2_{uuid.uuid4().hex}",
        creator_id_override=creator_id
    )

    statement = commercial_accounting_service.generate_statement(creator_id, period)
    assert statement["gross_revenue"] == 80.0000
    assert statement["net_revenue"] == 80.0000
    assert statement["total_earnings"] == 32.0000
    assert statement["closing_balance"] == 32.0000
    assert len(statement["lines"]) == 2


# ==============================================================================
# 6. SECURITY & TENANT ISOLATION TESTS
# ==============================================================================

def test_creator_earnings_endpoint_isolated_to_authenticated_creator():
    """GET /api/creators/{creator_id}/earnings enforces 6H tenant isolation."""
    headers_zola = get_auth_headers("creator_zola")
    res_zola = client.get("/api/creators/creator_zola/earnings", headers=headers_zola)
    assert res_zola.status_code == 200
    data = res_zola.json()
    assert data["creator_id"] == "creator_zola"
    assert "available_balance" in data
    assert "earned_balance" in data

    # Attempt cross-tenant inspection by unauthorized creator
    headers_other = get_auth_headers("creator_other")
    res_forbidden = client.get("/api/creators/creator_zola/earnings", headers=headers_other)
    assert res_forbidden.status_code == 403
