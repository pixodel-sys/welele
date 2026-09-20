"""
Welele Media™ — Episode Production Pack Architecture & Production Integrity Test Suite (Phase 3 Downstream Production Layer)
Tests all 12 Production Integrity Invariants + Isibusiso Episode 1 Specimen & Delta Report:
  1 — Canon Mutation Rejection
  2 — Provenance Escalation Rejection
  3 — Sparse Input Honesty (No Hallucinated Production Details)
  4 — Five-Track Coordination (Video, Dialogue, Narration, Ambience, Music)
  5 — Track Drift Rejection
  6 — Continuity Break Detection
  7 — Blueprint Bypass Rejection
  8 — Production Decision ≠ Canon
  9 — Empty Episode Incomplete Shell Honesty
  10 — Lineage Traceability & Hash Separation
  11 — Timing Conflict Detection
  12 — Unsupported Detail Rejection
  Isibusiso Episode 1 Specimen & Architectural Delta Observation
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
from schemas.production_schemas import CanonMutationError
from schemas.episode_production_pack_schemas import (
    PackReadinessState,
    ProductionProvenance,
    ProductionUnit,
    VideoTrackSpecification,
    DialogueTrackSpecification,
    NarrationTrackSpecification,
    AmbienceTrackSpecification,
    MusicTrackSpecification,
    EpisodeProductionPackModel
)

client = TestClient(app)


@pytest.fixture
def isibusiso_pipeline_setup():
    """Ensures canonical Isibusiso IP → Story Package → Series → Episode 1 → Blueprint exist."""
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
        # Ensure dialogues, plants, and rules exist
        if not pkg.get("dialogues"):
            pkg["dialogues"] = [
                {"character": "Thandiwe Zulu", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."},
                {"character": "Bhekisisa Khumalo", "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over."}
            ]
            ip_repository.local_update("story_packages", "id", pkg_id, pkg)

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
        ep1["is_empty_draft"] = False

    # Ensure authoritative Episode Blueprint exists
    bp = production_repository.get_episode_blueprint(ep1["id"], version="1.0.0")
    if not bp:
        bp = episode_blueprint_service.generate_blueprint(episode_id=ep1["id"], version="1.0.0")

    return {
        "ip_id": ip_id,
        "story_package_id": pkg_id,
        "series_id": series_id,
        "episode_id": ep1["id"],
        "blueprint_id": bp["id"]
    }


def test_production_integrity_check_1_canon_mutation_rejection():
    """
    Production Integrity Check 1: Canon Mutation Rejection
    Attempting to mutate character identity, motivation, world rule, chronology, or logline
    via Production Pack must raise CanonMutationError.
    """
    with pytest.raises(CanonMutationError, match="Downstream Truth Boundary Violation"):
        episode_production_pack_service.validate_canonical_mutation_boundary({
            "characters": [{"name": "Mutated Cast Member"}],
            "logline": "Mutated logline attempting to corrupt Story Package."
        })

    with pytest.raises(CanonMutationError, match="Downstream Truth Boundary Violation"):
        episode_production_pack_service.validate_canonical_mutation_boundary({
            "world_rules": [{"rule": "Corrupted Rule"}],
            "chronology_spine": [{"anchor_number": 999}]
        })


def test_production_integrity_check_2_provenance_escalation_rejection():
    """
    Production Integrity Check 2: Provenance Escalation Rejection
    Attempting to escalate GENERATED, DERIVED, PROPOSED, or PRODUCTION_DECISION into CANON must fail.
    """
    for non_canon in ["GENERATED", "DERIVED", "PROPOSED", "PRODUCTION_DECISION", "UNKNOWN"]:
        with pytest.raises(ValueError, match="Provenance Escalation Error"):
            episode_production_pack_service.validate_provenance_escalation(
                source_provenance=non_canon,
                target_provenance="CANON"
            )


def test_production_integrity_check_3_sparse_input_honesty_no_hallucinations(isibusiso_pipeline_setup):
    """
    Production Integrity Check 3: Sparse Input Honesty
    When given a sparse Episode / Blueprint, the Production Pack must not invent unbacked lenses,
    lighting, wardrobe, actors, vehicles, weapons, or music BPM.
    """
    series_id = isibusiso_pipeline_setup["series_id"]
    
    # Create or retrieve sparse episode 99
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep_sparse = next((e for e in all_eps if e.get("episode_number") == 99), None)
    if not ep_sparse:
        ep_sparse = series_episode_service.create_episode(series_id=series_id, episode_number=99, is_empty_draft=True)
    else:
        series_repository.local_update("episodes", "id", ep_sparse["id"], {"is_empty_draft": True, "readiness_state": "DRAFT_EMPTY"})
        ep_sparse["is_empty_draft"] = True
        ep_sparse["readiness_state"] = "DRAFT_EMPTY"

    # Generate sparse blueprint
    bp_sparse = episode_blueprint_service.generate_blueprint(episode_id=ep_sparse["id"])
    
    # Generate production pack from sparse blueprint
    pack = episode_production_pack_service.generate_production_pack(episode_id=ep_sparse["id"])

    assert pack["readiness_state"] in [PackReadinessState.INCOMPLETE.value, PackReadinessState.INCOMPLETE]
    assert pack["readiness_audit"]["is_sparse_draft"] is True
    
    for u in pack["production_units"]:
        assert u["video_track"]["visual_action"] == "NOT_SPECIFIED"
        assert u["video_track"]["lighting"] == "NOT_SPECIFIED"
        assert u["dialogue_track"]["dialogue"] == "NOT_SPECIFIED"
        assert u["music_track"]["cue"] == "NOT_SPECIFIED"
        assert u["music_track"]["style_instrumentation"] == "NOT_SPECIFIED"
        assert u["provenance"] == ProductionProvenance.DERIVED.value


def test_production_integrity_check_4_five_track_coordination(isibusiso_pipeline_setup):
    """
    Production Integrity Check 4: Five-Track Coordination
    Verify that every Production Unit coordinates all 5 tracks: Video, Dialogue, Narration, Ambience, Music.
    """
    ep_id = isibusiso_pipeline_setup["episode_id"]
    pack = episode_production_pack_service.generate_production_pack(episode_id=ep_id)

    assert len(pack["production_units"]) == 9
    for u in pack["production_units"]:
        assert u["unit_id"].startswith("unit_ep1_")
        assert "video_track" in u
        assert "dialogue_track" in u
        assert "narration_track" in u
        assert "ambience_track" in u
        assert "music_track" in u


def test_production_integrity_check_5_track_drift_rejection():
    """
    Production Integrity Check 5: Track Drift Rejection
    Flags contradiction between Video characters and Dialogue speaker without context.
    """
    unit_contradicted = ProductionUnit(
        unit_id="unit_ep1_01",
        sequence=1,
        episode_id="ep_test_01",
        blueprint_beat_ref="beat_ep1_01",
        story_purpose="Cold Open",
        location_ref="Clinic Room",
        character_refs=["Thandiwe Zulu"],
        estimated_duration_seconds=15,
        production_status="COORDINATED",
        video_track=VideoTrackSpecification(visual_action="Thandiwe alone delivers baby", environment="Clinic"),
        dialogue_track=DialogueTrackSpecification(speaker="Bhekisisa Khumalo", dialogue="Give me the child."),
        narration_track=NarrationTrackSpecification(),
        ambience_track=AmbienceTrackSpecification(),
        music_track=MusicTrackSpecification()
    )

    with pytest.raises(ValueError, match="Track Drift Contradiction"):
        episode_production_pack_service.validate_track_drift(unit_contradicted)


def test_production_integrity_check_6_continuity_break_detection(isibusiso_pipeline_setup):
    """
    Production Integrity Check 6: Continuity Break Detection
    Verifies that the Production Pack inherits continuity references (active plants, world rules).
    """
    ep_id = isibusiso_pipeline_setup["episode_id"]
    pack = episode_production_pack_service.generate_production_pack(episode_id=ep_id)

    # Unit 1 must have active plant continuity
    u1 = pack["production_units"][0]
    assert any("Royal ink-mark" in c for c in u1["continuity_refs"])
    assert "Royal Ink-Mark on infant shoulder" in u1["video_track"]["required_visual_elements"]


def test_production_integrity_check_7_blueprint_bypass_rejection():
    """
    Production Integrity Check 7: Blueprint Bypass Rejection
    Attempting to generate a Production Pack without an authoritative Episode Blueprint must fail.
    """
    with pytest.raises(ValueError, match="Blueprint Authority Error"):
        episode_production_pack_service.generate_production_pack(
            episode_id="ep_ghost_without_blueprint",
            blueprint_version="1.0.0"
        )


def test_production_integrity_check_8_production_decision_not_canon(isibusiso_pipeline_setup):
    """
    Production Integrity Check 8: Production Decision ≠ Canon
    Operational choices (e.g. practical clinic set) remain PRODUCTION_DECISION and never become CANON.
    """
    ep_id = isibusiso_pipeline_setup["episode_id"]
    pack = episode_production_pack_service.generate_production_pack(
        episode_id=ep_id,
        custom_decisions=[{
            "unit_id": "unit_ep1_01",
            "decision_type": "LOCATION_CHOICE",
            "decision": "Shoot interior delivery scene on practical clinic set in Soweto."
        }]
    )

    u1 = pack["production_units"][0]
    assert len(u1["production_decisions"]) == 1
    assert u1["production_decisions"][0]["provenance"] == ProductionProvenance.PRODUCTION_DECISION.value
    assert u1["production_decisions"][0]["provenance"] != ProductionProvenance.CANON.value


def test_production_integrity_check_9_empty_episode_incomplete_shell_honesty(isibusiso_pipeline_setup):
    """
    Production Integrity Check 9: Empty Episode Handling
    A DRAFT_EMPTY Episode produces an incomplete shell, never claiming READY_FOR_PRODUCTION.
    """
    series_id = isibusiso_pipeline_setup["series_id"]
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep_empty = next((e for e in all_eps if e.get("episode_number") == 98), None)
    if not ep_empty:
        ep_empty = series_episode_service.create_episode(series_id=series_id, episode_number=98, is_empty_draft=True)
    else:
        series_repository.local_update("episodes", "id", ep_empty["id"], {"is_empty_draft": True, "readiness_state": "DRAFT_EMPTY"})
        ep_empty["is_empty_draft"] = True
        ep_empty["readiness_state"] = "DRAFT_EMPTY"

    # Generate empty blueprint shell first
    episode_blueprint_service.generate_blueprint(episode_id=ep_empty["id"])

    # Generate pack
    pack = episode_production_pack_service.generate_production_pack(episode_id=ep_empty["id"])
    assert pack["readiness_state"] in [PackReadinessState.INCOMPLETE.value, PackReadinessState.INCOMPLETE]
    assert pack["readiness_state"] not in [PackReadinessState.READY_FOR_PRODUCTION.value, PackReadinessState.READY_FOR_PRODUCTION]
    assert len(pack["readiness_audit"]["missing_video_instructions"]) > 0


def test_production_integrity_check_10_lineage_traceability_and_hash_separation(isibusiso_pipeline_setup):
    """
    Production Integrity Check 10: Lineage Traceability & Hash Separation
    Verify complete chain: Production Pack → Blueprint → Episode → Series → Story Package → Forge Config.
    """
    ep_id = isibusiso_pipeline_setup["episode_id"]
    pack = episode_production_pack_service.generate_production_pack(episode_id=ep_id)

    # 1. Lineage Chain References
    assert pack["episode_id"] == ep_id
    assert pack["blueprint_id"] == isibusiso_pipeline_setup["blueprint_id"]
    assert pack["series_id"] == isibusiso_pipeline_setup["series_id"]
    assert pack["story_package_id"] == isibusiso_pipeline_setup["story_package_id"]
    assert pack["ip_id"] == isibusiso_pipeline_setup["ip_id"]
    assert pack["forge_configuration_id"] == "CFG-001"

    # 2. Hash Separation
    source_hash = pack["source_lineage_hash"]
    artifact_hash = pack["artifact_lineage_hash"]
    assert source_hash is not None
    assert artifact_hash is not None
    assert artifact_hash != source_hash
    assert len(artifact_hash) == 64  # SHA-256


def test_production_integrity_check_11_timing_conflict_detection():
    """
    Production Integrity Check 11: Timing Conflict Detection
    Incompatible track timings (e.g. dialogue starts after video window ends) must be flagged/rejected.
    """
    unit_bad_timing = ProductionUnit(
        unit_id="unit_ep1_01",
        sequence=1,
        episode_id="ep_test_01",
        blueprint_beat_ref="beat_ep1_01",
        story_purpose="Cold Open",
        location_ref="Clinic Room",
        character_refs=["Thandiwe Zulu"],
        estimated_duration_seconds=15,
        timing_start_seconds=0,
        timing_end_seconds=15,
        production_status="COORDINATED",
        video_track=VideoTrackSpecification(
            visual_action="Midwife delivers infant",
            environment="Clinic",
            timing_start_seconds=0,
            timing_end_seconds=15
        ),
        dialogue_track=DialogueTrackSpecification(
            speaker="Thandiwe Zulu",
            dialogue="Hold the candle steady.",
            timing_start_seconds=20,  # Invalid: Starts at 20s when video ends at 15s
            timing_end_seconds=25
        ),
        narration_track=NarrationTrackSpecification(),
        ambience_track=AmbienceTrackSpecification(),
        music_track=MusicTrackSpecification()
    )

    with pytest.raises(ValueError, match="Timing Conflict"):
        episode_production_pack_service.validate_timing_compatibility(unit_bad_timing)


def test_production_integrity_check_12_unsupported_detail_rejection():
    """
    Production Integrity Check 12: Unsupported Detail Rejection
    Injecting an unbacked production detail cannot be classified as CANON.
    """
    unsupported_prompt = VideoTrackSpecification(
        visual_action="Character enters in futuristic cyber-suit with laser katana.",
        environment="Neo-Tokyo Cyberpunk Alley",
        provenance=ProductionProvenance.DERIVED  # Sourced as DERIVED, cannot be CANON
    )

    with pytest.raises(ValueError, match="Provenance Escalation Error"):
        episode_production_pack_service.validate_provenance_escalation(
            source_provenance=unsupported_prompt.provenance.value,
            target_provenance="CANON"
        )


def test_isibusiso_specimen_manual_vs_machine_delta_report(isibusiso_pipeline_setup):
    """
    Specimen & Delta Observation: Compare Machine Production Pack with Manual Reference Pack.
    Uses only MATCH, MISSING, ADDITIONAL, CONFLICT, UNSUPPORTED classifications.
    """
    ep_id = isibusiso_pipeline_setup["episode_id"]
    machine_pack = episode_production_pack_service.generate_production_pack(episode_id=ep_id)

    manual_reference = {
        "specimen_title": "ISIBUSISO — PRODUCTION PROMPT PACK — Episode 1 Pilot Build",
        "production_units": [
            {"unit_id": f"unit_ep1_{i:02d}", "name": f"Unit {i}"} for i in range(1, 10)
        ]
    }

    delta_report = episode_production_pack_service.compare_specimen_with_manual_pack(
        machine_pack=machine_pack,
        manual_specimen=manual_reference
    )

    assert delta_report["summary"]["match_count"] >= 9
    assert "MATCH" in delta_report["categories"]
    assert "MISSING" in delta_report["categories"]
    assert "ADDITIONAL" in delta_report["categories"]
    assert "CONFLICT" in delta_report["categories"]
    assert "UNSUPPORTED" in delta_report["categories"]
    assert delta_report["summary"]["conflict_count"] == 0
