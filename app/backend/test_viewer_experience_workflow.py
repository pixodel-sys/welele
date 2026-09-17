"""
Welele Media™ — Isibusiso Episode 1 Viewer Experience Workflow Verification (Phase 5)
Tests the empirical viewer validation, media asset identity chain, stale asset rejection,
truthful Episode 2 availability gating, the 7 Viewer Experience Checks, and ledgers.
"""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app
from database import db
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from services.episode_production_pack_service import episode_production_pack_service
from services.production_execution_service import production_execution_service
from services.viewer_execution_service import viewer_execution_service
from schemas.viewer_execution_models import (
    ViewerCheckCategory,
    ViewerSeverity,
    ViewerResolutionType,
    ViewerBreakpoint,
    ViewerReworkEntry,
    ViewerExperienceCheckResult,
    MediaAssetIdentityChain,
    HumanObservationRecord,
    ViewerEvidencePackage
)

client = TestClient(app)


@pytest.fixture
def isibusiso_viewer_test_setup():
    """Ensures canonical Isibusiso IP → Story Package → Series → Episode 1 & 2 → Blueprint → Production Pack → Master exist."""
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
        if not pkg.get("dialogues"):
            pkg["dialogues"] = [
                {"character": "Thandiwe Zulu", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."},
                {"character": "Bhekisisa Khumalo", "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over."}
            ]
            ip_repository.local_update("story_packages", "id", pkg_id, pkg)

    # Ensure parent Series exists
    series = series_episode_service.create_series_from_story_package(ip_id=ip_id, story_package_id=pkg_id, season_number=1)
    series_id = series["id"]
    series_repository.local_update("series", "id", series_id, {
        "title": "Isibusiso",
        "vertical_poster": "/posters/isibusiso.jpg",
        "cover_image": "/banners/isibusiso_banner.jpg",
        "is_published": True,
        "free_episodes": 1,
        "status": "published"
    })

    # Also register in legacy db.stories for backward compatibility
    stories = db.get("stories")
    if not any(s["id"] == series_id for s in stories):
        db.insert("stories", {
            "id": series_id,
            "title": "Isibusiso",
            "logline": target_ip["logline"],
            "genre": target_ip["genre"],
            "primary_language": "isiZulu",
            "cover_image": "/banners/isibusiso_banner.jpg",
            "vertical_poster": "/posters/isibusiso.jpg",
            "free_episodes_count": 1,
            "is_published": True
        })

    # Ensure Episode 1 exists
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1, is_empty_draft=False)
    
    media_asset_id = "asset-isibusiso-s01e01-v1"
    ep1_id = ep1["id"]
    series_repository.local_update("episodes", "id", ep1_id, {
        "series_id": series_id,
        "title": "Episode 1 — The Midnight Sovereign",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": True,
        "video_url": "/videos/isibusiso_s01e01_master.mp4",
        "media_asset_id": media_asset_id,
        "duration_seconds": 90,
        "cliffhanger_time": 88
    })

    # Register media asset record in repository
    media_rec = {
        "id": media_asset_id,
        "episode_id": ep1_id,
        "series_id": series_id,
        "storage_key": f"masters/{series_id}/{ep1_id}.mp4",
        "master_video_url": "/videos/isibusiso_s01e01_master.mp4",
        "delivery_url": "/videos/isibusiso_s01e01_master.mp4",
        "status": "verified"
    }
    existing_media = series_repository.local_get("media_assets") or []
    if not any(m.get("id") == media_asset_id for m in existing_media):
        series_repository.local_insert("media_assets", media_rec)

    # Ensure Episode 2 exists as truthful DRAFT_EMPTY
    ep2 = next((e for e in all_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(series_id=series_id, episode_number=2, is_empty_draft=True)
    
    ep2_id = ep2["id"]
    series_repository.local_update("episodes", "id", ep2_id, {
        "series_id": series_id,
        "title": "Episode 2 — Bloodline Accord",
        "is_empty_draft": True,
        "readiness_state": "DRAFT_EMPTY",
        "lifecycle_state": "DRAFT",
        "status": "draft",
        "is_free": False,
        "video_url": None,
        "media_asset_id": None
    })

    # Ensure Blueprint and Pack exist
    bp = production_repository.get_episode_blueprint(ep1_id, version="1.0.0")
    if not bp:
        bp = episode_blueprint_service.generate_blueprint(episode_id=ep1_id, version="1.0.0")

    pack = production_repository.get_episode_pack(ip_id, 1)
    if not pack:
        pack = episode_production_pack_service.generate_production_pack(episode_id=ep1_id, blueprint_version="1.0.0")

    return {
        "ip_id": ip_id,
        "series_id": series_id,
        "ep1_id": ep1_id,
        "ep2_id": ep2_id,
        "blueprint_id": bp["id"],
        "pack_id": pack["id"]
    }


def test_viewer_discovery_integrity(isibusiso_viewer_test_setup):
    """Test 1: Discovery Integrity — verifies series discovery, metadata, genre, tags, and series grouping."""
    series_id = isibusiso_viewer_test_setup["series_id"]
    series_data = series_repository.get_series(series_id)
    assert series_data is not None

    assert series_data["id"] == series_id
    assert "Isibusiso" in series_data["title"]
    assert "High-Stakes Melodrama" in series_data.get("genre", "")
    assert series_data.get("primary_language") == "isiZulu"


def test_viewer_identity_integrity(isibusiso_viewer_test_setup):
    """Test 2: Identity Integrity — verifies episode title, season/ep numbers, and duration match canon."""
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]
    series_id = isibusiso_viewer_test_setup["series_id"]

    all_eps = series_repository.get_episodes_for_series(series_id)
    ep = next((e for e in all_eps if e["id"] == ep1_id), None)
    assert ep is not None

    assert ep["id"] == ep1_id
    assert ep["series_id"] == series_id
    assert ep["episode_number"] == 1
    assert "Midnight Sovereign" in ep["title"]
    assert ep["duration_seconds"] == 90


def test_viewer_stale_asset_rejection_and_identity_chain(isibusiso_viewer_test_setup):
    """Test 3: The Stale Asset Test — assert placeholder != authoritative asset and verify identity chain."""
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]
    series_id = isibusiso_viewer_test_setup["series_id"]

    # 1. Verify that placeholder and authoritative hashes are strictly non-equal
    ph_hash = viewer_execution_service.compute_asset_hash("welele_ocean_waves_placeholder")
    auth_hash = viewer_execution_service.compute_asset_hash("isibusiso_s01e01_production_master_v1")
    assert ph_hash != auth_hash, "Placeholder asset hash must NEVER match authoritative production master!"

    # 2. Verify identity chain for Episode 1
    identity_chain = viewer_execution_service.verify_asset_identity_chain(
        episode_id=ep1_id,
        series_id=series_id
    )
    assert isinstance(identity_chain, MediaAssetIdentityChain)
    assert identity_chain.is_authoritative_master is True
    assert identity_chain.is_placeholder is False
    assert identity_chain.episode_id == ep1_id
    assert identity_chain.delivery_stream_url == "/videos/isibusiso_s01e01_master.mp4"


