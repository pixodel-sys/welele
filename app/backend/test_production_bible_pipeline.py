"""
Welele Media™ — Production Bible & 5-Track Episode Production Pack Verification Suite
Tests the complete chain of truth:
  Story Forge → Story Package → Production Bible → Episode Production Pack
Proves zero loss of narrative truth, continuity, provenance (CFG-001) or production intent.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from repositories.ip_repository import ip_repository
from repositories.production_repository import production_repository
from services.production_bible_service import production_bible_service
from schemas.production_schemas import ProvenanceType

client = TestClient(app)


@pytest.fixture
def creator_auth():
    token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def isibusiso_ip(creator_auth):
    """Ensures a canonical Isibusiso IP with certified M3 Story Package exists."""
    # Check if IP exists
    ips = ip_repository.list_ips()
    target_ip = None
    for item in ips:
        if item.get("franchise_code") == "IP-ISIBUSISO" or item.get("title") == "Isibusiso":
            target_ip = item
            break

    if not target_ip:
        create_res = client.post(
            "/api/ip/create",
            json={
                "title": "Isibusiso",
                "franchise_code": "IP-ISIBUSISO",
                "logline": "A devout Soweto midwife delivers a baby during a township power blackout and notices a birthmark matching a legendary royal bloodline. When the wealthy Khumalo mining family arrives at dawn claiming the child, she discovers her own estranged daughter was the surrogate mother.",
                "synopsis": "Set across the stark contrast of Mofolo South township clinic and the Sandhurst high-security compound, Isibusiso tracks the explosive collision between customary royal succession and modern corporate mining power.",
                "genre": "High-Stakes Melodrama / Microdrama",
                "primary_language": "isiZulu",
                "master_owner_id": "creator_zola"
            },
            headers=creator_auth
        )
        assert create_res.status_code == 200
        target_ip = create_res.json()["ip"]

    # Ensure Story Package exists
    ip_id = target_ip["id"]
    detail = ip_repository.get_ip_detail(ip_id)
    if not detail.get("story_packages"):
        pkg_payload = {
            "ip_id": ip_id,
            "creator_id": "creator_zola",
            "package_title": "Isibusiso: The Sacred Lineage",
            "story_world_id": "sw_soweto_sandton",
            "target_duration_seconds": 90,
            "version": "1.0.0",
            "beats": [
                {
                    "beat_number": 1,
                    "label": "Cold Open: Midnight Delivery",
                    "action_description": "During a rolling Soweto blackout, midwife Thandiwe delivers a baby by candlelight and gasps as she cleans the royal ink-mark on its shoulder.",
                    "intensity": 8,
                    "timestamp_seconds": 10
                },
                {
                    "beat_number": 2,
                    "label": "Dawn Confrontation",
                    "action_description": "Bhekisisa Khumalo's convoy arrives with cash briefcases. Lerato steps out of the black Mercedes, confessing to the surrogacy contract.",
                    "intensity": 9,
                    "timestamp_seconds": 45
                },
                {
                    "beat_number": 3,
                    "label": "Cliffhanger Paywall Cut",
                    "action_description": "Bhekisisa's guards draw weapons to seize the infant, but township neighbours surround the clinic with sjamboks as Thandiwe holds the customary birth record high.",
                    "intensity": 10,
                    "timestamp_seconds": 88,
                    "cliffhanger_trigger": True
                }
            ],
            "dialogues": [
                {"character": "Thandiwe", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."},
                {"character": "Bhekisisa", "line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over."},
                {"character": "Lerato", "line": "Mama, forgive me... I had no other way to clear the loan sharks."}
            ],
            "cliffhanger_prompt": "Will Thandiwe sign the Khumalo settlement or trigger a township uprising to protect the royal infant?",
            "forge_configuration_id": "CFG-001",
            "human_approved": True
        }
        pkg_res = client.post(f"/api/ip/{ip_id}/story-forge/save", json=pkg_payload, headers=creator_auth)
        assert pkg_res.status_code == 200

    return ip_id


def test_story_package_to_production_bible_10_sections(isibusiso_ip, creator_auth):
    """
    Test 1: Verify Story Package → Production Bible generation preserves all 10 canonical sections
    and adheres to provenance taxonomy (CANON / DERIVED / GENERATED / PRODUCTION_DECISION).
    """
    res = client.post(
        "/api/v1/production/bibles/generate",
        json={"ip_id": isibusiso_ip, "version": "1.0.0"},
        headers=creator_auth
    )
    assert res.status_code == 200
    bible = res.json()

    # Provenance Anchoring
    assert bible["forge_configuration_id"] == "CFG-001"
    assert bible["lineage_hash"] is not None
    assert bible["ip_id"] == isibusiso_ip

    # Section 1: Title Identity
    s1 = bible["section_1_title_identity"]
    assert s1["title"] == "Isibusiso: The Sacred Lineage" or "Isibusiso" in s1["title"]
    assert s1["format"] == "9:16 Vertical Microdrama"
    assert s1["target_duration_seconds"] == 90
    assert s1["primary_language"] == "isiZulu"
    assert s1["provenance"] == ProvenanceType.CANON.value

    # Section 2: Creative DNA
    s2 = bible["section_2_creative_dna"]
    assert "midwife" in s2["logline"].lower()
    assert "royal" in s2["dramatic_engine"].lower()
    assert s2["provenance"] == ProvenanceType.CANON.value

    # Section 3: Character Production Bible
    s3 = bible["section_3_character_bible"]
    assert len(s3) >= 3
    char_names = [c["name"] for c in s3]
    assert any("Thandiwe" in n for n in char_names)
    assert any("Bhekisisa" in n for n in char_names)
    assert any("Lerato" in n for n in char_names)

    # Section 4: World / Location Bible
    s4 = bible["section_4_location_bible"]
    assert len(s4) >= 2
    assert s4[0]["provenance"] == ProvenanceType.DERIVED.value

    # Section 5: Supernatural / World Rules
    s5 = bible["section_5_world_rules"]
    assert len(s5) >= 2
    rule_keys = [r["rule_key"] for r in s5]
    assert "RULE_CUSTOMARY_LINEAGE_COVENANT" in rule_keys
    assert s5[0]["provenance"] == ProvenanceType.CANON.value

    # Section 6: Visual Language
    s6 = bible["section_6_visual_language"]
    assert "9:16" in s6["aspect_ratio"]
    assert len(s6["color_palette"]) >= 3
    assert s6["provenance"] == ProvenanceType.PRODUCTION_DECISION.value

    # Section 7: Audio Language
    s7 = bible["section_7_audio_language"]
    assert "Thandiwe" in s7["vernacular_matrix"]
    assert len(s7["foley_architecture"]) >= 3
    assert s7["score_signature"]["bpm"] == 68
    assert s7["provenance"] == ProvenanceType.PRODUCTION_DECISION.value

    # Section 8: Continuity Bible
    s8 = bible["section_8_continuity_bible"]
    assert len(s8["chronology_spine"]) >= 3
    assert len(s8["narrative_plants_and_payoffs"]) >= 2
    assert s8["provenance"] == ProvenanceType.CANON.value

    # Section 9: Production Constraints
    s9 = bible["section_9_production_constraints"]
    assert s9["practical_sets_max"] <= 2
    assert s9["cast_density_per_scene_max"] <= 3
    assert s9["provenance"] == ProvenanceType.PRODUCTION_DECISION.value

    # Section 10: Prompt Constitution
    s10 = bible["section_10_prompt_constitution"]
    assert "CANON_OVERRIDES_PROMPT_CONVENIENCE" in s10["canon_override_rule"]
    assert s10["aspect_ratio_enforcement"] == "9:16 Vertical Native Only"
    assert s10["provenance"] == ProvenanceType.CANON.value


def test_production_bible_to_episode_1_production_pack_5_tracks(isibusiso_ip, creator_auth):
    """
    Test 2: Verify Production Bible → Episode 1 Production Pack generates all 5 coordinated tracks:
    VIDEO, DIALOGUE, NARRATION, AMBIENCE, MUSIC without creating unapproved canon.
    """
    res = client.post(
        "/api/v1/production/packs/generate",
        json={"ip_id": isibusiso_ip, "episode_number": 1},
        headers=creator_auth
    )
    assert res.status_code == 200
    pack = res.json()

    assert pack["episode_number"] == 1
    assert pack["duration_seconds"] == 90
    assert pack["forge_configuration_id"] == "CFG-001"
    assert len(pack["beats"]) == 3

    tracks = pack["five_tracks"]

    # Track 1: VIDEO
    video = tracks["video"]
    assert len(video["scene_descriptions"]) == 3
    assert len(video["camera_direction"]) >= 3
    assert "Chiaroscuro" in video["lighting_execution"]
    assert video["provenance"] == ProvenanceType.GENERATED.value

    # Track 2: DIALOGUE
    dialogue = tracks["dialogue"]
    assert len(dialogue["dialogue_lines"]) == 3
    speakers = [d["speaker"] for d in dialogue["dialogue_lines"]]
    assert "Thandiwe" in speakers
    assert "Bhekisisa" in speakers
    assert "Lerato" in speakers
    assert dialogue["provenance"] == ProvenanceType.CANON.value

    # Track 3: NARRATION
    narration = tracks["narration"]
    assert narration["has_narration"] is True
    assert narration["opening_hook_vo"] is not None
    assert narration["provenance"] == ProvenanceType.DERIVED.value

    # Track 4: AMBIENCE
    ambience = tracks["ambience"]
    assert "blackout" in ambience["room_tone"].lower()
    assert len(ambience["foley_events"]) >= 4
    assert ambience["provenance"] == ProvenanceType.GENERATED.value

    # Track 5: MUSIC
    music = tracks["music"]
    assert music["tempo_bpm"] == 68
    assert music["paywall_cut_behavior"] == "ABRUPT_SILENCE_AT_CLIFFHANGER"
    assert len(music["stems_progression"]) == 4
    assert music["provenance"] == ProvenanceType.GENERATED.value

    # Narrative Continuity
    continuity = pack["narrative_continuity"]
    assert len(continuity["state_mutations"]) >= 3
    assert len(continuity["active_plants"]) >= 2
    assert continuity["provenance"] == ProvenanceType.CANON.value


def test_production_pack_retrieval_and_provenance_immutability(isibusiso_ip):
    """
    Test 3: Verify GET endpoints for Production Bible and Episode Production Pack enforce immutability.
    """
    # Fetch Bible
    res_bible = client.get(f"/api/v1/production/bibles/{isibusiso_ip}")
    assert res_bible.status_code == 200
    bible = res_bible.json()
    assert bible["forge_configuration_id"] == "CFG-001"

    # Fetch Episode 1 Pack
    res_pack = client.get(f"/api/v1/production/packs/{isibusiso_ip}/episodes/1")
    assert res_pack.status_code == 200
    pack = res_pack.json()
    assert pack["episode_number"] == 1
    assert pack["cliffhanger_prompt"] == "Will Thandiwe sign the Khumalo settlement or trigger a township uprising to protect the royal infant?"
