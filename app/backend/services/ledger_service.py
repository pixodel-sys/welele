"""
Welele Media™ — Pillar 3: Double-Entry Financial Ledger Service
Architecture Rules:
- Transactional core enforces strict double-entry ledger bookkeeping.
- Enforces atomic balance operations and idempotency key deduplication.
- All balance movements are immutable.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.ledger_repository import ledger_repository

class LedgerService:
    def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        return ledger_repository.get_or_create_wallet(user_id)

    def create_wallet_for_user(self, user_id: str, initial_coins: int = 25) -> Dict[str, Any]:
        return ledger_repository.get_or_create_wallet(user_id)

    def get_balance(self, user_id: str) -> Dict[str, int]:
        return ledger_repository.get_balance(user_id)

    def debit_coins(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str,
        idempotency_key: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return ledger_repository.debit_coins_atomic(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            description=description
        )

    def credit_coins(
        self,
        user_id: str,
        base_coins: int,
        bonus_coins: int = 0,
        transaction_type: str = "TOPUP_PURCHASE",
        reference_id: str = "",
        idempotency_key: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        return ledger_repository.credit_coins_atomic(
            user_id=user_id,
            base_coins=base_coins,
            bonus_coins=bonus_coins,
            transaction_type=transaction_type,
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            description=description
        )

    def unlock_episode(
        self,
        user_id: str,
        episode_id: str,
        story_id: str,
        unlock_method: str = "COINS",
        coin_price: int = 5,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return ledger_repository.unlock_episode(
            user_id=user_id,
            episode_id=episode_id,
            series_id=story_id,
            unlock_method=unlock_method,
            coin_price=coin_price,
            idempotency_key=idempotency_key
        )

    def get_ledger_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return ledger_repository.get_ledger_history(user_id=user_id, limit=limit)

ledger_service = LedgerService()
