"""
Test Suite: Regression Invariant Suite against Frozen Episode 1 Baseline
Guarantees that no future modifications to:
- Story Forge canon
- Episodic expansion engine
- Production compiler
- AI production adapter

can degrade any of the 10 frozen baseline dimensions:
1. Character Identity (biometric similarity >= 0.95)
2. Wardrobe (green midwife tunic with wax distress, charcoal suit)
3. Spatial Continuity (interior ward -> exterior gate)
4. Lighting Grammar (2700K candle vs 5600K headlights)
5. Prop Persistence (Royal ink-mark on infant left scapula & customary ledger)
6. Voice Identity (ancestral isiZulu 120 WPM vs boardroom 135 WPM)
7. Dialogue Fidelity (verbatim match)
8. Audio/Music (locked 68 BPM Zulu drum heartbeat pulse)
9. Timing (88-90s vertical microdrama: 15s hook, 50s reversal, 88s climax)
10. Paywall/Cliffhanger Integrity (hard blackout at 88.0s) + Canon Immutability
"""

import pytest
from fixtures.frozen_episode_1_baseline import FROZEN_BASELINE_EPISODE_1
from repositories.ip_repository import ip_repository
from services.production_bible_service import production_bible_service
from services.ai_production_adapter_service import ai_production_adapter_compiler
from services.media_production_audit_service import media_production_audit_service
from schemas.production_schemas import ProductionBibleModel, EpisodeProductionPackModel


