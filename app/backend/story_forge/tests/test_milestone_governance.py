"""
Welele Story Forge™ — Milestone Governance & Required State Schema Regression Test Suite
Validates Completion Contract v0.2 and REQUIRED_STATE_SCHEMA_v0.1:
- Hierarchical milestones (M0: PREMISE_LOCK, M1: DRAMATIC_ENGINE_LOCK, M2: EPISODIC_ARC_LOCK, M3: FORGE_COMPLETE)
- Flexible Counterforce Model (Character, Supernatural Entity, Institution, System)
- Six Canonical Chronology Anchors
- Idempotent Required-State Deficiency Synthesis
"""

import pytest
from typing import Dict, Any, List
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    CharacterRelationship,
    NarrativePlant,
    ChronologyEvent,
    ProductionDecision,
    ProductionAspect,
    WorldSetting,
    StateStatus,
    Dependency,
    DependencyType,
    DependencyStatus,
    PriorityComponents,
    AuthorityMode,
    SkillEnum,
    MilestoneEnum,
    ReadinessStatus
)
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.engine import DependencyEngine
from story_forge.adapters import MockReasoningAdapter, MockLLMProvider, LLMReasoningAdapter


def test_m0_premise_lock_certification():
    """
    Test 1: Valid logline and title certifies M0: PREMISE_LOCK,
    but is rejected from M1, M2, and M3.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "test-m0"
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_1",
        logline="A young woman returns to her rural hometown after her father's unexplained death and discovers a locked ancestral debt."
    )

    assessment = judge.assess(story_id)

    assert assessment.status == ReadinessStatus.PREMISE_LOCK
    assert assessment.current_milestone == MilestoneEnum.M0_PREMISE_LOCK
    assert MilestoneEnum.M0_PREMISE_LOCK in assessment.satisfied_milestones
    assert MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK not in assessment.satisfied_milestones
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK not in assessment.satisfied_milestones
    assert MilestoneEnum.M3_FORGE_COMPLETE not in assessment.satisfied_milestones
    assert "M1_PROTAGONIST_MOTIVATION_REQUIRED" in assessment.missing_invariants


def test_m1_dramatic_engine_flexible_counterforce():
    """
    Test 2: Flexible Counterforce validation.
    M1 must pass with character counterforce OR institutional/supernatural entity counterforce.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    # Scenario A: Character Counterforce (Antagonist role)
    story_id = "test-m1-char"
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_1",
        logline="A young woman returns home after her father dies to confront a rival clan holding an ancestral debt."
    )
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(
        name="Zodwa",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Expose the ancestral debt and protect family.",
        relationships=[CharacterRelationship(target_character="Bheki", relation_type="OPPOSES")]
    )
    state.characters["Bheki"] = CharacterState(
        name="Bheki",
        role=CharacterRole.ANTAGONIST,
        core_motivation="Claim the Khumalo ancestral wealth by any means."
    )
    repo.save_state(state)

    assessment_a = judge.assess(story_id)
    assert assessment_a.current_milestone == MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK
    assert MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK in assessment_a.satisfied_milestones

    # Scenario B: Supernatural Entity / Arena Counterforce
    story_id_b = "test-m1-supernatural"
    repo.create_story(
        story_id=story_id_b,
        title="River Whispers",
        owner_id="creator_1",
        logline="A young woman investigates the supernatural river entity that demanded her father's ancestral blood sacrifice."
    )
    state_b = repo.get_current_state(story_id_b)
    state_b.characters["Zodwa"] = CharacterState(
        name="Zodwa",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Break the supernatural curse before the solstice.",
        relationships=[CharacterRelationship(target_character="River_Spirit", relation_type="RESISTS_CURSE")]
    )
    state_b.world = WorldSetting(
        primary_location="Bergville River",
        rules_and_lore=["Ancient aquatic spirit demanding generational debt repayment."]
    )
    repo.save_state(state_b)

    assessment_b = judge.assess(story_id_b)
    assert assessment_b.current_milestone == MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK
    assert MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK in assessment_b.satisfied_milestones


