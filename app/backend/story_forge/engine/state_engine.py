"""
Welele Story Forge™ — State Mutation Engine
Transactional, append-aware mutation executor with optimistic concurrency and validation rollback.
"""

from typing import List, Optional, Tuple, Dict, Any
from copy import deepcopy
from ..models import (
    StoryState,
    StateMutation,
    MutationType,
    CharacterState,
    CharacterRole,
    CharacterRelationship,
    StateStatus,
    KnowledgeState,
    KnowledgeStatus,
    NarrativePlant
)
from ..validation import StoryValidator, ValidationResult


class StateMutationError(Exception):
    """Raised when mutation application or validation fails."""
    def __init__(self, message: str, validation_result: Optional[ValidationResult] = None):
        super().__init__(message)
        self.validation_result = validation_result


class StateEngine:
    def __init__(self, validator: Optional[StoryValidator] = None):
        self.validator = validator or StoryValidator()

    def apply_mutations(
        self,
        current_state: StoryState,
        mutations: List[StateMutation],
        transition_id: Optional[str] = None
    ) -> Tuple[StoryState, ValidationResult]:
        """
        Transactionally applies mutations to produce a new version of StoryState.
        If any mutation or resulting state is invalid, raises StateMutationError.
        """
        # 1. Validate individual mutations before application
        for mut in mutations:
            mut_val = self.validator.validate_mutation(current_state, mut)
            if not mut_val.is_valid:
                raise StateMutationError(
                    f"Mutation validation failed on {mut.target_path}",
                    validation_result=mut_val
                )

        # 2. Clone state for new version
        new_state = deepcopy(current_state)
        new_state.previous_state_version = current_state.state_version
        new_state.state_version = current_state.state_version + 1
        new_state.source_transition_id = transition_id

        # 3. Apply mutations
        for mut in mutations:
            self._apply_single_mutation(new_state, mut)

        # 4. Validate complete resulting state
        final_validation = self.validator.validate_state(new_state)
        if not final_validation.is_valid:
            raise StateMutationError(
                "Final StoryState validation failed after applying mutations",
                validation_result=final_validation
            )

        return new_state, final_validation

    @classmethod
    def _resolve_character_entry(
        cls,
        state: StoryState,
        char_key: str,
        fallback_name: Optional[str] = None
    ) -> Tuple[str, CharacterState]:
        """
        Resolves or creates a canonical character entry, matching exact keys,
        normalized underscore/space variations, role aliases, or explicit fallback names.
        Prevents duplicate alias key pollution (e.g., 'Zodwa Khumalo' vs 'Zodwa_Khumalo').
        """
        # 1. Exact match
        if char_key in state.characters:
            return char_key, state.characters[char_key]

        # 2. Normalized match against existing character keys
        norm_key = char_key.replace("_", " ").strip().lower()
        for name, c in state.characters.items():
            if name.replace("_", " ").strip().lower() == norm_key:
                return name, c
            if c.name and c.name.replace("_", " ").strip().lower() == norm_key:
                return name, c

        # 3. Role alias match (e.g. 'protagonist')
        if char_key.upper() in CharacterRole.__members__:
            role_enum = CharacterRole[char_key.upper()]
            for name, c in state.characters.items():
                if c.role == role_enum:
                    return name, c

        # 4. If a fallback/explicit name was supplied in the payload
        if fallback_name:
            norm_fallback = fallback_name.replace("_", " ").strip().lower()
            for name, c in state.characters.items():
                if name.replace("_", " ").strip().lower() == norm_fallback:
                    return name, c
                if c.name and c.name.replace("_", " ").strip().lower() == norm_fallback:
                    return name, c

        # 5. Create new character entry using fallback_name or char_key normalized
        target_name = fallback_name or char_key.replace("_", " ").strip()
        new_char = CharacterState(name=target_name)
        state.characters[target_name] = new_char
        return target_name, new_char

    def _apply_single_mutation(self, state: StoryState, mutation: StateMutation) -> None:
        path = mutation.target_path
        val = mutation.new_value

        # Global story properties
        if path == "title":
            state.title = str(val)
        elif path == "logline":
            state.logline = str(val)
        elif path == "theme":
            state.theme = str(val)
        elif path == "tone":
            state.tone = str(val)

        # Character mutations
        elif path.startswith("characters."):
            parts = path.split(".")
            char_key = parts[1]

            if len(parts) == 2:
                # Direct character object or dict replacement / creation
                if isinstance(val, dict):
                    clean_dict = dict(val)
                    explicit_name = clean_dict.get("name")
                    
                    # Handle role alias if key was a role like 'protagonist'
                    role_alias = None
                    if char_key.upper() in CharacterRole.__members__:
                        role_alias = CharacterRole[char_key.upper()]

                    if "role" in clean_dict and isinstance(clean_dict["role"], str):
                        try:
                            clean_dict["role"] = CharacterRole(clean_dict["role"].upper())
                        except ValueError:
                            clean_dict["role"] = role_alias or CharacterRole.SUPPORTING
                    elif role_alias and "role" not in clean_dict:
                        clean_dict["role"] = role_alias

                    if "status" in clean_dict and isinstance(clean_dict["status"], str):
                        val_status = clean_dict["status"].upper()
                        if val_status in ("RESOLVED", "ESTABLISHED", "FACT", "CONFIRMED"):
                            clean_dict["status"] = StateStatus.FACT
                        elif val_status in ("UNKNOWN",):
                            clean_dict["status"] = StateStatus.UNKNOWN
                        elif val_status in ("UNRESOLVED", "PENDING"):
                            clean_dict["status"] = StateStatus.UNRESOLVED
                        else:
                            clean_dict["status"] = StateStatus.FACT

                    canonical_key, char = self._resolve_character_entry(state, char_key, explicit_name)

                    # Multi-attribute atomic ingestion
                    for k, v in clean_dict.items():
                        if k in ("core_motivation", "motivation"):
                            char.core_motivation = str(v) if v is not None else None
                        elif k in ("secret_desire", "desire"):
                            char.secret_desire = str(v) if v is not None else None
                        elif k in ("fatal_flaw", "flaw"):
                            char.fatal_flaw = str(v) if v is not None else None
                        elif k == "attributes" and isinstance(v, dict):
                            char.attributes.update(v)
                        elif hasattr(char, k):
                            setattr(char, k, v)
                        else:
                            char.attributes[k] = v

                elif isinstance(val, CharacterState):
                    target_name = val.name or char_key
                    canonical_key, _ = self._resolve_character_entry(state, char_key, target_name)
                    state.characters[canonical_key] = val

            elif len(parts) >= 3:
                canonical_key, char = self._resolve_character_entry(state, char_key)

                if len(parts) == 3:
                    field = parts[2]
                    if field in ("role", "character_role"):
                        try:
                            char.role = CharacterRole(str(val).upper())
                        except ValueError:
                            char.role = CharacterRole.SUPPORTING
                    elif field in ("core_motivation", "motivation"):
                        char.core_motivation = str(val) if val is not None else None
                    elif field in ("secret_desire", "desire"):
                        char.secret_desire = str(val) if val is not None else None
                    elif field in ("fatal_flaw", "flaw"):
                        char.fatal_flaw = str(val) if val is not None else None
                    elif field == "archetype":
                        char.archetype = str(val) if val is not None else None
                    elif field == "status":
                        val_status = str(val).upper()
                        if val_status in ("RESOLVED", "ESTABLISHED", "FACT", "CONFIRMED"):
                            char.status = StateStatus.FACT
                        elif val_status in ("UNKNOWN",):
                            char.status = StateStatus.UNKNOWN
                        elif val_status in ("UNRESOLVED", "PENDING"):
                            char.status = StateStatus.UNRESOLVED
                        else:
                            char.status = StateStatus.FACT
                    elif field == "relationships":
                        if isinstance(val, list):
                            char.relationships = [
                                r if isinstance(r, CharacterRelationship) else CharacterRelationship(**r)
                                for r in val
                            ]
                    elif field == "attributes" and isinstance(val, dict):
                        char.attributes.update(val)
                    else:
                        char.attributes[field] = val
                elif len(parts) == 4 and parts[2] == "attributes":
                    attr_key = parts[3]
                    char.attributes[attr_key] = val

        # Knowledge state mutations
        elif path.startswith("knowledge."):
            parts = path.split(".")
            char_name = parts[1]
            fact_key = parts[2] if len(parts) > 2 else "GENERAL"

            # Remove existing matching knowledge
            state.knowledge_states = [
                k for k in state.knowledge_states
                if not (k.character_name == char_name and k.fact_key == fact_key)
            ]

            status_val = KnowledgeStatus.KNOWS
            confidence = 1.0
            if isinstance(val, dict):
                status_val = KnowledgeStatus(val.get("status", "KNOWS"))
                confidence = float(val.get("confidence", 1.0))
            elif isinstance(val, KnowledgeStatus):
                status_val = val

            state.knowledge_states.append(
                KnowledgeState(
                    character_name=char_name,
                    fact_key=fact_key,
                    status=status_val,
                    confidence=confidence
                )
            )

        # Plants mutations
        elif path.startswith("plants."):
            parts = path.split(".")
            code = parts[1]
            state.plants = [p for p in state.plants if p.element_code != code]
            if isinstance(val, NarrativePlant):
                state.plants.append(val)
            elif isinstance(val, dict):
                state.plants.append(NarrativePlant(**val))
