"""
Welele Media™ — Base Repository
Provides unified asynchronous connection management, transaction contexts, and Supabase client bindings.
Guarantees persistence across local development, staging, and production environments.
"""

import os
import threading
from typing import Dict, Any, List, Optional
from config import settings
from database import db

class BaseRepository:
    _lock = threading.RLock()

    def __init__(self):
        self._supabase = None
        self._init_client()

    def _init_client(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(
                        f"CRITICAL ARCHITECTURAL HALT: Failed to connect to authoritative PostgreSQL database in {settings.ENVIRONMENT}: {e}. "
                        "Silent fallback to ephemeral storage is strictly prohibited in staging/production."
                    )
                self._supabase = None
        else:
            if settings.IS_PRODUCTION_OR_STAGING:
                raise RuntimeError(
                    f"CRITICAL ARCHITECTURAL HALT: {settings.ENVIRONMENT.upper()} environment detected without SUPABASE_URL / SUPABASE_KEY. "
                    "Silent fallback to ephemeral storage is strictly prohibited in staging/production."
                )
            self._supabase = None

    @property
    def is_live(self) -> bool:
        return self._supabase is not None

    def get_table(self, table_name: str):
        if self._supabase:
            return self._supabase.table(table_name)
        return None

    def local_get(self, table: str) -> List[Dict[str, Any]]:
        return db.get(table)

    def local_set(self, table: str, items: List[Dict[str, Any]]):
        db.set(table, items)

    def local_insert(self, table: str, item: Dict[str, Any]) -> Dict[str, Any]:
        return db.insert(table, item)

    def local_update(self, table: str, key_field: str, key_val: Any, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            items = db.get(table)
            for item in items:
                if item.get(key_field) == key_val:
                    item.update(updates)
                    db.set(table, items)
                    return item
        return None

    def local_delete(self, table: str, key_field: str, key_val: Any) -> bool:
        with self._lock:
            items = db.get(table)
            filtered = [item for item in items if item.get(key_field) != key_val]
            if len(filtered) != len(items):
                db.set(table, filtered)
                return True
        return False