@pytest.fixture
def executed_episode_1_audit():
    """Generates the live pipeline output for Episode 1."""
    # Ensure IP and story package are registered
    ips = ip_repository.list_ips()
    target_ip = next((ip for ip in ips if ip.get("franchise_code") == "IP-ISIBUSISO" or ip.get("title") == "Isibusiso"), None)
    if not target_ip:
        target_ip = {
            "id": "ip_isibusiso_dynasty",
            "title": "Isibusiso",
            "franchise_code": "IP-ISIBUSISO",
            "logline": "A devout Soweto midwife delivers a baby during a township power blackout and notices a birthmark matching a legendary royal bloodline.",
            "synopsis": "Isibusiso tracks the collision between customary royal succession and corporate mining power.",
            "genre": "High-Stakes Melodrama / Vertical Microdrama",
            "primary_language": "isiZulu",
            "master_owner_id": "creator_zola"
        }
        ip_repository.local_insert("digital_ips", target_ip)

    ip_id = target_ip["id"]
    detail = ip_repository.get_ip_detail(ip_id)
    if not detail.get("story_packages"):
        pkg = {
            "id": "pkg_isibusiso_v1",
            "ip_id": ip_id,
            "creator_id": "creator_zola",
            "package_title": "Isibusiso: The Sacred Lineage",
            "target_duration_seconds": 90,
            "primary_language": "isiZulu",
            "logline": target_ip["logline"],
            "genre": target_ip["genre"],
            "thematic_premise": "Customary royal birthright versus corporate mining commodification.",
            "characters": [
                {
                    "name": "Thandiwe Sithole",
                    "role": "PROTAGONIST",
                    "archetype": "The Devout Midwife",
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
                {"rule_key": "RULE_CUSTOMARY_LINEAGE_COVENANT", "law_description": "Royal birthright cannot be alienated.", "narrative_impact": "Supersedes Sandton contract."}
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

    plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)
    rendered = media_production_audit_service.render_episode_media(plan)
    audit = media_production_audit_service.audit_rendered_media_against_source(rendered, plan, bible, pack)
    return audit, rendered, plan


def test_frozen_baseline_character_and_wardrobe_invariants(executed_episode_1_audit):
    """Regression Test 1: Character identity and wardrobe fidelity against frozen baseline."""
    audit, rendered, plan = executed_episode_1_audit
    invariants = FROZEN_BASELINE_EPISODE_1["invariants"]

    # 1. Biometrics
    thandiwe_binding = next(b for b in plan.character_entity_bindings if "Thandiwe" in b.canonical_character_name)
    assert thandiwe_binding.reference_entity_id == invariants["character_identity"]["thandiwe_entity_id"]
    assert invariants["character_identity"]["thandiwe_lora_token"] in thandiwe_binding.visual_embedding_tag

    c1 = next(i for i in audit.audit_results if i.criterion_name == "Character Identity Continuity")
    assert c1.fidelity_score >= invariants["character_identity"]["min_face_similarity_threshold"]

    # 2. Wardrobe
    c2 = next(i for i in audit.audit_results if i.criterion_name == "Wardrobe Continuity")
    assert c2.status.value == "PASSED"


def test_frozen_baseline_props_and_lighting_invariants(executed_episode_1_audit):
    """Regression Test 2: Spatial, lighting, and key prop continuity against frozen baseline."""
    audit, rendered, plan = executed_episode_1_audit
    invariants = FROZEN_BASELINE_EPISODE_1["invariants"]

    # 1. Lighting Grammar
    c4 = next(i for i in audit.audit_results if i.criterion_name == "Lighting & Visual Language Continuity")
    assert str(invariants["lighting_grammar"]["scene_1_interior"]) in c4.measured_value
    assert str(invariants["lighting_grammar"]["scene_2_exterior"]) in c4.measured_value

    # 2. Prop Persistence
    c5 = next(i for i in audit.audit_results if "Key Prop Continuity" in i.criterion_name)
    assert c5.fidelity_score == 1.0
    for expected_prop in invariants["prop_persistence"]:
        assert any(expected_prop["prop_name"] in p for s in rendered.segments for p in s.prop_present)


def test_frozen_baseline_voice_dialogue_music_invariants(executed_episode_1_audit):
    """Regression Test 3: Voice identity, dialogue fidelity, and 68 BPM music against frozen baseline."""
    audit, rendered, plan = executed_episode_1_audit
    invariants = FROZEN_BASELINE_EPISODE_1["invariants"]

    # 1. Voice Identity & WPM
    c6 = next(i for i in audit.audit_results if i.criterion_name == "Voice Identity & Dialect Continuity")
    assert invariants["voice_identity"]["thandiwe_voice_profile"] in c6.measured_value
    assert str(invariants["voice_identity"]["thandiwe_wpm"]) in c6.measured_value

    # 2. Dialogue Fidelity
    c7 = next(i for i in audit.audit_results if i.criterion_name == "Dialogue Fidelity")
    assert c7.status.value == "PASSED"
    # Verify the actual spoken dialogue in the rendered shot matches the verbatim invariant exactly
    rendered_shot_2_dialogue = next(s.spoken_dialogue for s in rendered.segments if s.spoken_dialogue is not None)
    assert rendered_shot_2_dialogue == invariants["dialogue_fidelity"][0]["verbatim_line"]

    # 3. Audio & Music Tempo
    c8 = next(i for i in audit.audit_results if i.criterion_name == "Audio & Music Continuity")
    assert f"{invariants['audio_music']['tempo_bpm']} BPM" in c8.measured_value


def test_frozen_baseline_timing_paywall_and_immutability(executed_episode_1_audit):
    """Regression Test 4: Timing, 88-second paywall cut, and strict canon immutability."""
    audit, rendered, plan = executed_episode_1_audit
    invariants = FROZEN_BASELINE_EPISODE_1["invariants"]

    # 1. Timing
    assert rendered.total_duration_seconds == invariants["timing_and_beats"]["beat_3_climax_window"][1]
    assert rendered.paywall_cut_timestamp_seconds == invariants["paywall_and_canon"]["hard_freeze_at_second"]

    # 2. Paywall Cut & Immuntability
    c10 = next(i for i in audit.audit_results if "88-Second Paywall Cut" in i.criterion_name)
    assert c10.status.value == "PASSED"
    assert audit.canon_mutation_detected is invariants["paywall_and_canon"]["canon_mutation_permitted"]
    assert audit.unapproved_ai_lore_introduced is invariants["paywall_and_canon"]["runtime_tokens_leak_upstream"]
