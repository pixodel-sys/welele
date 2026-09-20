"""
Welele Media™ — Series & Episode Architecture Canonical Test Suite
Tests downstream governance invariants:
  1. Distinguishes upstream source_lineage_hash from downstream artifact_lineage_hash.
  2. M3 Story Package completion is the existing upstream authority (no duplicate certification).
  3. Existing Episode Production Pack referenced directly via production_pack_id.
  4. PACK_COORDINATED is strictly structural coordination, NOT production/distribution readiness.
  5. Continuity inheritance stored as references + mutations, never duplicated story lore.
  6. Downstream truth boundary & identity uniqueness tests.
  7. Isibusiso canonical specimen end-to-end (Season 1 → Ep 1, 2, 3).
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from services.series_episode_service import series_episode_service
from services.production_bible_service import production_bible_service
from schemas.production_schemas import CanonMutationError, ProvenanceType
from schemas.series_episode_schemas import (
    SeriesLifecycleState,
    EpisodeLifecycleState,
    EpisodeReadinessState
)

client = TestClient(app)


@pytest.fixture
def isibusiso_canonical_setup():
    """Ensures canonical Isibusiso IP with authoritative M3 Story Package exists."""
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
        # Ensure chronology spine and plants are present for downstream tests
        if not pkg.get("chronology_spine"):
            pkg["chronology_spine"] = [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."}
            ]
            pkg["plants"] = [
                {"plant": "Royal Ink-Mark on infant shoulder", "status": "PLANTED", "payoff_target": "Ep 1 & Season Finale"},
                {"plant": "1912 Land Covenant Seal in clinic safe", "status": "PLANTED", "payoff_target": "Ep 3 & Council Climax"}
            ]
            ip_repository.local_update("story_packages", "id", pkg_id, pkg)

    # Ensure Episode 1 Production Pack exists
    existing_packs = production_repository.local_get("episode_production_packs") or []
    if not any(p.get("ip_id") == ip_id and p.get("episode_number") == 1 for p in existing_packs):
        production_bible_service.generate_episode_production_pack(ip_id=ip_id, episode_number=1)

    return {"ip_id": ip_id, "story_package_id": pkg_id}


def test_story_package_to_series_relationship_and_lineage_separation(isibusiso_canonical_setup):
    """
    Correction 1 & 2:
    - Series references upstream M3 Story Package directly without duplicate certification.
    - Distinguishes source_lineage_hash from artifact_lineage_hash.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]

    series = series_episode_service.create_series_from_story_package(
        ip_id=ip_id,
        story_package_id=pkg_id,
        season_number=1
    )

    assert series["id"].startswith("series_")
    assert series["ip_id"] == ip_id
    assert series["story_package_id"] == pkg_id
    assert series["season_number"] == 1
    assert series["forge_configuration_id"] == "CFG-001"

    ip_detail = ip_repository.get_ip_detail(ip_id)
    pkg = next(p for p in ip_detail["story_packages"] if p["id"] == pkg_id)

    # Invariant 1: source_lineage_hash accurately references upstream package hash and != artifact_lineage_hash
    assert series["source_lineage_hash"] == (pkg.get("lineage_hash") or "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6")
    assert series["artifact_lineage_hash"] is not None
    assert series["artifact_lineage_hash"] != series["source_lineage_hash"]
    assert len(series["artifact_lineage_hash"]) == 64  # SHA-256


def test_orphan_prevention_on_series_and_episodes():
    """
    Truth Boundary & Orphan Handling:
    - Rejects Series creation referencing non-existent IP or Story Package.
    - Rejects Episode creation referencing non-existent Series.
    """
    # 1. Invalid IP
    with pytest.raises(ValueError, match="Orphan Error"):
        series_episode_service.create_series_from_story_package(
            ip_id="ip_non_existent_fake",
            story_package_id="pkg_fake"
        )

    # 2. Invalid Episode parent
    with pytest.raises(ValueError, match="Orphan Rejection"):
        series_episode_service.create_episode(
            series_id="series_ghost_does_not_exist",
            episode_number=1
        )


