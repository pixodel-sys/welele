"""
Welele Media™ — Creator Foundation & Episode Pipeline Integration Tests
Validates Creator Studio OS, Series Command Room, 5-Step Pipeline Ingestion, and Moderation Bridge.
"""

from fastapi.testclient import TestClient
from main import app
from database import db
from services.rbac_service import create_access_token

client = TestClient(app)

def test_creator_foundation_and_moderation_bridge():
    print("Testing Creator Studio OS & Episode Pipeline...")

    creator_token = create_access_token(user_id="creator_zola", role="creator")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # 1. Creator Dashboard Metrics
    res_dash = client.get("/api/creators/creator_zola/dashboard", headers=creator_headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert "stats" in dash_data
    assert "series" in dash_data
    assert dash_data["stats"]["total_views"] > 0
    print("[PASS] Creator Dashboard: KPIs & series roster retrieved successfully.")

    # 2. Series Command Room Workspace Data
    stories = db.get("stories")
    assert len(stories) > 0
    test_series_id = stories[0]["id"]
    
    res_work = client.get(f"/api/creators/series/{test_series_id}/workspace", headers=creator_headers)
    assert res_work.status_code == 200
    work_data = res_work.json()
    assert "series" in work_data
    assert "metrics" in work_data
    assert "completion_rate" in work_data["metrics"]
    print(f"[PASS] Series Command Room: Loaded workspace for '{work_data['series']['title']}' with {len(work_data['series']['episodes'])} episodes.")

    # 3. Submit Episode via 5-Step Episode Pipeline
    initial_episodes_count = len(work_data["series"]["episodes"])
    new_ep_payload = {
        "series_id": test_series_id,
        "episode_number": initial_episodes_count + 1,
        "title": "The Secret Will Revealed",
        "synopsis": "The hidden codicil is presented at midnight, catching the Khumalo board off guard.",
        "video_url": "/videos/welele_placeholder.mp4",
        "thumbnail_url": "/posters/blood_ties.jpg",
        "duration_seconds": 68,
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_time": 58,
        "cliffhanger_hook": "Who authorized her DNA test before the funeral?",
        "status": "under_review",
        "preflight_health": {
            "aspect_ratio_ok": True,
            "aspect_ratio_label": "1080 × 1920 (9:16)",
            "duration_ok": True,
            "duration_seconds": 68,
            "audio_detected": True,
            "thumbnail_present": True,
            "cliffhanger_marker_ok": True,
            "cliffhanger_time_seconds": 58,
            "cliffhanger_hook_copy": "Who authorized her DNA test before the funeral?",
            "captions_present": True
        }
    }
    creator_id = stories[0].get("creator_id", "creator_zola")
    creator_token = create_access_token(user_id=creator_id, role="creator")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    res_add = client.post("/api/creators/episodes/add", json=new_ep_payload, headers=creator_headers)
    assert res_add.status_code == 200
    add_data = res_add.json()
    assert add_data["success"] is True
    created_ep = add_data["episode"]
    assert created_ep["status"] == "under_review"
    print(f"[PASS] Episode Pipeline: Ingested episode '{created_ep['title']}' (ID: {created_ep['id']}) with status 'under_review'.")

    # 4. Moderation Bridge: Verify Item Appears in Admin Moderation Queue
    admin_token = create_access_token(user_id="admin_supervisor", role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    res_mod = client.get("/api/admin/moderation-queue", headers=admin_headers)
    assert res_mod.status_code == 200
    queue = res_mod.json().get("queue", [])
    matching_mod_item = next((item for item in queue if item.get("episode_id") == created_ep["id"]), None)
    assert matching_mod_item is not None, "Submitted episode did not bridge into Moderation Queue"
    print(f"[PASS] Admin Moderation Bridge: Episode bridged to queue item '{matching_mod_item['id']}'.")

    # 5. Admin Moderation: Approve Item & Verify Status Sync to Story
    res_appr = client.post(f"/api/admin/moderation/{matching_mod_item['id']}/approve", headers=admin_headers)
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert appr_data["success"] is True
    assert appr_data["status"] == "approved"

    # Verify Story has episode updated to 'published' in SeriesRepository
    from repositories.series_repository import series_repository
    updated_series = series_repository.get_series_detail(test_series_id)
    assert updated_series is not None
    approved_ep = next((e for e in updated_series["episodes"] if e["id"] == created_ep["id"]), None)
    assert approved_ep is not None
    assert approved_ep["status"] == "published"
    print(f"[PASS] Lifecycle Completed: Approved episode promoted to 'published' in global series repository.")

    print("\n=======================================================")
    print("ALL CREATOR FOUNDATION & PIPELINE TESTS PASSED!")
