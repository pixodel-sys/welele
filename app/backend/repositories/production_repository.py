"""
Welele Media™ — Production Repository
Persists and retrieves Production Bibles and 5-Track Episode Production Packs.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository

class ProductionRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def save_production_bible(self, bible_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates a Production Bible in the repository."""
        if not bible_data.get("id"):
            bible_data["id"] = f"pb_{uuid.uuid4().hex[:8]}"
        if not bible_data.get("created_at"):
            bible_data["created_at"] = datetime.now(timezone.utc).isoformat()

        # Check if already exists in local DB
        existing = self.local_get("production_bibles")
        found = False
        for i, b in enumerate(existing):
            if b.get("id") == bible_data["id"] or (b.get("ip_id") == bible_data.get("ip_id") and b.get("version") == bible_data.get("version")):
                existing[i] = bible_data
                self.local_set("production_bibles", existing)
                found = True
                break
        if not found:
            self.local_insert("production_bibles", bible_data)

        # Attempt remote Supabase persistence if available
        if self.is_live:
            try:
                self.get_table("production_bibles").upsert(bible_data).execute()
            except Exception as e:
                print(f"[ProductionRepository] Remote upsert warning: {e}")

        return bible_data

    def get_production_bible_by_id(self, bible_id: str) -> Optional[Dict[str, Any]]:
        bibles = self.local_get("production_bibles")
        for b in bibles:
            if b.get("id") == bible_id:
                return b
        return None

    def get_production_bible_by_ip(self, ip_id: str) -> Optional[Dict[str, Any]]:
        bibles = self.local_get("production_bibles")
        for b in bibles:
            if b.get("ip_id") == ip_id:
                return b
        return None

    def list_production_bibles(self) -> List[Dict[str, Any]]:
        return self.local_get("production_bibles")

    def save_episode_pack(self, pack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates an Episode Production Pack."""
        if not pack_data.get("id"):
            pack_data["id"] = f"epp_{uuid.uuid4().hex[:8]}"
        if not pack_data.get("created_at"):
            pack_data["created_at"] = datetime.now(timezone.utc).isoformat()

        existing = self.local_get("episode_production_packs")
        found = False
        for i, p in enumerate(existing):
            if p.get("id") == pack_data["id"] or (p.get("episode_id") and p.get("episode_id") == pack_data.get("episode_id")):
                existing[i] = pack_data
                self.local_set("episode_production_packs", existing)
                found = True
                break
            elif p.get("ip_id") == pack_data.get("ip_id") and p.get("episode_number") == pack_data.get("episode_number") and "production_units" in p:
                existing[i] = pack_data
                self.local_set("episode_production_packs", existing)
                found = True
                break
        if not found:
            self.local_insert("episode_production_packs", pack_data)

        if self.is_live:
            try:
                self.get_table("episode_production_packs").upsert(pack_data).execute()
            except Exception as e:
                print(f"[ProductionRepository] Remote episode pack upsert warning: {e}")

        return pack_data

    def get_episode_pack(self, ip_id: str, episode_number: int) -> Optional[Dict[str, Any]]:
        packs = self.local_get("episode_production_packs")
        for p in packs:
            if p.get("ip_id") == ip_id and p.get("episode_number") == episode_number and "production_units" in p:
                return p
        for p in packs:
            if p.get("ip_id") == ip_id and p.get("episode_number") == episode_number:
                return p
        return None

    def get_episode_pack_by_episode_id(self, episode_id: str, version: str = "1.0.0") -> Optional[Dict[str, Any]]:
        packs = self.local_get("episode_production_packs")
        for p in packs:
            if p.get("episode_id") == episode_id and p.get("pack_version", "1.0.0") == version:
                return p
        return None

    def list_episode_packs(self, ip_id: Optional[str] = None) -> List[Dict[str, Any]]:
        packs = self.local_get("episode_production_packs")
        if ip_id:
            return [p for p in packs if p.get("ip_id") == ip_id]
        return packs

    def save_episode_blueprint(self, blueprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Saves or updates an Episode Blueprint."""
        if not blueprint_data.get("id"):
            blueprint_data["id"] = f"bp_{uuid.uuid4().hex[:8]}"
        if not blueprint_data.get("created_at"):
            blueprint_data["created_at"] = datetime.now(timezone.utc).isoformat()

        existing = self.local_get("episode_blueprints")
        found = False
        for i, b in enumerate(existing):
            if b.get("id") == blueprint_data["id"] or (b.get("episode_id") == blueprint_data.get("episode_id") and b.get("blueprint_version") == blueprint_data.get("blueprint_version")):
                existing[i] = blueprint_data
                self.local_set("episode_blueprints", existing)
                found = True
                break
        if not found:
            self.local_insert("episode_blueprints", blueprint_data)

        if self.is_live:
            try:
                self.get_table("episode_blueprints").upsert(blueprint_data).execute()
            except Exception as e:
                print(f"[ProductionRepository] Remote episode blueprint upsert warning: {e}")

        return blueprint_data

    def get_episode_blueprint(self, episode_id: str, version: str = "1.0.0") -> Optional[Dict[str, Any]]:
        blueprints = self.local_get("episode_blueprints")
        for b in blueprints:
            if b.get("episode_id") == episode_id and b.get("blueprint_version") == version:
                return b
        return None

    def list_episode_blueprints(self, series_id: Optional[str] = None) -> List[Dict[str, Any]]:
        blueprints = self.local_get("episode_blueprints")
        if series_id:
            return [b for b in blueprints if b.get("series_id") == series_id]
        return blueprints

production_repository = ProductionRepository()

