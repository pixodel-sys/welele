"""
Welele Media™ — Episode Blueprint Architecture & Production Integrity Test Suite (Phase 2 Downstream Planning Layer)
Tests all 8 Production Integrity Invariants + Isibusiso Season 1 Episode 1 End-to-End Specimen:
  1 — Canon Mutation Rejection
  2 — Canon Duplication Prevention
  3 — Hallucinated Production Detail Rejection (Sparse-Input Honesty)
  4 — Continuity Break Prevention
  5 — Emotional Movement Integrity (Validation of Full Emotional Movement)
  6 — Cliffhanger Integrity (Validation of Unresolved Question & Consequence)
  7 — Empty Episode Incomplete Shell Honesty
  8 — Lineage Traceability & Distinct Artifact Lineage Hash
"""

import pytest
from fastapi.testclient import TestClient
from main import app

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from schemas.production_schemas import CanonMutationError
from schemas.episode_blueprint_schemas import (
    BlueprintStatus,
    BlueprintProvenance,
    BeatType,
    BlueprintEmotionalTrajectory,
    BlueprintCliffhanger,
    EpisodeBlueprintModel
)

client = TestClient(app)


@pytest.fixture
def isibusiso_canonical_setup():
    """Ensures canonical Isibusiso IP, M3 Story Package, Series, and Episode 1 exist."""
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
        updated = False
        if not pkg.get("world_rules"):
            pkg["world_rules"] = [
                {"rule_key": "RULE_CUSTOMARY_LINEAGE_COVENANT", "summary": "Royal birthright cannot be alienated or sold via civil contract."},
                {"rule_key": "RULE_SACRED_SUCCESSION_PRIMACY", "summary": "Customary elder council must verify physical ink-mark before coronation."}
            ]
            updated = True
        if not pkg.get("chronology_spine"):
            pkg["chronology_spine"] = [
                {"anchor_number": 1, "anchor_name": "Midnight Delivery", "summary": "Thandiwe delivers baby by candlelight; discovers royal ink-mark."},
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."},
                {"anchor_number": 3, "anchor_name": "Threshold Stand", "summary": "Thandiwe refuses settlement; community forms protective barrier."}
            ]
            updated = True
        if not pkg.get("plants"):
            pkg["plants"] = [
                {"plant": "Royal Ink-Mark on infant shoulder", "status": "PLANTED", "payoff_target": "Ep 1 & Season Finale"},
                {"plant": "1912 Land Covenant Seal in clinic safe", "status": "PLANTED", "payoff_target": "Ep 3 & Council Climax"}
            ]
            updated = True
        if not pkg.get("beats"):
            pkg["beats"] = [
                {"beat_number": 1, "label": "Cold Open: Midnight Delivery", "timestamp_seconds": 15, "action_description": "Midwife Thandiwe delivers newborn."},
                {"beat_number": 2, "label": "Dawn Confrontation", "timestamp_seconds": 50, "action_description": "Khumalo convoy arrives with cash."},
                {"beat_number": 3, "label": "Cliffhanger Paywall Cut", "timestamp_seconds": 88, "action_description": "Guards draw weapons."}
            ]
            updated = True
        if updated:
            ip_repository.local_update("story_packages", "id", pkg_id, pkg)

    # Ensure parent Series exists
    series = series_episode_service.create_series_from_story_package(ip_id=ip_id, story_package_id=pkg_id, season_number=1)
    series_id = series["id"]

    # Ensure Episode 1 exists and is not empty draft
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1, is_empty_draft=False)
    else:
        series_repository.local_update("episodes", "id", ep1["id"], {"is_empty_draft": False})
        ep1["is_empty_draft"] = False

    return {
        "ip_id": ip_id,
        "story_package_id": pkg_id,
        "series_id": series_id,
        "episode_id": ep1["id"]
    }


