"""
Welele Story Forge™ — State & Mutation Validator
Enforces narrative coherence without destructive silent repairs.
"""

from typing import List, Optional
from ..models import StoryState, StateMutation, StateStatus, CharacterRole, KnowledgeStatus
from .rules import ValidationResult, ValidationError


class StoryValidator:
    """
    Validates candidate mutations and comprehensive StoryState integrity.
    """

    def validate_mutation(self, current_state: StoryState, mutation: StateMutation) -> ValidationResult:
        result = ValidationResult()
        path = mutation.target_path

        # 1. Protect against invalid character roles
        if path.startswith("characters.") and path.endswith(".role"):
            parts = path.split(".")
            char_name = parts[1]
            val = str(mutation.new_value).upper()
            valid_roles = [r.value for r in CharacterRole]
            if val not in valid_roles:
                result.add_error(
                    entity=char_name,
                    path=path,
                    conflict=f"Invalid character role '{val}'. Must be one of {valid_roles}.",
                    source_rule="RULE_VALID_CHARACTER_ROLE",
                    recovery=f"Set role to one of {valid_roles} or keep UNRESOLVED."
                )

        # 2. Protect established FACTs from being silently overwritten with empty/null
        if path.startswith("characters."):
            parts = path.split(".")
            char_name = parts[1]
            if char_name in current_state.characters:
                char = current_state.characters[char_name]
                if char.status == StateStatus.FACT and mutation.new_value is None:
                    result.add_error(
                        entity=char_name,
                        path=path,
                        conflict=f"Attempted to overwrite established FACT character {char_name} with null.",
                        source_rule="RULE_IMMUTABLE_CANONICAL_FACT",
                        recovery="Use explicit state transition with deprecation rationale rather than null deletion."
                    )

        return result

    def validate_state(self, state: StoryState) -> ValidationResult:
        result = ValidationResult()

        # 1. Validate Character Consistency
        for name, char in state.characters.items():
            if not name.strip():
                result.add_error(
                    entity="UNKNOWN",
                    path="characters.name",
                    conflict="Character has empty name identifier.",
                    source_rule="RULE_CHARACTER_NAME_REQUIRED"
                )

            # Ensure reciprocal relationship consistency
            for rel in char.relationships:
                if rel.target_character == name:
                    result.add_error(
                        entity=name,
                        path=f"characters.{name}.relationships",
                        conflict=f"Character {name} cannot have a relationship with themselves.",
                        source_rule="RULE_NO_SELF_RELATIONSHIP"
                    )

        # 2. Validate Knowledge States
        for k in state.knowledge_states:
            if k.character_name not in state.characters:
                result.add_error(
                    entity=k.character_name,
                    path=f"knowledge.{k.character_name}",
                    conflict=f"Knowledge state recorded for nonexistent character '{k.character_name}'.",
                    source_rule="RULE_KNOWLEDGE_CHARACTER_EXISTS"
                )

        # 3. Validate Narrative Plants
        for plant in state.plants:
            if not plant.element_code.strip():
                result.add_error(
                    entity="PLANT",
                    path="plants.element_code",
                    conflict="Narrative plant element_code is required.",
                    source_rule="RULE_PLANT_CODE_REQUIRED"
                )

        return result
