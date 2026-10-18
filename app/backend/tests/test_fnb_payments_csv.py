"""
WELELE MEDIA™ — Milestone 6I-G.4.4 Test Suite
Authoritative FNB Payments CSV Export Verification (FNB-CSV-001 through FNB-CSV-030)
"""

import re
import csv
import io
import uuid
import hashlib
import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from schemas.commercial_accounting_schemas import (
    PaymentRunStatus,
    PaymentRunItemStatus,
    PayoutStatus
)
from repositories.commercial_accounting_repository import commercial_accounting_repository
from services.creator_payout_service import creator_payout_service
from services.commercial_payment_run_service import (
    commercial_payment_run_service,
    CommercialPaymentRunService
)
from services.fnb_payment_export_service import (
    generate_fnb_payments_csv,
    compute_fnb_hash_total,
    map_fnb_account_type,
    validate_fnb_branch_code,
    format_fnb_amount,
    validate_fnb_reference,
    format_fnb_action_date,
    FNB_ACCOUNT_TYPES
)


@pytest.fixture
def fnb_clean_state():
    """Sets up an isolated, clean test state for offline unit testing."""
    creator_id = f"creator_fnb_{uuid.uuid4().hex[:8]}"

    # Seed creator profile
    existing_creators = commercial_accounting_repository.local_get("creators")
    if not any(c.get("id") == creator_id for c in existing_creators):
        commercial_accounting_repository.local_insert("creators", {
            "id": creator_id,
            "name": "FNB Run Creator",
            "coin_earnings": 0
        })

    # Seed immutable ledger earnings
    earning_entry = {
        "id": str(uuid.uuid4()),
        "creator_id": creator_id,
        "revenue_event_id": str(uuid.uuid4()),
        "accounting_period": "2026-10",
        "entry_type": "EARNING",
        "creator_amount": 5000.0000,
        "currency": "ZAR",
        "status": "SETTLED",
        "idempotency_key": f"fixture_fnb_earning_{uuid.uuid4().hex[:12]}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    commercial_accounting_repository.local_insert("creator_ledger", earning_entry)
    yield creator_id


# ==============================================================================
# FNB-CSV-001: Correct column structure
# ==============================================================================

def test_fnb_csv_001_column_structure():
    """FNB-CSV-001: Correct 4-row header layout and 7-column tabular structure."""
    items = [{
        "payout_id": "p1",
        "beneficiary_name_snapshot": "Alice Wonder",
        "account_number_snapshot": "62001122334",
        "branch_code_snapshot": "250655",
        "account_type_snapshot": "Current",
        "amount": Decimal("150.00"),
        "payment_reference_snapshot": "WEL-ALICE-01"
    }]
    art = generate_fnb_payments_csv(
        run_reference="RUN-20261018-001",
        payment_run_id="run-001",
        period_end="2026-10-18",
        items=items,
        own_account="62000000000",
        payment_action_date="18-10-2026"
    )

    lines = [line for line in art["csv_content"].splitlines() if line]
    assert len(lines) == 5  # 4 header lines + 1 data line

    reader = csv.reader(lines)
    rows = list(reader)

    # Row 1: Template identifier
    assert rows[0][0] == "BInSol - U ver 1.00"
    assert len(rows[0]) == 7

    # Row 2: Action Date
    assert rows[1][0] == "18-10-2026"
    assert len(rows[1]) == 7

    # Row 3: Own Account & Hash Total
    assert rows[2][0] == "62000000000"
    assert len(rows[2][1]) == 12
    assert len(rows[2]) == 7

    # Row 4: Column Headings
    expected_headers = [
        "Recipient Name",
        "Recipient Account",
        "Recipient Account Type",
        "Branch Code",
        "Amount",
        "Own Reference",
        "Recipient Reference"
    ]
    assert rows[3] == expected_headers

    # Row 5: Transaction Data
    assert rows[4][0] == "Alice Wonder"
    assert rows[4][1] == "62001122334"
    assert rows[4][2] == "1"
    assert rows[4][3] == "250655"
    assert rows[4][4] == "150.00"
    assert rows[4][5] == "RUN-20261018-001"
    assert rows[4][6] == "WEL-ALICE-01"


# ==============================================================================
# FNB-CSV-002: Correct field lengths
# ==============================================================================

def test_fnb_csv_002_field_lengths():
    """FNB-CSV-002: Fields respect maximum FNB length constraints."""
    items = [{
        "payout_id": "p1",
        "beneficiary_name_snapshot": "A" * 25,  # Exceeds 20, exporter trims to 20
        "account_number_snapshot": "1" * 20,   # Exact 20
        "branch_code_snapshot": "123456",      # Exact 6
        "account_type_snapshot": "1",          # Exact 1
        "amount": Decimal("99999999.99"),      # Exact 11
        "payment_reference_snapshot": "R" * 20 # Exact 20
    }]
    art = generate_fnb_payments_csv(
        run_reference="R" * 20,
        payment_run_id="run-002",
        period_end="2026-10-18",
        items=items,
        own_account="9" * 20,
        payment_action_date="18-10-2026"
    )
    rows = list(csv.reader(art["csv_content"].splitlines()))
    data_row = rows[4]

    assert len(rows[1][0]) == 10  # Action Date
    assert len(rows[2][0]) <= 20  # Own Account
    assert len(rows[2][1]) == 12  # Hash Total
    assert len(data_row[0]) <= 20 # Recipient Name
    assert len(data_row[1]) <= 20 # Recipient Account
    assert len(data_row[2]) == 1  # Account Type
    assert len(data_row[3]) <= 6  # Branch Code
    assert len(data_row[4]) <= 11 # Amount
    assert len(data_row[5]) <= 20 # Own Reference
    assert len(data_row[6]) <= 20 # Recipient Reference


# ==============================================================================
# FNB-CSV-003: Correct account-type mappings
# ==============================================================================

def test_fnb_csv_003_account_type_mappings():
    """FNB-CSV-003: Official account types 0, 1, 2, 3, 4, 6, D, S, F, W supported; invalid rejected."""
    # Test valid mappings
    assert map_fnb_account_type("0") == "0"
    assert map_fnb_account_type("1") == "1"
    assert map_fnb_account_type("Current") == "1"
    assert map_fnb_account_type("Cheque") == "1"
    assert map_fnb_account_type("Savings") == "2"
    assert map_fnb_account_type("Transmission") == "3"
    assert map_fnb_account_type("Bond") == "4"
    assert map_fnb_account_type("Subscription Share") == "6"
    assert map_fnb_account_type("eWallet Pro") == "D"
    assert map_fnb_account_type("Send Money") == "S"
    assert map_fnb_account_type("FNB Card") == "F"
    assert map_fnb_account_type("WesBank") == "W"

    # Unsupported fail closed
    with pytest.raises(ValueError, match="Unsupported FNB account type"):
        map_fnb_account_type("CryptoWallet")

    with pytest.raises(ValueError, match="Unsupported FNB account type"):
        map_fnb_account_type("PayPal")


# ==============================================================================
# FNB-CSV-004: Correct branch-code handling
# ==============================================================================

def test_fnb_csv_004_branch_code_handling():
    """FNB-CSV-004: Branch code length <= 6, 0 for public recipient, 250655 for eWallet/Send Money."""
    assert validate_fnb_branch_code("051001", "Current") == "051001"
    assert validate_fnb_branch_code("999999", "Savings") == "999999"
    assert validate_fnb_branch_code("anything", "0") == "0"  # Public recipient forced to 0
    assert validate_fnb_branch_code("", "eWallet Pro") == "250655"  # Defaults to universal code
    assert validate_fnb_branch_code("", "Send Money") == "250655"

    with pytest.raises(ValueError, match="exceeds maximum length of 6 characters"):
        validate_fnb_branch_code("1234567", "Current")

    with pytest.raises(ValueError, match="Branch code cannot be empty"):
        validate_fnb_branch_code("", "Current")


# ==============================================================================
# FNB-CSV-005, 006, 007, 008, 009: Amount validation rules
# ==============================================================================

def test_fnb_csv_005_amount_zero_decimals():
    """FNB-CSV-005: Amount with zero decimals formatted with .00 (e.g. 12 -> 12.00)."""
    assert format_fnb_amount(12) == "12.00"
    assert format_fnb_amount("12") == "12.00"
    assert format_fnb_amount(Decimal("100")) == "100.00"


def test_fnb_csv_006_amount_one_decimal():
    """FNB-CSV-006: Amount with one decimal formatted with trailing zero (.1 -> 0.10, 12.1 -> 12.10)."""
    assert format_fnb_amount(".1") == "0.10"
    assert format_fnb_amount("0.1") == "0.10"
    assert format_fnb_amount("12.1") == "12.10"
    assert format_fnb_amount(Decimal("12.1")) == "12.10"


def test_fnb_csv_007_amount_two_decimals():
    """FNB-CSV-007: Amount with two decimals formatted exactly (12.10 -> 12.10, 0.10 -> 0.10)."""
    assert format_fnb_amount("12.10") == "12.10"
    assert format_fnb_amount("0.10") == "0.10"
    assert format_fnb_amount(Decimal("45.67")) == "45.67"


def test_fnb_csv_008_amount_gt_two_decimals_rejected():
    """FNB-CSV-008: Amount with >2 non-zero decimal places rejected fail-closed."""
    with pytest.raises(ValueError, match="more than two decimal places"):
        format_fnb_amount("12.123")

    with pytest.raises(ValueError, match="more than two decimal places"):
        format_fnb_amount("0.1001")


def test_fnb_csv_009_zero_or_negative_amount_rejected():
    """FNB-CSV-009: Zero or negative amount rejected fail-closed."""
    with pytest.raises(ValueError, match="must be strictly greater than zero"):
        format_fnb_amount("0")

    with pytest.raises(ValueError, match="must be strictly greater than zero"):
        format_fnb_amount("0.00")

    with pytest.raises(ValueError, match="must be strictly greater than zero"):
        format_fnb_amount("-10.00")


# ==============================================================================
# FNB-CSV-010: Leading-zero account number preserved
# ==============================================================================

def test_fnb_csv_010_leading_zero_account_number_preserved():
    """FNB-CSV-010: Account numbers with leading zeros are strictly preserved as strings."""
    items = [{
        "payout_id": "p1",
        "beneficiary_name_snapshot": "Bob Builder",
        "account_number_snapshot": "0123456789",  # Starts with 0!
        "branch_code_snapshot": "051001",        # Starts with 0!
        "account_type_snapshot": "Savings",
        "amount": Decimal("200.00"),
        "payment_reference_snapshot": "WEL-BOB-01"
    }]
    art = generate_fnb_payments_csv(
        run_reference="RUN-20261018-010",
        payment_run_id="run-010",
        period_end="2026-10-18",
        items=items,
        own_account="09876543210"  # Starts with 0!
    )
    rows = list(csv.reader(art["csv_content"].splitlines()))
    assert rows[2][0] == "09876543210"  # Own account preserved
    assert rows[4][1] == "0123456789"   # Recipient account preserved
    assert rows[4][3] == "051001"       # Branch code preserved


# ==============================================================================
# FNB-CSV-011 & 012: Reference validation
# ==============================================================================

def test_fnb_csv_011_reference_length_validation():
    """FNB-CSV-011: Reference max 20 chars; empty or >20 rejected."""
    assert validate_fnb_reference("A" * 20) == "A" * 20

    with pytest.raises(ValueError, match="exceeds maximum length of 20 characters"):
        validate_fnb_reference("A" * 21)

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_fnb_reference("")


def test_fnb_csv_012_invalid_reference_characters_rejected():
    """FNB-CSV-012: Characters outside [A-Za-z0-9 _.-/] rejected."""
    assert validate_fnb_reference("PAY-2026/10_01.A") == "PAY-2026/10_01.A"

    with pytest.raises(ValueError, match="contains invalid characters"):
        validate_fnb_reference("REF$MONEY")

    with pytest.raises(ValueError, match="contains invalid characters"):
        validate_fnb_reference("REF#123;DROP")


# ==============================================================================
# FNB-CSV-013 & 014: FNB Hash Total Algorithm & Determinism
# ==============================================================================

def test_fnb_csv_013_hash_total_algorithm_test_vectors():
    """FNB-CSV-013: Mathematical pure function test vectors for FNB Hash Total."""
    # Test vector 1:
    # Own: 100, Recipients: [200, 300] -> Sum = 600 -> "000000000600"
    ht1 = compute_fnb_hash_total(own_account="100", recipient_accounts=["200", "300"])
    assert ht1 == "000000000600"
    assert len(ht1) == 12

    # Test vector 2: Realistic South African accounts
    # Own: 62000000000 (FNB 11 digits)
    # Recipient 1: 62111111111
    # Recipient 2: 98765432101
    # Total = 62000000000 + 62111111111 + 98765432101 = 222876543212
    # Mod 10^12 = 222876543212 (12 digits)
    ht2 = compute_fnb_hash_total(
        own_account="62000000000",
        recipient_accounts=["62111111111", "98765432101"]
    )
    assert ht2 == "222876543212"
    assert len(ht2) == 12

    # Test vector 3: Wraparound / Last 12 digits (> 1 trillion)
    # Own: 900000000000, Recipient: 200000000000 -> Sum = 1100000000000 (13 digits)
    # Last 12 digits: 100000000000
    ht3 = compute_fnb_hash_total(
        own_account="900000000000",
        recipient_accounts=["200000000000"]
    )
    assert ht3 == "100000000000"
    assert len(ht3) == 12


def test_fnb_csv_014_hash_total_deterministic():
    """FNB-CSV-014: Same inputs produce identical hash total repeatedly."""
    own = "62890012345"
    accs = ["123456789", "987654321", "55555555555"]
    assert compute_fnb_hash_total(own, accs) == compute_fnb_hash_total(own, accs)


# ==============================================================================
# FNB-CSV-015 & 016: SHA-256 vs FNB Hash Total Independence
# ==============================================================================

def test_fnb_csv_015_sha256_deterministic():
    """FNB-CSV-015: SHA-256 byte digest is 100% deterministic."""
    items = [{
        "payout_id": "p1",
        "beneficiary_name_snapshot": "Deterministic Actor",
        "account_number_snapshot": "62001122334",
        "branch_code_snapshot": "250655",
        "account_type_snapshot": "Current",
        "amount": Decimal("100.00"),
        "payment_reference_snapshot": "REF-001"
    }]
    art1 = generate_fnb_payments_csv("RUN-DET-01", "run-1", "2026-10-18", items, own_account="62000000000")
    art2 = generate_fnb_payments_csv("RUN-DET-01", "run-1", "2026-10-18", items, own_account="62000000000")

    assert art1["csv_content"] == art2["csv_content"]
    assert art1["file_sha256"] == art2["file_sha256"]


def test_fnb_csv_016_fnb_hash_total_and_sha256_independently_stored():
    """FNB-CSV-016: FNB Hash Total (numeric 12) and SHA-256 (hex 64) are distinct and independently stored."""
    items = [{
        "payout_id": "p1",
        "beneficiary_name_snapshot": "Dual Hash Actor",
        "account_number_snapshot": "62001122334",
        "branch_code_snapshot": "250655",
        "account_type_snapshot": "Current",
        "amount": Decimal("100.00"),
        "payment_reference_snapshot": "REF-002"
    }]
    art = generate_fnb_payments_csv("RUN-DET-02", "run-2", "2026-10-18", items, own_account="62000000000")

    assert len(art["fnb_hash_total"]) == 12
    assert art["fnb_hash_total"].isdigit()

    assert len(art["file_sha256"]) == 64
    assert all(c in "0123456789abcdef" for c in art["file_sha256"])

    assert art["fnb_hash_total"] != art["file_sha256"]


# ==============================================================================
# FNB-CSV-017, 018, 019, 020: Payment Run Integrity & Payout Lifecycle
# ==============================================================================

def test_fnb_csv_017_approved_run_exports_successfully(fnb_clean_state):
    """FNB-CSV-017: Approved payment run exports to FNB CSV successfully."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("150.00"),
        currency="ZAR",
        account_details="FNB Acc 62001122334",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="supervisor_2")

    exp = commercial_payment_run_service.export_run(run_id, actor_id="operator_1", export_format="fnb_csv")
    assert exp["status"] == PaymentRunStatus.EXPORTED.value or "file_name" in exp
    assert exp["file_name"].endswith("_FNB_Payments.csv")
    assert len(exp["file_sha256"]) == 64
    assert len(exp["fnb_hash_total"]) == 12


def test_fnb_csv_018_unapproved_run_cannot_export(fnb_clean_state):
    """FNB-CSV-018: DRAFT or UNDER_REVIEW run cannot be exported."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.00"),
        currency="ZAR",
        account_details="FNB Acc 62001122334",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]

    # Try exporting in DRAFT
    with pytest.raises(ValueError, match="Status is 'DRAFT', expected 'APPROVED' or 'EXPORTED'"):
        commercial_payment_run_service.export_run(run_id, actor_id="operator_1")

    # Try exporting in UNDER_REVIEW
    commercial_payment_run_service.submit_for_review(run_id, actor_id="operator_1")
    with pytest.raises(ValueError, match="Status is 'UNDER_REVIEW', expected 'APPROVED' or 'EXPORTED'"):
        commercial_payment_run_service.export_run(run_id, actor_id="operator_1")


