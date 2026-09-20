"""
Welele Story Forge™ — Deterministic Mock Reasoning Adapter v0.1
Pure-function offline reasoning adapter adhering to the ReasoningAdapter contract.
Consumes ReasoningRequest and produces validated ReasoningDecision without DB or state access.
"""

from typing import Optional, List, Dict, Any, Callable
from .contracts import (
    ReasoningAdapter,
    ReasoningRequest,
    ReasoningDecision,
    ForgeObjective
)
from ..models import (
    SkillEnum,
    AuthorityMode,
    StateMutation,
    MutationType,
    CharacterRole,
    ProductionDecision,
    ProductionAspect
)


class MockReasoningAdapter(ReasoningAdapter):
    """
    Deterministic mock reasoning adapter with scriptable rules and benchmark presets.
    Operates strictly via the `reason(request: ReasoningRequest) -> ReasoningDecision` protocol.
    """

    def __init__(self, script_rules: Optional[Dict[str, Callable[[ReasoningRequest], ReasoningDecision]]] = None):
        self.script_rules = script_rules or {}
        self.decision_history: List[ReasoningDecision] = []

    def register_rule(self, trigger_key: str, handler: Callable[[ReasoningRequest], ReasoningDecision]):
        self.script_rules[trigger_key] = handler

    def reason(self, request: ReasoningRequest) -> ReasoningDecision:
        dep = request.active_dependency
        dep_key = dep.dependency_key if dep else "DEFAULT"

        # Check for registered custom scripted rule
        if dep_key in self.script_rules:
            decision = self.script_rules[dep_key](request)
            self.decision_history.append(decision)
            return decision

        # ---------------------------------------------------------------------
        # Benchmark Scenarios (Inhliziyo Ayiphakelwa & Core Archetypes)
        # ---------------------------------------------------------------------

        # 1. Unresolved Nkosinathi Motivation
        if dep_key.startswith("CHAR_MOTIVATION_NKOSINATHI"):
            if not request.creator_response:
                decision = ReasoningDecision(
                    action=AuthorityMode.ASK,
                    dependency_id=dep.id if dep else None,
                    skill=SkillEnum.EXCAVATOR,
                    question="What is Nkosinathi's immediate driving goal upon discovering Thabo and Tebogo's engagement?",
                    rationale="Creator ownership strictly required for primary antagonist motivation.",
                    confidence=0.98,
                    requires_creator=True,
                    assumptions=["Nkosinathi witnessed the private engagement ceremony."],
                    evidence=["Chronology Event #1: Nkosinathi Discovers Engagement"]
                )
            else:
                decision = ReasoningDecision(
                    action=AuthorityMode.INFER,
                    dependency_id=dep.id if dep else None,
                    skill=SkillEnum.EXCAVATOR,
                    proposal=request.creator_response,
                    proposed_mutations=[
                        StateMutation(
                            target_path="characters.Nkosinathi.core_motivation",
                            new_value=request.creator_response,
                            mutation_type=MutationType.UPDATE,
                            rationale="Applied validated creator answer"
                        ),
                        StateMutation(
                            target_path="characters.Nkosinathi.role",
                            new_value=CharacterRole.ANTAGONIST.value,
                            mutation_type=MutationType.UPDATE,
                            rationale="Inferred antagonist role based on confrontation trajectory"
                        )
                    ],
                    rationale="Applied validated creator response into canonical state.",
                    confidence=1.0,
                    requires_creator=False,
                    assumptions=[],
                    evidence=[f"Creator Response: {request.creator_response}"]
                )
            self.decision_history.append(decision)
            return decision

        # 2. Unresolved Nkosinathi <-> Tebogo Relationship
        if dep_key.startswith("REL_NKOSINATHI_TEBOGO") or dep_key.startswith("REL_TEBOGO_NKOSINATHI"):
            if not request.creator_response:
                decision = ReasoningDecision(
                    action=AuthorityMode.ASK,
                    dependency_id=dep.id if dep else None,
                    skill=SkillEnum.CONNECTOR,
                    question="What was the nature of Nkosinathi and Tebogo's relationship prior to the engagement?",
                    rationale="Clarifies emotional stakes of the betrayal.",
                    confidence=0.95,
                    requires_creator=True,
                    assumptions=["Past unvoiced history exists between Nkosinathi and Tebogo."],
                    evidence=["Nkosinathi reaction to engagement discovery"]
                )
            else:
                decision = ReasoningDecision(
                    action=AuthorityMode.INFER,
                    dependency_id=dep.id if dep else None,
                    skill=SkillEnum.CONNECTOR,
                    proposal=request.creator_response,
                    proposed_mutations=[
                        StateMutation(
                            target_path="characters.Nkosinathi.relationships",
                            new_value=[{
                                "target_character": "Tebogo",
                                "relation_type": "EX_LOVER",
                                "status": "FACT",
                                "dynamic": request.creator_response,
                                "tension_level": 9
                            }],
                            mutation_type=MutationType.UPDATE,
                            rationale="Recorded canonical relationship"
                        )
                    ],
                    rationale="Applied creator relationship dynamic.",
                    confidence=1.0,
                    requires_creator=False,
                    assumptions=[],
                    evidence=[f"Creator Response: {request.creator_response}"]
                )
            self.decision_history.append(decision)
            return decision

        # 3. Inferred Rivalry: Nkosinathi <-> Thabo
        if dep_key.startswith("REL_NKOSINATHI_THABO") or dep_key.startswith("REL_THABO_NKOSINATHI"):
            decision = ReasoningDecision(
                action=AuthorityMode.INFER,
                dependency_id=dep.id if dep else None,
                skill=SkillEnum.CONNECTOR,
                proposal="Direct rivalry stemming from engagement discovery.",
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Nkosinathi.relationships",
                        new_value=[{
                            "target_character": "Thabo",
                            "relation_type": "RIVAL",
                            "status": "FACT",
                            "dynamic": "Hostile dynasty competition and personal betrayal",
                            "tension_level": 10
                        }],
                        mutation_type=MutationType.UPDATE,
                        rationale="Derived from engagement discovery"
                    )
                ],
                rationale="Direct rivalry inferred safely from canonical event and motivation.",
                confidence=0.96,
                requires_creator=False,
                assumptions=["Thabo is aware of dynasty competition."],
                evidence=["Chronology Event #1", "Nkosinathi motivation"]
            )
            self.decision_history.append(decision)
            return decision

        # 4. Inferred Engagement: Thabo <-> Tebogo
        if dep_key.startswith("REL_THABO_TEBOGO") or dep_key.startswith("REL_TEBOGO_THABO"):
            decision = ReasoningDecision(
                action=AuthorityMode.INFER,
                dependency_id=dep.id if dep else None,
                skill=SkillEnum.CONNECTOR,
                proposal="Secret engagement in Maboneng.",
                proposed_mutations=[
                    StateMutation(
                        target_path="characters.Thabo.relationships",
                        new_value=[{
                            "target_character": "Tebogo",
                            "relation_type": "FIANCE",
                            "status": "FACT",
                            "dynamic": "Secret engagement in Maboneng",
                            "tension_level": 4
                        }],
                        mutation_type=MutationType.UPDATE,
                        rationale="Derived from starting event"
                    )
                ],
                rationale="Established canonical relationship directly from starting event.",
                confidence=1.0,
                requires_creator=False,
                assumptions=[],
                evidence=["Chronology Event #1: Nkosinathi Discovers Engagement"]
            )
            self.decision_history.append(decision)
            return decision

        # 5. Inferred Knowledge States
        if dep_key.startswith("KNOW_"):
            parts = dep_key.split("_")
            char_target = parts[1].capitalize() if len(parts) > 1 else "Nkosinathi"
            decision = ReasoningDecision(
                action=AuthorityMode.INFER,
                dependency_id=dep.id if dep else None,
                skill=SkillEnum.CONTINUITY_ENGINE,
                proposal=f"Knowledge state for {char_target}.",
                proposed_mutations=[
                    StateMutation(
                        target_path=f"knowledge.{char_target}.ENGAGEMENT",
                        new_value={"status": "KNOWS", "confidence": 1.0},
                        mutation_type=MutationType.CREATE,
                        rationale="Direct witness discovery"
                    )
                ],
                rationale=f"Inferred direct knowledge state for participant {char_target}.",
                confidence=0.99,
                requires_creator=False,
                assumptions=[],
                evidence=["Chronology Event #1 participant list"]
            )
            self.decision_history.append(decision)
            return decision

        # 6. Production Decisions
        if dep_key.startswith("PROD_") or (dep and dep.dependency_type == "PRODUCTION"):
            prod_dec = ProductionDecision(
                story_id=request.story_id,
                decision_key=dep_key,
                narrative_resolution="The confrontation takes place in an isolated high-stakes urban setting.",
                production_aspect=ProductionAspect.LOCATION,
                deferred_details="Exact rooftop or warehouse venue and drone permit choreography deferred to physical production."
            )
            decision = ReasoningDecision(
                action=AuthorityMode.RECORD_PRODUCTION_DECISION,
                dependency_id=dep.id if dep else None,
                skill=SkillEnum.FORGER,
                production_decision=prod_dec,
                rationale="Separated narrative canon from physical filming choices.",
                confidence=0.95,
                requires_creator=False,
                assumptions=["Filming location requires commercial permit."],
                evidence=["Urban Johannesburg setting requirement"]
            )
            self.decision_history.append(decision)
            return decision

        # 7. General Fallback Reasoning
        if dep:
            decision = ReasoningDecision(
                action=AuthorityMode.ASK,
                dependency_id=dep.id,
                skill=SkillEnum(dep.suggested_skill) if dep.suggested_skill in [s.value for s in SkillEnum] else SkillEnum.EXCAVATOR,
                question=f"How should the story resolve: {dep.description}?",
                rationale=f"Creator ownership required for unresolved dependency {dep.dependency_key}.",
                confidence=0.85,
                requires_creator=True,
                assumptions=[],
                evidence=[dep.description]
            )
        else:
            decision = ReasoningDecision(
                action=AuthorityMode.STOP,
                skill=SkillEnum.FORGE_JUDGE,
                rationale="All active dependencies resolved or deferred. Narrative kernel cycle complete.",
                confidence=1.0,
                requires_creator=False,
                assumptions=[],
                evidence=["Zero active candidates in dependency queue"]
            )

        self.decision_history.append(decision)
        return decision
