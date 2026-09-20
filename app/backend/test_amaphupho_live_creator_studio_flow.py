"""
End-to-End Creator Story Studio Integration Test: Amaphupho ("Dreams")
Simulates a real human creator interacting with Creator Story Studio through FastAPI API endpoints.

Validates:
1. Natural story conversation in, natural story conversation out.
2. Zero machine ontology exposed to creator (no 'counterforce', 'dependency', 'invariant', etc.).
3. Holistic absorption of rich multi-fact answers.
4. Smooth handling of contradictions, revisions, and tangential/collateral answers.
5. Preserves creator dramatic authority (no premature ANTAGONIST canonization).
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from story_forge.models import CharacterRole, StateStatus, KnowledgeStatus

client = TestClient(app)


def test_amaphupho_real_creator_studio_flow():
    creator_id = f"creator_thabo_{uuid.uuid4().hex[:6]}"
    story_id = f"amaphupho_{uuid.uuid4().hex[:6]}"

    # Step 1: Create Story Inception
    create_res = client.post("/api/forge/stories", json={
        "story_id": story_id,
        "title": "Amaphupho (\"Dreams\")",
        "owner_id": creator_id,
        "logline": "A talented township producer secretly crafts a viral Amapiano track as Ghost404, only for his conflicted partner to submit a remix to save his dying mother.",
        "primary_language": "isiZulu"
    })
    assert create_res.status_code == 200
    story_data = create_res.json()
    assert story_data["title"] == "Amaphupho (\"Dreams\")"

    # Step 2: Start Session with Initial Creator Premise
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": creator_id,
        "session_id": f"sess_{story_id}",
        "initial_premise": "Sizwe is a gifted music producer in Soweto living in fear of his strict father who forbids music. Under the alias Ghost404, he secretly creates a revolutionary Amapiano track."
    })
    assert sess_res.status_code == 200
    session_data = sess_res.json()
    session_id = session_data["id"]

    # Step 3: Fetch Current Action for Creator Story Studio
    action_1 = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert action_1["action"] == "ASK"
    assert action_1["question"] is not None
    assert len(action_1["question"].strip()) > 5
    assert action_1["requires_creator"] is True

    # Step 4: Turn 1 - Creator Submits Rich Multi-Fact Answer
    turn1_input = (
        "Mandla has known Sizwe is Ghost404 since they mixed the original track together. "
        "He's under pressure because of his mother's medical bills, so when the track went viral he saw an opportunity. "
        "He submitted his remix because he thinks Sizwe is too scared of his father to claim the deal."
    )
    cycle1_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": turn1_input
    })
    assert cycle1_res.status_code == 200
    cycle1_data = cycle1_res.json()
    state_1 = cycle1_data["current_state"]

    # Assert multiple facts were absorbed holistically
    assert "Mandla" in state_1["characters"]
    assert "Sizwe" in state_1["characters"]
    assert len(state_1["knowledge_states"]) > 0
    assert any("Ghost404" in k["fact_key"] for k in state_1["knowledge_states"])

    # Step 5: Check Next Question in Studio
    action_2 = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert action_2["action"] == "ASK"
    assert action_2["question"] is not None
    assert "father" in action_2["question"].lower() or "sizwe" in action_2["question"].lower()

    # Step 6: Turn 2 - Creator Submits Contradiction / Revision
    turn2_input = "Actually, Mandla and Sizwe haven't spoken in five years."
    cycle2_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": turn2_input
    })
    assert cycle2_res.status_code == 200
    cycle2_data = cycle2_res.json()
    state_2 = cycle2_data["current_state"]

    # Verify relationship revision recorded
    mandla_char = state_2["characters"]["Mandla"]
    assert any("ESTRANGED" in r["relation_type"] or "5-year" in (r.get("dynamic") or "") for r in mandla_char["relationships"])

    # Step 7: Turn 3 - Creator Submits Tangential / Multi-Aspect Answer (The Killer Test)
    turn3_input = (
        "His father will probably throw him out of the house. "
        "And Mandla already knows he's Ghost404 because they made the track together. "
        "Actually, Mandla has submitted his own version to the label."
    )
    cycle3_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": turn3_input
    })
    assert cycle3_res.status_code == 200
    cycle3_data = cycle3_res.json()
    assert cycle3_data["active_question"] is not None
    assert "please answer" not in cycle3_data["active_question"].lower()

    # Step 8: Turn 4 - Adversarial Dramatic Role Test (Preserve Creator Authority)
    turn4_input = (
        "Mandla submitted his remix because his mother is in the ICU and needs R80,000 for surgery. "
        "He hates doing this to Sizwe, but he believes Sizwe will never go public anyway because of his father."
    )
    cycle4_res = client.post(f"/api/forge/sessions/{session_id}/input", json={
        "creator_response": turn4_input
    })
    assert cycle4_res.status_code == 200
    cycle4_data = cycle4_res.json()
    state_4 = cycle4_data["current_state"]

    # Verify Mandla was NOT prematurely canonized as ANTAGONIST
    mandla_final = state_4["characters"]["Mandla"]
    assert mandla_final["role"] != "ANTAGONIST"
    assert "R80,000" in mandla_final["core_motivation"] or "surgery" in mandla_final["core_motivation"].lower()

    # Verify next creative question gives creator authority over dramatic framing
    action_final = client.get(f"/api/forge/sessions/{session_id}/current").json()
    assert "traitor" in action_final["question"].lower() or "brother" in action_final["question"].lower() or "desperate" in action_final["question"].lower()

    # Step 9: Verify Zero Machine Ontology Leaked Across All Questions
    for forbidden in ["counterforce", "dependency", "invariant", "mutation", "canon", "deficiency", "schema"]:
        assert forbidden not in action_final["question"].lower()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
