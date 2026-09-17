"""
Welele Story Forge™ — Context Contamination Canary Regression Test
Invariant: A sterile story must never acquire narrative concepts that exist only
in another fixture, specimen, or example.
Canary Specimen: 'The Durban Crumb'
"""

import pytest
import re
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    StateStatus,
    DependencyType,
    SkillEnum
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.engine import DependencyEngine, StateEngine, ConsequencePropagator
from story_forge.validation import StoryValidator
from story_forge.orchestrator.kernel import StoryForgeKernel
from story_forge.orchestrator.judge import ForgeJudge
from story_forge.adapters import LLMReasoningAdapter, MockReasoningAdapter
from story_forge.adapters.providers.mock_provider import MockLLMProvider

CONTAMINATION_CANARY_KEYWORDS = [
    "ancestral",
    "debt",
    "clan",
    "creditor",
    "father's death",
    "supernatural",
    "nkosinathi",
    "tebogo",
    "zodwa",
    "isibusiso"
]


def assert_sterile_from_contamination(content: str, context_label: str):
    """Asserts that no specimen-specific contamination keywords are present in the text."""
    for kw in CONTAMINATION_CANARY_KEYWORDS:
        assert not re.search(r'\b' + re.escape(kw) + r'\b', content, re.IGNORECASE), (
            f"Contamination violation in {context_label}: Found foreign specimen keyword '{kw}' in text:\n'{content}'"
        )


def test_durban_crumb_contamination_canary_regression():
    """
    Canary Regression:
    Execute 'The Durban Crumb' (a sterile pastry-baking drama) through the Forge pipeline (M0 -> M1 -> M2).
    Verify that zero foreign specimen concepts are injected into dependencies, context, or prompts,
    and verify that the first M2 anchor question relates purely to dramatic structure
    (what event disrupts Lerato's status quo and establishes the stakes) without knowing or prescribing the answer.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_durban_crumb_canary_001"
    session_id = "sess_crumb_canary_001"
    trace_id = "trc_crumb_canary_001"

    # M0: Raw Story State
    logline = (
        "A determined pastry chef enters a televised coastal baking championship to keep "
        "her late grandmother's bakery from being repossessed by a corporate hotel developer."
    )
    state = repo.create_story(
        story_id=story_id,
        title="The Durban Crumb",
        owner_id="creator_lerato",
        logline=logline
    )

    # M1: Established Characters & Polar Dynamics
    state.characters["char_lerato"] = CharacterState(
        name="Lerato Khanyile",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Win the Durban Pastry Grand Prix to clear the commercial lease on her late grandmother's bakery.",
        secret_desire="Prove that traditional township pastry recipes deserve Michelin-grade global recognition.",
        fatal_flaw="Refuses corporate business partnerships out of fierce artistic independence."
    )
    state.characters["char_vance"] = CharacterState(
        name="Marcus Vance",
        role=CharacterRole.ANTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Acquire the Durban beachfront strip to develop an ultra-luxury boutique hotel.",
        secret_desire="Erase all modest local establishments to maximize coastal property prestige.",
        fatal_flaw="Arrogantly dismisses grassroots community solidarity."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = LLMReasoningAdapter(provider=MockLLMProvider())

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        validator=validator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # 1. Verify Pairwise Role Priority (generic polarity, no Nkosinathi/Tebogo hardcoding)
    detected_deps = dep_engine.detect(state=state, interpretation="", events=[])
    rel_dep = next((d for d in detected_deps if d.dependency_key.startswith("REL_")), None)
    assert rel_dep is not None
    # Protagonist vs Antagonist dynamic must have high priority leverage
    assert rel_dep.components.leverage == 8
    assert rel_dep.components.urgency == 8
    assert_sterile_from_contamination(rel_dep.description, "Pairwise Relationship Dependency")

    for d in detected_deps:
        repo.save_dependency(d)

    # 2. Advance to M2: Evaluate Required State Deficiencies (Six Chronology Anchors)
    all_deps = repo.get_dependencies(story_id)
    deficient_deps = dep_engine.evaluate_required_state_deficiencies(
        state=state,
        events=[],
        existing_dependencies=all_deps
    )

    for d in deficient_deps:
        repo.save_dependency(d)
        # Check every deficiency description for foreign specimen concepts
        assert_sterile_from_contamination(d.description, f"Deficiency '{d.dependency_key}'")

    # 3. Verify Structural M2 Chronology Anchors
    anchor_1 = next((d for d in deficient_deps if d.dependency_key == "EVENT_01_INCITING_DISRUPTION"), None)
    assert anchor_1 is not None
    assert anchor_1.dependency_type == DependencyType.CAUSAL
    assert anchor_1.suggested_skill == SkillEnum.CHALLENGER.value
    # Must be purely structural, never assuming father's death or ancestral debt
    assert "Core event that disrupts the protagonist's status quo and establishes narrative stakes." in anchor_1.description
    assert "ancestral" not in anchor_1.description.lower()
    assert "debt" not in anchor_1.description.lower()
    assert "father" not in anchor_1.description.lower()

    # 4. Context Assembly & Prompt Construction
    all_deps_after = repo.get_dependencies(story_id)
    active_dep = dep_engine.prioritise(all_deps_after)
    assert active_dep is not None

    reasoning_req = kernel._assemble_reasoning_request(
        state=state,
        active_dep=active_dep,
        events=[],
        creator_input="Advance story development.",
        creator_response=None
    )
    assert_sterile_from_contamination(str(reasoning_req.dict()), "ReasoningRequest Context")

    # Build prompt immediately before transmission
    system_prompt = adapter._build_system_prompt()
    user_prompt = adapter._build_user_prompt(reasoning_req)
    assert_sterile_from_contamination(system_prompt, "System Prompt")
    assert_sterile_from_contamination(user_prompt, "User Prompt")

    # Verify generic example formatting in prompt
    assert "characters.CharacterName" in user_prompt
    assert "Zodwa" not in user_prompt
    assert "Khumalo" not in user_prompt

    # 5. Execute Cycle — Model should address the dramatic function without hardcoded bias
    decision = adapter.reason(reasoning_req)
    assert_sterile_from_contamination(str(decision.dict()), "ReasoningDecision")
