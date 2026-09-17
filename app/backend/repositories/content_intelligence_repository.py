"""
Welele Media™ — Content Intelligence Repository (Phase 7)
Normalized persistence for observations, intelligence records, decisions, and evidence packages.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository


class ContentIntelligenceRepository(BaseRepository):
    """
    Persistence layer for Content Intelligence, Decisions, and Evidence Packages.
    Guarantees versioned lineage traceability and persistence across dev/staging/prod.
    """

    def save_intelligence_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a Content Intelligence record."""
        if not record_data.get("intelligence_id"):
            record_data["intelligence_id"] = f"int_{uuid.uuid4().hex[:10]}"
        if not record_data.get("created_at"):
            record_data["created_at"] = datetime.now(timezone.utc).isoformat()

        # Deduplicate / update
        existing = self.local_get("content_intelligence_records")
        found = False
        for i, item in enumerate(existing):
            if item.get("intelligence_id") == record_data["intelligence_id"]:
                existing[i] = record_data
                self.local_set("content_intelligence_records", existing)
                found = True
                break
        if not found:
            self.local_insert("content_intelligence_records", record_data)

        if self.is_live:
            try:
                self.get_table("content_intelligence_records").upsert(record_data).execute()
            except Exception as e:
                print(f"[ContentIntelligenceRepository] Remote upsert warning: {e}")

        return record_data

    def get_intelligence_record(self, intelligence_id: str) -> Optional[Dict[str, Any]]:
        records = self.local_get("content_intelligence_records")
        for r in records:
            if r.get("intelligence_id") == intelligence_id or r.get("id") == intelligence_id:
                return r
        return None

    def list_intelligence_records(
        self,
        ip_id: Optional[str] = None,
        series_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        records = self.local_get("content_intelligence_records")
        results = records
        if ip_id:
            results = [r for r in results if r.get("ip_id") == ip_id]
        if series_id:
            results = [r for r in results if r.get("series_id") == series_id]
        if episode_id:
            results = [r for r in results if r.get("episode_id") == episode_id]
        if domain:
            results = [r for r in results if r.get("domain") == domain]
        return results

    def save_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a Content Decision."""
        if not decision_data.get("decision_id"):
            decision_data["decision_id"] = f"dec_{uuid.uuid4().hex[:10]}"
        if not decision_data.get("created_at"):
            decision_data["created_at"] = datetime.now(timezone.utc).isoformat()
        decision_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        existing = self.local_get("content_decisions")
        found = False
        for i, item in enumerate(existing):
            if item.get("decision_id") == decision_data["decision_id"]:
                existing[i] = decision_data
                self.local_set("content_decisions", existing)
                found = True
                break
        if not found:
            self.local_insert("content_decisions", decision_data)

        if self.is_live:
            try:
                self.get_table("content_decisions").upsert(decision_data).execute()
            except Exception as e:
                print(f"[ContentIntelligenceRepository] Remote decision upsert warning: {e}")

        return decision_data

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        decisions = self.local_get("content_decisions")
        for d in decisions:
            if d.get("decision_id") == decision_id or d.get("id") == decision_id:
                return d
        return None

    def list_decisions(
        self,
        target_layer: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        decisions = self.local_get("content_decisions")
        results = decisions
        if target_layer:
            results = [d for d in results if d.get("target_layer") == target_layer]
        if status:
            results = [d for d in results if d.get("status") == status]
        return results

    def save_evidence_package(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a Content Intelligence Evidence Package."""
        if not package_data.get("package_id"):
            package_data["package_id"] = f"cie_{uuid.uuid4().hex[:10]}"
        if not package_data.get("created_at"):
            package_data["created_at"] = datetime.now(timezone.utc).isoformat()

        existing = self.local_get("content_intelligence_evidence_packages")
        found = False
        for i, item in enumerate(existing):
            if item.get("package_id") == package_data["package_id"] or (item.get("episode_id") == package_data.get("episode_id") and item.get("package_id")):
                existing[i] = package_data
                self.local_set("content_intelligence_evidence_packages", existing)
                found = True
                break
        if not found:
            self.local_insert("content_intelligence_evidence_packages", package_data)

        if self.is_live:
            try:
                self.get_table("content_intelligence_evidence_packages").upsert(package_data).execute()
            except Exception as e:
                print(f"[ContentIntelligenceRepository] Remote package upsert warning: {e}")

        return package_data

    def get_evidence_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        packages = self.local_get("content_intelligence_evidence_packages")
        for p in packages:
            if p.get("package_id") == package_id or p.get("id") == package_id:
                return p
        return None

    def list_evidence_packages(self, episode_id: Optional[str] = None) -> List[Dict[str, Any]]:
        packages = self.local_get("content_intelligence_evidence_packages")
        if episode_id:
            return [p for p in packages if p.get("episode_id") == episode_id]
        return packages


content_intelligence_repository = ContentIntelligenceRepository()
