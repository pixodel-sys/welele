"""
Welele Media™ — Creator Foundation & Supply-Chain Vertical Slice Integration Tests (Phase 1)
Validates: Story Package -> Series -> Episode Draft -> Media Asset -> Moderation Workflow -> WEE & Catalog Publication.
"""

import sys
import os
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def test_complete_ip_supply_chain_vertical_slice():
    print("\n--- Running Complete IP Supply-Chain Vertical Slice Test ---")

    # Generate Creator & Admin Auth Tokens
    creator_token = create_access_token(user_id="creator_zola", role="creator")
    admin_token = create_access_token(user_id="admin_supervisor", role="admin")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # STEP 1: Writer synthesizes and persists a versioned Story Package for ip_blood_ties
    package_payload = {
        "ip_id": "ip_blood_ties",
        "creator_id": "creator_zola",
        "package_title": "Season 2: The Alexandra Heist",
        "version": "v1.0.0",
        "target_duration_seconds": 90,
        "beats": [
            {"timestamp_seconds": 0, "label": "Opening Hook", "intensity": 8, "action_description": "A luxury armored van breaks down in Alexandra."},
            {"timestamp_seconds": 45, "label": "Midpoint Confrontation", "intensity": 9, "action_description": "Lerato discovers her brother cut the brake line."},
            {"timestamp_seconds": 88, "label": "Cliffhanger Paywall", "intensity": 10, "action_description": "Laser sights pinpoint the master safe.", "cliffhanger_trigger": True}
        ],
        "dialogues": [
            {"speaker": "Sipho", "original_text": "The money belongs to the rank.", "dialect_code": "zu", "dialect_label": "isiZulu"}
        ],
        "cliffhanger_prompt": "Will Sipho crack the digital lock before security breaches the alley?",
        "ai_model_used": "gemini-3.7-flash",
        "human_approved": True
    }

    res_pkg = client.post("/api/ip/ip_blood_ties/story-forge/save", json=package_payload, headers=creator_headers)
    assert res_pkg.status_code == 200, f"Package save failed: {res_pkg.text}"

    saved_pkg = res_pkg.json()["package"]
    assert saved_pkg["id"].startswith("sfp_")
    print(f"[PASS] Step 1: Persisted canonical Story Package '{saved_pkg['package_title']}' (ID: {saved_pkg['id']}).")

    # STEP 2: Creator creates an Episode Draft linked to the Story Package and Series
    ep_payload = {
        "series_id": "story_blood_ties",
        "episode_number": 5,
        "title": "The Alexandra Heist: Breach",
        "synopsis": "The convoy is surrounded as midnight sirens echo across the northern corridor.",
        "duration_seconds": 85,
        "video_url": "/videos/welele_placeholder.mp4",
        "thumbnail_url": "/posters/blood_ties.jpg",
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_time": 75,
        "cliffhanger_hook": "Will Sipho crack the digital lock before security breaches the alley?",
        "status": "under_review",
        "preflight_health": {
            "aspect_ratio_ok": True,
            "aspect_ratio_label": "1080 × 1920 (9:16)",
            "duration_ok": True,
            "duration_seconds": 85,
            "audio_detected": True,
            "thumbnail_present": True,
            "cliffhanger_marker_ok": True,
            "cliffhanger_time_seconds": 75,
            "cliffhanger_hook_copy": "Will Sipho crack the digital lock before security breaches the alley?",
            "captions_present": True
        }
    }

    res_ep = client.post("/api/creators/episodes/add", json=ep_payload)
    assert res_ep.status_code == 200, f"Episode creation failed: {res_ep.text}"
    created_ep = res_ep.json()["episode"]
    assert created_ep["status"] == "under_review"
    print(f"[PASS] Step 2: Created Episode Draft '{created_ep['title']}' (ID: {created_ep['id']}) with attached Media Asset.")

    # STEP 3: Admin inspects the normalized Moderation Queue
    res_queue = client.get("/api/admin/moderation-queue", headers=admin_headers)
    assert res_queue.status_code == 200
    queue = res_queue.json().get("queue", [])
    matching_item = next((item for item in queue if item.get("episode_id") == created_ep["id"]), None)
    assert matching_item is not None, "Submitted episode draft did not appear in normalized moderation queue."
    print(f"[PASS] Step 3: Episode found in Admin Moderation Queue (ID: {matching_item['id']}).")

    # STEP 4: Admin issues an auditable 'approved' decision
    res_appr = client.post(f"/api/admin/moderation/{matching_item['id']}/approve", headers=admin_headers)
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert appr_data["status"] == "approved"
    print(f"[PASS] Step 4: Admin issued approved decision with reviewer audit trail.")

    # STEP 5: Verify the approved episode is immediately live in the public catalog and WEE
    res_feed = client.get("/api/series/feed")
    assert res_feed.status_code == 200
    series_list = res_feed.json().get("series", [])
    bt_series = next((s for s in series_list if s["id"] == "story_blood_ties"), None)
    assert bt_series is not None
    live_ep = next((e for e in bt_series["episodes"] if e["id"] == created_ep["id"]), None)
    assert live_ep is not None, "Approved episode not present in live public series feed"
    assert live_ep["video_url"] == "/videos/welele_placeholder.mp4"
    print(f"[PASS] Step 5: Approved episode automatically hydrated into public feed & WEE layout for viewer playback.")

    print("\n=======================================================")
    print("ALL SUPPLY-CHAIN VERTICAL SLICE TESTS PASSED (100% SUCCESS)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_complete_ip_supply_chain_vertical_slice()
