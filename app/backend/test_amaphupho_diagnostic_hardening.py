"""
Welele Story Forge™ — Golden Path Diagnostic Hardening Test Suite
Addresses the four Story Reasoning issues identified in Amaphupho Document Context:
1. Unsupported Invention: Questions must not hallucinate ungrounded events (e.g. packed-club scene, ghost from past, death warrant).
2. Entity / Attribute Drift: Character identities, genders, and pronouns must stay anchored in canonical state (Sizwe is never "she").
3. Story-Version Precedence: Later/stronger story decisions (7-day reveal condition) take precedence over older notes (30-day deadline).
4. Creator Revision Recognition: Major decisions ("He doesn't reveal who he is") trigger material revision recognition and consequence exploration.
"""

import pytest
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    StateStatus,
    KnowledgeStatus,
    ConstraintStatus,
    StoryConstraint
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.collaborative import (
    CollaborativeForgeLoop,
    FactStatus,
    MicroscopeDiagnosticTrace
)
from story_forge.collaborative.mock_director import MockCollaborativeDirector
from story_forge.collaborative.director import CollaborativeStoryDirector


@pytest.fixture
def setup_amaphupho_diagnostic_env():
    """Initializes the Amaphupho story environment in Forge."""
    repo = InMemoryStoryForgeRepository()
    story_id = "story_amaphupho_diag"

    state = repo.create_story(
        story_id=story_id,
        title="Amaphupho (\"Dreams\")",
        owner_id="creator_thabo",
        logline="A brilliant but terrified township producer secretly crafts a viral Amapiano track, only for his estranged partner to steal the credit while his strict father threatens his future."
    )

    # Establish canonical protagonist Sizwe with explicit identity grounding
    state.characters["Sizwe"] = CharacterState(
        character_id="char_sizwe_01",
        name="Sizwe",
        gender="Male",
        pronouns="he/him",
        summary="A gifted 24-year-old Soweto music producer living in dread of his authoritarian father.",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Share his music with the world as Ghost404",
        secret_desire="Earn his father's respect without abandoning Amapiano",
        fatal_flaw="Paralyzing fear of confrontation"
    )
    repo.save_state(state)

    director = MockCollaborativeDirector()
    loop = CollaborativeForgeLoop(repository=repo, director=director)
    return loop, repo, story_id


def test_issue_1_unsupported_invention_prevention(setup_amaphupho_diagnostic_env):
    """
    Issue 1: Unsupported invention.
    Questions must NOT introduce fabricated, ungrounded events or melodrama
    (e.g., packed-club scene, 'ghost from his past', 'death warrant').
    Objective: Context -> Understand -> Identify what is genuinely unresolved -> Ask one useful question.
    """
    loop, repo, story_id = setup_amaphupho_diagnostic_env

    # Pass in the creator's real premise and context
    creator_input = (
        "Mandla has submitted his remix of Ghost404 to the label because his mother is in the ICU. "
        "He knows Sizwe is too terrified of his father to claim the track."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_input
    )

    # 1. Verify question ends with a single '?'
    assert next_q.endswith("?")

    # 2. Verify forbidden fabricated dramatic tropes are completely absent
    hallucinated_tropes = [
        "packed-club",
        "packed club",
        "ghost from his past",
        "death warrant",
        "neon lights",
        "assassination",
        "shootout"
    ]
    for trope in hallucinated_tropes:
        assert trope not in next_q.lower(), f"Question contained unsupported invention '{trope}'"

    # 3. Verify question is tightly grounded in established dilemma (father / Sizwe / Mandla)
    assert "father" in next_q.lower() or "sizwe" in next_q.lower() or "mandla" in next_q.lower()


def test_issue_2_entity_and_attribute_drift_prevention(setup_amaphupho_diagnostic_env):
    """
    Issue 2: Entity/attribute drift.
    Sizwe was mistakenly referred to as 'she'.
    Character identity, gender, and pronouns must remain strictly grounded in canonical context across turns.
    """
    loop, repo, story_id = setup_amaphupho_diagnostic_env
    state_before = repo.get_current_state(story_id)

    # 1. Assert canonical state holds explicit gender and pronouns
    sizwe = state_before.characters["Sizwe"]
    assert sizwe.gender == "Male"
    assert sizwe.pronouns == "he/him"

    # 2. Test user prompt serialization in director
    director = CollaborativeStoryDirector()
    user_prompt = director._build_user_prompt(
        story_state=state_before,
        creator_input="What does Sizwe do next?",
        conversation_history=[],
        story_synopsis=state_before.logline
    )

    # Verify user prompt explicitly informs the reasoning layer of Sizwe's gender and pronouns
    assert "Gender: Male" in user_prompt
    assert "Pronouns: he/him" in user_prompt

    # 3. Run a turn and ensure no feminine pronoun drift occurs in the question or reasoning
    creator_turn = "Sizwe is working late in his bedroom studio when he hears his father returning home."
    trans, state_after, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_turn
    )

    # Assert Sizwe is never referred to as she/her in the generated question
    q_words = [w.strip("?,.!\"'") for w in next_q.lower().split()]
    assert "she" not in q_words, f"Character drift: Sizwe referred to as 'she' in question: {next_q}"
    assert "her" not in q_words, f"Character drift: Sizwe referred to with 'her' in question: {next_q}"


