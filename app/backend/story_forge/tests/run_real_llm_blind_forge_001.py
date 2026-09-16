"""
Welele Story Forge™ — Real LLM Blind Forge Test 001 Execution Script
Executes Blind Forge Test 001 using the real HttpLLMProvider (Gemini) under strict unguided experimental conditions:
- Pure raw premise + creative/production objective only
- Zero pre-baked characters, dependencies, chronology, or hidden hacks
- Full audit trace and story state captured for independent assessment
"""

import sys
import os
import time
import json
import logging
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

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
logger = logging.getLogger("welele.story_forge.blind_001")


def simulate_creator_response_to_question(question: str) -> str:
    """
    Supplies consistent, unguided creator responses to questions asked by the LLM,
    drawing solely from the high-level premise and creative objectives.
    """
    q_lower = question.lower()
    if "rival" in q_lower or "clan" in q_lower or "creditor" in q_lower or "antagonist" in q_lower or "counterforce" in q_lower or "opposing" in q_lower:
        return "The rival clan is the Ndlovu family, led by Bheki Ndlovu, an imposing warlord who claims Baba Mthembu bound the firstborn to seal their wealth."
    elif "motivation" in q_lower or "goal" in q_lower or "driven" in q_lower or "seeking" in q_lower or "aim" in q_lower:
        return "Zodwa is determined to uncover the truth behind her father's death and expose the ancestral debt as an investigative journalist, while protecting her family from supernatural retribution."
    elif "protagonist" in q_lower or "young woman" in q_lower or ("name" in q_lower and "zodwa" not in q_lower):
        return "Her name is Zodwa Khumalo, a 26-year-old investigative journalist who left the village 6 years ago."
    elif "plant" in q_lower or "document" in q_lower or "study" in q_lower or "locked" in q_lower or "deed" in q_lower or "contract" in q_lower or "proof" in q_lower:
        return "The locked study holds Baba Mthembu's iron lockbox containing the 1988 Blood Ledger proving the ancestral pact."
    elif "relationship" in q_lower or "dynamic" in q_lower or "conflict" in q_lower:
        return "Bheki Ndlovu was once Baba Mthembu's sworn ally before the debt defaulted; he treats Zodwa with patronizing menace and demands immediate payment."
    elif "supernatural" in q_lower or "mystery" in q_lower or "death" in q_lower or "father" in q_lower:
        return "Her father Sipho died of sudden heart failure inside the locked study with no sign of forced entry, but his journal mentions nightly whispers from the river."
    elif "location" in q_lower or "setting" in q_lower or "production" in q_lower:
        return "The Khumalo homestead in rural Bergville, KZN, and Zodwa's apartment in Johannesburg."
    else:
        return f"Regarding '{question}': The family must resolve the hidden blood pact before the upcoming solstice ceremony."


