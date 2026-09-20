"""
Welele Media™ — Cold Start Regression Test
Verifies that database.py correctly bootstraps when welele_store.json
does not exist on disk (fresh clone / clean deployment / gitignore removes file).

Expected behaviour:
  - The data directory is created automatically (os.makedirs)
  - An empty store is written to disk (_save called from _load's else branch)
  - All canonical collections are present and empty
  - Insert and read operations succeed immediately after cold boot

This test MUST NOT restore welele_store.json to git.
This test MUST NOT depend on the canonical store file existing.
"""

import os
import json
import tempfile
import threading
import pytest


def _make_fresh_database(store_path: str):
    """
    Instantiate a Database with a custom store path pointing to a file
    that does not yet exist, simulating a cold-start environment.
    Uses the isolation mechanism already built into the Database class.
    """
    from database import Database
    instance = Database.__new__(Database)

    # Replicate __new__ initialisation without triggering the singleton
    instance.data = {
        "digital_ips": [], "story_worlds": [], "character_bibles": [],
        "rights_ledger": [], "story_forge_packages": [], "stories": [],
        "series": [], "creators": [], "episodes": [], "media_assets": [],
        "media_jobs": [], "media_renditions": [], "users": [], "wallets": [],
        "coin_ledger": [], "payment_events": [], "unlocked_episodes": [],
        "payment_transactions": [], "bullet_comments": [], "transactions": [],
        "gifts": [], "comments": [], "reactions": [], "moderation_queue": [],
        "experience_layouts": [], "telemetry_events": [],
        "viewer_telemetry_events": [], "production_bibles": [],
        "episode_blueprints": [], "episode_production_packs": [],
        "intelligence_evidence": [], "intelligence_recommendations": [],
        "content_intelligence_records": [], "content_decisions": [],
        "content_intelligence_evidence_packages": [], "security_audit_ledger": [],
    }
    instance._supabase = None
    instance._canonical_store_path = os.path.abspath(store_path)
    instance._active_store_path = os.path.abspath(store_path)
    instance._is_isolated_test_store = False
    instance._read_only_canonical_guard = False
    instance._temp_store_file = None
    instance._lock = threading.Lock()
    instance._load()
    return instance


class TestColdStartNoStore:
    """
    Regression: database bootstraps correctly when welele_store.json
    does not exist on disk at startup.
    """

    def test_cold_start_creates_file_automatically(self, tmp_path):
        """
        GIVEN  no welele_store.json exists on disk
        WHEN   the Database initialises
        THEN   the file is created automatically
        AND    the data directory is created if it did not exist
        """
        store_path = tmp_path / "data" / "welele_store.json"

        # Confirm the file does NOT exist before boot
        assert not store_path.exists(), "Pre-condition failed: store file must not exist before cold start"

        db = _make_fresh_database(str(store_path))

        assert store_path.exists(), "Cold start must create welele_store.json automatically"
        assert store_path.parent.is_dir(), "Cold start must create parent data directory automatically"

    def test_cold_start_produces_valid_empty_store(self, tmp_path):
        """
        GIVEN  no welele_store.json exists
        WHEN   the Database initialises
        THEN   the written file contains valid JSON
        AND    all canonical collections are present and empty
        """
        store_path = tmp_path / "data" / "welele_store.json"
        db = _make_fresh_database(str(store_path))

        with open(store_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        assert isinstance(content, dict), "Store must be a JSON object"
        assert "telemetry_events" in content, "Canonical collection 'telemetry_events' must exist"
        assert "security_audit_ledger" in content, "Canonical collection 'security_audit_ledger' must exist"
        assert content["telemetry_events"] == [], "Collections must start empty on cold start"
        assert content["stories"] == [], "Collections must start empty on cold start"

    def test_cold_start_insert_and_read_succeeds(self, tmp_path):
        """
        GIVEN  a cold-started database with no prior store
        WHEN   a record is inserted
        THEN   it can be immediately read back without error
        """
        store_path = tmp_path / "data" / "welele_store.json"
        db = _make_fresh_database(str(store_path))

        record = {"id": "test_story_001", "title": "Soweto Nights", "genre": "Drama"}
        db.insert("stories", record)

        results = db.get("stories")
        assert len(results) == 1
        assert results[0]["id"] == "test_story_001"
        assert results[0]["title"] == "Soweto Nights"

    def test_cold_start_persists_to_disk(self, tmp_path):
        """
        GIVEN  a cold-started database with an insert committed
        WHEN   the store file is read back from disk directly
        THEN   the inserted record is present in the persisted JSON
        """
        store_path = tmp_path / "data" / "welele_store.json"
        db = _make_fresh_database(str(store_path))

        db.insert("stories", {"id": "persist_check_001", "title": "Durban Heat"})

        with open(store_path, "r", encoding="utf-8") as f:
            persisted = json.load(f)

        ids = [s["id"] for s in persisted.get("stories", [])]
        assert "persist_check_001" in ids, "Inserted record must be persisted to disk on cold start"
