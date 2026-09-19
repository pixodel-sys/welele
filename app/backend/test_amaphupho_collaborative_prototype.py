"""
Welele Story Forge™ — Gate 2.1 Architectural Prototype Test Suite
Collaborative Story Reasoning Loop with Amaphupho ("Dreams")

Demonstrates:
1. Rich Answer Absorption (extracts 5-10 facts across characters, motives, knowledge, and beats in one turn)
2. Intelligent Next-Question Selection (asks based on dramatic stakes, not database dependencies)
3. Contradiction / Revision Handling (reconciles 'haven't spoken in 5 years' without silent rewriting)
4. The Killer Test (absorbs tangential/multi-aspect answers without saying 'Please answer the question')
5. Dynamic Obstacle Revision (revises primary dramatic conflict from Mandla to Fear of Father)
6. Microscope Diagnostic Trace Inspection (full 8-stage developer microscope view)
"""

import pytest
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    StateStatus,
    KnowledgeStatus,
    Dependency,
    DependencyType,
    DependencyStatus
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.collaborative import (
    CollaborativeForgeLoop,
    FactStatus,
    ExtractedFact,
    MicroscopeDiagnosticTrace
)
from story_forge.collaborative.mock_director import MockCollaborativeDirector


@pytest.fixture
def setup_amaphupho_loop():
    """Initializes the Amaphupho story in Forge repository with baseline state."""
    repo = InMemoryStoryForgeRepository()
    story_id = "story_amaphupho_pilot"
    
    # Inception state: Amaphupho
    state = repo.create_story(
        story_id=story_id,
        title="Amaphupho (\"Dreams\")",
        owner_id="creator_thabo",
        logline="A brilliant but terrified township producer secretly crafts a viral Amapiano track, only for his estranged partner to steal the credit while his strict father threatens his future."
    )
    # Seed baseline protagonist Sizwe
    state.characters["Sizwe"] = CharacterState(
        character_id="char_sizwe_01",
        name="Sizwe",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Share his music with the world as Ghost404",
        secret_desire="Earn his father's respect without abandoning Amapiano",
        fatal_flaw="Paralyzing fear of confrontation"
    )
    repo.save_state(state)
    
    # Initialize some baseline dependencies in graph
    repo.save_dependency(
        Dependency(
            story_id=story_id,
            dependency_key="PREMISE_COUNTERFORCE_DEFINITION",
            dependency_type=DependencyType.CHARACTER,
            status=DependencyStatus.ACTIVE,
            target_entity="Mandla",
            description="Establish the opposing force or rival dynamic."
        )
    )
    
    director = MockCollaborativeDirector()
    loop = CollaborativeForgeLoop(repository=repo, director=director)
    return loop, repo, story_id


def test_1_rich_answer_absorption(setup_amaphupho_loop):
    """
    Test 1: Give the LLM an answer containing 5-10 pieces of story information.
    Verifies it extracts all facts holistically without forcing the creator through individual fields.
    """
    loop, repo, story_id = setup_amaphupho_loop

    creator_rich_input = (
        "Mandla has known Sizwe is Ghost404 since they mixed the original track together. "
        "He's under pressure because of his mother's medical bills, so when the track went viral he saw an opportunity. "
        "He submitted his remix because he thinks Sizwe is too scared of his father to claim the deal."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_rich_input
    )

    # 1. Verify multiple facts extracted across categories (at least 7 facts)
    assert len(trace.facts_extracted) >= 7
    categories = {f.category for f in trace.facts_extracted}
    assert "KNOWLEDGE" in categories
    assert "EVENT" in categories
    assert "MOTIVATION" in categories
    assert "FLAW" in categories
    assert "RELATIONSHIP" in categories

    # 2. Verify all extracted facts have explicit FactStatus (INFERRED / CANONICAL)
    for fact in trace.facts_extracted:
        assert fact.status in (FactStatus.INFERRED, FactStatus.PROPOSED, FactStatus.CREATOR_CONFIRMED)

    # 3. Verify Forge Kernel committed state canonically without data loss
    assert "Mandla" in state.characters
    mandla = state.characters["Mandla"]
    assert mandla.role == CharacterRole.ANTAGONIST
    assert "medical bills" in mandla.core_motivation
    assert len(mandla.relationships) > 0
    assert mandla.relationships[0].target_character == "Sizwe"

    # Verify KnowledgeState was committed
    ghost_know = next((k for k in state.knowledge_states if k.character_name == "Mandla" and "Ghost404" in k.fact_key), None)
    assert ghost_know is not None
    assert ghost_know.status == KnowledgeStatus.KNOWS

    # Verify Sizwe's vulnerability updated
    assert "father" in state.characters["Sizwe"].fatal_flaw.lower()


