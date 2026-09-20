"""
Welele Story Forge™ — Forge Completion Judge
Assesses whether a Story Package is production-ready across hierarchical milestones:
M0: PREMISE_LOCK -> M1: DRAMATIC_ENGINE_LOCK -> M2: EPISODIC_ARC_LOCK -> M3: FORGE_COMPLETE
"""

from typing import Optional, List
from ..models import (
    StoryState,
    ForgeCompletionAssessment,
    MilestoneEnum,
    ReadinessStatus,
    DependencyStatus,
    CharacterRole,
    StateStatus
)
from ..repository import StoryForgeRepository


class ForgeJudge:
    def __init__(self, repository: StoryForgeRepository):
        self.repository = repository

    def assess(self, story_id: str, target_milestone: Optional[MilestoneEnum] = None) -> ForgeCompletionAssessment:
        state = self.repository.get_current_state(story_id)
        if not state:
            raise ValueError(f"Story {story_id} not found")

        target = target_milestone or MilestoneEnum.M3_FORGE_COMPLETE
        deps = self.repository.get_dependencies(story_id)
        prod_decisions = self.repository.get_production_decisions(story_id)
        events = (state.chronology if (hasattr(state, 'chronology') and state.chronology) else self.repository.get_events(story_id))

        unresolved_deps = [
            d for d in deps
            if d.status not in (DependencyStatus.RESOLVED, DependencyStatus.DELIBERATELY_UNKNOWN, DependencyStatus.DEFERRED)
        ]

        blocking_keys = [d.dependency_key for d in unresolved_deps]
        missing_invariants: List[str] = []
        satisfied_milestones: List[MilestoneEnum] = []

        # =====================================================================
        # MILESTONE 0: PREMISE_LOCK (M0)
        # =====================================================================
        m0_passed = True
        if not state.title or not state.title.strip():
            m0_passed = False
            missing_invariants.append("M0_TITLE_REQUIRED")
        if not state.logline or len(state.logline.strip()) < 20:
            m0_passed = False
            missing_invariants.append("M0_LOGLINE_REQUIRED")

        if m0_passed:
            satisfied_milestones.append(MilestoneEnum.M0_PREMISE_LOCK)

        # =====================================================================
        # MILESTONE 1: DRAMATIC_ENGINE_LOCK (M1)
        # =====================================================================
        m1_passed = m0_passed
        if m0_passed:
            # 1. Protagonist verification
            protagonists = [
                c for c in state.characters.values()
                if c.role == CharacterRole.PROTAGONIST or (len(state.characters) == 1 and c.status == StateStatus.FACT)
            ]
            has_valid_protagonist = len(protagonists) > 0 and all(bool(c.core_motivation and c.core_motivation.strip()) for c in state.characters.values())
            if not has_valid_protagonist:
                m1_passed = False
                missing_invariants.append("M1_PROTAGONIST_MOTIVATION_REQUIRED")

            # 2. Flexible Counterforce verification (Character, Institution, Supernatural Force, System)
            logline_text = (state.logline or "").lower()
            has_systemic_counterforce = any(
                term in logline_text
                for term in ("drought", "famine", "blizzard", "storm", "corruption", "poverty", "syndicate", "debt", "disaster", "opposing", "enemy", "rival", "disease", "illness", "survival", "crisis")
            )
            has_counterforce = (
                any(c.role == CharacterRole.ANTAGONIST for c in state.characters.values()) or
                len(state.world.rules_and_lore) > 0 or
                has_systemic_counterforce or
                any("debt" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "retribution" in (getattr(p, 'plant_name', None) or p.element_code).lower() or "conflict" in (getattr(p, 'plant_name', None) or p.element_code).lower() for p in state.plants)
            )
            if not has_counterforce:
                m1_passed = False
                missing_invariants.append("M1_COUNTERFORCE_REQUIRED")

            # 3. Relational dynamic / collision edge
            has_relationships = any(len(c.relationships) > 0 for c in state.characters.values())
            if not has_relationships:
                m1_passed = False
                missing_invariants.append("M1_RELATIONSHIP_DYNAMIC_REQUIRED")

            # 4. Supernatural / World Rules (if premise asserts supernatural/occult elements)
            logline_lower = (state.logline or "").lower()
            is_supernatural_premise = any(kw in logline_lower for kw in ("supernatural", "spirit", "ghost", "witchcraft", "occult", "curse", "blood pact", "demon", "magic"))
            if is_supernatural_premise:
                has_world_rules = len(state.world.rules_and_lore) > 0 or any("supernatural" in (c.core_motivation or "").lower() for c in state.characters.values())
                if not has_world_rules:
                    m1_passed = False
                    missing_invariants.append("M1_WORLD_RULES_REQUIRED")

            if m1_passed:
                satisfied_milestones.append(MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK)

        # =====================================================================
        # MILESTONE 2: EPISODIC_ARC_LOCK (M2)
        # =====================================================================
        m2_passed = m1_passed
        if m1_passed:
            # Six chronology anchors are structural requirements, not six mandatory manually-created event records.
            # Explicit endings are canonical narrative information and participate in completion evaluation.
            all_chronology = (state.chronology if (hasattr(state, 'chronology') and state.chronology) else events)
            explicit_ending = getattr(state, 'explicit_ending_declared', False)

            has_structural_arc = False
            if len(all_chronology) == 0:
                has_structural_arc = False
            elif len(all_chronology) >= 6:
                has_structural_arc = True
            elif explicit_ending and len(all_chronology) >= 3:
                has_structural_arc = True
            elif len(all_chronology) >= 3:
                anchor_types = {getattr(e, 'anchor_type', None) for e in all_chronology if getattr(e, 'anchor_type', None)}
                if explicit_ending:
                    anchor_types.add("RESOLUTION")
                core_anchors = {"INCITING_DISRUPTION", "POINT_OF_NO_RETURN", "MIDPOINT_REVELATION", "DARK_NIGHT", "CLIMAX", "RESOLUTION"}
                if len(anchor_types.intersection(core_anchors)) >= 4 and ("RESOLUTION" in anchor_types or explicit_ending):
                    has_structural_arc = True

            if not has_structural_arc:
                m2_passed = False
                missing_invariants.append(f"M2_SIX_CHRONOLOGY_ANCHORS_REQUIRED (structural arc incomplete: found {len(all_chronology)} events, explicit_ending={explicit_ending})")

            # Narrative plant payoff integrity
            has_unresolved_plants = any(
                p.payoff_status == "PLANTED" and not p.intended_payoff
                for p in state.plants
            )
            if has_unresolved_plants:
                m2_passed = False
                missing_invariants.append("M2_PLANT_PAYOFF_LINK_REQUIRED")

            if m2_passed:
                satisfied_milestones.append(MilestoneEnum.M2_EPISODIC_ARC_LOCK)

        # =====================================================================
        # MILESTONE 3: FORGE_COMPLETE (M3)
        # =====================================================================
        m3_passed = m2_passed and (len(unresolved_deps) == 0)
        if m2_passed:
            # Check production decisions if production constraints exist in logline/arena
            if len(prod_decisions) == 0 and ("locations" in logline_lower or "budget" in logline_lower or "micro-drama" in logline_lower):
                m3_passed = False
                missing_invariants.append("M3_PRODUCTION_DECISIONS_REQUIRED")

            # Substantive package validation: must not be an empty shell
            if len(state.characters) < 2 or not any(len(c.relationships) > 0 for c in state.characters.values()):
                m3_passed = False
                missing_invariants.append("M3_DRAMATIC_RELATIONSHIPS_REQUIRED")

            if len(all_chronology) == 0:
                m3_passed = False
                missing_invariants.append("M3_CHRONOLOGY_SPINE_REQUIRED")

            if m3_passed:
                satisfied_milestones.append(MilestoneEnum.M3_FORGE_COMPLETE)

        # Determine highest certified milestone
        current_milestone: Optional[MilestoneEnum] = None
        if MilestoneEnum.M3_FORGE_COMPLETE in satisfied_milestones:
            current_milestone = MilestoneEnum.M3_FORGE_COMPLETE
            status = ReadinessStatus.FORGE_COMPLETE
            notes = f"All 4 milestones (M0-M3) and {len(deps)} dependencies verified complete."
        elif MilestoneEnum.M2_EPISODIC_ARC_LOCK in satisfied_milestones:
            current_milestone = MilestoneEnum.M2_EPISODIC_ARC_LOCK
            status = ReadinessStatus.EPISODIC_ARC_LOCK
            notes = f"M0, M1, and M2 certified. Pending M3 production readiness."
        elif MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK in satisfied_milestones:
            current_milestone = MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK
            status = ReadinessStatus.DRAMATIC_ENGINE_LOCK
            notes = f"M0 and M1 certified. Pending M2 six-anchor chronology spine."
        elif MilestoneEnum.M0_PREMISE_LOCK in satisfied_milestones:
            current_milestone = MilestoneEnum.M0_PREMISE_LOCK
            status = ReadinessStatus.PREMISE_LOCK
            notes = f"M0 certified. Missing M1 dramatic engine invariants: {missing_invariants}."
        else:
            current_milestone = None
            status = ReadinessStatus.NOT_READY
            notes = f"Blocked by missing invariants: {missing_invariants} and {len(blocking_keys)} unresolved dependencies."

        # Filter missing invariants based on target milestone
        allowed_prefixes = ["M0_"]
        if target in (MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK, MilestoneEnum.M2_EPISODIC_ARC_LOCK, MilestoneEnum.M3_FORGE_COMPLETE):
            allowed_prefixes.append("M1_")
        if target in (MilestoneEnum.M2_EPISODIC_ARC_LOCK, MilestoneEnum.M3_FORGE_COMPLETE):
            allowed_prefixes.append("M2_")
        if target == MilestoneEnum.M3_FORGE_COMPLETE:
            allowed_prefixes.append("M3_")

        target_missing_invariants = [
            inv for inv in missing_invariants
            if any(inv.startswith(pfx) for pfx in allowed_prefixes)
        ]

        def dep_belongs_to_or_before(dep_key: str, target_m: MilestoneEnum) -> bool:
            is_m0 = "TITLE" in dep_key or "LOGLINE" in dep_key or "PREMISE" in dep_key
            is_m1 = is_m0 or "CHAR_" in dep_key or "PROTAGONIST" in dep_key or "COUNTERFORCE" in dep_key or "RELATIONSHIP" in dep_key or "WORLD_RULE" in dep_key
            is_m2 = is_m1 or dep_key.startswith("EVENT_") or "CHRONOLOGY" in dep_key or "PLANT_PAYOFF" in dep_key or "PAYOFF" in dep_key
            if target_m == MilestoneEnum.M0_PREMISE_LOCK:
                return is_m0
            elif target_m == MilestoneEnum.M1_DRAMATIC_ENGINE_LOCK:
                return is_m1
            elif target_m == MilestoneEnum.M2_EPISODIC_ARC_LOCK:
                return is_m2
            return True

        target_blocking_keys = [k for k in blocking_keys if dep_belongs_to_or_before(k, target)]
        for inv in target_missing_invariants:
            if inv not in target_blocking_keys:
                target_blocking_keys.append(inv)

        unresolved_narrative = len([d for d in unresolved_deps if d.dependency_type.value in ("NARRATIVE", "CHARACTER")])
        unresolved_causal = len([d for d in unresolved_deps if d.dependency_type.value == "CAUSAL"])
        unresolved_temporal = len([d for d in unresolved_deps if d.dependency_type.value in ("TEMPORAL", "KNOWLEDGE")])

        assessment = ForgeCompletionAssessment(
            story_id=story_id,
            assessed_state_version=state.state_version,
            status=status,
            current_milestone=current_milestone,
            target_milestone=target,
            satisfied_milestones=satisfied_milestones,
            missing_invariants=target_missing_invariants,
            unresolved_narrative_count=unresolved_narrative,
            unresolved_causal_count=unresolved_causal,
            unresolved_temporal_count=unresolved_temporal,
            production_decisions_count=len(prod_decisions),
            blocking_dependencies=target_blocking_keys,
            assessment_notes=notes
        )

        self.repository.save_completion_assessment(assessment)
        return assessment
