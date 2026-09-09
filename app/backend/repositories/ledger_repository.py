"""
Welele Media™ — Double-Entry Financial Ledger Repository (GAP-002 & GAP-003)
Enforces atomic balance operations, idempotency key verification, and double-entry accounting audit logs.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from .base_repository import BaseRepository

class LedgerRepository(BaseRepository):
    def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        wallets = self.local_get("wallets")
        wallet = next((w for w in wallets if w.get("user_id") == user_id), None)
        if not wallet:
            wallet = {
                "id": f"w_{uuid.uuid4().hex[:10]}",
                "user_id": user_id,
                "coin_balance": 100,
                "bonus_coins": 25,
                "lifetime_coins_purchased": 0,
                "lifetime_coins_spent": 0,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("wallets", wallet)

            # Record onboarding reward journal entry
            initial_entry = {
                "id": f"ledg_{uuid.uuid4().hex[:10]}",
                "wallet_id": wallet["id"],
                "user_id": user_id,
                "amount": 125,
                "balance_before": 0,
                "balance_after": 125,
                "transaction_type": "ONBOARDING_REWARD",
                "reference_id": "ref_welcome_bonus",
                "idempotency_key": f"idemp_onboard_{user_id}",
                "description": "Welcome onboarding coins (100 Base + 25 Bonus)",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("coin_ledger", initial_entry)
        return wallet

    def get_balance(self, user_id: str) -> Dict[str, int]:
        wallet = self.get_or_create_wallet(user_id)
        return {
            "coin_balance": wallet.get("coin_balance", 0),
            "bonus_coins": wallet.get("bonus_coins", 0),
            "total_usable_coins": wallet.get("coin_balance", 0) + wallet.get("bonus_coins", 0)
        }

    def debit_coins_atomic(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str,
        idempotency_key: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if amount <= 0:
            return False, "Debit amount must be greater than zero", None

        with self._lock:
            # Check idempotency key if provided
            if idempotency_key:
                ledger = self.local_get("coin_ledger")
                existing = next((l for l in ledger if l.get("idempotency_key") == idempotency_key), None)
                if existing:
                    return True, "Idempotent debit already executed", existing

            wallet = self.get_or_create_wallet(user_id)
            wallets = self.local_get("wallets")
            wallet = next((w for w in wallets if w.get("user_id") == user_id), wallet)

            current_base = wallet.get("coin_balance", 0)
            current_bonus = wallet.get("bonus_coins", 0)
            total_available = current_base + current_bonus

            if total_available < amount:
                return False, f"Insufficient balance (Required: {amount}, Available: {total_available})", None

            deduct_bonus = min(current_bonus, amount)
            deduct_base = amount - deduct_bonus

            new_bonus = current_bonus - deduct_bonus
            new_base = current_base - deduct_base
            new_total = new_base + new_bonus

            # Update wallet
            self.local_update("wallets", "id", wallet["id"], {
                "coin_balance": new_base,
                "bonus_coins": new_bonus,
                "lifetime_coins_spent": wallet.get("lifetime_coins_spent", 0) + amount,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

            # Create immutable double-entry ledger entry
            ledger_entry = {
                "id": f"ledg_{uuid.uuid4().hex[:10]}",
                "wallet_id": wallet["id"],
                "user_id": user_id,
                "amount": -amount,
                "balance_before": total_available,
                "balance_after": new_total,
                "transaction_type": transaction_type,
                "reference_id": reference_id,
                "idempotency_key": idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}",
                "description": description or f"Debited {amount} coins for {transaction_type}",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("coin_ledger", ledger_entry)

            return True, "Debit executed successfully", ledger_entry

    def credit_coins_atomic(
        self,
        user_id: str,
        base_coins: int,
        bonus_coins: int = 0,
        transaction_type: str = "TOPUP_PURCHASE",
        reference_id: str = "",
        idempotency_key: Optional[str] = None,
        description: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        total_credit = base_coins + bonus_coins
        if total_credit <= 0:
            return False, "Credit amount must be greater than zero", {}

        with self._lock:
            if idempotency_key:
                ledger = self.local_get("coin_ledger")
                existing = next((l for l in ledger if l.get("idempotency_key") == idempotency_key), None)
                if existing:
                    return True, "Idempotent credit already processed", existing

            wallet = self.get_or_create_wallet(user_id)
            wallets = self.local_get("wallets")
            wallet = next((w for w in wallets if w.get("user_id") == user_id), wallet)

            current_base = wallet.get("coin_balance", 0)
            current_bonus = wallet.get("bonus_coins", 0)
            total_before = current_base + current_bonus

            new_base = current_base + base_coins
            new_bonus = current_bonus + bonus_coins
            total_after = new_base + new_bonus

            self.local_update("wallets", "id", wallet["id"], {
                "coin_balance": new_base,
                "bonus_coins": new_bonus,
                "lifetime_coins_purchased": wallet.get("lifetime_coins_purchased", 0) + base_coins,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

            ledger_entry = {
                "id": f"ledg_{uuid.uuid4().hex[:10]}",
                "wallet_id": wallet["id"],
                "user_id": user_id,
                "amount": total_credit,
                "balance_before": total_before,
                "balance_after": total_after,
                "transaction_type": transaction_type,
                "reference_id": reference_id or f"ref_topup_{uuid.uuid4().hex[:8]}",
                "idempotency_key": idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}",
                "description": description or f"Credited {total_credit} coins",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("coin_ledger", ledger_entry)

            return True, "Credit executed successfully", ledger_entry

    def unlock_episode(
        self,
        user_id: str,
        episode_id: str,
        series_id: str,
        unlock_method: str = "COINS",
        coin_price: int = 5,
        idempotency_key: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        with self._lock:
            unlocks = self.local_get("unlocked_episodes")
            already = next((u for u in unlocks if u.get("user_id") == user_id and u.get("episode_id") == episode_id), None)
            if already:
                return True, "Episode is already unlocked", already

        if unlock_method == "COINS" and coin_price > 0:
            success, msg, _ = self.debit_coins_atomic(
                user_id=user_id,
                amount=coin_price,
                transaction_type="EPISODE_UNLOCK",
                reference_id=episode_id,
                idempotency_key=idempotency_key or f"idemp_unl_{user_id}_{episode_id}",
                description=f"Unlocked episode {episode_id} of series {series_id}"
            )
            if not success:
                return False, msg, None

        unlock_record = {
            "id": f"unl_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "episode_id": episode_id,
            "series_id": series_id,
            "unlock_method": unlock_method,
            "coins_spent": coin_price if unlock_method == "COINS" else 0,
            "unlocked_at": datetime.now(timezone.utc).isoformat()
        }

        with self._lock:
            self.local_insert("unlocked_episodes", unlock_record)

        return True, "Episode unlocked successfully", unlock_record

    def get_ledger_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        ledger = self.local_get("coin_ledger")
        user_entries = [e for e in ledger if e.get("user_id") == user_id]
        user_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_entries[:limit]

ledger_repository = LedgerRepository()
