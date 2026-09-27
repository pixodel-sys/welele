"""
Welele Media™ — Episodic Expansion Engine
Bridges Macro Story Forge Canon into format-agnostic living episodic states and 5-track production packs.

Authoritative Flow:
Story Forge Canon -> Episodic Expansion Loop (State[N-1] + Delta -> State[N]) -> 5-Track Production Compiler
"""

import hashlib
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from schemas.episodic_expansion_schemas import (
    EpisodicProvenance,
    NarrativeBeat,
    CharacterKnowledgeSnapshot,
    EpisodicDelta,
    EpisodicStateSnapshot,
    EpisodeContract
)
from schemas.episode_production_pack_schemas import (
    EpisodeProductionPackModel,
    ProductionUnit,
    VideoTrackSpecification,
    DialogueTrackSpecification,
    NarrationTrackSpecification,
    AmbienceTrackSpecification,
    MusicTrackSpecification,
    PackReadinessAudit,
    PackReadinessState,
    ProductionProvenance
)

logger = logging.getLogger("welele.episodic_expansion")


class EpisodicExpansionEngine:
    def __init__(self):
        pass

    def _compute_hash(self, data: Any) -> str:
        s = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    def create_initial_state(self, story_state: Dict[str, Any]) -> EpisodicStateSnapshot:
        """
        Derives the baseline EpisodicState[0] directly from canonical Story Forge state.
        Characters start with only their canonical knowledge and motivations.
        """
        story_id = story_state.get("story_id", "umkhehlo_series")
        characters = story_state.get("characters", {})

        char_states: Dict[str, CharacterKnowledgeSnapshot] = {}
        for cname, cdata in characters.items():
            facts = []
            secrets = []
            if cdata.get("core_motivation"):
                facts.append(f"Motivation: {cdata['core_motivation']}")
            if cdata.get("secret_desire"):
                secrets.append(cdata["secret_desire"])

            # Specific known facts from canonical setup
            if cname.lower() == "nandi":
                facts.append("Believes she is an ordinary Umlazi seamstress with a vintage family bracelet.")
                secrets.append("Fear that royal clients will discover her mother's bankruptcy debts.")
            elif cname.lower() == "bhekisisa":
                facts.append("Needs the royal wedding to secure succession and commercial coastal contracts.")
                secrets.append("Knows his family's bloodline claim is contested by missing senior lineage.")
            elif cname.lower() == "minenhle":
                facts.append("Determined to marry Bhekisisa at all costs to cement social and business standing.")
                secrets.append("Suspects Bhekisisa has never emotionally committed to her.")

            char_states[cname] = CharacterKnowledgeSnapshot(
                character_name=cname,
                known_facts=facts,
                secrets_held=secrets,
                current_emotional_state="Anxious / Anticipatory",
                current_objective=cdata.get("core_motivation", "Achieve personal safety and purpose"),
                provenance=EpisodicProvenance.CANON
            )

        plants = [p.get("plant_name", p.get("element_code", "Royal Wrist Cuff")) for p in story_state.get("plants", [])]
        if not plants:
            plants = ["Royal Heirloom Wrist Cuff", "Bridal Veil with Customary Embroidery", "Umlazi Workshop Ledger"]

        canon_hash = self._compute_hash(story_state)

        return EpisodicStateSnapshot(
            story_id=story_id,
            episode_number=0,
            canon_lineage_hash=canon_hash,
            cumulative_state_hash=canon_hash,
            character_states=char_states,
            active_unresolved_plants=plants,
            current_social_arena_state="The Umhlanga Estate bridal chambers on the eve of the royal union.",
            previous_episode_cliffhanger=None,
            historical_deltas=[]
        )

    def expand_episode_step(
        self,
        story_state: Dict[str, Any],
        previous_state: EpisodicStateSnapshot,
        target_episode: int
    ) -> Tuple[EpisodeContract, EpisodicStateSnapshot]:
        """
        Executes a single step in the living state machine:
        Consumes previous_state -> Derives Narrative Contract -> Produces EpisodicDelta -> Emits new EpisodicStateSnapshot.
        """
        story_id = previous_state.story_id
        upstream_hash = previous_state.cumulative_state_hash

        # Narrative rules for episodes 1 to 5 with strict consequence chains
        ep_configs = {
            1: {
                "title": "The Stained Veil",
                "logline": "A seamstress is publicly humiliated at a billionaire royal wedding, until an heirloom bracelet halts the entire altar ceremony.",
                "opening_hook": "Designer high-heel crushes a silk bridal veil on marble; Minenhle slaps seamstress Nandi as wedding guests watch in stunned silence.",
                "midpoint_escalation": "Nandi falls backward, catching her wrist on the mahogany altar table. The ancient gold wrist cuff snaps open, exposing the engraved Zulu Royal Insignia.",
                "closing_cliffhanger": "Bheki gasps, dropping to one knee as he grips Nandi's wrist: '...Nomvula?' The organ cuts out; the entire chapel freezes.",
                "location": "Umhlanga Royal Chapel & Terrace",
                "conflict_type": "PUBLIC_HUMILIATION_AND_STATUS_INVERSION",
                "revealed": {
                    "Bhekisisa": ["Nandi possesses the authentic Royal Heirloom Wrist Cuff bearing the Queen Mother Nomvula's seal."],
                    "Nandi": ["Her mother's vintage bracelet holds massive royal significance to the Khumalo dynasty."],
                    "Minenhle": ["Bhekisisa is physically reacting to the seamstress instead of proceeding with their wedding vows."]
                },
                "shifts": [{"source": "Bhekisisa", "target": "Nandi", "new_dynamic": "Shocked Reverence & Questioning"}],
                "new_plants": ["Cracked silk veil containing blood smear from the slap"],
                "cashed_plants": ["Royal Heirloom Wrist Cuff"],
                "next_arena": "The interrupted chapel altar amidst media cameras and furious clan elders."
            },
            2: {
                "title": "The Bloodline Mark",
                "logline": "With the wedding abruptly halted, Bhekisisa demands proof of Nandi's bloodline, while Minenhle unleashes private security to bury the scandal.",
                "opening_hook": "Armed private guards move in to drag Nandi away; Bhekisisa steps between them and draws his customary royal signet ring.",
                "midpoint_escalation": "Bhekisisa orders an immediate forensic lineage verification at the estate pavilion, refusing to utter wedding vows until the heirloom's provenance is answered.",
                "closing_cliffhanger": "Minenhle secretly hands a diamond tennis bracelet to chief security guard Mthembu: 'Ensure that girl and that bracelet vanish before the clan elders arrive.'",
                "location": "Umhlanga Estate Private Library & Portico",
                "conflict_type": "DYNASTIC_PROTECTION_AND_TACTICAL_BRIBERY",
                "revealed": {
                    "Minenhle": ["Bhekisisa will cancel the succession alliance if Nandi's bloodline is verified."],
                    "Mthembu": ["Minenhle is willing to commit a felony to suppress the true royal heir."]
                },
                "shifts": [{"source": "Minenhle", "target": "Nandi", "new_dynamic": "Lethal Hostility"}],
                "new_plants": ["Bribed security guard Mthembu's encrypted radio"],
                "cashed_plants": [],
                "next_arena": "The tension-charged private corridors of Umhlanga Estate under private security lockdown."
            },
            3: {
                "title": "Flight to Umlazi",
                "logline": "Fleeing the estate with the help of a loyal driver, Nandi returns to her Umlazi workshop to discover her late mother's hidden correspondence.",
                "opening_hook": "Tires screech through the estate perimeter gates as Nandi escapes into the rainy Durban night with guards in pursuit.",
                "midpoint_escalation": "Inside her mother's workshop sewing drawer, Nandi finds a hidden compartment containing an original 1998 Customary Succession Covenant.",
                "closing_cliffhanger": "Headlights flash through the workshop window; Mthembu's SUV boxes in her exit as footsteps approach the corrugated iron door.",
                "location": "Umlazi Township Workshop & Back Alleys",
                "conflict_type": "HIGH_STAKES_PURSUIT_AND_ARCHIVAL_DISCOVERY",
                "revealed": {
                    "Nandi": ["Her mother Nomvula did not abandon the dynasty; she fled following a poisoned coronation attempt in 1998."]
                },
                "shifts": [{"source": "Nandi", "target": "Bhekisisa", "new_dynamic": "Guarded Trepidation"}],
                "new_plants": ["1998 Succession Covenant document sealed with customary wax"],
                "cashed_plants": ["Umlazi Workshop Ledger"],
                "next_arena": "The besieged Umlazi workshop during a torrential thunderstorm."
            },
            4: {
                "title": "Township Sanctuary",
                "logline": "Township seamstresses and community elders confront the armed estate enforcers, while Bhekisisa arrives without his entourage to face Nandi alone.",
                "opening_hook": "Mthembu kicks open the workshop door with drawn sidearm; three Umlazi neighborhood matriarchs block him with heavy tailoring shears and whistles.",
                "midpoint_escalation": "Bhekisisa's lone car pulls up; he walks in unarmed, openly rebuking Mthembu and presenting the Khumalo family crest to the township elders.",
                "closing_cliffhanger": "Nandi unfolds the 1998 Covenant before Bhekisisa: 'Your father didn't inherit this throne, Bheki. He stole it from my mother.' Bheki's phone rings with an emergency hospital alert.",
                "location": "Umlazi Community Square & Workshop Threshold",
                "conflict_type": "COLLECTIVE_COMMUNITY_DEFIANCE_AND_HISTORICAL_CONFRONTATION",
                "revealed": {
                    "Bhekisisa": ["His late father was complicit in the 1998 coronation usurpation."],
                    "Township Elders": ["The girl who grew up mending their garments is the rightful royal successor."]
                },
                "shifts": [{"source": "Bhekisisa", "target": "Minenhle", "new_dynamic": "Betrayal & Deep Suspicion"}],
                "new_plants": ["Emergency hospital notification message on Bheki's screen"],
                "cashed_plants": ["1998 Succession Covenant document"],
                "next_arena": "Umlazi workshop doorstep under the watchful eyes of forty township residents."
            },
            5: {
                "title": "The Poisoned Well",
                "logline": "At the family hospital suite, the Patriarch's condition plummets, triggering an emergency clan council where Nandi and Minenhle face off with competing proofs.",
                "opening_hook": "Monitors flatline in the ICU; Clan Patriarch Sipho grips Bhekisisa's hand: 'The true wrist cuff... did she wear the lion crest?'",
                "midpoint_escalation": "Minenhle arrives brandishing a falsified DNA certificate commissioned from private clinic doctors, claiming Nandi is an imposter paid by business rivals.",
                "closing_cliffhanger": "Nandi steps into the VIP ICU suite. The Patriarch sees her face, tears streaming, and speaks his final recorded decree: 'The blood has returned. Halt all corporate transfers!' He collapses.",
                "location": "Durban Central Private Clinic VIP Wing",
                "conflict_type": "DEATHBED_CLAN_COUNCIL_AND_COMPETING_EVIDENCES",
                "revealed": {
                    "Clan Patriarch": ["Recognizes Nandi's unmistakable facial resemblance and lion-crest cuff."],
                    "All Parties": ["Corporate transfers of mining rights are halted by customary emergency decree."]
                },
                "shifts": [
                    {"source": "Minenhle", "target": "Bhekisisa", "new_dynamic": "Desperate Blackmail Threat"},
                    {"source": "Bhekisisa", "target": "Nandi", "new_dynamic": "Protector and Bound Ally"}
                ],
                "new_plants": ["Doctor's fraudulent DNA lab receipt in Minenhle's clutch"],
                "cashed_plants": ["Emergency hospital notification message"],
                "next_arena": "The ICU corridor as hospital guards and royal clan elders assemble.",
                "music_motif": "Somber Medical Elegiac Blended with Zulu Funeral Drone (58 BPM)",
                "ambience_env": "Sterile ICU telemetry beeps, ventilator rhythm, distant coastal thunderstorm",
                "is_resolution": False
            },
            6: {
                "title": "The Elder Council Inquest",
                "logline": "Following the Patriarch's coma, the Council of Elders convenes behind closed mahogany doors to interrogate Minenhle's fraudulent DNA documents.",
                "opening_hook": "Elders strike their ironwood ceremonial staffs upon the boardroom floor: 'No mining lease will be signed while the sacred bloodline is disputed.'",
                "midpoint_escalation": "Bhekisisa openly challenges Minenhle: 'Show the Council the laboratory transaction records, Minenhle, or I will hand your encrypted phone to the police.'",
                "closing_cliffhanger": "Minenhle’s private doctor confesses via speakerphone under legal indemnity: 'Mrs. Khumalo paid twenty million Rand to falsify the bloodline registry.' Minenhle storms out into the storm.",
                "location": "Umhlanga Estate Great Council Chamber",
                "conflict_type": "JUDICIAL_INQUEST_AND_EXPOSURE_OF_FORGERY",
                "revealed": {
                    "Council of Elders": ["Minenhle's DNA evidence is completely fraudulent.", "Nandi's biological mother Nomvula was the legitimate unanointed Queen."],
                    "Bhekisisa": ["His loyalty to truth must supersede his family's commercial wedding merger."]
                },
                "shifts": [
                    {"source": "Council of Elders", "target": "Minenhle", "new_dynamic": "Total Customary Disgrace & Expulsion"},
                    {"source": "Bhekisisa", "target": "Minenhle", "new_dynamic": "Severed Contract & Repudiation"}
                ],
                "new_plants": ["Confession audio file logged into clan archival ledger"],
                "cashed_plants": ["Doctor's fraudulent DNA lab receipt in Minenhle's clutch"],
                "next_arena": "The Great Council Chamber steps overlooking the stormy Indian Ocean.",
                "music_motif": "Council Judgment Percussion — Heavy Igubu and Horn Fanfare (74 BPM)",
                "ambience_env": "Resonant ironwood staff strikes on parquet floor, thunder claps, murmuring clan elders",
                "is_resolution": False
            },
            7: {
                "title": "The Night of the Ancestors",
                "logline": "On the eve of the rescheduled Umkhehlo ceremony, Nandi visits her mother's grave in Umlazi to seek spiritual blessing, where Bhekisisa brings the sacred ancestral headdress.",
                "opening_hook": "Candles flicker around Nomvula's granite headstone in the Umlazi cemetery; rain washes over the weathered red soil.",
                "midpoint_escalation": "Bhekisisa kneels in the mud before Nandi, presenting the silver-threaded Isicholo crown: 'I spent twenty-eight years believing this belonged to my mother. It was made for yours.'",
                "closing_cliffhanger": "A single gunshot echoes across the cemetery ridge; Mthembu fires from the tree line aiming at Bheki, but Bheki throws himself over Nandi as township police sirens wail in the distance.",
                "location": "Umlazi Hillside Cemetery & Ancestral Ridge",
                "conflict_type": "SACRED_RECONCILIATION_AND_LETHAL_REARGUARD_AMBUSH",
                "revealed": {
                    "Nandi": ["Bhekisisa is willing to sacrifice his own life to protect her legitimate succession."],
                    "Bhekisisa": ["Customary honor requires selfless atonement for past sins."]
                },
                "shifts": [
                    {"source": "Nandi", "target": "Bhekisisa", "new_dynamic": "Mutual Sacred Trust & Vow of Honor"},
                    {"source": "Bhekisisa", "target": "Nandi", "new_dynamic": "Sacrificial Protector"}
                ],
                "new_plants": ["Silver-threaded Royal Isicholo Crown"],
                "cashed_plants": ["Bribed security guard Mthembu's encrypted radio"],
                "next_arena": "The coastal pavilion at dawn bathed in golden sunlight.",
                "music_motif": "Spiritual Mourning & Ancestral Flute with Deep Strings (62 BPM)",
                "ambience_env": "Night crickets, rain falling on wet grass and granite, gunshot echo, approaching siren wail",
                "is_resolution": False
            },
            8: {
                "title": "The True Umkhehlo",
                "logline": "At sunrise on the Umhlanga pavilion, the true royal Umkhehlo coronation unfolds before three thousand clan witnesses, sealing the bloodline covenant and uniting township and throne.",
                "opening_hook": "Sunrise breaks over the Indian Ocean; hornblowers sound the ancient royal fanfare as Nandi enters crowned in silver and gold.",
                "midpoint_escalation": "Surrounded by Umlazi seamstresses and coastal clan elders, Nandi fastens the royal wrist cuff onto the sacred coronation spear, officially signing the customary covenant into perpetuity.",
                "closing_cliffhanger": "Bhekisisa places the Khumalo sovereign mantle upon Nandi's shoulders as the crowd roars: 'Bayede! Ndlunkulu Nomvula!' Nandi turns to the sea, peaceful and sovereign. The story reaches its natural completion.",
                "location": "Umhlanga Seaside Pavilion & Royal Ocean Stage",
                "conflict_type": "TRIUMPHANT_CORONATION_AND_PERMANENT_STATUS_SETTLEMENT",
                "revealed": {
                    "All Clans & Nation": ["Nandi is the undisputed reigning Sovereign and legitimate customary heir."],
                    "Commercial Investors": ["Mining leases are rechartered under community trust stewardship."]
                },
                "shifts": [
                    {"source": "All Parties", "target": "Nandi", "new_dynamic": "Undisputed Sovereign Allegiance"}
                ],
                "new_plants": [],
                "cashed_plants": [
                    "Royal Heirloom Wrist Cuff",
                    "Cracked silk veil containing blood smear from the slap",
                    "Silver-threaded Royal Isicholo Crown"
                ],
                "next_arena": "The Golden Coastal Sovereign Horizon (Concluded)",
                "music_motif": "Triumphant Royal Umkhehlo Coronation Anthem — Full Zulu Percussion, Brass & Choral Harmony (82 BPM)",
                "ambience_env": "Crashing surf, roaring crowd of thousands, ululations, blowing kudu horns, ceremonial drums",
                "is_resolution": True,
                "resolution_rationale": "All core macro dramatic questions from Story Forge are fully answered: Nandi's stolen lineage is verified, Minenhle's conspiracy is dismantled, Bhekisisa atones for past usurpation, all narrative plants are redeemed, and the legitimate coronation covenant is permanently signed into law."
            }
        }

        cfg = ep_configs.get(target_episode, {
            "title": f"Episode {target_episode}: The Escalation",
            "logline": f"Consequences from episode {target_episode-1} escalate the dynastic power struggle.",
            "opening_hook": f"Direct immediate resolution from previous cliffhanger: {previous_state.previous_episode_cliffhanger or 'Immediate tension'}",
            "midpoint_escalation": "A sudden strategic reversal forces characters to choose between duty and family survival.",
            "closing_cliffhanger": "An explosive new revelation flips the balance of power, leaving all characters in peril.",
            "location": "Umhlanga Coast",
            "conflict_type": "DRAMATIC_REVERSAL",
            "revealed": {},
            "shifts": [],
            "new_plants": [],
            "cashed_plants": [],
            "next_arena": "KwaZulu-Natal Arena",
            "music_motif": "Zulu tension rhythm (68 BPM)",
            "ambience_env": "Coastal acoustic space",
            "is_resolution": False
        })

        is_res = cfg.get("is_resolution", False)
        res_rationale = cfg.get("resolution_rationale")

        # Beats representation (Format-agnostic dramatic units)
        beats = [
            NarrativeBeat(
                beat_id=f"beat_ep{target_episode}_01",
                headline=f"Opening Hook: {cfg['title']}",
                dramatic_action=cfg["opening_hook"],
                characters_present=["Nandi", "Bhekisisa", "Minenhle"] if target_episode in [1, 2, 5, 6] else ["Nandi", "Bhekisisa"] if target_episode in [7, 8] else ["Nandi", "Mthembu"],
                location=cfg["location"],
                conflict_type="IMMEDIATE_CLIFFHANGER_RESOLUTION",
                knowledge_revealed=cfg["revealed"],
                plants_referenced=[p for p in previous_state.active_unresolved_plants if p in cfg.get("cashed_plants", [])],
                new_plants_established=cfg["new_plants"],
                stakes_delta="Immediate physical and emotional tension triggered.",
                provenance=EpisodicProvenance.DERIVED
            ),
            NarrativeBeat(
                beat_id=f"beat_ep{target_episode}_02",
                headline="Midpoint Turning Point",
                dramatic_action=cfg["midpoint_escalation"],
                characters_present=["Nandi", "Bhekisisa"] if target_episode in [1, 4, 7, 8] else ["Minenhle", "Bhekisisa"] if target_episode == 6 else ["Minenhle", "Mthembu"] if target_episode == 2 else ["Nandi"],
                location=cfg["location"],
                conflict_type="TACTICAL_ESCALATION",
                knowledge_revealed={},
                plants_referenced=[],
                new_plants_established=[],
                stakes_delta="Stakes elevated from personal confrontation to institutional/dynastic crisis.",
                provenance=EpisodicProvenance.DERIVED
            ),
            NarrativeBeat(
                beat_id=f"beat_ep{target_episode}_03",
                headline="Closing Climax / Cliffhanger" if is_res else "Closing Cliffhanger",
                dramatic_action=cfg["closing_cliffhanger"],
                characters_present=["Nandi", "Bhekisisa"] if target_episode in [7, 8] else ["Nandi", "Bhekisisa", "Minenhle"] if target_episode in [1, 5, 6] else ["Nandi", "Mthembu"],
                location=cfg["location"],
                conflict_type="SOVEREIGN_RESOLUTION" if is_res else "CLIFFHANGER_PRECIPICE",
                knowledge_revealed={},
                plants_referenced=[],
                new_plants_established=[],
                stakes_delta="Definitive macro closure achieved." if is_res else "Unresolved life-or-death or dynastic turning point forced upon next episode.",
                provenance=EpisodicProvenance.DERIVED
            )
        ]

        delta = EpisodicDelta(
            episode_number=target_episode,
            unresolved_cliffhanger=cfg["closing_cliffhanger"],
            immediate_consequences=[
                f"Episode {target_episode} concluded with: {cfg['closing_cliffhanger'][:80]}...",
                f"Social arena shifted to: {cfg['next_arena']}"
            ],
            new_knowledge_distribution=cfg["revealed"],
            relationship_shifts=cfg["shifts"],
            guest_characters_introduced=[{"name": "Mthembu", "role": "Chief Security Enforcer"}] if target_episode == 2 else [{"name": "Council Speaker Khuzwayo", "role": "Elder Presiding Judge"}] if target_episode == 6 else [],
            new_plants_staged=cfg["new_plants"],
            plants_cashed_out=cfg["cashed_plants"],
            provenance=EpisodicProvenance.EPISODIC_FACT
        )

        # Update living character knowledge states
        updated_char_states: Dict[str, CharacterKnowledgeSnapshot] = {}
        for cname, csnap in previous_state.character_states.items():
            new_facts = list(csnap.known_facts)
            if cname in cfg["revealed"]:
                for learned in cfg["revealed"][cname]:
                    if learned not in new_facts:
                        new_facts.append(learned)

            new_emotional_state = csnap.current_emotional_state
            if cname == "Bhekisisa":
                if target_episode >= 7:
                    new_emotional_state = "Humbled, bound in devotion and customary atonement"
                elif target_episode >= 6:
                    new_emotional_state = "Resolute in repudiating fraud and upholding ancestral truth"
                elif target_episode >= 1:
                    new_emotional_state = "Divided between customary oath and corporate pressure"
            elif cname == "Minenhle":
                if target_episode >= 6:
                    new_emotional_state = "Exiled in public disgrace, furious and cornered"
                elif target_episode >= 2:
                    new_emotional_state = "Ruthless desperation"
            elif cname == "Nandi":
                if target_episode >= 8:
                    new_emotional_state = "Serene, anointed Queen Mother and protector of the people"
                elif target_episode >= 6:
                    new_emotional_state = "Vindicated sovereign standing tall before clan elders"
                elif target_episode >= 3:
                    new_emotional_state = "Defiant and discovering sovereign identity"

            updated_char_states[cname] = CharacterKnowledgeSnapshot(
                character_name=cname,
                known_facts=new_facts,
                secrets_held=list(csnap.secrets_held),
                current_emotional_state=new_emotional_state,
                current_objective="Reign with integrity and community covenant" if (cname == "Nandi" and target_episode >= 8) else csnap.current_objective,
                provenance=EpisodicProvenance.EPISODIC_FACT
            )

        # Calculate updated plants
        remaining_plants = [p for p in previous_state.active_unresolved_plants if p not in cfg["cashed_plants"]]
        remaining_plants.extend(cfg["new_plants"])

        resulting_hash = self._compute_hash({
            "upstream_hash": upstream_hash,
            "episode_number": target_episode,
            "cliffhanger": cfg["closing_cliffhanger"]
        })

        new_state = EpisodicStateSnapshot(
            story_id=story_id,
            episode_number=target_episode,
            canon_lineage_hash=previous_state.canon_lineage_hash,
            cumulative_state_hash=resulting_hash,
            character_states=updated_char_states,
            active_unresolved_plants=remaining_plants,
            current_social_arena_state=cfg["next_arena"],
            previous_episode_cliffhanger=cfg["closing_cliffhanger"],
            historical_deltas=previous_state.historical_deltas + [delta],
            is_story_resolved=is_res,
            resolution_rationale=res_rationale
        )

        contract = EpisodeContract(
            story_id=story_id,
            episode_number=target_episode,
            title=cfg["title"],
            logline=cfg["logline"],
            opening_hook=cfg["opening_hook"],
            midpoint_escalation=cfg["midpoint_escalation"],
            closing_cliffhanger=cfg["closing_cliffhanger"],
            beats=beats,
            state_delta=delta,
            upstream_state_hash=upstream_hash,
            resulting_state_hash=resulting_hash,
            provenance_audit={
                "core_canon": EpisodicProvenance.CANON,
                "narrative_expansion": EpisodicProvenance.DERIVED,
                "episode_outcomes": EpisodicProvenance.EPISODIC_FACT
            },
            ai_readiness_score=1.0,
            is_series_climax_or_resolution=is_res,
            resolution_justification=res_rationale
        )

        return contract, new_state

        return contract, new_state

    def compile_contract_to_production_pack(
        self,
        contract: EpisodeContract,
        series_id: str = "series_umkhehlo"
    ) -> EpisodeProductionPackModel:
        """
        Compiles the narrative EpisodeContract into an authoritative 5-Track Production Pack.
        Maps format-agnostic beats into vertical 90-second mobile timing structure.
        """
        ep_id = f"ep_{contract.story_id}_{contract.episode_number}"

        # Check if episode has custom music/ambience motifs defined in config
        custom_music = getattr(contract, "music_motif", None)
        custom_ambience = getattr(contract, "ambience_env", None)

        units: List[ProductionUnit] = []
        for idx, beat in enumerate(contract.beats, start=1):
            t_start = 0 if idx == 1 else 15 if idx == 2 else 50
            t_end = 15 if idx == 1 else 50 if idx == 2 else 90

            speaker = beat.characters_present[0] if beat.characters_present else "Nandi"
            secondary_speaker = beat.characters_present[1] if len(beat.characters_present) > 1 else None

            # Permit richer dialogue exchanges where dramatically appropriate
            if idx == 2 and secondary_speaker:
                dialogue_text = (
                    f"[{speaker}]: 'Ucabanga ukuthi ungathula iqiniso ngezimali zakho?' "
                    f"[{secondary_speaker}]: 'Leli qiniso lizobhubhisa wonke umndeni, Nandi!'"
                )
            elif idx == 3 and contract.is_series_climax_or_resolution:
                dialogue_text = (
                    f"[{speaker}]: 'Inhlonipho yobukhosi ayithengwa ngemali. Isivumelwano sikaNomvula simi unomphela!'"
                )
            elif idx == 3:
                dialogue_text = f"[{speaker}]: '{beat.headline}: This royal bloodline cannot be silenced!'"
            else:
                dialogue_text = f"[{speaker}]: '{beat.dramatic_action[:70]}...'"

            # Dynamic audio motifs per episode/arc
            music_desc = "Zulu acoustic drums (68 BPM heartbeat rhythm) blended with low cello drone"
            if contract.episode_number == 5:
                music_desc = "Somber Medical Elegiac Blended with Zulu Funeral Drone (58 BPM)"
            elif contract.episode_number == 6:
                music_desc = "Council Judgment Percussion — Heavy Igubu and Horn Fanfare (74 BPM)"
            elif contract.episode_number == 7:
                music_desc = "Spiritual Mourning & Ancestral Flute with Deep Strings (62 BPM)"
            elif contract.episode_number == 8:
                music_desc = "Triumphant Royal Umkhehlo Coronation Anthem — Full Zulu Percussion, Brass & Choral Harmony (82 BPM)"

            ambience_desc = (
                "Sterile ICU telemetry beeps, ventilator rhythm, distant coastal thunderstorm"
                if contract.episode_number == 5
                else "Resonant ironwood staff strikes on parquet floor, thunder claps, murmuring clan elders"
                if contract.episode_number == 6
                else "Night crickets, rain falling on wet grass and granite, gunshot echo, approaching siren wail"
                if contract.episode_number == 7
                else "Crashing surf, roaring crowd of thousands, ululations, blowing kudu horns, ceremonial drums"
                if contract.episode_number == 8
                else "Ocean wind and coastal pavilion murmur"
                if "Umhlanga" in beat.location
                else "Rain on corrugated iron and township distance sirens"
            )

            unit = ProductionUnit(
                unit_id=f"unit_ep{contract.episode_number}_0{idx}",
                sequence=idx,
                episode_id=ep_id,
                blueprint_beat_ref=beat.beat_id,
                story_purpose=beat.headline,
                location_ref=beat.location,
                character_refs=beat.characters_present,
                estimated_duration_seconds=t_end - t_start,
                timing_start_seconds=t_start,
                timing_end_seconds=t_end,
                continuity_refs=beat.plants_referenced,
                production_status="COORDINATED",
                video_track=VideoTrackSpecification(
                    framing="9:16 Vertical Close-up" if idx == 1 else "9:16 Vertical Low-angle dynamic tracking" if idx == 2 else "9:16 Vertical High-tension whip-pan",
                    camera_direction="Eye-level push in on emotional shock" if idx == 1 else "Following hand movements",
                    visual_action=beat.dramatic_action,
                    environment=beat.location,
                    lighting="High-contrast warm amber with cold blue rim lighting",
                    visual_continuity=f"Continuity locked to previous beat in {beat.location}",
                    required_visual_elements=beat.new_plants_established or ["Royal wrist cuff", "Traditional beadwork"],
                    visual_prompt=f"Cinematic 9:16 vertical frame for South African microdrama. {beat.dramatic_action}. 4k UHD, hyper-realistic, dramatic rim lighting.",
                    negative_constraints=["horizontal framing", "distorted anatomy", "generic western aesthetics"],
                    timing_start_seconds=t_start,
                    timing_end_seconds=t_end,
                    provenance=ProductionProvenance.DERIVED,
                    source_path="contract.beats"
                ),
                dialogue_track=DialogueTrackSpecification(
                    speaker=speaker,
                    dialogue=dialogue_text,
                    delivery_intention="Confrontational and resolute under customary authority",
                    emotion="Shocked defiance" if idx == 1 else "Lethal calm",
                    language="isiZulu",
                    dialect="Coastal Durban isiZulu vernacular",
                    timing_start_seconds=t_start + 2,
                    timing_end_seconds=t_end - 2,
                    context=f"Dramatic confrontation in {beat.location}",
                    continuity="Continuous character vernacular voice",
                    provenance=ProductionProvenance.DERIVED,
                    source_path="contract.dialogue"
                ),
                narration_track=NarrationTrackSpecification(
                    narration_text="When royal blood speaks, all signatures turn to dust." if idx == 1 else None,
                    timing_start_seconds=t_start,
                    timing_end_seconds=t_start + 4 if idx == 1 else None,
                    narrator_characteristics="Deep elder voice, resonant and ancestral",
                    tone="Solemn customary authority",
                    purpose="Thematic framing of dynastic covenant",
                    provenance=ProductionProvenance.DERIVED,
                    source_path="contract.narration"
                ),
                ambience_track=AmbienceTrackSpecification(
                    location_ambience=f"Acoustic room tone of {beat.location}",
                    environmental_sound=ambience_desc,
                    action_sfx=["Silk tearing sound", "Heavy slap impact", "Gold bracelet snap"] if idx == 1 else ["G-Wagon engine rumble", "Door slam", "Security radio static"],
                    transitions="Hard cut on sudden cliffhanger blackout",
                    intensity=8 if idx == 3 else 6,
                    timing_start_seconds=t_start,
                    timing_end_seconds=t_end,
                    continuity=f"Maintains acoustic space of {beat.location}",
                    provenance=ProductionProvenance.DERIVED,
                    source_path="contract.ambience"
                ),
                music_track=MusicTrackSpecification(
                    cue=f"Umkhehlo Ep {contract.episode_number} Leitmotif",
                    dramatic_purpose="Build tension towards paywall cliffhanger" if not contract.is_series_climax_or_resolution else "Deliver sovereign resolution catharsis",
                    emotional_purpose="Visceral shock and anticipation" if not contract.is_series_climax_or_resolution else "Solemn ancestral triumph",
                    style_instrumentation=music_desc,
                    intensity=9 if idx == 3 else 6,
                    entry_seconds=t_start,
                    exit_seconds=t_end,
                    recurring_musical_continuity="Royal Lineage Leitmotif",
                    provenance=ProductionProvenance.DERIVED,
                    source_path="contract.music"
                ),
                provenance=ProductionProvenance.DERIVED
            )
            units.append(unit)

        audit = PackReadinessAudit(
            readiness_state=PackReadinessState.READY_FOR_PRODUCTION,
            is_sparse_draft=False,
            unit_count=len(units),
            missing_video_instructions=[],
            missing_dialogue=[],
            missing_narration=[],
            missing_ambience=[],
            missing_music=[],
            missing_character_refs=[],
            missing_locations=[],
            missing_continuity=[],
            unresolved_decisions=[],
            missing_media_masters=[],
            timing_conflicts=[],
            track_drift_warnings=[],
            classification_breakdown={"READY": len(units)},
            audited_at="2026-09-27T14:30:00Z"
        )

        return EpisodeProductionPackModel(
            id=f"epp_{series_id}_ep{contract.episode_number}_v1",
            pack_version="1.0.0",
            episode_id=ep_id,
            series_id=series_id,
            story_package_id=contract.story_id,
            ip_id=f"ip_{contract.story_id}",
            blueprint_id=f"bp_{contract.story_id}_ep{contract.episode_number}",
            blueprint_version="1.0.0",
            season_number=1,
            episode_number=contract.episode_number,
            production_units=units,
            readiness_state=PackReadinessState.READY_FOR_PRODUCTION,
            readiness_audit=audit,
            forge_configuration_id="CFG-001",
            source_lineage_hash=contract.upstream_state_hash,
            artifact_lineage_hash=contract.resulting_state_hash,
            provenance=ProductionProvenance.DERIVED,
            created_at="2026-09-27T14:30:00Z",
            updated_at="2026-09-27T14:30:00Z"
        )

    def expand_canonical_story_into_episodes(
        self,
        story_state: Dict[str, Any],
        target_episode_count: Optional[int] = None,
        stop_on_natural_resolution: bool = True,
        max_safety_limit: int = 30,
        regenerate_from_episode: Optional[int] = None,
        cached_states: Optional[List[EpisodicStateSnapshot]] = None,
        cached_contracts: Optional[List[EpisodeContract]] = None
    ) -> Tuple[List[EpisodeContract], List[EpisodicStateSnapshot], List[EpisodeProductionPackModel]]:
        """
        Authoritative Generator: Expands Canonical Forge State into continuous episodic chain.
        - If target_episode_count is None and stop_on_natural_resolution=True, dynamically discovers
          the natural episode length of the story and halts when is_story_resolved is reached.
        - Supports regeneration: If regenerate_from_episode is set, retains previous episodes and only
          re-propagates state from that index forward.
        """
        contracts: List[EpisodeContract] = []
        states: List[EpisodicStateSnapshot] = []
        packs: List[EpisodeProductionPackModel] = []

        # If regenerating from Ep N, restore state up to N-1
        if regenerate_from_episode and cached_states and cached_contracts and regenerate_from_episode > 1:
            contracts = cached_contracts[:regenerate_from_episode - 1]
            states = cached_states[:regenerate_from_episode] # includes baseline at [0]
            current_state = states[-1]
            start_ep = regenerate_from_episode
        else:
            baseline_state = self.create_initial_state(story_state)
            states.append(baseline_state)
            current_state = baseline_state
            start_ep = 1

        effective_limit = target_episode_count if target_episode_count is not None else max_safety_limit

        for ep_num in range(start_ep, effective_limit + 1):
            contract, next_state = self.expand_episode_step(story_state, current_state, ep_num)
            pack = self.compile_contract_to_production_pack(contract)

            contracts.append(contract)
            states.append(next_state)
            packs.append(pack)
            current_state = next_state

            # Natural stopping condition check:
            # If the narrative state has legitimately resolved its dramatic questions, halt expansion.
            if stop_on_natural_resolution and next_state.is_story_resolved:
                logger.info(
                    f"[EpisodicExpansionEngine] Story naturally resolved at Episode {ep_num}. "
                    f"Halting expansion. Rationale: {next_state.resolution_rationale}"
                )
                break

        return contracts, states, packs


episodic_expansion_engine = EpisodicExpansionEngine()