def test_m2_six_canonical_chronology_anchors():
    """
    Test 3: Six Canonical Chronology Anchors for M2 (EPISODIC_ARC_LOCK).
    State with < 6 events fails M2; state with all 6 anchors passes M2.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "test-m2-anchors"
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_1",
        logline="A vertical micro-drama series set in rural Bergville locations about a woman confronting an ancestral debt."
    )
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation="Expose truth")
    state.characters["Bheki"] = CharacterState(name="Bheki", role=CharacterRole.ANTAGONIST, core_motivation="Collect debt")
    repo.save_state(state)

    # Add only 3 events (incomplete spine)
    for i in range(1, 4):
        repo.save_event(ChronologyEvent(story_id=story_id, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}"))

    assessment_incomplete = judge.assess(story_id)
    assert assessment_incomplete.current_milestone == MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK not in assessment_incomplete.satisfied_milestones

    # Complete the full 6 canonical chronology anchors
    for i in range(4, 7):
        repo.save_event(ChronologyEvent(story_id=story_id, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}"))

    assessment_complete = judge.assess(story_id)
    assert assessment_complete.current_milestone == MilestoneEnum.M2_EPISODIC_ARC_LOCK
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK in assessment_complete.satisfied_milestones


def test_m2_narrative_plant_payoff_linking():
    """
    Test 4: Unresolved narrative plant blocks M2 until intended payoff is declared.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "test-m2-plants"
    repo.create_story(story_id=story_id, title="Ancestral Debt", owner_id="creator_1", logline="A thriller about an ancestral debt.")
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation="Expose truth")
    state.characters["Bheki"] = CharacterState(name="Bheki", role=CharacterRole.ANTAGONIST, core_motivation="Collect debt")
    state.plants.append(NarrativePlant(plant_name="ancestral_ledger", description="Secret book", payoff_status="PLANTED", intended_payoff=None))
    repo.save_state(state)

    # 6 events present
    for i in range(1, 7):
        repo.save_event(ChronologyEvent(story_id=story_id, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}"))

    assessment_blocked = judge.assess(story_id)
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK not in assessment_blocked.satisfied_milestones
    assert "M2_PLANT_PAYOFF_LINK_REQUIRED" in assessment_blocked.missing_invariants

    # Resolve intended payoff
    state = repo.get_current_state(story_id)
    state.plants[0].intended_payoff = "Used in Episode 6 climax to expose Bheki's fraud."
    repo.save_state(state)

    assessment_passed = judge.assess(story_id)
    assert MilestoneEnum.M2_EPISODIC_ARC_LOCK in assessment_passed.satisfied_milestones


def test_m3_forge_complete_multi_gate():
    """
    Test 5: Full package satisfying M0, M1, M2, and M3 certifies FORGE_COMPLETE.
    """
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)

    story_id = "test-m3-complete"
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_1",
        logline="A supernatural vertical micro-drama thriller set in rural Bergville and urban Johannesburg locations."
    )
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation="Expose truth")
    state.characters["Bheki"] = CharacterState(name="Bheki", role=CharacterRole.ANTAGONIST, core_motivation="Collect debt")
    state.plants.append(NarrativePlant(plant_name="ancestral_ledger", description="Secret book", intended_payoff="Used in climax"))
    state.world = WorldSetting(rules_and_lore=["Supernatural solstice deadline"])
    repo.save_state(state)

    for i in range(1, 7):
        repo.save_event(ChronologyEvent(story_id=story_id, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}"))

    # Production decision recorded for declared location constraint
    repo.save_production_decision(
        ProductionDecision(
            story_id=story_id,
            decision_key="PROD_LOCATION_BERGVILLE",
            narrative_resolution="Homestead scenes filmed on rural Bergville farm.",
            production_aspect=ProductionAspect.LOCATION,
            deferred_details="Location scouting scheduled."
        )
    )

    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.FORGE_COMPLETE
    assert assessment.current_milestone == MilestoneEnum.M3_FORGE_COMPLETE
    assert len(assessment.satisfied_milestones) == 4


def test_untrusted_stop_at_m0_overridden_and_synthesizes_deficiencies():
    """
    Test 6: Untrusted STOP at M0 is overridden by Kernel, and required state deficiencies are synthesized.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)

    story_id = "test-stop-deficiency"
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_1",
        logline="A young woman returns to her rural hometown after her father's unexplained death and discovers an ancestral debt."
    )

    # LLM proposes STOP on M0 state
    mock_provider.enqueue_response({
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Premise recorded. Stopping.",
        "confidence": 1.0,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, s, q = kernel.process_cycle(story_id=story_id, session_id="sess_1", trace_id="tr_1")

    # Untrusted STOP overridden to PROPOSE
    assert t.authority_mode == AuthorityMode.PROPOSE

    # Kernel synthesized the missing M1 invariants into repository dependencies
    deps = repo.get_dependencies(story_id)
    dep_keys = [d.dependency_key for d in deps]
    assert "PREMISE_PROTAGONIST_DEFINITION" in dep_keys or "PREMISE_COUNTERFORCE_DEFINITION" in dep_keys


def test_required_state_synthesis_is_idempotent():
    """
    Test 7: Repeated Required-State synthesis is idempotent and does not create duplicate dependencies.
    """
    engine = DependencyEngine()
    state = StoryState(story_id="test-idempotent", title="Test Story", logline="A young woman returns home after her father dies.")

    # Call 1
    deps_1 = engine.evaluate_required_state_deficiencies(state=state, events=[], existing_dependencies=[])
    assert len(deps_1) > 0

    # Call 2 with existing dependencies passed in
    deps_2 = engine.evaluate_required_state_deficiencies(state=state, events=[], existing_dependencies=deps_1)
    # Zero duplicates should be synthesized
    assert len(deps_2) == 0

    # Total combined distinct keys
    keys_1 = set(d.dependency_key for d in deps_1)
    assert len(keys_1) == len(deps_1)