def test_issue_3_story_version_precedence_handling(setup_amaphupho_diagnostic_env):
    """
    Issue 3: Story-version precedence.
    The reasoning layer retrieved the original 30-day deadline after the supplied story had developed a later seven-day reveal condition.
    Investigate how later/stronger story decisions are represented and prioritised.
    """
    loop, repo, story_id = setup_amaphupho_diagnostic_env

    # Document notes contain both preliminary draft note (30-day) and evolved outline (seven-day reveal condition)
    document_context = (
        "[TREATMENT NOTES & DRAFTS]\n"
        "Early Draft Note: The label contract allows 30-day deadline to claim the master recording.\n"
        "Evolved Episode 2 Outline: Radio station sets an urgent seven-day reveal condition for Ghost404 to appear live."
    )

    # Run cycle with both conditions present in context
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=document_context
    )

    # 1. Verify StoryConstraint state representation
    assert len(state.constraints) >= 2

    active_constraints = [c for c in state.constraints if c.status == ConstraintStatus.ACTIVE]
    superseded_constraints = [c for c in state.constraints if c.status == ConstraintStatus.SUPERSEDED]

    assert len(active_constraints) >= 1
    assert len(superseded_constraints) >= 1

    # Active constraint must be the 7-day condition
    active_c = active_constraints[0]
    assert "seven" in active_c.description.lower() or "7-day" in active_c.description.lower()

    # Superseded constraint must be the 30-day deadline
    superseded_c = superseded_constraints[0]
    assert "30" in superseded_c.description

    # 2. Verify next question prioritizes the active 7-day reveal condition, NOT the superseded 30-day deadline
    assert "seven" in next_q.lower() or "7" in next_q.lower()
    assert "30" not in next_q, f"Reasoning retrieved superseded 30-day deadline in question: {next_q}"


def test_issue_4_creator_revision_recognition_material_decision(setup_amaphupho_diagnostic_env):
    """
    Issue 4: Creator revision recognition.
    When the creator responds with a potentially major story decision such as 'He doesn't reveal who he is',
    the system should recognise this as a possible material revision and investigate its consequences
    rather than immediately generating another pre-authored cinematic question.
    """
    loop, repo, story_id = setup_amaphupho_diagnostic_env

    # Turn 1: Establish baseline
    loop.process_cycle(
        story_id=story_id,
        creator_input="Mandla submitted his remix of Ghost404 because he needs money for his mother's surgery."
    )

    # Turn 2: Creator makes a pivotal narrative decision / negative choice
    creator_decision = "He doesn't reveal who he is."

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_decision
    )

    # 1. Verify revision was recognized in trace
    revisions = trace.forge_reconciliation.conflicts_flagged
    assert len(revisions) > 0

    # 2. Verify it is recognized as a material decision, not just ignored
    revision_records = [
        f for f in trace.facts_extracted if f.category in ("EVENT", "STAKES", "FLAW")
    ]
    assert len(revision_records) > 0

    # 3. Verify Forge committed the decision constraint to state
    decision_constraints = [
        c for c in state.constraints if c.category == "DECISION" or "conceal" in c.description.lower()
    ]
    assert len(decision_constraints) > 0
    assert decision_constraints[0].status == ConstraintStatus.ACTIVE

    # 4. Verify question investigates the fallout of this choice rather than leaping to a pre-authored cinematic question
    # The question must explore what happens given that he concealed his identity (e.g., seeing Mandla celebrated, living with the stolen track)
    assert "hidden" in next_q.lower() or "celebrated" in next_q.lower() or "mandla" in next_q.lower()
    assert "packed-club" not in next_q.lower()
    assert "death warrant" not in next_q.lower()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
