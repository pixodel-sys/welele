"""
Welele Media™ — Isibusiso Episode 1 Empirical Production Workflow Verification (Phase 4)
Tests the actual production execution, Breakpoint Ledger, Rework Ledger, Unit Sufficiency Audit,
and the 10 Production Integrity Checks.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from services.episode_production_pack_service import episode_production_pack_service
from services.production_execution_service import production_execution_service
from schemas.production_execution_models import (
    BreakpointCategory,
    BreakpointSeverity,
    ResolutionType,
    UnitSufficiencyStatus
)

client = TestClient(app)


@pytest.fixture
def isibusiso_production_test_setup():
    """Ensures canonical Isibusiso IP → Story Package → Series → Episode 1 → Blueprint → Production Pack exist."""
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
            "chronology_spine": [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."}
            ],
            "plants": [
                {"plant": "Royal Ink-Mark on infant shoulder", "status": "PLANTED", "payoff_target": "Ep 1 & Season Finale"},
                {"plant": "1912 Land Covenant Seal in clinic safe", "status": "PLANTED", "payoff_target": "Ep 3 & Council Climax"}
            ],
            "world_rules": [
                {"rule_key": "RULE_CUSTOMARY_LINEAGE_COVENANT", "summary": "Royal birthright cannot be alienated or sold via civil contract."},
                {"rule_key": "RULE_SACRED_SUCCESSION_PRIMACY", "summary": "Customary elder council must verify physical ink-mark before coronation."}
            ],
            "dialogues": [
                {"character": "Thandiwe Zulu", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."},
                {"character": "Bhekisisa Khumalo", "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over."}
            ],
            "beats": [
                {"beat_number": 1, "label": "Cold Open: Midnight Delivery", "timestamp_seconds": 15, "action_description": "Midwife Thandiwe delivers newborn."},
                {"beat_number": 2, "label": "Dawn Confrontation", "timestamp_seconds": 50, "action_description": "Khumalo convoy arrives with cash."},
                {"beat_number": 3, "label": "Cliffhanger Paywall Cut", "timestamp_seconds": 88, "action_description": "Guards draw weapons."}
            ],
            "forge_configuration_id": "CFG-001",
            "lineage_hash": "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        }
        ip_repository.local_insert("story_packages", pkg)
        pkg_id = "pkg_isibusiso_v1"
    else:
        pkg = story_packages[0]
        pkg_id = pkg["id"]

    # Ensure parent Series exists
    series = series_episode_service.create_series_from_story_package(ip_id=ip_id, story_package_id=pkg_id, season_number=1)
    series_id = series["id"]

    # Ensure Episode 1 exists
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1, is_empty_draft=False)
    else:
        series_repository.local_update("episodes", "id", ep1["id"], {"is_empty_draft": False})

    # Ensure Blueprint exists
    bp = production_repository.get_episode_blueprint(ep1["id"], version="1.0.0")
    if not bp:
        bp = episode_blueprint_service.generate_blueprint(episode_id=ep1["id"], version="1.0.0")

    # Ensure Production Pack exists
    pack = production_repository.get_episode_pack(ip_id, 1)
    if not pack:
        pack = episode_production_pack_service.generate_production_pack(episode_id=ep1["id"], blueprint_version="1.0.0")

    return {
        "ip_id": ip_id,
        "episode_id": ep1["id"],
        "series_id": series_id,
        "blueprint_id": bp["id"],
        "production_pack_id": pack["id"]
    }


def test_isibusiso_episode_1_full_production_execution(isibusiso_production_test_setup):
    """
    Validates empirical production execution of Isibusiso Episode 1 measured dynamically
    against the authoritative Episode Production Pack.
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    # Verify directly against authoritative upstream pack rather than hardcoded assumptions
    pack = production_repository.get_episode_pack(ip_id, 1) or episode_production_pack_service.generate_production_pack(episode_id=ep_id)
    expected_unit_count = len(pack.get("production_units", []))
    expected_duration = sum(u.get("estimated_duration_seconds", 10) for u in pack.get("production_units", []))

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)

    assert evidence.production_status == "PRODUCTION_TEST_COMPLETED"
    assert evidence.master_manifest.total_units_executed == expected_unit_count
    assert evidence.master_manifest.total_duration_seconds == expected_duration

    for unit_master in evidence.master_manifest.assembled_units:
        assert unit_master.unit_id.startswith("unit_ep1_")
        assert "aspect_ratio" in unit_master.video_asset_spec
        assert "sample_rate" in unit_master.dialogue_mix_spec
        assert "volume_level_db" in unit_master.ambience_mix_spec
        assert "volume_level_db" in unit_master.music_mix_spec
        assert unit_master.sync_status == "SYNCHRONIZED"


