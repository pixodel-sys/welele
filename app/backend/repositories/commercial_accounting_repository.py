"""
Welele Media™ — Commercial Accounting Repository (Workstream 6I-E)
Manages persistence and retrieval for:
- commercial_agreements & commercial_agreement_versions
- revenue_events & revenue_deductions
- creator_ledger (append-only)
- creator_statements & creator_statement_lines
- creator_payouts & creator_payout_allocations
Supports PostgreSQL (Supabase) in staging and local store for isolated test suites.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal

from config import settings
from .base_repository import BaseRepository

logger = logging.getLogger("welele.commercial_accounting")


def to_uuid(name: str) -> str:
    """Deterministically maps any string identifier into a valid PostgreSQL UUID5."""
    try:
        uuid.UUID(str(name))
        return str(name)
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))


class CommercialAccountingRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self._seed_default_commercial_contracts()

    def _seed_default_commercial_contracts(self):
        """Seeds canonical baseline agreements in local store for development and testing."""
        if self.is_live:
            return

        # Blood Ties - Model B (40% creator share)
        blood_ties_series_id = "c3e9302a-9809-51c2-b219-4e2a3079787f"
        queen_of_jozi_series_id = "df8e81cd-6da8-512e-aaf6-8625549079b0"

        agreements = self.local_get("commercial_agreements")
        if not any(a.get("agreement_reference") == "AGR-BT-2026-001" for a in agreements):
            agr_bt_id = "a0000000-0000-0000-0000-000000000001"
            agr_bt = {
                "id": agr_bt_id,
                "project_id": blood_ties_series_id,
                "series_id": blood_ties_series_id,
                "creator_id": "71de72b7-d88d-55fc-b5e8-bc3260ad8569",
                "agreement_reference": "AGR-BT-2026-001",
                "title": "Blood Ties Commercial Distribution Agreement",
                "commercial_model": "MODEL_B",
                "governing_law": "South Africa",
                "status": "ACTIVE",
                "agreement_signed_at": "2026-01-01T00:00:00Z",
                "licence_start_at": "2026-01-15T00:00:00Z",
                "commercial_release_at": "2026-02-01T00:00:00Z",
                "licence_end_at": "2028-02-01T00:00:00Z",
                "metadata": {"notes": "Canonical Model B reference agreement"},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("commercial_agreements", agr_bt)

            v_bt_id = "b0000000-0000-0000-0000-000000000001"
            v_bt = {
                "id": v_bt_id,
                "agreement_id": agr_bt_id,
                "version_number": 1,
                "effective_from": "2026-01-01T00:00:00Z",
                "effective_to": None,
                "commercial_model": "MODEL_B",
                "creator_share_percentage": 0.4000,
                "welele_share_percentage": 0.6000,
                "deduction_rules": [],
                "terms_metadata": {"schedule": "Schedule B-1: 40% Net Revenue"},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("commercial_agreement_versions", v_bt)

        # Queen of Jozi - Model A (Default 0% creator share during exclusive licence)
        if not any(a.get("agreement_reference") == "AGR-QJ-2026-001" for a in agreements):
            agr_qj_id = "a0000000-0000-0000-0000-000000000002"
            agr_qj = {
                "id": agr_qj_id,
                "project_id": queen_of_jozi_series_id,
                "series_id": queen_of_jozi_series_id,
                "creator_id": "71de72b7-d88d-55fc-b5e8-bc3260ad8569",
                "agreement_reference": "AGR-QJ-2026-001",
                "title": "Queen of Jozi Production Partnership Agreement",
                "commercial_model": "MODEL_A",
                "governing_law": "South Africa",
                "status": "ACTIVE",
                "agreement_signed_at": "2026-01-01T00:00:00Z",
                "licence_start_at": "2026-01-10T00:00:00Z",
                "commercial_release_at": "2026-01-20T00:00:00Z",
                "licence_end_at": "2027-01-20T00:00:00Z",
                "metadata": {"notes": "Canonical Model A reference agreement"},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("commercial_agreements", agr_qj)

            v_qj_id = "b0000000-0000-0000-0000-000000000002"
            v_qj = {
                "id": v_qj_id,
                "agreement_id": agr_qj_id,
                "version_number": 1,
                "effective_from": "2026-01-01T00:00:00Z",
                "effective_to": None,
                "commercial_model": "MODEL_A",
                "creator_share_percentage": 0.0000,
                "welele_share_percentage": 1.0000,
                "deduction_rules": [],
                "terms_metadata": {"schedule": "Schedule A: 0% creator revenue share during exclusive period"},
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("commercial_agreement_versions", v_qj)

    # --- Commercial Agreements & Versions ---

    def get_commercial_agreement_by_series(self, series_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active commercial agreement for a given series/project."""
        # 1. Live Supabase fetch when live
        if self.is_live:
            try:
                res = self.get_table("commercial_agreements").select("*").or_(
                    f"series_id.eq.{series_id},series_id.eq.{to_uuid(series_id)},project_id.eq.{series_id}"
                ).eq("status", "ACTIVE").limit(1).execute()
                if res and res.data:
                    record = res.data[0]
                    self.local_insert("commercial_agreements", record)
                    return record
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_commercial_agreement_by_series error: {e}")

        # 2. Local store check
        agreements = self.local_get("commercial_agreements")
        match = next((a for a in agreements if (a.get("series_id") == series_id or a.get("project_id") == series_id or a.get("series_id") == to_uuid(series_id)) and a.get("status") == "ACTIVE"), None)
        return match

    def get_commercial_agreement_by_id(self, agreement_id: str) -> Optional[Dict[str, Any]]:
        if self.is_live:
            try:
                res = self.get_table("commercial_agreements").select("*").eq("id", agreement_id).limit(1).execute()
                if res and res.data:
                    record = res.data[0]
                    self.local_insert("commercial_agreements", record)
                    return record
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_commercial_agreement_by_id error: {e}")

        agreements = self.local_get("commercial_agreements")
        match = next((a for a in agreements if a.get("id") == agreement_id), None)
        return match

    def insert_commercial_agreement(self, agreement: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in agreement:
            agreement["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        agreement.setdefault("created_at", now)
        agreement.setdefault("updated_at", now)
        self.local_insert("commercial_agreements", agreement)
        if self.is_live:
            try:
                self.get_table("commercial_agreements").upsert(agreement).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_commercial_agreement error: {e}")
        return agreement

    def get_agreement_versions(self, agreement_id: str) -> List[Dict[str, Any]]:
        if self.is_live:
            try:
                res = self.get_table("commercial_agreement_versions").select("*").eq("agreement_id", agreement_id).order("version_number").execute()
                if res and res.data:
                    versions = self.local_get("commercial_agreement_versions")
                    for v in res.data:
                        if not any(lv.get("id") == v.get("id") for lv in versions):
                            self.local_insert("commercial_agreement_versions", v)
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_agreement_versions error: {e}")

        versions = self.local_get("commercial_agreement_versions")
        local_matches = [v for v in versions if v.get("agreement_id") == agreement_id]
        if local_matches:
            return sorted(local_matches, key=lambda x: x.get("version_number", 1))
        return []

    def insert_agreement_version(self, version: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in version:
            version["id"] = str(uuid.uuid4())
        version.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("commercial_agreement_versions", version)
        if self.is_live:
            try:
                self.get_table("commercial_agreement_versions").upsert(version).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_agreement_version error: {e}")
        return version

    # --- Revenue Events & Deductions ---

    def get_revenue_event_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        events = self.local_get("revenue_events")
        match = next((e for e in events if e.get("idempotency_key") == idempotency_key), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("revenue_events").select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_revenue_event_by_idempotency error: {e}")
        return None

    def insert_revenue_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in event:
            event["id"] = str(uuid.uuid4())
        event.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("revenue_events", event)
        if self.is_live:
            try:
                self.get_table("revenue_events").upsert(event).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_revenue_event error: {e}")
        return event

    def insert_revenue_deduction(self, deduction: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in deduction:
            deduction["id"] = str(uuid.uuid4())
        deduction.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("revenue_deductions", deduction)
        if self.is_live:
            try:
                self.get_table("revenue_deductions").insert(deduction).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_revenue_deduction error: {e}")
        return deduction

    def get_revenue_deductions(self, revenue_event_id: str) -> List[Dict[str, Any]]:
        deductions = self.local_get("revenue_deductions")
        matches = [d for d in deductions if d.get("revenue_event_id") == revenue_event_id]
        if matches:
            return matches
        if self.is_live:
            try:
                res = self.get_table("revenue_deductions").select("*").eq("revenue_event_id", revenue_event_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_revenue_deductions error: {e}")
        return []

    # --- Creator Ledger (Append-Only) ---

    def get_creator_ledger_entry_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        entries = self.local_get("creator_ledger")
        match = next((e for e in entries if e.get("idempotency_key") == idempotency_key), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_ledger").select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_creator_ledger_entry_by_idempotency error: {e}")
        return None

    def get_creator_ledger_entry_by_id(self, ledger_id: str) -> Optional[Dict[str, Any]]:
        entries = self.local_get("creator_ledger")
        match = next((e for e in entries if e.get("id") == ledger_id), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_ledger").select("*").eq("id", ledger_id).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_creator_ledger_entry_by_id error: {e}")
        return None

    def insert_creator_ledger_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Appends an immutable entry to the creator ledger."""
        if "id" not in entry:
            entry["id"] = str(uuid.uuid4())
        entry.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("creator_ledger", entry)
        if self.is_live:
            try:
                self.get_table("creator_ledger").insert(entry).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_creator_ledger_entry error: {e}")
        return entry

    def get_creator_ledger(
        self,
        creator_id: str,
        accounting_period: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        entries = self.local_get("creator_ledger")
        matches = [e for e in entries if e.get("creator_id") == creator_id]
        if accounting_period:
            matches = [e for e in matches if e.get("accounting_period") == accounting_period]
        matches.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matches[:limit]

    # --- Creator Statements ---

    def get_statement(self, creator_id: str, accounting_period: str, currency: str = "ZAR") -> Optional[Dict[str, Any]]:
        statements = self.local_get("creator_statements")
        match = next((s for s in statements if s.get("creator_id") == creator_id and s.get("accounting_period") == accounting_period and s.get("currency") == currency), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_statements").select("*").eq("creator_id", creator_id).eq("accounting_period", accounting_period).eq("currency", currency).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_statement error: {e}")
        return None

    def upsert_statement(self, statement: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in statement:
            statement["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        statement.setdefault("generated_at", now)
        statement.setdefault("created_at", now)
        
        # update local
        existing = self.local_get("creator_statements")
        updated = False
        for idx, s in enumerate(existing):
            if s.get("creator_id") == statement.get("creator_id") and s.get("accounting_period") == statement.get("accounting_period") and s.get("currency") == statement.get("currency"):
                existing[idx] = statement
                updated = True
                break
        if not updated:
            existing.append(statement)
        self.local_set("creator_statements", existing)

        if self.is_live:
            try:
                self.get_table("creator_statements").upsert(statement).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] upsert_statement error: {e}")
        return statement

    def insert_statement_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for line in lines:
            if "id" not in line:
                line["id"] = str(uuid.uuid4())
            line.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            self.local_insert("creator_statement_lines", line)
        if self.is_live and lines:
            try:
                self.get_table("creator_statement_lines").insert(lines).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_statement_lines error: {e}")
        return lines

    # --- Creator Payouts (Accounting Object Only) ---

    def get_payout_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        payouts = self.local_get("creator_payouts")
        match = next((p for p in payouts if p.get("idempotency_key") == idempotency_key), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_payouts").select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payout_by_idempotency error: {e}")
        return None

    def insert_payout(self, payout: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in payout:
            payout["id"] = str(uuid.uuid4())
        payout.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("creator_payouts", payout)
        if self.is_live:
            try:
                db_payout = {**payout, "id": to_uuid(payout["id"])}
                self.get_table("creator_payouts").insert(db_payout).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_payout error: {e}")
        return payout

    def get_creator_payouts(self, creator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        payouts = self.local_get("creator_payouts")
        if creator_id:
            matches = [p for p in payouts if p.get("creator_id") == creator_id]
        else:
            matches = list(payouts)
        if self.is_live:
            try:
                q = self.get_table("creator_payouts").select("*").order("created_at", desc=True)
                if creator_id:
                    q = q.eq("creator_id", creator_id)
                res = q.execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_creator_payouts error: {e}")
        return matches

    def get_payout_by_id(self, payout_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single payout record by its primary key UUID."""
        payouts = self.local_get("creator_payouts")
        match = next((p for p in payouts if p.get("id") == payout_id), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_payouts").select("*").eq("id", to_uuid(payout_id)).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payout_by_id error: {e}")
        return None

    def get_all_payouts(self, limit: int = 200, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all creator payouts for admin governance and reconciliation."""
        payouts = self.local_get("creator_payouts")
        if status:
            payouts = [p for p in payouts if p.get("status") == status]
        if self.is_live:
            try:
                q = self.get_table("creator_payouts").select("*").order("created_at", desc=True).limit(limit)
                if status:
                    q = q.eq("status", status)
                res = q.execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_all_payouts error: {e}")
        payouts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return payouts[:limit]

    def update_payout(self, payout_id: str, updates: Dict[str, Any]) -> bool:
        """Updates mutable fields (status, settlement details, metadata) of a creator_payouts row."""
        payouts = self.local_get("creator_payouts")
        p = next((x for x in payouts if x.get("id") == payout_id), None)
        if p:
            p.update(updates)
            self.local_update("creator_payouts", "id", payout_id, p)
        if self.is_live:
            try:
                self.get_table("creator_payouts").update(updates).eq("id", to_uuid(payout_id)).execute()
                return True
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] update_payout error: {e}")
                return False
        return True

    def insert_payout_allocation(self, allocation: Dict[str, Any]) -> Dict[str, Any]:
        """Inserts an immutable allocation bridging a payout request to an underlying creator_ledger earning entry."""
        if "id" not in allocation:
            allocation["id"] = str(uuid.uuid4())
        allocation.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.local_insert("creator_payout_allocations", allocation)
        if self.is_live:
            try:
                db_alloc = {
                    **allocation,
                    "id": to_uuid(allocation["id"]),
                    "payout_id": to_uuid(allocation["payout_id"]),
                    "ledger_entry_id": to_uuid(allocation["ledger_entry_id"])
                }
                self.get_table("creator_payout_allocations").insert(db_alloc).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_payout_allocation error: {e}")
        return allocation

    def get_payout_allocations(self, payout_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves allocations for a given payout ID or all allocations across all payouts."""
        allocations = self.local_get("creator_payout_allocations")
        if payout_id:
            allocations = [a for a in allocations if a.get("payout_id") == payout_id]
        if self.is_live:
            try:
                q = self.get_table("creator_payout_allocations").select("*")
                if payout_id:
                    q = q.eq("payout_id", to_uuid(payout_id))
                res = q.execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payout_allocations error: {e}")
        return allocations

    def get_allocations_for_ledger_entry(self, ledger_entry_id: str) -> List[Dict[str, Any]]:
        """Retrieves all allocations referencing a specific creator_ledger entry."""
        allocations = self.local_get("creator_payout_allocations")
        matches = [a for a in allocations if a.get("ledger_entry_id") == ledger_entry_id]
        if self.is_live:
            try:
                res = self.get_table("creator_payout_allocations").select("*").eq("ledger_entry_id", to_uuid(ledger_entry_id)).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_allocations_for_ledger_entry error: {e}")
        return matches


    def get_creator_statements(self, creator_id: str) -> List[Dict[str, Any]]:
        """Retrieves all generated statements for a creator, ordered by period descending."""
        statements = self.local_get("creator_statements")
        matches = [s for s in statements if s.get("creator_id") == creator_id]
        if self.is_live:
            try:
                res = self.get_table("creator_statements").select("*").eq("creator_id", creator_id).order("accounting_period", desc=True).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_creator_statements error: {e}")
        matches.sort(key=lambda s: s.get("accounting_period", ""), reverse=True)
        return matches

    def get_statement_lines(self, statement_id: str) -> List[Dict[str, Any]]:
        """Retrieves statement lines for a specific statement."""
        lines = self.local_get("creator_statement_lines")
        matches = [l for l in lines if l.get("statement_id") == statement_id]
        if self.is_live:
            try:
                res = self.get_table("creator_statement_lines").select("*").eq("statement_id", statement_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_statement_lines error: {e}")
        return matches

    def get_revenue_events(
        self,
        limit: int = 200,
        only_exceptions: bool = False,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves revenue events with optional filtering for reconciliation and exception handling."""
        events = self.local_get("revenue_events")
        if only_exceptions:
            events = [
                e for e in events
                if e.get("metadata", {}).get("accounting_exception") is True
                or e.get("metadata", {}).get("unresolved_commercial_allocation") is True
            ]
        if source:
            events = [e for e in events if e.get("source") == source]

        if self.is_live:
            try:
                q = self.get_table("revenue_events").select("*").order("occurred_at", desc=True).limit(limit)
                if source:
                    q = q.eq("source", source)
                res = q.execute()
                if res and res.data:
                    data = res.data
                    if only_exceptions:
                        data = [
                            e for e in data
                            if (e.get("metadata") or {}).get("accounting_exception") is True
                            or (e.get("metadata") or {}).get("unresolved_commercial_allocation") is True
                        ]
                    return data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_revenue_events error: {e}")

        events.sort(key=lambda e: e.get("occurred_at", ""), reverse=True)
        return events[:limit]

    def get_revenue_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single revenue event by its ID."""
        events = self.local_get("revenue_events")
        match = next((e for e in events if e.get("id") == event_id), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("revenue_events").select("*").eq("id", event_id).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_revenue_event_by_id error: {e}")
        return None

    def update_revenue_event_metadata(
        self,
        event_id: str,
        metadata_updates: Dict[str, Any],
        commercial_agreement_version_id: Optional[str] = None
    ) -> bool:
        """Updates metadata and optional contract version link on a revenue event (used in exception resolution)."""
        events = self.local_get("revenue_events")
        event = next((e for e in events if e.get("id") == event_id), None)
        if event:
            current_meta = event.get("metadata") or {}
            current_meta.update(metadata_updates)
            event["metadata"] = current_meta
            if commercial_agreement_version_id:
                event["commercial_agreement_version_id"] = commercial_agreement_version_id
            self.local_update("revenue_events", "id", event_id, event)

        if self.is_live:
            try:
                db_update: Dict[str, Any] = {}
                # Fetch existing to merge metadata
                curr = self.get_table("revenue_events").select("metadata").eq("id", event_id).limit(1).execute()
                if curr and curr.data:
                    merged = curr.data[0].get("metadata") or {}
                    merged.update(metadata_updates)
                    db_update["metadata"] = merged
                else:
                    db_update["metadata"] = metadata_updates

                if commercial_agreement_version_id:
                    db_update["commercial_agreement_version_id"] = commercial_agreement_version_id

                self.get_table("revenue_events").update(db_update).eq("id", event_id).execute()
                return True
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] update_revenue_event_metadata error: {e}")
                return False
        return True

    def get_creator_ledger_entries_by_revenue_event(self, revenue_event_id: str) -> List[Dict[str, Any]]:
        """Retrieves creator ledger entries attached to a revenue event."""
        entries = self.local_get("creator_ledger")
        matches = [e for e in entries if e.get("revenue_event_id") == revenue_event_id]
        if self.is_live:
            try:
                res = self.get_table("creator_ledger").select("*").eq("revenue_event_id", revenue_event_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_creator_ledger_entries_by_revenue_event error: {e}")
        return matches

    def get_all_creator_ledger_entries(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Retrieves recent creator ledger entries across all creators for operational reconciliation."""
        entries = self.local_get("creator_ledger")
        if self.is_live:
            try:
                res = self.get_table("creator_ledger").select("*").order("created_at", desc=True).limit(limit).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_all_creator_ledger_entries error: {e}")
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return entries[:limit]

    # --- 6I-G.4.2 Creator Payment Runs & Items ---

    def insert_payment_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        """Persists a new creator payment run."""
        if "id" not in run:
            run["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        run.setdefault("created_at", now)
        run.setdefault("updated_at", now)
        self.local_insert("creator_payment_runs", run)
        if self.is_live:
            try:
                self.get_table("creator_payment_runs").insert(run).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_payment_run error: {e}")
        return run

    def update_payment_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates payment run metadata, status, approvals, or hashes."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = self.local_update("creator_payment_runs", "id", run_id, updates)
        if self.is_live:
            try:
                self.get_table("creator_payment_runs").update(updates).eq("id", run_id).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] update_payment_run error: {e}")
        return updated

    def get_payment_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a payment run by ID."""
        runs = self.local_get("creator_payment_runs")
        match = next((r for r in runs if str(r.get("id")) == str(run_id)), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_payment_runs").select("*").eq("id", run_id).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payment_run error: {e}")
        return None

    def get_payment_run_by_reference(self, run_reference: str) -> Optional[Dict[str, Any]]:
        """Retrieves a payment run by its unique human reference (e.g. RUN-2026-W42-001)."""
        runs = self.local_get("creator_payment_runs")
        match = next((r for r in runs if r.get("run_reference") == run_reference), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_payment_runs").select("*").eq("run_reference", run_reference).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payment_run_by_reference error: {e}")
        return None

    def get_payment_run_by_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a payment run by its run-level idempotency key."""
        runs = self.local_get("creator_payment_runs")
        match = next((r for r in runs if r.get("idempotency_key") == idempotency_key), None)
        if match:
            return match
        if self.is_live:
            try:
                res = self.get_table("creator_payment_runs").select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payment_run_by_idempotency error: {e}")
        return None

    def list_payment_runs(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists payment runs ordered by creation date descending."""
        runs = self.local_get("creator_payment_runs")
        if status:
            runs = [r for r in runs if r.get("status") == status]
        if self.is_live:
            try:
                query = self.get_table("creator_payment_runs").select("*").order("created_at", desc=True).limit(limit)
                if status:
                    query = query.eq("status", status)
                res = query.execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] list_payment_runs error: {e}")
        runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return runs[:limit]

    def insert_payment_run_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persists immutable snapshot items for an approved or draft payment run."""
        now = datetime.now(timezone.utc).isoformat()
        for item in items:
            if "id" not in item:
                item["id"] = str(uuid.uuid4())
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            self.local_insert("creator_payment_run_items", item)
        if self.is_live and items:
            try:
                self.get_table("creator_payment_run_items").insert(items).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] insert_payment_run_items error: {e}")
        return items

    def get_payment_run_items(self, payment_run_id: str) -> List[Dict[str, Any]]:
        """Retrieves all snapshot items for a payment run."""
        items = self.local_get("creator_payment_run_items")
        matches = [item for item in items if str(item.get("payment_run_id")) == str(payment_run_id)]
        if self.is_live:
            try:
                res = self.get_table("creator_payment_run_items").select("*").eq("payment_run_id", payment_run_id).execute()
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_payment_run_items error: {e}")
        return matches

    def get_active_payment_run_item_for_payout(self, payout_id: str) -> Optional[Dict[str, Any]]:
        """Checks if a payout is already included in any active (non-cancelled, non-excluded) payment run."""
        items = self.local_get("creator_payment_run_items")
        runs = {str(r["id"]): r for r in self.local_get("creator_payment_runs")}
        for item in items:
            if str(item.get("payout_id")) == str(payout_id) and item.get("status") not in ["EXCLUDED", "FAILED"]:
                parent_run = runs.get(str(item.get("payment_run_id")))
                if parent_run and parent_run.get("status") != "CANCELLED":
                    return item
        if self.is_live:
            try:
                res = self.get_table("creator_payment_run_items").select("*").eq("payout_id", payout_id).neq("status", "EXCLUDED").execute()
                if res and res.data:
                    for row in res.data:
                        run = self.get_payment_run(row["payment_run_id"])
                        if run and run.get("status") != "CANCELLED":
                            return row
            except Exception as e:
                logger.warning(f"[CommercialAccounting:DB] get_active_payment_run_item_for_payout error: {e}")
        return None

    def update_payment_run_item(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates a specific payment run item (e.g. status, external reference, failure reason)."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated = self.local_update("creator_payment_run_items", "id", item_id, updates)
        if self.is_live:
            try:
                self.get_table("creator_payment_run_items").update(updates).eq("id", item_id).execute()
            except Exception as e:
                logger.error(f"[CommercialAccounting:DB] update_payment_run_item error: {e}")
        return updated

    def get_eligible_payouts_for_run(self, currency: str = "ZAR") -> List[Dict[str, Any]]:
        """
        Retrieves unbatched, valid PENDING creator payouts eligible for a payment run.
        Eligible payout criteria:
        1. status = 'PENDING'
        2. currency = requested currency (ZAR)
        3. requested_amount > 0
        4. Not already assigned to an active payment run
        """
        payouts = self.get_creator_payouts()
        eligible = []
        for p in payouts:
            if p.get("status") != "PENDING":
                continue
            if p.get("currency", "ZAR") != currency:
                continue
            if Decimal(str(p.get("requested_amount", 0))) <= Decimal("0.0000"):
                continue
            if self.get_active_payment_run_item_for_payout(p["id"]):
                continue
            eligible.append(p)
        return eligible


# Singleton instance
commercial_accounting_repository = CommercialAccountingRepository()

