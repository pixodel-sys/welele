"""
Welele Story Forge™ — Real LLM Proof Run 002: Comedy (The Wrong Funeral)
Executes Proof Run 002 using the real HttpLLMProvider (Gemini) under strict unguided experimental conditions:
- Pure raw premise + creative/production objective only
- Zero pre-baked characters, dependencies, chronology, or hidden assistance
- Full audit trace and story state captured for independent assessment
"""

import sys
import os
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
from story_forge.models.completion import ReadinessStatus, MilestoneEnum
from story_forge.models import CharacterRole, StateStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("welele.story_forge.proof_002")


def simulate_creator_response_to_question(question: str) -> str:
    """
    Supplies consistent, unguided creator responses to questions asked by the LLM,
    grounded strictly in the comedy premise and creative/production objectives.
    """
    q_lower = question.lower()
    
    # 1. Mistaken identity / Who they mistake him for
    if "mistake" in q_lower or "who" in q_lower and ("family" in q_lower or "waiting" in q_lower or "think" in q_lower):
        return (
            "The family mistakes him for 'Dr. Mthembu', the eccentric spiritual practitioner and overseas-trained doctor "
            "hired to perform the sacred ancestral send-off and unlock the grandfather's hidden inheritance vault."
        )
    # 2. Counterforce / Opposing family members / Antagonist
    elif "family" in q_lower or "matriarch" in q_lower or "rival" in q_lower or "antagonist" in q_lower or "counterforce" in q_lower or "opposing" in q_lower or "mandla" in q_lower:
        return (
            "The family is led by Gogo MaSithole, a stern, deeply superstitious matriarch, and her suspicious, hot-tempered "
            "son Mandla Sithole, who is armed and watching 'Dr. Mthembu' like a hawk to ensure he doesn't steal the inheritance."
        )
    # 3. Protagonist motivation / Goal
    elif "motivation" in q_lower or "goal" in q_lower or "driven" in q_lower or "seeking" in q_lower or "aim" in q_lower or "want" in q_lower:
        return (
            "Sipho's immediate goal is to escape the venue without exposing himself and get to his real uncle's funeral in time, "
            "but as the family showers him with bizarre reverence and threats of supernatural curses if he leaves before the ritual, "
            "he is forced to hilariously fake being a master spiritual healer to survive."
        )
    # 4. Protagonist identity / Name / Profession
    elif "protagonist" in q_lower or "man" in q_lower or ("name" in q_lower and "sipho" not in q_lower) or "profession" in q_lower:
        return (
            "His name is Sipho Khanyile, a timid 29-year-old tax consultant from Soweto who is utterly terrified of confrontation "
            "and was only trying to deliver his mother's casserole dish to his late Uncle Themba's service."
        )
    # 5. Supernatural / Rules / Ghost / Spirit / Phenomenon
    elif "supernatural" in q_lower or "spirit" in q_lower or "ritual" in q_lower or "curse" in q_lower or "ghost" in q_lower:
        return (
            "The deceased patriarch, Baba Sithole, was believed to have sealed an ancestral fortune with a mischievous spirit. "
            "Whenever someone tells a blatant lie or blasphemes the ancestors at the funeral, comical poltergeist disturbances "
            "erupt (the casket rattles, the choir's pitch distorts, wind blows indoors) which the family assumes are signs of Sipho's immense psychic aura."
        )
    # 6. Narrative plant / Artifact / Item
    elif "plant" in q_lower or "item" in q_lower or "object" in q_lower or "dish" in q_lower or "artifact" in q_lower or "document" in q_lower or "box" in q_lower:
        return (
            "The mother's pyrex casserole dish covered in floral foil that Sipho is carrying—the family believes it is the sacred sacred medicine vessel containing rare ancestral herbs, which they forbid him from opening until the climax."
        )
    # 7. Relationship dynamic / Conflict
    elif "relationship" in q_lower or "dynamic" in q_lower or "tension" in q_lower:
        return (
            "Mandla is intensely jealous of Sipho, suspecting he is a fraud trying to claim Gogo's blessing, creating a constant cat-and-mouse dynamic across every room of the venue."
        )
    # 8. Setting / Venue / Production constraints
    elif "setting" in q_lower or "location" in q_lower or "venue" in q_lower or "production" in q_lower or "budget" in q_lower:
        return (
            "The Sithole family mansion and front yard marquee in Vosloorus, encompassing the VIP tent, the kitchen, the private study where the casket rests, and the gated driveway."
        )
    else:
        return (
            f"Regarding '{question}': Sipho must balance keeping up the charade with finding a way to escape before the final casket viewing ritual at sunset."
        )


