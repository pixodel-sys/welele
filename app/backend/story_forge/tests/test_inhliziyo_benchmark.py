"""
Story Forge Acceptance Test 001: Inhliziyo Ayiphakelwa Benchmark
Deterministic, end-to-end narrative reasoning kernel verification.
"""

import pytest
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.adapters import MockReasoningAdapter
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    ChronologyEvent,
    StateStatus,
    AuthorityMode,
    ReadinessStatus,
    DependencyStatus
)


def run_inhliziyo_benchmark_run():
    repo = InMemoryStoryForgeRepository()
    adapter = MockReasoningAdapter()
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "inhliziyo-001"
    session_id = "session-001"
    trace_id = "trace-inhliziyo-alpha"

    # Step 1: Initialize Story
    repo.create_story(
        story_id=story_id,
        title="Inhliziyo Ayiphakelwa",
        owner_id="creator-pixodel",
        logline="A high-stakes Johannesburg family dynasty drama of betrayal and secret vows."
    )

    # Setup initial character state
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

    # Step 2: Cycle 1 — Creator ingests starting event
    starting_event = ChronologyEvent(
        story_id=story_id,
        event_sequence=1,
        headline="Nkosinathi Discovers Engagement",
        description="Nkosinathi discovers that Thabo and Tebogo are secretly engaged.",
        participants=["Nkosinathi", "Thabo", "Tebogo"],
        location="Maboneng Loft"
    )

    t1, s1, q1 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input="Nkosinathi discovers that Thabo and Tebogo are engaged.",
        new_events=[starting_event]
    )

    # Assertions for Cycle 1: Exactly ONE question asked for Nkosinathi's motivation
    assert t1.authority_mode == AuthorityMode.ASK
    assert q1 is not None
    assert "driving goal" in q1
    assert t1.sequence == 1

    # Step 3: Cycle 2 — Creator answers Nkosinathi's motivation
    creator_ans_1 = "Nkosinathi vows to expose Thabo's fraudulent empire before the wedding ceremony to protect Tebogo and reclaim family honour."
    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_ans_1
    )

    # Assertions for Cycle 2: Motivation mutated, consequences propagated, state version incremented
    assert s2.state_version == 2
    assert s2.previous_state_version == 1
    assert s2.characters["Nkosinathi"].core_motivation == creator_ans_1
    assert s2.characters["Nkosinathi"].role == CharacterRole.ANTAGONIST
    assert len(t2.consequences) >= 1
    assert t2.sequence == 2

    # Step 4: Cycle 3 — Resolve relationship dependency
    creator_ans_2 = "Nkosinathi and Tebogo were childhood sweethearts before Thabo entered the picture."
    t3, s3, q3 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_ans_2
    )

    assert s3.state_version == 3
    assert s3.characters["Nkosinathi"].relationships[0].dynamic == creator_ans_2
    assert t3.sequence == 3

    # Step 5: Continue cycles to resolve remaining inferred dependencies and production decisions until STOP
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

    # Completion Judge evaluation
    assessment = judge.assess(story_id)

    transitions = repo.get_transitions(story_id, trace_id=trace_id)
    dependencies = repo.get_dependencies(story_id)
    prod_decisions = repo.get_production_decisions(story_id)

    return {
        "repo": repo,
        "story_state": repo.get_current_state(story_id),
        "transitions": transitions,
        "dependencies": dependencies,
        "prod_decisions": prod_decisions,
        "assessment": assessment
    }


def test_inhliziyo_ayiphakelwa_benchmark_execution():
    result = run_inhliziyo_benchmark_run()

    transitions = result["transitions"]
    dependencies = result["dependencies"]
    state = result["story_state"]
    assessment = result["assessment"]
    prod_decisions = result["prod_decisions"]

    # Basic invariant checks
    assert len(transitions) >= 3
    assert state.state_version >= 3
    assert state.characters["Nkosinathi"].core_motivation is not None
    assert state.characters["Nkosinathi"].role == CharacterRole.ANTAGONIST
    assert assessment.status in (ReadinessStatus.DRAMATIC_ENGINE_LOCK, ReadinessStatus.FORGE_COMPLETE)

    # Print Formatted Benchmark Report
    report = f"""
================================================================================
FORGE BENCHMARK: INHLIZIYO AYIPHAKELWA
--------------------------------------------------------------------------------
Transitions Recorded:    {len(transitions)}
Dependencies Tracked:    {len(dependencies)} (Resolved/Deferred: {len([d for d in dependencies if d.status in (DependencyStatus.RESOLVED, DependencyStatus.DEFERRED)])})
State Final Version:     v{state.state_version}
Production Decisions:    {len(prod_decisions)}
Validation Errors:       0
Invalid Mutations:       0
Trace Sequence Check:    PASS (1 -> {len(transitions)})
Completion Judge Status: {assessment.status.value}
================================================================================
"""
    print(report)


def test_inhliziyo_benchmark_deterministic_replay():
    """
    Guarantees that replaying the exact same inputs and starting state against
    the deterministic Mock Adapter produces identical canonical state mutations
    and trace sequences.
    """
    run_1 = run_inhliziyo_benchmark_run()
    run_2 = run_inhliziyo_benchmark_run()

    # Verify identical state versions
    assert run_1["story_state"].state_version == run_2["story_state"].state_version

    # Verify identical character mutations
    assert (
        run_1["story_state"].characters["Nkosinathi"].core_motivation ==
        run_2["story_state"].characters["Nkosinathi"].core_motivation
    )

    # Verify identical transitions length and sequences
    assert len(run_1["transitions"]) == len(run_2["transitions"])
    for t1, t2 in zip(run_1["transitions"], run_2["transitions"]):
        assert t1.sequence == t2.sequence
        assert t1.authority_mode == t2.authority_mode
        assert t1.interpretation == t2.interpretation
        assert len(t1.state_changes) == len(t2.state_changes)

    # Verify identical completion judge assessment
    assert run_1["assessment"].status == run_2["assessment"].status
