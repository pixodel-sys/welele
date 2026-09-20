"""
Welele Story Forge™ — Semantic Adversarial Test Suite: Conversational Action Authority
Tests the six core adversarial cases:
1. Explicit ending: “Roll credits. Dark screen. The end.” -> CONCLUDE_STORY, next_question = null.
2. Story dialogue: “Stop. This is the end,” she said. -> not CONCLUDE_STORY.
3. Narrative decision: “Sizwe doesn't reveal himself.” -> SYNTHESIZE_AND_CONTINUE, no forced question.
4. Genuine unresolved dilemma: “He wants the deal, but he can't bring himself to tell his father.” -> ASK_QUESTION with grounded dilemma inquiry.
5. Meta-therapeutic trap: “How do you feel about what Sizwe said?” -> rejected / grounded in dramatic stakes, not therapy interview.
6. Ending + unresolved Forge state: End conversation on incomplete story -> conversation = CLOSED, forge_state = NOT_READY.
7. Resilience against coincidental keywords ('stop', 'end', 'kill', 'leave') in normal creator answers.
"""

import pytest
from uuid import uuid4

from story_forge.models import (
    StoryState,
    CharacterRole,
    CharacterState,
    StateStatus,
    AuthorityMode,
    MilestoneEnum,
    ReadinessStatus,
    Dependency,
    DependencyType,
    DependencyStatus
)
from story_forge.collaborative.director import CollaborativeStoryDirector, LLMInvalidOutputError
from story_forge.collaborative.mock_director import MockCollaborativeDirector
from story_forge.collaborative.loop import CollaborativeForgeLoop
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.engine import StateEngine, DependencyEngine, ConsequencePropagator
from story_forge.validation import StoryValidator
from story_forge.orchestrator import ForgeJudge
from story_forge.api.routes import submit_session_input, SubmitInputRequest, get_current_action


@pytest.fixture
def test_context():
    repo = InMemoryStoryForgeRepository()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    dep_engine = DependencyEngine()
    propagator = ConsequencePropagator()
    director = MockCollaborativeDirector()
    judge = ForgeJudge(repository=repo)
    loop = CollaborativeForgeLoop(
        repository=repo,
        director=director,
        state_engine=state_engine,
        dependency_engine=dep_engine,
        propagator=propagator,
        validator=validator
    )

    story_id = f"story_{uuid4().hex[:8]}"
    initial_state = StoryState(
        story_id=story_id,
        title="Amaphupho",
        logline="A talented young producer from Soweto produces a viral amapiano hit under the alias Ghost404.",
        characters={
            "Sizwe": CharacterState(
                character_id="char_sizwe",
                name="Sizwe",
                role=CharacterRole.PROTAGONIST,
                gender="Male",
                pronouns="he/him",
                status=StateStatus.FACT
            )
        },
        state_version=1
    )
    repo.save_state(initial_state)

    # Seed an unresolved dependency to verify Forge truth retention
    dep = Dependency(
        id=f"dep_{uuid4().hex[:6]}",
        story_id=story_id,
        dependency_key="counterforce_resolution",
        dependency_type=DependencyType.CHARACTER,
        target_entity="Mandla",
        description="Mandla's opposition and moral dynamic must be resolved in canon.",
        status=DependencyStatus.ACTIVE,
        priority_score=0.9
    )
    repo.save_dependency(dep)

    # Create session
    session = repo.create_session(story_id=story_id, creator_id="creator_semantic")

    return {
        "repo": repo,
        "loop": loop,
        "judge": judge,
        "story_id": story_id,
        "session_id": session["id"]
    }


def test_1_explicit_ending(test_context):
    """
    1. Explicit ending
    “Roll credits. Dark screen. The end.”
    Expected:
    conversational_action = CONCLUDE_STORY
    next_question = null
    No further question manufactured.
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    input_text = "Roll credits. Dark screen. The end."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    # 1. Verify semantic action in reasoning output / trace
    assert trace.next_conversational_move is None
    assert next_q is None

    # 2. Verify authority mode is STOP
    assert trans.authority_mode == AuthorityMode.STOP
    assert trans.question_asked is None

    # 3. Verify state records explicit ending
    assert state.explicit_ending_declared is True


def test_2_story_dialogue_not_conclude(test_context):
    """
    2. Story dialogue
    “Stop. This is the end,” she said.
    Expected:
    not CONCLUDE_STORY
    Conversation continues; dialogue attribution prevents false positive stop.
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    input_text = '“Stop. This is the end,” she said.'
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    # 1. Must NOT be CONCLUDE_STORY / STOP
    assert trans.authority_mode != AuthorityMode.STOP
    assert state.explicit_ending_declared is False

    # 2. Must generate an in-world dramatic question about the scene
    assert next_q is not None
    assert "?" in next_q
    assert "ultimatum" in next_q.lower() or "sizwe" in next_q.lower() or "finality" in next_q.lower()


def test_3_narrative_decision_synthesize_and_continue(test_context):
    """
    3. Narrative decision
    “Sizwe doesn't reveal himself.”
    Expected:
    SYNTHESIZE_AND_CONTINUE
    No forced question (next_question = null).
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    input_text = "Sizwe doesn't reveal himself."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    # 1. Verify no question is forced
    assert next_q is None
    assert trans.question_asked is None

    # 2. Authority mode is PROPOSE (synthesize & wait for next beat, not ASK, not STOP)
    assert trans.authority_mode == AuthorityMode.PROPOSE

    # 3. Decision constraint is committed to canonical state
    assert any(c.category == "DECISION" for c in state.constraints)


def test_4_genuine_unresolved_dilemma(test_context):
    """
    4. Genuine unresolved dilemma
    “He wants the deal, but he can't bring himself to tell his father.”
    Expected:
    ASK_QUESTION with a question grounded in that dilemma.
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    input_text = "He wants the deal, but he can't bring himself to tell his father."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    # 1. Verify authority mode is ASK
    assert trans.authority_mode == AuthorityMode.ASK
    assert next_q is not None

    # 2. Question must be grounded in the dilemma (father, contract/deal, secret/hiding)
    q_lower = next_q.lower()
    assert "father" in q_lower
    assert ("contract" in q_lower or "deal" in q_lower or "hide" in q_lower or "secret" in q_lower)


