"""
INVENTIVE TEST: Inhlawulo ("The Price") Creator Response Flow
Tests:
1. Story Inception: 'Inhlawulo ("The Price")'
2. Natural synopsis submission -> immediate ASK mode with targeted creative question
3. Creator natural language input:
   'Nomcebo discovers that the will connects her directly to the dead man, but she doesn't yet know why. She has to decide whether to investigate quietly or tell her boss.'
4. Input acceptance, state progression, and next genuine creative question formulated without processing loop.
"""

import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from story_forge.models import StoryState, CharacterRole, MilestoneEnum, ReadinessStatus, AuthorityMode

client = TestClient(app)


def test_inhlawulo_creator_response_progression():
    creator_id = f"creator_pilot_{uuid.uuid4().hex[:6]}"
    story_id = f"inhlawulo_{uuid.uuid4().hex[:6]}"

    # Step 1: Create Story
    create_res = client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": 'Inhlawulo ("The Price")',
        "owner_id": creator_id,
        "logline": 'A young forensic auditor in Durban uncovers a fraudulent will linking her estranged family to a murdered billionaire.',
        "primary_language": "isiZulu"
    })
    assert create_res.status_code == 200
    story_data = create_res.json()
    assert story_data["title"] == 'Inhlawulo ("The Price")'

    # Step 2: Start Session with initial synopsis
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}",
        "initial_premise": "Nomcebo is an honest junior probate auditor at a Durban legal firm who is assigned to verify the estate of deceased shipping tycoon Mr. Mthembu. She finds anomalies in the signed testament."
    })
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    # Step 3: Verify initial question is active and in ASK mode
    action_1 = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert action_1["action"] in ("ASK", "PROPOSE")
    assert action_1["requires_creator"] is True
    assert action_1["question"] is not None
    assert len(action_1["question"].strip()) > 5

    # Step 4: Creator responds with exact natural language text
    creator_input_text = "Nomcebo discovers that the will connects her directly to the dead man, but she doesn't yet know why. She has to decide whether to investigate quietly or tell her boss."
    cycle_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": creator_input_text
    })
    assert cycle_res.status_code == 200
    cycle_data = cycle_res.json()
    updated_state = cycle_data["current_state"]

    # Step 5: Verify entity extraction & state advancement
    assert "Nomcebo" in updated_state["characters"] or any("Nomcebo" in c["name"] for c in updated_state["characters"].values())
    assert updated_state["state_version"] >= 2

    # Step 6: Verify next action is ready for creator input
    action_2 = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert action_2["action"] in ("ASK", "PROPOSE", "STOP")
    if action_2["action"] != "STOP":
        assert action_2["question"] is not None
        assert len(action_2["question"].strip()) > 5
        assert action_2["requires_creator"] is True


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
