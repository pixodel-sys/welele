"""
Welele Media™ — Acceptance Test: Creator Studio State Reconciliation & Lifecycle Integrity
Verifies the exact lifecycle sequence:
1. Creator uploads EP06 -> status is Under Review
2. Creator Workspace/Dashboard query -> EP06 is present with status 'under_review'
3. Browser Refresh simulation (re-fetch workspace) -> EP06 persists
4. Creator Logout & Login simulation (fresh token authentication) -> EP06 persists
5. Admin Moderation Approval -> EP06 promoted to 'published'
6. Creator refresh -> EP06 status is 'published'
7. Viewer feed -> EP06 now visible in public catalog
8. Viewer entitlement -> Locked by coin price until authorized ledger unlock
"""

import sys
import os
import io
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def test_creator_reconciliation_and_lifecycle():
    # -------------------------------------------------------------------------
    # 1. Setup Creator Auth & Fresh Session
    # -------------------------------------------------------------------------
    creator_id = "creator_zola"
    creator_token_session_1 = create_access_token(user_id=creator_id, role="creator")
    creator_headers_session_1 = {"Authorization": f"Bearer {creator_token_session_1}"}

    series_id = "story_blood_ties"

    # Pre-upload baseline check:
    pre_ws = client.get(f"/api/creators/series/{series_id}/workspace", headers=creator_headers_session_1)
    assert pre_ws.status_code == 200
    pre_ws_data = pre_ws.json()
    initial_episodes = pre_ws_data["series"]["episodes"]
    initial_count = len(initial_episodes)
    target_ep_num = initial_count + 1

    # -------------------------------------------------------------------------
    # 2. Creator Ingests & Submits New Episode Master (Under Review)
    # -------------------------------------------------------------------------
    fake_video_bytes = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + b"\x00" * 1024
    upload_res = client.post(
        "/api/storage/upload-binary",
        files={"file": (f"ep_bt_{target_ep_num}_master.mp4", io.BytesIO(fake_video_bytes), "video/mp4")},
        data={"series_id": series_id, "episode_number": target_ep_num}
    )
    assert upload_res.status_code == 200
    storage_key = upload_res.json()["storage_key"]
    public_cdn_url = upload_res.json()["public_cdn_url"]

    ep_payload = {
        "series_id": series_id,
        "episode_number": target_ep_num,
        "title": f"The Midnight Ledger Ep {target_ep_num}",
        "synopsis": "A midnight safe audit uncovers the missing Khumalo shares.",
        "video_url": public_cdn_url,
        "storage_key": storage_key,
        "thumbnail_url": "/posters/blood_ties.jpg",
        "duration_seconds": 75,
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_time": 68,
        "cliffhanger_hook": "The thumbprint scanner accepts the wrong heir.",
        "status": "under_review",
        "preflight_health": {
            "aspect_ratio_ok": True,
            "duration_ok": True,
            "audio_detected": True,
            "thumbnail_present": True,
            "cliffhanger_marker_ok": True,
            "captions_present": True
        }
    }

    add_res = client.post("/api/creators/episodes/add", json=ep_payload, headers=creator_headers_session_1)
    assert add_res.status_code == 200, f"Add episode failed: {add_res.text}"
    add_data = add_res.json()
    assert add_data["success"] is True
    created_ep = add_data["episode"]
    created_ep_id = created_ep["id"]
    assert created_ep["status"] == "under_review", "Status must be under_review"
    assert add_data["moderation_ticket"] is not None
    print(f"\n[PASS] 1. Episode uploaded & server returned canonical ticket: {add_data['moderation_ticket']}")

    # -------------------------------------------------------------------------
    # 3. Creator Workspace Immediate State Verification
    # -------------------------------------------------------------------------
    ws_res_1 = client.get(f"/api/creators/series/{series_id}/workspace", headers=creator_headers_session_1)
    assert ws_res_1.status_code == 200
    ws_data_1 = ws_res_1.json()
    ws_episodes_1 = ws_data_1["series"]["episodes"]
    
    # Prove the newly added episode is immediately present in the workspace roster
    matched_ep_1 = next((e for e in ws_episodes_1 if e["id"] == created_ep_id), None)
    assert matched_ep_1 is not None, "EP must be present in Creator Workspace immediately"
    assert matched_ep_1["status"] == "under_review", f"Expected under_review, got {matched_ep_1['status']}"
    assert matched_ep_1["is_free"] is False
    assert matched_ep_1["coin_price"] == 5
    assert ws_data_1["metrics"]["under_review_count"] >= 1
    print(f"[PASS] 2. Creator Workspace immediately reflects EP as 'under_review' with commercial price (5 Coins)")

    # -------------------------------------------------------------------------
    # 4. Refresh Browser Simulation (Re-query workspace & dashboard)
    # -------------------------------------------------------------------------
    dash_res_1 = client.get(f"/api/creators/{creator_id}/dashboard", headers=creator_headers_session_1)
    assert dash_res_1.status_code == 200
    dash_data_1 = dash_res_1.json()
    dash_series_1 = next((s for s in dash_data_1["series"] if s["id"] == series_id), None)
    assert dash_series_1 is not None
    dash_ep_1 = next((e for e in dash_series_1["episodes"] if e["id"] == created_ep_id), None)
    assert dash_ep_1 is not None, "EP must persist across dashboard refresh"
    assert dash_ep_1["status"] == "under_review"
    print("[PASS] 3. Creator Dashboard refresh maintains 'under_review' EP in series roster")

    # -------------------------------------------------------------------------
    # 5. Creator Logout & Login Simulation (New Auth Token Session)
    # -------------------------------------------------------------------------
    # Simulate fresh login generating new JWT
    creator_token_session_2 = create_access_token(user_id=creator_id, role="creator")
    creator_headers_session_2 = {"Authorization": f"Bearer {creator_token_session_2}"}

    ws_res_2 = client.get(f"/api/creators/series/{series_id}/workspace", headers=creator_headers_session_2)
    assert ws_res_2.status_code == 200
    ws_data_2 = ws_res_2.json()
    matched_ep_2 = next((e for e in ws_data_2["series"]["episodes"] if e["id"] == created_ep_id), None)
    assert matched_ep_2 is not None, "EP must persist after fresh login session"
    assert matched_ep_2["status"] == "under_review"
    print("[PASS] 4. Fresh Creator Login session reliably returns 'under_review' EP without state loss")

    # -------------------------------------------------------------------------
    # 6. Prove Viewer Feed Does NOT Show the Episode Yet (Viewer Isolation)
    # -------------------------------------------------------------------------
    viewer_feed_pre = client.get("/api/stories/feed")
    assert viewer_feed_pre.status_code == 200
    viewer_stories = viewer_feed_pre.json()["stories"]
    viewer_bt = next((s for s in viewer_stories if s["id"] == series_id), None)
    assert viewer_bt is not None
    viewer_ep_pre = next((e for e in viewer_bt["episodes"] if e["id"] == created_ep_id), None)
    assert viewer_ep_pre is None, "Viewer feed MUST NOT display under_review episode"
    print("[PASS] 5. Viewer Isolation Confirmed: unapproved episode is not visible in public feed")

    # -------------------------------------------------------------------------
    # 7. Admin Moderation Decision: Approve EP
    # -------------------------------------------------------------------------
    admin_token = create_access_token(user_id="admin_supervisor", role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    queue_res = client.get("/api/admin/moderation-queue", headers=admin_headers)
    assert queue_res.status_code == 200
    queue_items = queue_res.json().get("queue", [])
    mod_item = next((item for item in queue_items if item.get("episode_id") == created_ep_id), None)
    assert mod_item is not None, "EP must be present in Admin Moderation Queue"

    appr_res = client.post(f"/api/admin/moderation/{mod_item['id']}/approve", headers=admin_headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
    print(f"[PASS] 6. Admin approved moderation item '{mod_item['id']}'")

    # -------------------------------------------------------------------------
    # 8. Creator Refreshes Workspace -> Status is now 'published'
    # -------------------------------------------------------------------------
    ws_res_3 = client.get(f"/api/creators/series/{series_id}/workspace", headers=creator_headers_session_2)
    assert ws_res_3.status_code == 200
    ws_episodes_3 = ws_res_3.json()["series"]["episodes"]
    matched_ep_3 = next((e for e in ws_episodes_3 if e["id"] == created_ep_id), None)
    assert matched_ep_3 is not None
    assert matched_ep_3["status"] == "published", f"Expected published after approval, got {matched_ep_3['status']}"
    print("[PASS] 7. Creator Workspace reflects 'published' status immediately after admin approval")

    # -------------------------------------------------------------------------
    # 9. Viewer Feed -> EP is now visible and governed by Entitlement
    # -------------------------------------------------------------------------
    viewer_feed_post = client.get("/api/stories/feed")
    assert viewer_feed_post.status_code == 200
    viewer_stories_post = viewer_feed_post.json()["stories"]
    viewer_bt_post = next((s for s in viewer_stories_post if s["id"] == series_id), None)
    assert viewer_bt_post is not None
    viewer_ep_post = next((e for e in viewer_bt_post["episodes"] if e["id"] == created_ep_id), None)
    assert viewer_ep_post is not None, "Viewer feed MUST display published episode"

    # Pre-unlock stream request:
    viewer_id = "viewer_auth_test_user"
    ledger_repository.get_or_create_wallet(viewer_id)
    stream_locked_res = client.get(f"/api/episodes/{series_id}/{created_ep_id}?user_id={viewer_id}")
    assert stream_locked_res.status_code == 200
    assert stream_locked_res.json()["is_unlocked"] is False

    # Unlock episode with coins:
    unlock_res = client.post(f"/api/episodes/{series_id}/{created_ep_id}/unlock?user_id={viewer_id}&method=COINS")
    assert unlock_res.status_code == 200

    # Post-unlock stream request:
    stream_unlocked_res = client.get(f"/api/episodes/{series_id}/{created_ep_id}?user_id={viewer_id}")
    assert stream_unlocked_res.status_code == 200
    assert stream_unlocked_res.json()["is_unlocked"] is True
    print("[PASS] 8. Viewer Authorisation & Entitlement verified: Locked -> Unlocked -> Authorised Stream")

    print("\n==================================================================")
    print("CREATOR RECONCILIATION & LIFECYCLE CONTRACT VERIFIED (100% SUCCESS)")
    print("==================================================================\n")

if __name__ == "__main__":
    test_creator_reconciliation_and_lifecycle()
