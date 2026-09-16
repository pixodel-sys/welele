"""
Welele Story Forge™ — Consequence Propagator
Evaluates accepted state mutations to answer: "What else must now be true?"
"""

from typing import List, Tuple, Optional
from ..models import (
    StoryState,
    StateMutation,
    Consequence,
    KnowledgeState,
    KnowledgeStatus,
    StateStatus,
    ChronologyEvent,
    MutationType
)


class ConsequencePropagator:
    """
    Propagates deterministic narrative, knowledge, and relational consequences
    arising from state mutations.
    """

    def propagate(
        self,
        state: StoryState,
        mutations: List[StateMutation],
        events: Optional[List[ChronologyEvent]] = None
    ) -> List[Consequence]:
        consequences: List[Consequence] = []

        for mut in mutations:
            path = mut.target_path

            # 1. Character Motivation / Status Mutation Propagation
            if path.startswith("characters."):
                parts = path.split(".")
                char_name = parts[1]
                field = parts[2] if len(parts) > 2 else ""

                if field == "core_motivation":
                    consequences.append(
                        Consequence(
                            description=(
                                f"Establishing {char_name}'s motivation ({mut.new_value}) "
                                f"forces relational tension with connected characters."
                            ),
                            impacted_entity=char_name,
                            new_dependency_detected=f"TENSION_SURROUNDING_{char_name.upper()}"
                        )
                    )
                elif field == "role":
                    consequences.append(
                        Consequence(
                            description=f"Assigning role {mut.new_value} to {char_name} solidifies character dynamic in story canon.",
                            impacted_entity=char_name
                        )
                    )

            # 2. Chronology Event Propagation -> Knowledge State
            elif path.startswith("events") or path.startswith("chronology"):
                if isinstance(mut.new_value, dict) or hasattr(mut.new_value, "headline"):
                    headline = getattr(mut.new_value, "headline", mut.new_value.get("headline", "Event")) if isinstance(mut.new_value, dict) else mut.new_value.headline
                    participants = getattr(mut.new_value, "participants", mut.new_value.get("participants", [])) if isinstance(mut.new_value, dict) else mut.new_value.participants

                    for char_name in participants:
                        consequences.append(
                            Consequence(
                                description=f"{char_name} witnessed '{headline}' directly, acquiring firsthand FACT knowledge.",
                                impacted_entity=char_name,
                                derived_mutation=StateMutation(
                                    target_path=f"knowledge.{char_name}.{headline}",
                                    new_value={"status": "KNOWS", "confidence": 1.0},
                                    mutation_type=MutationType.CREATE,
                                    rationale="Direct participant in event"
                                )
                            )
                        )

            # 3. Relationship Mutation Propagation
            elif "relationships" in path:
                consequences.append(
                    Consequence(
                        description=f"Relationship mutation on {path} alters reciprocal dramatic balance.",
                        impacted_entity=path,
                        new_dependency_detected=f"RECIPROCAL_{path.replace('.', '_')}"
                    )
                )

        return consequences