def test_fnb_csv_019_export_never_creates_paid_status(fnb_clean_state):
    """FNB-CSV-019: Exporting an FNB CSV never transitions payouts to PAID."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.00"),
        currency="ZAR",
        account_details="FNB Acc 62001122334",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="supervisor_2")

    commercial_payment_run_service.export_run(run_id, actor_id="operator_1")

    payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert payout["status"] != PayoutStatus.PAID.value
    assert payout["settled_at"] is None


def test_fnb_csv_020_export_transitions_pending_to_processing(fnb_clean_state):
    """FNB-CSV-020: Export transitions eligible PENDING payouts to PROCESSING."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.00"),
        currency="ZAR",
        account_details="FNB Acc 62001122334",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    p_id = p["payout"]["id"]
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p_id]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="supervisor_2")

    commercial_payment_run_service.export_run(run_id, actor_id="operator_1")

    payout = commercial_accounting_repository.get_payout_by_id(p_id)
    assert payout["status"] == PayoutStatus.PROCESSING.value


# ==============================================================================
# FNB-CSV-021 & 022: Snapshot Integrity & Fail Closed
# ==============================================================================

def test_fnb_csv_021_approved_beneficiary_snapshot_is_used(fnb_clean_state):
    """FNB-CSV-021: Export generates file strictly from approved item snapshots."""
    items = [{
        "payout_id": "p_snap_1",
        "beneficiary_name_snapshot": "Approved Beneficiary",
        "account_number_snapshot": "98765432101",
        "branch_code_snapshot": "051001",
        "account_type_snapshot": "Current",
        "amount": Decimal("250.00"),
        "payment_reference_snapshot": "WEL-SNAP-99"
    }]
    art = generate_fnb_payments_csv("RUN-SNAP", "run-s", "2026-10-18", items)
    rows = list(csv.reader(art["csv_content"].splitlines()))

    assert rows[4][0] == "Approved Beneficiary"
    assert rows[4][1] == "98765432101"
    assert rows[4][3] == "051001"
    assert rows[4][6] == "WEL-SNAP-99"


