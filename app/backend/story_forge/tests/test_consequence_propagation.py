"""
Story Forge Unit Tests: Consequence Propagation
Answers: "What else must now be true?"
"""

import pytest
from story_forge.models import (
    StoryState,
    StateMutation,
    MutationType,
    CharacterState,
    ChronologyEvent
)
from story_forge.engine.propagator import ConsequencePropagator


def test_consequence_propagation_for_character_motivation():
    propagator = ConsequencePropagator()
    state = StoryState(story_id="story-prop")
    state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi")

    mutations = [
        StateMutation(
            target_path="characters.Nkosinathi.core_motivation",
            new_value="Avenge the betrayal",
            mutation_type=MutationType.UPDATE
        )
    ]

    consequences = propagator.propagate(state, mutations)
    assert len(consequences) == 1
    assert consequences[0].impacted_entity == "Nkosinathi"
    assert "forces relational tension" in consequences[0].description
    assert consequences[0].new_dependency_detected == "TENSION_SURROUNDING_NKOSINATHI"


def test_consequence_propagation_for_chronology_event():
    propagator = ConsequencePropagator()
    state = StoryState(story_id="story-prop")
    state.characters["Thabo"] = CharacterState(name="Thabo")
    state.characters["Tebogo"] = CharacterState(name="Tebogo")

    mutations = [
        StateMutation(
            target_path="events.add",
            new_value={
                "headline": "Secret Engagement in Maboneng",
                "participants": ["Thabo", "Tebogo"]
            },
            mutation_type=MutationType.CREATE
        )
    ]

    consequences = propagator.propagate(state, mutations)
    assert len(consequences) == 2
    witnesses = [c.impacted_entity for c in consequences]
    assert "Thabo" in witnesses
    assert "Tebogo" in witnesses
    assert consequences[0].derived_mutation is not None
    assert consequences[0].derived_mutation.target_path.startswith("knowledge.")
