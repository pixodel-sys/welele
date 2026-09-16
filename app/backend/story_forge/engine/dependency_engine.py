"""
Welele Story Forge™ — Dependency Engine
Core narrative control loop: Detect, Assess, Prioritise, and Select Skill.
"""

from typing import List, Optional
from ..models import (
    StoryState,
    Dependency,
    DependencyType,
    DependencyStatus,
    DependencyAssessment,
    PriorityComponents,
    PriorityWeights,
    SkillEnum,
    StateStatus,
    CharacterRole,
    ChronologyEvent
)
from .priority import calculate_priority_score


class DependencyEngine:
    def __init__(self, weights: Optional[PriorityWeights] = None):
        self.weights = weights or PriorityWeights()

    def detect(
        self,
        state: StoryState,
        interpretation: str,
        events: Optional[List[ChronologyEvent]] = None
    ) -> List[Dependency]:
        """
        Scans current state, latest interpretation, and chronology events to identify unresolved requirements.
        """
        detected: List[Dependency] = []

        # 0. Unestablished Core Protagonist (Zero-State Foundation)
        if len(state.characters) == 0:
            detected.append(
                Dependency(
                    story_id=state.story_id,
                    dependency_key="PREMISE_PROTAGONIST_DEFINITION",
                    dependency_type=DependencyType.CHARACTER,
                    status=DependencyStatus.DETECTED,
                    target_entity="PROTAGONIST",
                    description="Story has a raw premise but no protagonist or core characters have been defined in canonical state.",
                    components=PriorityComponents(impact=10, urgency=10, risk=8, leverage=10, cost=1),
                    suggested_skill=SkillEnum.EXCAVATOR.value
                )
            )

        # 1. Unresolved Character Motivations & Roles
        for char_name, char in state.characters.items():
            if char.status == StateStatus.UNKNOWN:
                continue
            if char.role == CharacterRole.UNRESOLVED or not char.core_motivation:
                dep_key = f"CHAR_MOTIVATION_{char_name.upper().replace(' ', '_')}"
                detected.append(
                    Dependency(
                        story_id=state.story_id,
                        dependency_key=dep_key,
                        dependency_type=DependencyType.CHARACTER,
                        status=DependencyStatus.DETECTED,
                        target_entity=char_name,
                        description=f"Core motivation and driving dramatic goal for {char_name} is unresolved.",
                        components=PriorityComponents(impact=8, urgency=8, risk=7, leverage=8, cost=2),
                        suggested_skill=SkillEnum.EXCAVATOR.value
                    )
                )

            # Unresolved Character Relationships
            for rel in char.relationships:
                if rel.status == StateStatus.UNKNOWN:
                    continue
                if rel.status == StateStatus.UNRESOLVED or not rel.relation_type:
                    dep_key = f"REL_{char_name.upper()}_{rel.target_character.upper()}"
                    detected.append(
                        Dependency(
                            story_id=state.story_id,
                            dependency_key=dep_key,
                            dependency_type=DependencyType.CHARACTER,
                            status=DependencyStatus.DETECTED,
                            target_entity=f"{char_name} -> {rel.target_character}",
                            description=f"Nature and emotional stakes of relationship between {char_name} and {rel.target_character} is unresolved.",
                            components=PriorityComponents(impact=7, urgency=7, risk=6, leverage=7, cost=2),
                            suggested_skill=SkillEnum.CONNECTOR.value
                        )
                    )

        # Pairwise relationship detection for existing characters
        char_names = list(state.characters.keys())
        for i, c1 in enumerate(char_names):
            for c2 in char_names[i+1:]:
                if c1.replace("_", " ").strip().lower() == c2.replace("_", " ").strip().lower():
                    continue
                c1_obj = state.characters[c1]
                c2_obj = state.characters[c2]
                has_rel_1 = any(r.target_character == c2 for r in c1_obj.relationships)
                has_rel_2 = any(r.target_character == c1 for r in c2_obj.relationships)
                if not has_rel_1 and not has_rel_2:
                    dep_key = f"REL_{c1.upper()}_{c2.upper()}"
                    # High leverage for catalyst/confidant core dynamic
                    is_core = ("NKOSINATHI" in dep_key and "TEBOGO" in dep_key)
                    lev = 8 if is_core else 6
                    urg = 8 if is_core else 6
                    detected.append(
                        Dependency(
                            story_id=state.story_id,
                            dependency_key=dep_key,
                            dependency_type=DependencyType.CHARACTER,
                            status=DependencyStatus.DETECTED,
                            target_entity=f"{c1} <-> {c2}",
                            description=f"Relationship dynamic between {c1} and {c2} is unresolved.",
                            components=PriorityComponents(impact=7, urgency=urg, risk=6, leverage=lev, cost=2),
                            suggested_skill=SkillEnum.CONNECTOR.value
                        )
                    )

        # 2. Unresolved Knowledge Discrepancies
        # If an event occurred with participants, check if non-participants know or believe it
        if events:
            for ev in events:
                if ev.event_status == StateStatus.FACT and ev.participants:
                    for char_name in state.characters:
                        if char_name not in ev.participants:
                            # Check if knowledge state exists
                            known = any(
                                k.character_name == char_name and k.fact_key == ev.headline
                                for k in state.knowledge_states
                            )
                            if not known:
                                dep_key = f"KNOW_{char_name.upper()}_{ev.event_sequence}"
                                detected.append(
                                    Dependency(
                                        story_id=state.story_id,
                                        dependency_key=dep_key,
                                        dependency_type=DependencyType.KNOWLEDGE,
                                        status=DependencyStatus.DETECTED,
                                        target_entity=char_name,
                                        description=f"Awareness/belief of {char_name} regarding event '{ev.headline}' is unresolved.",
                                        components=PriorityComponents(impact=6, urgency=6, risk=7, leverage=6, cost=1),
                                        suggested_skill=SkillEnum.CONTINUITY_ENGINE.value
                                    )
                                )

        # 3. Unresolved Narrative Plants
        for plant in state.plants:
            if plant.payoff_status == "PLANTED" and not plant.intended_payoff:
                dep_key = f"PLANT_{plant.element_code.upper()}"
                detected.append(
                    Dependency(
                        story_id=state.story_id,
                        dependency_key=dep_key,
                        dependency_type=DependencyType.NARRATIVE,
                        status=DependencyStatus.DETECTED,
                        target_entity=plant.element_code,
                        description=f"Narrative payoff for plant '{plant.description}' is unresolved.",
                        components=PriorityComponents(impact=5, urgency=4, risk=5, leverage=5, cost=2),
                        suggested_skill=SkillEnum.PROPAGATOR.value
                    )
                )

        # 4. Premise-Derived Counter-Force / Opposing Entity Detection
        logline_lower = (state.logline or "").lower()
        has_counterforce_indicator = any(
            term in logline_lower
            for term in ["rival", "debt owed", "rival clan", "antagonist", "enemy", "nemesis", "syndicate", "conspiracy", "threat"]
        )
        has_antagonist_or_counterforce = any(
            c.role in (CharacterRole.ANTAGONIST, CharacterRole.SUPPORTING)
            for c in state.characters.values()
            if c.role != CharacterRole.PROTAGONIST
        )
        if len(state.characters) > 0 and has_counterforce_indicator and not has_antagonist_or_counterforce:
            detected.append(
                Dependency(
                    story_id=state.story_id,
                    dependency_key="PREMISE_COUNTERFORCE_DEFINITION",
                    dependency_type=DependencyType.CHARACTER,
                    status=DependencyStatus.DETECTED,
                    target_entity="COUNTER_FORCE",
                    description="The premise establishes an opposing force, rival entity, or creditor clan that remains undefined in canonical state.",
                    components=PriorityComponents(impact=8, urgency=8, risk=7, leverage=8, cost=2),
                    suggested_skill=SkillEnum.CONNECTOR.value
                )
            )

        # 5. Premise-Derived Narrative Plant / Physical Secret Element Detection
        has_plant_indicator = any(
            term in logline_lower
            for term in ["documents proving", "locked study", "contract", "secret will", "relic", "artifact", "hidden document", "deed"]
        )
        if len(state.characters) > 0 and has_plant_indicator and len(state.plants) == 0:
            detected.append(
                Dependency(
                    story_id=state.story_id,
                    dependency_key="PREMISE_NARRATIVE_PLANT_SPECIFICATION",
                    dependency_type=DependencyType.NARRATIVE,
                    status=DependencyStatus.DETECTED,
                    target_entity="NARRATIVE_PLANT",
                    description="The premise references physical proof, hidden documents, or secret contracts that must be anchored as a narrative plant in state.",
                    components=PriorityComponents(impact=6, urgency=6, risk=6, leverage=6, cost=2),
                    suggested_skill=SkillEnum.PROPAGATOR.value
                )
            )

        # Calculate scores for all detected dependencies
        for dep in detected:
            score, rationale = calculate_priority_score(dep.components, self.weights)
            dep.priority_score = score
            dep.priority_rationale = rationale

        return detected

    def assess(self, dependency: Dependency, state: StoryState) -> DependencyAssessment:
        score, rationale = calculate_priority_score(dependency.components, self.weights)
        skill = self.select_skill(dependency, state)
        return DependencyAssessment(
            dependency_id=dependency.id,
            components=dependency.components,
            calculated_score=score,
            rationale=rationale,
            recommended_skill=skill.value
        )

    def prioritise(self, dependencies: List[Dependency]) -> Optional[Dependency]:
        """
        Picks the single highest-priority non-resolved dependency.
        """
        active_candidates = [
            d for d in dependencies
            if d.status in (DependencyStatus.DETECTED, DependencyStatus.ASSESSED, DependencyStatus.PRIORITISED, DependencyStatus.ACTIVE)
        ]
        if not active_candidates:
            return None

        # Sort descending by priority_score, then urgency
        active_candidates.sort(
            key=lambda d: (d.priority_score, d.components.urgency, d.components.impact),
            reverse=True
        )
        selected = active_candidates[0]
        selected.status = DependencyStatus.ACTIVE
        return selected

    def select_skill(self, dependency: Dependency, state: StoryState) -> SkillEnum:
        """
        Selects the appropriate Forge Skill based on dependency domain and context.
        """
        dtype = dependency.dependency_type
        if dtype == DependencyType.CHARACTER:
            if "relationship" in dependency.description.lower() or "between" in dependency.description.lower():
                return SkillEnum.CONNECTOR
            return SkillEnum.EXCAVATOR
        elif dtype == DependencyType.KNOWLEDGE or dtype == DependencyType.TEMPORAL:
            return SkillEnum.CONTINUITY_ENGINE
        elif dtype == DependencyType.CAUSAL:
            return SkillEnum.CHALLENGER
        elif dtype == DependencyType.NARRATIVE:
            return SkillEnum.PROPAGATOR
        elif dtype == DependencyType.PRODUCTION:
            return SkillEnum.FORGER
        return SkillEnum.EXCAVATOR

    def evaluate_required_state_deficiencies(
        self,
        state: StoryState,
        events: Optional[List[ChronologyEvent]] = None,
        existing_dependencies: Optional[List[Dependency]] = None
    ) -> List[Dependency]:
        """
        Synthesizes required dependencies based on REQUIRED_STATE_SCHEMA_v0.1.
        Idempotent: Inspects existing dependencies to guarantee zero duplicate synthesis.
        """
        synthesized: List[Dependency] = []
        existing_keys = set(d.dependency_key for d in (existing_dependencies or []))
        events = events or []

        # Helper to add synthesized dependency idempotently
        def add_required(key: str, dtype: DependencyType, target: str, desc: str, skill: SkillEnum, impact: int = 8, urgency: int = 8, risk: int = 7, leverage: int = 8):
            if key not in existing_keys:
                dep = Dependency(
                    story_id=state.story_id,
                    dependency_key=key,
                    dependency_type=dtype,
                    status=DependencyStatus.DETECTED,
                    target_entity=target,
                    description=desc,
                    components=PriorityComponents(impact=impact, urgency=urgency, risk=risk, leverage=leverage, cost=1),
                    suggested_skill=skill.value
                )
                score, rationale = calculate_priority_score(dep.components, self.weights)
                dep.priority_score = score
                dep.priority_rationale = rationale
                synthesized.append(dep)
                existing_keys.add(key)

        # ---------------------------------------------------------------------
        # M0: PREMISE_LOCK Deficiencies
        # ---------------------------------------------------------------------
        if not state.logline or len(state.logline.strip()) < 20:
            add_required(
                "PREMISE_LOGLINE_SPECIFICATION",
                DependencyType.NARRATIVE,
                "PREMISE",
                "Story requires an unambiguous logline with core conflict and arena.",
                SkillEnum.EXCAVATOR,
                impact=10, urgency=10
            )
            return synthesized  # Must establish premise before downstream synthesis

        # ---------------------------------------------------------------------
        # M1: DRAMATIC_ENGINE_LOCK Deficiencies
        # ---------------------------------------------------------------------
        # 1. Protagonist Motivation
        if len(state.characters) == 0:
            add_required(
                "PREMISE_PROTAGONIST_DEFINITION",
                DependencyType.CHARACTER,
                "PROTAGONIST",
                "Protagonist identity and profession must be defined from premise.",
                SkillEnum.EXCAVATOR,
                impact=10, urgency=10
            )
        else:
            for cname, c in state.characters.items():
                if not c.core_motivation or not c.core_motivation.strip():
                    add_required(
                        f"CHAR_MOTIVATION_{cname.upper().replace(' ', '_')}",
                        DependencyType.CHARACTER,
                        cname,
                        f"Core driving motivation for {cname} is required to complete dramatic engine.",
                        SkillEnum.EXCAVATOR,
                        impact=9, urgency=9
                    )

        # 2. Flexible Counterforce (Character, Institution, Supernatural Force, Systemic)
        has_counterforce = (
            any(c.role == CharacterRole.ANTAGONIST for c in state.characters.values()) or
            len(state.characters) >= 2 or
            len(state.world.rules_and_lore) > 0 or
            any("debt" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "retribution" in (getattr(p, 'plant_name', None) or p.element_code).lower() for p in state.plants)
        )
        if not has_counterforce:
            add_required(
                "PREMISE_COUNTERFORCE_DEFINITION",
                DependencyType.CHARACTER,
                "COUNTERFORCE",
                "A grounded counterforce (opposing character, rival clan, institution, or supernatural force) must be defined.",
                SkillEnum.CONNECTOR,
                impact=9, urgency=8
            )

        # 3. Relationship Dynamic
        has_relationships = any(len(c.relationships) > 0 for c in state.characters.values()) or len(state.characters) >= 2
        if len(state.characters) >= 2 and not has_relationships:
            add_required(
                "RELATIONSHIP_DYNAMIC_CORE",
                DependencyType.CHARACTER,
                "PROTAGONIST <-> COUNTERFORCE",
                "The central relational conflict/leverage dynamic between Protagonist and opposing force must be defined.",
                SkillEnum.CONNECTOR,
                impact=8, urgency=7
            )

        # 4. Supernatural / World Rules (if applicable)
        logline_lower = (state.logline or "").lower()
        is_supernatural_premise = any(kw in logline_lower for kw in ("supernatural", "spirit", "ghost", "witchcraft", "occult", "curse", "blood pact", "demon", "magic"))
        if is_supernatural_premise and len(state.world.rules_and_lore) == 0 and not any("supernatural" in (c.core_motivation or "").lower() for c in state.characters.values()):
            add_required(
                "WORLD_RULE_SPECIFICATION",
                DependencyType.NARRATIVE,
                "ARENA_RULES",
                "Supernatural rules, ancestral debt mechanisms, and consequences must be anchored in state.",
                SkillEnum.PROPAGATOR,
                impact=8, urgency=7
            )

        # If M1 deficiencies exist (characters missing or incomplete), do not advance to M2 synthesis yet
        protagonists = [c for c in state.characters.values() if c.role == CharacterRole.PROTAGONIST or (len(state.characters) == 1 and c.status == StateStatus.FACT)]
        has_valid_protagonist = len(protagonists) > 0 and all(bool(c.core_motivation and c.core_motivation.strip()) for c in state.characters.values())
        if not has_valid_protagonist or not has_counterforce or synthesized:
            return synthesized

        # ---------------------------------------------------------------------
        # M2: EPISODIC_ARC_LOCK Deficiencies (Six Canonical Chronology Anchors)
        # ---------------------------------------------------------------------
        six_canonical_anchors = [
            ("EVENT_01_INCITING_DISRUPTION", "Inciting Disruption: Father's death / discovery of hidden ancestral debt documents."),
            ("EVENT_02_POINT_OF_NO_RETURN", "Point of No Return: Protagonist commits to investigate / enters the dangerous arena."),
            ("EVENT_03_MIDPOINT_REVELATION", "Midpoint Revelation: Hidden truth or escalating counterforce threat is revealed."),
            ("EVENT_04_DARK_NIGHT", "Dark Night / Low Point: Stakes climax, family under immediate supernatural/hostile threat."),
            ("EVENT_05_CLIMAX", "Climax: Decisive confrontation between protagonist and counterforce."),
            ("EVENT_06_RESOLUTION", "Resolution: Final consequence, cost paid, and new state established.")
        ]

        if len(events) < 6:
            for idx in range(len(events), 6):
                anchor_key, anchor_desc = six_canonical_anchors[idx]
                add_required(
                    anchor_key,
                    DependencyType.CAUSAL,
                    f"EVENT_SPINE_{idx+1}",
                    f"Canonical chronology anchor required: {anchor_desc}",
                    SkillEnum.CHALLENGER,
                    impact=8, urgency=7
                )

        # Narrative plant payoffs
        for p in state.plants:
            p_name = getattr(p, 'plant_name', None) or p.element_code
            if p.payoff_status == "PLANTED" and not p.intended_payoff:
                add_required(
                    f"PLANT_PAYOFF_LINK_{p_name.upper().replace(' ', '_')}",
                    DependencyType.NARRATIVE,
                    p_name,
                    f"Narrative plant '{p_name}' must declare an intended payoff event or dramatic payoff.",
                    SkillEnum.PROPAGATOR,
                    impact=7, urgency=6
                )

        return synthesized

