"""
Welele Media™ — Append-Only Trust & Security Audit Service
Institutional Trust Infrastructure: Cryptographically linked, tamper-evident audit ledger
covering AUTH, IP, CONTENT, COMMERCE, EXPERIENCE, and SECURITY state transitions.
"""

import time
import json
import uuid
import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from repositories.base_repository import BaseRepository

GENESIS_BLOCK_HASH = "0" * 64

class AuditService(BaseRepository):
    _audit_lock = threading.RLock()

    def __init__(self):
        super().__init__()
        self._ensure_genesis()

    def _ensure_genesis(self):
        """Initializes genesis block in memory store if empty."""
        with self._audit_lock:
            existing = self.local_get("security_audit_ledger")
            if not existing:
                genesis_entry = {
                    "sequence_id": 1,
                    "event_id": "audit_genesis_000000",
                    "domain": "SECURITY",
                    "event_type": "trust_ledger.genesis",
                    "actor_id": "system_bootstrap",
                    "actor_role": "system",
                    "target_type": "system",
                    "target_id": "welele_trust_engine",
                    "before_state": {},
                    "after_state": {"status": "INITIALIZED", "engine": "Welele Trust Foundation v2.0"},
                    "metadata": {"source": "kernel", "chain": "mainnet"},
                    "payload_hash": hashlib.sha256(b"WELELE_GENESIS_PAYLOAD").hexdigest(),
                    "previous_hash": GENESIS_BLOCK_HASH,
                    "entry_hash": hashlib.sha256(f"{GENESIS_BLOCK_HASH}:WELELE_GENESIS_PAYLOAD".encode("utf-8")).hexdigest(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self.local_insert("security_audit_ledger", genesis_entry)

    def _compute_payload_hash(self, payload: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of structured JSON payload."""
        canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def _compute_entry_hash(
        self,
        previous_hash: str,
        sequence_id: int,
        domain: str,
        event_type: str,
        actor_id: str,
        timestamp: str,
        payload_hash: str
    ) -> str:
        """Calculates cryptographic block hash chaining to the preceding entry."""
        header_str = f"{previous_hash}|{sequence_id}|{domain}|{event_type}|{actor_id}|{timestamp}|{payload_hash}"
        return hashlib.sha256(header_str.encode("utf-8")).hexdigest()

    def record_trust_event(
        self,
        domain: str,                     # 'AUTH' | 'IP' | 'CONTENT' | 'COMMERCE' | 'EXPERIENCE' | 'SECURITY'
        event_type: str,                 # e.g. 'content.episode_submitted', 'auth.failed_login'
        actor_id: str,
        actor_role: str,
        target_type: str,
        target_id: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Appends an immutable, hash-chained trust record to the audit ledger.
        NO UPDATE OR DELETE CAPABILITIES EXIST.
        """
        with self._audit_lock:
            existing_chain = self.local_get("security_audit_ledger")
            last_entry = existing_chain[-1] if existing_chain else None
            prev_hash = last_entry["entry_hash"] if last_entry else GENESIS_BLOCK_HASH
            next_seq = len(existing_chain) + 1

            now_ts = datetime.now(timezone.utc).isoformat()
            event_id = f"aud_{uuid.uuid4().hex[:12]}"

            payload_data = {
                "before_state": before_state or {},
                "after_state": after_state or {},
                "metadata": metadata or {}
            }
            payload_hash = self._compute_payload_hash(payload_data)

            entry_hash = self._compute_entry_hash(
                previous_hash=prev_hash,
                sequence_id=next_seq,
                domain=domain.upper(),
                event_type=event_type,
                actor_id=actor_id,
                timestamp=now_ts,
                payload_hash=payload_hash
            )

            audit_entry = {
                "sequence_id": next_seq,
                "event_id": event_id,
                "domain": domain.upper(),
                "event_type": event_type,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "target_type": target_type,
                "target_id": target_id,
                "before_state": before_state or {},
                "after_state": after_state or {},
                "metadata": metadata or {},
                "payload_hash": payload_hash,
                "previous_hash": prev_hash,
                "entry_hash": entry_hash,
                "timestamp": now_ts
            }

            self.local_insert("security_audit_ledger", audit_entry)

            # Mirror to PostgreSQL Supabase if live
            if self.is_live:
                try:
                    self.get_table("security_audit_ledger").insert({
                        "event_id": event_id,
                        "domain": domain.upper(),
                        "event_type": event_type,
                        "actor_id": actor_id,
                        "actor_role": actor_role,
                        "target_type": target_type,
                        "target_id": target_id,
                        "payload_hash": payload_hash,
                        "previous_hash": prev_hash,
                        "entry_hash": entry_hash,
                        "details": payload_data,
                        "created_at": now_ts
                    }).execute()
                except Exception as e:
                    # Log fallback without breaking the operational pipeline
                    print(f"[AUDIT_WARNING] Supabase remote sync fallback: {e}")

            return audit_entry

    def list_audit_events(
        self,
        domain: Optional[str] = None,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves verified audit records with filtering in reverse chronological order."""
        with self._audit_lock:
            chain = list(self.local_get("security_audit_ledger"))
            
            filtered = chain
            if domain:
                filtered = [e for e in filtered if e.get("domain") == domain.upper()]
            if event_type:
                filtered = [e for e in filtered if e.get("event_type") == event_type]
            if actor_id:
                filtered = [e for e in filtered if e.get("actor_id") == actor_id]
            if target_id:
                filtered = [e for e in filtered if e.get("target_id") == target_id]

            # Return newest first
            return list(reversed(filtered))[:limit]

    def verify_audit_chain_integrity(self) -> Dict[str, Any]:
        """
        Traverses and cryptographically recalculates every block in the ledger.
        Detects any retroactive tampering, deleted records, or broken hash links.
        """
        with self._audit_lock:
            chain = self.local_get("security_audit_ledger")
            if not chain:
                return {"valid": False, "total_blocks": 0, "error": "Audit ledger is empty"}

            previous_hash = GENESIS_BLOCK_HASH
            for idx, entry in enumerate(chain):
                # 1. Verify sequence order
                expected_seq = idx + 1
                if entry.get("sequence_id") != expected_seq:
                    return {
                        "valid": False,
                        "broken_block_sequence": entry.get("sequence_id"),
                        "error": f"Sequence discontinuity: expected {expected_seq}, got {entry.get('sequence_id')}"
                    }

                # 2. Check previous hash continuity (except genesis)
                if idx > 0 and entry.get("previous_hash") != previous_hash:
                    return {
                        "valid": False,
                        "broken_block_sequence": entry.get("sequence_id"),
                        "event_id": entry.get("event_id"),
                        "error": f"Hash link broken at sequence {entry.get('sequence_id')}: expected {previous_hash}, got {entry.get('previous_hash')}"
                    }

                # 3. Recalculate payload hash
                payload_data = {
                    "before_state": entry.get("before_state", {}),
                    "after_state": entry.get("after_state", {}),
                    "metadata": entry.get("metadata", {})
                }
                computed_payload_hash = self._compute_payload_hash(payload_data)
                if idx > 0 and computed_payload_hash != entry.get("payload_hash"):
                    return {
                        "valid": False,
                        "broken_block_sequence": entry.get("sequence_id"),
                        "event_id": entry.get("event_id"),
                        "error": f"Payload tampering detected in block {entry.get('sequence_id')}"
                    }

                # 4. Recalculate entry block hash
                if idx > 0:
                    computed_entry_hash = self._compute_entry_hash(
                        previous_hash=entry.get("previous_hash"),
                        sequence_id=entry.get("sequence_id"),
                        domain=entry.get("domain"),
                        event_type=entry.get("event_type"),
                        actor_id=entry.get("actor_id"),
                        timestamp=entry.get("timestamp"),
                        payload_hash=computed_payload_hash
                    )
                    if computed_entry_hash != entry.get("entry_hash"):
                        return {
                            "valid": False,
                            "broken_block_sequence": entry.get("sequence_id"),
                            "event_id": entry.get("event_id"),
                            "error": f"Entry signature mismatch in block {entry.get('sequence_id')}"
                        }

                previous_hash = entry.get("entry_hash")

            return {
                "valid": True,
                "total_blocks": len(chain),
                "head_block_hash": previous_hash,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }

audit_service = AuditService()
