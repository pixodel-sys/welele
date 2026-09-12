"""
Welele Media™ — Story Forge Canonical Lineage & Persistence Regression Test (P0)
Verifies: Story Forge -> Persist -> package_id -> Accept -> Episode Pipeline -> Immutable Lineage
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def get_creator_headers():
    token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    return {"Authorization": f"Bearer {token}"}

def test_story_forge_canonical_persistence_and_lineage():
    creator_headers = get_creator_headers()

    # 1. Save Story Forge Package to canonical IP
    ip_id = "ip_blood_ties"
    package_payload = {
        "ip_id": ip_id,
        "creator_id": "creator_zola",
        "package_title": "Blood Ties: The Midnight Testimony",
        "target_duration_seconds": 90,
        "beats": [
            {"beat_number": 1, "description": "Sipho discovers the unsealed codicil."},
            {"beat_number": 2, "description": "Lerato threatens the family lawyer."},
            {"beat_number": 3, "description": "Gunshots ring out at the Sandton rank."}
        ],
        "dialogues": [
            {"character": "Sipho", "line": "You cannot hide the truth from the ancestors."}
        ],
        "cliffhanger_prompt": "Who authorized the midnight raid on the workshop?",
        "ai_model_used": "gemini-1.5-flash",
        "human_approved": True
    }

    res_save = client.post(
        f"/api/ip/{ip_id}/story-forge/save",
        json=package_payload,
        headers=creator_headers
    )
    assert res_save.status_code == 200, f"Failed saving story forge package: {res_save.text}"
    data = res_save.json()
    assert data["success"] is True
    pkg = data["package"]
    assert pkg["id"].startswith("sfp_")
    assert "lineage_hash" in pkg and len(pkg["lineage_hash"]) == 64
    canonical_pkg_id = pkg["id"]

    # 2. Verify IP detail contains the package
    res_ip = client.get(f"/api/ip/{ip_id}")
    assert res_ip.status_code == 200
    ip_data = res_ip.json()
    found_pkg = next((p for p in ip_data.get("story_packages", []) if p["id"] == canonical_pkg_id), None)
    assert found_pkg is not None
    assert found_pkg["lineage_hash"] == pkg["lineage_hash"]

    # 3. Ingest Episode with story_package_id lineage
    ep_payload = {
        "series_id": "story_blood_ties",
        "episode_number": 99,
        "title": "The Midnight Testimony",
        "synopsis": "The unsealed codicil reveals the truth.",
        "duration_seconds": 90,
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_time": 75,
        "cliffhanger_hook": "Who authorized the midnight raid on the workshop?",
        "story_package_id": canonical_pkg_id,
        "status": "draft",
        "storage_key": "masters/story_blood_ties/ep_bt_99.mp4",
        "video_url": "/videos/welele_placeholder.mp4"
    }

    res_ep = client.post(
        "/api/creators/episodes/add",
        json=ep_payload,
        headers=creator_headers
    )
    assert res_ep.status_code == 200, f"Failed creating episode: {res_ep.text}"
    ep_created = res_ep.json()["episode"]
    assert ep_created["story_package_id"] == canonical_pkg_id

    # 4. Verify lineage persists in Creator workspace
    res_workspace = client.get("/api/creators/series/story_blood_ties/workspace", headers=creator_headers)
    assert res_workspace.status_code == 200
    workspace_eps = res_workspace.json()["series"]["episodes"]
    ep_in_ws = next((e for e in workspace_eps if e["id"] == ep_created["id"]), None)
    assert ep_in_ws is not None
    assert ep_in_ws.get("story_package_id") == canonical_pkg_id

    # 5. Simulate reload / persistence verification
    all_episodes = series_repository.local_get("episodes")
    persisted_ep = next((e for e in all_episodes if e["id"] == ep_created["id"]), None)
    assert persisted_ep is not None
    assert persisted_ep.get("story_package_id") == canonical_pkg_id
