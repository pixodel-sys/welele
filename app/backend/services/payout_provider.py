"""
Welele Media™ — Provider-Neutral Creator Payout Abstraction (Workstream 6I-G.2)
Defines the provider-neutral interface, instruction data contracts, and status models
for external settlement rails without activating or invoking any external providers.

CRITICAL INVARIANTS:
1. External settlement execution is DISABLED in staging and frozen in production.
2. External provider calls MUST BE 0.
3. No outbound calls to EFT, mobile money, 1Voucher, Capitec Pay, Paystack, Ozow, etc.
4. No simulated/fake provider responses.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    """Normalized provider-neutral transaction status."""
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class PayoutInstruction(BaseModel):
    """
    Provider-neutral instruction object containing the exact parameters
    required to submit a disbursement instruction to any future settlement provider.
    """
    payout_id: str = Field(..., description="Internal UUID of the creator_payouts record")
    creator_id: str = Field(..., description="Canonical ID of the creator receiving funds")
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Monetary disbursement amount in fiat")
    currency: str = Field(default="ZAR", description="Disbursement currency (ZAR)")
    destination_reference: str = Field(..., min_length=1, description="Provider-neutral destination account/reference")
    idempotency_key: str = Field(..., min_length=1, description="Idempotency key guaranteeing exactly-once instruction")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata and contract context")


class ProviderResult(BaseModel):
    """
    Provider-neutral outcome representation returned upon instruction submission
    or status query.
    """
    instruction_id: str
    provider_reference: Optional[str] = None
    status: ProviderStatus
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SettlementConfirmation(BaseModel):
    """
    Authoritative settlement evidence required to prove genuine external settlement
    before any payout can transition to PAID.
    """
    payout_id: str = Field(..., description="Internal UUID of the creator_payouts record")
    provider_reference: str = Field(..., min_length=1, description="Authoritative external transaction reference")
    amount: Decimal = Field(..., gt=Decimal("0.0000"), description="Confirmed settled monetary amount")
    currency: str = Field(default="ZAR", description="Confirmed settlement currency")
    settled_at: datetime = Field(..., description="Authoritative timestamp from settlement proof")
    idempotency_key: str = Field(..., min_length=1, description="Settlement event idempotency key")
    provider_status: ProviderStatus = Field(default=ProviderStatus.SETTLED, description="Provider outcome")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Audit and validation proof")


class PayoutProvider(ABC):
    """
    Abstract provider-neutral interface. Any concrete settlement adapter
    (future bank EFT, mobile money, etc.) must implement this interface.
    """

    @abstractmethod
    def submit_instruction(self, instruction: PayoutInstruction) -> ProviderResult:
        """Submits a payout instruction to the provider rail."""
        pass

    @abstractmethod
    def query_instruction(self, provider_reference: str) -> ProviderResult:
        """Queries the current status of an instruction on the provider rail."""
        pass

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Indicates whether this provider rail is actively enabled."""
        pass


class DisabledPayoutProvider(PayoutProvider):
    """
    Default provider-neutral adapter.
    Enforces the 6I-G.2 boundary: External settlement execution is DISABLED.
    Guarantees external payout provider calls MUST BE 0.
    """

    def __init__(self):
        self._call_count: int = 0

    @property
    def is_active(self) -> bool:
        return False

    @property
    def external_call_count(self) -> int:
        return self._call_count

    def submit_instruction(self, instruction: PayoutInstruction) -> ProviderResult:
        # Strict boundary guard: Never invoke external rails
        self._call_count += 1
        raise RuntimeError(
            "CRITICAL BOUNDARY INVARIANT: External creator payout rails are disabled in staging. "
            "No outbound provider invocation permitted."
        )

    def query_instruction(self, provider_reference: str) -> ProviderResult:
        self._call_count += 1
        raise RuntimeError(
            "CRITICAL BOUNDARY INVARIANT: External creator payout rails are disabled in staging. "
            "No outbound provider status query permitted."
        )


# Authoritative default provider instance (disabled by invariant)
default_payout_provider = DisabledPayoutProvider()
