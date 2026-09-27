"""
Test Suite: AI Production Adapter & Plan Compiler
Validates:
1. Exact Compilation of Canonical Production Document (Isibusiso Episode 1):
   - Confirms that the production document is already sufficiently expressive to compile directly.
   - Zero questions asked to creator for information already present.
2. Inquiry Classification (Categories A, B, C):
   - Category A: Missing Canonical Info (bubbles upstream to Story Forge)
   - Category B: Missing Physical Production Info (bubbles upstream to Production Office)
   - Category C: AI Runtime/Adapter Requirement (self-resolved deterministically by adapter, never bubbles upstream)
3. Provenance & Immutability Isolation:
   - AI-runtime entity IDs, LoRA tags, and diffusion parameters NEVER mutate canonical Story Forge truth.
4. Coordinated 5-Track Execution Completeness:
   - 9:16 vertical video prompt, locked isiZulu dialogue with subtext, voice profiles, Foley, and 68 BPM score.
"""

import pytest
from services.production_bible_service import production_bible_service
from services.ai_production_adapter_service import (
    ai_production_adapter_compiler,
    FeedbackCategory
)
from schemas.production_schemas import (
    ProductionBibleModel,
    EpisodeProductionPackModel
)


@pytest.fixture
def isibusiso_canonical_production_doc():
    """Generates the authoritative Production Bible and Episode 1 Pack for Isibusiso."""
    from repositories.ip_repository import ip_repository

    ips = ip_repository.list_ips()
    target_ip = next((ip for ip in ips if ip.get("franchise_code") == "IP-ISIBUSISO" or ip.get("title") == "Isibusiso"), None)
    if not target_ip:
        target_ip = {
            "id": "ip_isibusiso_dynasty",
            "title": "Isibusiso",
            "franchise_code": "IP-ISIBUSISO",
            "logline": "A devout Soweto midwife delivers a baby during a township power blackout and notices a birthmark matching a legendary royal bloodline. When the wealthy Khumalo mining family arrives at dawn claiming the child, she discovers her own estranged daughter was the surrogate mother.",
            "synopsis": "Set across the stark contrast of Mofolo South township clinic and the Sandhurst high-security compound, Isibusiso tracks the explosive collision between customary royal succession and modern corporate mining power.",
            "genre": "High-Stakes Melodrama / Vertical Microdrama",
            "primary_language": "isiZulu",
            "master_owner_id": "creator_zola"
        }
        ip_repository.local_insert("digital_ips", target_ip)

    ip_id = target_ip["id"]
    detail = ip_repository.get_ip_detail(ip_id)
    story_packages = detail.get("story_packages", [])
    if not story_packages:
        pkg = {
            "id": "pkg_isibusiso_v1",
            "ip_id": ip_id,
            "creator_id": "creator_zola",
            "package_title": "Isibusiso: The Sacred Lineage",
            "story_world_id": "sw_soweto_sandton",
            "target_duration_seconds": 90,
            "version": "1.0.0",
            "primary_language": "isiZulu",
            "secondary_languages": ["English", "Sesotho", "Tsotsitaal"],
            "logline": target_ip["logline"],
            "genre": target_ip["genre"],
            "thematic_premise": "Customary royal birthright and sacred lineage versus corporate mining commodification.",
            "characters": [
                {
                    "name": "Thandiwe Sithole",
                    "role": "PROTAGONIST",
                    "archetype": "The Devout Midwife / Moral Shield",
                    "core_motivation": "Protect the royal infant and reconcile with Lerato",
                    "fatal_flaw": "Rigid moral pride",
                    "signature_dialogue": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."
                },
                {
                    "name": "Bhekisisa Khumalo",
                    "role": "ANTAGONIST",
                    "archetype": "Dynastic Mining Patriarch",
                    "core_motivation": "Secure legitimate male heir to preserve mining concessions",
                    "fatal_flaw": "Corporate entitlement and dynastic panic",
                    "signature_dialogue": "That child carries the only bloodline that keeps my mining shafts open. Hand him over."
                },
                {
                    "name": "Lerato Sithole",
                    "role": "SUPPORTING",
                    "archetype": "Desperate Surrogate Daughter",
                    "core_motivation": "Clear debt from township loan sharks",
                    "fatal_flaw": "Guilt and vulnerability",
                    "signature_dialogue": "Mama, forgive me... I had no other way to clear the loan sharks."
                }
            ],
            "locations": [
                {
                    "location_name": "Mofolo South Clinic Ward",
                    "setting_type": "INTERIOR_PRACTICAL",
                    "spatial_layout": "15m² practical interior, iron gurney, wooden cabinet",
                    "lighting_conditions": "2700K Warm Candle Key, Deep Shadows"
                },
                {
                    "location_name": "Clinic Exterior Gate",
                    "setting_type": "EXTERIOR_PRACTICAL",
                    "spatial_layout": "Corrugated iron perimeter, gravel road",
                    "lighting_conditions": "5600K Pre-dawn Blue Ambient + Headlights"
                }
            ],
            "inviolable_rules": [
                {"rule_key": "RULE_CUSTOMARY_LINEAGE_COVENANT", "law_description": "Royal birthright cannot be alienated or sold via civil contract.", "narrative_impact": "Supersedes Sandton contract."}
            ],
            "chronology_spine": [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."}
            ],
            "plants": [
                {"plant": "Royal Ink-Mark on infant shoulder", "status": "PLANTED", "payoff_target": "Ep 1 & Season Finale"},
                {"plant": "1912 Land Covenant Seal in clinic safe", "status": "PLANTED", "payoff_target": "Ep 3 & Council Climax"}
            ],
            "dialogue": [
                {"speaker": "Thandiwe", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.", "subtext": "Moral defiance", "timestamp_s": 35, "delivery_tone": "Steely maternal authority."},
                {"speaker": "Bhekisisa", "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over.", "subtext": "Dynastic panic", "timestamp_s": 55, "delivery_tone": "Cold corporate threat."}
            ],
            "beats": [
                {"beat_number": 1, "label": "Cold Open: Midnight Delivery", "timestamp_seconds": 15, "action_description": "Midwife Thandiwe delivers newborn."},
                {"beat_number": 2, "label": "Dawn Confrontation", "timestamp_seconds": 50, "action_description": "Khumalo convoy arrives with cash."},
                {"beat_number": 3, "label": "Cliffhanger Paywall Cut", "timestamp_seconds": 88, "action_description": "Guards draw weapons."}
            ],
            "forge_configuration_id": "CFG-001",
            "lineage_hash": "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        }
        ip_repository.local_insert("story_forge_packages", pkg)

    bible_dict = production_bible_service.generate_production_bible(ip_id)
    pack_dict = production_bible_service.generate_episode_production_pack(ip_id, bible_dict["id"], episode_number=1)
    
    bible = ProductionBibleModel(**bible_dict)
    pack = EpisodeProductionPackModel(**pack_dict)
    return bible, pack


def test_ai_adapter_compilation_from_exact_production_doc(isibusiso_canonical_production_doc):
    """
    Test 1: Take Episode 1 exactly as supplied and produce the AI-specific executable plan.
    Proves that the document is sufficiently expressive and requires zero upstream inquiries.
    """
    bible, pack = isibusiso_canonical_production_doc

    # Compile into executable AI plan
    ai_plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)

    # Validate plan metadata
    assert ai_plan.compilation_status == "READY_FOR_EXECUTION"
    assert ai_plan.source_production_bible_id == bible.id
    assert ai_plan.source_pack_id == pack.id
    assert len(ai_plan.unresolved_questions) == 0  # Zero questions asked to creator!

    # Validate runtime character entity bindings (Category C synthesized)
    assert len(ai_plan.character_entity_bindings) == 3
    thandiwe_binding = next(b for b in ai_plan.character_entity_bindings if "Thandiwe" in b.canonical_character_name)
    assert thandiwe_binding.reference_entity_id == "ent_thandiwe_sithole"
    assert "lora" in thandiwe_binding.visual_embedding_tag
    assert "voice_isizulu_matriarch_v1" in thandiwe_binding.voice_profile_id
    assert thandiwe_binding.speech_rate_wpm == 120

    # Validate executable shots storyboard
    assert ai_plan.total_shots == 3
    assert ai_plan.total_duration_seconds == 88 or ai_plan.total_duration_seconds == 90
    assert ai_plan.paywall_lock_timestamp_seconds == 88

    # Shot 1: Midnight Delivery
    shot_1 = ai_plan.executable_shots[0]
    assert shot_1.aspect_ratio == "9:16"
    assert shot_1.resolution == "1080x1920"
    assert "2700K" in shot_1.lighting_setup or "Candle" in shot_1.lighting_setup
    assert "Welele_Mzansi_Chiaroscuro_v1" in shot_1.color_lut_id
    assert "35mm" in shot_1.lens_specification
    assert shot_1.diffusion_cfg_scale == 7.5
    assert shot_1.score_bpm == 68

    # Shot 2: Convoy Confrontation with verbatim dialogue
    shot_2 = ai_plan.executable_shots[1]
    assert shot_2.speaking_entity_id is not None
    assert "platinum ore" in shot_2.spoken_dialogue_isizulu.lower()
    assert "authority" in shot_2.emotion_guidance.lower()

    # Shot 3: Climax Stand-off
    shot_3 = ai_plan.executable_shots[2]
    assert "Whip-Pan" in shot_3.ai_video_prompt or "Freeze" in shot_3.ai_video_prompt
    assert shot_3.timing_end_seconds >= 88


def test_inquiry_classification_taxonomy():
    """
    Test 2: Test the tripartite inquiry classification:
    Category A: Missing canonical info -> Bubbles upstream to Story Forge
    Category B: Missing physical production info -> Bubbles upstream to Production Office
    Category C: AI runtime/adapter requirement -> Auto-resolved by adapter, does NOT bubble upstream
    """
    # Category C inquiries (AI Runtime / Adapter)
    q_lora = "What is the reference_entity_id and LoRA checkpoint for Thandiwe?"
    class_lora = ai_production_adapter_compiler.classify_inquiry(q_lora)
    assert class_lora["category"] == FeedbackCategory.C_AI_RUNTIME_ADAPTER
    assert class_lora["bubbles_upstream"] is False
    assert class_lora["action"] == "AUTO_RESOLVE_BY_ADAPTER"

    q_cfg = "What CFG scale and diffusion step count should be used for the 9:16 vertical render?"
    class_cfg = ai_production_adapter_compiler.classify_inquiry(q_cfg)
    assert class_cfg["category"] == FeedbackCategory.C_AI_RUNTIME_ADAPTER
    assert class_cfg["bubbles_upstream"] is False

    q_tts = "What TTS voice ID and WPM speech rate should be assigned to Bhekisisa?"
    class_tts = ai_production_adapter_compiler.classify_inquiry(q_tts)
    assert class_tts["category"] == FeedbackCategory.C_AI_RUNTIME_ADAPTER
    assert class_tts["bubbles_upstream"] is False

    # Category B inquiries (Missing Physical Production Info)
    q_stunt = "Has a stunt double and fire marshal permit been approved for the gate scene?"
    class_stunt = ai_production_adapter_compiler.classify_inquiry(q_stunt)
    assert class_stunt["category"] == FeedbackCategory.B_MISSING_PRODUCTION
    assert class_stunt["bubbles_upstream"] is True

    # Category A inquiries (Missing Canonical Info)
    q_canon = "Is Thandiwe secretly related to the royal Khumalo clan through marriage?"
    class_canon = ai_production_adapter_compiler.classify_inquiry(q_canon)
    assert class_canon["category"] == FeedbackCategory.A_MISSING_CANONICAL
    assert class_canon["bubbles_upstream"] is True


def test_runtime_parameters_do_not_mutate_story_canon(isibusiso_canonical_production_doc):
    """
    Test 3: Verify that compiling the AI Plan does not mutate or inject runtime parameters
    into upstream Story Forge or Production Bible models.
    """
    bible, pack = isibusiso_canonical_production_doc
    original_thandiwe_dict = bible.section_3_character_bible[0].model_dump()

    ai_plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)

    # Check that Thandiwe in bible was not mutated with reference_entity_id or LoRA tokens
    assert "reference_entity_id" not in bible.section_3_character_bible[0].model_dump()
    assert "lora_asset_id" not in bible.section_3_character_bible[0].model_dump()
    assert bible.section_3_character_bible[0].name == original_thandiwe_dict["name"]
    assert bible.section_3_character_bible[0].canon_provenance.value == "CANON"