def test_production_integrity_check_1_canon_mutation_rejection(isibusiso_canonical_setup):
    """
    Production Integrity Check 1: Canon Mutation Rejection
    Attempting to mutate upstream Story Package logline, character bible, world rules,
    chronology, or Forge Configuration through the Blueprint must raise CanonMutationError.
    """
    with pytest.raises(CanonMutationError, match="Downstream Truth Boundary Violation"):
        episode_blueprint_service.validate_canonical_mutation_boundary({
            "logline": "Mutated logline attempting to corrupt Story Package.",
            "character_bible": [{"name": "Mutated Character"}]
        })

    with pytest.raises(CanonMutationError, match="Downstream Truth Boundary Violation"):
        episode_blueprint_service.validate_canonical_mutation_boundary({
            "world_rules": [{"rule": "Corrupted Customary Law"}],
            "forge_configuration_id": "CFG-HACKED"
        })


def test_production_integrity_check_2_canon_duplication_prevention(isibusiso_canonical_setup):
    """
    Production Integrity Check 2: Canon Duplication Prevention
    Verify that Blueprint character and world data references upstream entities
    (character_id_ref, world_rules_refs) rather than creating duplicate canonical records.
    """
    ep_id = isibusiso_canonical_setup["episode_id"]
    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_id)

    # 1. Characters must use references
    assert len(blueprint["character_arcs"]) >= 3
    for arc in blueprint["character_arcs"]:
        assert "character_name_ref" in arc
        assert "character_id_ref" in arc
        assert arc["provenance"] == BlueprintProvenance.DERIVED.value

    # 2. Character Bible & World Lore must not be duplicated into the root blueprint payload
    assert "character_bible" not in blueprint
    assert "world_lore" not in blueprint
    assert "supernatural_rules" not in blueprint

    # 3. World rules must be stored as key references
    assert "RULE_CUSTOMARY_LINEAGE_COVENANT" in blueprint["continuity_context"]["world_rules_refs"]


def test_production_integrity_check_3_hallucinated_production_detail_sparse_honesty(isibusiso_canonical_setup):
    """
    Production Integrity Check 3: Hallucinated Production Detail Rejection
    When fed a sparse episode, the Blueprint must NOT invent unbacked camera lenses,
    lighting temperatures, costumes, actors, or dialogue as facts.
    """
    series_id = isibusiso_canonical_setup["series_id"]
    
    # Create or retrieve sparse draft episode
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep_sparse = next((e for e in all_eps if e.get("episode_number") == 99), None)
    if not ep_sparse:
        ep_sparse = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=99,
            is_empty_draft=True
        )
    else:
        series_repository.local_update("episodes", "id", ep_sparse["id"], {"is_empty_draft": True})
        ep_sparse["is_empty_draft"] = True

    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_sparse["id"])

    # Must be marked INCOMPLETE
    assert blueprint["status"] == BlueprintStatus.INCOMPLETE.value
    assert blueprint["completeness_audit"]["is_sparse_draft"] is True
    assert blueprint["completeness_audit"]["is_complete"] is False

    # Unbacked sparse fields must be explicitly listed
    unbacked = blueprint["completeness_audit"]["unbacked_sparse_fields"]
    assert any("exact_camera_lenses: NOT_SPECIFIED" in f for f in unbacked)
    assert any("dialogue: UNKNOWN" in f for f in unbacked)
    assert any("lighting_temperatures: NOT_SPECIFIED" in f for f in unbacked)

    # Narrative actions must be NOT_SPECIFIED, not manufactured hallucinations
    for beat in blueprint["beat_sequence"]:
        assert beat["narrative_action"] == "NOT_SPECIFIED"
        assert beat["location_ref"] == "UNKNOWN"
        assert beat["provenance"] == BlueprintProvenance.UNKNOWN.value


