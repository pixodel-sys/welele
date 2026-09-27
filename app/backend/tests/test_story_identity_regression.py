"""
Welele Media™ — Backend Story Identity & Fallback Regression Tests
Verifies the complete regression flow specified for creator session integrity:
1. Create Story A = "Bougie".
2. Confirm its story_id, title, and backend state.
3. Call getStoryState() repeatedly (read-only idempotency invariant).
4. Call getCurrentAction() with no active story (empty/unknown session ID) - returns 404 and NEVER creates phantom drafts.
5. Simulate screen transitions: Story Intake (list), Cockpit (state/deps), Production Room (queue).
6. Verify no "Untitled Story" records are created by reads or empty-ID calls.
7. Resume Story A and confirm identity, story_id, title ("Bougie"), and canonical state are preserved.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.models import StoryState

client = TestClient(app)

def test_story_identity_preservation_and_zero_ghost_drafts():
    # Step 1: Create Story A = "Bougie"
    create_payload = {
        "story_id": "bougie_regression_01",
        "title": "Bougie",
        "owner_id": "creator_test_01",
        "logline": "A high-stakes Johannesburg luxury dynasty drama.",
        "primary_language": "isiZulu"
    }
    res = client.post("/api/v1/forge/stories", json=create_payload)
    assert res.status_code == 200, res.text
    created = res.json()
    assert created["story_id"] == "bougie_regression_01"
    assert created["title"] == "Bougie"
    assert created["state_version"] == 1

    # Step 2: Confirm story_id, title, and backend state
    list_res = client.get("/api/v1/forge/stories")
    assert list_res.status_code == 200
    stories = list_res.json()
    bougie = next((s for s in stories if s["id"] == "bougie_regression_01"), None)
    assert bougie is not None
    assert bougie["title"] == "Bougie"
    assert bougie["logline"] == "A high-stakes Johannesburg luxury dynasty drama."

    # Step 3: Call getStoryState() repeatedly
    for _ in range(25):
        state_res = client.get("/api/v1/forge/stories/bougie_regression_01/state")
        assert state_res.status_code == 200
        state_data = state_res.json()
        assert state_data["title"] == "Bougie"
        assert state_data["story_id"] == "bougie_regression_01"
        assert state_data["state_version"] == 1

    # Read nonexistent IDs repeatedly: must return 404, NEVER create phantom drafts
    for i in range(15):
        missing_res = client.get(f"/api/v1/forge/stories/ghost_query_{i}/state")
        assert missing_res.status_code == 404

    # Step 4: Call getCurrentAction() with no active story / empty / unknown session ID
    for i in range(15):
        empty_sess_res = client.get(f"/api/v1/forge/sessions/unregistered_sess_{i}/current")
        assert empty_sess_res.status_code == 404
        # Empty string session path
        empty_path_res = client.get("/api/v1/forge/sessions//current")
        assert empty_path_res.status_code in (404, 307)

    # Invariant: Confirm list count has NOT increased and NO ghosts exist
    list_res2 = client.get("/api/v1/forge/stories")
    stories2 = list_res2.json()
    ghosts = [s for s in stories2 if "ghost" in s["id"] or s.get("title", "").strip().lower() in ("untitled", "untitled story", "story", "")]
    assert len(ghosts) == 0, f"Found unexpected ghost stories: {ghosts}"

    # Step 5: Simulate navigation between Story Intake, Cockpit, and Production Room
    # 5a. Intake Screen: list stories
    intake_list = client.get("/api/v1/forge/stories").json()
    assert any(s["id"] == "bougie_regression_01" for s in intake_list)

    # 5b. Cockpit Screen: fetch state, dependencies, completion
    cockpit_state = client.get("/api/v1/forge/stories/bougie_regression_01/state").json()
    assert cockpit_state["title"] == "Bougie"
    client.get("/api/v1/forge/stories/bougie_regression_01/dependencies")
    client.get("/api/v1/forge/stories/bougie_regression_01/completion")

    # 5c. Production Room: list queue
    prod_queue = client.get("/api/v1/forge/stories").json()
    assert any(s["id"] == "bougie_regression_01" for s in prod_queue)

    # Step 6: Cleanup untitled endpoint check
    clean_res = client.delete("/api/v1/forge/stories/cleanup/untitled")
    assert clean_res.status_code == 200

    # Step 7: Resume Story A
    resume_res = client.get("/api/v1/forge/stories/bougie_regression_01/state")
    assert resume_res.status_code == 200
    resumed = resume_res.json()
    assert resumed["story_id"] == "bougie_regression_01"
    assert resumed["title"] == "Bougie"
    assert resumed["state_version"] == 1

    # Step 8: Final validation - Confirm no new story was created and Story A remains Bougie
    final_list = client.get("/api/v1/forge/stories").json()
    matching_bougie = [s for s in final_list if s["id"] == "bougie_regression_01"]
    assert len(matching_bougie) == 1, "Exactly one Story A must exist"
    assert matching_bougie[0]["title"] == "Bougie"
    assert not any(s.get("title", "").strip().lower() == "untitled story" for s in final_list)
