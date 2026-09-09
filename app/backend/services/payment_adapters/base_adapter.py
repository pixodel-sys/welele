"""
Welele Media™ — Base Payment Provider Adapter Interface
Defines the normalization contract, signature verification, and standard payment event schema.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel

class NormalizedPaymentEvent(BaseModel):
    provider: str
    provider_transaction_id: str
    event_type: str
    amount_fiat: float
    currency: str
    user_id: str
    coins_grant: int
    target_id: Optional[str] = None
    target_type: Optional[str] = None # 'COINS', 'EPISODE_UNLOCK', 'PASS'
    raw_payload_hash: str
    signature_verified: bool
    status: str # 'SUCCESS', 'FAILED', 'PENDING'

class BasePaymentAdapter(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @abstractmethod
    def verify_signature(self, payload: bytes, signature_header: Optional[str]) -> bool:
        pass

    @abstractmethod
    def normalize_payload(self, raw_data: Dict[str, Any], signature_verified: bool) -> NormalizedPaymentEvent:
        pass
