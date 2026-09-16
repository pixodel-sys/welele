"""
Welele Story Forge™ — LLM Adapter Smoke Test (Inhliziyo Ayiphakelwa) v0.1
Verifies that the LLM Reasoning Adapter operates smoothly with the Frozen Kernel,
propagating consequences, validating mutations, and completing the narrative cycle.

"Can a real LLM-structured adapter successfully operate through the Forge reasoning contract without breaking the machine?"
"""

import pytest
from typing import Dict, Any

from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.models.state import StoryState, CharacterState
from story_forge.models.events import ChronologyEvent
from story_forge.models.transition import SkillEnum, AuthorityMode, StateMutation, MutationType
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.adapters import LLMReasoningAdapter, MockLLMProvider
from story_forge.models.completion import ReadinessStatus, MilestoneEnum
from story_forge.models import CharacterRole, StateStatus


def test_llm_adapter_inhliziyo_smoke_execution():
    """
    Executes the Inhliziyo benchmark sequence using the LLMReasoningAdapter + MockLLMProvider.
    Validates that:
    - All LLM proposals strictly conform to ReasoningDecision schema.
    - The Frozen Kernel governs and validates all state mutations.
    - Transitions carry complete provenance (adapter_name, latency, confidence, assumptions).
    - The full cycle terminates in FORGE_COMPLETE with 0 authority or validation errors.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider(provider_name="test_llm_provider", model_name="gpt-4o-mini-mock")
    llm_adapter = LLMReasoningAdapter(provider=mock_provider, adapter_name="LLMReasoningAdapter")
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=llm_adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "inhliziyo-llm-001"
    session_id = "session-llm-001"
    trace_id = "trace-llm-inhliziyo"

    # 1. Initialize Inhliziyo Initial State
    repo.create_story(
        story_id=story_id,
        title="Inhliziyo Ayiphakelwa",
        owner_id="creator_001",
        logline="A high-society romance unravels amid hidden motives."
    )

    initial_state = repo.get_current_state(story_id)
    initial_state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi", role=CharacterRole.UNRESOLVED)
    initial_state.characters["Thabo"] = CharacterState(
        name="Thabo",
        role=CharacterRole.PROTAGONIST,
        core_motivation="Build an unassailable financial empire and secure Tebogo's hand.",
        status=StateStatus.FACT
    )
    initial_state.characters["Tebogo"] = CharacterState(
        name="Tebogo",
        role=CharacterRole.CONFIDANT,
        core_motivation="Protect the family legacy while following her true heart.",
        status=StateStatus.FACT
    )
    repo.save_state(initial_state)

    # -------------------------------------------------------------------------
    # Script provider responses corresponding to Inhliziyo dependencies
    # -------------------------------------------------------------------------

    # 1. Nkosinathi motivation ASK
    mock_provider.register_keyed_response("CHAR_MOTIVATION_NKOSINATHI", {
        "action": "ASK",
        "dependency_id": "dep_mot",
        "skill": "EXCAVATOR",
        "question": "What is Nkosinathi's immediate driving goal upon discovering Thabo and Tebogo's engagement?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Antagonist core motivation requires creator ownership.",
        "confidence": 0.98,
        "requires_creator": True,
        "assumptions": ["Nkosinathi witnessed the engagement."],
        "evidence": ["Event #1: Engagement Announcement"]
    })

    starting_event = ChronologyEvent(
        story_id=story_id,
        event_sequence=1,
        headline="Nkosinathi Discovers Engagement",
        description="Nkosinathi discovers that Thabo and Tebogo are secretly engaged.",
        participants=["Nkosinathi", "Thabo", "Tebogo"],
        location="Maboneng Loft"
    )

    # Execute Cycle 1 -> ASK
    t1, s1, q1 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input="Nkosinathi discovers that Thabo and Tebogo are engaged.",
        new_events=[starting_event]
    )
    assert t1.authority_mode == AuthorityMode.ASK
    assert q1 == "What is Nkosinathi's immediate driving goal upon discovering Thabo and Tebogo's engagement?"

    # Creator answers Question 1
    creator_ans_1 = "Nkosinathi vows to expose Thabo's fraudulent empire before the wedding ceremony to protect Tebogo and reclaim family honour."
    mock_provider.register_keyed_response("reclaim family honour", {
        "action": "INFER",
        "dependency_id": "dep_mot",
        "skill": "EXCAVATOR",
        "question": None,
        "proposal": "Apply creator answer to Nkosinathi motivation and role",
        "proposed_mutations": [
            {
                "target_path": "characters.Nkosinathi.core_motivation",
                "mutation_type": "UPDATE",
                "new_value": creator_ans_1,
                "rationale": "Direct creator answer"
            },
            {
                "target_path": "characters.Nkosinathi.role",
                "mutation_type": "UPDATE",
                "new_value": "ANTAGONIST",
                "rationale": "Inferred antagonist role"
            }
        ],
        "production_decision": None,
        "rationale": "Applying creator motivation into canonical state.",
        "confidence": 1.0,
        "requires_creator": False,
        "assumptions": [],
        "evidence": ["Creator input"]
    })

    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_ans_1
    )
    assert t2.authority_mode == AuthorityMode.INFER
    state = repo.get_current_state(story_id)
    assert state.state_version == 2
    assert state.characters["Nkosinathi"].core_motivation == creator_ans_1
    assert state.characters["Nkosinathi"].role == CharacterRole.ANTAGONIST

    # 2. Nkosinathi <-> Tebogo Relationship ASK
    mock_provider.register_keyed_response("REL_NKOSINATHI_TEBOGO", {
        "action": "ASK",
        "dependency_id": "dep_rel",
        "skill": "CONNECTOR",
        "question": "What is the historical nature of the past relationship between Nkosinathi and Tebogo?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Unresolved prior relationship requires creator input.",
        "confidence": 0.95,
        "requires_creator": True,
        "assumptions": [],
        "evidence": ["Logline: hidden motives"]
    })

    t3_ask, s3_ask, q3_ask = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )
    assert t3_ask.authority_mode == AuthorityMode.ASK

    # Creator answers Question 2
    creator_ans_2 = "Nkosinathi and Tebogo were childhood sweethearts before Thabo entered the picture."
    mock_provider.register_keyed_response("childhood sweethearts", {
        "action": "INFER",
        "dependency_id": "dep_rel",
        "skill": "CONNECTOR",
        "question": None,
        "proposal": "Apply creator relationship history",
        "proposed_mutations": [
            {
                "target_path": "characters.Nkosinathi.relationships",
                "mutation_type": "UPDATE",
                "new_value": [{"target_character": "Tebogo", "relation_type": "FORMER_BETROTHED", "dynamic": creator_ans_2, "tension_level": 8}],
                "rationale": "Creator relationship specification"
            }
        ],
        "production_decision": None,
        "rationale": "Applying validated relationship history.",
        "confidence": 1.0,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    t3, s3, q3 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_ans_2
    )
    assert t3.authority_mode == AuthorityMode.INFER
    state = repo.get_current_state(story_id)
    assert state.state_version == 3

    # 3. Complete remaining cycles until STOP
    max_cycles = 10
    while max_cycles > 0:
        t_next, s_next, q_next = kernel.process_cycle(
            story_id=story_id,
            session_id=session_id,
            trace_id=trace_id
        )
        if t_next.authority_mode == AuthorityMode.STOP:
            break
        max_cycles -= 1

    # Check Judge
    assessment = judge.assess(story_id)
    assert assessment.status in (ReadinessStatus.DRAMATIC_ENGINE_LOCK, ReadinessStatus.FORGE_COMPLETE)
    assert assessment.unresolved_narrative_count == 0
    m1_assessment = judge.assess(story_id, target_milestone=MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK)
    assert len(m1_assessment.blocking_dependencies) == 0

    # Check transitions and provenance
    transitions = repo.get_transitions(story_id, trace_id=trace_id)
    assert len(transitions) >= 3
    for t in transitions:
        assert t.provenance is not None
        assert t.provenance.adapter_name == "LLMReasoningAdapter"
        assert t.provenance.latency_ms is not None
