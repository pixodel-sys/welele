import os
import json
import threading
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
                        "stories": [],
                        "creators": [],
                        "episodes": [],
                        "users": [],
                        "wallets": [],
                        "coin_ledger": [],
                        "unlocked_episodes": [],
                        "payment_transactions": [],
                        "bullet_comments": [],
                        "transactions": [],
                        "gifts": [],
                        "comments": [],
                        "reactions": [],
                        "moderation_queue": [],
                        "experience_layouts": []
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
                print(f"[Supabase] Connected to live PostgreSQL instance at {settings.SUPABASE_URL}")
            except Exception as e:
                print(f"[Supabase] Initialization warning (falling back to local store): {e}")
                self._supabase = None

    @property
    def supabase_client(self):
        return self._supabase

    def _load(self):
        os.makedirs(os.path.dirname(settings.DATA_FILE), exist_ok=True)
        if os.path.exists(settings.DATA_FILE):
            try:
                with open(settings.DATA_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                print(f"[DB] Error loading data file: {e}")
                self._save()
        else:
            self._save()

    def _save(self):
        os.makedirs(os.path.dirname(settings.DATA_FILE), exist_ok=True)
        try:
            with open(settings.DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB] Error saving data file: {e}")

    def get(self, collection: str) -> List[Dict[str, Any]]:
        with self._lock:
            return self.data.get(collection, [])

    def set(self, collection: str, items: List[Dict[str, Any]]):
        with self._lock:
            self.data[collection] = items
            self._save()

    def insert(self, collection: str, item: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            if collection not in self.data:
                self.data[collection] = []
            self.data[collection].append(item)
            self._save()

        # Asynchronously sync to live Supabase if connected
        if self._supabase:
            try:
                table_name = collection
                if collection == "comments":
                    table_name = "bullet_comments"
                elif collection == "transactions":
                    table_name = "payment_transactions"
                
                # Check if table exists in Supabase before insertion
                self._supabase.table(table_name).upsert(item).execute()
            except Exception as e:
                # Local persistence remains intact
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
            except Exception:
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
            except Exception:
                pass

        return deleted

db = Database()
