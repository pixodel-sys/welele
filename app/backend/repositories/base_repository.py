"""
Welele Media™ — Base Repository
Provides unified asynchronous connection management, transaction contexts, and Supabase client bindings.
Guarantees persistence across local development, staging, and production environments.

Canonical-state boundary:
    PostgreSQL/Supabase is the sole persisted authority for canonical catalogue
    collections in staging/production. The legacy local Database remains
    available for isolated development/test state, but cannot participate as a
    second production catalogue authority.
"""

import os
import threading
from typing import Dict, Any, List, Optional
import logging
from config import settings
from database import db

logger = logging.getLogger("welele.repository")


# Collections whose persisted authority has been migrated to PostgreSQL.
# These are intentionally scoped to canonical domain state; unrelated local
# application/test collections are not affected by this boundary.
CANONICAL_LOCAL_TABLES = frozenset({
    "digital_ips",
    "story_worlds",
    "character_bibles",
    "rights_ledger",
    "story_forge_packages",
    "series",
    "episodes",
    "media_assets",
    "media_jobs",
    "media_renditions",
    "experience_layouts",
    "creator_profiles",
    "workspace_members",
})


class BaseRepository:
    _lock = threading.RLock()

    def __init__(self):
        self._supabase = None
        self._init_client()

    def _init_client(self):
        if settings.ENVIRONMENT == "test":
            self._supabase = None
            return

        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            from target_validator import validate_database_target, extract_project_ref
            validate_database_target(settings.ENVIRONMENT, settings.SUPABASE_URL)
            try:
                from supabase import create_client
                self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                ref = extract_project_ref(settings.SUPABASE_URL)
                logger.info(f"[BaseRepository] Client connected (project ref: {ref})")
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(
                        f"CRITICAL ARCHITECTURAL HALT: Failed to connect to authoritative PostgreSQL database in {settings.ENVIRONMENT}: {e}. "
                        "Silent fallback to ephemeral storage is strictly prohibited in staging/production."
                    )
                logger.warning(f"[BaseRepository:Dev] Supabase connection failed, falling back to local persistent store: {e}")
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
        return self._supabase is not None and settings.ENVIRONMENT != "test"

    @property
    def _canonical_local_quarantined(self) -> bool:
        """Whether canonical local state must be hidden from live application paths."""
        return settings.IS_PRODUCTION_OR_STAGING

    def get_table(self, table_name: str):
        if self._supabase:
            return self._supabase.table(table_name)
        return None

    def get_client(self):
        return self._supabase

    def local_get(self, table: str, allow_canonical_local: bool = False) -> List[Dict[str, Any]]:
        if self._canonical_local_quarantined and table in CANONICAL_LOCAL_TABLES and not allow_canonical_local:
            return []
        return db.get(table)

    def local_set(self, table: str, items: List[Dict[str, Any]], allow_canonical_local: bool = False):
        if self._canonical_local_quarantined and table in CANONICAL_LOCAL_TABLES and not allow_canonical_local:
            logger.info("[CanonicalBoundary] Ignoring local set for canonical table '%s'; PostgreSQL is authoritative.", table)
            return
        db.set(table, items)

    def local_insert(self, table: str, item: Dict[str, Any], allow_canonical_local: bool = False) -> Dict[str, Any]:
        if self._canonical_local_quarantined and table in CANONICAL_LOCAL_TABLES and not allow_canonical_local:
            logger.info("[CanonicalBoundary] Ignoring local insert for canonical table '%s'; PostgreSQL is authoritative.", table)
            return item
        return db.insert(table, item)

    def local_update(
        self,
        table: str,
        key_field: str,
        key_val: Any,
        updates: Dict[str, Any],
        allow_canonical_local: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if self._canonical_local_quarantined and table in CANONICAL_LOCAL_TABLES and not allow_canonical_local:
            logger.info("[CanonicalBoundary] Ignoring local update for canonical table '%s'; PostgreSQL is authoritative.", table)
            return None
        with self._lock:
            items = db.get(table)
            for item in items:
                if item.get(key_field) == key_val:
                    item.update(updates)
                    db.set(table, items)
                    return item
        return None

    def local_delete(
        self,
        table: str,
        key_field: str,
        key_val: Any,
        allow_canonical_local: bool = False,
    ) -> bool:
        if self._canonical_local_quarantined and table in CANONICAL_LOCAL_TABLES and not allow_canonical_local:
            logger.info("[CanonicalBoundary] Ignoring local delete for canonical table '%s'; PostgreSQL is authoritative.", table)
            return False
        with self._lock:
            items = db.get(table)
            filtered = [item for item in items if item.get(key_field) != key_val]
            if len(filtered) != len(items):
                db.set(table, filtered)
                return True
        return False
