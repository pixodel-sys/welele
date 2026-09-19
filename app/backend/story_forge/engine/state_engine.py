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
    ConstraintStatus,
    StoryConstraint,
    KnowledgeState,
    KnowledgeStatus,
    NarrativePlant
)
from ..validation import StoryValidator, ValidationResult


from .entity_registry import EntityRegistry, ResolutionOutcome


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
        Resolves or creates a canonical character entry using EntityRegistry (LOCK 2 & LOCK 3).
        Enforces stable IDs and prevents silent merging.
        """
        candidate = fallback_name or char_key
        res = EntityRegistry.resolve_entity(state, candidate)
        if res.outcome == ResolutionOutcome.MATCH and res.character and res.character_key:
            return res.character_key, res.character
        elif res.outcome == ResolutionOutcome.AMBIGUOUS:
            raise StateMutationError(f"Ambiguous character reference: {res.ambiguity_reason}")
        else:
            # ResolutionOutcome.NEW
            target_name = fallback_name or char_key.replace("_", " ").strip()
            new_char = res.character or CharacterState(name=target_name)
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
        elif path == "explicit_ending_declared":
            state.explicit_ending_declared = bool(val)
        elif path in ("story_document_context", "document_context"):
            state.story_document_context = str(val) if val is not None else None
        elif path == "chronology" or path.startswith("chronology"):
            if isinstance(val, list):
                state.chronology.extend(val)
            elif isinstance(val, dict):
                state.chronology.append(val)

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
                        elif k in ("gender", "sex"):
                            char.gender = str(v) if v is not None else None
                        elif k in ("pronouns", "pronoun"):
                            char.pronouns = str(v) if v is not None else None
                        elif k in ("summary", "description"):
                            char.summary = str(v) if v is not None else None
                        elif k == "relationships":
                            incoming_rels = v if isinstance(v, list) else [v]
                            for r in incoming_rels:
                                rel_obj = r if isinstance(r, CharacterRelationship) else CharacterRelationship(**r)
                                existing_idx = next(
                                    (idx for idx, existing_r in enumerate(char.relationships) if existing_r.target_character.lower() == rel_obj.target_character.lower()),
                                    None
                                )
                                if existing_idx is not None:
                                    char.relationships[existing_idx] = rel_obj
                                else:
                                    char.relationships.append(rel_obj)
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
                    elif field in ("gender", "sex"):
                        char.gender = str(val) if val is not None else None
                    elif field in ("pronouns", "pronoun"):
                        char.pronouns = str(val) if val is not None else None
                    elif field in ("summary", "description"):
                        char.summary = str(val) if val is not None else None
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
                        incoming_rels = val if isinstance(val, list) else [val]
                        for r in incoming_rels:
                            rel_obj = r if isinstance(r, CharacterRelationship) else CharacterRelationship(**r)
                            existing_idx = next(
                                (idx for idx, existing_r in enumerate(char.relationships) if existing_r.target_character.lower() == rel_obj.target_character.lower()),
                                None
                            )
                            if existing_idx is not None:
                                char.relationships[existing_idx] = rel_obj
                            else:
                                char.relationships.append(rel_obj)
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

        # Constraints mutations (Story-Version Precedence & Canonical Rules)
        elif path == "constraints" or path.startswith("constraints."):
            if path == "constraints":
                if isinstance(val, list):
                    for item in val:
                        c_obj = item if isinstance(item, StoryConstraint) else StoryConstraint(**item)
                        idx = next((i for i, c in enumerate(state.constraints) if c.constraint_id == c_obj.constraint_id), None)
                        if idx is not None:
                            state.constraints[idx] = c_obj
                        else:
                            state.constraints.append(c_obj)
            else:
                parts = path.split(".")
                cid_or_field = parts[1]
                if len(parts) == 2:
                    c_dict = val if isinstance(val, dict) else {"description": str(val)}
                    c_id = c_dict.get("constraint_id", cid_or_field)
                    c_cat = c_dict.get("category", "DEADLINE")
                    c_desc = c_dict.get("description", str(val))
                    c_status_str = str(c_dict.get("status", "ACTIVE")).upper()
                    try:
                        c_status = ConstraintStatus(c_status_str)
                    except ValueError:
                        c_status = ConstraintStatus.ACTIVE

                    # Enforce Story-Version Precedence:
                    # When an ACTIVE constraint of the same category or explicitly superseding an older constraint is added,
                    # mark the older constraint as SUPERSEDED.
                    if c_status == ConstraintStatus.ACTIVE:
                        supersedes_target = c_dict.get("supersedes") or c_dict.get("superseded_by")
                        for existing_c in state.constraints:
                            if existing_c.status == ConstraintStatus.ACTIVE:
                                if supersedes_target and (existing_c.constraint_id == supersedes_target or supersedes_target.lower() in existing_c.description.lower()):
                                    existing_c.status = ConstraintStatus.SUPERSEDED
                                    existing_c.superseded_by = c_id
                                elif existing_c.category.upper() == c_cat.upper() and existing_c.constraint_id != c_id:
                                    existing_c.status = ConstraintStatus.SUPERSEDED
                                    existing_c.superseded_by = c_id

                    new_constraint = StoryConstraint(
                        constraint_id=c_id,
                        category=c_cat,
                        description=c_desc,
                        status=c_status,
                        superseded_by=c_dict.get("superseded_by"),
                        source_context=c_dict.get("source_context"),
                        created_turn=int(c_dict.get("created_turn", state.state_version))
                    )
                    idx = next((i for i, c in enumerate(state.constraints) if c.constraint_id == c_id), None)
                    if idx is not None:
                        state.constraints[idx] = new_constraint
                    else:
                        state.constraints.append(new_constraint)
                elif len(parts) >= 3:
                    c_id = parts[1]
                    field = parts[2]
                    target_c = next((c for c in state.constraints if c.constraint_id == c_id), None)
                    if target_c:
                        if field == "status":
                            target_c.status = ConstraintStatus(str(val).upper())
                        elif field == "superseded_by":
                            target_c.superseded_by = str(val)
                        elif field == "description":
                            target_c.description = str(val)