def test_2_intelligent_next_question_selection(setup_amaphupho_loop):
    """
    Test 2: Ensure the LLM asks the most useful next creative question grounded in dramatic stakes,
    NOT the next unresolved machine dependency.
    """
    loop, repo, story_id = setup_amaphupho_loop

    creator_rich_input = (
        "Mandla has known Sizwe is Ghost404 since they mixed the original track together. "
        "He's under pressure because of his mother's medical bills, so when the track went viral he saw an opportunity. "
        "He submitted his remix because he thinks Sizwe is too scared of his father to claim the deal."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_rich_input
    )

    # 1. Verify next question is natural, focused on character and dilemma
    assert next_q.endswith("?")
    assert "father" in next_q.lower() or "sizwe" in next_q.lower()

    # 2. Verify WHY IT MATTERS TO THE STORY is dramatic, not technical
    assert "Mandla" in trace.why_it_matters_to_the_story or "father" in trace.why_it_matters_to_the_story
    assert "dependency" not in trace.why_it_matters_to_the_story.lower()
    assert "required state" not in trace.why_it_matters_to_the_story.lower()

    # 3. Verify ZERO machine ontology terms leaked into question
    for forbidden in ["counterforce", "dependency", "invariant", "mutation", "canon", "deficiency", "schema"]:
        assert forbidden not in next_q.lower(), f"Question leaked '{forbidden}'"


def test_3_contradiction_and_revision_handling(setup_amaphupho_loop):
    """
    Test 3: Contradiction / Revision
    Initially: Mandla and Sizwe are co-producers.
    Creator: 'Actually, Mandla and Sizwe haven't spoken in five years.'
    LLM must recognise this as revision/contradiction, send it through Forge reconciliation,
    and avoid silently overwriting canon.
    """
    loop, repo, story_id = setup_amaphupho_loop

    # Turn 1: Establish baseline
    loop.process_cycle(
        story_id=story_id,
        creator_input="Mandla is Sizwe's co-producer who mixed the track."
    )

    # Turn 2: Creator contradicts / revises history
    revision_input = "Actually, Mandla and Sizwe haven't spoken in five years."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=revision_input
    )

    # Verify revision was detected and flagged in trace
    assert len(trace.forge_reconciliation.conflicts_flagged) > 0
    assert any("5-year estrangement" in c or "REVISION" in c for c in trace.forge_reconciliation.conflicts_flagged)

    # Verify state was updated accurately
    mandla = state.characters["Mandla"]
    assert any("ESTRANGED" in r.relation_type or "5-year" in (r.dynamic or "") for r in mandla.relationships)

    # Verify next question explores the emotional wound of the revision
    assert "five years" in next_q.lower() or "brotherhood" in next_q.lower() or "broke" in next_q.lower()


def test_4_the_killer_test_tangential_multi_aspect_answer(setup_amaphupho_loop):
    """
    Test 4 (The Killer Test):
    Forge asks: 'What is Sizwe most afraid will happen if his father discovers Ghost404?'
    Creator responds with tangential + multi-aspect information:
    'His father will probably throw him out of the house. And Mandla already knows he's Ghost404 because they made the track together. Actually, Mandla has submitted his own version to the label.'
    
    Expected:
    - LLM does NOT say 'Please answer the question'.
    - Absorbs the father threat (eviction).
    - Absorbs Mandla's insider knowledge.
    - Absorbs Mandla's remix submission to the label.
    - Continues conversation intelligently around the urgent ticking clock.
    """
    loop, repo, story_id = setup_amaphupho_loop

    tangential_input = (
        "His father will probably throw him out of the house. "
        "And Mandla already knows he's Ghost404 because they made the track together. "
        "Actually, Mandla has submitted his own version to the label."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=tangential_input,
        conversation_history=[
            {"speaker": "StoryForge", "text": "What is Sizwe most afraid will happen if his father discovers Ghost404?"}
        ]
    )

    # 1. Did NOT reject or prompt "Please answer the question"
    assert "please answer" not in next_q.lower()
    assert "did not answer" not in next_q.lower()

    # 2. Extracted both the direct answer (stakes: throw him out) and collateral facts (Mandla knows, Mandla submitted)
    extracted_statements = [f.statement.lower() for f in trace.facts_extracted]
    assert any("throw" in s or "house" in s or "father" in s for s in extracted_statements)
    assert any("ghost404" in s and "knows" in s for s in extracted_statements)
    assert any("submitted" in s and "label" in s for s in extracted_statements)

    # 3. Canonical state holds all three updates
    assert "Mandla" in state.characters
    assert any(k.character_name == "Mandla" and "Ghost404" in k.fact_key for k in state.knowledge_states)
    assert "homelessness" in state.characters["Sizwe"].fatal_flaw.lower() or "father" in state.characters["Sizwe"].fatal_flaw.lower()

    # 4. Next question responds to the urgent ticking clock of the label submission
    assert "label" in next_q.lower() or "fear" in next_q.lower() or "push" in next_q.lower()


