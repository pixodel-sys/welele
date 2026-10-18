"""
Welele Media™ — 6I-F.1 Commercial Operations & Reconciliation Test Suite
Comprehensive coverage for:
1. Authoritative 3-Way Reconciliation (Viewer Debit ↔ Revenue Event ↔ Creator Ledger)
2. Fail-Closed Accounting Exception Handling & Controlled Reprocessing
3. Statement Generation, Idempotency & API Operationalization
4. Immutable Creator Ledger Reads & Authoritative Balances
5. Admin Operational Reconciliation Endpoints & Trust Audit Logs
6. Platform Payout Safety & Boundary Invariants
"""

import uuid
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from fastapi.testclient import TestClient

from main import app
from database import db
from schemas.commercial_accounting_schemas import (
    CommercialModel,
    RevenueEventSource,
    RevenueEventType,
    LedgerEntryType,
    LedgerStatus,
    PayoutStatus
)
from repositories.commercial_accounting_repository import commercial_accounting_repository
from services.commercial_accounting_service import commercial_accounting_service
from services.commercial_reconciliation_service import commercial_reconciliation_service
from services.rbac_service import create_access_token
from services.audit_service import audit_service

client = TestClient(app)


def get_admin_headers():
    token = create_access_token(user_id="admin_supervisor", role="admin")
    return {"Authorization": f"Bearer {token}"}


