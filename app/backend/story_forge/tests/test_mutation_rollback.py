"""
Story Forge Unit Tests: State Mutation Safety & Rollback Invariants
"""

import pytest
from story_forge.models import (
    StoryState,
    StateMutation,
    MutationType,
    CharacterState,
    CharacterRole
)
from story_forge.engine.state_engine import StateEngine, StateMutationError
from story_forge.repository.in_memory_repo import InMemoryStoryForgeRepository
from story_forge.repository.base import ConcurrencyError


def test_valid_mutation_increments_version():
    engine = StateEngine()
    state = StoryState(story_id="story-100", state_version=1)
    state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi", role=CharacterRole.UNRESOLVED)

    mutations = [
        StateMutation(
            target_path="characters.Nkosinathi.core_motivation",
            new_value="Reclaim family honor",
            mutation_type=MutationType.UPDATE
        ),
        StateMutation(
            target_path="characters.Nkosinathi.role",
            new_value="PROTAGONIST",
            mutation_type=MutationType.UPDATE
        )
    ]

    new_state, val_result = engine.apply_mutations(state, mutations, transition_id="trans-1")
    assert new_state.state_version == 2
    assert new_state.previous_state_version == 1
    assert new_state.source_transition_id == "trans-1"
    assert new_state.characters["Nkosinathi"].core_motivation == "Reclaim family honor"
    assert new_state.characters["Nkosinathi"].role == CharacterRole.PROTAGONIST
    assert val_result.is_valid is True

    # Ensure original state was not mutated in place
    assert state.state_version == 1
    assert state.characters["Nkosinathi"].core_motivation is None


def test_invalid_mutation_fails_and_preserves_original():
    engine = StateEngine()
    state = StoryState(story_id="story-100", state_version=1)
    state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi", role=CharacterRole.UNRESOLVED)

    invalid_mutations = [
        StateMutation(
            target_path="characters.Nkosinathi.role",
            new_value="INVALID_ROLE_XYZ",
            mutation_type=MutationType.UPDATE
        )
    ]

    with pytest.raises(StateMutationError) as exc_info:
        engine.apply_mutations(state, invalid_mutations)

    assert "Mutation validation failed" in str(exc_info.value)
    # Original state untouched
    assert state.state_version == 1
    assert state.characters["Nkosinathi"].role == CharacterRole.UNRESOLVED


def test_optimistic_concurrency_rejects_stale_write():
    repo = InMemoryStoryForgeRepository()
    repo.create_story(story_id="story-stale", title="Stale Test", owner_id="user-1")

    # State at version 1
    s1 = repo.get_current_state("story-stale")
    assert s1.state_version == 1

    # Client A advances to version 2
    s2 = StoryState(story_id="story-stale", state_version=2, previous_state_version=1, title="Updated Title")
    repo.save_state(s2)
    assert repo.get_current_state("story-stale").state_version == 2

    # Client B attempts to commit version 2 against previous version 1
    stale_state = StoryState(story_id="story-stale", state_version=2, previous_state_version=1, title="Conflicting Write")
    with pytest.raises(ConcurrencyError) as exc_info:
        repo.save_state(stale_state)

    assert "Stale state write rejected" in str(exc_info.value)
