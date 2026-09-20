"""
Regression Test: Dependency Reconciliation & Active Pointer Advancement
Guarantees:
1. When a creator response results in an INFER decision resolving PREMISE_PROTAGONIST_DEFINITION,
   the Kernel automatically advances active_dependency_id to the next highest-priority OPEN deficiency.
2. A resolved dependency is NEVER persisted or returned as an active dependency.
3. If an action is INFER or resolves a dependency, the Kernel produces a targeted question for the next open dependency.
"""

import pytest
from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus,
    Dependency, DependencyType, DependencyStatus, AuthorityMode, SkillEnum
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel
from story_forge.adapters import (
    ReasoningAdapter, ReasoningRequest, ReasoningDecision
)
from story_forge.models.transition import StateMutation, MutationType


class MockInferProtagonistAdapter(ReasoningAdapter):
    """Mocks an adapter that returns INFER to resolve protagonist definition on creator response."""
    def reason(self, request: ReasoningRequest) -> ReasoningDecision:
        if request.creator_response and "Sabelo" in request.creator_response:
            return ReasoningDecision(
                action=AuthorityMode.INFER,
                skill=SkillEnum.EXCAVATOR,
                rationale="Inferred Sabelo as protagonist with core motivation from creator narrative.",
                confidence=0.95,
                requires_creator=False,
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Sabelo",
                        mutation_type=MutationType.CREATE,
                        new_value={
                            "character_id": "char_sabelo_001",
                            "name": "Sabelo",
                            "role": CharacterRole.PROTAGONIST.value,
                            "status": StateStatus.FACT.value,
                            "core_motivation": "Protect family and escape poverty",
                            "fatal_flaw": "Greed under pressure"
                        },
                        rationale="Creator defined Sabelo as central protagonist."
                    )
                ]
            )
        # Default first question
        return ReasoningDecision(
            action=AuthorityMode.ASK,
            skill=SkillEnum.EXCAVATOR,
            question="What does Sabelo really want, and what is at stake for him?",
            rationale="Need to define protagonist motivation.",
            confidence=0.9,
            requires_creator=True
        )


def test_infer_advances_active_dependency_and_never_persists_resolved():
    repo = InMemoryStoryForgeRepository()
    state = repo.create_story(
        story_id="test_sabelo_advancement",
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Sabelo is a security guard who steals R2 million from drug dealer Jonas's car boot."
    )
    session = repo.create_session("test_sabelo_advancement", "creator_zola", "sess_adv_01")
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=MockInferProtagonistAdapter())

    # Cycle 1: Generate initial question
    trans1, s1, q1 = kernel.process_cycle("test_sabelo_advancement", session_id="sess_adv_01")
    assert trans1.authority_mode == AuthorityMode.ASK
    assert q1 == "What does Sabelo really want, and what is at stake for him?"
    initial_dep = repo.get_dependency_by_key("test_sabelo_advancement", "PREMISE_PROTAGONIST_DEFINITION")
    assert initial_dep is not None
    assert initial_dep.status == DependencyStatus.ACTIVE

    # Cycle 2: Creator supplies Sabelo motivation (invokes reasoning adapter when extractor has no static role keywords)
    creator_text = "Sabelo is driven by ambition to escape poverty and become wealthy. He risks getting shot by Jonas."
    trans2, s2, q2 = kernel.process_cycle(
        "test_sabelo_advancement",
        session_id="sess_adv_01",
        creator_response=creator_text
    )

    # Assert Protagonist is now canonically committed in StoryState
    assert "Sabelo" in s2.characters
    assert s2.characters["Sabelo"].role == CharacterRole.PROTAGONIST

    # Assert PREMISE_PROTAGONIST_DEFINITION is RESOLVED
    resolved_dep = repo.get_dependency_by_key("test_sabelo_advancement", "PREMISE_PROTAGONIST_DEFINITION")
    assert resolved_dep.status == DependencyStatus.RESOLVED

    # Assert transition active_dependency_id is ADVANCED to the NEXT open deficiency
    assert trans2.active_dependency_id != resolved_dep.id
    all_deps = repo.get_dependencies("test_sabelo_advancement")
    next_dep = next((d for d in all_deps if d.id == trans2.active_dependency_id), None)
    assert next_dep is not None
    assert next_dep.status == DependencyStatus.ACTIVE
    assert next_dep.dependency_key != "PREMISE_PROTAGONIST_DEFINITION"

    # Assert a targeted question for the new dependency is generated
    assert q2 is not None
    assert len(q2.strip()) > 0
    assert trans2.authority_mode == AuthorityMode.INFER
    assert "standing" in q2.lower() or "who" in q2.lower()


def test_api_current_action_never_returns_resolved_dependency():
    """Guarantees that GET /sessions/{id}/current always returns an open dependency and never a resolved one."""
    from story_forge.api.routes import get_current_action
    from story_forge.models import DependencyStatus
    
    repo = InMemoryStoryForgeRepository()
    state = repo.create_story(
        story_id="test_api_current_advancement",
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Sabelo is a security guard who steals R2 million from drug dealer Jonas's car boot."
    )
    session = repo.create_session("test_api_current_advancement", "creator_zola", "sess_api_01")
    kernel = StoryForgeKernel(repository=repo, reasoning_adapter=MockInferProtagonistAdapter())

    # Initial cycle
    trans1, s1, q1 = kernel.process_cycle("test_api_current_advancement", session_id="sess_api_01")
    repo.update_session("sess_api_01", {
        "current_action": trans1.authority_mode.value,
        "current_question": q1,
        "active_dependency_id": trans1.active_dependency_id
    })

    # Force the active dependency to RESOLVED in repo while keeping its ID in session to simulate stale session pointer
    dep_to_resolve = repo.get_dependency_by_key("test_api_current_advancement", "PREMISE_PROTAGONIST_DEFINITION")
    dep_to_resolve.status = DependencyStatus.RESOLVED
    repo.save_dependency(dep_to_resolve)

    # Call get_current_action
    action_resp = get_current_action("sess_api_01", repo=repo)
    
    # Assert active dependency returned is NOT the resolved one
    assert action_resp.active_dependency_key != "PREMISE_PROTAGONIST_DEFINITION"
    assert action_resp.question is not None
    assert len(action_resp.question.strip()) > 0