def test_production_integrity_check_4_continuity_break_prevention(isibusiso_canonical_setup):
    """
    Production Integrity Check 4: Continuity Break Prevention
    Verify that the Blueprint cannot casually contradict or omit inherited active plants
    or world rules passed from previous state.
    """
    ep_id = isibusiso_canonical_setup["episode_id"]
    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_id)

    inherited_state = {
        "active_plants": ["Royal Ink-Mark on infant shoulder", "1912 Land Covenant Seal in clinic safe"],
        "world_rules_refs": ["RULE_CUSTOMARY_LINEAGE_COVENANT"]
    }

    # Valid continuity verification passes
    episode_blueprint_service.validate_continuity_integrity(blueprint, inherited_state)

    # Contradicted / missing plant raises error
    corrupted_state = {
        "active_plants": ["Ghost Plant from Nowhere That Must Exist"],
        "world_rules_refs": ["RULE_CUSTOMARY_LINEAGE_COVENANT"]
    }
    with pytest.raises(ValueError, match="Continuity Break: Blueprint omitted active narrative plants"):
        episode_blueprint_service.validate_continuity_integrity(blueprint, corrupted_state)


def test_production_integrity_check_5_emotional_movement_validation():
    """
    Production Integrity Check 5: Emotional Movement Integrity
    Verify that the Blueprint cannot claim emotional transformation without identifying
    starting state → trigger → change → ending state.
    """
    # Valid emotional trajectory passes
    valid_trajectory = BlueprintEmotionalTrajectory(
        starting_state="Quiet maternal devotion",
        pressure_context="Violent arrival of Khumalo family",
        escalation_point="Surrogacy contract presented",
        emotional_turn_trigger="Recognition of the royal birthmark",
        emotional_shift="From passive grief to fierce defiant protection",
        resulting_behavior="Sounds emergency community bell and blocks doorway",
        ending_state="Spiritual anchor of community defiance"
    )
    episode_blueprint_service.validate_emotional_movement(valid_trajectory)

    # Invalid empty trigger raises error
    invalid_trajectory = BlueprintEmotionalTrajectory(
        starting_state="Quiet maternal devotion",
        pressure_context="Violent arrival",
        escalation_point="Contract presented",
        emotional_turn_trigger="NOT_SPECIFIED",
        emotional_shift="Major emotional transformation",
        resulting_behavior="UNKNOWN",
        ending_state="Defiant"
    )
    with pytest.raises(ValueError, match="Emotional Integrity Error"):
        episode_blueprint_service.validate_emotional_movement(invalid_trajectory)


def test_production_integrity_check_6_cliffhanger_integrity_validation():
    """
    Production Integrity Check 6: Cliffhanger Integrity
    Verify that a cliffhanger must contain an actual unresolved narrative consequence/question
    rather than merely being labeled 'CLIFFHANGER' or 'Strong cliffhanger'.
    """
    valid_cliffhanger = BlueprintCliffhanger(
        narrative_event="Armed mining guards draw weapons as township crowd gathers with sjamboks",
        unresolved_question="Will Bhekisisa order guards to fire or retreat before the customary elders arrive?",
        consequence="Imminent township bloodbath or violent abduction of the royal infant",
        affected_characters=["Thandiwe Zulu", "Bhekisisa Khumalo"],
        timing_seconds=88,
        next_episode_dependency="Episode 2 Dawn Arrival"
    )
    episode_blueprint_service.validate_cliffhanger(valid_cliffhanger)

    # Hollow placeholder cliffhanger raises error
    hollow_cliffhanger = BlueprintCliffhanger(
        narrative_event="End of episode cut",
        unresolved_question="Strong cliffhanger",
        consequence="",
        affected_characters=[],
        timing_seconds=88,
        next_episode_dependency="Next episode"
    )
    with pytest.raises(ValueError, match="Cliffhanger Integrity Error"):
        episode_blueprint_service.validate_cliffhanger(hollow_cliffhanger)


