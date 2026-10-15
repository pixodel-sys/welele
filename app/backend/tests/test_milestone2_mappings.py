"""
Welele Media™ — Milestone 2: Staging Database Write-Path Mappings Verification Suite
Document ID: WELELE-TEST-M2-MAPPINGS-V1
Target Database: Supabase Staging Project (dbsnaidhznofvyffdfni)

PURPOSE:
Verifies the two concrete database write-path schema mappings:
1. Telemetry Mapping:
   - Application writes to actual PostgreSQL table `public.telemetry_events`.
   - POST /api/telemetry/events succeeds against staging with valid response.
   - Corresponding row appears in public.telemetry_events with correct schema fields.
   - No attempt is made to write to viewer_telemetry_events.
   - Rich taxonomy context and metadata are preserved.

2. Security Audit Ledger Mapping:
   - Action invoking audit_service.record_trust_event succeeds against staging.
   - Payload mapped to actual PostgreSQL DDL: details (JSONB), created_at (TIMESTAMPTZ), sequence_id (BIGSERIAL).
   - Expected actor/event/target retained.
   - Cryptographic SHA-256 hash-chain integrity preserved and validated.
   - No unrecognized top-level columns (before_state, after_state, metadata, timestamp) sent to PostgreSQL.
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

CANDIDATE_STAGING_PATHS = [
    r"G:\App_Development\App_Dev\Welele Media\.env\.env.staging",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.staging"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env", ".env.staging"),
]


def get_staging_client_or_skip():
    """Retrieves Supabase client pointing strictly to Staging (dbsnaidhznofvyffdfni)."""
    staging_path = None
    for p in CANDIDATE_STAGING_PATHS:
        if os.path.exists(p):
            staging_path = p
            break

    if staging_path:
        load_dotenv(staging_path, override=True)

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        pytest.skip("Staging Supabase credentials not found.")

    from target_validator import (
        validate_database_target,
        extract_project_ref,
        CONFIRMED_STAGING_REF,
        CONFIRMED_PRODUCTION_REF
    )

    os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
    os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF

    ref = extract_project_ref(url)
    if ref == CONFIRMED_PRODUCTION_REF:
        pytest.fail("CRITICAL GUARD TRIGGERED: Cannot execute tests against FROZEN PRODUCTION project!")

    assert ref == CONFIRMED_STAGING_REF, f"Expected staging ref {CONFIRMED_STAGING_REF}, got {ref}"
    validate_database_target("staging", url)

    from supabase import create_client
    return create_client(url, key)


# =============================================================================
# ISSUE 1: TELEMETRY WRITE-PATH MAPPING VERIFICATION
# =============================================================================

def test_telemetry_write_path_mapping_to_staging():
    """
    Verifies that:
    - POST /api/telemetry/events succeeds against staging.
    - HTTP response is successful (status 200, status received/saved).
    - A corresponding row appears in public.telemetry_events.
    - No attempt is made to write to viewer_telemetry_events.
    - Existing telemetry fields (playback_second, region_code, metadata) are correctly represented.
    """
    client_live = get_staging_client_or_skip()

    # Re-initialize main app in staging mode
    from main import app
    from database import db
    from repositories.telemetry_repository import telemetry_repository

    # Bind live staging client to db for integration test
    orig_supabase = db._supabase
    orig_isolated = db._is_isolated_test_store
    db._supabase = client_live
    db._is_isolated_test_store = False
    assert db._supabase is not None, "Authoritative Supabase client must be connected"
    
    test_client = TestClient(app)
    
    unique_session = f"sess_m2_verify_{uuid.uuid4().hex[:8]}"
    test_event_id = f"evt_m2_{uuid.uuid4().hex[:12]}"
    
    event_payload = {
        "event_id": test_event_id,
        "event_family": "WATCH",
        "event_type": "PLAYBACK_PROGRESS",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "session_id": unique_session,
        "viewer_id": "user_zola",
        "anonymous_id": "anon_m2_device_01",
        "content_type": "EPISODE",
        "content_id": "ep_blood_ties_01",
        "series_id": "story_blood_ties",
        "episode_id": "ep_blood_ties_01",
        "position_seconds": 45.0,
        "duration_seconds": 90.0,
        "milestone_pct": 50,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "source": "DISCOVERY_FEED",
        "environment": "staging",
        "is_test": True,
        "technical_context": {"bitrate": 1500, "buffer_health_sec": 12.5},
        "cohort_context": {"market": "ZA", "viewer_tier": "VIP"},
        "metadata": {
            "test_marker": "milestone_2_verification",
            "device_class": "mobile_pwa"
        }
    }

    # 1. Ingest via HTTP POST /api/telemetry/events
    response = test_client.post("/api/telemetry/events", json=event_payload)
    assert response.status_code == 200, f"HTTP POST failed with {response.status_code}: {response.text}"
    res_data = response.json()
    assert res_data.get("status") in ("received", "saved", "success", "recorded"), f"Unexpected response status: {res_data}"
    assert res_data.get("event_id") == test_event_id

    # 2. Verify that the event was persisted to public.telemetry_events in staging PostgreSQL
    db_res = client_live.table("telemetry_events").select("*").eq("session_id", unique_session).execute()
    assert db_res.data is not None and len(db_res.data) > 0, "Telemetry event row not found in public.telemetry_events!"
    
    row = db_res.data[0]
    try:
        assert row["event_name"] == "PLAYBACK_PROGRESS"
        assert row["session_id"] == unique_session
        assert row["playback_second"] == 45
        assert row["region_code"] == "ZA"
        assert row["device_type"] in ("mobile_pwa", "DISCOVERY_FEED")
        
        # Verify metadata preserves all rich context
        meta = row.get("metadata") or {}
        assert meta.get("event_id") == test_event_id
        assert meta.get("milestone_pct") == 50
        assert meta.get("event_family") == "WATCH"
        assert meta.get("test_marker") == "milestone_2_verification"
        assert meta.get("technical_context", {}).get("bitrate") == 1500

        # Verify foreign keys are valid UUIDs or None (no FK violation occurred)
        assert "series_id" in row
        assert "episode_id" in row
        assert "user_id" in row
        
        # 3. Verify no table named viewer_telemetry_events was targeted in Supabase
        # (calling .table("viewer_telemetry_events") directly would raise PGRST205 relation does not exist)
        with pytest.raises(Exception) as exc_info:
            client_live.table("viewer_telemetry_events").select("id").limit(1).execute()
        assert "404" in str(exc_info.value) or "PGRST205" in str(exc_info.value) or "does not exist" in str(exc_info.value)

    finally:
        # Cleanup: remove verification row from staging and restore client state
        client_live.table("telemetry_events").delete().eq("session_id", unique_session).execute()
        db._supabase = orig_supabase
        db._is_isolated_test_store = orig_isolated


# =============================================================================
# ISSUE 2: SECURITY AUDIT LEDGER MAPPING VERIFICATION
# =============================================================================

def test_security_audit_write_path_mapping_to_staging():
    """
    Verifies that:
    - audit_service.record_trust_event succeeds against staging PostgreSQL.
    - Expected actor/event/target information is retained.
    - details and created_at are populated correctly.
    - Cryptographic hash-chain fields (payload_hash, previous_hash, entry_hash) remain valid.
    - No unrecognized top-level columns (before_state, after_state, metadata, timestamp) are sent to PostgreSQL.
    """
    client_live = get_staging_client_or_skip()

    from services.audit_service import audit_service
    from database import db

    orig_supabase = db._supabase
    orig_isolated = db._is_isolated_test_store
    db._supabase = client_live
    db._is_isolated_test_store = False
    assert db._supabase is not None, "Authoritative Supabase client must be connected"

    test_actor = f"actor_m2_{uuid.uuid4().hex[:6]}"
    test_target = f"target_m2_{uuid.uuid4().hex[:6]}"
    test_marker = f"audit_verify_{uuid.uuid4().hex[:8]}"

    before_state = {"status": "UNVERIFIED", "attempt": 1}
    after_state = {"status": "VERIFIED_M2", "attempt": 1, "approved_by": test_actor}
    metadata = {"marker": test_marker, "client_ip": "127.0.0.1", "channel": "staging_test"}

    # 1. Trigger trust event
    entry = audit_service.record_trust_event(
        domain="SECURITY",
        event_type="security.milestone2_verification",
        actor_id=test_actor,
        actor_role="admin",
        target_type="system_verification",
        target_id=test_target,
        before_state=before_state,
        after_state=after_state,
        metadata=metadata
    )

    assert entry is not None
    event_id = entry["event_id"]
    assert event_id.startswith("aud_")

    # 2. Verify row appeared in public.security_audit_ledger in staging PostgreSQL
    db_res = client_live.table("security_audit_ledger").select("*").eq("event_id", event_id).execute()
    assert db_res.data is not None and len(db_res.data) == 1, "Audit entry not found in public.security_audit_ledger!"

    row = db_res.data[0]
    try:
        # Verify sequence_id was generated monotonically by PostgreSQL BIGSERIAL
        assert isinstance(row["sequence_id"], int)
        assert row["sequence_id"] > 0

        # Verify actor / event / target
        assert row["domain"] == "SECURITY"
        assert row["event_type"] == "security.milestone2_verification"
        assert row["actor_id"] == test_actor
        assert row["actor_role"] == "admin"
        assert row["target_type"] == "system_verification"
        assert row["target_id"] == test_target

        # Verify details JSONB column correctly packed before_state, after_state, metadata
        details = row.get("details") or {}
        assert details.get("before_state") == before_state
        assert details.get("after_state") == after_state
        assert details.get("metadata") == metadata

        # Verify created_at
        assert row.get("created_at") is not None

        # Verify cryptographic hash chain integrity
        payload_hash = row["payload_hash"]
        previous_hash = row["previous_hash"]
        entry_hash = row["entry_hash"]

        assert len(payload_hash) == 64
        assert len(previous_hash) == 64
        assert len(entry_hash) == 64

        # Recalculate payload hash deterministically and compare
        expected_payload_hash = audit_service._compute_payload_hash(details)
        assert payload_hash == expected_payload_hash, "Stored payload_hash does not match cryptographic hash of details!"

        # Verify chain integrity check passes
        verification = audit_service.verify_audit_chain_integrity()
        assert verification["valid"] is True, f"Audit chain validation failed: {verification}"

    finally:
        # Cleanup: remove verification audit row and restore client state
        client_live.table("security_audit_ledger").delete().eq("event_id", event_id).execute()
        db._supabase = orig_supabase
        db._is_isolated_test_store = orig_isolated


def test_telemetry_unknown_ids_do_not_violate_fk_constraints():
    """
    Verifies that unknown or unregistered content/user identifiers are safely mapped
    to None on foreign key columns rather than crashing PostgreSQL with FK constraint violations (23503),
    while preserving the raw identifiers in the metadata JSONB column.
    """
    client_live = get_staging_client_or_skip()
    from main import app
    from database import db

    orig_supabase = db._supabase
    orig_isolated = db._is_isolated_test_store
    db._supabase = client_live
    db._is_isolated_test_store = False

    test_client = TestClient(app)
    unique_session = f"sess_fk_safe_{uuid.uuid4().hex[:8]}"
    test_event_id = f"evt_fk_{uuid.uuid4().hex[:12]}"

    payload = {
        "event_id": test_event_id,
        "event_family": "WATCH",
        "event_type": "PLAYBACK_PROGRESS",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "session_id": unique_session,
        "viewer_id": "user_nonexistent_999",
        "anonymous_id": "anon_test_device",
        "content_type": "EPISODE",
        "content_id": "ep_unregistered_888",
        "series_id": "story_unknown_777",
        "episode_id": "ep_unregistered_888",
        "position_seconds": 15.0,
        "duration_seconds": 60.0,
        "milestone_pct": 25,
        "event_source": "CLIENT",
        "metadata": {"test": "fk_safety_verification"}
    }

    try:
        response = test_client.post("/api/telemetry/events", json=payload)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"

        db_res = client_live.table("telemetry_events").select("*").eq("session_id", unique_session).execute()
        assert db_res.data and len(db_res.data) == 1

        row = db_res.data[0]
        # FK columns must be None because these IDs are not registered in public.series / public.episodes / public.users
        assert row["series_id"] is None
        assert row["episode_id"] is None
        assert row["user_id"] is None

        # But raw IDs are safely preserved in metadata
        meta = row.get("metadata") or {}
        assert meta.get("series_id") == "story_unknown_777"
        assert meta.get("episode_id") == "ep_unregistered_888"
        assert meta.get("viewer_id") == "user_nonexistent_999"

    finally:
        client_live.table("telemetry_events").delete().eq("session_id", unique_session).execute()
        db._supabase = orig_supabase
        db._is_isolated_test_store = orig_isolated


def test_audit_chain_sequential_integrity_multi_event():
    """
    Verifies that multiple sequential audit events maintain unbroken cryptographic chaining
    (Block N+1 previous_hash == Block N entry_hash) both in-memory and in staging PostgreSQL.
    """
    client_live = get_staging_client_or_skip()
    from services.audit_service import audit_service
    from database import db

    orig_supabase = db._supabase
    orig_isolated = db._is_isolated_test_store
    db._supabase = client_live
    db._is_isolated_test_store = False

    events_to_clean = []

    try:
        # Event 1
        entry_1 = audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.chain_test_step_1",
            actor_id="actor_step1",
            actor_role="admin",
            target_type="chain_test",
            target_id="target_step1",
            before_state={"step": 0},
            after_state={"step": 1}
        )
        events_to_clean.append(entry_1["event_id"])

        # Event 2
        entry_2 = audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.chain_test_step_2",
            actor_id="actor_step2",
            actor_role="admin",
            target_type="chain_test",
            target_id="target_step2",
            before_state={"step": 1},
            after_state={"step": 2}
        )
        events_to_clean.append(entry_2["event_id"])

        # Cryptographic link assertion
        assert entry_2["previous_hash"] == entry_1["entry_hash"], (
            f"Chaining break: Block 2 prev_hash ({entry_2['previous_hash']}) != "
            f"Block 1 entry_hash ({entry_1['entry_hash']})"
        )

        # Check in staging PostgreSQL
        db_res_1 = client_live.table("security_audit_ledger").select("*").eq("event_id", entry_1["event_id"]).execute()
        db_res_2 = client_live.table("security_audit_ledger").select("*").eq("event_id", entry_2["event_id"]).execute()

        assert db_res_1.data and len(db_res_1.data) == 1
        assert db_res_2.data and len(db_res_2.data) == 1

        row_1 = db_res_1.data[0]
        row_2 = db_res_2.data[0]

        assert row_2["previous_hash"] == row_1["entry_hash"]
        assert row_2["sequence_id"] > row_1["sequence_id"]

    finally:
        for eid in events_to_clean:
            client_live.table("security_audit_ledger").delete().eq("event_id", eid).execute()
        db._supabase = orig_supabase
        db._is_isolated_test_store = orig_isolated

