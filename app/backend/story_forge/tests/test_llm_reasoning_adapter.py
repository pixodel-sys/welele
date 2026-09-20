"""
Welele Story Forge™ — LLM Reasoning Adapter Contract Tests v0.1
Comprehensive contract tests verifying the intelligence boundary:
'The LLM proposes. The Forge Kernel governs.'
"""

import pytest
from typing import Dict, Any

from story_forge.adapters import (
    LLMReasoningAdapter,
    MockLLMProvider,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMInvalidOutputError,
    ReasoningRequest,
    ReasoningDecision,
    StoryContext,
    DependencyContext,
    EntityContext,
    EventContext,
    ForgeObjective
)
from story_forge.models import (
    AuthorityMode,
    SkillEnum,
    MutationType,
    ProductionAspect,
    CharacterRole
)
from story_forge.orchestrator import StoryForgeKernel
from story_forge.repository.in_memory_repo import InMemoryStoryForgeRepository
from story_forge.models.state import StoryState, CharacterState


@pytest.fixture
def base_request() -> ReasoningRequest:
    return ReasoningRequest(
        story_id="story_llm_test",
        state_version=1,
        story_context=StoryContext(
            story_id="story_llm_test",
            title="Inhliziyo Ayiphakelwa",
            logline="A high-society romance unravels amid hidden motives.",
            theme="Love vs Duty",
            tone="Dramatic Romance"
        ),
        active_dependency=DependencyContext(
            id="dep_001",
            dependency_key="CHAR_MOTIVATION_NKOSINATHI",
            dependency_type="CHARACTER_MOTIVATION",
            target_entity="Nkosinathi",
            description="Nkosinathi's immediate driving goal is unresolved.",
            status="UNRESOLVED",
            priority_score=13.0,
            suggested_skill="EXCAVATOR"
        ),
        relevant_entities=[
            EntityContext(
                name="Nkosinathi",
                role="ANTAGONIST",
                status="ACTIVE",
                core_motivation=None,
                fatal_flaw="Jealousy"
            )
        ],
        relevant_events=[
            EventContext(
                event_sequence=1,
                story_time="Day 1 - Evening",
                headline="Engagement Announcement",
                description="Thabo and Tebogo announce their engagement.",
                participants=["Thabo", "Tebogo", "Nkosinathi"]
            )
        ],
        objective=ForgeObjective.RESOLVE_DEPENDENCY
    )


def test_valid_ask_decision(base_request):
    """Test 1: Valid ASK with exactly one question and requires_creator=True."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "ASK",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": "What is the specific root of Nkosinathi's resentment toward Thabo?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Creator ownership strictly required for primary antagonist motivation.",
        "confidence": 0.95,
        "requires_creator": True,
        "assumptions": ["Nkosinathi was present during the announcement."],
        "evidence": ["Event #1: Engagement Announcement"]
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    decision = adapter.reason(base_request)

    assert decision.action == AuthorityMode.ASK
    assert decision.skill == SkillEnum.EXCAVATOR
    assert decision.question == "What is the specific root of Nkosinathi's resentment toward Thabo?"
    assert decision.requires_creator is True
    assert len(decision.proposed_mutations) == 0
    assert decision.adapter_name == "LLMReasoningAdapter"
    assert decision.adapter_version == "0.1.0"


def test_ask_with_multiple_questions_rejected(base_request):
    """Test 2: ASK containing multiple questions must be rejected with LLMInvalidOutputError."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "ASK",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": "Why is Nkosinathi jealous? And what is his financial background?",
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Multiple questions formulated.",
        "confidence": 0.90,
        "requires_creator": True,
        "assumptions": [],
        "evidence": []
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMInvalidOutputError) as exc:
        adapter.reason(base_request)

    assert "ASK action must contain exactly one question" in str(exc.value)


def test_ask_with_committed_mutations_rejected(base_request):
    """Test 3: ASK attempting to commit state mutations before creator input must be rejected."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "ASK",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": "What drives Nkosinathi?",
        "proposal": None,
        "proposed_mutations": [
            {
                "target_path": "characters.Nkosinathi.core_motivation",
                "mutation_type": "UPDATE",
                "new_value": "Wants revenge",
                "rationale": "Premature mutation"
            }
        ],
        "production_decision": None,
        "rationale": "Invalid combination",
        "confidence": 0.85,
        "requires_creator": True,
        "assumptions": [],
        "evidence": []
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMInvalidOutputError) as exc:
        adapter.reason(base_request)

    assert "ASK action cannot commit or propose state mutations" in str(exc.value)


def test_valid_infer_decision(base_request):
    """Test 4: Valid INFER with proposed mutations, no creator question, and requires_creator=False."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "INFER",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": None,
        "proposal": "Infer Nkosinathi antagonist role based on confrontation evidence",
        "proposed_mutations": [
            {
                "target_path": "characters.Nkosinathi.role",
                "mutation_type": "UPDATE",
                "new_value": "ANTAGONIST",
                "rationale": "Inferred from engagement confrontation"
            }
        ],
        "production_decision": None,
        "rationale": "Clear evidence in chronology allows safe deduction.",
        "confidence": 0.88,
        "requires_creator": False,
        "assumptions": ["Nkosinathi's hostility is active."],
        "evidence": ["Event #1"]
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    decision = adapter.reason(base_request)

    assert decision.action == AuthorityMode.INFER
    assert decision.question is None
    assert decision.requires_creator is False
    assert len(decision.proposed_mutations) == 1
    assert decision.proposed_mutations[0].target_path == "characters.Nkosinathi.role"
    assert decision.proposed_mutations[0].new_value == "ANTAGONIST"


