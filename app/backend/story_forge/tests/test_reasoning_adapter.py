"""
Story Forge Unit Tests: Reasoning Adapter Contract & Decision Governance
Verifies the boundary: 'The Adapter reasons. The Kernel governs.'
"""

import pytest
from pydantic import ValidationError
from story_forge.models import (
    SkillEnum,
    AuthorityMode,
    StateMutation,
    MutationType,
    CharacterRole,
    StateStatus,
    ProductionDecision,
    ProductionAspect,
    StoryState,
    CharacterState
)
from story_forge.adapters import (
    ReasoningRequest,
    ReasoningDecision,
    StoryContext,
    DependencyContext,
    EntityContext,
    MockReasoningAdapter,
    ForgeObjective
)
from story_forge.orchestrator.kernel import StoryForgeKernel, DecisionValidationError
from story_forge.repository import InMemoryStoryForgeRepository


def test_valid_reasoning_request_and_decision():
    req = ReasoningRequest(
        story_id="story-1",
        state_version=1,
        story_context=StoryContext(story_id="story-1", title="Test Story"),
        active_dependency=DependencyContext(
            id="dep-1",
            dependency_key="CHAR_MOTIVATION_NKOSINATHI",
            dependency_type="CHARACTER",
            target_entity="Nkosinathi",
            description="Nkosinathi core motivation unresolved.",
            status="DETECTED",
            priority_score=28.0,
            suggested_skill="EXCAVATOR"
        ),
        objective=ForgeObjective.RESOLVE_DEPENDENCY
    )

    adapter = MockReasoningAdapter()
    decision = adapter.reason(req)

    assert decision.action == AuthorityMode.ASK
    assert decision.skill == SkillEnum.EXCAVATOR
    assert decision.question is not None
    assert decision.requires_creator is True
    assert decision.confidence == 0.98
    assert len(decision.assumptions) >= 1
    assert len(decision.evidence) >= 1


def test_action_semantics_ask_requires_question():
    with pytest.raises(ValidationError) as exc_info:
        ReasoningDecision(
            action=AuthorityMode.ASK,
            skill=SkillEnum.EXCAVATOR,
            question=None,  # Invalid: ASK requires question
            rationale="Testing missing question on ASK",
            requires_creator=True
        )
    assert "When action is ASK, exactly one non-empty primary question must be formulated" in str(exc_info.value)


def test_action_semantics_infer_rejects_question():
    with pytest.raises(ValidationError) as exc_info:
        ReasoningDecision(
            action=AuthorityMode.INFER,
            skill=SkillEnum.CONNECTOR,
            question="What is the relationship?",  # Invalid: INFER must not ask creator
            rationale="Testing question on INFER",
            requires_creator=False
        )
    assert "When action is INFER, question must be None" in str(exc_info.value)


def test_action_semantics_production_decision_payload_required():
    with pytest.raises(ValidationError) as exc_info:
        ReasoningDecision(
            action=AuthorityMode.RECORD_PRODUCTION_DECISION,
            skill=SkillEnum.FORGER,
            production_decision=None,  # Invalid: missing payload
            rationale="Testing missing production decision"
        )
    assert "production_decision payload is required" in str(exc_info.value)


def test_kernel_decision_governance_rejects_invalid_mutations():
    repo = InMemoryStoryForgeRepository()
    repo.create_story(story_id="story-gov", title="Governance Test", owner_id="user-1")

    # Custom adapter attempting to propose an invalid character role
    class RogueAdapter:
        def reason(self, request: ReasoningRequest) -> ReasoningDecision:
            return ReasoningDecision(
                action=AuthorityMode.INFER,
                skill=SkillEnum.EXCAVATOR,
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Nkosinathi.role",
                        new_value="INVALID_SUPERHERO_ROLE",
                        mutation_type=MutationType.UPDATE
                    )
                ],
                rationale="Rogue invalid proposal",
                confidence=0.99
            )

    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=RogueAdapter())

    with pytest.raises(DecisionValidationError) as exc_info:
        kernel.process_cycle(
            story_id="story-gov",
            session_id="session-1",
            trace_id="trace-1"
        )

    assert "Proposed mutation violates domain invariants" in str(exc_info.value)


def test_transition_provenance_captures_observability():
    repo = InMemoryStoryForgeRepository()
    repo.create_story(story_id="story-obs", title="Observability Test", owner_id="user-1")

    initial_state = repo.get_current_state("story-obs")
    initial_state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi", role=CharacterRole.UNRESOLVED)
    repo.save_state(initial_state)

    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=MockReasoningAdapter())

    transition, new_state, q = kernel.process_cycle(
        story_id="story-obs",
        session_id="session-obs",
        trace_id="trace-obs",
        creator_input="Nkosinathi arrives."
    )

    # Verify provenance metadata
    prov = transition.provenance
    assert prov.adapter_name == "MockReasoningAdapter"
    assert prov.adapter_version == "0.1.0"
    assert prov.confidence > 0.0
    assert prov.latency_ms is not None
    assert isinstance(prov.assumptions, list)
    assert isinstance(prov.evidence, list)
