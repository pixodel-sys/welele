"""
WELELE MEDIA™ — FNB Payments CSV Exporter
Milestone 6I-G.4.4: FNB Payments CSV Export Implementation

Authoritative implementation of the FNB Bulk Payment CSV structure based on the
official FNB Online Banking Enterprise Payment CSV Import Guide.

Export boundary:
- Deterministic CSV generation
- FNB Hash Total (pure mathematical function on account numbers + own account)
- Internal SHA-256 cryptographic audit fingerprint
- Strict field length, account type, amount, and reference validations
- Fail-closed on missing snapshot data
- Zero automated submission to FNB (Human-in-the-Loop export only)
"""

import csv
import io
import re
import hashlib
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional, Union


# ------------------------------------------------------------------------------
# 1. ACCOUNT TYPES
# ------------------------------------------------------------------------------

FNB_ACCOUNT_TYPES: Dict[str, str] = {
    "0": "0",  # Public Recipient
    "1": "1",  # Current / cheque / bond account
    "2": "2",  # Savings account
    "3": "3",  # Transmission account
    "4": "4",  # Bond Account
    "6": "6",  # Subscription Share Account
    "D": "D",  # eWallet Account (eWallet Pro)
    "S": "S",  # eWallet Account (Send Money)
    "F": "F",  # FNB Card Account
    "W": "W",  # WesBank
}

ACCOUNT_TYPE_ALIASES: Dict[str, str] = {
    "current": "1",
    "cheque": "1",
    "check": "1",
    "checking": "1",
    "current / cheque": "1",
    "current/cheque": "1",
    "savings": "2",
    "saving": "2",
    "transmission": "3",
    "bond": "4",
    "bond account": "4",
    "subscription share": "6",
    "subscription share account": "6",
    "subscription": "6",
    "ewallet": "D",
    "ewallet pro": "D",
    "ewallet account (ewallet pro)": "D",
    "send money": "S",
    "ewallet account (send money)": "S",
    "fnb card": "F",
    "fnb card account": "F",
    "card": "F",
    "wesbank": "W",
    "public recipient": "0",
    "public": "0",
}


def map_fnb_account_type(raw_type: Any) -> str:
    """
    Validates and maps account types to the official FNB single-character code.
    Rejects unsupported account types fail-closed.
    """
    if raw_type is None:
        raise ValueError("Account type is required and cannot be None.")
    s = str(raw_type).strip()
    if not s:
        raise ValueError("Account type is required and cannot be empty.")

    upper_s = s.upper()
    if upper_s in FNB_ACCOUNT_TYPES:
        return upper_s

    lower_s = s.lower()
    if lower_s in ACCOUNT_TYPE_ALIASES:
        return ACCOUNT_TYPE_ALIASES[lower_s]

    raise ValueError(
        f"Unsupported FNB account type '{raw_type}'. Supported account types: "
        f"0 (Public Recipient), 1 (Current/cheque), 2 (Savings), 3 (Transmission), "
        f"4 (Bond), 6 (Subscription Share), D (eWallet Pro), S (Send Money), "
        f"F (FNB Card), W (WesBank)."
    )


# ------------------------------------------------------------------------------
# 2. BRANCH CODES
# ------------------------------------------------------------------------------

def validate_fnb_branch_code(branch_code: Any, account_type: str) -> str:
    """
    Validates the recipient branch code against FNB rules.
    - Public Recipient (0) -> '0'
    - eWallet / Send Money (D or S) -> FNB universal branch code '250655' if empty
    - Normal recipient -> branch code or universal branch code (max 6 AN)
    """
    acc_type_code = map_fnb_account_type(account_type)
    if acc_type_code == "0":
        return "0"

    clean = str(branch_code).strip() if branch_code is not None else ""
    if acc_type_code in ("D", "S") and not clean:
        return "250655"

    if not clean:
        raise ValueError("Branch code cannot be empty for standard recipient accounts.")

    if len(clean) > 6:
        raise ValueError(f"Branch code '{clean}' exceeds maximum length of 6 characters.")

    # Must be alphanumeric
    if not clean.isalnum():
        raise ValueError(f"Branch code '{clean}' contains invalid non-alphanumeric characters.")

    return clean


