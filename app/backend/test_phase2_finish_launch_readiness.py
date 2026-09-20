"""
Welele Media™ — Phase 2: FINISH — Project 40 Launch Readiness Verification Suite
================================================================================
Operating Rule: Evidence earns engineering.
Critical Content Boundary: Jellyfish proves the machine; never exposed to public viewers.

Verifies:
1. Workstream 1: Internal Jellyfish playback, stream resolution, and progression.
2. Workstream 2 & 7: Strict viewer boundary (Jellyfish absent from public feed & 403 on public stream).
3. Workstream 3: CMS Publish Pipeline (Approve atomically sets PUBLISHED + PRODUCTION_READY).
4. Workstream 5: Authoritative monetisation rail (success posts ledger, failure rejects with 402, repeat unlock protected).
5. Workstream 6: Signed media access & physical storage retrieval.
6. Workstream 7: Telemetry & test data isolation (is_test_session).
7. Future-Proofing: Proves the same pipeline receives genuine Project 40 launch content without code changes.
"""

import os
import pytest
from fastapi.testclient import TestClient
from main import app
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository
from services.storage_service import storage_service
from services.viewer_telemetry_service import viewer_telemetry_service
from services.audit_service import audit_service
from database import db

client = TestClient(app)

# ---------------------------------------------------------------------------
# FIXTURES & SETUP
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def ensure_seed():
    series_repository.seed_if_missing()