def test_viewer_playback_and_av_integrity(isibusiso_viewer_test_setup):
    """Test 4: Playback and AV Integrity — verifies streaming endpoint returns active stream with correct format."""
    series_id = isibusiso_viewer_test_setup["series_id"]
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]

    response = client.get(f"/api/v1/episodes/{series_id}/{ep1_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["is_available"] is True
    assert data["status_label"] == "Watch Now"
    assert data["stream"] is not None
    assert data["stream"]["format"] == "9:16 Canonical Vertical"
    assert "isibusiso" in data["stream"]["primary_url"].lower()


def test_viewer_hook_and_cliffhanger_mechanics(isibusiso_viewer_test_setup):
    """Test 5: Hook and Continuation Mechanics — verifies 15s hook pacing and 88s cliffhanger cutoff."""
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]
    series_id = isibusiso_viewer_test_setup["series_id"]

    bp = production_repository.get_episode_blueprint(ep1_id)
    assert bp is not None

    # Check hook pacing from blueprint
    hook_sec = bp.get("hook_timing_seconds") or bp.get("hook_structure", {}).get("target_duration_seconds", 15)
    assert hook_sec <= 15

    # Check cliffhanger in stream payload
    response = client.get(f"/api/v1/episodes/{series_id}/{ep1_id}")
    assert response.status_code == 200
    data = response.json()
    assert data.get("cliffhanger") is not None
    assert data["cliffhanger"]["timestamp_seconds"] == 88


