"""
Welele Story Forge™ — Validation Rules & Domain Invariants
Deterministic consistency checks for narrative, character, chronology, knowledge, and canon integrity.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..models import StoryState, StateMutation, StateStatus, CharacterRole, KnowledgeStatus


class ValidationError(BaseModel):
    affected_entity: str
    affected_path: str
    conflict: str
    source_rule: str
    recommended_recovery: Optional[str] = None


class ValidationResult(BaseModel):
    is_valid: bool = True
    errors: List[ValidationError] = Field(default_factory=list)

    def add_error(
        self,
        entity: str,
        path: str,
        conflict: str,
        source_rule: str,
        recovery: Optional[str] = None
    ):
        self.is_valid = False
        self.errors.append(
            ValidationError(
                affected_entity=entity,
                affected_path=path,
                conflict=conflict,
                source_rule=source_rule,
                recommended_recovery=recovery
            )
        )
