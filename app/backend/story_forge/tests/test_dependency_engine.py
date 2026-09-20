"""
Story Forge Unit Tests: Dependency Detection and Skill Selection
"""

import pytest
from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    CharacterRelationship,
    StateStatus,
    DependencyType,
    DependencyStatus,
    SkillEnum
)
from story_forge.engine.dependency_engine import DependencyEngine


def test_dependency_detection_unresolved_character():
    engine = DependencyEngine()
    state = StoryState(story_id="story-1", title="Test Story")
    state.characters["Nkosinathi"] = CharacterState(
        name="Nkosinathi",
        role=CharacterRole.UNRESOLVED,
        core_motivation=None
    )

    detected = engine.detect(state, "Nkosinathi arrives at the scene.")
    assert len(detected) >= 1
    dep = detected[0]
    assert dep.dependency_key == "CHAR_MOTIVATION_NKOSINATHI"
    assert dep.dependency_type == DependencyType.CHARACTER
    assert dep.suggested_skill == SkillEnum.EXCAVATOR.value


def test_prioritisation_picks_highest_score():
    engine = DependencyEngine()
    state = StoryState(story_id="story-1")
    state.characters["Nkosinathi"] = CharacterState(
        name="Nkosinathi",
        role=CharacterRole.UNRESOLVED
    )
    state.characters["Tebogo"] = CharacterState(
        name="Tebogo",
        role=CharacterRole.CONFIDANT,
        relationships=[
            CharacterRelationship(target_character="Thabo", relation_type="FIANCE", status=StateStatus.UNRESOLVED)
        ]
    )

    detected = engine.detect(state, "")
    top = engine.prioritise(detected)
    assert top is not None
    assert top.status == DependencyStatus.ACTIVE
    assert top.priority_score > 0