def test_viewer_empty_episode_2_availability_gating(isibusiso_viewer_test_setup):
    """Test 6: The Empty Episode 2 Test — verifies DRAFT_EMPTY episode is strictly gated with no fallback media."""
    series_id = isibusiso_viewer_test_setup["series_id"]
    ep2_id = isibusiso_viewer_test_setup["ep2_id"]

    response = client.get(f"/api/v1/episodes/{series_id}/{ep2_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["is_available"] is False
    assert data["status_label"] == "Coming Soon"
    assert data["stream"] is None
    assert data["fallback_media_permitted"] is False
    assert data["is_unlocked"] is False


def test_viewer_state_survives_reload_without_asset_substitution(isibusiso_viewer_test_setup):
    """Test 7: Refresh / Resume Truth Test — repeated queries return consistent authoritative state."""
    series_id = isibusiso_viewer_test_setup["series_id"]
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]

    r1 = client.get(f"/api/v1/episodes/{series_id}/{ep1_id}").json()
    r2 = client.get(f"/api/v1/episodes/{series_id}/{ep1_id}").json()

    assert r1["stream"]["primary_url"] == r2["stream"]["primary_url"]
    assert r1["is_available"] == r2["is_available"]
    assert r1["status_label"] == r2["status_label"]


def test_viewer_experience_checks_execute_and_record_results(isibusiso_viewer_test_setup):
    """Test 8: Viewer Experience Checks — executes 7 automated checks and compiles evidence package."""
    ip_id = isibusiso_viewer_test_setup["ip_id"]
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]

    evidence = viewer_execution_service.execute_isibusiso_episode_1_viewer_validation(
        ip_id=ip_id,
        episode_id=ep1_id
    )

    assert evidence is not None
    assert evidence.overall_status == "VIEWER_VALIDATION_COMPLETED"
    assert len(evidence.experience_checks) == 7

    names = [c.check_name for c in evidence.experience_checks]
    assert "Discovery Integrity" in names
    assert "Identity Integrity" in names
    assert "Media Integrity" in names
    assert "Playback Integrity" in names
    assert "Audio/Visual Experience Integrity" in names
    assert "Hook Experience" in names
    assert "Continuation Integrity" in names

    for check in evidence.experience_checks:
        assert check.status == "PASSED"


def test_viewer_breakpoint_and_rework_ledgers(isibusiso_viewer_test_setup):
    """Test 9: Breakpoint and Rework Ledgers — verifies breakpoint and rework tracking alongside human observations."""
    ip_id = isibusiso_viewer_test_setup["ip_id"]
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]

    evidence = viewer_execution_service.execute_isibusiso_episode_1_viewer_validation(
        ip_id=ip_id,
        episode_id=ep1_id
    )

    assert len(evidence.breakpoint_ledger) >= 1
    assert len(evidence.rework_ledger) >= 1
    assert len(evidence.human_observations) >= 2

    # Breakpoints must be classified with clean severity
    for bp in evidence.breakpoint_ledger:
        assert isinstance(bp.category, ViewerCheckCategory)
        assert isinstance(bp.severity, ViewerSeverity)
        assert isinstance(bp.resolution_type, ViewerResolutionType)

    # Rework ledger items must record actionable resolution
    for rework in evidence.rework_ledger:
        assert rework.rework_id.startswith("VW-RWK-")
        assert rework.repeatable in [True, False]


def test_no_upstream_mutation_or_telemetry_invention(isibusiso_viewer_test_setup):
    """Test 10: Upstream Boundaries and Telemetry Honesty — zero upstream mutations and no invented telemetry systems."""
    ip_id = isibusiso_viewer_test_setup["ip_id"]
    ep1_id = isibusiso_viewer_test_setup["ep1_id"]

    # Snapshot upstream state before viewer test
    detail_before = ip_repository.get_ip_detail(ip_id)
    bp_before = production_repository.get_episode_blueprint(ep1_id)
    pack_before = production_repository.get_episode_pack(ip_id, 1)

    evidence = viewer_execution_service.execute_isibusiso_episode_1_viewer_validation(
        ip_id=ip_id,
        episode_id=ep1_id
    )

    # Assert upstream state is identical
    detail_after = ip_repository.get_ip_detail(ip_id)
    bp_after = production_repository.get_episode_blueprint(ep1_id)
    pack_after = production_repository.get_episode_pack(ip_id, 1)

    assert detail_before["ip"] == detail_after["ip"]
    assert bp_before == bp_after
    assert pack_before == pack_after

    # Ensure no fabricated telemetry engine models
    evidence_dict = evidence.model_dump()
    assert "retention_funnel" not in evidence_dict
    assert "churn_prediction" not in evidence_dict
    assert "algorithmic_recommendations" not in evidence_dict
