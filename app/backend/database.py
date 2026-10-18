import os
import json
import copy
import threading
import tempfile
from typing import Dict, Any, List, Optional
import logging
from config import settings

logger = logging.getLogger("welele.database")

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
                        "security_audit_ledger": [],
                        "creator_payment_runs": [],
                        "creator_payment_run_items": []
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
        if settings.ENVIRONMENT == "test":
            self._supabase = None
            logger.debug("[Database:Test] Test environment detected; cloud Supabase client instantiation is disabled.")
            return

        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            from target_validator import validate_database_target, extract_project_ref
            validate_database_target(settings.ENVIRONMENT, settings.SUPABASE_URL)
            try:
                from supabase import create_client
                self._supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                ref = extract_project_ref(settings.SUPABASE_URL)
                logger.info(f"[Database] Authoritative PostgreSQL connected (project ref: {ref})")
            except Exception as e:
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(
                        f"CRITICAL ARCHITECTURAL HALT: Failed to connect to authoritative PostgreSQL database in {settings.ENVIRONMENT}: {e}. "
                        "Silent fallback to ephemeral storage is strictly prohibited in staging/production."
                    )
                logger.warning(f"[Database:Dev] Supabase connection failed, falling back to local persistent store: {e}")
                self._supabase = None
        else:
            if settings.IS_PRODUCTION_OR_STAGING:
                raise RuntimeError(
                    f"CRITICAL ARCHITECTURAL HALT: {settings.ENVIRONMENT.upper()} environment detected without SUPABASE_URL / SUPABASE_KEY. "
                    "Silent fallback to ephemeral JSON/memory is strictly prohibited in staging/production."
                )
            logger.info(f"[Database:Dev] Running in {settings.ENVIRONMENT} mode using disk-backed store at {settings.DATA_FILE}")

    @property
    def supabase_client(self):
        return self._supabase

    @property
    def is_live(self) -> bool:
        return self._supabase is not None and settings.ENVIRONMENT != "test"

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
            item_id = item.get("id") or item.get("event_id")
            if item_id:
                for idx, existing_item in enumerate(self.data[collection]):
                    if existing_item.get("id") == item_id or existing_item.get("event_id") == item_id:
                        self.data[collection][idx] = item
                        self._save()
                        return item
            self.data[collection].append(item)
            self._save()

        # Sync to live Supabase ONLY in live non-test mode
        if self._supabase and not self._is_isolated_test_store:
            try:
                table_name = collection
                payload_to_sync = item
                on_conflict = None

                if collection == "comments":
                    table_name = "bullet_comments"
                elif collection == "transactions":
                    table_name = "payment_transactions"
                elif collection in ("viewer_telemetry_events", "telemetry_events"):
                    table_name = "telemetry_events"
                    payload_to_sync = self._map_telemetry_for_supabase(item)
                    on_conflict = "id"
                elif collection == "security_audit_ledger":
                    table_name = "security_audit_ledger"
                    payload_to_sync = self._map_audit_for_supabase(item)
                    on_conflict = "event_id"
                elif collection == "series":
                    table_name = "series"
                    valid_series_cols = {
                        "id", "ip_id", "season_number", "title", "tagline", "synopsis",
                        "cover_image", "vertical_poster", "genre", "rating", "total_episodes",
                        "free_episodes", "coin_price_per_episode", "is_published",
                        "available_languages", "tags", "created_at", "updated_at"
                    }
                    payload_to_sync = {k: v for k, v in item.items() if k in valid_series_cols}
                    if "id" in payload_to_sync:
                        payload_to_sync["id"] = self._to_uuid(str(payload_to_sync["id"]))
                    if "ip_id" in payload_to_sync:
                        payload_to_sync["ip_id"] = self._to_uuid(str(payload_to_sync["ip_id"]))
                elif collection == "episodes":
                    table_name = "episodes"
                    valid_ep_cols = {
                        "id", "series_id", "story_package_id", "season_number", "episode_number",
                        "title", "synopsis", "duration_seconds", "is_free", "coin_price",
                        "cliffhanger_time_seconds", "cliffhanger_hook", "status", "created_at", "updated_at"
                    }
                    payload_to_sync = {k: v for k, v in item.items() if k in valid_ep_cols}
                    if "id" in payload_to_sync:
                        payload_to_sync["id"] = self._to_uuid(str(payload_to_sync["id"]))
                    if "series_id" in payload_to_sync:
                        payload_to_sync["series_id"] = self._to_uuid(str(payload_to_sync["series_id"]))
                elif collection in (
                    "wallets", "coin_ledger", "unlocked_episodes",
                    "commercial_agreements", "commercial_agreement_versions",
                    "revenue_events", "revenue_deductions", "creator_ledger",
                    "creator_statements", "creator_statement_lines",
                    "creator_payouts", "creator_payout_allocations"
                ):
                    # Managed authoritatively by LedgerRepository and CommercialAccountingRepository with domain logic
                    return item

                if on_conflict:
                    self._supabase.table(table_name).upsert(payload_to_sync, on_conflict=on_conflict).execute()
                else:
                    self._supabase.table(table_name).upsert(payload_to_sync).execute()
            except Exception as e:
                logger.error(f"[Database] Remote sync failed on '{collection}': {e}")
                raise RuntimeError(f"Database write failure on table '{collection}': {e}") from e

        return item

    @staticmethod
    def _to_uuid(name: str) -> str:
        import uuid
        try:
            uuid.UUID(str(name))
            return str(name)
        except Exception:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))

    def _resolve_fk_uuid(self, table: str, raw_val: Optional[Any], slug_prefix: str) -> Optional[str]:
        """
        Resolves an ID (UUID string or slug) to a verified foreign key UUID in Supabase.
        Returns None if not found or invalid to avoid breaking foreign key constraints.
        """
        import uuid
        if not raw_val or not self._supabase:
            return None
        val_str = str(raw_val).strip()
        resolved_uuid = None
        try:
            resolved_uuid = str(uuid.UUID(val_str))
        except (ValueError, AttributeError):
            resolved_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{val_str}"))

        if not hasattr(self, "_fk_cache"):
            self._fk_cache = {}
        if table not in self._fk_cache:
            try:
                res = self._supabase.table(table).select("id").execute()
                self._fk_cache[table] = set(r["id"] for r in (res.data or []))
            except Exception:
                self._fk_cache[table] = set()

        if resolved_uuid in self._fk_cache[table]:
            return resolved_uuid
        return None

    def _map_telemetry_for_supabase(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the application telemetry event payload to the PostgreSQL telemetry_events schema.
        Normalizes UUIDs, validates foreign-key references against live catalog entities,
        and packs all rich telemetry taxonomy & context fields into 'metadata' JSONB.
        """
        import uuid
        from datetime import datetime, timezone

        raw_id = item.get("id") or item.get("event_id")
        event_uuid = None
        if raw_id:
            try:
                event_uuid = str(uuid.UUID(str(raw_id)))
            except (ValueError, AttributeError):
                event_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.telemetry.{raw_id}"))
        else:
            event_uuid = str(uuid.uuid4())

        raw_name = (
            item.get("event_name") or
            item.get("event_type") or
            item.get("event_family") or
            "unknown"
        )
        if hasattr(raw_name, "value"):
            raw_name = raw_name.value
        event_name = str(raw_name)[:64]

        session_id = str(item.get("session_id") or item.get("client_session_id") or "anonymous_session")[:64]

        series_uuid = self._resolve_fk_uuid("series", item.get("series_id"), "story_")
        ep_candidate = item.get("episode_id") or (item.get("content_id") if item.get("content_type") == "EPISODE" else None)
        ep_uuid = self._resolve_fk_uuid("episodes", ep_candidate, "ep_")
        ip_uuid = self._resolve_fk_uuid("digital_ips", item.get("ip_id"), "ip_")
        user_uuid = self._resolve_fk_uuid("users", item.get("user_id") or item.get("viewer_id"), "user_")

        playback_sec = 0
        raw_pos = item.get("playback_second") if item.get("playback_second") is not None else item.get("position_seconds")
        if raw_pos is not None:
            try:
                playback_sec = int(round(float(raw_pos)))
            except (ValueError, TypeError):
                playback_sec = 0

        region_code = str(item.get("region_code") or "ZA")[:8]
        device_type = str(item.get("device_type") or item.get("source") or "mobile_pwa")[:32]

        meta = dict(item.get("metadata") or {})
        preserve_keys = (
            "event_id", "event_family", "event_type", "occurred_at", "viewer_id",
            "anonymous_id", "content_type", "content_id", "series_id", "episode_id",
            "position_seconds", "duration_seconds", "milestone_pct", "event_source",
            "event_version", "source", "environment", "is_test", "technical_context",
            "cohort_context", "ingested_at"
        )
        for k in preserve_keys:
            if k in item and k not in meta:
                v = item[k]
                if hasattr(v, "value"):
                    v = v.value
                meta[k] = v

        created_at = (
            item.get("created_at") or
            item.get("occurred_at") or
            item.get("ingested_at") or
            datetime.now(timezone.utc).isoformat()
        )

        return {
            "id": event_uuid,
            "event_name": event_name,
            "session_id": session_id,
            "series_id": series_uuid,
            "episode_id": ep_uuid,
            "ip_id": ip_uuid,
            "user_id": user_uuid,
            "playback_second": playback_sec,
            "region_code": region_code,
            "device_type": device_type,
            "metadata": meta,
            "created_at": created_at
        }

    def _map_audit_for_supabase(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps the application security audit payload to the PostgreSQL security_audit_ledger schema.
        Packs before_state, after_state, and metadata into the 'details' JSONB column,
        maps 'timestamp' to 'created_at', and preserves all hash-chain integrity fields.
        """
        from datetime import datetime, timezone
        details = item.get("details")
        if not details or not isinstance(details, dict):
            details = {
                "before_state": item.get("before_state", {}),
                "after_state": item.get("after_state", {}),
                "metadata": item.get("metadata", {})
            }
        
        mapped = {
            "event_id": item["event_id"],
            "domain": str(item.get("domain") or "SECURITY").upper()[:32],
            "event_type": str(item.get("event_type") or "unknown")[:64],
            "actor_id": str(item.get("actor_id") or "system")[:64],
            "actor_role": str(item.get("actor_role") or "system")[:32],
            "target_type": str(item.get("target_type") or "system")[:64],
            "target_id": str(item.get("target_id") or "system")[:64],
            "payload_hash": str(item.get("payload_hash") or "0" * 64)[:64],
            "previous_hash": str(item.get("previous_hash") or "0" * 64)[:64],
            "entry_hash": str(item.get("entry_hash") or "0" * 64)[:64],
            "details": details,
            "created_at": item.get("created_at") or item.get("timestamp") or datetime.now(timezone.utc).isoformat()
        }
        return mapped

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