def test_fnb_csv_022_missing_beneficiary_snapshot_fails_closed():
    """FNB-CSV-022: Missing snapshot fields fail closed without partial export."""
    # Missing account number
    bad_items = [{
        "payout_id": "p_bad",
        "beneficiary_name_snapshot": "Missing Account",
        "account_number_snapshot": "",  # Empty!
        "branch_code_snapshot": "250655",
        "account_type_snapshot": "Current",
        "amount": Decimal("100.00")
    }]
    with pytest.raises(ValueError, match="Missing account_number_snapshot"):
        generate_fnb_payments_csv("RUN-FAIL", "run-f", "2026-10-18", bad_items)

    # Missing beneficiary name
    bad_items2 = [{
        "payout_id": "p_bad2",
        "beneficiary_name_snapshot": None,
        "account_number_snapshot": "123456789",
        "branch_code_snapshot": "250655",
        "account_type_snapshot": "Current",
        "amount": Decimal("100.00")
    }]
    with pytest.raises(ValueError, match="Missing beneficiary_name_snapshot"):
        generate_fnb_payments_csv("RUN-FAIL2", "run-f2", "2026-10-18", bad_items2)


# ==============================================================================
# FNB-CSV-023: Duplicate export behavior is controlled/idempotent
# ==============================================================================

