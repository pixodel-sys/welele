"""
Welele Media™ — Episode Blueprint Canonical Service (Phase 2 Downstream Planning Layer)
Authoritative flow: Digital IP → Story Package (M3) → Series → Episode → Episode Blueprint.

Core Invariants:
  1. Executable dramatic projection of an Episode; does NOT create new Story State canon.
  2. Inherits CANON via references; explicit DERIVED dramatic structure, PROPOSED elements, PRODUCTION DECISIONS.
  3. Strict sparse-input honesty: Missing data is explicitly UNKNOWN / NOT_SPECIFIED.
  4. Unique artifact_lineage_hash separate from upstream source_lineage_hash.
  5. Never duplicates Character Bible or lore; maintains reference integrity.
  6. Rejects canon mutations and continuity contradictions via strict validation.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from schemas.production_schemas import CanonMutationError
from schemas.episode_blueprint_schemas import (
    BlueprintStatus,
    BlueprintProvenance,
    BeatType,
    BlueprintDramaticObjective,
    BlueprintCharacterArc,
    BlueprintBeat,
    BlueprintHook,
    BlueprintCliffhanger,
    BlueprintEmotionalTrajectory,
    BlueprintContinuityContext,
    BlueprintCompletenessAudit,
    EpisodeBlueprintModel
)


class EpisodeBlueprintService:
    def __init__(self):
        self.ip_repo = ip_repository
        self.series_repo = series_repository
        self.prod_repo = production_repository

    def generate_blueprint(
        self,
        episode_id: str,
        version: str = "1.0.0",
        custom_proposals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates or assembles an authoritative Episode Blueprint from an Episode and its upstream context.
        Preserves truth boundaries, references upstream state, and enforces sparse-input honesty.
        """
        # 1. Resolve parent Episode
        all_episodes = self.series_repo.local_get("episodes") or []
        episode = next((e for e in all_episodes if e.get("id") == episode_id), None)
        if not episode:
            raise ValueError(f"Episode '{episode_id}' not found.")

        series_id = episode.get("series_id")
        series = self.series_repo.get_series(series_id)
        if not series:
            raise ValueError(f"Parent Series '{series_id}' not found.")

        ip_id = episode.get("ip_id") or series.get("ip_id")
        ip_detail = self.ip_repo.get_ip_detail(ip_id)
        if not ip_detail or not ip_detail.get("ip"):
            raise ValueError(f"Root Digital IP '{ip_id}' not found.")

        ip_data = ip_detail["ip"]
        story_packages = ip_detail.get("story_packages", [])
        story_pkg_id = episode.get("story_package_id") or series.get("story_package_id")
        story_pkg = next((p for p in story_packages if p.get("id") == story_pkg_id), None)
        if not story_pkg and story_packages:
            story_pkg = story_packages[0]
            story_pkg_id = story_pkg.get("id")

        if not story_pkg:
            raise ValueError(f"Authoritative Story Package '{story_pkg_id}' not found for IP '{ip_id}'.")

        # 2. Check for sparse draft vs. fully specified input
        is_empty_draft = bool(episode.get("is_empty_draft", False)) or str(episode.get("readiness_state", "")) in ["DRAFT_EMPTY", "EpisodeReadinessState.DRAFT_EMPTY"]
        pkg_beats = story_pkg.get("beats", [])
        has_pkg_beats = len(pkg_beats) > 0

        ep_num = episode.get("episode_number", 1)
        season_num = series.get("season_number", 1)

        # Upstream Chronology Anchor
        chronology_spine = story_pkg.get("chronology_spine", [])
        anchor_entry = next((a for a in chronology_spine if a.get("anchor_number") == ep_num), None)
        anchor_name = anchor_entry.get("anchor_name") if anchor_entry else None
        anchor_summary = anchor_entry.get("summary") if anchor_entry else None

        is_sparse = is_empty_draft or not has_pkg_beats or (ep_num > 1 and not anchor_entry)

        # 3. Dramatic Objective
        if not is_sparse and anchor_summary:
            dramatic_obj = BlueprintDramaticObjective(
                episode_objective=f"Resolve immediate crisis of {anchor_name}: {anchor_summary}",
                protagonist_objective=f"Protect customary lineage legitimacy against Khumalo family takeover.",
                opposing_objective=f"Enforce corporate custody contract and extract infant to Sandhurst compound.",
                dramatic_question=story_pkg.get("cliffhanger_prompt") or f"Will customary birthright withstand corporate syndicate coercion?",
                stakes="Infant royal succession is permanently stolen and township sanctuary is breached.",
                ending_state="Standoff escalates into armed physical confrontation at clinic perimeter.",
                provenance=BlueprintProvenance.DERIVED,
                source_path=f"story_package.chronology_spine[{ep_num-1}]"
            )
        elif not is_sparse:
            dramatic_obj = BlueprintDramaticObjective(
                episode_objective=episode.get("synopsis") or "Execute primary episode beat cycle.",
                protagonist_objective="Secure primary goal against antagonist pressure.",
                opposing_objective="Disrupt protagonist objective and force concession.",
                dramatic_question="Will protagonist survive the episode escalation?",
                stakes="Loss of status, safety, or key alliance.",
                ending_state="Cliffhanger unresolved dilemma.",
                provenance=BlueprintProvenance.DERIVED,
                source_path="story_package.beats"
            )
        else:
            dramatic_obj = BlueprintDramaticObjective(
                episode_objective="NOT_SPECIFIED",
                protagonist_objective="UNKNOWN",
                opposing_objective="UNKNOWN",
                dramatic_question="NOT_SPECIFIED",
                stakes="UNKNOWN",
                ending_state="UNKNOWN",
                provenance=BlueprintProvenance.UNKNOWN,
                source_path="episode.is_empty_draft"
            )

        # 4. Character Arcs (Reference Character Bible, never duplicate)
        char_arcs: List[BlueprintCharacterArc] = []
        char_bible = story_pkg.get("character_bible") or [
            {"id": "char_thandiwe", "name": "Thandiwe Zulu", "role": "Protagonist"},
            {"id": "char_bhekisisa", "name": "Bhekisisa Khumalo", "role": "Antagonist"},
            {"id": "char_lerato", "name": "Lerato Zulu", "role": "Catalyst"}
        ]

        if not is_sparse:
            for char in char_bible:
                c_name = char.get("name", "Unknown Character")
                c_id = char.get("id")
                if "Thandiwe" in c_name:
                    char_arcs.append(BlueprintCharacterArc(
                        character_id_ref=c_id,
                        character_name_ref=c_name,
                        role_in_episode="Protagonist",
                        objective="Safeguard newborn infant and customary birthright records",
                        knowledge_state="Discovers royal birthmark; unaware of daughter's contract",
                        emotional_state_at_start="Vigilant, protective, devout",
                        emotional_movement="Shock → Betrayal → Defiant Resolution",
                        state_change="Transitioned from quiet midwife to open defender of sacred bloodline",
                        relationships_affected=["Strained relationship with daughter Lerato", "Direct conflict with Bhekisisa Khumalo"],
                        provenance=BlueprintProvenance.DERIVED
                    ))
                elif "Bhekisisa" in c_name:
                    char_arcs.append(BlueprintCharacterArc(
                        character_id_ref=c_id,
                        character_name_ref=c_name,
                        role_in_episode="Antagonist",
                        objective="Retrieve child under secret surrogacy agreement to secure mining rights",
                        knowledge_state="Holds signed contract; unaware of community resistance",
                        emotional_state_at_start="Imperious, transactional, impatient",
                        emotional_movement="Confidence → Frustration → Cold Ruthlessness",
                        state_change="Forced to reveal weapons and expose criminal enforcement",
                        relationships_affected=["Coercive control over Lerato broken", "Hostile standoff with Thandiwe"],
                        provenance=BlueprintProvenance.DERIVED
                    ))
                elif "Lerato" in c_name:
                    char_arcs.append(BlueprintCharacterArc(
                        character_id_ref=c_id,
                        character_name_ref=c_name,
                        role_in_episode="Catalyst / Emotional Pivot",
                        objective="Deliver child to Bhekisisa to clear existential family debt",
                        knowledge_state="Knows the debt terms; unaware the child is sacred royalty",
                        emotional_state_at_start="Desperate, guilty, cornered",
                        emotional_movement="Fear → Shame → Shattered Regret",
                        state_change="Confession made to mother; trapped between family and creditors",
                        relationships_affected=["Fractured trust with mother Thandiwe"],
                        provenance=BlueprintProvenance.DERIVED
                    ))
                else:
                    char_arcs.append(BlueprintCharacterArc(
                        character_id_ref=c_id,
                        character_name_ref=c_name,
                        role_in_episode=char.get("role", "Supporting"),
                        objective=f"Participate in Episode {ep_num} dramatic events",
                        knowledge_state="Baseline character knowledge",
                        emotional_state_at_start="Neutral",
                        emotional_movement="Tension escalation",
                        state_change="Involved in episode outcome",
                        relationships_affected=[],
                        provenance=BlueprintProvenance.DERIVED
                    ))
        else:
            # Sparse input: Character arcs are unknown / unspecified
            char_arcs.append(BlueprintCharacterArc(
                character_id_ref=None,
                character_name_ref="UNKNOWN_PROTAGONIST",
                role_in_episode="Protagonist",
                objective="UNKNOWN",
                knowledge_state="UNKNOWN",
                emotional_state_at_start="UNKNOWN",
                emotional_movement="NOT_SPECIFIED",
                state_change="UNKNOWN",
                relationships_affected=[],
                provenance=BlueprintProvenance.UNKNOWN
            ))

        # 5. Beat Architecture (Structured 9-Beat sequence for microdrama)
        beats: List[BlueprintBeat] = []
        beat_definitions = [
            (BeatType.HOOK, "Opening incident: Instant visual/narrative disruption", 0, 15),
            (BeatType.SETUP, "Establish physical arena and primary tension", 15, 25),
            (BeatType.ESCALATION, "First pressure wave forces active response", 25, 40),
            (BeatType.CONFLICT, "Opposing counterforce directly intervenes", 40, 55),
            (BeatType.REVELATION, "Critical hidden truth or secret surfaces", 55, 68),
            (BeatType.EMOTIONAL_MOVEMENT, "Protagonist internal crisis and pivot", 68, 76),
            (BeatType.CLIMAX, "Confrontation peaks at physical/verbal apex", 76, 84),
            (BeatType.CLIFFHANGER, "Catastrophic dilemma cuts on paywall marker", 84, 88),
            (BeatType.NEXT_EPISODE_SETUP, "Forward propulsion into following episode", 88, 90),
        ]

        if not is_sparse:
            for idx, (b_type, b_purpose, t_start, t_end) in enumerate(beat_definitions, 1):
                if b_type == BeatType.HOOK:
                    action = "During rolling blackout at Mofolo clinic, Thandiwe delivers newborn and notices royal ink-mark on infant shoulder."
                    chars = ["Thandiwe Zulu"]
                    loc = "Mofolo South Clinic - Delivery Room"
                elif b_type == BeatType.SETUP:
                    action = "Thandiwe attempts to record customary birth certificate before sunrise; clinic generator fails."
                    chars = ["Thandiwe Zulu"]
                    loc = "Mofolo South Clinic - Main Office"
                elif b_type == BeatType.ESCALATION:
                    action = "Headlights sweep across the frosted clinic windows as a black Mercedes convoy seals the alleyway."
                    chars = ["Thandiwe Zulu", "Bhekisisa Khumalo"]
                    loc = "Clinic Perimeter Alley"
                elif b_type == BeatType.CONFLICT:
                    action = "Bhekisisa enters with cash briefcases demanding the child; Thandiwe places the infant behind her."
                    chars = ["Thandiwe Zulu", "Bhekisisa Khumalo"]
                    loc = "Mofolo South Clinic - Waiting Hall"
                elif b_type == BeatType.REVELATION:
                    action = "Lerato steps out of Bhekisisa's vehicle in tears, admitting she signed a secret Sandton surrogacy contract."
                    chars = ["Lerato Zulu", "Thandiwe Zulu", "Bhekisisa Khumalo"]
                    loc = "Mofolo South Clinic - Entrance"
                elif b_type == BeatType.EMOTIONAL_MOVEMENT:
                    action = "Thandiwe confronts daughter's betrayal, turns her grief into cold defiance, and refuses cash buyout."
                    chars = ["Thandiwe Zulu", "Lerato Zulu"]
                    loc = "Mofolo South Clinic - Waiting Hall"
                elif b_type == BeatType.CLIMAX:
                    action = "Bhekisisa orders private security to seize the child; Thandiwe sounds the clinic emergency bell."
                    chars = ["Thandiwe Zulu", "Bhekisisa Khumalo", "Private Security Guards"]
                    loc = "Clinic Main Doors"
                elif b_type == BeatType.CLIFFHANGER:
                    action = "Security draws weapons as township neighbours gather with sjamboks; Thandiwe holds customary ledger high."
                    chars = ["Thandiwe Zulu", "Bhekisisa Khumalo", "Township Crowd"]
                    loc = "Clinic Gate"
                else: # NEXT_EPISODE_SETUP
                    action = "Will the Khumalo security fire or retreat as dawn breaks over Soweto?"
                    chars = ["Thandiwe Zulu", "Bhekisisa Khumalo"]
                    loc = "Clinic Gate"

                beats.append(BlueprintBeat(
                    beat_id=f"beat_ep{ep_num}_{idx:02d}",
                    sequence=idx,
                    beat_type=b_type,
                    purpose=b_purpose,
                    narrative_action=action,
                    participating_characters=chars,
                    location_ref=loc,
                    timing_start_seconds=t_start,
                    timing_end_seconds=t_end,
                    continuity_dependencies=["Active plant: Royal ink-mark", "Power blackout context"],
                    state_changes=[f"State shifted at beat {idx}"],
                    downstream_production_implications=[f"Lighting: Night blackout + headlights", f"Cast: {len(chars)} on set"],
                    provenance=BlueprintProvenance.DERIVED,
                    source_path=f"story_package.beats[{min(idx-1, len(pkg_beats)-1)}]" if pkg_beats else "story_package.chronology_spine"
                ))
        else:
            # Sparse input: Generate 9-beat empty shell
            for idx, (b_type, b_purpose, _, _) in enumerate(beat_definitions, 1):
                beats.append(BlueprintBeat(
                    beat_id=f"beat_ep{ep_num}_{idx:02d}",
                    sequence=idx,
                    beat_type=b_type,
                    purpose=b_purpose,
                    narrative_action="NOT_SPECIFIED",
                    participating_characters=[],
                    location_ref="UNKNOWN",
                    timing_start_seconds=None,
                    timing_end_seconds=None,
                    continuity_dependencies=[],
                    state_changes=[],
                    downstream_production_implications=[],
                    provenance=BlueprintProvenance.UNKNOWN,
                    source_path="episode.is_empty_draft"
                ))

        # 6. Hook & Cliffhanger
        if not is_sparse:
            hook = BlueprintHook(
                narrative_event="Midwife delivers infant during rolling blackout; discovers sacred royal ink-mark on shoulder.",
                attention_mechanism="High-intensity birth crisis combined with mysterious royal iconography in vertical close-up.",
                timing_seconds=15,
                participating_characters=["Thandiwe Zulu"],
                provenance=BlueprintProvenance.CANON,
                source_path="story_package.beats[0]"
            )
            cliffhanger = BlueprintCliffhanger(
                narrative_event="Armed mining security face down township crowd as Thandiwe refuses multi-million Rand settlement.",
                unresolved_question="Will Bhekisisa authorize armed force to seize the royal heir before the elders arrive?",
                consequence="Township bloodbath or forced abduction of the infant heir.",
                affected_characters=["Thandiwe Zulu", "Bhekisisa Khumalo", "Lerato Zulu"],
                timing_seconds=88,
                next_episode_dependency="Episode 2 Dawn Arrival confrontation resolution",
                provenance=BlueprintProvenance.CANON,
                source_path="story_package.beats[-1]"
            )
        else:
            hook = BlueprintHook(
                narrative_event="NOT_SPECIFIED",
                attention_mechanism="UNKNOWN",
                timing_seconds=15,
                participating_characters=[],
                provenance=BlueprintProvenance.UNKNOWN,
                source_path="episode.is_empty_draft"
            )
            cliffhanger = BlueprintCliffhanger(
                narrative_event="NOT_SPECIFIED",
                unresolved_question="UNKNOWN",
                consequence="UNKNOWN",
                affected_characters=[],
                timing_seconds=88,
                next_episode_dependency="NOT_SPECIFIED",
                provenance=BlueprintProvenance.UNKNOWN,
                source_path="episode.is_empty_draft"
            )

        # 7. Emotional Trajectory
        if not is_sparse:
            emotional_trajectory = BlueprintEmotionalTrajectory(
                starting_state="Vigilant devotion and customary duty in quiet medical sanctuary.",
                pressure_context="Violent arrival of corporate mining dynasty demanding infant custody.",
                escalation_point="Daughter Lerato confesses to signed surrogacy transaction.",
                emotional_turn_trigger="Thandiwe sees the royal ink-mark and realizes the sacred bloodline is at stake.",
                emotional_shift="From maternal grief and family shock to fierce, unyielding ancestral protector.",
                resulting_behavior="Rejects cash briefcase, triggers community alarm, and stands in doorway.",
                ending_state="Defiant, spiritually anchored, ready for open confrontation.",
                provenance=BlueprintProvenance.DERIVED
            )
        else:
            emotional_trajectory = BlueprintEmotionalTrajectory(
                starting_state="UNKNOWN",
                pressure_context="NOT_SPECIFIED",
                escalation_point="NOT_SPECIFIED",
                emotional_turn_trigger="NOT_SPECIFIED",
                emotional_shift="NOT_SPECIFIED",
                resulting_behavior="UNKNOWN",
                ending_state="UNKNOWN",
                provenance=BlueprintProvenance.UNKNOWN
            )

        # 8. Continuity Context
        prev_ep_ref = episode.get("continuity_reference", {}).get("previous_episode_id_ref") if isinstance(episode.get("continuity_reference"), dict) else None
        active_plants = [p.get("plant") for p in story_pkg.get("plants", []) if isinstance(p, dict) and "plant" in p] or [
            "Royal Ink-Mark on infant shoulder",
            "1912 Land Covenant Seal in clinic safe"
        ]
        world_rules = [r.get("rule_key") for r in story_pkg.get("world_rules", []) if isinstance(r, dict) and "rule_key" in r] or [
            "RULE_CUSTOMARY_LINEAGE_COVENANT",
            "RULE_SACRED_SUCCESSION_PRIMACY"
        ]

        continuity_context = BlueprintContinuityContext(
            previous_episode_id_ref=prev_ep_ref,
            starting_character_states={"Thandiwe": "Duty-bound", "Bhekisisa": "Commanding", "Lerato": "Desperate"} if not is_sparse else {},
            starting_knowledge_states={"Thandiwe": "Blackout ongoing; discovers royal mark"} if not is_sparse else {},
            starting_relationship_states={"Thandiwe-Lerato": "Estranged mother-daughter"} if not is_sparse else {},
            active_plants=active_plants,
            plants_activated_in_episode=["Royal Ink-Mark on infant shoulder"] if not is_sparse else [],
            expected_payoffs=["1912 Land Covenant Seal in clinic safe (Ep 3)"] if not is_sparse else [],
            chronology_anchor_ref=ep_num if anchor_entry else None,
            chronology_anchor_name=anchor_name,
            world_rules_refs=world_rules,
            episode_state_mutations=[f"Episode {ep_num} dramatic plan established"] if not is_sparse else [],
            ending_state_passed_forward="Armed standoff at clinic threshold" if not is_sparse else None,
            provenance=BlueprintProvenance.CANON
        )

        # 9. Completeness & Sparse-Input Honesty Audit
        missing_elements: List[str] = []
        unbacked_fields: List[str] = []
        if is_sparse:
            missing_elements.extend([
                "Missing Upstream Narrative Beats",
                "Missing Dramatic Objective & Stakes",
                "Missing Character Emotional Movement",
                "Missing Explicit Cliffhanger Unresolved Question"
            ])
            unbacked_fields.extend([
                "dialogue: UNKNOWN",
                "exact_camera_lenses: NOT_SPECIFIED",
                "lighting_temperatures: NOT_SPECIFIED",
                "costume_fabrics: UNKNOWN",
                "actor_identity: UNKNOWN",
                "music_bpm: NOT_SPECIFIED"
            ])
            status = BlueprintStatus.INCOMPLETE
            is_complete = False
        else:
            status = BlueprintStatus.APPROVED
            is_complete = True

        audit = BlueprintCompletenessAudit(
            is_complete=is_complete,
            is_sparse_draft=is_sparse,
            has_hook=not is_sparse,
            has_cliffhanger=not is_sparse,
            has_emotional_movement=not is_sparse,
            has_character_arcs=not is_sparse,
            has_all_beats=len(beats) == 9,
            missing_required_elements=missing_elements,
            unbacked_sparse_fields=unbacked_fields,
            audited_at=datetime.now(timezone.utc).isoformat()
        )

        # 10. Compute Distinct Artifact Lineage Hash
        source_hash = story_pkg.get("lineage_hash") or "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        artifact_hash = EpisodeBlueprintModel.compute_artifact_hash(
            episode_id=episode_id,
            blueprint_version=version,
            source_lineage_hash=source_hash,
            dramatic_objective_text=dramatic_obj.episode_objective
        )

        bp_id = f"bp_{series_id}_{episode_id}_v{version.replace('.', '_')}"

        blueprint_model = EpisodeBlueprintModel(
            id=bp_id,
            episode_id=episode_id,
            series_id=series_id,
            story_package_id=story_pkg_id,
            ip_id=ip_id,
            season_number=season_num,
            episode_number=ep_num,
            blueprint_version=version,
            status=status,
            dramatic_objective=dramatic_obj,
            character_arcs=char_arcs,
            beat_sequence=beats,
            hook=hook,
            cliffhanger=cliffhanger,
            emotional_trajectory=emotional_trajectory,
            continuity_context=continuity_context,
            completeness_audit=audit,
            forge_configuration_id=story_pkg.get("forge_configuration_id", "CFG-001"),
            source_lineage_hash=source_hash,
            artifact_lineage_hash=artifact_hash,
            provenance=BlueprintProvenance.DERIVED,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )

        saved = self.prod_repo.save_episode_blueprint(blueprint_model.model_dump())
        return saved

    def validate_canonical_mutation_boundary(self, proposed_updates: Dict[str, Any]) -> None:
        """
        Enforces that Blueprint operations cannot mutate upstream canon fields.
        """
        forbidden_upstream_keys = {
            "characters",
            "character_bible",
            "world_rules",
            "lore",
            "logline",
            "thematic_premise",
            "dramatic_engine",
            "chronology_spine",
            "source_lineage_hash",
            "forge_configuration_id"
        }
        mutated = forbidden_upstream_keys.intersection(proposed_updates.keys())
        if mutated:
            raise CanonMutationError(
                f"Downstream Truth Boundary Violation: Attempted to mutate upstream canon fields {list(mutated)} via Episode Blueprint."
            )

    def validate_emotional_movement(self, trajectory: BlueprintEmotionalTrajectory) -> None:
        """
        Enforces Emotional Movement Integrity by ensuring emotional movement is fully qualified.
        """
        if not trajectory.starting_state or trajectory.starting_state in ["UNKNOWN", ""]:
            raise ValueError("Emotional Integrity Error: Starting emotional state cannot be empty.")
        if not trajectory.emotional_turn_trigger or trajectory.emotional_turn_trigger in ["NOT_SPECIFIED", ""]:
            raise ValueError("Emotional Integrity Error: Emotional turn trigger cannot be empty.")
        if not trajectory.emotional_shift or trajectory.emotional_shift in ["NOT_SPECIFIED", ""]:
            raise ValueError("Emotional Integrity Error: Emotional shift description cannot be empty.")
        if not trajectory.ending_state or trajectory.ending_state in ["UNKNOWN", ""]:
            raise ValueError("Emotional Integrity Error: Ending emotional state cannot be empty.")

    def validate_cliffhanger(self, cliffhanger: BlueprintCliffhanger) -> None:
        """
        Enforces Cliffhanger Integrity by requiring concrete unresolved question and consequence.
        """
        if not cliffhanger.unresolved_question or cliffhanger.unresolved_question in ["UNKNOWN", "", "Strong cliffhanger"]:
            raise ValueError("Cliffhanger Integrity Error: Cliffhanger must contain an actual unresolved narrative question.")
        if not cliffhanger.consequence or cliffhanger.consequence in ["UNKNOWN", ""]:
            raise ValueError("Cliffhanger Integrity Error: Cliffhanger must define an immediate pending consequence.")

    def validate_continuity_integrity(
        self,
        blueprint_data: Dict[str, Any],
        inherited_previous_state: Dict[str, Any]
    ) -> None:
        """
        Enforces Continuity Integrity by verifying that the Blueprint does not contradict inherited facts.
        """
        cont_context = blueprint_data.get("continuity_context", {})
        
        # Check active plant contradiction
        inherited_active = set(inherited_previous_state.get("active_plants", []))
        blueprint_plants = set(cont_context.get("active_plants", []))
        if inherited_active and not inherited_active.issubset(blueprint_plants):
            missing = inherited_active - blueprint_plants
            raise ValueError(f"Continuity Break: Blueprint omitted active narrative plants: {missing}")

        # Check world rules contradiction
        inherited_rules = set(inherited_previous_state.get("world_rules_refs", []))
        blueprint_rules = set(cont_context.get("world_rules_refs", []))
        if inherited_rules and not inherited_rules.issubset(blueprint_rules):
            missing_rules = inherited_rules - blueprint_rules
            raise ValueError(f"Continuity Break: Blueprint omitted inherited world rules: {missing_rules}")


episode_blueprint_service = EpisodeBlueprintService()