def test_infer_with_creator_question_rejected(base_request):
    """Test 5: INFER with a creator question must be rejected."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "INFER",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": "Should we infer this?",
        "proposal": "Proposed inference",
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Attempting to ask question under INFER action.",
        "confidence": 0.80,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMInvalidOutputError) as exc:
        adapter.reason(base_request)

    assert "When action is INFER, question must be None" in str(exc.value)


def test_valid_propose_decision(base_request):
    """Test 6: Valid PROPOSE requiring creator sign-off."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "PROPOSE",
        "dependency_id": "dep_001",
        "skill": "CONNECTOR",
        "question": None,
        "proposal": "Nkosinathi was formerly engaged to Tebogo two years prior.",
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Backstory proposal for creator approval.",
        "confidence": 0.82,
        "requires_creator": True,
        "assumptions": ["Enhances dramatic tension."],
        "evidence": ["Logline: hidden motives"]
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    decision = adapter.reason(base_request)

    assert decision.action == AuthorityMode.PROPOSE
    assert decision.skill == SkillEnum.CONNECTOR
    assert decision.requires_creator is True
    assert decision.proposal == "Nkosinathi was formerly engaged to Tebogo two years prior."


def test_valid_record_production_decision(base_request):
    """Test 7: Valid RECORD_PRODUCTION_DECISION with aspect and constraint flag."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "RECORD_PRODUCTION_DECISION",
        "dependency_id": "dep_001",
        "skill": "ORCHESTRATOR",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": {
            "aspect": "LOCATION",
            "decision": "Confrontation must be shot in a secluded urban venue.",
            "rationale": "Deferred to pre-production location scouting."
        },
        "rationale": "Production decision recorded for physical pre-production.",
        "confidence": 0.95,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    decision = adapter.reason(base_request)

    assert decision.action == AuthorityMode.RECORD_PRODUCTION_DECISION
    assert decision.production_decision is not None
    assert decision.production_decision.production_aspect == ProductionAspect.LOCATION
    assert decision.production_decision.narrative_resolution == "Confrontation must be shot in a secluded urban venue."


def test_invalid_json_raises_controlled_error(base_request):
    """Test 8: Malformed JSON from provider raises LLMInvalidOutputError."""
    mock_provider = MockLLMProvider()
    mock_provider.force_raw_malformed_json = "{ action: 'ASK', question: "

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMInvalidOutputError) as exc:
        adapter.reason(base_request)

    assert "Malformed JSON returned by provider" in str(exc.value)


def test_unknown_action_raises_controlled_error(base_request):
    """Test 9: Non-existent action mode raises LLMInvalidOutputError."""
    mock_provider = MockLLMProvider()
    mock_provider.enqueue_response({
        "action": "AUTO_FIX_CANON",
        "dependency_id": "dep_001",
        "skill": "EXCAVATOR",
        "question": None,
        "proposal": None,
        "proposed_mutations": [],
        "production_decision": None,
        "rationale": "Invented illegal action",
        "confidence": 1.0,
        "requires_creator": False,
        "assumptions": [],
        "evidence": []
    })

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMInvalidOutputError) as exc:
        adapter.reason(base_request)

    assert "Unknown or invalid action" in str(exc.value)


def test_provider_timeout_handling(base_request):
    """Test 10: Provider timeout propagates as LLMTimeoutError."""
    mock_provider = MockLLMProvider()
    mock_provider.force_timeout = True

    adapter = LLMReasoningAdapter(provider=mock_provider, timeout_seconds=5.0)
    with pytest.raises(LLMTimeoutError) as exc:
        adapter.reason(base_request)

    assert exc.value.retryable is True
    assert "timeout" in str(exc.value).lower()


def test_provider_rate_limit_handling(base_request):
    """Test 11: Provider rate limit propagates as LLMRateLimitError."""
    mock_provider = MockLLMProvider()
    mock_provider.force_rate_limit = True

    adapter = LLMReasoningAdapter(provider=mock_provider)
    with pytest.raises(LLMRateLimitError) as exc:
        adapter.reason(base_request)

    assert exc.value.retryable is True
    assert "rate limit" in str(exc.value).lower()


def test_prompt_context_isolation(base_request):
    """Test 12: Prompt construction includes only deliberate Kernel context slices."""
    mock_provider = MockLLMProvider()
    adapter = LLMReasoningAdapter(provider=mock_provider)

    # Trigger reasoning
    adapter.reason(base_request)

    assert len(mock_provider.calls_history) == 1
    call = mock_provider.calls_history[0]
    user_prompt = call["user_prompt"]

    assert "Inhliziyo Ayiphakelwa" in user_prompt
    assert "CHAR_MOTIVATION_NKOSINATHI" in user_prompt
    assert "Nkosinathi" in user_prompt
    assert "Engagement Announcement" in user_prompt
    # Must NOT contain random undeclared variables
    assert "SECRET_DATABASE_PASSWORD" not in user_prompt