def test_fnb_csv_023_duplicate_export_idempotency(fnb_clean_state):
    """FNB-CSV-023: Re-exporting an EXPORTED run returns identical artifact and hash."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.00"),
        currency="ZAR",
        account_details="FNB Acc 62001122334",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]
    commercial_payment_run_service.submit_for_review(run_id, actor_id="operator_1")
    commercial_payment_run_service.approve_run(run_id, approver_id="supervisor_2")

    exp1 = commercial_payment_run_service.export_run(run_id, actor_id="operator_1")
    exp2 = commercial_payment_run_service.export_run(run_id, actor_id="operator_1")

    assert exp1["csv_content"] == exp2["csv_content"]
    assert exp1["file_sha256"] == exp2["file_sha256"]
    assert exp1["fnb_hash_total"] == exp2["fnb_hash_total"]


# ==============================================================================
# FNB-CSV-024 & 025: Security & IDOR Protections
# ==============================================================================

def test_fnb_csv_024_creator_cannot_access_export():
    """FNB-CSV-024: Creators cannot access payment run export files (role isolation)."""
    from services.rbac_service import ROLE_PERMISSIONS
    creator_perms = ROLE_PERMISSIONS.get("creator", [])
    admin_operator_perms = ROLE_PERMISSIONS.get("admin_operator", [])
    finance_perms = ROLE_PERMISSIONS.get("finance", [])

    # Creator has no export permission
    assert "commercial:run:export" not in creator_perms
    assert "commercial:run:export" in admin_operator_perms
    assert "commercial:run:export" in finance_perms


def test_fnb_csv_025_account_numbers_masked_in_normal_reads(fnb_clean_state):
    """FNB-CSV-025: Account numbers are masked in standard read endpoints (******4321)."""
    creator_id = fnb_clean_state
    p = creator_payout_service.request_payout(
        creator_id=creator_id,
        requested_amount=Decimal("100.00"),
        currency="ZAR",
        account_details="FNB Acc 987654321",
        idempotency_key=f"p_{uuid.uuid4().hex}"
    )
    now = datetime.now(timezone.utc)
    res = commercial_payment_run_service.create_run(
        period_start=now - timedelta(days=7),
        period_end=now,
        currency="ZAR",
        created_by="operator_1",
        idempotency_key=f"run_{uuid.uuid4().hex}",
        payout_ids=[p["payout"]["id"]]
    )
    run_id = res["run"]["id"]

    # Read run view with masking
    run_view = commercial_payment_run_service.get_run(run_id, mask_sensitive=True)
    item_view = run_view["items"][0]
    assert item_view["account_number_snapshot"].startswith("*****")
    assert item_view["account_number_snapshot"].endswith("4321")


# ==============================================================================
# FNB-CSV-026 through 030: Exact Totals, Counts, and Invariants
# ==============================================================================

def test_fnb_csv_026_csv_byte_output_deterministic():
    """FNB-CSV-026: Given identical approved data, CSV bytes are 100% deterministic."""
    items = [
        {
            "payout_id": "p1",
            "beneficiary_name_snapshot": "Alice Wonder",
            "account_number_snapshot": "62001122334",
            "branch_code_snapshot": "250655",
            "account_type_snapshot": "Current",
            "amount": Decimal("100.00"),
            "payment_reference_snapshot": "REF-001"
        },
        {
            "payout_id": "p2",
            "beneficiary_name_snapshot": "Bob Builder",
            "account_number_snapshot": "62005566778",
            "branch_code_snapshot": "051001",
            "account_type_snapshot": "Savings",
            "amount": Decimal("200.00"),
            "payment_reference_snapshot": "REF-002"
        }
    ]
    art1 = generate_fnb_payments_csv("RUN-026", "run-026", "2026-10-18", items)
    art2 = generate_fnb_payments_csv("RUN-026", "run-026", "2026-10-18", items)

    assert art1["csv_content"].encode("utf-8") == art2["csv_content"].encode("utf-8")


def test_fnb_csv_027_total_csv_amount_equals_approved_run_total():
    """FNB-CSV-027: Total CSV amount equals approved run total amount."""
    items = [
        {"payout_id": "p1", "beneficiary_name_snapshot": "A", "account_number_snapshot": "111", "branch_code_snapshot": "250655", "account_type_snapshot": "1", "amount": Decimal("120.50"), "payment_reference_snapshot": "R1"},
        {"payout_id": "p2", "beneficiary_name_snapshot": "B", "account_number_snapshot": "222", "branch_code_snapshot": "250655", "account_type_snapshot": "2", "amount": Decimal("80.25"), "payment_reference_snapshot": "R2"}
    ]
    art = generate_fnb_payments_csv("RUN-027", "run-027", "2026-10-18", items)
    assert art["total_amount"] == 200.75

    rows = list(csv.reader(art["csv_content"].splitlines()))
    amounts_sum = sum(Decimal(r[4]) for r in rows[4:])
    assert amounts_sum == Decimal("200.75")


def test_fnb_csv_028_csv_payment_count_equals_approved_run_count():
    """FNB-CSV-028: CSV payment count equals approved run count."""
    items = [
        {"payout_id": f"p_{i}", "beneficiary_name_snapshot": f"Actor {i}", "account_number_snapshot": f"62000{i}", "branch_code_snapshot": "250655", "account_type_snapshot": "1", "amount": Decimal("50.00"), "payment_reference_snapshot": f"R{i}"}
        for i in range(5)
    ]
    art = generate_fnb_payments_csv("RUN-028", "run-028", "2026-10-18", items)
    assert art["payment_count"] == 5

    rows = list(csv.reader(art["csv_content"].splitlines()))
    assert len(rows[4:]) == 5


def test_fnb_csv_029_every_csv_row_maps_to_one_approved_payout():
    """FNB-CSV-029: Every CSV row maps to exactly one approved payout."""
    items = [
        {"payout_id": "p_alpha", "beneficiary_name_snapshot": "Alpha", "account_number_snapshot": "1001", "branch_code_snapshot": "250655", "account_type_snapshot": "1", "amount": Decimal("10.00"), "payment_reference_snapshot": "R-A"},
        {"payout_id": "p_beta", "beneficiary_name_snapshot": "Beta", "account_number_snapshot": "1002", "branch_code_snapshot": "250655", "account_type_snapshot": "2", "amount": Decimal("20.00"), "payment_reference_snapshot": "R-B"}
    ]
    art = generate_fnb_payments_csv("RUN-029", "run-029", "2026-10-18", items)
    rows = art["processed_rows"]
    assert len(rows) == 2
    assert rows[0]["payout_id"] == "p_alpha"
    assert rows[1]["payout_id"] == "p_beta"


def test_fnb_csv_030_no_payout_appears_twice():
    """FNB-CSV-030: No payout appears twice in an exported payment run."""
    dup_items = [
        {"payout_id": "p_dup", "beneficiary_name_snapshot": "Dup 1", "account_number_snapshot": "1001", "branch_code_snapshot": "250655", "account_type_snapshot": "1", "amount": Decimal("10.00")},
        {"payout_id": "p_dup", "beneficiary_name_snapshot": "Dup 2", "account_number_snapshot": "1001", "branch_code_snapshot": "250655", "account_type_snapshot": "1", "amount": Decimal("10.00")}
    ]
    with pytest.raises(ValueError, match="appears multiple times in payment run"):
        generate_fnb_payments_csv("RUN-030", "run-030", "2026-10-18", dup_items)
