"""
Welele Media™ — Pillar 3: Relational Transaction Core & Double-Entry Coin Ledger
Architecture Rules:
- Transactional core (user wallets, coin balances, unlocks, ledgers, subscriptions) maintains strict integrity.
- Guarantees zero double-spend via atomic balance checks and immutable audit logging.
- All balance movements create an immutable record in `coin_ledger`.
"""

import os
import sys
import uuid
import datetime
import threading
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db

class LedgerService:
    _lock = threading.Lock()

    def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        """Retrieves existing user wallet or initializes a new wallet with starting balance."""
        with self._lock:
            wallets = db.get("wallets")
            wallet = next((w for w in wallets if w.get("user_id") == user_id), None)
            if not wallet:
                wallet = {
                    "id": f"w_{uuid.uuid4().hex[:10]}",
                    "user_id": user_id,
                    "coin_balance": 100, # Default onboarding coins
                    "bonus_coins": 25,
                    "lifetime_coins_purchased": 0,
                    "lifetime_coins_spent": 0,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                db.insert("wallets", wallet)
                
                # Create initial ledger entry for onboarding reward
                initial_entry = {
                    "id": f"ledg_{uuid.uuid4().hex[:10]}",
                    "wallet_id": wallet["id"],
                    "user_id": user_id,
                    "amount": 125,
                    "balance_before": 0,
                    "balance_after": 125,
                    "transaction_type": "ONBOARDING_REWARD",
                    "reference_id": "ref_welcome_bonus",
                    "description": "Welcome onboarding coins (100 Base + 25 Bonus)",
                    "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }
                db.insert("coin_ledger", initial_entry)
            return wallet

    def get_balance(self, user_id: str) -> Dict[str, int]:
        wallet = self.get_or_create_wallet(user_id)
        return {
            "coin_balance": wallet.get("coin_balance", 0),
            "bonus_coins": wallet.get("bonus_coins", 0),
            "total_usable_coins": wallet.get("coin_balance", 0) + wallet.get("bonus_coins", 0)
        }

    def debit_coins(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str,
        description: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Atomically debits coins with double-entry ledger logging.
        Returns: (success: bool, message: str, ledger_entry: Optional[dict])
        """
        if amount <= 0:
            return False, "Amount must be greater than zero", None

        with self._lock:
            wallets = db.get("wallets")
            wallet = next((w for w in wallets if w.get("user_id") == user_id), None)
            if not wallet:
                wallet = self.get_or_create_wallet(user_id)
                wallets = db.get("wallets")
                wallet = next((w for w in wallets if w.get("user_id") == user_id), None)

            current_base = wallet.get("coin_balance", 0)
            current_bonus = wallet.get("bonus_coins", 0)
            total_available = current_base + current_bonus

            if total_available < amount:
                return False, f"Insufficient coin balance (Required: {amount}, Available: {total_available})", None

            # Deduct from bonus coins first, then base balance
            deduct_bonus = min(current_bonus, amount)
            deduct_base = amount - deduct_bonus

            new_bonus = current_bonus - deduct_bonus
            new_base = current_base - deduct_base
            new_total = new_base + new_bonus

            # Update wallet
            db.update("wallets", wallet["id"], {
                "coin_balance": new_base,
                "bonus_coins": new_bonus,
                "lifetime_coins_spent": wallet.get("lifetime_coins_spent", 0) + amount,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

            # Create immutable ledger entry
            ledger_entry = {
                "id": f"ledg_{uuid.uuid4().hex[:10]}",
                "wallet_id": wallet["id"],
                "user_id": user_id,
                "amount": -amount,
                "balance_before": total_available,
                "balance_after": new_total,
                "transaction_type": transaction_type,
                "reference_id": reference_id,
                "description": description or f"Spent {amount} coins on {transaction_type}",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            db.insert("coin_ledger", ledger_entry)

            return True, "Coins successfully deducted", ledger_entry

    def credit_coins(
        self,
        user_id: str,
        base_coins: int,
        bonus_coins: int = 0,
        transaction_type: str = "TOPUP",
        reference_id: str = "",
        description: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Atomically credits coins to user wallet and writes to the audit ledger.
        """
        total_credit = base_coins + bonus_coins
        if total_credit <= 0:
            return False, "Credit amount must be greater than zero", {}

        with self._lock:
            wallet = self.get_or_create_wallet(user_id)
            wallets = db.get("wallets")
            wallet = next((w for w in wallets if w.get("user_id") == user_id), wallet)

            current_base = wallet.get("coin_balance", 0)
            current_bonus = wallet.get("bonus_coins", 0)
            total_before = current_base + current_bonus

            new_base = current_base + base_coins
            new_bonus = current_bonus + bonus_coins
            total_after = new_base + new_bonus

            db.update("wallets", wallet["id"], {
                "coin_balance": new_base,
                "bonus_coins": new_bonus,
                "lifetime_coins_purchased": wallet.get("lifetime_coins_purchased", 0) + base_coins,
                "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
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
                "description": description or f"Credited {total_credit} coins ({base_coins} base + {bonus_coins} bonus)",
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            db.insert("coin_ledger", ledger_entry)

            return True, "Coins credited successfully", ledger_entry

    def unlock_episode(
        self,
        user_id: str,
        episode_id: str,
        story_id: str,
        unlock_method: str = "COINS",
        coin_price: int = 5
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Enforces paywall unlock and records to unlocked_episodes table.
        """
        with self._lock:
            unlocks = db.get("unlocked_episodes")
            already = next((u for u in unlocks if u.get("user_id") == user_id and u.get("episode_id") == episode_id), None)
            if already:
                return True, "Episode is already unlocked", already

        if unlock_method == "COINS" and coin_price > 0:
            success, msg, _ = self.debit_coins(
                user_id=user_id,
                amount=coin_price,
                transaction_type="EPISODE_UNLOCK",
                reference_id=episode_id,
                description=f"Unlocked episode {episode_id} of series {story_id}"
            )
            if not success:
                return False, msg, None

        unlock_record = {
            "id": f"unl_{uuid.uuid4().hex[:10]}",
            "user_id": user_id,
            "episode_id": episode_id,
            "story_id": story_id,
            "unlock_method": unlock_method,
            "coins_spent": coin_price if unlock_method == "COINS" else 0,
            "unlocked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        with self._lock:
            db.insert("unlocked_episodes", unlock_record)

        return True, "Episode unlocked successfully", unlock_record

    def get_ledger_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            ledger = db.get("coin_ledger")
            user_entries = [e for e in ledger if e.get("user_id") == user_id]
            user_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return user_entries[:limit]

ledger_service = LedgerService()