def test_identity_uniqueness_on_episodes(isibusiso_canonical_setup):
    """
    Identity Uniqueness:
    - Rejects duplicate episode_number creation inside the same Series.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)

    # Clean existing test episodes
    series_id = series["id"]
    existing_eps = [e for e in series_repository.local_get("episodes") if e.get("series_id") == series_id]
    for ep in existing_eps:
        series_repository.local_delete("episodes", "id", ep["id"])

    # First creation of Episode 1 succeeds
    ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1)
    assert ep1["episode_number"] == 1

    # Duplicate creation of Episode 1 must raise ValueError
    with pytest.raises(ValueError, match="Identity Collision"):
        series_episode_service.create_episode(series_id=series_id, episode_number=1)


def test_existing_production_pack_reference_and_pack_coordinated_definition(isibusiso_canonical_setup):
    """
    Correction 3 & 4:
    - Episode 1 references existing EpisodeProductionPack via production_pack_id.
    - PACK_COORDINATED strictly denotes structural 5-track coordination, NOT production readiness.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)
    series_id = series["id"]

    # Re-fetch or create Episode 1
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1)

    assert ep1["production_pack_id"] is not None
    assert ep1["production_pack_id"].startswith("epp_")

    # Invariant 4: PACK_COORDINATED is NOT production ready because physical media is missing
    assert ep1["readiness_state"] == EpisodeReadinessState.PACK_COORDINATED.value
    assert ep1["readiness_audit"]["is_empty_draft"] is False
    assert ep1["readiness_audit"]["has_production_pack_ref"] is True
    assert ep1["readiness_audit"]["has_master_video"] is False
    assert "Missing Master Video Asset (No High-DPI Camera Master)" in ep1["readiness_audit"]["missing_elements"]


def test_sparse_input_honesty_for_empty_draft_episodes(isibusiso_canonical_setup):
    """
    Sparse-Input Honesty:
    - Episode 2 and 3 (without packs or camera masters) are marked DRAFT_EMPTY / BEAT_OUTLINED.
    - Never receives false positive production-ready green lights.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)
    series_id = series["id"]

    all_eps = series_repository.get_episodes_for_series(series_id)
    ep2 = next((e for e in all_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=2,
            is_empty_draft=True
        )

    # Invariant: Empty draft must not claim false readiness
    assert ep2["readiness_state"] in [EpisodeReadinessState.DRAFT_EMPTY.value, EpisodeReadinessState.BEAT_OUTLINED.value]
    assert ep2["production_pack_id"] is None
    assert ep2["readiness_audit"]["has_master_video"] is False
    assert len(ep2["readiness_audit"]["missing_elements"]) > 0


def test_continuity_inheritance_as_references_without_lore_duplication(isibusiso_canonical_setup):
    """
    Correction 5:
    - Continuity is stored as references (anchor_number_ref, previous_episode_id_ref, active_plant_refs)
      plus explicit state mutations.
    - Does not duplicate character bibles or lore rules into the episode record.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)
    series_id = series["id"]

    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    ep2 = next((e for e in all_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(series_id=series_id, episode_number=2)

    cont2 = ep2["continuity_reference"]
    assert cont2["anchor_number_ref"] == 2
    assert cont2["anchor_name_ref"] == "Dawn Arrival"
    assert cont2["previous_episode_id_ref"] == ep1["id"]
    assert "Royal Ink-Mark on infant shoulder" in cont2["active_plant_refs"]

    # Verify zero character bible / lore duplication in episode payload
    assert "character_bible" not in ep2
    assert "world_rules" not in ep2


def test_canonical_mutation_boundary_enforcement(isibusiso_canonical_setup):
    """
    Truth Boundary Enforcement:
    - Downstream Series/Episode operations cannot mutate upstream Story Package facts.
    """
    ip_id = isibusiso_canonical_setup["ip_id"]
    pkg_id = isibusiso_canonical_setup["story_package_id"]
    series = series_episode_service.create_series_from_story_package(ip_id, pkg_id, 1)

    # Attempting to mutate upstream canon fields through downstream layer must raise CanonMutationError
    with pytest.raises(CanonMutationError, match="Downstream Truth Boundary Violation"):
        series_episode_service.validate_canonical_mutation_boundary(
            series_id=series["id"],
            proposed_updates={
                "characters": [{"name": "Corrupted Character"}],
                "world_rules": [{"rule": "Corrupted Rule"}]
            }
        )
