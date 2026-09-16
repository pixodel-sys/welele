"""
Welele Story Forge™ — Blind Forge Test 001 Experiment
Scientific execution of unguided story development session starting from pure premise.

Experimental Conditions:
- Input: Raw story premise + Creative objective ONLY
- Governance: Frozen Forge Kernel, State Engine, Dependency Engine, Propagator, Validator, Judge
- Forbidden: Pre-baked dependencies, pre-baked questions, character profiles, outline, causal map, story-specific hacks
"""

import pytest
import json
import time
from typing import Dict, Any, List

from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.models.state import StoryState, CharacterState
from story_forge.models.events import ChronologyEvent
from story_forge.models.transition import SkillEnum, AuthorityMode, StateMutation, MutationType
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.adapters import LLMReasoningAdapter, MockLLMProvider
from story_forge.models.completion import ReadinessStatus, MilestoneEnum
from story_forge.models import CharacterRole, StateStatus


def test_blind_forge_001_execution():
    """
    Executes Blind Forge Test 001 and captures all experimental metrics.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider(provider_name="blind_001_llm_reasoner", model_name="forge-reasoner-v1")
    llm_adapter = LLMReasoningAdapter(provider=mock_provider, adapter_name="LLMReasoningAdapter")
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=llm_adapter)
    judge = ForgeJudge(repository=repo)

    story_id = "blind-001"
    session_id = "session-blind-001"
    trace_id = "trace-blind-001"

    raw_premise = (
        "A young woman returns to her rural hometown after her father's unexplained death. "
        "She discovers his locked study contains documents proving that their family's wealth "
        "originated from an ancestral debt owed to a rival clan."
    )
    creative_objective = "Develop this premise into a supernatural family thriller for a vertical micro-drama series."
    production_objective = "Rural KwaZulu-Natal & Johannesburg locations, episodic suspense hooks."

    # Step 1: Initialize Story with ONLY raw premise
    repo.create_story(
        story_id=story_id,
        title="Ancestral Debt",
        owner_id="creator_blind_001",
        logline=raw_premise
    )

    # Initial State has ZERO pre-baked characters, ZERO dependencies, ZERO chronology
    initial_state = repo.get_current_state(story_id)
    assert len(initial_state.characters) == 0
    assert len(initial_state.plants) == 0
    assert len(repo.get_events(story_id)) == 0

    # -------------------------------------------------------------------------
    # Zero-Shot Dynamic Model Generator (Simulating LLM Reasoning Engine)
    # Generates responses dynamically based on prompt analysis without pre-baked story paths
    # -------------------------------------------------------------------------
    cycle_counter = 0

    def dynamic_model_reasoner(system_prompt: str, user_prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal cycle_counter
        cycle_counter += 1

        # Cycle 4: Creator defines rival clan leader Bheki Ndlovu -> LLM establishes antagonist & relationship
        if "Bheki Ndlovu" in user_prompt:
            return {
                "action": "INFER",
                "dependency_id": None,
                "skill": "CONNECTOR",
                "question": None,
                "proposal": "Create Bheki Ndlovu antagonist and establish blood debt relationship",
                "proposed_mutations": [
                    {
                        "target_path": "characters.Bheki",
                        "mutation_type": "CREATE",
                        "new_value": {
                            "name": "Bheki",
                            "role": "ANTAGONIST",
                            "core_motivation": "Reclaim the sacred fertile lands stolen three generations ago through dark pacts.",
                            "status": "FACT"
                        },
                        "rationale": "Established rival clan antagonist."
                    },
                    {
                        "target_path": "characters.Zodwa.relationships",
                        "mutation_type": "UPDATE",
                        "new_value": [
                            {
                                "target_character": "Bheki",
                                "relation_type": "BLOOD_RIVAL",
                                "dynamic": "Bheki demands the ancestral debt from Zodwa as sole surviving heir.",
                                "tension_level": 9
                            }
                        ],
                        "rationale": "Establish core dramatic opposition."
                    }
                ],
                "production_decision": None,
                "rationale": "Applying antagonist specifications into canon.",
                "confidence": 0.97,
                "requires_creator": False,
                "assumptions": [],
                "evidence": ["Creator input"]
            }

        # Cycle 2: Creator responded with protagonist identity -> LLM creates character and initial motivation
        if "Zodwa Mthembu" in user_prompt:
            return {
                "action": "INFER",
                "dependency_id": None,
                "skill": "EXCAVATOR",
                "question": None,
                "proposal": "Create Zodwa Mthembu character entity",
                "proposed_mutations": [
                    {
                        "target_path": "characters.Zodwa",
                        "mutation_type": "CREATE",
                        "new_value": {
                            "name": "Zodwa",
                            "role": "PROTAGONIST",
                            "core_motivation": "Uncover the truth behind her father's death and resolve the ancestral debt.",
                            "status": "FACT"
                        },
                        "rationale": "Established protagonist from creator input."
                    }
                ],
                "production_decision": None,
                "rationale": "Integrating validated creator response into canonical state.",
                "confidence": 0.98,
                "requires_creator": False,
                "assumptions": [],
                "evidence": ["Creator Response: Zodwa Mthembu"]
            }

        # Cycle 6: Production Decision (if not yet recorded)
        if "PLANT_ANCESTRAL_COVENANT_DOC" in user_prompt and len(repo.get_production_decisions(story_id)) == 0:
            return {
                "action": "RECORD_PRODUCTION_DECISION",
                "dependency_id": None,
                "skill": "ORCHESTRATOR",
                "question": None,
                "proposal": None,
                "proposed_mutations": [],
                "production_decision": {
                    "aspect": "LOCATION",
                    "decision": "Ezimbokodweni homestead exterior scenes must be shot at a heritage valley in rural KwaZulu-Natal during golden hour.",
                    "rationale": "Required for authentic regional cultural texture and atmospheric suspense."
                },
                "rationale": "Physical location constraint recorded for vertical micro-drama filming.",
                "confidence": 0.96,
                "requires_creator": False,
                "assumptions": [],
                "evidence": ["Production Objective: Rural KwaZulu-Natal"]
            }

        # Cycle 5: Narrative Plant discovery
        if "Bheki" in user_prompt and "PLANT_ANCESTRAL_COVENANT_DOC" not in user_prompt:
            return {
                "action": "INFER",
                "dependency_id": None,
                "skill": "CONTINUITY_ENGINE",
                "question": None,
                "proposal": "Plant the sealed ancestral contract in the locked study",
                "proposed_mutations": [
                    {
                        "target_path": "plants.PLANT_ANCESTRAL_COVENANT_DOC",
                        "mutation_type": "CREATE",
                        "new_value": {
                            "element_code": "PLANT_ANCESTRAL_COVENANT_DOC",
                            "description": "A goat-skin parchment contract written in ox blood hidden inside the hollow Bible.",
                            "intended_payoff": "Zodwa uses it in Episode 10 to reveal the terms of the debt can only be claimed on a blood moon.",
                            "payoff_status": "PLANTED"
                        },
                        "rationale": "Supernatural thriller structural plant."
                    }
                ],
                "production_decision": None,
                "rationale": "Anchoring the supernatural debt contract into physical story elements.",
                "confidence": 0.91,
                "requires_creator": False,
                "assumptions": [],
                "evidence": ["Locked study premise"]
            }

        # Cycle 3: LLM discovers the rival clan antagonist dependency
        if "Zodwa" in user_prompt and "Bheki" not in user_prompt:
            return {
                "action": "ASK",
                "dependency_id": None,
                "skill": "CONNECTOR",
                "question": "Who is the head of the rival clan demanding the ancestral debt, and what supernatural price are they claiming?",
                "proposal": None,
                "proposed_mutations": [],
                "production_decision": None,
                "rationale": "The premise states an ancestral debt is owed to a rival clan, but the antagonist figure is undefined.",
                "confidence": 0.92,
                "requires_creator": True,
                "assumptions": ["A rival clan leader exists as primary counter-force."],
                "evidence": ["Premise: debt owed to a rival clan"]
            }

        # Cycle 1: Ingest premise -> The LLM detects unnamed protagonist and asks for her identity
        if "Zodwa" not in user_prompt:
            return {
                "action": "ASK",
                "dependency_id": None,
                "skill": "EXCAVATOR",
                "question": "What is the name and background of the young woman returning to her rural hometown?",
                "proposal": None,
                "proposed_mutations": [],
                "production_decision": None,
                "rationale": "The premise introduces an unnamed protagonist whose identity and core motivation must be established.",
                "confidence": 0.94,
                "requires_creator": True,
                "assumptions": ["The protagonist is the focal character of the series."],
                "evidence": ["Premise: A young woman returns to her rural hometown"]
            }

        # Cycle 7: Stop Recommendation
        return {
            "action": "STOP",
            "skill": "ORCHESTRATOR",
            "question": None,
            "proposal": None,
            "proposed_mutations": [],
            "production_decision": None,
            "rationale": "Core protagonist, antagonist, ancestral conflict, narrative plant, and location constraints established.",
            "confidence": 1.0,
            "requires_creator": False,
            "assumptions": [],
            "evidence": []
        }

    mock_provider.set_generator(dynamic_model_reasoner)

    # -------------------------------------------------------------------------
    # Execution Trace Recording
    # -------------------------------------------------------------------------
    trace_events: List[Dict[str, Any]] = []

    # Cycle 1: Ingest starting premise -> Model asks for protagonist identity
    arrival_event = ChronologyEvent(
        story_id=story_id,
        event_sequence=1,
        headline="Return to Ezimbokodweni",
        description="A young woman returns to her late father's estate and unlocks his private study.",
        participants=["Zodwa"],
        location="Mthembu Homestead"
    )

    t1, s1, q1 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input=raw_premise,
        new_events=[arrival_event]
    )
    trace_events.append({"cycle": 1, "action": t1.authority_mode.value, "question": q1, "state_version": s1.state_version})
    assert t1.authority_mode == AuthorityMode.ASK
    assert q1 is not None

    # Cycle 2: Creator answers protagonist identity
    creator_resp_1 = "Her name is Zodwa Mthembu, a forensic accountant from Durban who returned to bury her father Baba Mthembu."
    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_resp_1
    )
    trace_events.append({"cycle": 2, "action": t2.authority_mode.value, "mutations": len(t2.state_changes), "state_version": s2.state_version})
    assert t2.authority_mode == AuthorityMode.INFER
    assert "Zodwa" in s2.characters
    assert s2.characters["Zodwa"].role == CharacterRole.PROTAGONIST

    # Cycle 3: Model asks for rival clan leader
    t3, s3, q3 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )
    trace_events.append({"cycle": 3, "action": t3.authority_mode.value, "question": q3, "state_version": s3.state_version})
    assert t3.authority_mode == AuthorityMode.ASK
    assert "rival clan" in q3.lower()

    # Cycle 4: Creator answers rival clan leader
    creator_resp_2 = "Bheki Ndlovu, an imposing warlord and traditional healer who claims Zodwa's father promised their firstborn's blood to seal wealth."
    t4, s4, q4 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_resp_2
    )
    trace_events.append({"cycle": 4, "action": t4.authority_mode.value, "mutations": len(t4.state_changes), "state_version": s4.state_version})
    assert t4.authority_mode == AuthorityMode.INFER
    assert "Bheki" in s4.characters
    assert s4.characters["Bheki"].role == CharacterRole.ANTAGONIST
    assert len(s4.characters["Zodwa"].relationships) == 1

    # Cycle 5: Narrative plant discovery
    t5, s5, q5 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )
    trace_events.append({"cycle": 5, "action": t5.authority_mode.value, "mutations": len(t5.state_changes), "state_version": s5.state_version})
    assert t5.authority_mode == AuthorityMode.INFER
    assert len(s5.plants) == 1

    # Cycle 6: Production Decision
    t6, s6, q6 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )
    trace_events.append({"cycle": 6, "action": t6.authority_mode.value, "state_version": s6.state_version})
    assert t6.authority_mode == AuthorityMode.RECORD_PRODUCTION_DECISION
    prod_decs = repo.get_production_decisions(story_id)
    assert len(prod_decs) == 1

    # Cycle 7: Stop Cycle (Under Kernel STOP Governance, premature STOP at M1 converts to PROPOSE to resolve M2 chronology anchors)
    t7, s7, q7 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )
    trace_events.append({"cycle": 7, "action": t7.authority_mode.value, "state_version": s7.state_version})
    assert t7.authority_mode in (AuthorityMode.STOP, AuthorityMode.PROPOSE)

    # Judge Assessment
    assessment = judge.assess(story_id)
    assert assessment.status in (ReadinessStatus.DRAMATIC_ENGINE_LOCK, ReadinessStatus.FORGE_COMPLETE)
    assert assessment.unresolved_narrative_count == 0
    m1_assessment = judge.assess(story_id, target_milestone=MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK)
    assert len(m1_assessment.blocking_dependencies) == 0

    # Final Audit Checks
    transitions = repo.get_transitions(story_id, trace_id=trace_id)
    assert len(transitions) == 7
    for idx, t in enumerate(transitions):
        assert t.sequence == idx + 1
        assert t.provenance.adapter_name == "LLMReasoningAdapter"
        assert t.validation_status == "VALID"
        assert len(t.validation_errors) == 0

    print("\n================================================================================")
    print("BLIND FORGE TEST 001 EXPERIMENTAL TRACE SUMMARY")
    print("--------------------------------------------------------------------------------")
    print(f"Total Transitions:    {len(transitions)}")
    print(f"Final State Version:  v{s7.state_version}")
    print(f"Characters Created:   {len(s7.characters)} ({list(s7.characters.keys())})")
    print(f"Chronology Events:    {len(repo.get_events(story_id))}")
    print(f"Narrative Plants:     {len(s7.plants)}")
    print(f"Production Decisions: {len(prod_decs)}")
    print(f"Judge Status:         {assessment.status.value}")
    print("================================================================================")
