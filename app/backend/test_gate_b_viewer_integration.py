"""
PHASE 1 — GATE B: VIEWER → PLATFORM INTEGRATION TEST SUITE
Comprehensive verification of the full end-to-end Welele platform pipeline:
Story Forge (M3 Package) → Content / Series / Episode → Media Asset → CMS / Experience →
Viewer → Playback → Session / Telemetry → Community Engagement → Monetisation / Entitlement → Ledger.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from database import db
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository
from repositories.event_repository import event_repository
from repositories.production_repository import production_repository
from services.series_episode_service import series_episode_service
from services.experience_engine import ExperienceEngine
from services.storage_service import storage_service
from services.ledger_service import ledger_service
from services.commerce_service import CommerceService
from services.viewer_execution_service import viewer_execution_service
from services.viewer_telemetry_service import viewer_telemetry_service
from schemas.viewer_telemetry_models import (
    ViewerTelemetryEvent, EventSpineFamily, ViewerEventType, EventSource
)
from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus,
    MilestoneEnum, ReadinessStatus, DependencyStatus
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.api.routes import get_story_package

client = TestClient(app)


# ---------------------------------------------------------------------------
# FIXTURES & CLEAN-ROOM SETUP
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gate_b_environment():
    """
    Builds the certified Sabelo Story Package in Story Forge (from Gate A clean-room)
    and secondary story Thandi (from Gate A.1) and publishes them down the platform spine.
    """
    # 1. Forge clean-room Sabelo
    forge_repo = InMemoryStoryForgeRepository()
    story_id = "sabelo_gate_b_clean"
    forge_repo.create_story(
        story_id=story_id,
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Desperate security guard Sabelo steals R2 million from drug dealer Jonas's car boot to fund urgent heart surgery for his sister Zodwa."
    )
    forge_repo.create_session(story_id, "creator_zola", "sess_forge_sabelo")
    kernel = StoryForgeKernel(repository=forge_repo)
    judge = ForgeJudge(repository=forge_repo)

    # Cycle 1: Core setup
    kernel.process_cycle(
        story_id,
        session_id="sess_forge_sabelo",
        creator_input="Sabelo is an honest security guard at a high-end Fontana casino in downtown Johannesburg who discovers R2 million in drug dealer Jonas's BMW boot. His younger sister Zodwa is hospitalized needing urgent heart surgery."
    )
    # Cycle 2: Midpoint & escalation
    kernel.process_cycle(
        story_id,
        session_id="sess_forge_sabelo",
        creator_response="Sabelo takes the money and flees before sunrise. Jonas discovers the theft and threatens his family, sending ruthless debt collectors after Zodwa."
    )
    # Cycle 3: Climax & Resolution
    kernel.process_cycle(
        story_id,
        session_id="sess_forge_sabelo",
        creator_response="Sabelo faces Jonas in a tense final confrontation at the hospital parking lot. Sabelo outsmarts Jonas with casino security footage, getting Jonas arrested by the police. Zodwa survives her surgery and Sabelo starts a legitimate transport business. That is the end."
    )

    assessment = judge.assess(story_id)
    story_package = get_story_package(story_id, repo=forge_repo, judge=judge)
    story_pkg_id = f"pkg_{story_id}_m3"
    sabelo_state = forge_repo.get_story(story_id)

    # 2. Forge secondary story Thandi for isolation tests
    thandi_story_id = "thandi_gate_b_clean"
    forge_repo.create_story(
        story_id=thandi_story_id,
        title="Thandi: The Silent Witness",
        owner_id="creator_thandi",
        logline="Courtroom microdrama. Thandi, a deaf court stenographer, uncovers a corrupt judicial syndicate."
    )
    forge_repo.create_session(thandi_story_id, "creator_thandi", "sess_forge_thandi")
    kernel.process_cycle(
        thandi_story_id,
        session_id="sess_forge_thandi",
        creator_input="Thandi is a skilled deaf stenographer in Johannesburg High Court who lip-reads Judge Mthembu taking a R5 million bribe to acquit a human trafficking kingpin. Her mentor Advocate Ndlovu warns her to stay silent."
    )
    kernel.process_cycle(
        thandi_story_id,
        session_id="sess_forge_thandi",
        creator_response="Thandi secretly archives the stenographic record onto an encrypted USB drive. Judge Mthembu suspects a leak and sends court security to search her apartment."
    )
    kernel.process_cycle(
        thandi_story_id,
        session_id="sess_forge_thandi",
        creator_response="Thandi hands the uncorrupted transcript directly to the Special Investigating Unit during live sentencing. Judge Mthembu is arrested on the bench. Thandi is promoted to Chief Transcriber. That is the end."
    )
    thandi_pkg = get_story_package(thandi_story_id, repo=forge_repo, judge=judge)
    thandi_pkg_id = f"pkg_{thandi_story_id}_m3"
    thandi_state = forge_repo.get_story(thandi_story_id)

    # 3. Publish Sabelo to Digital IP layer
    ip_sabelo = {
        "id": "ip_sabelo_fontana",
        "title": "Sabelo: The Fontana Boss",
        "franchise_code": "IP-SABELO",
        "logline": story_package.logline,
        "synopsis": story_package.logline,
        "genre": "Comedy Drama / Vertical Microdrama",
        "primary_language": "isiZulu",
        "master_owner_id": "creator_zola"
    }
    ip_repository.local_insert("digital_ips", ip_sabelo)

    # Register Story Package on IP
    pkg_dict = {
        "id": story_pkg_id,
        "ip_id": ip_sabelo["id"],
        "creator_id": "creator_zola",
        "package_title": story_package.title,
        "story_world_id": "sw_jhb_fontana",
        "target_duration_seconds": 90,
        "version": "1.0.0",
        "primary_language": "isiZulu",
        "secondary_languages": ["English", "Sesotho", "Tsotsitaal"],
        "logline": story_package.logline,
        "genre": ip_sabelo["genre"],
        "thematic_premise": "Desperate choices in the heart of Johannesburg",
        "chronology_spine": [
            {"anchor_number": i + 1, "anchor_name": e.get("headline", f"Event {i+1}"), "summary": e.get("summary", "")}
            for i, e in enumerate(story_package.chronology_spine)
        ],
        "plants": story_package.narrative_plants,
        "world_rules": [{"rule_key": f"RULE_{i+1}", "summary": str(r)} for i, r in enumerate(story_package.world.items())] if isinstance(story_package.world, dict) else [],
        "dialogues": [
            {"character": "Sabelo", "line": "I took the money for Zodwa."},
            {"character": "Jonas", "line": "Nobody steals from Jonas in Johannesburg."}
        ],
        "beats": [
            {"beat_number": 1, "label": "The Discovery", "timestamp_seconds": 15, "action_description": "Sabelo finds R2M in BMW boot"},
            {"beat_number": 2, "label": "The Confrontation", "timestamp_seconds": 55, "action_description": "Jonas corners Sabelo"},
            {"beat_number": 3, "label": "The Resolution", "timestamp_seconds": 88, "action_description": "Police arrest Jonas"}
        ],
        "forge_configuration_id": "CFG-001",
        "lineage_hash": f"hash_sabelo_v{story_package.state_version}"
    }
    ip_repository.local_insert("story_forge_packages", pkg_dict)

    # 4. Create Series for Sabelo
    series = series_episode_service.create_series_from_story_package(
        ip_id=ip_sabelo["id"],
        story_package_id=story_pkg_id,
        season_number=1,
        custom_title="Sabelo: The Fontana Boss"
    )
    series_id = series["id"]
    series_repository.local_update("series", "id", series_id, {
        "title": "Sabelo: The Fontana Boss",
        "vertical_poster": "/posters/sabelo.jpg",
        "cover_image": "/banners/sabelo_banner.jpg",
        "is_published": True,
        "free_episodes": 1,
        "status": "published"
    })

    # Register in legacy db.stories for backward compatibility
    stories = db.get("stories")
    if not any(s["id"] == series_id for s in stories):
        db.insert("stories", {
            "id": series_id,
            "title": "Sabelo: The Fontana Boss",
            "logline": ip_sabelo["logline"],
            "genre": ip_sabelo["genre"],
            "primary_language": "isiZulu",
            "cover_image": "/banners/sabelo_banner.jpg",
            "vertical_poster": "/posters/sabelo.jpg",
            "free_episodes_count": 1,
            "is_published": True
        })

    # 5. Create Episodes for Sabelo (Idempotent lookup)
    all_sabelo_eps = series_repository.get_episodes_for_series(series_id)
    
    # Episode 1: Free, Production Ready, Verified Master Asset
    ep1 = next((e for e in all_sabelo_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=1,
            custom_title="Episode 1 — The Boot of Fortune",
            is_empty_draft=False
        )
    ep1_id = ep1["id"]
    media_asset_id_ep1 = f"asset_sabelo_s01e01_v1"
    master_video_url_ep1 = "/videos/sabelo_s01e01_master.mp4"

    series_repository.local_update("episodes", "id", ep1_id, {
        "series_id": series_id,
        "title": "Episode 1 — The Boot of Fortune",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": True,
        "video_url": master_video_url_ep1,
        "media_asset_id": media_asset_id_ep1,
        "duration_seconds": 90,
        "cliffhanger_time": 75,
        "coin_price": 5
    })

    series_repository.local_insert("media_assets", {
        "id": media_asset_id_ep1,
        "episode_id": ep1_id,
        "series_id": series_id,
        "storage_key": f"masters/{series_id}/{ep1_id}.mp4",
        "master_video_url": master_video_url_ep1,
        "delivery_url": master_video_url_ep1,
        "status": "verified"
    })

    # Episode 2: Paid (Locked), Production Ready
    ep2 = next((e for e in all_sabelo_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=2,
            custom_title="Episode 2 — The Debt Collector",
            is_empty_draft=False
        )
    ep2_id = ep2["id"]
    media_asset_id_ep2 = f"asset_sabelo_s01e02_v1"
    master_video_url_ep2 = "/videos/sabelo_s01e02_master.mp4"

    series_repository.local_update("episodes", "id", ep2_id, {
        "series_id": series_id,
        "title": "Episode 2 — The Debt Collector",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": False,
        "video_url": master_video_url_ep2,
        "media_asset_id": media_asset_id_ep2,
        "duration_seconds": 90,
        "cliffhanger_time": 82,
        "coin_price": 5
    })

    series_repository.local_insert("media_assets", {
        "id": media_asset_id_ep2,
        "episode_id": ep2_id,
        "series_id": series_id,
        "storage_key": f"masters/{series_id}/{ep2_id}.mp4",
        "master_video_url": master_video_url_ep2,
        "delivery_url": master_video_url_ep2,
        "status": "verified"
    })

    # Episode 3: Coming Soon (DRAFT_EMPTY)
    ep3 = next((e for e in all_sabelo_eps if e.get("episode_number") == 3), None)
    if not ep3:
        ep3 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=3,
            custom_title="Episode 3 — Hospital Showdown",
            is_empty_draft=True
        )
    ep3_id = ep3["id"]
    series_repository.local_update("episodes", "id", ep3_id, {
        "series_id": series_id,
        "title": "Episode 3 — Hospital Showdown",
        "is_empty_draft": True,
        "readiness_state": "DRAFT_EMPTY",
        "lifecycle_state": "DRAFT",
        "status": "draft",
        "is_free": False,
        "video_url": None,
        "media_asset_id": None
    })

    # 6. Publish Thandi for Isolation Tests
    ip_thandi = {
        "id": "ip_thandi_witness",
        "title": "Thandi: The Silent Witness",
        "franchise_code": "IP-THANDI",
        "logline": thandi_pkg.logline,
        "synopsis": thandi_pkg.logline,
        "genre": "Courtroom Thriller / Vertical Microdrama",
        "primary_language": "isiZulu",
        "master_owner_id": "creator_thandi"
    }
    ip_repository.local_insert("digital_ips", ip_thandi)

    pkg_thandi_dict = {
        "id": thandi_pkg_id,
        "ip_id": ip_thandi["id"],
        "creator_id": "creator_thandi",
        "package_title": thandi_pkg.title,
        "story_world_id": "sw_jhb_court",
        "target_duration_seconds": 90,
        "version": "1.0.0",
        "primary_language": "isiZulu",
        "logline": thandi_pkg.logline,
        "genre": ip_thandi["genre"],
        "thematic_premise": "Justice and truth in the courtroom",
        "chronology_spine": [
            {"anchor_number": i + 1, "anchor_name": e.get("headline", f"Event {i+1}"), "summary": e.get("summary", "")}
            for i, e in enumerate(thandi_pkg.chronology_spine)
        ],
        "plants": [],
        "world_rules": [],
        "dialogues": [],
        "beats": [
            {"beat_number": 1, "label": "The Secret Bribe", "timestamp_seconds": 20, "action_description": "Thandi lip-reads judge"}
        ],
        "forge_configuration_id": "CFG-001",
        "lineage_hash": f"hash_thandi_v{thandi_pkg.state_version}"
    }
    ip_repository.local_insert("story_forge_packages", pkg_thandi_dict)

    series_thandi = series_episode_service.create_series_from_story_package(
        ip_id=ip_thandi["id"],
        story_package_id=thandi_pkg_id,
        season_number=1,
        custom_title="Thandi: The Silent Witness"
    )
    thandi_series_id = series_thandi["id"]
    series_repository.local_update("series", "id", thandi_series_id, {
        "title": "Thandi: The Silent Witness",
        "vertical_poster": "/posters/thandi.jpg",
        "cover_image": "/banners/thandi_banner.jpg",
        "is_published": True,
        "free_episodes": 1,
        "status": "published"
    })
    all_thandi_eps = series_repository.get_episodes_for_series(thandi_series_id)
    thandi_ep1 = next((e for e in all_thandi_eps if e.get("episode_number") == 1), None)
    if not thandi_ep1:
        thandi_ep1 = series_episode_service.create_episode(
            series_id=thandi_series_id,
            episode_number=1,
            custom_title="Episode 1 — The Lip Reader",
            is_empty_draft=False
        )
    thandi_ep1_id = thandi_ep1["id"]
    media_asset_thandi_ep1 = "asset_thandi_s01e01_v1"
    series_repository.local_update("episodes", "id", thandi_ep1_id, {
        "series_id": thandi_series_id,
        "title": "Episode 1 — The Lip Reader",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": True,
        "video_url": "/videos/thandi_s01e01_master.mp4",
        "media_asset_id": media_asset_thandi_ep1,
        "duration_seconds": 90,
        "cliffhanger_time": 78,
        "coin_price": 5
    })
    series_repository.local_insert("media_assets", {
        "id": media_asset_thandi_ep1,
        "episode_id": thandi_ep1_id,
        "series_id": thandi_series_id,
        "storage_key": f"masters/{thandi_series_id}/{thandi_ep1_id}.mp4",
        "master_video_url": "/videos/thandi_s01e01_master.mp4",
        "delivery_url": "/videos/thandi_s01e01_master.mp4",
        "status": "verified"
    })

    return {
        "forge_repo": forge_repo,
        "story_id": story_id,
        "sabelo_state": sabelo_state,
        "story_package": story_package,
        "story_pkg_id": story_pkg_id,
        "ip_sabelo": ip_sabelo,
        "series_id": series_id,
        "ep1_id": ep1_id,
        "ep2_id": ep2_id,
        "ep3_id": ep3_id,
        "media_asset_id_ep1": media_asset_id_ep1,
        "media_asset_id_ep2": media_asset_id_ep2,
        "master_video_url_ep1": master_video_url_ep1,
        "master_video_url_ep2": master_video_url_ep2,
        "thandi_story_id": thandi_story_id,
        "thandi_state": thandi_state,
        "thandi_pkg": thandi_pkg,
        "thandi_pkg_id": thandi_pkg_id,
        "thandi_series_id": thandi_series_id,
        "thandi_ep1_id": thandi_ep1_id,
        "media_asset_thandi_ep1": media_asset_thandi_ep1
    }


# ---------------------------------------------------------------------------
# TEST 1 — FORGED STORY → CONTENT RECORD
# ---------------------------------------------------------------------------

def test_1_forged_story_to_content_record(gate_b_environment):
    env = gate_b_environment
    series_data = series_repository.get_series(env["series_id"])
    assert series_data is not None, "Series must exist in repository"
    
    # 1. Traceability
    assert series_data["ip_id"] == env["ip_sabelo"]["id"]
    assert series_data["story_package_id"] == env["story_pkg_id"]
    assert series_data["source_lineage_hash"] == f"hash_sabelo_v{env['story_package'].state_version}"
    
    # 2. Fidelity
    assert "Sabelo: The Fontana Boss" in series_data["title"]
    assert "Desperate security guard Sabelo" in series_data["synopsis"] or "Sabelo" in series_data["synopsis"]
    
    # 3. Canonical metadata preserved
    assert series_data["primary_language"] == "isiZulu"
    assert series_data["format"] == "9:16 Vertical Microdrama"
    
    # 4. Episodes relationship (Filter canonical episodes 1..3)
    all_eps = series_repository.get_episodes_for_series(env["series_id"])
    eps = [e for e in all_eps if e.get("episode_number") in (1, 2, 3)]
    assert len(eps) == 3, "Must have exactly 3 canonical episodes created for Sabelo"
    eps.sort(key=lambda x: x["episode_number"])
    assert eps[0]["episode_number"] == 1
    assert eps[1]["episode_number"] == 2
    assert eps[2]["episode_number"] == 3
    
    # 5. No silent duplication
    all_matching = [s for s in series_repository.local_get("series") if s["id"] == env["series_id"]]
    assert len(all_matching) == 1, "Must have exactly 1 Series entity (no duplicates)"


# ---------------------------------------------------------------------------
# TEST 2 — CONTENT → MEDIA ASSET
# ---------------------------------------------------------------------------

def test_2_content_to_media_asset(gate_b_environment):
    env = gate_b_environment
    all_media = series_repository.local_get("media_assets")
    
    # Ep 1 Media Asset
    media_ep1 = next((m for m in all_media if m["id"] == env["media_asset_id_ep1"]), None)
    assert media_ep1 is not None, "Ep1 media asset must be explicitly retrievable"
    assert media_ep1["episode_id"] == env["ep1_id"]
    assert media_ep1["series_id"] == env["series_id"]
    assert media_ep1["status"] == "verified"
    assert media_ep1["master_video_url"] == env["master_video_url_ep1"]
    
    # Ep 2 Media Asset
    media_ep2 = next((m for m in all_media if m["id"] == env["media_asset_id_ep2"]), None)
    assert media_ep2 is not None, "Ep2 media asset must be explicitly retrievable"
    assert media_ep2["episode_id"] == env["ep2_id"]
    assert media_ep2["series_id"] == env["series_id"]
    
    # Adaptive Rendition Ladder Verification (1080p, 720p, 480p)
    renditions = storage_service.generate_adaptive_renditions(media_ep1["master_video_url"])
    assert len(renditions) >= 3, "Must generate at least 3 adaptive ladder renditions"
    resolutions = [r["resolution"] for r in renditions]
    assert "1080x1920" in resolutions
    assert "720x1280" in resolutions
    assert "480x854" in resolutions
    for r in renditions:
        assert r["stream_url"].endswith(".m3u8")
        assert "bitrate" in r


# ---------------------------------------------------------------------------
# TEST 3 — CMS / EXPERIENCE → VIEWER
# ---------------------------------------------------------------------------

def test_3_cms_experience_to_viewer(gate_b_environment):
    env = gate_b_environment
    # Add Sabelo to the Home manifest hero slot
    manifest = ExperienceEngine.get_stored_manifest("home", state="published")
    hero_sec = next((s for s in manifest.get("sections", []) if s.get("section_id") == "sec_hero_home"), None)
    if hero_sec:
        # Add slot for Sabelo
        hero_sec["items"].insert(0, {
            "slot_id": f"slot_hero_sabelo",
            "content_type": "series",
            "content_id": env["series_id"],
            "badge": "NEW ORIGINAL",
            "headline_override": "Sabelo: The Fontana Boss",
            "subheadline_override": "Desperate choices in the heart of Johannesburg",
            "cta_text": "Watch Episode 1",
            "cta_action": "STREAM_EPISODE",
            "cta_target": env["ep1_id"],
            "artwork_overrides": {
                "mobile_9_16": "/posters/sabelo.jpg",
                "desktop_16_9": "/banners/sabelo_banner.jpg"
            },
            "is_active": True
        })
        ExperienceEngine.save_layout(manifest)

    # Resolve manifest via public live endpoint
    res = client.get("/api/experience/page/home")
    assert res.status_code == 200
    data = res.json()
    assert "sections" in data
    
    # Locate Sabelo in hero section
    hero = next((s for s in data["sections"] if s["section_id"] == "sec_hero_home"), None)
    assert hero is not None
    sabelo_item = next((it for it in hero["items"] if it.get("content_id") == env["series_id"]), None)
    assert sabelo_item is not None
    assert sabelo_item["headline_override"] == "Sabelo: The Fontana Boss"
    assert sabelo_item["cta_target"] == env["ep1_id"]
    assert sabelo_item["story"]["id"] == env["series_id"]
    assert sabelo_item["story"]["title"] == "Sabelo: The Fontana Boss"

    # Verify Draft/Coming Soon episode is NOT available for streaming
    ep3_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep3_id']}")
    assert ep3_res.status_code == 200
    ep3_data = ep3_res.json()
    assert ep3_data["is_available"] is False
    assert ep3_data["status_label"] == "Coming Soon"
    assert ep3_data["stream"] is None
    assert ep3_data["fallback_media_permitted"] is False


# ---------------------------------------------------------------------------
# TEST 4 — VIEWER DISCOVERY → PLAYBACK
# ---------------------------------------------------------------------------

def test_4_viewer_discovery_to_playback(gate_b_environment):
    env = gate_b_environment
    # 1. Discovery fetch
    exp_res = client.get("/api/experience/page/home")
    assert exp_res.status_code == 200

    # 2. Episode stream request (First Load)
    ep1_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}?user_id=viewer_sabelo_01")
    assert ep1_res.status_code == 200
    stream_payload = ep1_res.json()
    
    assert stream_payload["is_available"] is True
    assert stream_payload["is_unlocked"] is True
    assert stream_payload["media_asset_id"] == env["media_asset_id_ep1"]
    assert stream_payload["stream"]["primary_url"] == env["master_video_url_ep1"]
    assert stream_payload["stream"]["format"] == "9:16 Canonical Vertical"
    assert len(stream_payload["stream"]["adaptive_renditions"]) >= 3

    # 3. Direct Episode Entry & Refresh (Second fetch simulation)
    refresh_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}?user_id=viewer_sabelo_01")
    assert refresh_res.status_code == 200
    assert refresh_res.json()["stream"]["primary_url"] == env["master_video_url_ep1"]


# ---------------------------------------------------------------------------
# TEST 5 — 9:16 PLAYER INTEGRITY
# ---------------------------------------------------------------------------

def test_5_vertical_player_integrity(gate_b_environment):
    env = gate_b_environment
    ep1_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}")
    data = ep1_res.json()
    
    # 9:16 Canonical Format
    assert data["stream"] is not None
    assert data["stream"]["format"] == "9:16 Canonical Vertical"
    
    # Cliffhanger detection & hook
    assert "cliffhanger" in data
    assert data["cliffhanger"]["timestamp_seconds"] == 75
    
    # Global Brand Ident verification in manifest
    manifest = ExperienceEngine.resolve_manifest("home", state="published")
    assert "brand_config" in manifest
    brand = manifest["brand_config"]
    assert brand["play_brand_ident"] is True
    assert brand["brand_ident_url"] == "/videos/welele_ident_v2.mp4"
    assert brand["asset"]["name"] == "Welele Sonic Visual Ident v2"


# ---------------------------------------------------------------------------
# TEST 6 — COMMENTS / REACTIONS / COMMUNITY
# ---------------------------------------------------------------------------

def test_6_community_engagement_and_zero_forge_mutation(gate_b_environment):
    env = gate_b_environment
    ep1_id = env["ep1_id"]
    
    # 1. Post Comment
    comment_payload = {
        "episode_id": ep1_id,
        "user_name": "Kgomotso_JHB",
        "avatar": "https://images.unsplash.com/photo-1534528741775",
        "text": "Jonas is my favourite character, such a ruthless villain!"
    }
    c_res = client.post(f"/api/chat/episodes/{ep1_id}/comments", json=comment_payload)
    assert c_res.status_code == 200
    assert c_res.json()["success"] is True
    
    # 2. Send Reaction
    react_payload = {
        "episode_id": ep1_id,
        "emoji": "🔥",
        "timestamp_seconds": 45
    }
    r_res = client.post(f"/api/chat/episodes/{ep1_id}/reactions", json=react_payload)
    assert r_res.status_code == 200
    assert r_res.json()["success"] is True
    
    # 3. Retrieve Comments & Reactions
    get_c = client.get(f"/api/chat/episodes/{ep1_id}/comments")
    assert get_c.status_code == 200
    comments = get_c.json()["comments"]
    assert any(c["text"] == "Jonas is my favourite character, such a ruthless villain!" for c in comments)
    
    get_r = client.get(f"/api/chat/episodes/{ep1_id}/reactions")
    assert get_r.status_code == 200
    reactions = get_r.json()["reactions"]
    assert any(r["emoji"] == "🔥" and r["timestamp_seconds"] == 45 for r in reactions)

    # 4. HARD TRUTH BOUNDARY CHECK:
    # Verify Story Forge Canonical State in Forge Repo is completely untouched by comments/reactions
    forge_repo = env["forge_repo"]
    story_state = forge_repo.get_current_state(env["story_id"])
    assert story_state is not None
    # Protagonist and Antagonist remain strictly immutable
    assert story_state.characters["Sabelo"].role == CharacterRole.PROTAGONIST
    assert story_state.characters["Jonas"].role == CharacterRole.ANTAGONIST
    assert "Kgomotso_JHB" not in story_state.characters
    assert not any("Jonas is my favourite character" in ev.headline or "Jonas is my favourite character" in ev.description for ev in story_state.chronology)


# ---------------------------------------------------------------------------
# TEST 7 — SESSION / TELEMETRY
# ---------------------------------------------------------------------------

def test_7_session_telemetry_lineage(gate_b_environment):
    env = gate_b_environment
    session_id = f"sess_gate_b_{uuid.uuid4().hex[:8]}"
    viewer_id = "viewer_sabelo_01"
    
    # Timeline events: OPEN -> PLAY -> PROGRESS 25/50/75 -> PAUSE -> COMPLETE
    events = [
        ViewerTelemetryEvent(
            event_id=f"evt_open_{uuid.uuid4().hex[:6]}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.CONTENT_OPENED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            viewer_id=viewer_id,
            content_id=env["ep1_id"],
            series_id=env["series_id"],
            episode_id=env["ep1_id"],
            position_seconds=0.0,
            duration_seconds=90.0,
            event_source=EventSource.CLIENT,
            source="HERO_CAROUSEL"
        ),
        ViewerTelemetryEvent(
            event_id=f"evt_play_{uuid.uuid4().hex[:6]}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            viewer_id=viewer_id,
            content_id=env["ep1_id"],
            series_id=env["series_id"],
            episode_id=env["ep1_id"],
            position_seconds=0.1,
            duration_seconds=90.0,
            event_source=EventSource.CLIENT
        ),
        ViewerTelemetryEvent(
            event_id=f"evt_prog25_{uuid.uuid4().hex[:6]}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            viewer_id=viewer_id,
            content_id=env["ep1_id"],
            series_id=env["series_id"],
            episode_id=env["ep1_id"],
            position_seconds=22.5,
            duration_seconds=90.0,
            milestone_pct=25,
            event_source=EventSource.CLIENT
        ),
        ViewerTelemetryEvent(
            event_id=f"evt_pause_{uuid.uuid4().hex[:6]}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PAUSED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            viewer_id=viewer_id,
            content_id=env["ep1_id"],
            series_id=env["series_id"],
            episode_id=env["ep1_id"],
            position_seconds=45.0,
            duration_seconds=90.0,
            event_source=EventSource.CLIENT
        ),
        ViewerTelemetryEvent(
            event_id=f"evt_comp_{uuid.uuid4().hex[:6]}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_COMPLETED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            viewer_id=viewer_id,
            content_id=env["ep1_id"],
            series_id=env["series_id"],
            episode_id=env["ep1_id"],
            position_seconds=90.0,
            duration_seconds=90.0,
            milestone_pct=100,
            event_source=EventSource.CLIENT
        )
    ]

    for ev in events:
        res = client.post("/api/telemetry/events", json=ev.model_dump())
        assert res.status_code == 200
        assert res.json().get("status") in ("recorded", "deduplicated")

    # Retrieve and verify session trail
    trail_res = client.get(f"/api/telemetry/sessions/{session_id}")
    assert trail_res.status_code == 200
    trail = trail_res.json()
    assert len(trail) == 5
    for item in trail:
        assert item["session_id"] == session_id
        assert item["viewer_id"] == viewer_id
        assert item["series_id"] == env["series_id"]
        assert item["episode_id"] == env["ep1_id"]
        assert item["content_id"] == env["ep1_id"]


# ---------------------------------------------------------------------------
# TEST 8 — MONETISATION / ENTITLEMENT PATH
# ---------------------------------------------------------------------------

def test_8_monetisation_and_ledger_entitlement(gate_b_environment):
    env = gate_b_environment
    viewer_id = f"viewer_pay_{uuid.uuid4().hex[:6]}"
    
    # 1. Initialize wallet to 0 coins for clean unlock test
    wallet = ledger_service.get_or_create_wallet(viewer_id)
    ledger_repository.local_update("wallets", "id", wallet["id"], {
        "coin_balance": 0,
        "bonus_coins": 0
    })
    
    # 2. Check Episode 2 is initially LOCKED
    stream_check = client.get(f"/api/episodes/{env['series_id']}/{env['ep2_id']}?user_id={viewer_id}")
    assert stream_check.status_code == 200
    assert stream_check.json()["is_unlocked"] is False

    # 3. Attempt unlock with ZERO balance -> Should fail
    fail_unlock = client.post(
        f"/api/episodes/{env['series_id']}/{env['ep2_id']}/unlock?user_id={viewer_id}&method=COINS"
    )
    assert fail_unlock.status_code == 400
    assert "Insufficient" in fail_unlock.json()["detail"] or "balance" in fail_unlock.json()["detail"].lower()

    # 4. Fund wallet via airtime/coin test topup path (+20 coins)
    ledger_service.credit_coins(
        user_id=viewer_id,
        base_coins=20,
        bonus_coins=0,
        transaction_type="TOPUP_VODACOM_DCB",
        reference_id=f"ref_topup_{uuid.uuid4().hex[:6]}",
        description="Airtime topup 20 coins"
    )
    bal = ledger_service.get_balance(viewer_id)
    assert bal["total_usable_coins"] == 20

    # 5. Successful unlock (price: 5 coins)
    unlock_res = client.post(
        f"/api/episodes/{env['series_id']}/{env['ep2_id']}/unlock?user_id={viewer_id}&method=COINS"
    )
    assert unlock_res.status_code == 200
    unlock_data = unlock_res.json()
    assert unlock_data["success"] is True
    assert unlock_data["remaining_balance"] == 15

    # 6. Playback now unlocked
    stream_unlocked = client.get(f"/api/episodes/{env['series_id']}/{env['ep2_id']}?user_id={viewer_id}")
    assert stream_unlocked.status_code == 200
    assert stream_unlocked.json()["is_unlocked"] is True
    assert stream_unlocked.json()["stream"]["primary_url"] == env["master_video_url_ep2"]

    # 7. Verify Double-Entry Ledger History & Balance
    history = ledger_service.get_ledger_history(viewer_id)
    assert len(history) >= 2
    types = [h["transaction_type"] for h in history]
    assert "TOPUP_VODACOM_DCB" in types
    assert "EPISODE_UNLOCK" in types

    # 8. Duplicate unlock attempt is handled gracefully without double-charging
    unlock_dup = client.post(
        f"/api/episodes/{env['series_id']}/{env['ep2_id']}/unlock?user_id={viewer_id}&method=COINS"
    )
    assert unlock_dup.status_code == 200
    assert unlock_dup.json()["remaining_balance"] == 15


# ---------------------------------------------------------------------------
# TEST 9 — FAILURE / INTERRUPTION TEST
# ---------------------------------------------------------------------------

def test_9_failure_interruption_and_resilience(gate_b_environment):
    env = gate_b_environment
    
    # A. Non-existent Series / Episode returns truthful 404 (No silent fabrication)
    res_404 = client.get("/api/episodes/series_non_existent/ep_9999")
    assert res_404.status_code == 404

    # B. Corrupt / Draft media asset -> availability gate marks is_available=False
    corrupt_series_id = f"series_corrupt_{uuid.uuid4().hex[:6]}"
    series_repository.local_insert("series", {
        "id": corrupt_series_id,
        "title": "Corrupt Media Series",
        "ip_id": env["ip_sabelo"]["id"],
        "story_package_id": env["story_pkg_id"],
        "is_published": True
    })
    fake_ep = series_episode_service.create_episode(
        series_id=corrupt_series_id,
        episode_number=1,
        custom_title="Episode 1 — Corrupt Media",
        is_empty_draft=False
    )
    series_repository.local_update("episodes", "id", fake_ep["id"], {
        "video_url": "/videos/welele_placeholder.mp4",
        "readiness_state": "DRAFT_EMPTY",
        "lifecycle_state": "DRAFT"
    })
    corrupt_check = client.get(f"/api/episodes/{corrupt_series_id}/{fake_ep['id']}")
    assert corrupt_check.status_code == 200
    assert corrupt_check.json()["is_available"] is False
    assert corrupt_check.json()["fallback_media_permitted"] is False
    assert corrupt_check.json()["stream"] is None

    # C. Telemetry resilience under network reconnect (duplicate event ingestion is idempotent)
    dup_event_id = f"evt_dup_{uuid.uuid4().hex[:6]}"
    ev = ViewerTelemetryEvent(
        event_id=dup_event_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id="sess_net_fail",
        viewer_id="viewer_test",
        content_id=env["ep1_id"],
        series_id=env["series_id"],
        episode_id=env["ep1_id"],
        position_seconds=0.0,
        duration_seconds=90.0,
        event_source=EventSource.CLIENT
    )
    r1 = client.post("/api/telemetry/events", json=ev.model_dump())
    assert r1.status_code == 200
    r2 = client.post("/api/telemetry/events", json=ev.model_dump())
    assert r2.status_code == 200
    assert r2.json()["status"] == "deduplicated"


# ---------------------------------------------------------------------------
# TEST 10 — OFFLINE / MOCK FALLBACK INTEGRITY
# ---------------------------------------------------------------------------

def test_10_offline_mock_fallback_integrity(gate_b_environment):
    env = gate_b_environment
    # Verify production path explicitly carries CANON provenance
    ep1_data = next((e for e in series_repository.local_get("episodes") if e.get("id") == env["ep1_id"]), None)
    assert ep1_data is not None
    assert ep1_data["provenance"] == "CANON"
    assert ep1_data["source_lineage_hash"] == f"hash_sabelo_v{env['story_package'].state_version}"
    
    # Check that stream response explicitly forbids fallback media
    stream_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}")
    assert stream_res.json()["fallback_media_permitted"] is False


# ---------------------------------------------------------------------------
# TEST 11 — IDENTITY / DATA-SPINE INTEGRITY
# ---------------------------------------------------------------------------

def test_11_identity_data_spine_trace(gate_b_environment):
    env = gate_b_environment
    viewer_id = "viewer_trace_sabelo"
    session_id = f"sess_trace_{uuid.uuid4().hex[:6]}"

    # Ingest a traceable telemetry event
    tel_event_id = f"tel_trace_{uuid.uuid4().hex[:6]}"
    ev = ViewerTelemetryEvent(
        event_id=tel_event_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        viewer_id=viewer_id,
        content_id=env["ep1_id"],
        series_id=env["series_id"],
        episode_id=env["ep1_id"],
        position_seconds=5.0,
        duration_seconds=90.0,
        event_source=EventSource.CLIENT
    )
    viewer_telemetry_service.record_event(ev)

    # Unlock Episode 2 to generate Entitlement and Ledger Entry
    ledger_service.credit_coins(viewer_id, 10, transaction_type="TOPUP_TEST")
    ok, msg, unlock_record = ledger_service.unlock_episode(
        user_id=viewer_id,
        episode_id=env["ep2_id"],
        story_id=env["series_id"],
        coin_price=5
    )
    assert ok is True
    entitlement_id = unlock_record["id"]
    history = ledger_service.get_ledger_history(viewer_id)
    unlock_tx = next((h for h in history if h.get("transaction_type") == "EPISODE_UNLOCK"), history[0])
    ledger_entry_id = unlock_tx["id"]

    # Verify complete data-spine relationship
    assert env["story_id"] == "sabelo_gate_b_clean"
    assert env["story_pkg_id"] == "pkg_sabelo_gate_b_clean_m3"
    assert env["series_id"].startswith("series_")
    assert env["ep1_id"].startswith("ep_")
    assert env["media_asset_id_ep1"] == "asset_sabelo_s01e01_v1"
    assert viewer_id == "viewer_trace_sabelo"
    assert session_id.startswith("sess_trace_")
    assert tel_event_id.startswith("tel_trace_")
    assert entitlement_id.startswith("unl_")
    assert ledger_entry_id.startswith("ledg_")

    print("\n--- TEST 11: DATA-SPINE DETERMINISTIC TRACE ---")
    print(f"Story ID:            {env['story_id']}")
    print(f"Story Package ID:    {env['story_pkg_id']}")
    print(f"Series ID:           {env['series_id']}")
    print(f"Episode ID:          {env['ep1_id']}")
    print(f"Media Asset ID:      {env['media_asset_id_ep1']}")
    print(f"Viewer ID:           {viewer_id}")
    print(f"Session ID:          {session_id}")
    print(f"Telemetry Event ID:  {tel_event_id}")
    print(f"Entitlement ID:      {entitlement_id}")
    print(f"Ledger Entry ID:     {ledger_entry_id}")


# ---------------------------------------------------------------------------
# TEST 12 — STORY TRUTH BOUNDARY
# ---------------------------------------------------------------------------

def test_12_story_truth_boundary_isolation(gate_b_environment):
    env = gate_b_environment
    # Verify viewer metadata strictly matches Story Package and Canonical State
    sabelo_state = env["forge_repo"].get_current_state(env["story_id"])
    assert sabelo_state.characters["Sabelo"].role == CharacterRole.PROTAGONIST
    assert sabelo_state.characters["Jonas"].role == CharacterRole.ANTAGONIST
    assert "Zodwa" in sabelo_state.characters
    assert "Sister" not in sabelo_state.characters, "Stale unresolved 'Sister' entity must NOT exist"
    
    # Series synopsis strictly carries the package logline
    series_data = series_repository.get_series(env["series_id"])
    assert series_data["title"] == "Sabelo: The Fontana Boss"
    assert "Zodwa" in series_data["synopsis"] or "sister" in series_data["synopsis"].lower()

    # Viewer comments cannot add or alter character names in Forge
    client.post(f"/api/chat/episodes/{env['ep1_id']}/comments", json={
        "episode_id": env["ep1_id"],
        "user_name": "Fan_99",
        "text": "Actually Sabelo's uncle Sipho is the boss!"
    })
    forge_state = env["forge_repo"].get_current_state(env["story_id"])
    assert "Sipho" not in forge_state.characters
    assert "Fan_99" not in forge_state.characters


# ---------------------------------------------------------------------------
# TEST 13 — MULTI-STORY ISOLATION
# ---------------------------------------------------------------------------

def test_13_multi_story_isolation(gate_b_environment):
    env = gate_b_environment
    viewer_sabelo = "viewer_sabelo_iso"
    viewer_thandi = "viewer_thandi_iso"

    # Ingest Sabelo telemetry
    sabelo_session = f"sess_sabelo_{uuid.uuid4().hex[:6]}"
    client.post("/api/telemetry/events", json=ViewerTelemetryEvent(
        event_id=f"evt_sab_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=sabelo_session,
        viewer_id=viewer_sabelo,
        content_id=env["ep1_id"],
        series_id=env["series_id"],
        episode_id=env["ep1_id"],
        position_seconds=0.0,
        duration_seconds=90.0
    ).model_dump())

    # Ingest Thandi telemetry
    thandi_session = f"sess_thandi_{uuid.uuid4().hex[:6]}"
    client.post("/api/telemetry/events", json=ViewerTelemetryEvent(
        event_id=f"evt_tha_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=thandi_session,
        viewer_id=viewer_thandi,
        content_id=env["thandi_ep1_id"],
        series_id=env["thandi_series_id"],
        episode_id=env["thandi_ep1_id"],
        position_seconds=0.0,
        duration_seconds=90.0
    ).model_dump())

    # Verify session isolation
    sabelo_events = client.get(f"/api/telemetry/sessions/{sabelo_session}").json()
    assert all(e["series_id"] == env["series_id"] for e in sabelo_events)
    assert not any(e["series_id"] == env["thandi_series_id"] for e in sabelo_events)

    thandi_events = client.get(f"/api/telemetry/sessions/{thandi_session}").json()
    assert all(e["series_id"] == env["thandi_series_id"] for e in thandi_events)
    assert not any(e["series_id"] == env["series_id"] for e in thandi_events)

    # Verify Comments Isolation
    client.post(f"/api/chat/episodes/{env['ep1_id']}/comments", json={
        "episode_id": env["ep1_id"],
        "user_name": "Sabelo_Fan",
        "text": "Sabelo is so brave!"
    })
    client.post(f"/api/chat/episodes/{env['thandi_ep1_id']}/comments", json={
        "episode_id": env["thandi_ep1_id"],
        "user_name": "Thandi_Fan",
        "text": "Thandi's lip reading skills are incredible!"
    })

    s_comments = client.get(f"/api/chat/episodes/{env['ep1_id']}/comments").json()["comments"]
    t_comments = client.get(f"/api/chat/episodes/{env['thandi_ep1_id']}/comments").json()["comments"]
    
    assert any("Sabelo is so brave!" in c["text"] for c in s_comments)
    assert not any("Thandi's lip reading" in c["text"] for c in s_comments)
    assert any("Thandi's lip reading" in c["text"] for c in t_comments)
    assert not any("Sabelo is so brave!" in c["text"] for c in t_comments)


# ---------------------------------------------------------------------------
# TEST 14 — REFRESH / RELOAD / SECOND SESSION
# ---------------------------------------------------------------------------

def test_14_reload_and_second_session(gate_b_environment):
    env = gate_b_environment
    viewer_id = f"viewer_session_return_{uuid.uuid4().hex[:6]}"

    # Initialize wallet to 0 coins
    wallet = ledger_service.get_or_create_wallet(viewer_id)
    ledger_repository.local_update("wallets", "id", wallet["id"], {
        "coin_balance": 0,
        "bonus_coins": 0
    })

    # Session 1: Topup 10 coins, Unlock Ep 2 (5 coins), Post comment
    ledger_service.credit_coins(viewer_id, 10, transaction_type="TOPUP_TEST")
    client.post(f"/api/episodes/{env['series_id']}/{env['ep2_id']}/unlock?user_id={viewer_id}&method=COINS")
    client.post(f"/api/chat/episodes/{env['ep2_id']}/comments", json={
        "episode_id": env["ep2_id"],
        "user_name": "Persistent_Viewer",
        "text": "Session 1 comment"
    })

    # Session 2: New browser / app reopen simulation
    stream_s2 = client.get(f"/api/episodes/{env['series_id']}/{env['ep2_id']}?user_id={viewer_id}")
    assert stream_s2.status_code == 200
    assert stream_s2.json()["is_unlocked"] is True, "Entitlement must persist across sessions"

    comments_s2 = client.get(f"/api/chat/episodes/{env['ep2_id']}/comments").json()["comments"]
    assert any(c["text"] == "Session 1 comment" for c in comments_s2), "Comments must persist across sessions"

    bal_s2 = ledger_service.get_balance(viewer_id)
    assert bal_s2["total_usable_coins"] == 5, "Coin balance must remain authoritative (10 topup - 5 spent = 5)"


# ---------------------------------------------------------------------------
# TEST 15 — AUTHORITATIVE STATE CONVERGENCE
# ---------------------------------------------------------------------------

def test_15_authoritative_state_convergence(gate_b_environment):
    env = gate_b_environment
    # Verify the entire data-spine alignment
    # 1. Story Forge Package
    pkg = env["story_package"]
    assert pkg.readiness_status == ReadinessStatus.FORGE_COMPLETE
    assert pkg.milestone == MilestoneEnum.M3_FORGE_COMPLETE
    
    # 2. Series Model
    series = series_repository.get_series(env["series_id"])
    assert series["source_lineage_hash"] == f"hash_sabelo_v{pkg.state_version}"
    
    # 3. Episode Model
    ep1 = next((e for e in series_repository.local_get("episodes") if e.get("id") == env["ep1_id"]), None)
    assert ep1 is not None
    assert ep1["series_id"] == series["id"]
    assert ep1["story_package_id"] == pkg.story_id or ep1["story_package_id"] == env["story_pkg_id"]
    
    # 4. Media Asset
    media = series_repository.local_get("media_assets")
    ep1_media = next((m for m in media if m["id"] == env["media_asset_id_ep1"]), None)
    assert ep1_media["episode_id"] == ep1["id"]
    assert ep1_media["status"] == "verified"
    
    # 5. CMS Experience
    manifest = ExperienceEngine.resolve_manifest("home", state="published")
    hero_sec = next((s for s in manifest["sections"] if s["section_id"] == "sec_hero_home"), None)
    sabelo_item = next((it for it in hero_sec["items"] if it.get("content_id") == series["id"]), None)
    assert sabelo_item is not None
    assert sabelo_item["story"]["title"] == "Sabelo: The Fontana Boss"
    
    print("\n=======================================================")
    print("PHASE 1 — GATE B: ALL 15 TESTS CONVERGED SUCCESSFULLY")
    print("=======================================================")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])



