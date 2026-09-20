"""
Welele Media™ — Provenance Honesty / "Boring Truth" Test Suite v1.0
Proves that the transformation pipeline (Story Package -> Production Bible -> Episode Production Pack)
does NOT invent, promote, or silently canonise information absent from the authoritative Story Package.

Acceptance Criteria:
  A. No unsupported CANON exists downstream.
  B. No GENERATED or DERIVED element is silently promoted to CANON.
  C. Missing information remains visibly missing (UNKNOWN / NOT_SPECIFIED / DEFERRED).
  D. Downstream generation cannot mutate Story Package truth.
  E. Every production detail has traceable provenance.
  F. The system can distinguish "not known" from "not yet decided."
  G. Existing Story Forge v1.0 tests remain unchanged and passing.
"""

import pytest
import uuid
import copy
from typing import Dict, Any
from repositories.ip_repository import ip_repository
from repositories.production_repository import production_repository
from services.production_bible_service import production_bible_service
from schemas.production_schemas import (
    ProvenanceType,
    GovernedState,
    CanonMutationError,
    ProvenanceEscalationError,
    validate_downstream_mutation,
    validate_provenance_escalation,
    verify_traceability
)


@pytest.fixture
def sparse_ip_fixture() -> str:
    """Creates a deliberately minimal but valid Story Package."""
    ip_id = f"ip_sparse_{uuid.uuid4().hex[:6]}"
    sparse_package = {
        "id": f"sfp_sparse_{uuid.uuid4().hex[:6]}",
        "ip_id": ip_id,
        "package_title": "The Silent Vault",
        "logline": "A retired lock-picker discovers a forgotten safe with no keyhole.",
        "genre": "Minimal Mystery",
        "primary_language": "Sesotho",
        "target_duration_seconds": 90,
        "characters": [
            {
                "name": "Dumisani",
                "role": "Protagonist",
                "core_motivation": "Open the safe before midnight.",
                "fatal_flaw": "Curiosity over safety.",
                "signature_quote": "Every lock has a pulse."
            }
        ],
        # Notice what is deliberately absent:
        # - NO costume details
        # - NO physical appearance beyond explicitly supplied attributes
        # - NO lens choices
        # - NO lighting temperatures
        # - NO music tempo
        # - NO sound effects
        # - NO set dimensions
        # - NO camera movements
        # - NO dialect specifics
        # - NO additional characters
        # - NO props
        # - NO dialogue beyond signature quote
        # - NO invented locations
        # - NO invented lore
        # - NO invented chronology
        "inviolable_rules": [
            "The safe cannot be breached by explosive force."
        ],
        "forge_configuration_id": "CFG-001",
        "lineage_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }

    ip_record = {
        "id": ip_id,
        "title": "The Silent Vault",
        "franchise_code": "IP-VAULT",
        "logline": "A retired lock-picker discovers a forgotten safe with no keyhole.",
        "genre": "Minimal Mystery",
        "primary_language": "Sesotho",
        "target_duration_seconds": 90
    }

    # Save to repositories
    ip_repository.local_insert("digital_ips", ip_record)
    ip_repository.local_insert("story_forge_packages", sparse_package)
    for c in sparse_package["characters"]:
        ip_repository.local_insert("character_bibles", {
            "id": f"char_{uuid.uuid4().hex[:6]}",
            "ip_id": ip_id,
            "name": c["name"],
            "role": c["role"],
            "core_motivation": c["core_motivation"],
            "fatal_flaw": c["fatal_flaw"],
            "signature_quote": c["signature_quote"]
        })

    return ip_id


# =============================================================================
# TEST 1: Sparse Story Package (Boring Truth Verification)
# =============================================================================

def test_sparse_story_package_preserves_unknown_and_deferred(sparse_ip_fixture: str):
    """
    Verifies that when given a sparse Story Package, missing details are explicitly
    represented as UNKNOWN, NOT_SPECIFIED, or DEFERRED, and NOT fabricated as CANON.
    """
    ip_id = sparse_ip_fixture
    bible = production_bible_service.generate_production_bible(ip_id)
    pack = production_bible_service.generate_episode_production_pack(ip_id, production_bible_id=bible["id"])

    # 1. Verify Character Bible (Section 3)
    char_entry = bible["section_3_character_bible"][0]
    assert char_entry["name"] == "Dumisani"
    assert char_entry["role"] == "PROTAGONIST"
    assert char_entry["core_motivation"] == "Open the safe before midnight."
    assert char_entry["canon_provenance"] == ProvenanceType.CANON

    # Missing physical/costume details must be DEFERRED, not invented
    assert char_entry["visual_key"] == "DEFERRED"
    assert char_entry["wardrobe_palette"] == "DEFERRED"
    assert char_entry["costume_distress_rules"] == "DEFERRED"
    assert char_entry["casting_spec"] == "DEFERRED"
    assert char_entry["dialect_guidance"] == "DEFERRED"

    # 2. Verify Location Bible (Section 4)
    loc_entry = bible["section_4_location_bible"][0]
    assert loc_entry["location_name"] == "NOT_SPECIFIED"
    assert loc_entry["spatial_layout"] == "NOT_SPECIFIED"
    assert loc_entry["lighting_conditions"] == "NOT_SPECIFIED"
    assert loc_entry["soundstage_vs_practical_criteria"] == "DEFERRED"

    # 3. Verify Visual & Audio Language (Sections 6 & 7)
    assert bible["section_6_visual_language"]["lighting_grammar"] == "DEFERRED_TO_GAFFER" or bible["section_6_visual_language"]["lighting_grammar"] == "DEFERRED"
    assert bible["section_6_visual_language"]["camera_and_lens_package"] == []

    assert bible["section_7_audio_language"]["score_signature"]["bpm"] == "DEFERRED"
    assert bible["section_7_audio_language"]["foley_architecture"] == []

    # 4. Verify Episode Production Pack Tracks
    track_music = pack["five_tracks"]["music"]
    assert track_music["tempo_bpm"] is None or track_music["tempo_bpm"] == 0
    assert track_music["score_theme"] == "NOT_SPECIFIED"
    assert track_music["instrumentation"] == []

    track_ambience = pack["five_tracks"]["ambience"]
    assert track_ambience["room_tone"] == "NOT_SPECIFIED"
    assert track_ambience["foley_events"] == []


# =============================================================================
# TEST 2: Canon Mutation Attempt (Reject Downstream Tampering)
# =============================================================================

def test_canon_mutation_attempt_rejection(sparse_ip_fixture: str):
    """
    Verifies that deliberate downstream generation attempting to alter character motivation,
    world rules, logline, or protagonist identity is rejected with CANON_MUTATION_REJECTED.
    """
    ip_detail = ip_repository.get_ip_detail(sparse_ip_fixture)
    upstream_pkg = ip_detail["story_packages"][0]
    original_snapshot = copy.deepcopy(upstream_pkg)

    # Downstream mutation attempt: Change Dumisani's motivation
    mutated_payload = {
        "logline": "A retired lock-picker discovers a forgotten safe with no keyhole.",
        "core_motivation": "Steal gold for personal wealth.",  # Tampered
        "characters": [
            {
                "name": "Dumisani",
                "role": "Protagonist",
                "core_motivation": "Steal gold for personal wealth."  # Mutated motivation!
            }
        ]
    }

    # Validator must reject the mutation
    with pytest.raises(CanonMutationError) as exc_info:
        validate_downstream_mutation(upstream_pkg, mutated_payload)

    assert "CANON_MUTATION_REJECTED" in str(exc_info.value)

    # Verify Story Package remains byte-for-byte identical
    current_upstream = ip_repository.get_ip_detail(sparse_ip_fixture)["story_packages"][0]
    assert current_upstream == original_snapshot


# =============================================================================
# TEST 3: Provenance Escalation (Authority Cannot Flow Upstream)
# =============================================================================

def test_provenance_escalation_rejection():
    """
    Verifies that attempting to transform GENERATED -> CANON or DERIVED -> CANON
    without authoritative upstream source is strictly rejected.
    """
    # Valid: CANON from CANON
    validate_provenance_escalation(ProvenanceType.CANON, ProvenanceType.CANON)

    # Valid: GENERATED from CANON
    validate_provenance_escalation(ProvenanceType.GENERATED, ProvenanceType.CANON)

    # Invalid: Attempting to escalate GENERATED to CANON
    with pytest.raises(ProvenanceEscalationError) as exc_info1:
        validate_provenance_escalation(ProvenanceType.CANON, ProvenanceType.GENERATED)
    assert "PROVENANCE_ESCALATION_REJECTED" in str(exc_info1.value)

    # Invalid: Attempting to escalate DERIVED to CANON
    with pytest.raises(ProvenanceEscalationError) as exc_info2:
        validate_provenance_escalation(ProvenanceType.CANON, ProvenanceType.DERIVED)
    assert "PROVENANCE_ESCALATION_REJECTED" in str(exc_info2.value)


# =============================================================================
# TEST 4: Traceability (Every Atomic Node Answers Provenance Questions)
# =============================================================================

def test_traceability_and_source_path_integrity(sparse_ip_fixture: str):
    """
    Verifies that every non-empty atomic field in Production Bible and Episode Production Pack
    has valid source_path, provenance, derivation_notes, and lineage hash.
    """
    ip_id = sparse_ip_fixture
    bible = production_bible_service.generate_production_bible(ip_id)
    pack = production_bible_service.generate_episode_production_pack(ip_id, production_bible_id=bible["id"])

    bible_trace = verify_traceability(bible)
    assert bible_trace["is_traceable"] is True, f"Bible traceability violations: {bible_trace['violations']}"

    pack_trace = verify_traceability(pack)
    assert pack_trace["is_traceable"] is True, f"Pack traceability violations: {pack_trace['violations']}"

    # Lineage confirmation
    assert bible["forge_configuration_id"] == "CFG-001"
    assert pack["forge_configuration_id"] == "CFG-001"
    assert len(bible["lineage_hash"]) == 64
    assert len(pack["lineage_hash"]) == 64


# =============================================================================
# TEST 5: Production Integrity Check — Sparse Input Honesty (No Confident Hallucinations)
# =============================================================================

def test_production_integrity_sparse_no_confident_hallucinations(sparse_ip_fixture: str):
    """
    Checks specifically for confident-looking invented details in an incomplete Story Package.
    None of these hallmark specifics from Isibusiso or generic prompts should leak:
      - 68 BPM
      - 5600K / 2700K
      - charcoal suit
      - G-Wagon / Mercedes
      - 9mm / handgun
      - loan shark / Bra Mike
      - 15m²
      - Sandton isiZulu
      - 24mm / 35mm / 50mm lenses
    """
    ip_id = sparse_ip_fixture
    bible = production_bible_service.generate_production_bible(ip_id)
    pack = production_bible_service.generate_episode_production_pack(ip_id, production_bible_id=bible["id"])

    bible_str = str(bible).lower()
    pack_str = str(pack).lower()
    combined = f"{bible_str} {pack_str}"

    forbidden_hallucinations = [
        "68 bpm",
        "5600k",
        "2700k",
        "charcoal suit",
        "g-wagon",
        "mercedes",
        "9mm",
        "handgun",
        "loan shark",
        "bra mike",
        "15m²",
        "sandton isizulu",
        "24mm",
        "35mm",
        "50mm"
    ]

    leaked = []
    for term in forbidden_hallucinations:
        if term in combined:
            leaked.append(term)

    assert len(leaked) == 0, f"Production Integrity Check Failed! Detected ungrounded confident hallucinations: {leaked}"
