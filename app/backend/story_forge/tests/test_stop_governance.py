"""
Welele Story Forge™ — STOP Governance & Completion Invariants Regression Test Suite
Validates that FORGE_COMPLETE is an architectural determination by Kernel + ForgeJudge,
and can NEVER be produced solely by an untrusted LLM STOP decision or confidence score.
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
from story_forge.adapters import MockReasoningAdapter, MockLLMProvider, LLMReasoningAdapter


def test_stop_with_unresolved_dependency_rejected_by_kernel():
    """
    Test A — STOP with unresolved character dependency.
    Given an unmotivated character in canon, if the model proposes STOP,
    the Kernel must override STOP to ACTIVE, and ForgeJudge must return NOT_READY.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-stop-unresolved"
    repo.create_story(story_id=story_id, title="Test Story", owner_id="creator_1", logline="A story with an unmotivated character.")
    
    # State has a character without motivation
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation=None)
    repo.save_state(state)

    # Model attempts to propose STOP
    mock_provider.set_generator(lambda s, u, r: {
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "I feel the story is done.",
        "confidence": 0.95,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, new_state, q = kernel.process_cycle(
        story_id=story_id,
        session_id="sess-1",
        trace_id="trace-1"
    )

    # Kernel MUST override STOP to ACTIVE/PROPOSE
    assert t.authority_mode == AuthorityMode.PROPOSE
    assessment = judge.assess(story_id)
    assert assessment.status != ReadinessStatus.FORGE_COMPLETE
    assert "PREMISE_PROTAGONIST_DEFINITION" in assessment.blocking_dependencies or "CHAR_MOTIVATION_ZODWA" in assessment.blocking_dependencies or "M1_PROTAGONIST_MOTIVATION_REQUIRED" in assessment.blocking_dependencies


def test_stop_with_unresolved_causal_dependency():
    """
    Test B — STOP with unresolved causal dependency.
    If a CAUSAL dependency remains unresolved, ForgeJudge must return NOT_READY.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-stop-causal"
    repo.create_story(story_id=story_id, title="Test Story", owner_id="creator_1", logline="A murder mystery.")
    
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation="Find killer")
    repo.save_state(state)

    # Add unresolved CAUSAL dependency
    causal_dep = Dependency(
        story_id=story_id,
        dependency_key="CAUSAL_POISON_ORIGIN",
        dependency_type=DependencyType.CAUSAL,
        status=DependencyStatus.DETECTED,
        target_entity="MURDER_WEAPON",
        description="Origin and delivery mechanism of the poison is unexplained.",
        components=PriorityComponents(impact=8, urgency=7, risk=8, leverage=7, cost=2)
    )
    repo.save_dependency(causal_dep)

    mock_provider.set_generator(lambda s, u, r: {
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Stopping early.",
        "confidence": 0.99,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, new_state, q = kernel.process_cycle(story_id=story_id, session_id="sess-1", trace_id="trace-1")
    assert t.authority_mode == AuthorityMode.PROPOSE

    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.NOT_READY
    assert assessment.unresolved_causal_count == 1
    assert "CAUSAL_POISON_ORIGIN" in assessment.blocking_dependencies


def test_stop_with_unresolved_temporal_dependency():
    """
    Test C — STOP with unresolved temporal/knowledge dependency.
    If a TEMPORAL dependency remains unresolved, ForgeJudge must return NOT_READY.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-stop-temporal"
    repo.create_story(story_id=story_id, title="Test Story", owner_id="creator_1", logline="A timeline heist.")
    
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(name="Zodwa", role=CharacterRole.PROTAGONIST, core_motivation="Steal ledger")
    repo.save_state(state)

    # Add unresolved TEMPORAL dependency
    temporal_dep = Dependency(
        story_id=story_id,
        dependency_key="TEMPORAL_ALIBI_GAP",
        dependency_type=DependencyType.TEMPORAL,
        status=DependencyStatus.DETECTED,
        target_entity="TIMELINE",
        description="2-hour gap between vault breach and police arrival is unaccounted for.",
        components=PriorityComponents(impact=7, urgency=7, risk=7, leverage=6, cost=2)
    )
    repo.save_dependency(temporal_dep)

    mock_provider.set_generator(lambda s, u, r: {
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Stopping before timeline is fixed.",
        "confidence": 0.90,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, new_state, q = kernel.process_cycle(story_id=story_id, session_id="sess-1", trace_id="trace-1")
    assert t.authority_mode == AuthorityMode.PROPOSE

    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.NOT_READY
    assert assessment.unresolved_temporal_count == 1
    assert "TEMPORAL_ALIBI_GAP" in assessment.blocking_dependencies


def test_stop_with_incomplete_creator_objective():
    """
    Test D — STOP with incomplete creator objective / ungrounded premise references.
    Given a premise establishing a rival clan conflict and locked study documents,
    if only 1 character is defined with 0 counterforce and 0 plants,
    ForgeJudge must evaluate NOT_READY or DEPENDENCIES_RESOLVED, blocking completion.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-stop-premise-objective"
    raw_logline = "A young woman discovers her family wealth originated from an ancestral debt owed to a rival clan."
    repo.create_story(story_id=story_id, title="Ancestral Debt", owner_id="creator_1", logline=raw_logline)
    
    # Only 1 protagonist in state; no antagonist and no relationships
    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(
        name="Zodwa",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Uncover father's death"
    )
    repo.save_state(state)

    mock_provider.set_generator(lambda s, u, r: {
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Ending early.",
        "confidence": 0.95,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, new_state, q = kernel.process_cycle(story_id=story_id, session_id="sess-1", trace_id="trace-1")
    
    # Kernel detects ungrounded PREMISE_COUNTERFORCE_DEFINITION
    assert t.authority_mode == AuthorityMode.PROPOSE
    
    assessment = judge.assess(story_id)
    assert assessment.status != ReadinessStatus.FORGE_COMPLETE


def test_legitimate_stop_satisfies_all_invariants():
    """
    Test E — Legitimate STOP.
    When all completion invariants are satisfied (protagonist with motivation,
    antagonist with motivation, reciprocal relationship, plant payoff, zero unresolved dependencies),
    the Kernel and ForgeJudge certify FORGE_COMPLETE.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-stop-legitimate"
    repo.create_story(story_id=story_id, title="Ancestral Debt", owner_id="creator_1", logline="A supernatural thriller.")
    
    # Set up fully integrated story state
    state = repo.get_current_state(story_id)
    zodwa = CharacterState(
        name="Zodwa",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Uncover the truth and protect family",
        relationships=[
            CharacterRelationship(
                target_character="Bheki",
                relation_type="BLOOD_RIVAL",
                dynamic="Opposing clan heir demanding debt",
                tension_level=9
            )
        ]
    )
    bheki = CharacterState(
        name="Bheki",
        role=CharacterRole.ANTAGONIST,
        core_motivation="Reclaim ancestral sacred lands",
        relationships=[
            CharacterRelationship(
                target_character="Zodwa",
                relation_type="BLOOD_RIVAL",
                dynamic="Demands blood debt from Zodwa",
                tension_level=9
            )
        ]
    )
    plant = NarrativePlant(
        element_code="PLANT_ANCESTRAL_DEBT_DOC",
        description="Sealed parchment in locked study",
        intended_payoff="Reveals solstice deadline",
        payoff_status="PLANTED"
    )
    state.characters = {"Zodwa": zodwa, "Bheki": bheki}
    state.plants = [plant]
    state.world.rules_and_lore = ["Ancestral debt rules"]
    repo.save_state(state)

    # 6 canonical chronology events for M2 satisfaction
    for i in range(1, 7):
        repo.save_event(ChronologyEvent(story_id=story_id, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}"))

    # Model proposes STOP
    mock_provider.set_generator(lambda s, u, r: {
        "action": "STOP",
        "skill": "FORGE_JUDGE",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "All core characters, motivations, reciprocal relations, and plants established.",
        "confidence": 0.98,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t, new_state, q = kernel.process_cycle(story_id=story_id, session_id="sess-1", trace_id="trace-1")
    
    # Kernel accepts STOP because ForgeJudge certifies FORGE_COMPLETE
    assert t.authority_mode == AuthorityMode.STOP
    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.FORGE_COMPLETE
    assert len(assessment.blocking_dependencies) == 0


def test_llm_cannot_self_certify_completion():
    """
    Test F — LLM Cannot Self-Certify Completion.
    Proves that regardless of the LLM's confidence score (0.50 -> 0.95 -> 1.00)
    and authoritative rationale ('Story is 100% complete and flawless'),
    if an unresolved dependency exists in state, the Kernel and Judge REJECT completion.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "test-self-certify-rejection"
    repo.create_story(story_id=story_id, title="Test Story", owner_id="creator_1", logline="A premise.")
    
    # State has unmotivated protagonist
    state = repo.get_current_state(story_id)
    state.characters["Hero"] = CharacterState(name="Hero", role=CharacterRole.PROTAGONIST, core_motivation=None)
    repo.save_state(state)

    # Test increasing levels of LLM confidence asserting completion
    confidence_levels = [0.50, 0.90, 0.99, 1.00]

    for conf in confidence_levels:
        mock_provider.set_generator(lambda s, u, r, c=conf: {
            "action": "STOP",
            "skill": "FORGE_JUDGE",
            "question": None,
            "proposal": None,
            "proposed_mutations": [],
            "production_decision": None,
            "rationale": f"I am {c*100}% certain the story is fully completed and ready for filming.",
            "confidence": c,
            "requires_creator": False,
            "assumptions": [],
            "evidence": ["Subjective opinion"]
        })

        t, new_state, q = kernel.process_cycle(
            story_id=story_id,
            session_id=f"sess-conf-{conf}",
            trace_id=f"trace-conf-{conf}"
        )

        # Kernel MUST override STOP to ACTIVE at EVERY confidence level
        assert t.authority_mode == AuthorityMode.PROPOSE, f"Failed at confidence {conf}: Kernel allowed LLM to self-certify STOP"
        assessment = judge.assess(story_id)
        assert assessment.status != ReadinessStatus.FORGE_COMPLETE
        assert assessment.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE
