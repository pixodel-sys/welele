"""
Welele Story Forge™ — Canonical Entity Registry & Resolution Engine
Locks Enforced:
- LOCK 2: Characters have stable internal IDs; names/aliases are labels, not identities.
- LOCK 3: Never silently merge ambiguous characters. If ambiguous: ASK.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
from uuid import uuid4

from ..models.state import CharacterState, CharacterRole, StateStatus, StoryState


class ResolutionOutcome(str, Enum):
    MATCH = "MATCH"
    NEW = "NEW"
    AMBIGUOUS = "AMBIGUOUS"


class EntityResolutionResult:
    def __init__(
        self,
        outcome: ResolutionOutcome,
        character_key: Optional[str] = None,
        character: Optional[CharacterState] = None,
        candidate_matches: Optional[List[str]] = None,
        ambiguity_reason: Optional[str] = None,
        similarity_score: float = 0.0
    ):
        self.outcome = outcome
        self.character_key = character_key
        self.character = character
        self.candidate_matches = candidate_matches or []
        self.ambiguity_reason = ambiguity_reason
        self.similarity_score = similarity_score


class EntityRegistry:
    """
    Governs canonical character identity resolution across Story Forge.
    Prevents duplicate alias pollution while strictly preventing silent merging of distinct characters.
    """

    MATCH_THRESHOLD = 0.88       # High confidence match (e.g. Noluthando vs Nolutando)
    AMBIGUOUS_THRESHOLD = 0.65   # Ambiguous band requiring creator clarification

    @classmethod
    def normalize_name(cls, name: str) -> str:
        if not name:
            return ""
        norm = name.replace("_", " ").strip().lower()
        # Strip common article prefixes if present (e.g. "the mother" -> "mother")
        if norm.startswith("the ") and len(norm) > 4:
            norm = norm[4:].strip()
        return norm

    @classmethod
    def calculate_similarity(cls, s1: str, s2: str) -> float:
        n1 = cls.normalize_name(s1)
        n2 = cls.normalize_name(s2)
        if not n1 or not n2:
            return 0.0
        if n1 == n2:
            return 1.0
        # Check sub-tokens (e.g. "Mama Joyce" vs "Joyce")
        tokens1 = set(n1.split())
        tokens2 = set(n2.split())
        if tokens1 and tokens2 and (tokens1.issubset(tokens2) or tokens2.issubset(tokens1)):
            return 0.90

        # Check prefix / shortened nickname match (e.g. "Noli" vs "Noluthando" and "Nolwazi")
        short_s, long_s = (n1, n2) if len(n1) <= len(n2) else (n2, n1)
        if len(short_s) >= 3 and long_s.startswith(short_s[:3]):
            prefix_score = 0.78 if long_s.startswith(short_s) else 0.70
            return max(prefix_score, SequenceMatcher(None, n1, n2).ratio())

        return SequenceMatcher(None, n1, n2).ratio()

    @classmethod
    def resolve_entity(
        cls,
        state: StoryState,
        candidate_name: str,
        role_hint: Optional[CharacterRole] = None,
        character_id_hint: Optional[str] = None
    ) -> EntityResolutionResult:
        """
        Resolves candidate character reference against canonical characters in StoryState.
        Returns MATCH, NEW, or AMBIGUOUS.
        """
        if not candidate_name and not character_id_hint:
            return EntityResolutionResult(
                outcome=ResolutionOutcome.AMBIGUOUS,
                ambiguity_reason="Candidate reference lacks both name and ID hint."
            )

        norm_candidate = cls.normalize_name(candidate_name)

        # 1. Exact match on character_id
        if character_id_hint:
            for key, char in state.characters.items():
                if char.character_id == character_id_hint:
                    return EntityResolutionResult(
                        outcome=ResolutionOutcome.MATCH,
                        character_key=key,
                        character=char,
                        similarity_score=1.0
                    )

        # 2. Exact match on dictionary key, character name, or alias
        for key, char in state.characters.items():
            norm_key = cls.normalize_name(key)
            norm_name = cls.normalize_name(char.name)
            norm_aliases = [cls.normalize_name(a) for a in char.aliases]

            if norm_candidate == norm_key or norm_candidate == norm_name or norm_candidate in norm_aliases:
                return EntityResolutionResult(
                    outcome=ResolutionOutcome.MATCH,
                    character_key=key,
                    character=char,
                    similarity_score=1.0
                )

        # 3. Role alias match (e.g. reference to "protagonist" when an established protagonist exists)
        if norm_candidate in ("protagonist", "lead", "main character"):
            protagonists = [
                (k, c) for k, c in state.characters.items()
                if c.role == CharacterRole.PROTAGONIST
            ]
            if len(protagonists) == 1:
                key, char = protagonists[0]
                return EntityResolutionResult(
                    outcome=ResolutionOutcome.MATCH,
                    character_key=key,
                    character=char,
                    similarity_score=1.0
                )

        if norm_candidate in ("antagonist", "counterforce", "rival", "villain"):
            antagonists = [
                (k, c) for k, c in state.characters.items()
                if c.role == CharacterRole.ANTAGONIST
            ]
            if len(antagonists) == 1:
                key, char = antagonists[0]
                return EntityResolutionResult(
                    outcome=ResolutionOutcome.MATCH,
                    character_key=key,
                    character=char,
                    similarity_score=1.0
                )

        # 4. Fuzzy & Typo Similarity Check across all existing characters
        best_match_key: Optional[str] = None
        best_char: Optional[CharacterState] = None
        best_score: float = 0.0
        ambiguous_candidates: List[str] = []

        for key, char in state.characters.items():
            scores = [
                cls.calculate_similarity(candidate_name, key),
                cls.calculate_similarity(candidate_name, char.name),
            ]
            for a in char.aliases:
                scores.append(cls.calculate_similarity(candidate_name, a))

            max_char_score = max(scores)
            if max_char_score >= cls.MATCH_THRESHOLD:
                if max_char_score > best_score:
                    best_score = max_char_score
                    best_match_key = key
                    best_char = char
            elif max_char_score >= cls.AMBIGUOUS_THRESHOLD:
                ambiguous_candidates.append(char.name)

        # Check for multiple ambiguous candidates (LOCK 3)
        if ambiguous_candidates:
            if not best_match_key:
                return EntityResolutionResult(
                    outcome=ResolutionOutcome.AMBIGUOUS,
                    candidate_matches=ambiguous_candidates,
                    ambiguity_reason=f"Reference '{candidate_name}' is ambiguously close to {', '.join(ambiguous_candidates)}.",
                    similarity_score=cls.AMBIGUOUS_THRESHOLD
                )

        # Clean high-confidence match
        if best_match_key and best_char:
            # Check if roles conflict severely (e.g. established antagonist vs candidate tagged protagonist)
            if role_hint and best_char.role != CharacterRole.UNRESOLVED and role_hint != best_char.role:
                if (role_hint == CharacterRole.PROTAGONIST and best_char.role == CharacterRole.ANTAGONIST) or \
                   (role_hint == CharacterRole.ANTAGONIST and best_char.role == CharacterRole.PROTAGONIST):
                    return EntityResolutionResult(
                        outcome=ResolutionOutcome.AMBIGUOUS,
                        candidate_matches=[best_char.name],
                        ambiguity_reason=f"Candidate '{candidate_name}' has role {role_hint.value} which conflicts with {best_char.name}'s role {best_char.role.value}.",
                        similarity_score=best_score
                    )

            # Register alternate spelling as alias if new
            if candidate_name not in best_char.aliases and candidate_name != best_char.name:
                best_char.aliases.append(candidate_name)

            return EntityResolutionResult(
                outcome=ResolutionOutcome.MATCH,
                character_key=best_match_key,
                character=best_char,
                similarity_score=best_score
            )

        # 5. Clean NEW character
        clean_key = candidate_name.strip()
        new_char = CharacterState(
            character_id=str(uuid4()),
            name=clean_key,
            role=role_hint or CharacterRole.UNRESOLVED,
            status=StateStatus.FACT
        )
        return EntityResolutionResult(
            outcome=ResolutionOutcome.NEW,
            character_key=clean_key,
            character=new_char,
            similarity_score=0.0
        )
