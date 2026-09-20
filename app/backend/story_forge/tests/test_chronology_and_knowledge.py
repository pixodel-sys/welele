"""
Story Forge Unit Tests: Chronology Events and Knowledge State Integrity
"""

import pytest
from story_forge.models import (
    StoryState,
    CharacterState,
    ChronologyEvent,
    KnowledgeState,
    KnowledgeStatus,
    StateStatus
)
from story_forge.validation import StoryValidator


def test_chronology_event_creation_and_sequence():
    ev1 = ChronologyEvent(
        story_id="story-chrono",
        event_sequence=1,
        headline="Secret Engagement",
        description="Thabo proposes to Tebogo in Maboneng.",
        participants=["Thabo", "Tebogo"],
        event_status=StateStatus.FACT
    )
    assert ev1.event_sequence == 1
    assert "Thabo" in ev1.participants
    assert ev1.event_status == StateStatus.FACT


def test_knowledge_state_character_validation():
    validator = StoryValidator()
    state = StoryState(story_id="story-k")
    state.characters["Nkosinathi"] = CharacterState(name="Nkosinathi")

    # Valid knowledge state
    state.knowledge_states.append(
        KnowledgeState(
            character_name="Nkosinathi",
            fact_key="ENGAGEMENT_FACT",
            status=KnowledgeStatus.KNOWS
        )
    )
    res_valid = validator.validate_state(state)
    assert res_valid.is_valid is True

    # Invalid knowledge state (pointing to character not present in state)
    state.knowledge_states.append(
        KnowledgeState(
            character_name="NonExistentGhostCharacter",
            fact_key="SOME_SECRET",
            status=KnowledgeStatus.KNOWS
        )
    )
    res_invalid = validator.validate_state(state)
    assert res_invalid.is_valid is False
    assert any(e.source_rule == "RULE_KNOWLEDGE_CHARACTER_EXISTS" for e in res_invalid.errors)
