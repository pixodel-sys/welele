import os
import json
import threading
import tempfile
from typing import Dict, Any, List, Optional
from config import settings

class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
                    cls._instance.data: Dict[str, Any] = {
                        "digital_ips": [],
                        "story_worlds": [],
                        "character_bibles": [],
                        "rights_ledger": [],
                        "story_forge_packages": [],
                        "stories": [],
                        "series": [],
                        "creators": [],
                        "episodes": [],
                        "media_assets": [],
                        "media_jobs": [],
                        "media_renditions": [],
                        "users": [],
                        "wallets": [],
                        "coin_ledger": [],
                        "payment_events": [],
                        "unlocked_episodes": [],
                        "payment_transactions": [],
                        "bullet_comments": [],
                        "transactions": [],
                        "gifts": [],
                        "comments": [],
                        "reactions": [],
                        "moderation_queue": [],
                        "experience_layouts": [],
                        "telemetry_events": [],
                        "intelligence_evidence": [],
                        "intelligence_recommendations": [],
                        "security_audit_ledger": []
                    }
                    cls._instance._supabase = None
                    cls._instance._init_supabase()
                    cls._instance._load()
        return cls._instance

    def _init_supabase(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                print(f"[Database] Authoritative PostgreSQL connected at {settings.SUPABASE_URL}")
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(
                        f"CRITICAL ARCHITECTURAL HALT: Failed to connect to authoritative PostgreSQL database in {settings.ENVIRONMENT}: {e}. "
                        "Silent fallback to ephemeral storage is strictly prohibited in staging/production."
                    )
                print(f"[Database:Dev] Supabase connection failed, falling back to local persistent store: {e}")
                self._supabase = None
        else:
            if settings.IS_PRODUCTION_OR_STAGING:
                raise RuntimeError(
                    f"CRITICAL ARCHITECTURAL HALT: {settings.ENVIRONMENT.upper()} environment detected without SUPABASE_URL / SUPABASE_KEY. "
                    "Silent fallback to ephemeral JSON/memory is strictly prohibited in staging/production."
                )
            print(f"[Database:Dev] Running in {settings.ENVIRONMENT} mode using disk-backed store at {settings.DATA_FILE}")

    @property
    def supabase_client(self):
        return self._supabase

    @property
    def is_live(self) -> bool:
        return self._supabase is not None

    def _load(self):
        os.makedirs(os.path.dirname(settings.DATA_FILE), exist_ok=True)
        if os.path.exists(settings.DATA_FILE):
            try:
                with open(settings.DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Database] Error reading data file: {e}")
                self._save()
        else:
            self._save()

    def _save(self):
        """Atomic write to disk to prevent data corruption during deployments or concurrent requests."""
        data_dir = os.path.dirname(settings.DATA_FILE)
        os.makedirs(data_dir, exist_ok=True)
        temp_file = os.path.join(data_dir, f".welele_store_{os.getpid()}_{threading.get_ident()}.tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, settings.DATA_FILE)
        except Exception as e:
            print(f"[Database] Error atomically saving data file: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    def get(self, collection: str) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.data.get(collection, []))

    def set(self, collection: str, items: List[Dict[str, Any]]):
        with self._lock:
            self.data[collection] = list(items)
            self._save()

    def insert(self, collection: str, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if collection not in self.data:
                self.data[collection] = []
            self.data[collection].append(item)
            self._save()

        # Sync to live Supabase if connected
        if self._supabase:
            try:
                table_name = collection
                if collection == "comments":
                    table_name = "bullet_comments"
                elif collection == "transactions":
                    table_name = "payment_transactions"
                self._supabase.table(table_name).upsert(item).execute()
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database write failure on table '{collection}': {e}")
                pass

        return item

    def update(self, collection: str, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        target_item = None
        with self._lock:
            items = self.data.get(collection, [])
            for item in items:
                if item.get("id") == item_id:
                    item.update(updates)
                    target_item = item
                    self._save()
                    break

        if target_item and self._supabase:
            try:
                table_name = collection
                if collection == "comments":
                    table_name = "bullet_comments"
                elif collection == "transactions":
                    table_name = "payment_transactions"
                self._supabase.table(table_name).update(updates).eq("id", item_id).execute()
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database update failure on table '{collection}': {e}")
                pass

        return target_item

    def delete(self, collection: str, item_id: str) -> bool:
        deleted = False
        with self._lock:
            items = self.data.get(collection, [])
            filtered = [item for item in items if item.get("id") != item_id]
            if len(filtered) != len(items):
                self.data[collection] = filtered
                self._save()
                deleted = True

        if deleted and self._supabase:
            try:
                table_name = collection
                if collection == "comments":
                    table_name = "bullet_comments"
                elif collection == "transactions":
                    table_name = "payment_transactions"
                self._supabase.table(table_name).delete().eq("id", item_id).execute()
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database delete failure on table '{collection}': {e}")
                pass

        return deleted

db = Database()