def run_proof_002_comedy_real_llm():
    print("=" * 80)
    print("WELELE STORY FORGE™ — REAL LLM PROOF RUN 002: COMEDY")
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

    story_id = "proof-002-comedy-real"
    session_id = "session-proof-002"
    trace_id = "trace-proof-002"

    raw_premise = (
        "A man arrives at a funeral expecting to mourn his uncle. "
        "He quickly realises he is at the wrong funeral. "
        "Before he can leave, the family mistakes him for someone they have been waiting for."
    )
    creative_objective = "South African supernatural comedy / family comedy, designed as a vertical microdrama."
    production_objective = "Low-to-medium budget. Primarily one funeral venue and surrounding locations. Strong character comedy, escalating misunderstandings and episode-ending hooks."

    print(f"\n[RAW CREATOR MATERIAL]")
    print(f"  Title: The Wrong Funeral")
    print(f"  Logline: {raw_premise}")
    print(f"  Creative Objective: {creative_objective}")
    print(f"  Production Objective: {production_objective}")

    # Step 1: Initialize Story with ONLY raw premise
    repo.create_story(
        story_id=story_id,
        title="The Wrong Funeral",
        owner_id="creator_proof_002",
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
    print("FINAL FORGE JUDGE ASSESSMENT (REAL LLM RUN - PROOF 002)")
    print("=" * 80)
    final_assessment = judge.assess(story_id)
    final_state = repo.get_current_state(story_id)
    all_transitions = repo.get_transitions(story_id, trace_id=trace_id)

    print(f"  Readiness Status:     {final_assessment.status.value}")
    print(f"  Current Milestone:    {final_assessment.current_milestone.value if final_assessment.current_milestone else 'NONE'}")
    print(f"  Satisfied Milestones: {[m.value for m in final_assessment.satisfied_milestones]}")
    print(f"  Assessed Version:     v{final_assessment.assessed_state_version}")
    print(f"  Unresolved Narrative: {final_assessment.unresolved_narrative_count}")
    print(f"  Unresolved Causal:    {final_assessment.unresolved_causal_count}")
    print(f"  Unresolved Temporal:  {final_assessment.unresolved_temporal_count}")
    print(f"  Production Decisions: {final_assessment.production_decisions_count}")
    print(f"  Missing Invariants:   {final_assessment.missing_invariants}")
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

    # Output trace JSON for independent audit
    trace_data = {
        "story_id": story_id,
        "title": "The Wrong Funeral",
        "genre": "South African Supernatural Comedy / Micro-drama",
        "model_identifier": real_provider.model_name,
        "provider": real_provider.provider_name,
        "forge_kernel_version": "0.2.0",
        "forge_judge_version": "0.2.0",
        "total_cycles": len(all_transitions),
        "final_state_version": final_state.state_version,
        "judge_status": final_assessment.status.value,
        "current_milestone": final_assessment.current_milestone.value if final_assessment.current_milestone else None,
        "satisfied_milestones": [m.value for m in final_assessment.satisfied_milestones],
        "missing_invariants": final_assessment.missing_invariants,
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

    trace_file = os.path.join(os.path.dirname(__file__), "proof_002_comedy_real_llm_trace.json")
    with open(trace_file, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, indent=2)

    print(f"\n[Trace JSON saved to: {trace_file}]")
    return trace_data


if __name__ == "__main__":
    run_proof_002_comedy_real_llm()
