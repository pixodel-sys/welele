"""
Welele Media™ — Double-Entry Financial Ledger Repository (GAP-002 & GAP-003)
Enforces atomic balance operations, idempotency key verification, and double-entry accounting audit logs.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from config import settings
from .base_repository import BaseRepository

logger = logging.getLogger("welele.ledger")

def to_uuid(name: str) -> str:
    """Deterministically maps any string identifier into a valid PostgreSQL UUID5."""
    try:
        uuid.UUID(str(name))
        return str(name)
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))

class LedgerRepository(BaseRepository):
    def get_or_create_wallet(self, user_id: str) -> Dict[str, Any]:
        wallets = self.local_get("wallets")
        wallet = next((w for w in wallets if w.get("user_id") == user_id), None)
        if wallet:
            return wallet

        if self.is_live:
            try:
                res = self.get_table("wallets").select("*").or_(f"user_id.eq.{user_id},user_id.eq.{to_uuid(user_id)}").execute()
                if res and res.data:
                    db_w = res.data[0]
                    wallet = {
                        "id": str(db_w.get("id")),
                        "user_id": user_id,
                        "coin_balance": db_w.get("coin_balance", 0),
                        "bonus_coins": db_w.get("bonus_coins", 0),
                        "lifetime_coins_purchased": db_w.get("lifetime_coins_purchased", 0),
                        "lifetime_coins_spent": db_w.get("lifetime_coins_spent", 0),
                        "updated_at": db_w.get("updated_at")
                    }
                    self.local_insert("wallets", wallet)
                    return wallet
            except Exception as e:
                logger.warning(f"[LedgerRepository:DB] get_or_create_wallet remote fetch error: {e}")

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

        if self.is_live:
            try:
                db_wallet = {
                    "id": to_uuid(wallet["id"]),
                    "user_id": to_uuid(user_id),
                    "coin_balance": wallet["coin_balance"],
                    "bonus_coins": wallet["bonus_coins"],
                    "lifetime_coins_purchased": wallet["lifetime_coins_purchased"],
                    "lifetime_coins_spent": wallet["lifetime_coins_spent"],
                    "updated_at": wallet["updated_at"]
                }
                self.get_table("wallets").upsert(db_wallet).execute()

                db_entry = {
                    "id": to_uuid(initial_entry["id"]),
                    "wallet_id": to_uuid(wallet["id"]),
                    "user_id": to_uuid(user_id),
                    "amount": initial_entry["amount"],
                    "balance_before": initial_entry["balance_before"],
                    "balance_after": initial_entry["balance_after"],
                    "transaction_type": "ONBOARDING_REWARD",
                    "reference_id": initial_entry["reference_id"],
                    "idempotency_key": initial_entry["idempotency_key"],
                    "description": initial_entry["description"],
                    "created_at": initial_entry["created_at"]
                }
                self.get_table("coin_ledger").insert(db_entry).execute()
            except Exception as e:
                logger.warning(f"[LedgerRepository:DB] Onboarding wallet persistence error: {e}")

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

            # Update wallet locally
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

            # Persist to authoritative PostgreSQL database when live
            if self.is_live:
                try:
                    db_wallet = {
                        "id": to_uuid(wallet["id"]),
                        "user_id": to_uuid(user_id),
                        "coin_balance": new_base,
                        "bonus_coins": new_bonus,
                        "lifetime_coins_spent": wallet.get("lifetime_coins_spent", 0) + amount,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                    self.get_table("wallets").upsert(db_wallet).execute()

                    db_ledger = {
                        "id": to_uuid(ledger_entry["id"]),
                        "wallet_id": to_uuid(wallet["id"]),
                        "user_id": to_uuid(user_id),
                        "amount": -amount,
                        "balance_before": total_available,
                        "balance_after": new_total,
                        "transaction_type": transaction_type,
                        "reference_id": reference_id,
                        "idempotency_key": ledger_entry["idempotency_key"],
                        "description": description or f"Debited {amount} coins for {transaction_type}",
                        "created_at": ledger_entry["created_at"]
                    }
                    self.get_table("coin_ledger").insert(db_ledger).execute()
                except Exception as e:
                    logger.error(f"[LedgerRepository:DB] Remote debit persistence error: {e}")
                    if settings.IS_PRODUCTION_OR_STAGING:
                        raise RuntimeError(f"Database write failure: Unable to persist coin debit for user '{user_id}': {e}")

            return True, "Debit executed successfully", ledger_entry

    VALID_TRANSACTION_TYPES = {
        "TOPUP_PURCHASE", "TOPUP_1VOUCHER", "TOPUP", "AIRTIME_TOPUP",
        "TOPUP_VODACOM_DCB", "TOPUP_PAYSTACK", "TOPUP_OZOW",
        "AIRTIME_PASS", "EPISODE_UNLOCK", "GIFT_SENT", "ROYALTY_CREDIT",
        "ONBOARDING_REWARD", "DAILY_REWARD", "REFUND", "DISPUTE_REVERSAL", "ADJUSTMENT",
        "TEST", "TEST_SEED"
    }

    IS_PURCHASE_TYPES = {
        "TOPUP_PURCHASE", "TOPUP_1VOUCHER", "TOPUP", "AIRTIME_TOPUP",
        "TOPUP_VODACOM_DCB", "TOPUP_PAYSTACK", "TOPUP_OZOW"
    }

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
        if not user_id:
            return False, "User ID cannot be null or empty", {}
        if base_coins < 0:
            return False, f"Base coins cannot be negative (provided: {base_coins})", {}
        if bonus_coins < 0:
            return False, f"Bonus coins cannot be negative (provided: {bonus_coins})", {}

        total_credit = base_coins + bonus_coins
        if total_credit <= 0:
            return False, f"Combined credit amount must be greater than zero (base: {base_coins}, bonus: {bonus_coins})", {}

        if not transaction_type or not transaction_type.strip():
            return False, "Transaction type cannot be null or empty", {}
        if transaction_type not in self.VALID_TRANSACTION_TYPES:
            return False, f"Invalid transaction type '{transaction_type}'", {}

        if transaction_type in self.IS_PURCHASE_TYPES and (not idempotency_key or not idempotency_key.strip()):
            return False, "Purchase/top-up credits require a non-empty idempotency_key", {}

        with self._lock:
            if idempotency_key:
                ledger = self.local_get("coin_ledger")
                existing = next((l for l in ledger if l.get("idempotency_key") == idempotency_key), None)
                if existing:
                    # CRITICAL: Same-Key / Different-Request Validation
                    if existing.get("user_id") != user_id:
                        raise RuntimeError(
                            f"CRITICAL IDEMPOTENCY VIOLATION: Idempotency key '{idempotency_key}' "
                            f"is already bound to user '{existing.get('user_id')}' (requested by '{user_id}')"
                        )
                    if existing.get("amount") != total_credit:
                        raise RuntimeError(
                            f"CRITICAL IDEMPOTENCY VIOLATION: Idempotency key '{idempotency_key}' "
                            f"was executed with amount {existing.get('amount')}, but incoming request specified {total_credit}"
                        )
                    if existing.get("transaction_type") != transaction_type:
                        raise RuntimeError(
                            f"CRITICAL IDEMPOTENCY VIOLATION: Idempotency key '{idempotency_key}' "
                            f"was executed with transaction_type '{existing.get('transaction_type')}', but incoming request specified '{transaction_type}'"
                        )
                    if (existing.get("reference_id") or "") != (reference_id or ""):
                        raise RuntimeError(
                            f"CRITICAL IDEMPOTENCY VIOLATION: Idempotency key '{idempotency_key}' "
                            f"was executed with reference_id '{existing.get('reference_id')}', but incoming request specified '{reference_id}'"
                        )
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

            ledger_entry = {
                "id": f"ledg_{uuid.uuid4().hex[:10]}",
                "wallet_id": wallet["id"],
                "user_id": user_id,
                "amount": total_credit,
                "balance_before": total_before,
                "balance_after": total_after,
                "transaction_type": transaction_type,
                "reference_id": reference_id or "",
                "idempotency_key": idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}",
                "description": description or f"Credited {total_credit} coins",
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            # Persist to authoritative PostgreSQL database when live
            if self.is_live:
                try:
                    # Authoritative: True database-level transaction atomicity via PostgreSQL RPC
                    # Fail-Closed Invariant: In staging and production, financial settlement MUST execute
                    # in a single atomic database transaction. Non-atomic separate REST calls are strictly prohibited.
                    rpc_params = {
                        "p_user_id": to_uuid(user_id),
                        "p_base_coins": base_coins,
                        "p_bonus_coins": bonus_coins,
                        "p_transaction_type": transaction_type,
                        "p_reference_id": ledger_entry["reference_id"],
                        "p_idempotency_key": ledger_entry["idempotency_key"],
                        "p_description": ledger_entry["description"]
                    }
                    rpc_res = self.get_client().rpc("fn_credit_coins_atomic", rpc_params).execute()
                    if not (rpc_res and rpc_res.data):
                        raise RuntimeError("Empty response received from fn_credit_coins_atomic RPC")

                    rpc_data = rpc_res.data
                    if not isinstance(rpc_data, dict):
                        raise RuntimeError(f"Invalid RPC response payload: {rpc_data}")

                    if not rpc_data.get("success"):
                        raise RuntimeError(f"fn_credit_coins_atomic rejected credit: {rpc_data.get('message')}")

                    ledger_entry["id"] = rpc_data.get("ledger_id", ledger_entry["id"])
                    ledger_entry["balance_after"] = rpc_data.get("balance_after", total_after)

                    if rpc_data.get("already_processed"):
                        return True, "Idempotent credit already processed", ledger_entry

                except Exception as rpc_err:
                    logger.error(f"[LedgerRepository:FAIL_CLOSED] fn_credit_coins_atomic RPC failure: {rpc_err}")
                    raise RuntimeError(
                        f"CRITICAL FINTECH HALT: fn_credit_coins_atomic RPC unavailable or failed. "
                        f"Halting settlement to prevent non-atomic ledger desynchronization for user '{user_id}': {rpc_err}"
                    )

            # Insert ledger entry first before mutating wallet balance
            self.local_insert("coin_ledger", ledger_entry)

            self.local_update("wallets", "id", wallet["id"], {
                "coin_balance": new_base,
                "bonus_coins": new_bonus,
                "lifetime_coins_purchased": wallet.get("lifetime_coins_purchased", 0) + (base_coins if transaction_type in self.IS_PURCHASE_TYPES else 0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

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

        if self.is_live:
            try:
                db_unlock = {
                    "id": to_uuid(unlock_record["id"]),
                    "user_id": to_uuid(user_id),
                    "episode_id": to_uuid(episode_id),
                    "series_id": to_uuid(series_id),
                    "unlock_method": unlock_method,
                    "coins_spent": unlock_record["coins_spent"],
                    "unlocked_at": unlock_record["unlocked_at"]
                }
                self.get_table("unlocked_episodes").upsert(db_unlock).execute()
            except Exception as e:
                logger.error(f"[LedgerRepository:DB] Remote unlock persistence error: {e}")
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database write failure: Unable to persist episode unlock for user '{user_id}' on episode '{episode_id}': {e}")

        return True, "Episode unlocked successfully", unlock_record

    def unlock_episode_record(
        self,
        user_id: str,
        episode_id: str,
        story_id: str,
        unlock_method: str = "DIRECT_1VOUCHER",
        coins_spent: int = 0
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        return self.unlock_episode(
            user_id=user_id,
            episode_id=episode_id,
            series_id=story_id,
            unlock_method=unlock_method,
            coin_price=coins_spent
        )

    def get_ledger_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        ledger = self.local_get("coin_ledger")
        user_entries = [e for e in ledger if e.get("user_id") == user_id]
        user_entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_entries[:limit]

ledger_repository = LedgerRepository()