def test_production_breakpoint_ledger_integrity(isibusiso_production_test_setup):
    """
    Verifies that the Production Breakpoint Ledger records material issues with proper categorization,
    severities, and non-mutating resolutions.
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)
    breakpoints = evidence.breakpoint_ledger

    assert len(breakpoints) >= 5
    for bp in breakpoints:
        assert bp.breakpoint_id.startswith("BP-")
        assert bp.category in [
            BreakpointCategory.INFORMATION_GAP,
            BreakpointCategory.TRANSLATION_GAP,
            BreakpointCategory.CONTINUITY_GAP,
            BreakpointCategory.PRODUCTION_GAP,
            BreakpointCategory.TOOL_GAP
        ]
        assert bp.severity in [
            BreakpointSeverity.LOW,
            BreakpointSeverity.MEDIUM,
            BreakpointSeverity.HIGH,
            BreakpointSeverity.BLOCKING
        ]
        assert bp.resolution_type in [
            ResolutionType.NEW_PRODUCTION_DECISION,
            ResolutionType.MANUAL_PRODUCTION_WORK,
            ResolutionType.EXISTING_CANON,
            ResolutionType.TOOL_WORKAROUND
        ]
        # Empirical rule: Breakpoints should not silently trigger architecture changes during observation
        assert bp.architecture_change_required is False


def test_production_rework_ledger_tracking(isibusiso_production_test_setup):
    """
    Verifies that rework events are formally tracked with reasons, origins, effort descriptions, and repeatability.
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)
    reworks = evidence.rework_ledger

    assert len(reworks) >= 2
    for rwk in reworks:
        assert rwk.rework_id.startswith("RWK-")
        assert len(rwk.reason) > 10
        assert len(rwk.effort_description) > 5
        assert len(rwk.result) > 5


def test_unit_sufficiency_audit(isibusiso_production_test_setup):
    """
    Verifies unit-by-unit production sufficiency evaluation.
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)
    sufficiencies = evidence.unit_sufficiency_reports

    assert len(sufficiencies) == 9
    for s in sufficiencies:
        assert s.status in [
            UnitSufficiencyStatus.SUFFICIENT,
            UnitSufficiencyStatus.SUFFICIENT_WITH_PRODUCTION_DECISION
        ]
        assert "VIDEO" in s.track_readiness
        assert "DIALOGUE" in s.track_readiness
        assert "AMBIENCE" in s.track_readiness
        assert "MUSIC" in s.track_readiness


def test_10_production_integrity_checks(isibusiso_production_test_setup):
    """
    Verifies all 10 Production Integrity Checks:
      1 — Character Continuity Integrity
      2 — Location Continuity Integrity
      3 — Prop Continuity Integrity
      4 — Temporal Continuity Integrity
      5 — Knowledge Continuity Integrity
      6 — Track Synchronization Integrity
      7 — Emotional Continuity Integrity
      8 — Hook Integrity
      9 — Cliffhanger Integrity
      10 — Production Sufficiency Integrity
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)
    checks = evidence.production_integrity_checks

    assert len(checks) == 10
    expected_check_names = [
        "Character Continuity Integrity",
        "Location Continuity Integrity",
        "Prop Continuity Integrity",
        "Temporal Continuity Integrity",
        "Knowledge Continuity Integrity",
        "Track Synchronization Integrity",
        "Emotional Continuity Integrity",
        "Hook Integrity",
        "Cliffhanger Integrity",
        "Production Sufficiency Integrity"
    ]

    for idx, expected_name in enumerate(expected_check_names, 1):
        check = next((c for c in checks if c.check_id == str(idx)), None)
        assert check is not None, f"Check {idx} ({expected_name}) missing from integrity checks."
        assert check.check_name == expected_name
        assert check.status == "PASSED"
        assert len(check.findings) > 15


def test_no_unsupported_certification_claims(isibusiso_production_test_setup):
    """
    Verifies evidence-based status without unbacked certification claims.
    """
    ip_id = isibusiso_production_test_setup["ip_id"]
    ep_id = isibusiso_production_test_setup["episode_id"]

    evidence = production_execution_service.execute_isibusiso_episode_1_production(ip_id=ip_id, episode_id=ep_id)

    assert evidence.production_status == "PRODUCTION_TEST_COMPLETED"
    assert "CERTIFIED" not in evidence.production_status
    assert "100% PRODUCTION READY" not in evidence.production_status
    assert evidence.summary_metrics["production_integrity_checks_passed"] == 10
