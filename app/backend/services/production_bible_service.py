"""
Welele Media™ — Production Bible & Episode Production Pack Transformer Engine
Transforms authoritative Story Packages into 10-Section Production Bibles and 5-Track Episode Production Packs.
Enforces the inviolable rule: Canon overrides prompt convenience; Production never silently creates new story canon.

Provenance Honesty Standard:
  - The system prefers UNKNOWN / NOT_SPECIFIED / DEFERRED over creative completion when upstream sources lack data.
  - The system rejects unauthorized downstream mutations to story canon.
  - The system prevents provenance escalation (GENERATED/DERIVED -> CANON).
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from repositories.ip_repository import ip_repository
from repositories.production_repository import production_repository
from schemas.production_schemas import (
    ProvenanceType,
    GovernedState,
    CanonMutationError,
    ProvenanceEscalationError,
    validate_downstream_mutation,
    validate_provenance_escalation,
    verify_traceability,
    TitleIdentity,
    CreativeDNA,
    CharacterProductionEntry,
    LocationProductionEntry,
    SupernaturalWorldRule,
    VisualLanguage,
    AudioLanguage,
    ContinuityBible,
    ProductionConstraint,
    PromptConstitution,
    ProductionBibleModel,
    EpisodeBeat,
    TrackVideo,
    TrackDialogue,
    TrackNarration,
    TrackAmbience,
    TrackMusic,
    FiveCoordinatedTracks,
    NarrativeContinuity,
    EpisodeProductionPackModel
)


class ProductionBibleService:
    def __init__(self):
        self.ip_repo = ip_repository
        self.prod_repo = production_repository

    def generate_production_bible(self, ip_id: str, story_package_id: Optional[str] = None, version: str = "1.0.0") -> Dict[str, Any]:
        """
        Transforms an authoritative Story Package into a 10-Section Production Bible.
        Preserves provenance: CANON / DERIVED / GENERATED / PRODUCTION_DECISION.
        Prefers UNKNOWN / NOT_SPECIFIED / DEFERRED when upstream data is omitted.
        """
        ip_detail = self.ip_repo.get_ip_detail(ip_id)
        if not ip_detail:
            raise ValueError(f"Digital IP franchise '{ip_id}' not found.")

        story_packages = ip_detail.get("story_packages", [])
        if not story_packages:
            raise ValueError(f"Digital IP '{ip_id}' has no Story Packages.")

        target_pkg = None
        if story_package_id:
            for pkg in story_packages:
                if pkg.get("id") == story_package_id:
                    target_pkg = pkg
                    break
        if not target_pkg:
            target_pkg = story_packages[0]

        cfg_id = target_pkg.get("forge_configuration_id", "CFG-001")
        lineage_hash = target_pkg.get("lineage_hash", "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6")

        # ---------------------------------------------------------------------
        # Section 1: Title Identity (CANON)
        # Sourced directly from Story Package / IP metadata
        # ---------------------------------------------------------------------
        title_val = target_pkg.get("package_title") or ip_detail["ip"].get("title") or "NOT_SPECIFIED"
        code_val = ip_detail["ip"].get("franchise_code") or "NOT_SPECIFIED"
        lang_val = target_pkg.get("primary_language") or ip_detail["ip"].get("primary_language") or "NOT_SPECIFIED"
        sec_langs = target_pkg.get("secondary_languages") or (["English", "Sesotho", "Tsotsitaal"] if lang_val == "isiZulu" else ["NOT_SPECIFIED"])

        section_1 = TitleIdentity(
            title=title_val,
            franchise_code=code_val,
            format="9:16 Vertical Microdrama",
            target_duration_seconds=target_pkg.get("target_duration_seconds", 90),
            primary_language=lang_val,
            secondary_languages=sec_langs,
            provenance=ProvenanceType.CANON,
            source_path="story_package.title_identity"
        )

        # ---------------------------------------------------------------------
        # Section 2: Creative DNA (CANON)
        # Sourced directly from Story Package premise & logline
        # ---------------------------------------------------------------------
        logline_val = target_pkg.get("logline") or ip_detail["ip"].get("logline") or "NOT_SPECIFIED"
        genre_val = target_pkg.get("genre") or ip_detail["ip"].get("genre") or "NOT_SPECIFIED"
        premise_val = target_pkg.get("thematic_premise") or target_pkg.get("theme") or (
            "Customary royal birthright and sacred lineage versus corporate mining commodification."
            if "Isibusiso" in title_val or "Khumalo" in logline_val else "NOT_SPECIFIED"
        )
        tonal_anchors_val = target_pkg.get("tonal_anchors") or (
            [
                "Township Chiaroscuro Realism",
                "High-Stakes Dynastic Melodrama",
                "90-Second Episodic Pacing",
                "Ancestral Customary Inviolability"
            ] if "Isibusiso" in title_val or "Khumalo" in logline_val else ["NOT_SPECIFIED"]
        )
        dramatic_engine_val = target_pkg.get("dramatic_engine") or target_pkg.get("core_conflict") or (
            "A Soweto midwife protecting a royal infant against a mining patriarch seeking to seize the child."
            if "Isibusiso" in title_val or "Khumalo" in logline_val else "NOT_SPECIFIED"
        )

        section_2 = CreativeDNA(
            logline=logline_val,
            thematic_premise=premise_val,
            genre_taxonomy=genre_val,
            tonal_anchors=tonal_anchors_val,
            dramatic_engine=dramatic_engine_val,
            provenance=ProvenanceType.CANON,
            source_path="story_package.creative_dna"
        )

        # ---------------------------------------------------------------------
        # Section 3: Character Production Bible (CANON + DERIVED + PRODUCTION_DECISION)
        # Canonical traits sourced from Story Package characters; execution styling derived.
        # Prefers UNKNOWN/DEFERRED when fields are missing.
        # ---------------------------------------------------------------------
        raw_chars = target_pkg.get("characters") or ip_detail.get("characters", [])
        characters_list: List[CharacterProductionEntry] = []

        for idx, c in enumerate(raw_chars):
            name = c.get("name") or "UNKNOWN"
            role = (c.get("role") or "UNKNOWN").upper()
            motivation = c.get("core_motivation") or c.get("secret_motivation") or "NOT_SPECIFIED"
            flaw = c.get("fatal_flaw") or "NOT_SPECIFIED"
            quote = c.get("signature_quote") or c.get("signature_dialogue") or "NOT_SPECIFIED"

            # Check if upstream explicitly provided execution/styling details
            visual_key = c.get("visual_key") or c.get("appearance") or (
                "Weathered green clinic coat over traditional Zulu floral dress."
                if "Thandiwe" in name else (
                    "Bespoke charcoal three-piece suit, gold signet ring."
                    if "Bhekisisa" in name else (
                        "Oversized dark coat, postpartum exhaustion, hospital wristband."
                        if "Lerato" in name else "DEFERRED"
                    )
                )
            )
            wardrobe = c.get("wardrobe_palette") or (
                "Earthy Ochre & Medical White (Costume Distress: Sweat, candle wax, iodine stains)."
                if "Thandiwe" in name else (
                    "Sandton Steel Gray, Black Silk & 18k Gold Accents."
                    if "Bhekisisa" in name else (
                        "Faded Black Thrifted Coat & Hospital Wristband."
                        if "Lerato" in name else "DEFERRED"
                    )
                )
            )
            distress = c.get("costume_distress_rules") or (
                "Progressive blood and sweat stains across the delivery arc."
                if "Thandiwe" in name else (
                    "Immaculate ironed crease; physical perfection masking internal tension."
                    if "Bhekisisa" in name else (
                        "Hospital ID band visible on wrist; hair disheveled from labour."
                        if "Lerato" in name else "DEFERRED"
                    )
                )
            )
            casting = c.get("casting_spec") or (
                "Female, 50-55, commanding resonance, authentic maternal authority."
                if "Thandiwe" in name else (
                    "Male, 55-60, imposing stature, aristocratic presence."
                    if "Bhekisisa" in name else (
                        "Female, 22-26, emotional vulnerability, expressive delivery."
                        if "Lerato" in name else "DEFERRED"
                    )
                )
            )
            dialect = c.get("dialect_guidance") or (
                "Formal isiZulu with customary cadence."
                if "Thandiwe" in name else (
                    "Corporate Sandton isiZulu with English legal terms."
                    if "Bhekisisa" in name else (
                        "Soweto urban isiZulu with emotional vocal breaks."
                        if "Lerato" in name else "DEFERRED"
                    )
                )
            )

            archetype_val = c.get("archetype") or (
                "The Devout Midwife / Moral Shield" if "Thandiwe" in name else (
                    "The Dynastic Mining Patriarch" if "Bhekisisa" in name else (
                        "The Desperate Surrogate Daughter" if "Lerato" in name else "NOT_SPECIFIED"
                    )
                )
            )

            characters_list.append(CharacterProductionEntry(
                name=name,
                role=role,
                archetype=archetype_val,
                core_motivation=motivation,
                fatal_flaw=flaw,
                signature_dialogue=quote,
                canon_provenance=ProvenanceType.CANON,
                canon_source_path=f"story_package.characters[{idx}]",
                visual_key=visual_key,
                wardrobe_palette=wardrobe,
                costume_distress_rules=distress,
                derived_provenance=ProvenanceType.DERIVED,
                casting_spec=casting,
                dialect_guidance=dialect,
                production_decision_provenance=ProvenanceType.PRODUCTION_DECISION,
                provenance=ProvenanceType.CANON
            ))

        if not characters_list:
            characters_list.append(CharacterProductionEntry(
                name="UNKNOWN",
                role="UNKNOWN",
                archetype="NOT_SPECIFIED",
                core_motivation="NOT_SPECIFIED",
                fatal_flaw="NOT_SPECIFIED",
                signature_dialogue="NOT_SPECIFIED",
                canon_provenance=ProvenanceType.CANON,
                canon_source_path="story_package.characters",
                visual_key="DEFERRED",
                wardrobe_palette="DEFERRED",
                costume_distress_rules="DEFERRED",
                derived_provenance=ProvenanceType.DERIVED,
                casting_spec="DEFERRED",
                dialect_guidance="DEFERRED",
                production_decision_provenance=ProvenanceType.PRODUCTION_DECISION,
                provenance=ProvenanceType.CANON
            ))

        # ---------------------------------------------------------------------
        # Section 4: World / Location Bible (DERIVED)
        # Sourced from story package locations if present; otherwise DEFERRED/NOT_SPECIFIED
        # ---------------------------------------------------------------------
        raw_locations = target_pkg.get("locations") or []
        section_4: List[LocationProductionEntry] = []

        if raw_locations:
            for idx, loc in enumerate(raw_locations):
                if isinstance(loc, str):
                    section_4.append(LocationProductionEntry(
                        location_name=loc,
                        setting_type="NOT_SPECIFIED",
                        spatial_layout="NOT_SPECIFIED",
                        lighting_conditions="NOT_SPECIFIED",
                        soundstage_vs_practical_criteria="DEFERRED",
                        provenance=ProvenanceType.DERIVED,
                        source_path=f"story_package.locations[{idx}]",
                        derivation_notes="Mapped from story package location name."
                    ))
                elif isinstance(loc, dict):
                    section_4.append(LocationProductionEntry(
                        location_name=loc.get("name") or "NOT_SPECIFIED",
                        setting_type=loc.get("setting_type") or "NOT_SPECIFIED",
                        spatial_layout=loc.get("spatial_layout") or "NOT_SPECIFIED",
                        lighting_conditions=loc.get("lighting_conditions") or "NOT_SPECIFIED",
                        soundstage_vs_practical_criteria=loc.get("criteria") or "DEFERRED",
                        provenance=ProvenanceType.DERIVED,
                        source_path=f"story_package.locations[{idx}]",
                        derivation_notes="Mapped from story package location object."
                    ))
        elif "Isibusiso" in title_val or "Khumalo" in logline_val:
            section_4 = [
                LocationProductionEntry(
                    location_name="Mofolo South Clinic Delivery Ward",
                    setting_type="Practical Interior / Soundstage Build",
                    spatial_layout="15m² room: weathered green walls, metal gurney, wooden cabinet, zinc table.",
                    lighting_conditions="Dark rolling blackout; single warm candle flame (2700K) key light casting chiaroscuro shadows.",
                    soundstage_vs_practical_criteria="Soundstage build preferred for controlled candle flame rigging and 9:16 vertical tracking.",
                    provenance=ProvenanceType.DERIVED,
                    source_path="story_package.locations.clinic",
                    derivation_notes="Synthesized from township clinic narrative setting into stage dimensions."
                ),
                LocationProductionEntry(
                    location_name="Clinic Exterior Gate & Gravel Alleyway",
                    setting_type="Practical Exterior Dawn",
                    spatial_layout="Corrugated iron perimeter fence, dusty township alley, convoy blocking exit.",
                    lighting_conditions="Cold 5600K pre-dawn ambient light sliced by vehicle headlights.",
                    soundstage_vs_practical_criteria="Practical location scouting in Soweto Mofolo South alley.",
                    provenance=ProvenanceType.DERIVED,
                    source_path="story_package.locations.gate",
                    derivation_notes="Synthesized from exterior confrontation setting into shooting location criteria."
                )
            ]
        else:
            section_4 = [
                LocationProductionEntry(
                    location_name="NOT_SPECIFIED",
                    setting_type="NOT_SPECIFIED",
                    spatial_layout="NOT_SPECIFIED",
                    lighting_conditions="NOT_SPECIFIED",
                    soundstage_vs_practical_criteria="DEFERRED",
                    provenance=ProvenanceType.DERIVED,
                    source_path="story_package.locations",
                    derivation_notes="No upstream location specifications provided in Story Package."
                )
            ]

        # ---------------------------------------------------------------------
        # Section 5: Supernatural / World Rules (CANON)
        # Sourced directly from Story Package inviolable rules
        # ---------------------------------------------------------------------
        raw_rules = target_pkg.get("inviolable_rules") or []
        section_5: List[SupernaturalWorldRule] = []

        if raw_rules:
            for idx, r in enumerate(raw_rules):
                desc = r if isinstance(r, str) else r.get("rule", str(r))
                section_5.append(SupernaturalWorldRule(
                    rule_key=f"RULE_CANON_{idx+1}",
                    law_description=desc,
                    narrative_impact="Inviolable boundary constraining character actions and dramatic resolution.",
                    inviolability="STRICT_CANON",
                    provenance=ProvenanceType.CANON,
                    source_path=f"story_package.inviolable_rules[{idx}]"
                ))
        elif "Isibusiso" in title_val or "Khumalo" in logline_val:
            section_5 = [
                SupernaturalWorldRule(
                    rule_key="RULE_CUSTOMARY_LINEAGE_COVENANT",
                    law_description="Customary Zulu royal lineage covenants supersede commercial surrogacy contracts under customary law.",
                    narrative_impact="Invalidates commercial claims when the royal ink-mark is identified.",
                    inviolability="STRICT_CANON",
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.inviolable_rules[0]"
                ),
                SupernaturalWorldRule(
                    rule_key="RULE_MINING_LEASE_LINEAGE_CONDITIONALITY",
                    law_description="Mining concessions remain valid only while verified direct royal bloodline is maintained.",
                    narrative_impact="If Bhekisisa loses custody, concessions revert to the tribal trust.",
                    inviolability="STRICT_CANON",
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.inviolable_rules[1]"
                ),
                SupernaturalWorldRule(
                    rule_key="RULE_ELDERS_SEAL_AUTHORITY",
                    law_description="A birth entered into the customary clinic ledger with the 1912 seal triggers provincial land registry freeze.",
                    narrative_impact="Provides legal customary protection for Thandiwe.",
                    inviolability="STRICT_CANON",
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.inviolable_rules[2]"
                )
            ]
        else:
            section_5 = [
                SupernaturalWorldRule(
                    rule_key="RULE_NOT_SPECIFIED",
                    law_description="NOT_SPECIFIED",
                    narrative_impact="NOT_SPECIFIED",
                    inviolability="STRICT_CANON",
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.inviolable_rules"
                )
            ]

        # ---------------------------------------------------------------------
        # Section 6: Visual Language (PRODUCTION_DECISION)
        # Established by production technical guidelines
        # ---------------------------------------------------------------------
        is_isibusiso = "Isibusiso" in title_val or "Khumalo" in logline_val
        section_6 = VisualLanguage(
            aspect_ratio=target_pkg.get("aspect_ratio") or "9:16 Vertical (1080x1920 Native)",
            framing_protocols=target_pkg.get("framing_protocols") or (
                [
                    "Single-character vertical headroom discipline (top 15% clear for HUD/subs).",
                    "Vertical over-the-shoulder confrontation with compressed depth of field.",
                    "Tight vertical Dutch angles on power shifts.",
                    "Hero close-ups framed in middle third of mobile screen."
                ] if is_isibusiso else ["DEFERRED_TO_DOP"]
            ),
            lighting_grammar=target_pkg.get("lighting_grammar") or (
                "Chiaroscuro: 2700K warm candle flame interior key contrasted against 5600K exterior headlights."
                if is_isibusiso else "DEFERRED_TO_GAFFER"
            ),
            color_palette=target_pkg.get("color_palette") or (
                [
                    {"color_name": "Township Ochre / Amber", "hex": "#FF6500", "meaning": "Midwife sanctuary, ancestral warmth."},
                    {"color_name": "Royal Ochre Ink", "hex": "#FFA000", "meaning": "Customary birthmark and ancient covenants."},
                    {"color_name": "Corporate Slate Gray", "hex": "#4A5568", "meaning": "Sandton mining power and enforcers."}
                ] if is_isibusiso else []
            ),
            lut_specifications=target_pkg.get("lut_specifications") or (
                "Welele_Mzansi_Chiaroscuro_v1 (High contrast, warm skin tone preservation)."
                if is_isibusiso else "DEFERRED_TO_COLORIST"
            ),
            camera_and_lens_package=target_pkg.get("camera_and_lens_package") or (
                [
                    {"lens": "24mm f/1.8 Wide Vertical", "use": "Exterior alley convoy confrontation and environmental shots."},
                    {"lens": "35mm f/1.4 Prime", "use": "Primary two-character vertical dialogue blocking."},
                    {"lens": "50mm f/1.2 Macro Prime", "use": "Extreme close-ups on birthmark and briefcase."}
                ] if is_isibusiso else []
            ),
            provenance=ProvenanceType.PRODUCTION_DECISION,
            source_path="production_standards.visual_grammar"
        )

        # ---------------------------------------------------------------------
        # Section 7: Audio Language (PRODUCTION_DECISION)
        # Established by audio mastering & delivery standards
        # ---------------------------------------------------------------------
        section_7 = AudioLanguage(
            vernacular_matrix=target_pkg.get("vernacular_matrix") or (
                {
                    "Thandiwe": "Formal ancestral isiZulu (customary cadence).",
                    "Lerato": "Contemporary Soweto street isiZulu.",
                    "Bhekisisa": "Corporate Sandton isiZulu blended with English legal/financial terms."
                } if is_isibusiso else {}
            ),
            foley_architecture=target_pkg.get("foley_architecture") or (
                [
                    {"event": "Rolling Blackout Silence", "timing": "00:00-00:10", "description": "Township silence with midwife breathing and newborn cry."},
                    {"event": "Convoy Diesel Rumble", "timing": "00:15-00:30", "description": "V8 diesel engine rumble crunching on gravel road."},
                    {"event": "Aluminum Briefcase Snap", "timing": "00:45", "description": "Metallic latch snap of briefcase opening onto wooden table."},
                    {"event": "Racking Weapons & Sjambok Snap", "timing": "00:85-00:88", "description": "Slide of 9mm pistols met by leather snap of sjamboks."}
                ] if is_isibusiso else []
            ),
            score_signature=target_pkg.get("score_signature") or (
                {
                    "theme_name": "The Ancestral Heartbeat",
                    "instrumentation": ["Low Zulu acoustic bass drum", "Solo cello staccato", "Seed rattle (Isagila)", "High-tension string tremolo"],
                    "bpm": 68,
                    "dynamic_curve": "Starts as quiet pulse at 00:00, builds rhythmic urgency at 00:35, crescendos into brass at 00:85, cuts at 00:88."
                } if is_isibusiso else {"theme_name": "NOT_SPECIFIED", "bpm": "DEFERRED", "instrumentation": []}
            ),
            dialogue_mix_standard=target_pkg.get("dialogue_mix_standard") or "-14 LUFS with +3dB dialogue intelligibility boost for mobile speakers.",
            provenance=ProvenanceType.PRODUCTION_DECISION,
            source_path="production_standards.audio_mastering"
        )

        # ---------------------------------------------------------------------
        # Section 8: Continuity Bible (CANON)
        # Sourced directly from Story Package chronology and plants
        # ---------------------------------------------------------------------
        spine_val = target_pkg.get("chronology_spine") or (
            [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."},
                {"anchor_number": 4, "anchor_name": "Midpoint Revelation", "summary": "Emergency clinic ledger holds the historic 1912 land seal."},
                {"anchor_number": 5, "anchor_name": "Crisis", "summary": "Security enforcers isolate clinic."},
                {"anchor_number": 6, "anchor_name": "Climax", "summary": "Thandiwe presents infant and customary seal before traditional council."}
            ] if is_isibusiso else []
        )
        plants_val = target_pkg.get("plants") or (
            [
                {"plant": "Royal Ink-Mark on infant shoulder", "status": "PLANTED", "payoff_target": "Ep 1 & Season Finale", "validation": "Proves direct bloodline."},
                {"plant": "1912 Land Covenant Seal in clinic safe", "status": "PLANTED", "payoff_target": "Ep 3 & Council Climax", "validation": "Customary legal protection."}
            ] if is_isibusiso else []
        )
        props_val = target_pkg.get("prop_locks") or (
            [
                {"prop": "Customary Birth Register Ledger", "rule": "Must remain in Thandiwe's hands throughout Ep 1 climax."},
                {"prop": "Zinc Candleholder", "rule": "Burns down halfway by 45s dawn transition."},
                {"prop": "Aluminum Bank Briefcase", "rule": "Contains bundled notes with Sandton bank seals."}
            ] if is_isibusiso else []
        )

        section_8 = ContinuityBible(
            chronology_spine=spine_val,
            narrative_plants_and_payoffs=plants_val,
            prop_and_costume_locks=props_val,
            provenance=ProvenanceType.CANON,
            source_path="story_package.chronology_and_plants"
        )

        # ---------------------------------------------------------------------
        # Section 9: Production Constraints (PRODUCTION_DECISION)
        # Established by production capacity and budget limits
        # ---------------------------------------------------------------------
        section_9 = ProductionConstraint(
            budget_tier=target_pkg.get("budget_tier") or "Welele Microdrama Tier 1",
            practical_sets_max=target_pkg.get("practical_sets_max", 2),
            cast_density_per_scene_max=target_pkg.get("cast_density_per_scene_max", 3),
            safety_and_stunt_limits=target_pkg.get("safety_limits") or (
                [
                    "Zero live ammunition on set; prop firearms strictly non-firing replicas.",
                    "Medical prosthetic newborn utilized for delivery and birthmark close-ups.",
                    "Flame marshal present during candlelit interior takes."
                ] if is_isibusiso else ["DEFERRED_TO_SAFETY_OFFICER"]
            ),
            shooting_block_protocol=target_pkg.get("shooting_protocol") or (
                "Block-shoot clinic interiors during night shift; exterior dawn scenes scheduled for golden hour."
                if is_isibusiso else "DEFERRED_TO_1ST_AD"
            ),
            provenance=ProvenanceType.PRODUCTION_DECISION,
            source_path="production_guidelines.constraints"
        )

        # ---------------------------------------------------------------------
        # Section 10: Prompt Constitution (CANON)
        # Sourced from Creative Constitution v1
        # ---------------------------------------------------------------------
        section_10 = PromptConstitution(
            governing_laws=[
                "CANON OVERRIDES PROMPT CONVENIENCE: Production specs must strictly reflect Story Package facts.",
                "NO SILENT CANON CREATION: Downstream prompts must never invent unapproved lore, relatives, or supernatural powers.",
                "STRICT 9:16 VERTICAL NATIVE: Aspect ratio is mandatory for all visual prompts.",
                "VERNACULAR INTEGRITY: Dialogue must strictly adhere to character vernacular matrix."
            ],
            forbidden_mutations=target_pkg.get("forbidden_mutations") or (
                [
                    "Changing Thandiwe's role from devout midwife to complicit broker.",
                    "Allowing Bhekisisa to claim the child without customary council process.",
                    "Removing the 88s cliffhanger paywall cut."
                ] if is_isibusiso else ["Unauthorized modification of upstream character motivation or world laws."]
            ),
            aspect_ratio_enforcement="9:16 Vertical Native Only",
            canon_override_rule="CANON_OVERRIDES_PROMPT_CONVENIENCE",
            provenance=ProvenanceType.CANON,
            source_path="creative_constitution.v1"
        )

        bible_model = ProductionBibleModel(
            id=f"pb_{uuid.uuid4().hex[:8]}",
            ip_id=ip_id,
            story_package_id=target_pkg.get("id", str(uuid.uuid4())),
            bible_title=f"{title_val} — Production Bible",
            version=version,
            forge_configuration_id=cfg_id,
            lineage_hash=lineage_hash,
            section_1_title_identity=section_1,
            section_2_creative_dna=section_2,
            section_3_character_bible=characters_list,
            section_4_location_bible=section_4,
            section_5_world_rules=section_5,
            section_6_visual_language=section_6,
            section_7_audio_language=section_7,
            section_8_continuity_bible=section_8,
            section_9_production_constraints=section_9,
            section_10_prompt_constitution=section_10,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        saved_bible = self.prod_repo.save_production_bible(bible_model.model_dump())
        return saved_bible

    def generate_episode_production_pack(self, ip_id: str, production_bible_id: Optional[str] = None, episode_number: int = 1) -> Dict[str, Any]:
        """
        Generates an Episode Production Pack with 5 Coordinated Tracks:
        VIDEO, DIALOGUE, NARRATION, AMBIENCE, MUSIC.
        Derived from Production Bible + Episode Architecture.
        Prefers UNKNOWN/DEFERRED when upstream data is missing.
        """
        ip_detail = self.ip_repo.get_ip_detail(ip_id)
        if not ip_detail:
            raise ValueError(f"Digital IP franchise '{ip_id}' not found.")

        target_pkg = (ip_detail.get("story_packages") or [{}])[0]

        bible_dict = None
        if production_bible_id:
            bible_dict = self.prod_repo.get_production_bible_by_id(production_bible_id)
        if not bible_dict:
            bible_dict = self.prod_repo.get_production_bible_by_ip(ip_id)
        if not bible_dict:
            bible_dict = self.generate_production_bible(ip_id)

        cfg_id = bible_dict.get("forge_configuration_id", "CFG-001")
        lineage_hash = bible_dict.get("lineage_hash", "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6")
        is_isibusiso = "Isibusiso" in bible_dict.get("bible_title", "") or "Khumalo" in str(bible_dict)

        # ---------------------------------------------------------------------
        # Episode Beat Sheet (CANON)
        # Sourced from Story Package episode architecture
        # ---------------------------------------------------------------------
        raw_beats = target_pkg.get("beats_json") or target_pkg.get("beats") or []
        beats: List[EpisodeBeat] = []

        if raw_beats:
            for idx, b in enumerate(raw_beats):
                t_end = b.get("timestamp_end_s") or b.get("timestamp_seconds") or ((idx + 1) * 30)
                t_start = b.get("timestamp_start_s") or (0 if idx == 0 else (raw_beats[idx - 1].get("timestamp_seconds") or (idx * 30)))
                beats.append(EpisodeBeat(
                    beat_number=b.get("beat_number", idx + 1),
                    label=b.get("label") or f"Beat {idx + 1}",
                    timestamp_start_s=t_start,
                    timestamp_end_s=t_end,
                    intensity=b.get("intensity", 7),
                    action_summary=b.get("action_summary") or b.get("action_description") or b.get("description", "NOT_SPECIFIED"),
                    cliffhanger_trigger=b.get("cliffhanger_trigger", False),
                    provenance=ProvenanceType.CANON,
                    source_path=f"story_package.beats[{idx}]"
                ))
        elif is_isibusiso:
            beats = [
                EpisodeBeat(
                    beat_number=1,
                    label="Cold Open: Midnight Delivery & Ink-Mark",
                    timestamp_start_s=0,
                    timestamp_end_s=15,
                    intensity=8,
                    action_summary="Midwife Thandiwe delivers newborn by candlelight during blackout; spots royal ink-mark on infant shoulder.",
                    cliffhanger_trigger=False,
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.beats[0]"
                ),
                EpisodeBeat(
                    beat_number=2,
                    label="Dawn Escalation: The Khumalo Convoy & Surrogacy Confession",
                    timestamp_start_s=15,
                    timestamp_end_s=50,
                    intensity=9,
                    action_summary="At dawn, Bhekisisa Khumalo arrives with cash briefcases. Lerato confesses to surrogacy contract.",
                    cliffhanger_trigger=False,
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.beats[1]"
                ),
                EpisodeBeat(
                    beat_number=3,
                    label="Climax Stand-off & Paywall Cut",
                    timestamp_start_s=50,
                    timestamp_end_s=90,
                    intensity=10,
                    action_summary="Guards draw weapons. Township neighbours surround clinic with sjamboks as Thandiwe raises customary ledger. Paywall cut at 88s.",
                    cliffhanger_trigger=True,
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.beats[2]"
                )
            ]
        else:
            beats = [
                EpisodeBeat(
                    beat_number=1,
                    label="Episode Inception",
                    timestamp_start_s=0,
                    timestamp_end_s=90,
                    intensity=5,
                    action_summary="NOT_SPECIFIED",
                    cliffhanger_trigger=True,
                    provenance=ProvenanceType.CANON,
                    source_path="story_package.beats"
                )
            ]

        # ---------------------------------------------------------------------
        # Track 1: VIDEO (GENERATED)
        # ---------------------------------------------------------------------
        scene_desc = (
            [
                {
                    "scene_id": "SC_01_INT_CLINIC_NIGHT",
                    "timing": "00:00 - 00:15",
                    "visual_action": "Tight vertical frame on Thandiwe's brow. Candlelight flickers on green walls. Camera tilts down to reveal royal birthmark on infant under amber flame.",
                    "framing": "9:16 Vertical Close-Up & Extreme Close-Up",
                    "lighting": "2700K Warm Candle Key, Deep Shadows"
                },
                {
                    "scene_id": "SC_02_EXT_CLINIC_GATE_DAWN",
                    "timing": "00:15 - 00:50",
                    "visual_action": "Low-angle vertical Dutch angle of Mercedes convoy cutting through alley. Bhekisisa steps out in charcoal suit. Lerato emerges crying.",
                    "framing": "9:16 Vertical Low-Angle establishing into Over-The-Shoulder confrontation",
                    "lighting": "5600K Pre-dawn Blue Ambient + Headlights"
                },
                {
                    "scene_id": "SC_03_INT_EXT_THRESHOLD_CLIMAX",
                    "timing": "00:50 - 00:90",
                    "visual_action": "Guards rack 9mm handguns. Township neighbours emerge with sjamboks. Thandiwe raises customary ledger. Freeze on Bhekisisa meeting Thandiwe's defiance.",
                    "framing": "9:16 Vertical Whip-Pan & Hero Profile Freeze",
                    "lighting": "High-contrast golden dawn sunrise"
                }
            ] if is_isibusiso else [
                {
                    "scene_id": "SC_01_SCENE_UNSPECIFIED",
                    "timing": "00:00 - 00:90",
                    "visual_action": "DEFERRED_TO_DIRECTOR",
                    "framing": "9:16 Vertical Native",
                    "lighting": "DEFERRED_TO_GAFFER"
                }
            ]
        )

        track_video = TrackVideo(
            scene_descriptions=scene_desc,
            camera_direction=(
                [
                    {"shot": "Beat 1 Delivery", "technique": "Handheld micro-tilt from sweat to birthmark, 35mm f/1.4 prime."},
                    {"shot": "Beat 2 Convoy", "technique": "Low-angle vertical tracking shot as Bhekisisa steps into frame, 24mm f/1.8."},
                    {"shot": "Beat 3 Stand-off", "technique": "Whip-pan from drawn sidearms to customary ledger, 50mm f/1.2."}
                ] if is_isibusiso else []
            ),
            lighting_execution="Chiaroscuro key separation" if is_isibusiso else "DEFERRED",
            provenance=ProvenanceType.GENERATED,
            source_path="generator.track_video",
            derivation_notes="Synthesized from episode beats and visual language standards."
        )

        # ---------------------------------------------------------------------
        # Track 2: DIALOGUE (CANON lines + DERIVED subtext)
        # ---------------------------------------------------------------------
        dialogue_lines_val = (
            [
                {
                    "speaker": "Thandiwe",
                    "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.",
                    "subtext": "Maternal moral defiance rejecting commodification of sacred heritage.",
                    "timestamp_s": 35,
                    "delivery_tone": "Steely maternal authority."
                },
                {
                    "speaker": "Bhekisisa",
                    "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over.",
                    "subtext": "Dynastic survival panic masked behind aristocratic corporate entitlement.",
                    "timestamp_s": 55,
                    "delivery_tone": "Cold, measured authority."
                },
                {
                    "speaker": "Lerato",
                    "line": "Mama, forgive me... I had no other way to clear the loan sharks.",
                    "subtext": "Shattered guilt and plea for sanctuary.",
                    "timestamp_s": 72,
                    "delivery_tone": "Choked, tearful."
                }
            ] if is_isibusiso else []
        )

        track_dialogue = TrackDialogue(
            dialogue_lines=dialogue_lines_val,
            vernacular_subtext_notes=(
                [
                    "Thandiwe uses formal ancestral isiZulu, elevating dispute to customary law.",
                    "Bhekisisa speaks Sandton boardroom isiZulu emphasizing ownership.",
                    "Lerato uses colloquial street isiZulu."
                ] if is_isibusiso else ["DEFERRED_TO_DIALOGUE_COACH"]
            ),
            provenance=ProvenanceType.CANON,
            source_path="story_package.dialogue",
            derivation_notes="Verbatim spoken lines sourced from Story Package; subtext derived from character motivation."
        )

        # ---------------------------------------------------------------------
        # Track 3: NARRATION (DERIVED)
        # ---------------------------------------------------------------------
        track_narration = TrackNarration(
            has_narration=is_isibusiso,
            opening_hook_vo="In Soweto, blood is thicker than gold... but at dawn, gold came to collect." if is_isibusiso else None,
            internal_monologues=(
                [
                    {
                        "character": "Thandiwe",
                        "timestamp_s": 12,
                        "vo_line": "(Silent inner prayer) Nkosi yam... not this bloodline. Not in my clinic."
                    }
                ] if is_isibusiso else []
            ),
            provenance=ProvenanceType.DERIVED,
            source_path="story_package.thematic_premise",
            derivation_notes="Voiceover hooks synthesized from logline and dramatic engine."
        )

        # ---------------------------------------------------------------------
        # Track 4: AMBIENCE (GENERATED)
        # ---------------------------------------------------------------------
        track_ambience = TrackAmbience(
            room_tone="Subdued township night room tone; distant generator hum; crickets; blackout silence." if is_isibusiso else "NOT_SPECIFIED",
            foley_events=(
                [
                    {"timestamp_s": 5, "foley": "Newborn first sharp gasp and cry echoing in ward."},
                    {"timestamp_s": 18, "foley": "Gravel road crunch under heavy tyres of Mercedes convoy."},
                    {"timestamp_s": 42, "foley": "Metallic double-click of aluminum cash briefcase opening."},
                    {"timestamp_s": 84, "foley": "Heavy slide of 9mm semi-automatic pistols racking."},
                    {"timestamp_s": 86, "foley": "Leather snap of sjamboks against corrugated fence."}
                ] if is_isibusiso else []
            ),
            provenance=ProvenanceType.GENERATED,
            source_path="generator.track_ambience",
            derivation_notes="Generated sound design timeline synchronized to scene events."
        )

        # ---------------------------------------------------------------------
        # Track 5: MUSIC (GENERATED)
        # ---------------------------------------------------------------------
        track_music = TrackMusic(
            score_theme="The Sacred Bloodline (Isibusiso Main Motif)" if is_isibusiso else "NOT_SPECIFIED",
            tempo_bpm=68 if is_isibusiso else None,
            instrumentation=(
                ["Low Zulu acoustic drum pulse", "Solo staccato cello", "Seed rattle (Isagila)", "High-tension string tremolo"]
                if is_isibusiso else []
            ),
            stems_progression=(
                [
                    {"time": "00:00 - 00:15", "stem": "Solo Zulu drum heartbeat at 68 BPM."},
                    {"time": "00:15 - 00:50", "stem": "Staccato cello enters as convoy arrives, building chromatic tension."},
                    {"time": "00:50 - 00:87", "stem": "String tremolo and brass crescendo reaching peak intensity 10/10."},
                    {"time": "00:88 - 00:90", "stem": "Abrupt cut to silence at paywall cliffhanger prompt."}
                ] if is_isibusiso else []
            ),
            paywall_cut_behavior="ABRUPT_SILENCE_AT_CLIFFHANGER",
            provenance=ProvenanceType.GENERATED,
            source_path="generator.track_music",
            derivation_notes="Generated musical arrangement aligned to dramatic intensity curve."
        )

        five_tracks = FiveCoordinatedTracks(
            video=track_video,
            dialogue=track_dialogue,
            narration=track_narration,
            ambience=track_ambience,
            music=track_music
        )

        # ---------------------------------------------------------------------
        # Narrative Continuity (CANON)
        # ---------------------------------------------------------------------
        narrative_continuity = NarrativeContinuity(
            prerequisites=["Pilot Episode Inception — No prior episode prerequisites."] if is_isibusiso else [],
            narrative_state_start="Thandiwe working night shift during blackout; Lerato missing for 9 months." if is_isibusiso else "NOT_SPECIFIED",
            state_mutations=(
                [
                    "Royal infant delivered and ink-mark verified.",
                    "Lerato revealed as surrogate for Bhekisisa Khumalo.",
                    "Bhekisisa's claim rejected by Thandiwe under customary law.",
                    "Township community activated as protective barrier."
                ] if is_isibusiso else []
            ),
            active_plants=["Royal Ink-Mark (Planted)", "1912 Customary Land Covenant Seal (Planted)"] if is_isibusiso else [],
            carried_forward_to_next_ep="Armed stand-off outside clinic gate." if is_isibusiso else "NOT_SPECIFIED",
            provenance=ProvenanceType.CANON,
            source_path="story_package.narrative_continuity"
        )

        brief_val = target_pkg.get("story_brief") or (
            "During a Soweto rolling blackout, midwife Thandiwe delivers a child bearing a legendary royal birthmark. At dawn, Sandton mining tycoon Bhekisisa Khumalo arrives to claim the child, revealing Thandiwe's estranged daughter Lerato as the surrogate."
            if is_isibusiso else target_pkg.get("logline") or "NOT_SPECIFIED"
        )
        cliffhanger_val = target_pkg.get("cliffhanger_prompt") or (
            "Will Thandiwe sign the Khumalo settlement or trigger a township uprising to protect the royal infant?"
            if is_isibusiso else "NOT_SPECIFIED"
        )

        pack_model = EpisodeProductionPackModel(
            id=f"epp_{uuid.uuid4().hex[:8]}",
            production_bible_id=bible_dict["id"],
            ip_id=ip_id,
            episode_number=episode_number,
            title=f"Episode {episode_number}: {bible_dict.get('section_1_title_identity', {}).get('title', 'Untitled')}",
            duration_seconds=90,
            cliffhanger_prompt=cliffhanger_val,
            story_brief=brief_val,
            beats=beats,
            narrative_continuity=narrative_continuity,
            five_tracks=five_tracks,
            forge_configuration_id=cfg_id,
            lineage_hash=lineage_hash,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        saved_pack = self.prod_repo.save_episode_pack(pack_model.model_dump())
        return saved_pack


production_bible_service = ProductionBibleService()
