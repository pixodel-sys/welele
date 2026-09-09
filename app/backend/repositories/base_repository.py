"""
Welele Media™ — Base Repository
Provides unified asynchronous connection management, transaction contexts, and Supabase client bindings.
"""

import os
import threading
from typing import Dict, Any, List, Optional
from config import settings

class BaseRepository:
    _lock = threading.RLock()
    _memory_store: Dict[str, List[Dict[str, Any]]] = {
        "digital_ips": [],
        "story_worlds": [],
        "character_bibles": [],
        "rights_ledger": [],
        "story_forge_packages": [],
        "series": [],
        "episodes": [],
        "media_assets": [],
        "media_jobs": [],
        "media_renditions": [],
        "wallets": [],
        "coin_ledger": [],
        "payment_events": [],
        "unlocked_episodes": [],
        "telemetry_events": [],
        "intelligence_evidence": [],
        "intelligence_recommendations": [],
        "bullet_comments": [],
        "experience_layouts": [],
        "security_audit_ledger": []
    }

    def __init__(self):
        self._supabase = None
        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except Exception:
                self._supabase = None

    @property
    def is_live(self) -> bool:
        return self._supabase is not None

    def get_table(self, table_name: str):
        if self._supabase:
            return self._supabase.table(table_name)
        return None

    def local_get(self, table: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._memory_store.get(table, []))

    def local_set(self, table: str, items: List[Dict[str, Any]]):
        with self._lock:
            self._memory_store[table] = items

    def local_insert(self, table: str, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if table not in self._memory_store:
                self._memory_store[table] = []
            self._memory_store[table].append(item)
        return item

    def local_update(self, table: str, key_field: str, key_val: Any, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = self._memory_store.get(table, [])
            for item in items:
                if item.get(key_field) == key_val:
                    item.update(updates)
                    return item
        return None