def test_5_dynamic_obstacle_revision(setup_amaphupho_loop):
    """
    Test 5: Creator revises the dramatic core:
    'Sizwe's real obstacle isn't Mandla. It's his fear of disappointing his father.'
    System revises understanding of dramatic conflict accordingly.
    """
    loop, repo, story_id = setup_amaphupho_loop

    pivot_input = "Sizwe's real obstacle isn't Mandla. It's his fear of disappointing his father."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=pivot_input
    )

    # Verify obstacle revision recorded
    obstacle_facts = [f for f in trace.facts_extracted if f.category == "OBSTACLE"]
    assert len(obstacle_facts) > 0
    assert "disappointing his father" in obstacle_facts[0].statement.lower()

    # Verify state reflects father's emotional shadow as core flaw
    assert "father" in state.characters["Sizwe"].fatal_flaw.lower()

    # Verify next question explores father's expectations
    assert "father" in next_q.lower()
    assert "?" in next_q


def test_6_microscope_diagnostic_trace_structure(setup_amaphupho_loop):
    """
    Test 6: Validates the 8-stage Microscope Diagnostic Trace format for developer visibility.
    """
    loop, repo, story_id = setup_amaphupho_loop

    creator_input = (
        "Mandla has known Sizwe is Ghost404 since they mixed the original track together. "
        "He's under pressure because of his mother's medical bills, so when the track went viral he saw an opportunity."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=creator_input
    )

    # Render formatted ASCII trace
    ascii_view = trace.format_microscope_view()
    print("\n" + ascii_view)

    # Assert all 8 required sections are present
    assert "1. CREATOR INPUT:" in ascii_view
    assert "2. LLM UNDERSTANDING:" in ascii_view
    assert "3. FACTS EXTRACTED:" in ascii_view
    assert "4. FACTS PROPOSED (MUTATIONS):" in ascii_view
    assert "5. FORGE RECONCILIATION:" in ascii_view
    assert "6. CANONICAL STATE SUMMARY:" in ascii_view
    assert "7. WHAT REMAINS UNCLEAR:" in ascii_view
    assert "8. WHY IT MATTERS TO THE STORY:" in ascii_view
    assert "9. NEXT CONVERSATIONAL MOVE:" in ascii_view


def test_7_adversarial_dramatic_role_inference_mandla_not_premature_antagonist(setup_amaphupho_loop):
    """
    Adversarial Test: Dramatic Role Separation vs Premature Antagonist Canonization
    
    Given: Mandla takes an obstructive action (submitting remix) driven by love/desperation for his dying mother.
    
    Guarantees:
    1. Action, Motivation, Relationship, and Dramatic Role are extracted as SEPARATE distinct facts.
    2. Obstructive action and situational opposition are recognized without prematurely canonizing 'Mandla = ANTAGONIST'.
    3. Dramatic role classification is treated as PROPOSED (not CANONICAL FACT).
    4. Canonical StoryState maintains Mandla's role as UNRESOLVED (or non-villain) pending creator dramatic choice.
    5. Next question explores the dramatic/moral framing with the creator.
    """
    loop, repo, story_id = setup_amaphupho_loop

    adversarial_input = (
        "Mandla submitted his remix because his mother is in the ICU and needs R80,000 for surgery. "
        "He hates doing this to Sizwe, but he believes Sizwe will never go public anyway because of his father."
    )

    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=adversarial_input
    )

    # 1. Verify clean separation of distinct facts
    categories = [f.category for f in trace.facts_extracted]
    assert "EVENT" in categories, "Action (remix submission) must be extracted as EVENT"
    assert "MOTIVATION" in categories, "Mother's ICU surgery must be extracted as MOTIVATION"
    assert "RELATIONSHIP" in categories, "Conflicted brother dynamic must be extracted as RELATIONSHIP"
    assert "OBSTACLE" in categories, "Situational obstruction must be extracted as OBSTACLE"
    assert "CHARACTER" in categories, "Dramatic role must be extracted as CHARACTER"

    # 2. Verify Dramatic Role is PROPOSED, NOT silently canonized as absolute FACT
    role_facts = [f for f in trace.facts_extracted if f.category == "CHARACTER" and f.target_entity == "Mandla"]
    assert len(role_facts) > 0
    assert role_facts[0].status == FactStatus.PROPOSED, "Dramatic role interpretation must be PROPOSED, awaiting creator choice"

    # 3. Verify Forge Canonical State did NOT prematurely lock Mandla as ANTAGONIST
    mandla = state.characters["Mandla"]
    assert mandla is not None
    assert mandla.role != CharacterRole.ANTAGONIST, "Obstructive action must NOT automatically canonize ANTAGONIST"
    assert mandla.role == CharacterRole.UNRESOLVED
    assert "R80,000" in mandla.core_motivation or "surgery" in mandla.core_motivation.lower()
    assert any("CONFLICTED" in r.relation_type or "BROTHER" in r.relation_type for r in mandla.relationships)

    # 4. Verify Next Question invites creator to define the dramatic framing
    assert "traitor" in next_q.lower() or "brother" in next_q.lower() or "desperate" in next_q.lower()
    assert "?" in next_q
    for forbidden in ["counterforce", "dependency", "invariant", "mutation", "deficiency", "schema"]:
        assert forbidden not in next_q.lower()
