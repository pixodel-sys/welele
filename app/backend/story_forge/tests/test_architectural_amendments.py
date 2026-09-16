"""
Welele Story Forge™ — Architectural Amendments Regression Test Suite
Validates the minimum architectural corrections exposed by Real LLM Blind Forge 001:
1. Canonical Character Identity vs Role
2. Atomic Multi-Attribute Character Ingestion
3. Unknown ≠ Unresolved Distinction Preservation
4. Non-responsive Creator Disambiguation Handling
"""

import pytest
from story_forge.models.state import StoryState, CharacterState, StateStatus, CharacterRole, CharacterRelationship
from story_forge.models.transition import StateMutation, MutationType, AuthorityMode, SkillEnum
from story_forge.engine.state_engine import StateEngine
from story_forge.engine.dependency_engine import DependencyEngine
from story_forge.validation.validator import StoryValidator
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.adapters import MockReasoningAdapter, LLMReasoningAdapter, MockLLMProvider
from story_forge.models.completion import ReadinessStatus


def test_canonical_character_identity_vs_role_rekeying():
    """
    Test 1: When a mutation is proposed using a generic role alias (e.g. characters.protagonist)
    with a concrete canonical name (e.g. Zodwa Khumalo), the StateEngine must re-key the entity
    to the canonical name and assign the appropriate CharacterRole.
    """
    state = StoryState(story_id="test_story", title="Test Story")
    validator = StoryValidator()
    engine = StateEngine(validator=validator)

    mutation = StateMutation(
        target_path="characters.protagonist",
        mutation_type=MutationType.CREATE,
        new_value={
            "name": "Zodwa Khumalo",
            "role": "PROTAGONIST",
            "status": "FACT"
        },
        rationale="Creator specified protagonist name"
    )

    new_state, val_result = engine.apply_mutations(state, [mutation], "trans_001")
    assert val_result.is_valid
    assert "Zodwa Khumalo" in new_state.characters
    assert "protagonist" not in new_state.characters
    char = new_state.characters["Zodwa Khumalo"]
    assert char.name == "Zodwa Khumalo"
    assert char.role == CharacterRole.PROTAGONIST
    assert char.status == StateStatus.FACT


def test_atomic_multi_attribute_character_ingestion():
    """
    Test 2: Validates that rich composite character payloads (name, role, motivation,
    age, occupation, background lore) are ingested atomically in a single mutation.
    """
    state = StoryState(story_id="test_story", title="Test Story")
    validator = StoryValidator()
    engine = StateEngine(validator=validator)

    mutation = StateMutation(
        target_path="characters.Zodwa",
        mutation_type=MutationType.CREATE,
        new_value={
            "name": "Zodwa Khumalo",
            "role": "PROTAGONIST",
            "core_motivation": "Uncover the truth behind her father's death",
            "secret_desire": "Reclaim ancestral dignity",
            "fatal_flaw": "Obsessive mistrust",
            "status": "FACT",
            "age": 26,
            "occupation": "Investigative Journalist",
            "hometown": "Bergville, KZN"
        },
        rationale="Atomic multi-attribute character ingestion"
    )

    new_state, val_result = engine.apply_mutations(state, [mutation], "trans_002")
    assert val_result.is_valid
    char = new_state.characters["Zodwa Khumalo"]
    assert char.name == "Zodwa Khumalo"
    assert char.role == CharacterRole.PROTAGONIST
    assert char.core_motivation == "Uncover the truth behind her father's death"
    assert char.secret_desire == "Reclaim ancestral dignity"
    assert char.fatal_flaw == "Obsessive mistrust"
    assert char.attributes["age"] == 26
    assert char.attributes["occupation"] == "Investigative Journalist"
    assert char.attributes["hometown"] == "Bergville, KZN"


