"""
Story Forge API Contract Tests: Verification of Application-Facing Endpoints
Tests the complete FastAPI boundary without touching internal engine components.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from story_forge.models import AuthorityMode, ReadinessStatus

client = TestClient(app)


def test_story_lifecycle_and_session_api():
    # 1. Create Story
    create_payload = {
        "title": "API Test Drama",
        "owner_id": "creator-uuid-001",
        "logline": "A test series for API contract verification.",
        "primary_language": "isiZulu"
    }
    res = client.post("/api/v1/forge/stories", json=create_payload)
    assert res.status_code == 200
    story_data = res.json()
    story_id = story_data["story_id"]
    assert story_data["title"] == "API Test Drama"

    # 2. Get Story Summary
    res_summary = client.get(f"/api/v1/forge/stories/{story_id}")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["title"] == "API Test Drama"

    # Setup initial character state
    from story_forge.api.routes import get_repository
    from story_forge.models import CharacterState, CharacterRole
    repo = get_repository()
    initial_state = repo.get_current_state(story_id)
    initial_state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi", role=CharacterRole.UNRESOLVED)
    repo.save_state(initial_state)

    # 3. Start Session
    session_payload = {
        "creator_id": "creator-uuid-001",
        "initial_premise": "Nkosinathi arrives at a private loft in Maboneng."
    }
    res_sess = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json=session_payload)
    assert res_sess.status_code == 200
    sess = res_sess.json()
    session_id = sess["id"]
    assert sess["story_id"] == story_id
    assert sess["session_status"] == "ACTIVE"

    # 4. Get Current Action
    res_curr = client.get(f"/api/v1/forge/sessions/{session_id}/current")
    assert res_curr.status_code == 200
    curr = res_curr.json()
    assert curr["session_id"] == session_id
    assert "action" in curr

    # 5. Submit Creator Input with Event
    input_payload = {
        "creator_input": "Nkosinathi discovers that Thabo and Tebogo are engaged.",
        "event_headline": "Engagement Discovery",
        "event_description": "Nkosinathi discovers the engagement in Maboneng.",
        "participants": ["Nkosinathi", "Thabo", "Tebogo"]
    }
    res_input = client.post(f"/api/v1/forge/sessions/{session_id}/input", json=input_payload)
    assert res_input.status_code == 200
    cycle = res_input.json()
    assert cycle["state_version"] >= 1
    assert cycle["transition"]["sequence"] >= 1

    # 5b. Submit Creator Answer to question
    ans_payload = {
        "creator_response": "Nkosinathi vows to expose Thabo's fraudulent empire before the wedding ceremony."
    }
    res_ans = client.post(f"/api/v1/forge/sessions/{session_id}/input", json=ans_payload)
    assert res_ans.status_code == 200
    cycle_ans = res_ans.json()
    assert cycle_ans["state_version"] >= 2

    # 6. Retrieve State, Dependencies, and Trace
    res_state = client.get(f"/api/v1/forge/stories/{story_id}/state")
    assert res_state.status_code == 200
    assert res_state.json()["state_version"] >= 2

    res_deps = client.get(f"/api/v1/forge/stories/{story_id}/dependencies")
    assert res_deps.status_code == 200
    assert len(res_deps.json()) >= 1

    res_trace = client.get(f"/api/v1/forge/stories/{story_id}/trace")
    assert res_trace.status_code == 200
    assert len(res_trace.json()) >= 2

    # 7. Completion Assessment
    res_comp = client.get(f"/api/v1/forge/stories/{story_id}/completion")
    assert res_comp.status_code == 200
    comp = res_comp.json()
    assert comp["status"] in ("NOT_READY", "PREMISE_LOCK", "DRAMATIC_ENGINE_LOCK", "EPISODIC_ARC_LOCK", "FORGE_COMPLETE")