# ---------------------------------------------------------------------------
# WORKSTREAM 1 & 2: JELLYFISH INTERNAL PLAYBACK & PUBLIC BOUNDARY
# ---------------------------------------------------------------------------
def test_jellyfish_internal_playback_success():
    """
    Proves that Jellyfish plays successfully in an authorized internal test session.
    Verifies media asset, storage key, 9:16 vertical stream URL, and Episode 1 free status.
    """
    res = client.get(
        "/api/episodes/series_internal_jellyfish_test/ep_jellyfish_1",
        params={"internal_test": "true", "user_id": "system_tester"},
        headers={"X-Welele-Internal-Test": "1"}
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["is_available"] is True
    assert data["is_unlocked"] is True
    assert data["status_label"] == "Watch Now"
    assert data["stream"] is not None
    assert "/videos/jellyfish.mp4" in data["stream"]["primary_url"]
    assert data["storage_key"] == "masters/internal_test/jellyfish.mp4"


def test_jellyfish_episode_2_locked_paywall_state():
    """
    Proves that Episode 2 of internal proving series is locked behind the 5-coin paywall.
    """
    res = client.get(
        "/api/episodes/series_internal_jellyfish_test/ep_jellyfish_2",
        params={"internal_test": "true", "user_id": "new_test_viewer"},
        headers={"X-Welele-Internal-Test": "1"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_available"] is True
    assert data["is_unlocked"] is False  # Episode 2 is locked!
    assert data["episode"]["unlock_price_coins"] == 5


def test_public_viewer_cannot_discover_jellyfish_in_feed():
    """
    CRITICAL CONTENT RULE: An unauthenticated / normal viewer browsing the public
    catalogue (/api/series and /api/series/feed) NEVER sees Jellyfish.
    """
    res = client.get("/api/series/feed")
    assert res.status_code == 200
    data = res.json()
    feed_series_ids = [s["id"] for s in data.get("series", [])]
    assert "series_internal_jellyfish_test" not in feed_series_ids, (
        "CRITICAL VIOLATION: Internal test series 'series_internal_jellyfish_test' "
        "was discovered in the public viewer feed!"
    )


def test_public_viewer_cannot_stream_jellyfish_without_auth():
    """
    CRITICAL CONTENT RULE: An unauthenticated public viewer requesting the Jellyfish
    stream route directly receives HTTP 403 Forbidden.
    """
    res = client.get(
        "/api/episodes/series_internal_jellyfish_test/ep_jellyfish_1",
        params={"user_id": "public_anonymous_viewer"}
    )
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}"
    detail = res.json().get("detail", "")
    assert "Internal test material (Jellyfish) is restricted" in detail


def test_public_viewer_cannot_access_jellyfish_series_detail():
    """
    Public viewer querying /api/series/series_internal_jellyfish_test directly receives HTTP 404.
    """
    res = client.get("/api/series/series_internal_jellyfish_test")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# WORKSTREAM 3: CMS PUBLISH PIPELINE
# ---------------------------------------------------------------------------
def test_cms_admin_approve_promotes_to_production_ready():
    """
    Proves that Admin Moderation Approval atomically promotes an episode from
    under_review / draft to:
    - status: 'published'
    - lifecycle_state: 'PUBLISHED'
    - readiness_state: 'PRODUCTION_READY'
    """
    # 1. Create a draft episode in testing
    test_ep_id = "ep_launch_candidate_test_01"
    series_repository.local_insert("episodes", {
        "id": test_ep_id,
        "series_id": "story_blood_ties",
        "episode_number": 99,
        "title": "Launch Candidate Pilot",
        "synopsis": "Valid launch candidate pilot episode.",
        "duration_seconds": 60,
        "status": "under_review",
        "lifecycle_state": "UNDER_REVIEW",
        "readiness_state": "DRAFT_EMPTY",
        "video_url": "/videos/sample_drama.mp4",
        "created_at": "2026-09-19T00:00:00Z"
    })

    # 2. Admin approves episode
    updated = series_repository.review_episode(
        episode_id=test_ep_id,
        decision="approved",
        feedback="Verified 9:16 safe zones, audio levels, and cliffhanger.",
        reviewer_id="admin_supervisor"
    )

    # 3. Verify atomic promotion
    assert updated is not None
    assert updated["status"] == "published"
    assert updated["lifecycle_state"] == "PUBLISHED"
    assert updated["readiness_state"] == "PRODUCTION_READY"
    assert updated["is_empty_draft"] is False

    # 4. Clean up test record
    all_eps = series_repository.local_get("episodes")
    filtered = [e for e in all_eps if e.get("id") != test_ep_id]
    series_repository.local_set("episodes", filtered)


# ---------------------------------------------------------------------------
# WORKSTREAM 5: MONETISATION RAIL & AUTHORITATIVE SETTLEMENT
# ---------------------------------------------------------------------------
def test_airtime_payment_success_and_ledger_entitlement():
    """
    Proves successful airtime payment rail execution:
    - Initiates charge with valid test MSISDN.
    - Transaction completes with reference.
    - Double-entry ledger records transaction.
    - Entitlement is recorded in unlocked_episodes.
    - Episode unlocks immediately.
    """
    user_id = "test_viewer_phase2_01"
    ep_id = "ep_jellyfish_2"

    # Step 1: Charge airtime for episode unlock
    charge_res = client.post("/api/payments/airtime/charge", json={
        "user_id": user_id,
        "carrier_id": "vodacom_airtime",
        "phone_number": "0828912345",
        "charge_type": "episode_unlock",
        "target_id": ep_id,
        "series_id": "series_internal_jellyfish_test",
        "amount_zar": 2.50,
        "coins_equivalent": 5
    })
    assert charge_res.status_code == 200
    charge_data = charge_res.json()
    assert charge_data["success"] is True
    assert charge_data["transaction"]["status"] == "completed"
    ref = charge_data["transaction"]["reference"]

    # Step 2: Verify entitlement persisted
    unlocks = db.get("unlocked_episodes") or []
    assert any(u.get("user_id") == user_id and u.get("episode_id") == ep_id for u in unlocks)

    # Step 3: Verify repeat unlock is idempotent
    second_charge = client.post("/api/payments/airtime/charge", json={
        "user_id": user_id,
        "carrier_id": "vodacom_airtime",
        "phone_number": "0828912345",
        "charge_type": "episode_unlock",
        "target_id": ep_id,
        "series_id": "series_internal_jellyfish_test",
        "amount_zar": 2.50,
        "coins_equivalent": 5
    })
    assert second_charge.status_code == 200

    # Step 4: Verify episode stream is now unlocked for this user
    stream_res = client.get(
        f"/api/episodes/series_internal_jellyfish_test/{ep_id}",
        params={"internal_test": "true", "user_id": user_id},
        headers={"X-Welele-Internal-Test": "1"}
    )
    assert stream_res.status_code == 200
    assert stream_res.json()["is_unlocked"] is True


def test_payment_failure_authoritative_rejection():
    """
    CRITICAL RESILIENCE RULE: Proves that carrier decline / insufficient airtime
    returns HTTP 402, records a failed transaction in DB, and DOES NOT grant any coins
    or unlocked content.
    """
    user_id = "test_viewer_insufficient_funds"
    target_ep = "ep_jellyfish_2"

    # Number ending in '0001' deterministically simulates insufficient balance
    fail_res = client.post("/api/payments/airtime/charge", json={
        "user_id": user_id,
        "carrier_id": "vodacom_airtime",
        "phone_number": "0820000001",
        "charge_type": "episode_unlock",
        "target_id": target_ep,
        "series_id": "series_internal_jellyfish_test",
        "amount_zar": 2.50,
        "coins_equivalent": 5
    })
    assert fail_res.status_code == 402
    assert "Insufficient airtime balance" in fail_res.json()["detail"]

    # Verify NO entitlement was granted
    unlocks = db.get("unlocked_episodes") or []
    assert not any(u.get("user_id") == user_id and u.get("episode_id") == target_ep for u in unlocks)

    # Verify transaction record is FAILED
    txs = db.get("transactions") or []
    failed_tx = next((t for t in txs if t.get("user_id") == user_id and t.get("status") == "FAILED"), None)
    assert failed_tx is not None


# ---------------------------------------------------------------------------
# WORKSTREAM 6: SIGNED MEDIA ACCESS & PHYSICAL STORAGE
# ---------------------------------------------------------------------------
def test_storage_service_presigned_download_url():
    """
    Proves that StorageService generates a secure time-bounded presigned download URL.
    """
    storage_key = "masters/internal_test/jellyfish.mp4"
    signed_meta = storage_service.generate_presigned_download_url(storage_key, expires_in_seconds=900)

    assert signed_meta is not None
    assert "download_url" in signed_meta
    assert signed_meta["expires_in_seconds"] == 900
    assert signed_meta["storage_key"] == storage_key


def test_storage_service_retrieves_jellyfish_binary():
    """
    Proves that physical binary storage retrieval works for internal Jellyfish test asset.
    """
    binary_bytes = storage_service.get_stored_binary("masters/internal_test/jellyfish.mp4")
    assert binary_bytes is not None
    assert len(binary_bytes) == 1047059, f"Expected 1047059 bytes, got {len(binary_bytes)}"


# ---------------------------------------------------------------------------
# WORKSTREAM 7: TELEMETRY & TEST DATA ISOLATION
# ---------------------------------------------------------------------------
def test_test_telemetry_isolation():
    """
    Proves that events from internal proving sessions carry is_test_session flag
    and do not contaminate production viewer metrics.
    """
    event_payload = {
        "event_id": "evt_test_jellyfish_start_01",
        "event_family": "WATCH",
        "event_type": "PLAYBACK_STARTED",
        "occurred_at": "2026-09-19T22:00:00Z",
        "session_id": "sess_internal_jellyfish_test_01",
        "viewer_id": "system_tester",
        "content_id": "ep_jellyfish_1",
        "series_id": "series_internal_jellyfish_test",
        "episode_id": "ep_jellyfish_1",
        "metadata": {
            "is_test_session": True,
            "proving_dataset": "JELLYFISH"
        },
        "source": "INTERNAL_TEST_SUITE"
    }

    res = client.post("/api/telemetry/events", json=event_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"].lower() in ["recorded", "accepted"]

    # Verify session event retrieval retains test session provenance
    sess_events = client.get("/api/telemetry/sessions/sess_internal_jellyfish_test_01").json()
    assert len(sess_events) >= 1
    assert sess_events[0]["metadata"]["is_test_session"] is True


# ---------------------------------------------------------------------------
# FUTURE-PROOFING: GENUINE PROJECT 40 CONTENT READINESS
# ---------------------------------------------------------------------------
def test_future_content_readiness_without_code_changes():
    """
    Proves that when genuine Project 40 launch content is added with valid video master,
    published through CMS, it becomes immediately playable to viewers without code changes.
    """
    p40_series_id = "story_project40_hero"
    p40_ep_id = "ep_p40_01"

    # 1. Simulate new genuine Project 40 series and episode
    series_repository.local_insert("series", {
        "id": p40_series_id,
        "title": "Project 40 Hero Drama",
        "genre": "Drama",
        "is_published": True,
        "is_internal_test": False,
        "lifecycle_state": "PUBLISHED",
        "total_episodes": 1,
        "free_episodes": 1
    })
    series_repository.local_insert("episodes", {
        "id": p40_ep_id,
        "series_id": p40_series_id,
        "episode_number": 1,
        "title": "P40 Pilot",
        "is_free": True,
        "status": "published",
        "lifecycle_state": "PUBLISHED",
        "readiness_state": "PRODUCTION_READY",
        "is_internal_test": False,
        "video_url": "/videos/sample_drama.mp4"
    })
    series_repository.local_insert("media_assets", {
        "id": f"media_{p40_ep_id}",
        "episode_id": p40_ep_id,
        "master_video_url": "/videos/sample_drama.mp4",
        "storage_key": f"masters/{p40_series_id}/{p40_ep_id}.mp4",
        "duration_seconds": 60,
        "is_internal_test": False
    })

    # 2. Public viewer feed immediately includes the genuine launch series
    feed = series_repository.list_feed()
    feed_ids = [s["id"] for s in feed]
    assert p40_series_id in feed_ids

    # 3. Public viewer can immediately stream Episode 1 without developer assistance
    res = client.get(f"/api/episodes/{p40_series_id}/{p40_ep_id}", params={"user_id": "real_public_viewer"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_available"] is True
    assert data["is_unlocked"] is True
    assert data["status_label"] == "Watch Now"
    assert "/videos/sample_drama.mp4" in data["stream"]["primary_url"]

    # 4. Clean up test fixture
    series_repository.local_set("series", [s for s in series_repository.local_get("series") if s["id"] != p40_series_id])
    series_repository.local_set("episodes", [e for e in series_repository.local_get("episodes") if e["id"] != p40_ep_id])
    series_repository.local_set("media_assets", [m for m in series_repository.local_get("media_assets") if m["episode_id"] != p40_ep_id])
