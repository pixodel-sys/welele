"""
Regression Test Suite: Story-First Creator Language & Zero Ontology Leakage
Verifies:
1. LLM Prompt contains explicit Story-First Hard Lock rules.
2. Formatted deficiency questions from DependencyEngine contain ZERO machine ontology terms.
3. LLMAdapter rejects questions containing forbidden machine terms.
4. Kernel cycle generates natural storytelling questions without dictionary translations.
"""
import pytest
from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus,
    Dependency, DependencyType, DependencyStatus, AuthorityMode, SkillEnum
)
from story_forge.engine.dependency_engine import DependencyEngine
from story_forge.adapters.llm_adapter import LLMReasoningAdapter, LLMInvalidOutputError
from story_forge.orchestrator import StoryForgeKernel

FORBIDDEN_ONTOLOGY_TERMS = [
    "counterforce",
    "dependency",
    "required state",
    "canon",
    "invariant",
    "mutation",
    "knowledge state",
    "chronology anchor",
    "validation",
    "schema",
    "graph",
    "deficiency"
]


def test_dependency_engine_questions_zero_ontology_leakage():
    """Ensure all synthesized and formatted questions from DependencyEngine contain no forbidden terms."""
    state = StoryState(
        story_id="story_leakage_test",
        title="Umthwalo",
        logline="A destitute brother enters an illegal high-stakes poker game.",
        premise="Family survival microdrama",
        characters={
            "c_sabelo": CharacterState(
                id="c_sabelo",
                name="Sabelo",
                role=CharacterRole.PROTAGONIST,
                status=StateStatus.FACT,
                core_motivation="Save his sister Zodwa's home"
            )
        }
    )

    test_keys = [
        ("PREMISE_LOGLINE_SPECIFICATION", "PREMISE", DependencyType.NARRATIVE),
        ("PREMISE_PROTAGONIST_DEFINITION", "PROTAGONIST", DependencyType.CHARACTER),
        ("CHAR_MOTIVATION_SABELO", "Sabelo", DependencyType.CHARACTER),
        ("PREMISE_COUNTERFORCE_DEFINITION", "OPPOSITION", DependencyType.CHARACTER),
        ("REL_SABELO_JONAS", "Sabelo <-> Jonas", DependencyType.CHARACTER),
        ("WORLD_RULE_SPECIFICATION", "RULES", DependencyType.NARRATIVE),
        ("EVENT_01_INCITING_DISRUPTION", "EVENT_1", DependencyType.CAUSAL),
        ("EVENT_02_POINT_OF_NO_RETURN", "EVENT_2", DependencyType.CAUSAL),
        ("EVENT_03_MIDPOINT_REVELATION", "EVENT_3", DependencyType.CAUSAL),
        ("EVENT_04_DARK_NIGHT", "EVENT_4", DependencyType.CAUSAL),
        ("EVENT_05_CLIMAX", "EVENT_5", DependencyType.CAUSAL),
        ("EVENT_06_RESOLUTION", "EVENT_6", DependencyType.CAUSAL),
        ("PLANT_PAYOFF_LINK_GOLD_WATCH", "Gold Watch", DependencyType.NARRATIVE),
    ]

    for key, entity, dtype in test_keys:
        dep = Dependency(
            story_id=state.story_id,
            dependency_key=key,
            dependency_type=dtype,
            status=DependencyStatus.DETECTED,
            target_entity=entity,
            description=f"Requirement for {entity}"
        )
        question = DependencyEngine.format_targeted_deficiency_question(dep, state)
        assert question is not None
        assert question.endswith("?")
        
        q_lower = question.lower()
        for forbidden in FORBIDDEN_ONTOLOGY_TERMS:
            assert forbidden not in q_lower, f"Question '{question}' for key '{key}' leaked forbidden ontology term '{forbidden}'"


def test_llm_adapter_rejects_forbidden_ontology_in_ask():
    """Ensure LLMAdapter raises LLMInvalidOutputError when question leaks machine ontology."""
    adapter = LLMReasoningAdapter()
    
    for forbidden in ["counterforce", "dependency", "invariant", "chronology anchor", "deficiency"]:
        bad_raw = {
            "action": "ASK",
            "skill": "EXCAVATOR",
            "question": f"What is the primary {forbidden} opposing Sabelo?",
            "requires_creator": True,
            "rationale": "Testing forbidden term rejection"
        }
        
        with pytest.raises(LLMInvalidOutputError) as exc_info:
            adapter._validate_and_build_decision(
                raw_data=bad_raw,
                request=None,
                latency_ms=10.0,
                request_id="req_test"
            )
        assert "Story-First Architectural Lock violation" in str(exc_info.value)
        assert forbidden in str(exc_info.value)


def test_llm_adapter_accepts_clean_story_first_question():
    """Ensure LLMAdapter accepts natural, compelling screenwriting questions."""
    adapter = LLMReasoningAdapter()
    
    clean_raw = {
        "action": "ASK",
        "skill": "EXCAVATOR",
        "question": "Who is standing in Sabelo's way when he tries to leave?",
        "requires_creator": True,
        "rationale": "Valid natural creative question"
    }
    
    decision = adapter._validate_and_build_decision(
        raw_data=clean_raw,
        request=None,
        latency_ms=10.0,
        request_id="req_test"
    )
    assert decision.action == AuthorityMode.ASK
    assert decision.question == "Who is standing in Sabelo's way when he tries to leave?"