# ------------------------------------------------------------------------------
# 3. AMOUNT RULES
# ------------------------------------------------------------------------------

def format_fnb_amount(amount: Union[Decimal, str, int, float]) -> str:
    """
    FNB Amount validation & formatting:
    - decimal separator = '.'
    - zero-only amounts invalid
    - maximum two decimal places
    - one decimal place is accepted (.1 -> 0.10, 12.1 -> 12.10)
    - two decimal places accepted (12.10 -> 12.10)
    - no decimal places accepted (12 -> 12.00)
    - more than two decimal places rejected (12.123 -> rejected)
    - max length: 11
    """
    if amount is None:
        raise ValueError("Amount cannot be None.")

    s = str(amount).strip()
    if not s:
        raise ValueError("Amount string cannot be empty.")

    # Handle strings starting with dot like '.1'
    if s.startswith("."):
        s = "0" + s
    elif s.startswith("-."):
        s = "-0." + s[2:]

    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Amount '{amount}' is not a valid numeric decimal.")

    if d <= Decimal("0"):
        raise ValueError(f"Amount '{d}' must be strictly greater than zero.")

    # Verify decimal places rule:
    # If the string contains a '.', check if there are non-zero digits past 2 decimal places
    if "." in s:
        parts = s.split(".")
        frac = parts[1]
        if len(frac) > 2:
            # Check if non-zero fraction extends beyond 2 decimal places
            significant_frac = frac.rstrip("0")
            if len(significant_frac) > 2:
                raise ValueError(
                    f"Amount '{amount}' has more than two decimal places ({len(significant_frac)} decimals detected)."
                )

    formatted = f"{d:.2f}"
    if len(formatted) > 11:
        raise ValueError(f"Amount '{formatted}' exceeds FNB maximum length of 11 characters.")

    return formatted


# ------------------------------------------------------------------------------
# 4. REFERENCES
# ------------------------------------------------------------------------------

# FNB allowed reference characters: alphanumeric, spaces, and safe punctuation -, _, ., /
FNB_REF_PATTERN = re.compile(r"^[A-Za-z0-9\s\-_\.\/]{1,20}$")


def validate_fnb_reference(ref: Any, field_name: str = "Reference") -> str:
    """
    Validates Own Reference and Recipient Reference against FNB rules:
    - Maximum 20 characters
    - Non-empty
    - Disallowed special characters fail closed
    """
    if ref is None:
        raise ValueError(f"{field_name} cannot be None.")
    s = str(ref).strip()
    if not s:
        raise ValueError(f"{field_name} cannot be empty or whitespace-only.")

    if len(s) > 20:
        raise ValueError(f"{field_name} '{s}' exceeds maximum length of 20 characters (length: {len(s)}).")

    if not FNB_REF_PATTERN.match(s):
        raise ValueError(
            f"{field_name} '{s}' contains invalid characters. "
            f"FNB supports only alphanumeric characters, spaces, and '-', '_', '.', '/'."
        )

    return s


# ------------------------------------------------------------------------------
# 5. FNB HASH TOTAL
# ------------------------------------------------------------------------------

def compute_fnb_hash_total(own_account: str, recipient_accounts: List[str]) -> str:
    """
    Pure mathematical implementation of the FNB Hash Total algorithm:
    1. Take every recipient account number in Column B.
    2. Add the digits of each recipient account number.
    3. Add the 11-digit Own Account Number from A3 once.
    4. Take the last 12 digits of the resulting total.
    5. Populate B3 with those 12 digits as a zero-padded string.

    This is an integrity control total, completely independent of SHA-256.
    """
    if own_account is None:
        raise ValueError("Own account cannot be None.")
    clean_own = "".join(c for c in str(own_account) if c.isdigit())
    if not clean_own:
        raise ValueError(f"Own account '{own_account}' must contain numeric digits for FNB Hash Total.")

    total = int(clean_own)
    for acc in recipient_accounts:
        if acc is None:
            raise ValueError("Recipient account cannot be None.")
        clean_acc = "".join(c for c in str(acc) if c.isdigit())
        if not clean_acc:
            raise ValueError(f"Recipient account '{acc}' must contain numeric digits for FNB Hash Total.")
        total += int(clean_acc)

    # Last 12 digits
    last_12 = total % (10**12)
    return f"{last_12:012d}"


