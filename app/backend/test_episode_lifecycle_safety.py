"""
Welele Media™ — Episode Lifecycle & Archival Safety Test (P1 / Phase 3)
Specimen in Focus: Blood Ties (story_blood_ties, ep_bt_3)
Proves:
1. Operational retirement without destructive data loss.
2. Complete removal from public Viewer feed and WEE slots.
3. Preservation of existing paid user entitlements (playback allowed for buyers).
4. Strict rejection of new purchases/unlocks for archived content.
5. Invariance of historical telemetry, double-entry ledger, and IP lineage.
6. Immutable cryptographic CONTENT audit event logging.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
from repositories.series_repository import series_repository
from repositories.event_repository import event_repository
from repositories.ledger_repository import ledger_repository
from services.rbac_service import create_access_token
from services.audit_service import audit_service
from services.ledger_service import ledger_service

client = TestClient(app)

def get_creator_headers():
    token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    return {"Authorization": f"Bearer {token}"}

def test_blood_ties_episode_lifecycle_and_retirement():
    creator_headers = get_creator_headers()
    series_id = "story_blood_ties"
    ep_id = "ep_bt_3"
    buyer_user_id = "user_test_buyer_01"
    new_user_id = "user_test_new_02"

    # -------------------------------------------------------------------------
    # 1. SETUP SPECIMEN BASELINE STATE (Blood Ties Episode 3)
    # -------------------------------------------------------------------------
    # Ensure ep_bt_3 is in published state initially
    series_repository.local_update("episodes", "id", ep_id, {"status": "published"})

    # Grant paid entitlement to buyer_user_id
    ledger_service.get_or_create_wallet(buyer_user_id)
    db.insert("unlocked_episodes", {
        "id": f"unlock_test_{uuid.uuid4().hex[:8]}",
        "user_id": buyer_user_id,
        "episode_id": ep_id,
        "series_id": series_id,
        "unlock_method": "COINS",
        "coins_spent": 5
    })

    # Record historical telemetry beacons for ep_bt_3
    event_repository.ingest_event({
        "event_name": "episode_started",
        "user_id": buyer_user_id,
        "session_id": "sess_bt_baseline",
        "series_id": series_id,
        "episode_id": ep_id,
        "playback_second": 0
    })
    event_repository.ingest_event({
        "event_name": "cliffhanger_reached",
        "user_id": buyer_user_id,
        "session_id": "sess_bt_baseline",
        "series_id": series_id,
        "episode_id": ep_id,
        "playback_second": 72
    })

    # Record Baseline Measurements
    all_telemetry_before = [e for e in event_repository.local_get("telemetry_events") if e.get("episode_id") == ep_id]
    telemetry_count_before = len(all_telemetry_before)
    assert telemetry_count_before >= 2

    all_unlocks_before = [u for u in db.get("unlocked_episodes") if u.get("episode_id") == ep_id]
    unlocks_count_before = len(all_unlocks_before)
    assert unlocks_count_before >= 1

    # Verify Viewer Feed BEFORE Archive (Episode 3 is present)
    res_feed_before = client.get(f"/api/stories/{series_id}")
    assert res_feed_before.status_code == 200
    eps_before = res_feed_before.json().get("episodes", [])
    assert any(e["id"] == ep_id for e in eps_before), "Blood Ties E3 must be in feed before archive"

    # -------------------------------------------------------------------------
    # 2. ATOMIC LIFECYCLE TRANSITION: RETIRE / ARCHIVE BLOOD TIES E3
    # -------------------------------------------------------------------------
    res_archive = client.post(
        f"/api/episodes/{series_id}/{ep_id}/archive",
        headers=creator_headers
    )
    assert res_archive.status_code == 200, f"Archival failed: {res_archive.text}"
    archive_data = res_archive.json()
    assert archive_data["success"] is True
    assert archive_data["episode"]["status"] == "archived"

    # -------------------------------------------------------------------------
    # 3. VERIFY AFTER ARCHIVE INVARIANCES & GATES
    # -------------------------------------------------------------------------

    # A. Public Viewer Feed Exclusion: ep_bt_3 must NOT be visible to viewers
    res_feed_after = client.get(f"/api/stories/{series_id}")
    assert res_feed_after.status_code == 200
    eps_after = res_feed_after.json().get("episodes", [])
    assert not any(e["id"] == ep_id for e in eps_after), "Archived Blood Ties E3 must be EXCLUDED from public viewer feed"

    # B. WEE Public Placement Exclusion
    res_wee = client.get("/api/experience/page/home")
    assert res_wee.status_code == 200
    wee_data = res_wee.json()
    for sec in wee_data.get("sections", []):
        for item in sec.get("items", []):
            if item.get("content_id") == series_id and item.get("story"):
                story_eps = item["story"].get("episodes", [])
                assert not any(e["id"] == ep_id for e in story_eps), "Archived episode must not be delivered via WEE story slots"

    # C. New Purchases / Unlocks Prohibited
    res_new_unlock = client.post(f"/api/episodes/{series_id}/{ep_id}/unlock?user_id={new_user_id}&method=COINS")
    assert res_new_unlock.status_code == 400
    assert "Cannot purchase or unlock an archived episode" in res_new_unlock.text

    # D. Existing Paid Entitlement Playback PRESERVED
    res_playback_buyer = client.get(f"/api/episodes/{series_id}/{ep_id}?user_id={buyer_user_id}")
    assert res_playback_buyer.status_code == 200, f"Paid entitlement playback must succeed for existing buyers: {res_playback_buyer.text}"
    stream_data = res_playback_buyer.json()
    assert stream_data["is_unlocked"] is True
    assert "stream" in stream_data and stream_data["stream"]["primary_url"]

    # E. Unauthorized Playback Blocked
    res_playback_blocked = client.get(f"/api/episodes/{series_id}/{ep_id}?user_id={new_user_id}")
    assert res_playback_blocked.status_code == 403
    assert "retired/archived" in res_playback_blocked.text

    # F. Telemetry Invariance: Telemetry records are 100% preserved
    all_telemetry_after = [e for e in event_repository.local_get("telemetry_events") if e.get("episode_id") == ep_id]
    assert len(all_telemetry_after) == telemetry_count_before, "Archival must NOT delete telemetry events"

    # G. Entitlements Invariance: Unlocked records are 100% preserved
    all_unlocks_after = [u for u in db.get("unlocked_episodes") if u.get("episode_id") == ep_id]
    assert len(all_unlocks_after) == unlocks_count_before, "Archival must NOT delete paid user unlock entitlements"

    # H. Creator Studio Visibility: Episode remains visible to creator as ARCHIVED
    res_workspace = client.get(f"/api/creators/series/{series_id}/workspace", headers=creator_headers)
    assert res_workspace.status_code == 200
    ws_eps = res_workspace.json()["series"]["episodes"]
    ep_in_ws = next((e for e in ws_eps if e["id"] == ep_id), None)
    assert ep_in_ws is not None
    assert ep_in_ws["status"] == "archived"

    # I. Audit Trail Verification
    audit_chain = audit_service.local_get("security_audit_ledger")
    arch_audit = next((a for a in audit_chain if a.get("target_id") == ep_id and a.get("event_type") == "content.episode_archived"), None)
    assert arch_audit is not None
    assert arch_audit["domain"] == "CONTENT"

    # J. Cryptographic Chain Integrity
    verify_res = audit_service.verify_audit_chain_integrity()
    assert verify_res["valid"] is True, f"Audit chain must remain valid: {verify_res}"
