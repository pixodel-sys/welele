import os
import json
import copy
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
                        "viewer_telemetry_events": [],
                        "production_bibles": [],
                        "episode_blueprints": [],
                        "episode_production_packs": [],
                        "intelligence_evidence": [],
                        "intelligence_recommendations": [],
                        "content_intelligence_records": [],
                        "content_decisions": [],
                        "content_intelligence_evidence_packages": [],
                        "security_audit_ledger": []
                    }
                    cls._instance._supabase = None
                    cls._instance._canonical_store_path = os.path.abspath(settings.DATA_FILE)
                    cls._instance._active_store_path = os.path.abspath(settings.DATA_FILE)
                    cls._instance._is_isolated_test_store = False
                    cls._instance._read_only_canonical_guard = False
                    cls._instance._temp_store_file = None
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

    @property
    def is_isolated_test(self) -> bool:
        return self._is_isolated_test_store

    def enable_test_isolation(self, custom_store_path: Optional[str] = None):
        """
        Primary Protection: Divert all database state into a disposable isolated universe.
        Secondary Protection: Enforce strict read-only lock on canonical production store.
        """
        import copy
        with self._lock:
            if not hasattr(self, '_baseline_canonical_data') or self._baseline_canonical_data is None:
                self._baseline_canonical_data = copy.deepcopy(self.data)

            if custom_store_path:
                self._active_store_path = os.path.abspath(custom_store_path)
            elif not self._temp_store_file:
                tf = tempfile.NamedTemporaryFile(prefix="welele_test_store_", suffix=".json", delete=False)
                tf.close()
                self._temp_store_file = tf.name
                self._active_store_path = os.path.abspath(tf.name)

            self.data = copy.deepcopy(self._baseline_canonical_data)
            self._is_isolated_test_store = True
            self._read_only_canonical_guard = True
            self._save()

    def reset_test_state(self):
        """Resets the active test universe back to the pristine canonical baseline."""
        import copy
        with self._lock:
            if hasattr(self, '_baseline_canonical_data') and self._baseline_canonical_data is not None:
                self.data = copy.deepcopy(self._baseline_canonical_data)
                self._save()

    def disable_test_isolation(self):
        """Tear down isolated test universe and restore canonical connection."""
        with self._lock:
            temp_to_clean = self._temp_store_file
            self._temp_store_file = None
            self._active_store_path = self._canonical_store_path
            self._is_isolated_test_store = False
            self._read_only_canonical_guard = False
            if hasattr(self, '_baseline_canonical_data') and self._baseline_canonical_data is not None:
                self.data = copy.deepcopy(self._baseline_canonical_data)
                self._baseline_canonical_data = None
            else:
                self._load()

            if temp_to_clean and os.path.exists(temp_to_clean):
                try:
                    os.remove(temp_to_clean)
                except Exception:
                    pass

    def _load(self):
        target = self._active_store_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.exists(target):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[Database] Error reading data file: {e}")
                self._save()
        else:
            self._save()

    def _save(self):
        """Atomic write to active store with architectural boundary guard."""
        target = self._active_store_path

        # Secondary Architectural Guard: Absolute prohibition of canonical store mutation in test mode
        if (self._read_only_canonical_guard or self._is_isolated_test_store) and target == self._canonical_store_path:
            raise RuntimeError(
                "ARCHITECTURAL BOUNDARY VIOLATION: Write to canonical store is strictly forbidden during test execution. "
                "Tests must execute within an isolated test store universe."
            )

        data_dir = os.path.dirname(target)
        os.makedirs(data_dir, exist_ok=True)
        temp_file = os.path.join(data_dir, f".welele_store_{os.getpid()}_{threading.get_ident()}.tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, target)
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
            item_id = item.get("id")
            if item_id:
                for idx, existing_item in enumerate(self.data[collection]):
                    if existing_item.get("id") == item_id:
                        self.data[collection][idx] = item
                        self._save()
                        return item
            self.data[collection].append(item)
            self._save()

        # Sync to live Supabase ONLY in live non-test mode
        if self._supabase and not self._is_isolated_test_store:
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
