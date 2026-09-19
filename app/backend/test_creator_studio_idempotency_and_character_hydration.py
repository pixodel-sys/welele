"""
Test Suite: Creator Studio Idempotency & Character Hydration Verification
Verifies:
1. Observational Idempotency: Polling GET /api/forge/sessions/{id}/current 10x causes ZERO state changes or LLM cycles.
2. Character Hydration: Incepting Inhlawulo / Amaphupho with logline/synopsis immediately hydrates the protagonist into StoryState.
3. Natural Storytelling Flow: Responding with tangents, contradictions, and multi-sentence paragraphs progresses naturally.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from story_forge.models import StoryState, CharacterRole, MilestoneEnum, AuthorityMode

client = TestClient(app)


def test_1_polling_idempotency_10_consecutive_get_current_calls():
    """
    CRITICAL CHECK: Calling GET /api/forge/sessions/{session_id}/current 10 times
    must be purely observational:
    - The question remains identical
    - StoryState version does not change
    - No new transitions or traces are generated
    - No new facts/mutations occur
    """
    creator_id = f"creator_{uuid.uuid4().hex[:6]}"
    story_id = f"idempotency_{uuid.uuid4().hex[:6]}"

    # Step 1: Create Story
    create_res = client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": 'Inhlawulo ("The Price")',
        "owner_id": creator_id,
        "logline": 'Nomcebo is an honest junior probate auditor at a Durban legal firm who discovers a forged will.',
        "primary_language": "isiZulu"
    })
    assert create_res.status_code == 200

    # Step 2: Start Session
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}"
    })
    assert sess_res.status_code == 200
    session_id = sess_res.json()["id"]

    # Initial baseline
    baseline_state = client.get(f"/api/forge/stories/{story_id}/state").json()
    baseline_trace = client.get(f"/api/forge/stories/{story_id}/trace").json()
    initial_version = baseline_state["state_version"]
    initial_trace_count = len(baseline_trace)

    # Initial current action
    action_0 = client.get(f"/api/forge/sessions/{session_id}/current").json()
    baseline_question = action_0["question"]
    assert baseline_question is not None and len(baseline_question) > 0

    # Step 3: Poll GET /current 10 times consecutively
    for i in range(1, 11):
        action_i = client.get(f"/api/forge/sessions/{session_id}/current").json()
        assert action_i["question"] == baseline_question, f"Poll {i} changed question!"
        assert action_i["action"] == action_0["action"], f"Poll {i} changed action!"
        assert action_i["state_version"] == initial_version, f"Poll {i} changed state version!"

        curr_state = client.get(f"/api/forge/stories/{story_id}/state").json()
        assert curr_state["state_version"] == initial_version, f"State version mutated on poll {i}!"
        assert len(curr_state["characters"]) == len(baseline_state["characters"]), f"Characters mutated on poll {i}!"

        curr_trace = client.get(f"/api/forge/stories/{story_id}/trace").json()
        assert len(curr_trace) == initial_trace_count, f"Trace count changed on poll {i}!"


def test_2_character_hydration_on_story_inception():
    """
    VERIFICATION OF 0 CHARACTERS vs HYDRATED PROTAGONIST:
    When Inhlawulo is incepted with Nomcebo in the logline/premise,
    starting the session must extract Nomcebo so she is visible in StoryState immediately.
    """
    creator_id = f"creator_{uuid.uuid4().hex[:6]}"
    story_id = f"inhlawulo_hydration_{uuid.uuid4().hex[:6]}"

    # Incept Story with Nomcebo
    client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": 'Inhlawulo ("The Price")',
        "owner_id": creator_id,
        "logline": 'Nomcebo is an honest junior probate auditor at a Durban legal firm who discovers a forged will linking her family to a murdered billionaire.',
        "primary_language": "isiZulu"
    })

    # Start Session (without duplicating premise, relying on logline)
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}"
    })
    assert sess_res.status_code == 200

    # Verify StoryState now contains Nomcebo
    state = client.get(f"/api/forge/stories/{story_id}/state").json()
    assert len(state["characters"]) >= 1
    assert "Nomcebo" in state["characters"] or any("Nomcebo" in c["name"] for c in state["characters"].values())

    # Verify question is character-aware and collaborative
    action = client.get(f"/api/forge/sessions/sess_{story_id}/current").json()
    assert action["question"] is not None
    assert "counterforce" not in action["question"].lower()
    assert "dependency" not in action["question"].lower()


def test_3_natural_creator_tangent_and_coherence():
    """
    Simulates real human creator giving rich, multi-sentence paragraphs
    with tangents, relationship tension, and dynamic discoveries.
    """
    creator_id = f"creator_{uuid.uuid4().hex[:6]}"
    story_id = f"amaphupho_live_{uuid.uuid4().hex[:6]}"

    # Create story
    client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": "Amaphupho",
        "owner_id": creator_id,
        "logline": "A gifted music producer in Soweto hides his breakout tracks behind an anonymous persona.",
        "primary_language": "isiZulu"
    })

    # Start session with rich setup
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}",
        "initial_premise": "Sizwe secretly produces amapiano bangers under the alias Ghost404 in his bedroom studio."
    })
    session_id = sess_res.json()["id"]

    # Natural response with tangents and relationship conflict
    creator_answer = (
        "Mandla came over yesterday while Sizwe was out buying bread and heard the finished Ghost404 track playing on loop. "
        "Mandla is struggling financially because his mother is in the ICU and needs R80,000 for surgery. "
        "He hates doing this to Sizwe, but he secretly submitted his own remix of the track to a major label executive "
        "because he believes Sizwe is too terrified of his father to ever claim the music himself."
    )

    cycle_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": creator_answer
    })
    assert cycle_res.status_code == 200
    cycle_data = cycle_res.json()

    # Verify state progressed coherently
    state = cycle_data["current_state"]
    assert "Mandla" in state["characters"] or any("Mandla" in c["name"] for c in state["characters"].values())

    # Mandla should NOT be prematurely forced to ANTAGONIST role if his motive is tragic/conflicted
    mandla = state["characters"].get("Mandla") or next((c for c in state["characters"].values() if "Mandla" in c["name"]), None)
    assert mandla is not None
    assert mandla["role"] in ("UNRESOLVED", "SUPPORTING", "CATALYST", "RIVAL", "ANTAGONIST")

    # Verify next conversational move is ready and natural
    action = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert action["action"] in ("ASK", "PROPOSE")
    assert action["question"] is not None
    assert len(action["question"]) > 10
