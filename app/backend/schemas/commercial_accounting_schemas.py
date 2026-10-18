"""
Welele Media™ — Commercial Accounting Schemas (Workstream 6I-E)
Defines domain data transfer objects, ledger models, contract resolution models,
and audit entities for the authoritative creator commercial accounting layer.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field


class CommercialModel(str, Enum):
    MODEL_A = "MODEL_A"  # Production-partnership: default 0% creator share during exclusive licence
    MODEL_B = "MODEL_B"  # Revenue-share: contractual % of Net Revenue (e.g. 40% creator / 60% Welele)


class AgreementStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"
    EXPIRED = "EXPIRED"


class RevenueEventSource(str, Enum):
    EPISODE_UNLOCK = "EPISODE_UNLOCK"
    AIRTIME_UNLOCK = "AIRTIME_UNLOCK"
    GIFT = "GIFT"
    SUBSCRIPTION_PASS = "SUBSCRIPTION_PASS"


class RevenueEventType(str, Enum):
    COIN_UNLOCK = "COIN_UNLOCK"
    AIRTIME_CHARGE = "AIRTIME_CHARGE"
    GIFT_SENT = "GIFT_SENT"


class SettlementStatus(str, Enum):
    SETTLED = "SETTLED"
    PENDING = "PENDING"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class DeductionType(str, Enum):
    PAYMENT_PROCESSING_FEE = "PAYMENT_PROCESSING_FEE"
    PLATFORM_FEE = "PLATFORM_FEE"
    STATUTORY_TAX = "STATUTORY_TAX"
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"


class LedgerEntryType(str, Enum):
    EARNING = "EARNING"
    ADJUSTMENT = "ADJUSTMENT"
    REVERSAL = "REVERSAL"
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"
    PAYOUT_HOLD = "PAYOUT_HOLD"
    PAYOUT_RELEASE = "PAYOUT_RELEASE"


class LedgerStatus(str, Enum):
    EARNED = "EARNED"
    SETTLED = "SETTLED"
    AVAILABLE = "AVAILABLE"
    PAID = "PAID"
    HELD = "HELD"
    DISPUTED = "DISPUTED"
    REVERSED = "REVERSED"


class PayoutStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"
    REVERSED = "REVERSED"
    HELD = "HELD"
    # Legacy backward-compatibility aliases
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


ALLOWED_PAYOUT_TRANSITIONS: Dict[str, List[str]] = {
    PayoutStatus.PENDING.value: [PayoutStatus.PROCESSING.value, PayoutStatus.HELD.value],
    PayoutStatus.HELD.value: [PayoutStatus.PENDING.value],
    PayoutStatus.PROCESSING.value: [PayoutStatus.PAID.value, PayoutStatus.FAILED.value, PayoutStatus.HELD.value],
    PayoutStatus.FAILED.value: [PayoutStatus.PROCESSING.value, PayoutStatus.HELD.value],
    PayoutStatus.PAID.value: [PayoutStatus.REVERSED.value],
    PayoutStatus.REVERSED.value: [],
}


# --- Commercial Agreement Models ---

class CommercialAgreementBase(BaseModel):
    project_id: Optional[str] = None
    series_id: Optional[str] = None
    creator_id: str
    agreement_reference: str
    title: str
    commercial_model: CommercialModel
    governing_law: str = "South Africa"
    status: AgreementStatus = AgreementStatus.ACTIVE
    agreement_signed_at: Optional[datetime] = None
    licence_start_at: Optional[datetime] = None
    commercial_release_at: Optional[datetime] = None
    licence_end_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommercialAgreementCreate(CommercialAgreementBase):
    pass


class CommercialAgreement(CommercialAgreementBase):
    id: str
    created_at: datetime
    updated_at: datetime


class CommercialAgreementVersionBase(BaseModel):
    agreement_id: str
    version_number: int
    effective_from: datetime
    effective_to: Optional[datetime] = None
    commercial_model: CommercialModel
    creator_share_percentage: Decimal = Field(..., ge=0, le=1)  # 0.0000 to 1.0000
    welele_share_percentage: Decimal = Field(..., ge=0, le=1)   # 0.0000 to 1.0000
    deduction_rules: List[Dict[str, Any]] = Field(default_factory=list)
    terms_metadata: Dict[str, Any] = Field(default_factory=dict)


class CommercialAgreementVersionCreate(CommercialAgreementVersionBase):
    pass


class CommercialAgreementVersion(CommercialAgreementVersionBase):
    id: str
    created_at: datetime


# --- Revenue Events & Deductions ---

class RevenueDeductionCreate(BaseModel):
    deduction_type: DeductionType
    amount: Decimal = Field(..., ge=0)
    currency: str = "ZAR"
    contractual_basis: str
    source_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RevenueDeduction(RevenueDeductionCreate):
    id: str
    revenue_event_id: str
    created_at: datetime


class RevenueEventCreate(BaseModel):
    project_id: Optional[str] = None
    series_id: Optional[str] = None
    episode_id: Optional[str] = None
    source: RevenueEventSource
    source_transaction_id: str
    provider_transaction_id: Optional[str] = None
    event_type: RevenueEventType
    gross_amount: Decimal = Field(..., ge=0)
    currency: str = "ZAR"
    occurred_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    settlement_status: SettlementStatus = SettlementStatus.SETTLED
    commercial_agreement_version_id: Optional[str] = None
    idempotency_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RevenueEvent(RevenueEventCreate):
    id: str
    created_at: datetime


# --- Creator Ledger ---

class CreatorLedgerEntryCreate(BaseModel):
    creator_id: str
    project_id: Optional[str] = None
    series_id: Optional[str] = None
    revenue_event_id: Optional[str] = None
    commercial_agreement_version_id: Optional[str] = None
    entry_type: LedgerEntryType
    gross_revenue: Decimal = Decimal("0.0000")
    deductions: Decimal = Decimal("0.0000")
    net_revenue: Decimal = Decimal("0.0000")
    allocation_percentage: Decimal = Decimal("0.0000")
    creator_amount: Decimal
    currency: str = "ZAR"
    accounting_period: str  # YYYY-MM
    status: LedgerStatus = LedgerStatus.SETTLED
    reversal_of_ledger_id: Optional[str] = None
    idempotency_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreatorLedgerEntry(CreatorLedgerEntryCreate):
    id: str
    created_at: datetime


# --- Creator Payouts (Accounting Object Only) ---

class CreatorPayoutRequest(BaseModel):
    creator_id: str
    amount_coins: Optional[int] = None
    amount_local: Decimal = Field(..., gt=0)
    currency: str = "ZAR"
    payout_method: str
    account_details: str
    idempotency_key: Optional[str] = None


class CreatorPayoutRecord(BaseModel):
    id: str
    creator_id: str
    requested_amount: Decimal
    currency: str
    payout_method: str
    account_details: str
    status: PayoutStatus = PayoutStatus.PENDING
    settlement_status: str = "Settlement Pending (External Rails Unproven)"
    idempotency_key: str
    requested_at: datetime
    settled_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# --- Statements & Balances ---

class CreatorBalances(BaseModel):
    creator_id: str
    currency: str = "ZAR"
    earned: Decimal = Decimal("0.0000")
    settled: Decimal = Decimal("0.0000")
    available: Decimal = Decimal("0.0000")
    paid: Decimal = Decimal("0.0000")
    held: Decimal = Decimal("0.0000")
    disputed: Decimal = Decimal("0.0000")
    reversed: Decimal = Decimal("0.0000")


class CreatorStatementLine(BaseModel):
    id: str
    statement_id: str
    ledger_entry_id: Optional[str] = None
    line_type: str
    project_id: Optional[str] = None
    series_id: Optional[str] = None
    description: str
    amount: Decimal
    created_at: datetime


class CreatorStatement(BaseModel):
    id: str
    creator_id: str
    accounting_period: str
    currency: str = "ZAR"
    opening_balance: Decimal
    gross_revenue: Decimal
    total_deductions: Decimal
    net_revenue: Decimal
    total_earnings: Decimal
    total_adjustments: Decimal
    total_payouts: Decimal
    closing_balance: Decimal
    status: str = "DRAFT"
    generated_at: datetime
    created_at: datetime
    lines: List[CreatorStatementLine] = Field(default_factory=list)


# --- 6I-G.2 Creator Payout & Settlement Models ---

class PayoutRequestCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Requested payout amount in ZAR")
    currency: str = Field(default="ZAR", description="Authoritative settlement currency (ZAR)")
    payout_method: str = Field(default="Bank EFT", description="Settlement destination method")
    account_details: str = Field(..., min_length=1, description="Destination reference/account identifier")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key")


class PayoutAllocationResponse(BaseModel):
    id: str
    payout_id: str
    ledger_entry_id: str
    amount_allocated: Decimal
    created_at: datetime


class PayoutResponse(BaseModel):
    id: str
    creator_id: str
    requested_amount: Decimal
    currency: str = "ZAR"
    payout_method: str
    account_details: str
    status: PayoutStatus
    settlement_status: str
    idempotency_key: str
    requested_at: datetime
    settled_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    allocations: List[PayoutAllocationResponse] = Field(default_factory=list)


class SettlementConfirmationRequest(BaseModel):
    payout_id: str
    provider_reference: str = Field(..., min_length=1)
    amount: Decimal
    currency: str = "ZAR"
    settled_at: Optional[datetime] = None
    idempotency_key: str = Field(..., min_length=1)
    provider_status: str = "SETTLED"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- 6I-G.4.2 Creator Payment Run Models ---

class PaymentRunStatus(str, Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    AWAITING_EXTERNAL_RESULT = "AWAITING_EXTERNAL_RESULT"
    RESULTS_RECORDED = "RESULTS_RECORDED"
    RECONCILED = "RECONCILED"
    CANCELLED = "CANCELLED"


class PaymentRunItemStatus(str, Enum):
    INCLUDED = "INCLUDED"
    HELD = "HELD"
    EXCLUDED = "EXCLUDED"
    PAID = "PAID"
    FAILED = "FAILED"


ALLOWED_PAYMENT_RUN_TRANSITIONS: Dict[str, List[str]] = {
    PaymentRunStatus.DRAFT.value: [PaymentRunStatus.UNDER_REVIEW.value, PaymentRunStatus.CANCELLED.value],
    PaymentRunStatus.UNDER_REVIEW.value: [PaymentRunStatus.APPROVED.value, PaymentRunStatus.DRAFT.value, PaymentRunStatus.CANCELLED.value],
    PaymentRunStatus.APPROVED.value: [PaymentRunStatus.EXPORTED.value, PaymentRunStatus.CANCELLED.value],
    PaymentRunStatus.EXPORTED.value: [PaymentRunStatus.AWAITING_EXTERNAL_RESULT.value, PaymentRunStatus.RESULTS_RECORDED.value],
    PaymentRunStatus.AWAITING_EXTERNAL_RESULT.value: [PaymentRunStatus.RESULTS_RECORDED.value],
    PaymentRunStatus.RESULTS_RECORDED.value: [PaymentRunStatus.RECONCILED.value],
    PaymentRunStatus.RECONCILED.value: [],
    PaymentRunStatus.CANCELLED.value: []
}


class PaymentRunCreate(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str = Field(default="ZAR")
    idempotency_key: Optional[str] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentRunItemResponse(BaseModel):
    id: str
    payment_run_id: str
    payout_id: str
    creator_id: str
    statement_id: Optional[str] = None
    amount: Decimal
    currency: str = "ZAR"
    status: PaymentRunItemStatus
    beneficiary_name_snapshot: str
    bank_name_snapshot: str
    account_number_snapshot: str  # Masked in ordinary responses
    branch_code_snapshot: str
    account_type_snapshot: str = "Current"
    payment_reference_snapshot: str
    external_payment_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentRunResponse(BaseModel):
    id: str
    run_reference: str
    period_start: datetime
    period_end: datetime
    currency: str = "ZAR"
    payout_count: int
    total_amount: Decimal
    status: PaymentRunStatus
    created_by: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    exported_at: Optional[datetime] = None
    export_file_hash_sha256: Optional[str] = None
    idempotency_key: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime


class PaymentRunDetailResponse(PaymentRunResponse):
    items: List[PaymentRunItemResponse] = Field(default_factory=list)


class ExternalResultItem(BaseModel):
    payout_id: str
    status: str = Field(..., description="SUCCESS or FAILED")
    external_payment_reference: Optional[str] = None
    failure_reason: Optional[str] = None
    settled_at: Optional[datetime] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = "ZAR"


class ExternalResultBatch(BaseModel):
    run_id: str
    results: List[ExternalResultItem]
    idempotency_key: Optional[str] = None


