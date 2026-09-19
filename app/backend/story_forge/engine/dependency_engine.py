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
                    # High leverage for core dramatic polarity (e.g. Protagonist vs Antagonist/Supporting)
                    is_core = (
                        (c1_obj.role == CharacterRole.PROTAGONIST and c2_obj.role in (CharacterRole.ANTAGONIST, CharacterRole.SUPPORTING))
                        or (c2_obj.role == CharacterRole.PROTAGONIST and c1_obj.role in (CharacterRole.ANTAGONIST, CharacterRole.SUPPORTING))
                    )
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
            for term in ["rival", "adversary", "opposing", "antagonist", "enemy", "nemesis", "syndicate", "conspiracy", "threat"]
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
                    description="The premise establishes an opposing force or counterforce that remains undefined in canonical state.",
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

    def reconcile_satisfied_dependencies(
        self,
        state: StoryState,
        events: Optional[List[ChronologyEvent]] = None,
        existing_dependencies: Optional[List[Dependency]] = None
    ) -> List[Dependency]:
        """
        Reconciles existing dependencies against the entire canonical StoryState and chronology.
        LOCK 5: Every creator response triggers 'What did we just learn?' across the entire graph.
        Returns the list of dependencies that were newly marked RESOLVED.
        """
        if not existing_dependencies:
            return []

        all_events = (state.chronology if (hasattr(state, 'chronology') and state.chronology) else (events or []))
        resolved_deps: List[Dependency] = []

        logline_valid = bool(state.logline and len(state.logline.strip()) >= 20)
        protagonists = [
            c for c in state.characters.values()
            if c.role == CharacterRole.PROTAGONIST or (len(state.characters) == 1 and c.status == StateStatus.FACT)
        ]
        has_valid_protagonist = len(protagonists) > 0 and all(bool(c.core_motivation and c.core_motivation.strip()) for c in state.characters.values())
        logline_text = (state.logline or "").lower()
        has_systemic_counterforce = any(
            term in logline_text
            for term in ("drought", "famine", "blizzard", "storm", "corruption", "poverty", "syndicate", "debt", "disaster", "opposing", "enemy", "rival", "disease", "illness", "survival", "crisis")
        )
        has_counterforce = (
            any(c.role == CharacterRole.ANTAGONIST for c in state.characters.values()) or
            len(state.world.rules_and_lore) > 0 or
            has_systemic_counterforce or
            any("conflict" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "retribution" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "debt" in (getattr(p, 'plant_name', None) or p.element_code).lower() for p in state.plants)
        )
        has_relationships = any(len(c.relationships) > 0 for c in state.characters.values())

        # Anchor types present
        anchor_types = {getattr(e, 'anchor_type', None) for e in all_events if getattr(e, 'anchor_type', None)}
        explicit_ending = getattr(state, "explicit_ending_declared", False)
        if explicit_ending:
            anchor_types.add("RESOLUTION")

        num_events = len(all_events)

        for dep in existing_dependencies:
            if dep.status in (DependencyStatus.RESOLVED, DependencyStatus.DEFERRED, DependencyStatus.DELIBERATELY_UNKNOWN):
                continue

            key = dep.dependency_key
            is_satisfied = False

            # Premise & Logline
            if key == "PREMISE_LOGLINE_SPECIFICATION" and logline_valid:
                is_satisfied = True

            # Protagonist definition
            elif key == "PREMISE_PROTAGONIST_DEFINITION" and len(state.characters) > 0:
                is_satisfied = True

            # Character motivations
            elif key.startswith("CHAR_MOTIVATION_"):
                target = dep.target_entity or key.replace("CHAR_MOTIVATION_", "")
                target_norm = target.replace("_", " ").lower()
                for c in state.characters.values():
                    if c.name.lower() == target_norm or c.name.upper().replace(" ", "_") == target.upper():
                        if c.core_motivation and c.core_motivation.strip():
                            is_satisfied = True
                            break

            # Counterforce
            elif key == "PREMISE_COUNTERFORCE_DEFINITION" and has_counterforce:
                is_satisfied = True

            # Relationship dynamic
            elif key.startswith("REL_"):
                parts = key.split("_")
                if len(parts) >= 3:
                    c1_key = parts[1].lower()
                    c2_key = parts[2].lower()
                    c1_obj = next((c for c in state.characters.values() if c.name.lower() == c1_key or c.name.upper().replace(" ", "_") == parts[1]), None)
                    c2_obj = next((c for c in state.characters.values() if c.name.lower() == c2_key or c.name.upper().replace(" ", "_") == parts[2]), None)
                    if c1_obj and c2_obj:
                        has_link = any(r.target_character.lower() == c2_obj.name.lower() for r in c1_obj.relationships) or \
                                   any(r.target_character.lower() == c1_obj.name.lower() for r in c2_obj.relationships)
                        if has_link:
                            is_satisfied = True
                    elif has_relationships:
                        is_satisfied = True
                elif has_relationships:
                    is_satisfied = True
            elif key == "RELATIONSHIP_DYNAMIC_CORE" and has_relationships:
                is_satisfied = True

            # World rules
            elif key == "WORLD_RULE_SPECIFICATION":
                if len(state.world.rules_and_lore) > 0 or any("supernatural" in (c.core_motivation or "").lower() for c in state.characters.values()):
                    is_satisfied = True

            # Chronology anchors
            elif key.startswith("EVENT_01_INCITING_DISRUPTION"):
                if "INCITING_DISRUPTION" in anchor_types or num_events >= 1:
                    is_satisfied = True
            elif key.startswith("EVENT_02_POINT_OF_NO_RETURN"):
                if "POINT_OF_NO_RETURN" in anchor_types or num_events >= 2:
                    is_satisfied = True
            elif key.startswith("EVENT_03_MIDPOINT_REVELATION"):
                if "MIDPOINT_REVELATION" in anchor_types or num_events >= 3:
                    is_satisfied = True
            elif key.startswith("EVENT_04_DARK_NIGHT"):
                if "DARK_NIGHT" in anchor_types or num_events >= 4:
                    is_satisfied = True
            elif key.startswith("EVENT_05_CLIMAX"):
                if "CLIMAX" in anchor_types or num_events >= 5:
                    is_satisfied = True
            elif key.startswith("EVENT_06_RESOLUTION"):
                if "RESOLUTION" in anchor_types or explicit_ending or num_events >= 6:
                    is_satisfied = True

            # If explicit ending was declared and story arc has established events (>= 3 beats):
            # All remaining event spine dependencies are satisfied!
            if explicit_ending and num_events >= 3 and key.startswith("EVENT_0"):
                is_satisfied = True

            # Narrative plants
            elif key.startswith("PLANT_PAYOFF_LINK_"):
                plant_target = dep.target_entity.lower()
                for p in state.plants:
                    p_name = (getattr(p, 'plant_name', None) or p.element_code).lower()
                    if p_name == plant_target and (p.intended_payoff or p.payoff_status != "PLANTED"):
                        is_satisfied = True
                        break

            if is_satisfied:
                dep.status = DependencyStatus.RESOLVED
                resolved_deps.append(dep)

        return resolved_deps

    def evaluate_required_state_deficiencies(
        self,
        state: StoryState,
        events: Optional[List[ChronologyEvent]] = None,
        existing_dependencies: Optional[List[Dependency]] = None
    ) -> List[Dependency]:
        """
        Synthesizes required dependencies based on REQUIRED_STATE_SCHEMA_v0.1.
        Idempotent: Inspects existing dependencies to guarantee zero duplicate synthesis.
        Chronology is evaluated from canonical StoryState.
        """
        synthesized: List[Dependency] = []
        existing_keys = set(d.dependency_key for d in (existing_dependencies or []))
        chronology = state.chronology if (hasattr(state, 'chronology') and state.chronology) else (events or [])

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
        logline_text = (state.logline or "").lower()
        has_systemic_counterforce = any(
            term in logline_text
            for term in ("drought", "famine", "blizzard", "storm", "corruption", "poverty", "syndicate", "debt", "disaster", "opposing", "enemy", "rival", "disease", "illness", "survival", "crisis")
        )
        has_counterforce = (
            any(c.role == CharacterRole.ANTAGONIST for c in state.characters.values()) or
            len(state.world.rules_and_lore) > 0 or
            has_systemic_counterforce or
            any("conflict" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "retribution" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "debt" in (getattr(p, 'plant_name', None) or p.element_code).lower() for p in state.plants)
        )
        if not has_counterforce:
            add_required(
                "PREMISE_COUNTERFORCE_DEFINITION",
                DependencyType.CHARACTER,
                "COUNTERFORCE",
                "A grounded counterforce (opposing character, rival faction, institution, or external pressure) must be defined.",
                SkillEnum.CONNECTOR,
                impact=9, urgency=8
            )

        # 3. Relationship Dynamic
        has_relationships = any(len(c.relationships) > 0 for c in state.characters.values())
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
                "Supernatural rules, operating conditions, limits and consequences must be anchored in state.",
                SkillEnum.PROPAGATOR,
                impact=8, urgency=7
            )

        # If M1 deficiencies exist (characters missing or incomplete), do not advance to M2 synthesis yet
        protagonists = [c for c in state.characters.values() if c.role == CharacterRole.PROTAGONIST or (len(state.characters) == 1 and c.status == StateStatus.FACT)]
        has_valid_protagonist = len(protagonists) > 0 and all(bool(c.core_motivation and c.core_motivation.strip()) for c in state.characters.values())
        if not has_valid_protagonist or not has_counterforce or synthesized:
            return synthesized

        # ---------------------------------------------------------------------
        # M2: EPISODIC_ARC_LOCK Deficiencies (Structural Chronology Anchors)
        # ---------------------------------------------------------------------
        explicit_ending = getattr(state, "explicit_ending_declared", False)

        # If explicit ending was declared and story arc has established events (>= 3 beats):
        # The six anchors are structural requirements, satisfied by opening + progression + resolution.
        if explicit_ending and len(chronology) >= 3:
            pass  # Structural arc satisfied
        elif len(chronology) >= 6:
            pass  # 6 distinct chronological anchors satisfied
        else:
            existing_anchor_types = {getattr(e, 'anchor_type', None) for e in chronology if getattr(e, 'anchor_type', None)}
            if explicit_ending:
                existing_anchor_types.add("RESOLUTION")

            six_canonical_anchors = [
                ("INCITING_DISRUPTION", "EVENT_01_INCITING_DISRUPTION", "Inciting Disruption: Core event that disrupts the protagonist's status quo and establishes narrative stakes."),
                ("POINT_OF_NO_RETURN", "EVENT_02_POINT_OF_NO_RETURN", "Point of No Return: Protagonist commits to the dramatic goal and crosses the threshold into the active arena."),
                ("MIDPOINT_REVELATION", "EVENT_03_MIDPOINT_REVELATION", "Midpoint Revelation: Critical truth surfaces or counterforce threat escalates, shifting dramatic dynamics."),
                ("DARK_NIGHT", "EVENT_04_DARK_NIGHT", "Dark Night / Low Point: Stakes climax, central vulnerability exposed, and success seems unattainable."),
                ("CLIMAX", "EVENT_05_CLIMAX", "Climax: Decisive confrontation between protagonist and counterforce resolving core dramatic tension."),
                ("RESOLUTION", "EVENT_06_RESOLUTION", "Resolution: Final consequences manifest, cost is realized, and a new status quo is established.")
            ]

            for idx, (anchor_type, anchor_key, anchor_desc) in enumerate(six_canonical_anchors):
                if anchor_type not in existing_anchor_types and len(chronology) <= idx:
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

    @classmethod
    def format_targeted_deficiency_question(cls, dep: Dependency, state: StoryState) -> str:
        """
        Produces an exact, targeted creative question for a specific narrative requirement.
        Zero machine ontology or generic placeholders are permitted.
        """
        key = dep.dependency_key
        protagonist_name = "the protagonist"
        for c in state.characters.values():
            if c.role == CharacterRole.PROTAGONIST:
                protagonist_name = c.name
                break

        if key == "PREMISE_LOGLINE_SPECIFICATION":
            return "What is the core premise and primary dramatic conflict of this story?"

        if key == "PREMISE_PROTAGONIST_DEFINITION":
            return "Who is the central character, and what is their situation at the start of the story?"

        if key.startswith("CHAR_MOTIVATION_"):
            char_name = dep.target_entity or key.replace("CHAR_MOTIVATION_", "").replace("_", " ").title()
            return f"What does {char_name} really want, and what are they afraid will happen if they fail?"

        if key == "PREMISE_COUNTERFORCE_DEFINITION":
            return f"Who is standing in {protagonist_name}'s way?"

        if key.startswith("REL_") or key == "RELATIONSHIP_DYNAMIC_CORE":
            return f"What is the friction or emotional tension between {protagonist_name} and the people around them?"

        if key == "WORLD_RULE_SPECIFICATION":
            return "What are the unspoken rules, boundaries, or dangers of this world that the characters must live with?"

        if key.startswith("EVENT_01_INCITING_DISRUPTION"):
            return f"What unexpected event shatters {protagonist_name}'s ordinary world and starts this story?"

        if key.startswith("EVENT_02_POINT_OF_NO_RETURN"):
            return f"What choice does {protagonist_name} make that means there is no going back?"

        if key.startswith("EVENT_03_MIDPOINT_REVELATION"):
            return f"What surprising revelation or shift happens halfway through that raises the stakes for {protagonist_name}?"

        if key.startswith("EVENT_04_DARK_NIGHT"):
            return f"What is {protagonist_name}'s lowest moment, where everything seems lost?"

        if key.startswith("EVENT_05_CLIMAX"):
            return f"How does the decisive final showdown unfold for {protagonist_name}?"

        if key.startswith("EVENT_06_RESOLUTION"):
            return f"When the dust settles, how has {protagonist_name}'s world permanently changed?"

        if key.startswith("PLANT_PAYOFF_LINK_"):
            return f"How does the story pay off '{dep.target_entity}' in a surprising or dramatic way?"

        # Fallback to targeted description
        return f"How does '{dep.target_entity or 'this part of the story'}' develop?"