def get_creator_headers(creator_id: str = "creator_zola_rec"):
    token = create_access_token(user_id=creator_id, role="creator", creator_id=creator_id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. 3-WAY RECONCILIATION TESTS
# ==============================================================================

def test_three_way_reconciliation_matched_event():
    """Proves standard commercial event is verified and matched across the 3-way chain."""
    series_id = f"series_bt_rec_{uuid.uuid4().hex[:6]}"
    creator_id = f"creator_rec_{uuid.uuid4().hex[:6]}"
    agr_id = str(uuid.uuid4())
    ver_id = str(uuid.uuid4())

    # Set up agreement
    commercial_accounting_repository.insert_commercial_agreement({
        "id": agr_id,
        "project_id": series_id,
        "series_id": series_id,
        "creator_id": creator_id,
        "agreement_reference": f"AGR-REC-{uuid.uuid4().hex[:4]}",
        "title": "Reconciliation Test Agreement",
        "commercial_model": "MODEL_B",
        "status": "ACTIVE"
    })
    commercial_accounting_repository.insert_agreement_version({
        "id": ver_id,
        "agreement_id": agr_id,
        "version_number": 1,
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_to": None,
        "commercial_model": "MODEL_B",
        "creator_share_percentage": 0.4000,
        "welele_share_percentage": 0.6000
    })

    tx_id = f"tx_rec_{uuid.uuid4().hex[:6]}"
    idemp = f"idemp_rec_{uuid.uuid4().hex[:8]}"

    res = commercial_accounting_service.process_commercial_event(
        series_id=series_id,
        episode_id=str(uuid.uuid4()),
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id=tx_id,
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("0.6500"),
        currency="ZAR",
        idempotency_key=idemp
    )
    assert res["creator_earnings_credited"] is True

    # Run Reconciliation
    report = commercial_reconciliation_service.reconcile_chain(limit=100)
    assert report["status"] in ["BALANCED", "DISCREPANCIES_DETECTED"]
    assert report["summary"]["matched_count"] >= 1
    assert report["summary"]["reconciled_gross_zar"] >= 0.6500
    assert report["summary"]["reconciled_creator_earnings_zar"] >= 0.2600


def test_reconciliation_detects_unallocated_exception():
    """Proves uncontracted event is correctly identified as an accounting exception with zero earnings."""
    uncon_series_id = f"series_uncontracted_{uuid.uuid4().hex[:6]}"
    res = commercial_accounting_service.process_commercial_event(
        series_id=uncon_series_id,
        episode_id=None,
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id=f"tx_uncon_{uuid.uuid4().hex[:6]}",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("10.0000"),
        currency="ZAR",
        idempotency_key=f"uncon_rec_{uuid.uuid4().hex[:8]}"
    )
    assert res["unresolved_allocation"] is True
    assert res["creator_earnings_credited"] is False

    report = commercial_reconciliation_service.reconcile_chain(limit=100)
    matching_exc = next(
        (e for e in report["exceptions"] if e["revenue_event_id"] == res["revenue_event"]["id"]),
        None
    )
    assert matching_exc is not None
    assert "No commercial agreement found" in matching_exc["reason"]
    # Invariant: Discrepancies should NOT be raised for expected fail-closed exceptions
    assert not any(d.get("revenue_event_id") == res["revenue_event"]["id"] for d in report["discrepancies"])


def test_reconciliation_gift_event_exception_isolated():
    """Proves gift event records exception and reconciliation verifies 0 creator ledger rows."""
    gift_tx = f"tx_gift_{uuid.uuid4().hex[:6]}"
    gift_series_id = f"series_gift_{uuid.uuid4().hex[:6]}"
    agr_id = str(uuid.uuid4())
    commercial_accounting_repository.insert_commercial_agreement({
        "id": agr_id,
        "project_id": gift_series_id,
        "series_id": gift_series_id,
        "creator_id": "creator_gift_test",
        "agreement_reference": f"AGR-GIFT-{uuid.uuid4().hex[:4]}",
        "title": "Gift Series Agreement",
        "commercial_model": "MODEL_B",
        "status": "ACTIVE"
    })
    commercial_accounting_repository.insert_agreement_version({
        "agreement_id": agr_id,
        "version_number": 1,
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_to": None,
        "commercial_model": "MODEL_B",
        "creator_share_percentage": 0.4000,
        "welele_share_percentage": 0.6000
    })
    res = commercial_accounting_service.process_commercial_event(
        series_id=gift_series_id,
        episode_id=None,
        source=RevenueEventSource.GIFT,
        source_transaction_id=gift_tx,
        event_type=RevenueEventType.GIFT_SENT,
        gross_amount=Decimal("2.6000"),
        currency="ZAR",
        idempotency_key=f"gift_rec_{uuid.uuid4().hex[:8]}"
    )
    assert res["unresolved_allocation"] is True
    assert res["creator_earnings_credited"] is False

    report = commercial_reconciliation_service.reconcile_chain(limit=100)
    matching_gift = next(
        (e for e in report["exceptions"] if e["revenue_event_id"] == res["revenue_event"]["id"]),
        None
    )
    assert matching_gift is not None
    assert "Gift economics not established" in matching_gift["reason"]


def test_reconciliation_detects_unauthorized_earnings_on_exception():
    """Proves reconciliation flags CRITICAL discrepancy if an exception event somehow has a creator ledger row."""
    fake_rev_id = str(uuid.uuid4())
    # Create exception revenue event
    commercial_accounting_repository.insert_revenue_event({
        "id": fake_rev_id,
        "source": "EPISODE_UNLOCK",
        "source_transaction_id": "tx_bad_flow",
        "event_type": "COIN_UNLOCK",
        "gross_amount": 10.0000,
        "currency": "ZAR",
        "idempotency_key": f"bad_flow_{uuid.uuid4().hex[:8]}",
        "metadata": {
            "accounting_exception": True,
            "exception_reason": "Test corruption"
        }
    })
    # Illegitimately insert creator ledger entry for an exception
    commercial_accounting_repository.insert_creator_ledger_entry({
        "id": str(uuid.uuid4()),
        "creator_id": "creator_bad",
        "revenue_event_id": fake_rev_id,
        "entry_type": "EARNING",
        "gross_revenue": 10.0000,
        "deductions": 0.0000,
        "net_revenue": 10.0000,
        "allocation_percentage": 0.4000,
        "creator_amount": 4.0000,
        "currency": "ZAR",
        "accounting_period": "2026-10",
        "status": "SETTLED",
        "idempotency_key": f"bad_ledg_{uuid.uuid4().hex[:8]}"
    })

    report = commercial_reconciliation_service.reconcile_chain(limit=100)
    crit_disc = next(
        (d for d in report["discrepancies"] if d.get("revenue_event_id") == fake_rev_id),
        None
    )
    assert crit_disc is not None
    assert crit_disc["issue_type"] == "EXCEPTION_WITH_UNAUTHORIZED_EARNINGS"
    assert crit_disc["severity"] == "CRITICAL"


# ==============================================================================
# 2. EXCEPTION MANAGEMENT & CONTROLLED RE-PROCESSING
# ==============================================================================

def test_get_unresolved_exceptions():
    """Proves query of unresolved commercial exceptions."""
    uncon_series_id = f"series_uncon_query_{uuid.uuid4().hex[:6]}"
    commercial_accounting_service.process_commercial_event(
        series_id=uncon_series_id,
        episode_id=None,
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id=f"tx_query_{uuid.uuid4().hex[:6]}",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("5.0000"),
        currency="ZAR",
        idempotency_key=f"query_rec_{uuid.uuid4().hex[:8]}"
    )

    exceptions = commercial_reconciliation_service.get_unresolved_exceptions(series_id=uncon_series_id)
    assert len(exceptions) >= 1
    assert exceptions[0]["series_id"] == uncon_series_id
    assert exceptions[0]["gross_amount"] == 5.0000


def test_reprocess_exception_still_uncontracted_fails_closed():
    """Proves reprocessing an event whose series is still uncontracted fails closed."""
    uncon_series_id = f"series_still_uncon_{uuid.uuid4().hex[:6]}"
    res = commercial_accounting_service.process_commercial_event(
        series_id=uncon_series_id,
        episode_id=None,
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id=f"tx_still_{uuid.uuid4().hex[:6]}",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("1.3000"),
        currency="ZAR",
        idempotency_key=f"still_{uuid.uuid4().hex[:8]}"
    )
    rev_id = res["revenue_event"]["id"]

    reproc_res = commercial_reconciliation_service.reprocess_exception(rev_id)
    assert reproc_res["success"] is False
    assert reproc_res["resolved"] is False
    assert "Contract resolution failed" in reproc_res["reason"]


def test_reprocess_exception_succeeds_when_agreement_registered():
    """Proves reprocessing an exception succeeds additively once commercial agreement is established."""
    new_series_id = f"series_late_contract_{uuid.uuid4().hex[:6]}"
    creator_id = f"creator_late_{uuid.uuid4().hex[:6]}"

    # 1. Event occurs before contract exists -> recorded with exception
    res = commercial_accounting_service.process_commercial_event(
        series_id=new_series_id,
        episode_id=None,
        source=RevenueEventSource.EPISODE_UNLOCK,
        source_transaction_id=f"tx_late_{uuid.uuid4().hex[:6]}",
        event_type=RevenueEventType.COIN_UNLOCK,
        gross_amount=Decimal("2.6000"),
        currency="ZAR",
        idempotency_key=f"late_rec_{uuid.uuid4().hex[:8]}"
    )
    assert res["unresolved_allocation"] is True
    rev_id = res["revenue_event"]["id"]

    # 2. Legal contract executed retrospectively
    agr_id = str(uuid.uuid4())
    commercial_accounting_repository.insert_commercial_agreement({
        "id": agr_id,
        "project_id": new_series_id,
        "series_id": new_series_id,
        "creator_id": creator_id,
        "agreement_reference": f"AGR-LATE-{uuid.uuid4().hex[:4]}",
        "title": "Retroactive Agreement",
        "commercial_model": "MODEL_B",
        "status": "ACTIVE"
    })
    commercial_accounting_repository.insert_agreement_version({
        "agreement_id": agr_id,
        "version_number": 1,
        "effective_from": "2026-01-01T00:00:00Z",
        "effective_to": None,
        "commercial_model": "MODEL_B",
        "creator_share_percentage": 0.4000,
        "welele_share_percentage": 0.6000
    })

    # 3. Controlled reprocessing
    reproc_res = commercial_reconciliation_service.reprocess_exception(rev_id)
    assert reproc_res["success"] is True
    assert reproc_res["resolved"] is True
    assert reproc_res["creator_ledger_entry"]["creator_id"] == creator_id
    assert Decimal(str(reproc_res["creator_ledger_entry"]["creator_amount"])) == Decimal("1.0400") # 40% of 2.6000

    # 4. Check that revenue event metadata is updated
    updated_ev = commercial_accounting_repository.get_revenue_event_by_id(rev_id)
    assert updated_ev["metadata"]["exception_resolved"] is True


# ==============================================================================
# 3. STATEMENTS & STATEMENT APIS
# ==============================================================================

def test_statement_generation_and_idempotency():
    """Proves monthly statement generation accurately reflects persisted ledger entries and is idempotent."""
    creator_id = f"creator_stmt_{uuid.uuid4().hex[:6]}"
    series_id = f"series_stmt_{uuid.uuid4().hex[:6]}"

    # Add ledger entries for 2026-10
    commercial_accounting_repository.insert_creator_ledger_entry({
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "series_id": series_id,
        "entry_type": "EARNING",
        "gross_revenue": 5.0000,
        "deductions": 0.0000,
        "net_revenue": 5.0000,
        "allocation_percentage": 0.4000,
        "creator_amount": 2.0000,
        "currency": "ZAR",
        "accounting_period": "2026-10",
        "status": "SETTLED",
        "idempotency_key": f"stmt_ledg_1_{uuid.uuid4().hex[:8]}"
    })
    commercial_accounting_repository.insert_creator_ledger_entry({
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "series_id": series_id,
        "entry_type": "EARNING",
        "gross_revenue": 10.0000,
        "deductions": 0.0000,
        "net_revenue": 10.0000,
        "allocation_percentage": 0.4000,
        "creator_amount": 4.0000,
        "currency": "ZAR",
        "accounting_period": "2026-10",
        "status": "SETTLED",
        "idempotency_key": f"stmt_ledg_2_{uuid.uuid4().hex[:8]}"
    })

    # Generate Statement
    stmt1 = commercial_accounting_service.generate_statement(creator_id, "2026-10")
    assert stmt1["creator_id"] == creator_id
    assert stmt1["accounting_period"] == "2026-10"
    assert Decimal(str(stmt1["gross_revenue"])) == Decimal("15.0000")
    assert Decimal(str(stmt1["total_earnings"])) == Decimal("6.0000")
    assert Decimal(str(stmt1["closing_balance"])) == Decimal("6.0000")
    assert len(stmt1["lines"]) == 2

    # Idempotent re-generation: reuses existing statement ID
    stmt2 = commercial_accounting_service.generate_statement(creator_id, "2026-10")
    assert stmt2["id"] == stmt1["id"]
    assert stmt2["total_earnings"] == stmt1["total_earnings"]


def test_creator_statements_endpoints():
    """Proves GET and POST endpoints for creator statements."""
    creator_id = f"creator_api_{uuid.uuid4().hex[:6]}"
    headers = get_creator_headers(creator_id)

    # 1. Generate statement via API
    gen_res = client.post(
        f"/api/v1/creators/{creator_id}/statements/generate",
        json={"accounting_period": "2026-10", "currency": "ZAR"},
        headers=headers
    )
    assert gen_res.status_code == 200, f"Generate failed: {gen_res.text}"
    stmt_data = gen_res.json()["statement"]
    assert stmt_data["accounting_period"] == "2026-10"

    # 2. List statements
    list_res = client.get(f"/api/v1/creators/{creator_id}/statements", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total_statements"] >= 1

    # 3. Get statement detail
    detail_res = client.get(f"/api/v1/creators/{creator_id}/statements/2026-10", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["statement"]["accounting_period"] == "2026-10"


def test_creator_ledger_endpoint():
    """Proves GET /creators/{creator_id}/ledger returns immutable entries and authoritative balances."""
    creator_id = f"creator_ledg_api_{uuid.uuid4().hex[:6]}"
    headers = get_creator_headers(creator_id)

    # Insert test ledger row
    commercial_accounting_repository.insert_creator_ledger_entry({
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "entry_type": "EARNING",
        "gross_revenue": 5.0000,
        "deductions": 0.0000,
        "net_revenue": 5.0000,
        "allocation_percentage": 0.4000,
        "creator_amount": 2.0000,
        "currency": "ZAR",
        "accounting_period": "2026-10",
        "status": "SETTLED",
        "idempotency_key": f"ledg_api_{uuid.uuid4().hex[:8]}"
    })

    res = client.get(f"/api/v1/creators/{creator_id}/ledger", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_entries"] >= 1
    assert data["balances"]["earned"] >= 2.0000
    assert data["balances"]["paid"] == 0.0000 # Strict invariant


# ==============================================================================
# 4. ADMIN OPERATIONAL RECONCILIATION ENDPOINTS
# ==============================================================================

def test_admin_commercial_reconciliation_endpoint():
    """Proves GET /api/v1/admin/commercial/reconciliation returns live report."""
    headers = get_admin_headers()
    res = client.get("/api/v1/admin/commercial/reconciliation", headers=headers)
    assert res.status_code == 200, f"Reconciliation endpoint failed: {res.text}"
    report = res.json()
    assert "reconciliation_id" in report
    assert "status" in report
    assert "summary" in report
    assert report["summary"]["external_payout_rails_active"] is False


def test_admin_commercial_exceptions_endpoint():
    """Proves GET /api/v1/admin/commercial/exceptions lists unallocated commercial exceptions."""
    headers = get_admin_headers()
    res = client.get("/api/v1/admin/commercial/exceptions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_exceptions" in data
    assert "exceptions" in data


def test_admin_commercial_summary_endpoint():
    """Proves GET /api/v1/admin/commercial/summary returns platform financial KPIs."""
    headers = get_admin_headers()
    res = client.get("/api/v1/admin/commercial/summary", headers=headers)
    assert res.status_code == 200
    kpis = res.json()
    assert "total_gross_revenue_zar" in kpis
    assert "total_creator_earnings_zar" in kpis
    assert "external_creator_payouts_status" in kpis
    assert "production_status" in kpis
