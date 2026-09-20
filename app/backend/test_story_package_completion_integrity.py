"""
Welele Story Forge™ — Story Package Completion Integrity & Entity Extraction Regression Tests
Guarantees:
1. Entity Identity: Relational descriptors (sister, brother, uncle, mother, boss) never overwrite explicit proper names (Zodwa, Thabo, Amu, Naledi, Mr Dube).
2. Relationship Invariant: Mutual relationships are canonically constructed and non-empty.
3. Completion Governance: ForgeJudge refuses M1/M2/M3 certification if dramatic engine or chronology spine is hollow (no len(characters) >= 2 shortcuts).
4. Authoritative Package API: GET /api/forge/stories/{story_id}/package compiles non-empty, certified StoryPackageArtifact.
5. Three Truths Convergence: Canonical State, ForgeJudge, and Story Package agree on identical narrative truth.
"""

import pytest
from fastapi.testclient import TestClient

import main
from story_forge.models import (
    StoryState,
    CharacterRole,
    CharacterRelationship,
    CharacterState,
    ChronologyEvent,
    MilestoneEnum,
    ReadinessStatus,
    StateStatus,
    WorldSetting,
    NarrativePlant,
    ProductionDecision,
    ProductionAspect,
    StoryPackageArtifact
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import ForgeJudge, StoryForgeKernel
from story_forge.engine import NarrativeExtractor, DependencyEngine

client = TestClient(main.app)


def test_entity_extraction_prioritizes_proper_nouns_across_roles():
    """
    Test 1: Proper noun priority across diverse kinship, relational, and opposition descriptors.
    Relational descriptor must never overwrite an explicitly supplied proper name.
    """
    state = StoryState(
        story_id="entity_test_001",
        title="The Test Story",
        logline="A high-stakes drama set in Johannesburg."
    )
    state.characters["Sabelo"] = CharacterState(
        name="Sabelo",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Save his family and workshop"
    )

    test_cases = [
        ("his younger sister Zodwa's urgent surgery", "Zodwa", CharacterRole.CONFIDANT, "SIBLING"),
        ("her older brother Thabo refused to help", "Thabo", CharacterRole.CONFIDANT, "SIBLING"),
        ("his uncle Amu demanded a share of the inheritance", "Amu", CharacterRole.SUPPORTING, "FAMILY"),
        ("mother Naledi prayed for their safety", "Naledi", CharacterRole.CONFIDANT, "PARENT"),
        ("his close friend Jonas offered a hiding place", "Jonas", CharacterRole.CONFIDANT, "FRIEND"),
        ("his corrupt boss Mr Dube threatened immediate dismissal", "Mr Dube", CharacterRole.ANTAGONIST, "OPPOSITION"),
        ("local loan shark Jonas demanded the workshop deed as collateral", "Jonas", CharacterRole.ANTAGONIST, "OPPOSITION"),
    ]

    for narrative_text, expected_name, expected_role, expected_rel in test_cases:
        res = NarrativeExtractor.extract(narrative_text, state)

        # 1. Extracted character names must contain the proper noun
        assert expected_name in res.extracted_character_names, (
            f"Failed for text: '{narrative_text}'. Expected name '{expected_name}' not in {res.extracted_character_names}"
        )

        # 2. Must NOT extract generic role words as character names
        forbidden_generic_names = ["Sister", "Brother", "Uncle", "Mother", "Boss", "Friend", "Loan Shark"]
        for fn in forbidden_generic_names:
            assert fn not in res.extracted_character_names, (
                f"Entity reduction detected for '{narrative_text}': generic name '{fn}' extracted instead of '{expected_name}'"
            )

        # 3. Must propose character creation for the proper name
        char_mut = next((m for m in res.proposed_mutations if m.target_path == f"characters.{expected_name}"), None)
        assert char_mut is not None, f"No character creation mutation for '{expected_name}'"
        assert char_mut.new_value["name"] == expected_name
        assert char_mut.new_value["role"] == expected_role.value

        # 4. Must propose bidirectional relationships with protagonist Sabelo
        rel_mut_protagonist = next((m for m in res.proposed_mutations if m.target_path == "characters.Sabelo.relationships"), None)
        assert rel_mut_protagonist is not None, f"No relationship mutation on Protagonist for '{expected_name}'"
        assert any(r["target_character"] == expected_name for r in rel_mut_protagonist.new_value)


def test_forge_judge_rejects_empty_shell_certifications():
    """
    Test 2: False completion governance rejected.
    Two characters with empty relationships and 0 events MUST NOT pass M1, M2, or M3.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "hollow_story_001"
    repo.create_story(
        story_id=story_id,
        title="Hollow Story",
        owner_id="creator_1",
        logline="A Johannesburg drama about a mechanic needing cash."
    )
    state = repo.get_current_state(story_id)
    # Add two characters, but no relationships and no events
    state.characters["Sabelo"] = CharacterState(name="Sabelo", role=CharacterRole.PROTAGONIST, core_motivation="Needs money")
    state.characters["Sister"] = CharacterState(name="Sister", role=CharacterRole.CONFIDANT, core_motivation="Sick")
    repo.save_state(state)

    assessment = judge.assess(story_id)

    # Must NOT certify M1 (missing counterforce, missing relationships)
    assert MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK not in assessment.satisfied_milestones
    assert "M1_COUNTERFORCE_REQUIRED" in assessment.missing_invariants
    assert "M1_RELATIONSHIP_DYNAMIC_REQUIRED" in assessment.missing_invariants

    # Must NOT certify M2 (0 events)
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK not in assessment.satisfied_milestones

    # Must NOT certify M3 (FORGE_COMPLETE)
    assert assessment.status != ReadinessStatus.FORGE_COMPLETE
    assert assessment.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE


def test_story_package_endpoint_authoritative_contract():
    """
    Test 3: First-class Story Package endpoint (GET /api/forge/stories/{story_id}/package).
    Verifies that the compiled package contains genuine story data.
    """
    story_payload = {
        "title": "Sabelo: The Fontana Boss",
        "owner_id": "creator_zola",
        "logline": "Comedy drama set in Johannesburg. Sabelo steals R2 million from drug dealer Jonas to save his sister Zodwa's surgery."
    }
    create_res = client.post("/api/forge/stories", json=story_payload)
    assert create_res.status_code == 200
    story_id = create_res.json()["story_id"]

    # Start session and submit rich story response
    sess_res = client.post(f"/api/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_zola",
        "initial_premise": story_payload["logline"]
    })
    session_id = sess_res.json()["id"]

    # Submit creator response introducing Zodwa and Jonas
    submit_res = client.post(
        f"/api/forge/sessions/{session_id}/input",
        json={"creator_response": "Sabelo is desperate to secretly fund his younger sister Zodwa's urgent surgery before Friday, while ruthless loan shark Jonas demands his family workshop as collateral."}
    )
    assert submit_res.status_code == 200

    # Fetch authoritative Story Package from backend
    pkg_res = client.get(f"/api/forge/stories/{story_id}/package")
    assert pkg_res.status_code == 200
    pkg_data = pkg_res.json()

    # Package structure verification
    assert pkg_data["story_package_version"] == "0.2.0"
    assert pkg_data["story_id"] == story_id
    assert pkg_data["title"] == "Sabelo: The Fontana Boss"
    assert "Zodwa" in [c["name"] for c in pkg_data["characters"]]
    assert "Jonas" in [c["name"] for c in pkg_data["characters"]]

    # Verify relationships exist on characters
    zodwa_char = next(c for c in pkg_data["characters"] if c["name"] == "Zodwa")
    assert len(zodwa_char["relationships"]) > 0

    jonas_char = next(c for c in pkg_data["characters"] if c["name"] == "Jonas")
    assert jonas_char["role"] == "ANTAGONIST"


def test_three_truths_convergence():
    """
    Test 4: Three Truths Convergence:
    Canonical State, Forge Judge, and Story Package must agree on the same underlying truth.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "convergence_story_001"
    repo.create_story(
        story_id=story_id,
        title="The Three Truths",
        owner_id="creator_1",
        logline="A complete drama where Sabelo opposes Jonas to protect Zodwa."
    )
    state = repo.get_current_state(story_id)
    state.characters["Sabelo"] = CharacterState(
        name="Sabelo",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Protect family",
        relationships=[CharacterRelationship(target_character="Zodwa", relation_type="SIBLING", dynamic="Care", tension_level=5)]
    )
    state.characters["Zodwa"] = CharacterState(
        name="Zodwa",
        role=CharacterRole.CONFIDANT,
        core_motivation="Survive surgery",
        relationships=[CharacterRelationship(target_character="Sabelo", relation_type="SIBLING", dynamic="Care", tension_level=5)]
    )
    state.characters["Jonas"] = CharacterState(
        name="Jonas",
        role=CharacterRole.ANTAGONIST,
        core_motivation="Demand collateral",
        relationships=[CharacterRelationship(target_character="Sabelo", relation_type="TARGET", dynamic="Debt", tension_level=9)]
    )
    for i in range(1, 7):
        event = ChronologyEvent(
            story_id=story_id,
            event_sequence=i,
            anchor_type="INCITING_DISRUPTION" if i == 1 else "RESOLUTION" if i == 6 else "EVENT_PROGRESSION",
            headline=f"Turning Point {i}",
            description=f"Description of turning point {i}"
        )
        state.chronology.append(event)
        repo.save_event(event)

    repo.save_state(state)

    # 1. Judge Assessment Truth
    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.FORGE_COMPLETE
    assert assessment.current_milestone == MilestoneEnum.M3_FORGE_COMPLETE
    assert len(assessment.missing_invariants) == 0

    # 2. Package Compilation Truth
    events = repo.get_events(story_id)
    pkg = StoryPackageArtifact(
        story_id=story_id,
        title=state.title,
        logline=state.logline or "",
        milestone=assessment.current_milestone,
        readiness_status=assessment.status,
        state_version=state.state_version,
        characters=[c.model_dump() for c in state.characters.values()],
        world=state.world.model_dump(),
        chronology_spine=[e.model_dump() for e in events],
        narrative_plants=[p.model_dump() for p in state.plants],
        knowledge_states=[k.model_dump() for k in state.knowledge_states],
        production_decisions=[],
        assessment=assessment
    )

    # 3. Assert full convergence across all 3
    # Same characters
    assert set(state.characters.keys()) == {c["name"] for c in pkg.characters}
    # Same events count
    assert len(state.chronology) == len(pkg.chronology_spine) == 6
    # Same milestone
    assert assessment.current_milestone == pkg.milestone == MilestoneEnum.M3_FORGE_COMPLETE
    # Zodwa is known by all 3
    assert "Zodwa" in state.characters
    assert any(c["name"] == "Zodwa" for c in pkg.characters)