def test_5_meta_therapeutic_trap_prevention(test_context):
    """
    5. Meta-therapeutic trap
    “How do you feel about what Sizwe said?”
    Expected:
    The system should not respond by turning the creator into the subject of therapy/talk-show questioning.
    Verify question addresses dramatic story craft, NOT creator feelings.
    Also verify CollaborativeStoryDirector actively rejects therapeutic questions with LLMInvalidOutputError.
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    # Test 5a: Submitting the meta-therapeutic prompt to MockCollaborativeDirector
    input_text = "How do you feel about what Sizwe said?"
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    assert next_q is not None
    q_lower = next_q.lower()

    # System must NOT ask how the creator feels
    for forbidden in CollaborativeStoryDirector.FORBIDDEN_THERAPEUTIC_PATTERNS:
        assert forbidden not in q_lower, f"Meta-therapeutic trap triggered: '{forbidden}' in question: {next_q}"

    # Must be grounded in story mechanics / character reaction
    assert "mandla" in q_lower or "narrative" in q_lower or "words" in q_lower

    # Test 5b: Direct unit test on CollaborativeStoryDirector validator rejecting meta-therapy
    director = CollaborativeStoryDirector()
    with pytest.raises(LLMInvalidOutputError) as exc_info:
        director._validate_and_build_output(
            raw_data={
                "llm_understanding": "Understanding",
                "extracted_facts": [],
                "proposed_mutations": [],
                "revisions_detected": [],
                "what_remains_unclear": "Nothing",
                "why_it_matters_to_the_story": "Drama",
                "conversational_action": "ASK_QUESTION",
                "is_story_concluded": False,
                "next_conversational_move": "As the writer, how did you feel when Sizwe betrayed his father?"
            },
            creator_input=input_text
        )
    assert "Meta-Therapeutic Trap violation" in str(exc_info.value)


def test_6_ending_with_unresolved_forge_state(test_context):
    """
    6. Ending + unresolved Forge state
    End the conversation while the story is deliberately incomplete.
    Expected:
    conversation = CLOSED (session completed, current action STOP, next question null)
    forge_state = NOT_READY (readiness assessment is NOT_READY, missing invariants, unresolved dependencies remain)
    Crucial Architectural Invariant:
    Forge preserves truth without forcing the conversation to continue merely because dependencies remain open.
    """
    ctx = test_context
    repo = ctx["repo"]
    judge = ctx["judge"]
    loop = ctx["loop"]
    story_id = ctx["story_id"]
    session_id = ctx["session_id"]

    # Ensure story is deliberately incomplete prior to ending (missing premise lock)
    curr_state = repo.get_current_state(story_id)
    curr_state.logline = ""
    repo.save_state(curr_state)

    # Submit explicit ending through the full route handler
    req = SubmitInputRequest(
        creator_input="Roll credits. Dark screen. The end."
    )
    cycle_resp = submit_session_input(
        session_id=session_id,
        req=req,
        repo=repo,
        collab_loop=loop
    )

    # 1. Verify Conversation is CLOSED
    assert cycle_resp.action == AuthorityMode.STOP
    assert cycle_resp.active_question is None

    session = repo.get_session(session_id)
    assert session["session_status"] == "COMPLETED"
    assert session["current_action"] == "STOP"
    assert session["current_question"] is None

    # Current action endpoint also reflects closed conversation
    curr = get_current_action(session_id=session_id, repo=repo)
    assert curr.action == AuthorityMode.STOP
    assert curr.question is None
    assert curr.requires_creator is False

    # 2. Verify Forge state is NOT_READY
    assessment = judge.assess(story_id)
    assert assessment.status == ReadinessStatus.NOT_READY
    assert assessment.status != ReadinessStatus.FORGE_COMPLETE
    assert MilestoneEnum.M3_FORGE_COMPLETE not in assessment.satisfied_milestones
    assert len(assessment.missing_invariants) > 0

    # Unresolved dependencies still exist and are preserved truthfully
    deps = repo.get_dependencies(story_id)
    unresolved_deps = [d for d in deps if d.status == DependencyStatus.ACTIVE]
    assert len(unresolved_deps) >= 1
    assert unresolved_deps[0].dependency_key == "counterforce_resolution"

    # Forge truthfully reports NOT_READY, but does NOT override creator boundary or manufacture questions
    assert cycle_resp.unresolved_dependencies_count >= 1


def test_7_coincidental_keywords_do_not_conclude(test_context):
    """
    7. Resilience against coincidental keywords.
    Normal creator sentences with words like 'stop', 'end', 'kill', 'leave'
    must not accidentally trigger an ending.
    """
    ctx = test_context
    loop = ctx["loop"]
    story_id = ctx["story_id"]

    input_text = "Sizwe decides to stop producing for Mandla and leave Soweto to end this dispute."
    trans, state, trace, next_q = loop.process_cycle(
        story_id=story_id,
        creator_input=input_text
    )

    assert trans.authority_mode != AuthorityMode.STOP
    assert state.explicit_ending_declared is False
