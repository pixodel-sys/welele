"""
Test Suite: Episode 1 End-to-End Media Production & 10-Point Continuity Audit
Validates:
1. Media Rendering & Assembly from compiled AI Execution Plan (88-second vertical episode).
2. The 10-Point Empirical Continuity Audit:
   - Character identity continuity
   - Wardrobe continuity
   - Location/spatial continuity
   - Lighting/visual-language continuity
   - Prop continuity (Royal ink-mark & customary ledger)
   - Voice identity and dialect
   - Dialogue fidelity
   - Audio/music continuity
   - Episode timing and beat boundaries
   - 88-second paywall cut & no narrative mutation
3. Verification that NO unapproved AI lore or synthetic canon leaks back upstream.
"""

import pytest
from repositories.ip_repository import ip_repository
from services.production_bible_service import production_bible_service
from services.ai_production_adapter_service import ai_production_adapter_compiler
from services.media_production_audit_service import (
    media_production_audit_service,
    AuditItemStatus
)
from schemas.production_schemas import (
    ProductionBibleModel,
    EpisodeProductionPackModel
)


@pytest.fixture
def isibusiso_seed_and_compiled_plan():
    """Seeds Isibusiso canonical state, generates Production Document, and compiles AI Plan."""
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

    plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)
    return bible, pack, plan


def test_rendered_media_end_to_end_assembly(isibusiso_seed_and_compiled_plan):
    """
    Test 1: Render and assemble the actual 88-second vertical media package from compiled plan.
    """
    bible, pack, plan = isibusiso_seed_and_compiled_plan

    rendered_media = media_production_audit_service.render_episode_media(plan)

    assert rendered_media.aspect_ratio == "9:16"
    assert rendered_media.resolution == "1080x1920"
    assert rendered_media.total_duration_seconds == 88.0
    assert rendered_media.paywall_cut_timestamp_seconds == 88.0
    assert len(rendered_media.segments) == 3
    assert rendered_media.media_url.endswith(".mp4")


def test_ten_point_continuity_audit_fidelity(isibusiso_seed_and_compiled_plan):
    """
    Test 2: Execute the rigorous 10-Point Media Continuity Audit.
    Verifies that the rendered media strictly adheres to the source Production Document.
    """
    bible, pack, plan = isibusiso_seed_and_compiled_plan

    rendered_media = media_production_audit_service.render_episode_media(plan)
    audit_report = media_production_audit_service.audit_rendered_media_against_source(
        rendered=rendered_media,
        plan=plan,
        bible=bible,
        pack=pack
    )

    # 1. Overall Audit Verdict
    assert audit_report.all_checks_passed is True
    assert audit_report.overall_fidelity_score >= 0.95
    assert audit_report.canon_mutation_detected is False
    assert audit_report.unapproved_ai_lore_introduced is False
    assert len(audit_report.audit_results) == 10

    # 2. Check 1: Character identity continuity
    c1 = next(i for i in audit_report.audit_results if i.criterion_name == "Character Identity Continuity")
    assert c1.status == AuditItemStatus.PASSED
    assert c1.fidelity_score >= 0.95

    # 3. Check 2: Wardrobe continuity
    c2 = next(i for i in audit_report.audit_results if i.criterion_name == "Wardrobe Continuity")
    assert c2.status == AuditItemStatus.PASSED

    # 4. Check 3: Location/spatial continuity
    c3 = next(i for i in audit_report.audit_results if i.criterion_name == "Location / Spatial Continuity")
    assert c3.status == AuditItemStatus.PASSED

    # 5. Check 4: Lighting & visual language
    c4 = next(i for i in audit_report.audit_results if i.criterion_name == "Lighting & Visual Language Continuity")
    assert c4.status == AuditItemStatus.PASSED
    assert "2700" in c4.measured_value and "5600" in c4.measured_value

    # 6. Check 5: Prop continuity (Royal ink-mark and customary ledger)
    c5 = next(i for i in audit_report.audit_results if "Key Prop Continuity" in i.criterion_name)
    assert c5.status == AuditItemStatus.PASSED
    assert c5.fidelity_score == 1.0

    # 7. Check 6: Voice identity & dialect
    c6 = next(i for i in audit_report.audit_results if i.criterion_name == "Voice Identity & Dialect Continuity")
    assert c6.status == AuditItemStatus.PASSED

    # 8. Check 7: Dialogue fidelity
    c7 = next(i for i in audit_report.audit_results if i.criterion_name == "Dialogue Fidelity")
    assert c7.status == AuditItemStatus.PASSED

    # 9. Check 8: Audio & music continuity (68 BPM)
    c8 = next(i for i in audit_report.audit_results if i.criterion_name == "Audio & Music Continuity")
    assert c8.status == AuditItemStatus.PASSED
    assert "68 BPM" in c8.measured_value

    # 10. Check 9 & 10: Episode timing, beat boundaries, and 88-second paywall cut
    c9 = next(i for i in audit_report.audit_results if i.criterion_name == "Episode Timing & Beat Boundaries")
    assert c9.status == AuditItemStatus.PASSED

    c10 = next(i for i in audit_report.audit_results if "88-Second Paywall Cut" in i.criterion_name)
    assert c10.status == AuditItemStatus.PASSED
    assert "88.0s" in c10.measured_value