def test_unknown_vs_unresolved_distinction_preservation():
    """
    Test 3: Validates that deliberately UNKNOWN attributes (StateStatus.UNKNOWN)
    do NOT trigger blocking UNRESOLVED dependencies in the DependencyEngine.
    """
    state = StoryState(story_id="test_story", title="Test Story")
    # Character with deliberate UNKNOWN status
    state.characters["Shadow_Figure"] = CharacterState(
        name="Shadow_Figure",
        role=CharacterRole.ANTAGONIST,
        core_motivation=None,
        status=StateStatus.UNKNOWN
    )
    # Character with UNRESOLVED role/motivation
    state.characters["Bheki"] = CharacterState(
        name="Bheki",
        role=CharacterRole.UNRESOLVED,
        core_motivation=None,
        status=StateStatus.FACT
    )

    dep_engine = DependencyEngine()
    detected = dep_engine.detect(state, "Scanning state")

    dep_keys = [d.dependency_key for d in detected]
    # Bheki is UNRESOLVED -> Must trigger dependency
    assert "CHAR_MOTIVATION_BHEKI" in dep_keys
    # Shadow_Figure is deliberately UNKNOWN -> Must NOT trigger blocking dependency
    assert "CHAR_MOTIVATION_SHADOW_FIGURE" not in dep_keys


def test_non_responsive_creator_response_handling_with_adapter():
    """
    Test 4: Validates that when a creator gives tangential lore instead of resolving
    the active dependency, the adapter properly formats the request and maintains ASK.
    """
    repo = InMemoryStoryForgeRepository()
    mock_provider = MockLLMProvider(provider_name="test_llm", model_name="test-model")
    adapter = LLMReasoningAdapter(provider=mock_provider)
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=adapter)

    story_id = "test_non_responsive_story"
    repo.create_story(story_id=story_id, title="Test Story", owner_id="creator_01", logline="A secret pact.")

    state = repo.get_current_state(story_id)
    state.characters["Zodwa"] = CharacterState(
        name="Zodwa",
        role=CharacterRole.PROTAGONIST,
        core_motivation=None,
        status=StateStatus.FACT
    )
    repo.save_state(state)

    # 1. First cycle: Model asks for motivation
    mock_provider.register_keyed_response("CHAR_MOTIVATION_ZODWA", {
        "action": "ASK",
        "dependency_id": "dep_mot",
        "skill": "EXCAVATOR",
        "question": "Is Zodwa's driving goal to expose the secret or protect her family?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Awaiting creator motivation choice",
        "confidence": 0.95,
        "requires_creator": True,
        "assumptions": [],
        "evidence": []
    })

    t1, s1, q1 = kernel.process_cycle(story_id=story_id, session_id="s1", trace_id="tr1")
    assert t1.authority_mode == AuthorityMode.ASK
    assert q1 == "Is Zodwa's driving goal to expose the secret or protect her family?"

    # 2. Creator answers with tangential lore: "Bheki Ndlovu is the rival clan leader"
    # Model detects that motivation is still unresolved, adapts to new lore, and re-asks
    tangential_response = "Bheki Ndlovu is the rival clan leader."
    mock_provider.register_keyed_response("Bheki Ndlovu is the rival clan leader.", {
        "action": "ASK",
        "dependency_id": "dep_mot",
        "skill": "EXCAVATOR",
        "question": "Given Bheki Ndlovu's presence, does Zodwa seek to expose Bheki or protect her family from him?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Creator supplied rival clan context; clarifying protagonist stance towards Bheki",
        "confidence": 0.95,
        "requires_creator": True,
        "assumptions": ["Bheki Ndlovu is the antagonist."],
        "evidence": ["Creator response"]
    })

    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        session_id="s1",
        trace_id="tr1",
        creator_response=tangential_response
    )
    assert t2.authority_mode == AuthorityMode.ASK
    assert "Given Bheki Ndlovu's presence" in q2
    # Dependency remains open
    deps = repo.get_dependencies(story_id)
    mot_deps = [d for d in deps if "MOTIVATION" in d.dependency_key]
    assert len(mot_deps) > 0