def test_production_integrity_check_7_empty_episode_shell_honesty(isibusiso_canonical_setup):
    """
    Production Integrity Check 7: Empty Episode Handling
    An Episode marked DRAFT_EMPTY produces an incomplete Blueprint shell,
    never claiming false completeness or green lights.
    """
    series_id = isibusiso_canonical_setup["series_id"]
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep_empty = next((e for e in all_eps if e.get("episode_number") == 98), None)
    if not ep_empty:
        ep_empty = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=98,
            is_empty_draft=True
        )
    else:
        series_repository.local_update("episodes", "id", ep_empty["id"], {"is_empty_draft": True})
        ep_empty["is_empty_draft"] = True

    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_empty["id"])
    assert blueprint["status"] == BlueprintStatus.INCOMPLETE.value
    assert blueprint["completeness_audit"]["is_complete"] is False
    assert len(blueprint["completeness_audit"]["missing_required_elements"]) >= 4
    assert blueprint["dramatic_objective"]["episode_objective"] == "NOT_SPECIFIED"
    assert blueprint["dramatic_objective"]["protagonist_objective"] == "UNKNOWN"


def test_production_integrity_check_8_lineage_traceability_and_hash_separation(isibusiso_canonical_setup):
    """
    Production Integrity Check 8: Lineage Traceability & Hash Separation
    Verify Blueprint → Episode → Series → Story Package → Forge Configuration chain
    and ensure Blueprint computes its own unique artifact lineage hash.
    """
    ep_id = isibusiso_canonical_setup["episode_id"]
    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_id)

    # 1. Lineage Chain Verification
    assert blueprint["episode_id"] == ep_id
    assert blueprint["series_id"] == isibusiso_canonical_setup["series_id"]
    assert blueprint["story_package_id"] == isibusiso_canonical_setup["story_package_id"]
    assert blueprint["ip_id"] == isibusiso_canonical_setup["ip_id"]
    assert blueprint["forge_configuration_id"] == "CFG-001"

    # 2. Artifact hash separation
    source_hash = blueprint["source_lineage_hash"]
    artifact_hash = blueprint["artifact_lineage_hash"]
    assert source_hash is not None
    assert artifact_hash is not None
    assert artifact_hash != source_hash
    assert len(artifact_hash) == 64  # SHA-256


def test_isibusiso_season_1_episode_1_specimen_end_to_end(isibusiso_canonical_setup):
    """
    Isibusiso Specimen: Complete end-to-end dramatic plan for Season 1 Episode 1.
    """
    ep_id = isibusiso_canonical_setup["episode_id"]
    blueprint = episode_blueprint_service.generate_blueprint(episode_id=ep_id, version="1.0.0")

    assert blueprint["id"].startswith("bp_")
    assert blueprint["status"] == BlueprintStatus.APPROVED.value
    assert blueprint["season_number"] == 1
    assert blueprint["episode_number"] == 1

    # 9-Beat Microdrama Structure
    beats = blueprint["beat_sequence"]
    assert len(beats) == 9
    beat_types = [b["beat_type"] for b in beats]
    assert beat_types == [
        BeatType.HOOK.value,
        BeatType.SETUP.value,
        BeatType.ESCALATION.value,
        BeatType.CONFLICT.value,
        BeatType.REVELATION.value,
        BeatType.EMOTIONAL_MOVEMENT.value,
        BeatType.CLIMAX.value,
        BeatType.CLIFFHANGER.value,
        BeatType.NEXT_EPISODE_SETUP.value
    ]

    # Hook & Cliffhanger
    assert "blackout" in blueprint["hook"]["narrative_event"].lower()
    assert "ink-mark" in blueprint["hook"]["narrative_event"].lower()
    assert blueprint["hook"]["timing_seconds"] == 15

    assert "unresolved_question" in blueprint["cliffhanger"]
    assert "consequence" in blueprint["cliffhanger"]
    assert blueprint["cliffhanger"]["timing_seconds"] == 88

    # Emotional Trajectory
    et = blueprint["emotional_trajectory"]
    assert "maternal" in et["starting_state"].lower() or "devotion" in et["starting_state"].lower()
    assert "defiant" in et["ending_state"].lower() or "confrontation" in et["ending_state"].lower()
