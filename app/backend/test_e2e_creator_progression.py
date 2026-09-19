"""
End-to-End Regression Test: Creator UI Progression via FastAPI TestClient
Tests exact live sequence:
Creator enters story information -> Submit -> Backend reconciles -> Kernel advances ->
Next question generated -> Session transitions to ASK with next_question -> requires_creator is True -> UI displays next question.
"""
import pytest
from fastapi.testclient import TestClient
import main
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.api.routes import get_repository

client = TestClient(main.app)


def test_e2e_creator_submission_advances_to_next_story_question():
    # 1. Create a clean story
    story_payload = {
        "title": "Sabelo: The Fontana Boss",
        "owner_id": "creator_zola",
        "logline": "Comedy drama set in Johannesburg. Sabelo is a security guard who steals R2 million from drug dealer Jonas's car boot."
    }
    create_res = client.post("/api/forge/stories", json=story_payload)
    assert create_res.status_code == 200
    story_data = create_res.json()
    story_id = story_data["story_id"]

    # 2. Start a session with initial premise
    sess_payload = {
        "creator_id": "creator_zola",
        "initial_premise": "Sabelo is a security guard who steals R2 million from drug dealer Jonas's car boot."
    }
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json=sess_payload)
    assert sess_res.status_code == 200
    session_data = sess_res.json()
    session_id = session_data["id"]

    # 3. Check initial active action / question
    curr_res = client.get(f"/api/forge/sessions/{session_id}/current")
    assert curr_res.status_code == 200
    curr_data = curr_res.json()
    assert curr_data["action"] == "ASK"
    assert curr_data["question"] is not None
    assert curr_data["requires_creator"] is True
    initial_q = curr_data["question"]

    # 4. Creator submits Sabelo's motivation
    creator_response_text = (
        "Sabelo is desperate to escape his dead-end night shift job and secretly pay for his younger sister's medical operation, "
        "even if he risks Jonas hunting him down."
    )
    submit_res = client.post(
        f"/api/forge/sessions/{session_id}/input",
        json={"creator_response": creator_response_text}
    )
    assert submit_res.status_code == 200
    submit_data = submit_res.json()

    # Verify submit response returns the new active question
    assert submit_data["active_question"] is not None
    assert submit_data["active_question"] != initial_q

    # 5. Frontend polls /api/forge/sessions/{session_id}/current
    after_curr_res = client.get(f"/api/forge/sessions/{session_id}/current")
    assert after_curr_res.status_code == 200
    after_data = after_curr_res.json()

    # CRITICAL ACCEPTANCE CRITERIA:
    # Next question is rendered, action is ASK, requires_creator is True, UI does NOT get stuck in loop
    assert after_data["action"] == "ASK"
    assert after_data["requires_creator"] is True
    assert after_data["question"] is not None
    assert after_data["question"] == submit_data["active_question"]
    assert len(after_data["question"]) > 10

    # Zero forbidden ontology leakage in the returned question
    forbidden_terms = ["counterforce", "dependency", "required state", "canon", "invariant", "mutation", "deficiency"]
    q_lower = after_data["question"].lower()
    for f in forbidden_terms:
        assert f not in q_lower, f"Question '{after_data['question']}' leaked forbidden term '{f}'"