def run_blind_forge_001_real_llm():
    print("=" * 80)
    print("WELELE STORY FORGE™ — REAL LLM BLIND FORGE TEST 001")
    print("=" * 80)

    # 1. Initialize Real Provider & Adapter
    real_provider = HttpLLMProvider()
    print(f"Provider Type:      {type(real_provider).__name__}")
    print(f"Provider Name:      {real_provider.provider_name}")
    print(f"Model Name:         {real_provider.model_name}")
    print(f"Base URL:           {real_provider.base_url}")
    
    adapter = LLMReasoningAdapter(
        provider=real_provider,
        adapter_name="LLMReasoningAdapter",
        temperature=0.2,
        timeout_seconds=45.0
    )

    repo = InMemoryStoryForgeRepository()
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "blind-001-real"
    session_id = "session-blind-001-real"
    trace_id = "trace-blind-001-real"

    raw_premise = (
        "A young woman returns to her rural hometown after her father's unexplained death. "
        "She discovers his locked study contains documents proving that their family's wealth "
        "originated from an ancestral debt owed to a rival clan."
    )
    creative_objective = "Develop this premise into a supernatural family thriller for a vertical micro-drama series."
    production_objective = "Rural KwaZulu-Natal & Johannesburg locations, episodic suspense hooks."

    print(f"\n[RAW CREATOR MATERIAL]")
    print(f"  Logline: {raw_premise}")
    print(f"  Creative Objective: {creative_objective}")
    print(f"  Production Objective: {production_objective}")

    # Step 1: Initialize Story with ONLY raw premise
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_blind_real",
        logline=raw_premise
    )

    initial_state = repo.get_current_state(story_id)
    assert len(initial_state.characters) == 0
    assert len(initial_state.plants) == 0
    assert len(repo.get_events(story_id)) == 0
    print("\n[VERIFIED INITIAL STATE]: 0 characters, 0 events, 0 plants, 0 pre-baked dependencies.")

    # Execute Autonomous Cycles
    max_cycles = 8
    cycle_num = 1
    latest_creator_response = None
    latest_creator_input = raw_premise

    while cycle_num <= max_cycles:
        print("\n" + "=" * 80)
        print(f">>> RUNNING FORGE CYCLE {cycle_num} OF {max_cycles}")
        print("=" * 80)

        t, s, q = kernel.process_cycle(
            story_id=story_id,
            session_id=session_id,
            trace_id=trace_id,
            creator_input=latest_creator_input if cycle_num == 1 else None,
            creator_response=latest_creator_response
        )

        latest_creator_input = None
        latest_creator_response = None

        print(f"[CYCLE {cycle_num} OUTCOME]")
        print(f"  Authority Mode:    {t.authority_mode.value}")
        print(f"  Skill Invoked:     {t.skill.value if t.skill else 'NONE'}")
        print(f"  Question:          {q}")
        print(f"  Interpretation:    {t.interpretation}")
        print(f"  Mutations Count:   {len(t.state_changes)}")
        for m in t.state_changes:
            print(f"    * {m.target_path} [{m.mutation_type.value}]: {m.rationale}")
        print(f"  State Version:     v{s.state_version}")
        print(f"  Characters in Canon:{list(s.characters.keys())}")
        print(f"  HTTP Latency:      {t.provenance.latency_ms} ms")
        print(f"  Confidence:        {t.provenance.confidence}")

        if t.authority_mode == AuthorityMode.STOP:
            print(f"\n[FORGE CERTIFIED STOP AT CYCLE {cycle_num}]")
            break

        if (t.authority_mode in (AuthorityMode.ASK, AuthorityMode.PROPOSE)) and q:
            ans = simulate_creator_response_to_question(q)
            print(f"\n  [CREATOR RESPONSE TO {t.authority_mode.value}]: \"{ans}\"")
            latest_creator_response = ans

        cycle_num += 1

    # Final Evaluation by Forge Judge
    print("\n" + "=" * 80)
    print("FINAL FORGE JUDGE ASSESSMENT (REAL LLM RUN)")
    print("=" * 80)
    final_assessment = judge.assess(story_id)
    final_state = repo.get_current_state(story_id)
    all_transitions = repo.get_transitions(story_id, trace_id=trace_id)

    print(f"  Readiness Status:     {final_assessment.status.value}")
    print(f"  Assessed Version:     v{final_assessment.assessed_state_version}")
    print(f"  Unresolved Narrative: {final_assessment.unresolved_narrative_count}")
    print(f"  Unresolved Causal:    {final_assessment.unresolved_causal_count}")
    print(f"  Unresolved Temporal:  {final_assessment.unresolved_temporal_count}")
    print(f"  Production Decisions: {final_assessment.production_decisions_count}")
    print(f"  Blocking Dependencies:{final_assessment.blocking_dependencies}")

    print("\n" + "=" * 80)
    print("FINAL CANONICAL STORY STATE SUMMARY")
    print("=" * 80)
    print(f"  Title:      {final_state.title}")
    print(f"  Logline:    {final_state.logline}")
    print(f"  Version:    v{final_state.state_version}")
    print(f"  Characters: {len(final_state.characters)}")
    for name, c in final_state.characters.items():
        print(f"    - {name} ({c.role.value}): Motivation='{c.core_motivation}', Status={c.status.value}")
    print(f"  Plants:     {len(final_state.plants)}")
    print(f"  Events:     {len(repo.get_events(story_id))}")
    print(f"  Production Decisions Recorded: {len(repo.get_production_decisions(story_id))}")

    # Output trace JSON for independent artifact generation
    trace_data = {
        "story_id": story_id,
        "model_identifier": real_provider.model_name,
        "provider": real_provider.provider_name,
        "forge_kernel_version": "0.2.0",
        "forge_judge_version": "0.2.0",
        "total_cycles": len(all_transitions),
        "final_state_version": final_state.state_version,
        "judge_status": final_assessment.status.value,
        "assessment_notes": final_assessment.assessment_notes,
        "transitions": [
            {
                "sequence": tr.sequence,
                "authority_mode": tr.authority_mode.value,
                "skill": tr.skill.value if tr.skill else None,
                "question": tr.question_asked,
                "interpretation": tr.interpretation,
                "latency_ms": tr.provenance.latency_ms,
                "confidence": tr.provenance.confidence,
                "mutations": [
                    {"path": m.target_path, "type": m.mutation_type.value, "rationale": m.rationale}
                    for m in tr.state_changes
                ]
            }
            for tr in all_transitions
        ]
    }

    trace_file = os.path.join(os.path.dirname(__file__), "blind_001_real_llm_trace.json")
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2)

    print(f"\n[Trace JSON saved to: {trace_file}]")
    return trace_data


if __name__ == "__main__":
    run_blind_forge_001_real_llm()
