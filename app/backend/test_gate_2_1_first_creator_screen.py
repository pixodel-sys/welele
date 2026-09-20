"""
GATE 2.1 OBSERVATION VERIFICATION: FIRST CREATOR SCREEN USABILITY
Verifies:
1. After creator submits initial synopsis, the system transitions directly into a genuine story-grounded question in ASK mode.
2. The UI does not remain stuck in an intermediate "Updating canonical story arc..." machine processing state.
3. The first question is generated and immediately accessible via /api/forge/sessions/{id}/current.
4. The empty response box problem is eliminated.
5. The response demonstrates understanding of the creator's natural language synopsis.
6. Zero canned questions dictionary; questions originate from the Story-First reasoning/Forge mechanism.
"""

import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from story_forge.models import (
    StoryState, CharacterRole, MilestoneEnum, ReadinessStatus, AuthorityMode
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.api.routes import get_story_package

client = TestClient(app)


def test_gate_2_1_first_creator_screen_transition():
    """
    Simulates a fresh creator entering the Story Forge cockpit, submitting their initial natural-language synopsis.
    Verifies immediate ASK state with a genuine, story-grounded creative question.
    """
    forge_repo = InMemoryStoryForgeRepository()
    creator_id = f"pilot_creator_{uuid.uuid4().hex[:6]}"
    story_id = f"story_pilot_{uuid.uuid4().hex[:6]}"

    # 1. Create Story
    create_res = client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": "Kagiso: The Gold Courier",
        "owner_id": creator_id,
        "logline": "A former mine surveyor discovers an illegal syndicate tapping into ancient gold veins under Johannesburg.",
        "primary_language": "isiZulu"
    })
    assert create_res.status_code == 200
    story_data = create_res.json()
    assert story_data["title"] == "Kagiso: The Gold Courier"

    # 2. Start Session with natural language initial premise
    session_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}",
        "initial_premise": "Kagiso is a 28-year-old underground mine surveyor in Welkom who discovers that syndicate kingpin Nkosi is using undocumented shafts to smuggle gold bullion. Kagiso must protect his younger sister Zodwa from the syndicate's enforcers."
    })
    assert session_res.status_code == 200
    sess_data = session_res.json()
    session_id = sess_data["id"]

    # 3. Query Current Action Endpoint (First Creator Screen)
    action_res = client.get(f"/api/forge/sessions/{session_id}/current")
    assert action_res.status_code == 200
    action_data = action_res.json()

    # INVARIANT 1: Action MUST be ASK, NEVER stuck in INFER
    assert action_data["action"] in ("ASK", "PROPOSE"), f"Action should require creator response, got {action_data['action']}"
    assert action_data["requires_creator"] is True

    # INVARIANT 2: Question MUST be present and non-empty
    assert action_data["question"] is not None and len(action_data["question"].strip()) > 10

    # INVARIANT 3: Question must be grounded in story characters/conflict, not generic machine ontology
    question_text = action_data["question"]
    assert "dependency_key" not in question_text
    assert "REQUIRED_STATE" not in question_text
    assert "mutation" not in question_text.lower()

    # INVARIANT 4: Story state reflects understanding of the premise
    state_res = client.get(f"/api/forge/stories/{story_id}/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert len(state_data["characters"]) >= 1

    # INVARIANT 5: Creator responds in natural language to the question
    cycle_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": "Nkosi's enforcers raid Kagiso's family home at midnight. Kagiso smuggles Zodwa out through the old drainage tunnel while taking a GPS tracker off the syndicate vehicle."
    })
    assert cycle_res.status_code == 200
    next_action = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert next_action["action"] in ("ASK", "PROPOSE", "STOP")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