# ------------------------------------------------------------------------------
# 6. ACTION DATE FORMATTING
# ------------------------------------------------------------------------------

def format_fnb_action_date(date_val: Union[datetime, date, str]) -> str:
    """
    Formats the payment action date to standard FNB DD-MM-YYYY (length 10).
    """
    if isinstance(date_val, datetime):
        return date_val.strftime("%d-%m-%Y")
    if isinstance(date_val, date):
        return date_val.strftime("%d-%m-%Y")

    s = str(date_val).strip()
    # YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        dt = datetime.strptime(s[:10], "%Y-%m-%d")
        return dt.strftime("%d-%m-%Y")

    # DD-MM-YYYY or DD/MM/YYYY
    if re.match(r"^\d{2}[-\/]\d{2}[-\/]\d{4}$", s):
        return s.replace("/", "-")

    raise ValueError(f"Invalid payment action date '{date_val}'. Expected DD-MM-YYYY or YYYY-MM-DD.")


# ------------------------------------------------------------------------------
# 7. DETERMINISTIC FNB PAYMENTS CSV GENERATOR
# ------------------------------------------------------------------------------

DEFAULT_WELELE_FNB_OWN_ACCOUNT = "62000000000"  # Welele Media nominal FNB disbursement account


def generate_fnb_payments_csv(
    run_reference: str,
    payment_run_id: str,
    period_end: Union[str, datetime, date],
    items: List[Dict[str, Any]],
    own_account: Optional[str] = None,
    payment_action_date: Optional[Union[str, datetime, date]] = None,
    own_reference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a deterministic, authoritative FNB Payments CSV file from approved payment run items.

    Enforces:
    - Immutable beneficiary snapshot fields only (fail-closed if missing)
    - Correct header lines:
        Row 1: BInSol - U ver 1.00,,,,,,
        Row 2: {action_date},,,,,,
        Row 3: {own_account},{hash_total},,,,,
        Row 4: Recipient Name,Recipient Account,Recipient Account Type,Branch Code,Amount,Own Reference,Recipient Reference
    - Exact 7-column tabular structure
    - Preserves string formatting for account numbers, branch codes, and leading zeroes
    - Computes FNB Hash Total (stored in artifact)
    - Computes SHA-256 digest of exact CSV bytes (stored in artifact)
    """
    if not items:
        raise ValueError("Cannot export empty payment run. At least one approved item is required.")

    # 1. Deterministic sort by payout_id
    sorted_items = sorted(items, key=lambda x: str(x.get("payout_id", "")))

    # 2. Check for duplicate payouts (invariance check)
    seen_payouts = set()
    for itm in sorted_items:
        p_id = str(itm.get("payout_id", ""))
        if p_id in seen_payouts:
            raise ValueError(f"Integrity failure: Payout '{p_id}' appears multiple times in payment run.")
        seen_payouts.add(p_id)

    # 3. Resolve Own Account & Action Date
    resolved_own_account = str(own_account or DEFAULT_WELELE_FNB_OWN_ACCOUNT).strip()
    if len(resolved_own_account) > 20:
        raise ValueError(f"Own account '{resolved_own_account}' exceeds FNB limit of 20 characters.")

    action_dt = payment_action_date or period_end
    formatted_action_date = format_fnb_action_date(action_dt)

    resolved_own_ref = str(own_reference or run_reference)[:20]
    validate_fnb_reference(resolved_own_ref, field_name="Own Reference")

    # 4. Validate all items and build row models
    recipient_accounts: List[str] = []
    processed_rows: List[Dict[str, str]] = []
    total_amount = Decimal("0.00")

    for itm in sorted_items:
        payout_id = str(itm.get("payout_id", ""))

        # Snapshots MUST be present (fail closed)
        beneficiary_name = itm.get("beneficiary_name_snapshot")
        if not beneficiary_name or not str(beneficiary_name).strip():
            raise ValueError(f"Missing beneficiary_name_snapshot for payout '{payout_id}'. Fail closed.")
        clean_name = str(beneficiary_name).strip()[:20]

        account_number = itm.get("account_number_snapshot")
        if not account_number or not str(account_number).strip():
            raise ValueError(f"Missing account_number_snapshot for payout '{payout_id}'. Fail closed.")
        clean_acc = str(account_number).strip()
        if len(clean_acc) > 20:
            raise ValueError(f"Account number '{clean_acc}' for payout '{payout_id}' exceeds 20 characters.")

        raw_acc_type = itm.get("account_type_snapshot")
        if not raw_acc_type or not str(raw_acc_type).strip():
            raise ValueError(f"Missing account_type_snapshot for payout '{payout_id}'. Fail closed.")
        fnb_acc_type = map_fnb_account_type(raw_acc_type)

        raw_branch = itm.get("branch_code_snapshot")
        fnb_branch = validate_fnb_branch_code(raw_branch, fnb_acc_type)

        raw_amount = itm.get("amount")
        if raw_amount is None:
            raise ValueError(f"Missing amount for payout '{payout_id}'. Fail closed.")
        fnb_amt = format_fnb_amount(raw_amount)
        total_amount += Decimal(fnb_amt)

        # Recipient Reference: snapshot or fallback, max 20, validated
        raw_rec_ref = itm.get("payment_reference_snapshot")
        if not raw_rec_ref or not str(raw_rec_ref).strip():
            # Canonical fallback from payout ID
            clean_rec_ref = f"WELELE-{payout_id[:8]}".upper()
        else:
            clean_rec_ref = str(raw_rec_ref).strip()[:20]

        # Ensure valid chars
        validate_fnb_reference(clean_rec_ref, field_name="Recipient Reference")

        recipient_accounts.append(clean_acc)
        processed_rows.append({
            "recipient_name": clean_name,
            "recipient_account": clean_acc,
            "recipient_account_type": fnb_acc_type,
            "branch_code": fnb_branch,
            "amount": fnb_amt,
            "own_reference": resolved_own_ref,
            "recipient_reference": clean_rec_ref,
            "payout_id": payout_id
        })

    # 5. Calculate FNB Hash Total
    fnb_hash_total = compute_fnb_hash_total(resolved_own_account, recipient_accounts)

    # 6. Build Deterministic CSV Output
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    # Row 1: Header / Template line (7 columns: col A has text, cols B-G empty)
    writer.writerow(["BInSol - U ver 1.00", "", "", "", "", "", ""])

    # Row 2: Action Date in A2 (cols B-G empty)
    writer.writerow([formatted_action_date, "", "", "", "", "", ""])

    # Row 3: Own Account in A3, Hash Total in B3 (cols C-G empty)
    writer.writerow([resolved_own_account, fnb_hash_total, "", "", "", "", ""])

    # Row 4: Column Headings
    writer.writerow([
        "Recipient Name",
        "Recipient Account",
        "Recipient Account Type",
        "Branch Code",
        "Amount",
        "Own Reference",
        "Recipient Reference"
    ])

    # Row 5+: Payment Transaction lines
    for r in processed_rows:
        writer.writerow([
            r["recipient_name"],
            r["recipient_account"],
            r["recipient_account_type"],
            r["branch_code"],
            r["amount"],
            r["own_reference"],
            r["recipient_reference"]
        ])

    csv_content = output.getvalue()
    csv_bytes = csv_content.encode("utf-8")
    sha256_hash = hashlib.sha256(csv_bytes).hexdigest()

    file_name = f"{run_reference}_FNB_Payments.csv"

    return {
        "run_reference": run_reference,
        "payment_run_id": payment_run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_name": file_name,
        "file_sha256": sha256_hash,
        "fnb_hash_total": fnb_hash_total,
        "payment_count": len(processed_rows),
        "total_amount": float(total_amount),
        "currency": "ZAR",
        "csv_content": csv_content,
        "own_account": resolved_own_account,
        "payment_action_date": formatted_action_date,
        "processed_rows": processed_rows
    }
