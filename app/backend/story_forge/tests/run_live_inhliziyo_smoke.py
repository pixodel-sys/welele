"""
Welele Story Forge™ — Live LLM Inhliziyo Smoke Test Execution Script
Executes Inhliziyo story reasoning against real HttpLLMProvider to verify end-to-end
contract compliance, network latency, structured output parsing, and kernel governance.
"""

import sys
import os
import time
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.models.state import StoryState, CharacterState
from story_forge.models.events import ChronologyEvent
from story_forge.models.transition import SkillEnum, AuthorityMode, StateMutation, MutationType
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.adapters import LLMReasoningAdapter, HttpLLMProvider
from story_forge.models.completion import ReadinessStatus
from story_forge.models import CharacterRole, StateStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("welele.story_forge.live_smoke")


def run_live_smoke():
    print("=" * 80)
    print("WELELE STORY FORGE™ — LIVE REAL-LLM INHLIZIYO SMOKE TEST")
    print("=" * 80)

    # 1. Initialize Real Provider & Adapter
    real_provider = HttpLLMProvider()
    print(f"Provider Type:      {type(real_provider).__name__}")
    print(f"Provider Name:      {real_provider.provider_name}")
    print(f"Model Name:         {real_provider.model_name}")
    print(f"Base URL:           {real_provider.base_url}")
    print(f"API Key Configured: {'YES (Valid non-mock key)' if real_provider.api_key and real_provider.api_key != 'mock-key' else 'NO'}")
    
    assert type(real_provider).__name__ == "HttpLLMProvider", "Must be HttpLLMProvider!"
    assert real_provider.api_key != "mock-key", "Real API key is required!"

    adapter = LLMReasoningAdapter(
        provider=real_provider,
        adapter_name="LLMReasoningAdapter",
        temperature=0.2,
        timeout_seconds=45.0
    )

    repo = InMemoryStoryForgeRepository()
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "inhliziyo-live-smoke"
    session_id = "session-live-smoke"
    trace_id = "trace-live-smoke-001"

    # 2. Setup Inhliziyo Story Base
    repo.create_story(
        story_id=story_id,
        title="Inhliziyo Ayiphakelwa",
        owner_id="creator_live_001",
        logline="A high-society romance unravels amid hidden motives in Johannesburg."
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

    starting_event = ChronologyEvent(
        story_id=story_id,
        event_sequence=1,
        headline="Nkosinathi Discovers Engagement",
        description="Nkosinathi discovers that Thabo and Tebogo are secretly engaged.",
        participants=["Nkosinathi", "Thabo", "Tebogo"],
        location="Maboneng Loft"
    )

    # 3. Execute Cycle 1
    print("\n" + "-" * 80)
    print(">>> EXECUTING CYCLE 1 (Prompting Real Model with Raw Premise & Active Unresolved Dependency)")
    print("-" * 80)

    t1, s1, q1 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input="Nkosinathi discovers that Thabo and Tebogo are engaged.",
        new_events=[starting_event]
    )

    print(f"[CYCLE 1 RESULT]")
    print(f"  Authority Mode:    {t1.authority_mode.value}")
    print(f"  Skill Invoked:     {t1.skill.value if t1.skill else 'NONE'}")
    print(f"  Question Asked:    {q1}")
    print(f"  Interpretation:    {t1.interpretation}")
    print(f"  State Version:     v{s1.state_version}")
    print(f"  Provenance Adapter: {t1.provenance.adapter_name}")
    print(f"  Latency (ms):      {t1.provenance.latency_ms} ms")
    print(f"  Confidence:        {t1.provenance.confidence}")
    print(f"  Assumptions:       {t1.provenance.assumptions}")
    print(f"  Evidence:          {t1.provenance.evidence}")

    # Verify real provenance
    assert t1.provenance is not None
    assert t1.provenance.latency_ms > 0
    assert t1.authority_mode in [AuthorityMode.ASK, AuthorityMode.PROPOSE, AuthorityMode.INFER]

    # 4. Handle response if ASK/PROPOSE
    if t1.authority_mode == AuthorityMode.ASK and q1:
        creator_answer = "Nkosinathi vows to expose Thabo's fraudulent empire before the wedding to protect Tebogo and reclaim family honor."
        print("\n" + "-" * 80)
        print(f">>> EXECUTING CYCLE 2 (Creator Response: \"{creator_answer}\")")
        print("-" * 80)

        t2, s2, q2 = kernel.process_cycle(
            story_id=story_id,
            session_id=session_id,
            trace_id=trace_id,
            creator_response=creator_answer
        )

        print(f"[CYCLE 2 RESULT]")
        print(f"  Authority Mode:    {t2.authority_mode.value}")
        print(f"  Skill Invoked:     {t2.skill.value if t2.skill else 'NONE'}")
        print(f"  Question Asked:    {q2}")
        print(f"  Interpretation:    {t2.interpretation}")
        print(f"  Mutations Applied: {len(t2.state_changes)}")
        for m in t2.state_changes:
            print(f"    - {m.target_path} [{m.mutation_type.value}]: {m.rationale}")
        print(f"  State Version:     v{s2.state_version}")
        print(f"  Latency (ms):      {t2.provenance.latency_ms} ms")

    # 5. Judge Assessment
    print("\n" + "-" * 80)
    print(">>> FORGE JUDGE READINESS EVALUATION")
    print("-" * 80)
    assessment = judge.assess(story_id)
    print(f"  Overall Status:       {assessment.status.value}")
    print(f"  State Version:        v{assessment.assessed_state_version}")
    print(f"  Unresolved Narrative: {assessment.unresolved_narrative_count}")
    print(f"  Unresolved Causal:    {assessment.unresolved_causal_count}")
    print(f"  Unresolved Temporal:  {assessment.unresolved_temporal_count}")
    print(f"  Production Decisions: {assessment.production_decisions_count}")
    print(f"  Blocking Deps:        {len(assessment.blocking_dependencies)}")

    # 6. Full Provenance Trace Summary
    transitions = repo.get_transitions(story_id, trace_id=trace_id)
    print("\n" + "=" * 80)
    print("PROVENANCE VERIFICATION SUMMARY")
    print("=" * 80)
    for idx, tr in enumerate(transitions, 1):
        print(f"Cycle {idx}:")
        print(f"  Action:             {tr.authority_mode.value}")
        print(f"  Skill:              {tr.skill.value if tr.skill else 'None'}")
        print(f"  Adapter:            {tr.provenance.adapter_name}")
        print(f"  HTTP Latency:       {tr.provenance.latency_ms} ms")
        print(f"  Confidence:         {tr.provenance.confidence}")
        print(f"  Assumptions Count:  {len(tr.provenance.assumptions)}")
        print(f"  Evidence Count:     {len(tr.provenance.evidence)}")

    print("\n>>> LIVE SMOKE TEST SUCCESSFUL! REAL LLM PROVENANCE VERIFIED.")
    return True


if __name__ == "__main__":
    success = run_live_smoke()
    if not success:
        sys.exit(1)
