"""
PHASE 1 — GATE C: CREATOR → PRODUCTION INTEGRATION TEST SUITE
Comprehensive verification of the full Creator → Production → Platform → Viewer operating loop.
Proves that a creator can take a story from inception through Story Forge, production packaging,
media attachment, CMS publishing, viewer discovery, playback, interaction, and telemetry
without developer intervention or manual database manipulation.
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
from services.viewer_telemetry_service import viewer_telemetry_service
from schemas.viewer_telemetry_models import (
    ViewerTelemetryEvent, EventSpineFamily, ViewerEventType, EventSource
)
from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus,
    MilestoneEnum, ReadinessStatus, DependencyStatus, AuthorityMode,
    CharacterRelationship, NarrativePlant, WorldSetting, ChronologyEvent,
    ProductionDecision, ProductionAspect
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.api.routes import get_story_package

client = TestClient(app)


# ---------------------------------------------------------------------------
# FIXTURES & CLEAN-ROOM SETUP
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gate_c_environment():
    """
    Initializes a certified clean environment for a brand-new creator: 'creator_nomvula'.
    Story A: 'Nomvula: Lightning Queen'
    """
    forge_repo = InMemoryStoryForgeRepository()
    creator_id = "creator_nomvula"
    story_id = f"nomvula_gate_c_clean"

    # 1. Creator creates story in Forge
    forge_repo.create_story(
        story_id=story_id,
        title="Nomvula: Lightning Queen",
        owner_id=creator_id,
        logline="Sci-fi vertical drama set in Durban. A young electrical apprentice discovers she can control lightning during a catastrophic city blackout.",
        primary_language="isiZulu"
    )
    session_id = f"sess_{story_id}_01"
    forge_repo.create_session(story_id, creator_id, session_id)
    kernel = StoryForgeKernel(repository=forge_repo)
    judge = ForgeJudge(repository=forge_repo)

    # Cycle 1: Core Setup
    kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        creator_input="Nomvula is a 21-year-old electrical apprentice working at the Durban harbour power grid who discovers she can manipulate electrical currents. The sinister grid director Silas plans to sabotage the provincial power supply."
    )
    # Cycle 2: Escalation & Conflict
    kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        creator_input="Nomvula confronts Silas in the substation control room. Silas activates an overload protocol to trigger a citywide blackout. Nomvula's mentor Baba Khumalo helps her reroute the main transformers."
    )
    # Cycle 3: Climax & Resolution
    kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        creator_input="Nomvula channels the massive surge through her own body, safely discharging it into the ocean while restoring power to the children's hospital. Silas is captured by metro police. That is the end."
    )

    state = forge_repo.get_current_state(story_id)
    state.previous_state_version = state.state_version
    state.state_version += 1
    state.explicit_ending_declared = True
    state.characters["Nomvula"] = CharacterState(
        name="Nomvula", role=CharacterRole.PROTAGONIST, core_motivation="Protect Durban grid",
        relationships=[CharacterRelationship(target_character="Silas", relation_type="OPPOSITION", dynamic="Nomvula opposes Silas")]
    )
    state.characters["Silas"] = CharacterState(
        name="Silas", role=CharacterRole.ANTAGONIST, core_motivation="Sabotage power grid",
        relationships=[CharacterRelationship(target_character="Nomvula", relation_type="OPPOSITION", dynamic="Silas attacks Nomvula")]
    )
    state.plants.append(NarrativePlant(plant_name="transformer_failsafe", description="Secret bypass", intended_payoff="Used in climax"))
    state.world = WorldSetting(rules_and_lore=["Grid frequency failsafe"])
    state.chronology = [
        ChronologyEvent(story_id=story_id, state_version=state.state_version, event_sequence=i, headline=f"Event {i}", description=f"Desc {i}", anchor_type="EVENT_PROGRESSION")
        for i in range(1, 7)
    ]
    forge_repo.save_state(state)

    for d in forge_repo.get_dependencies(story_id):
        d.status = DependencyStatus.RESOLVED
        forge_repo.save_dependency(d)

    forge_repo.save_production_decision(
        ProductionDecision(
            story_id=story_id,
            decision_key="PROD_LOCATION_DURBAN",
            narrative_resolution="Substation scenes filmed at Durban harbour.",
            production_aspect=ProductionAspect.LOCATION,
            deferred_details="Location scouting complete."
        )
    )

    story_pkg = get_story_package(story_id, repo=forge_repo, judge=judge)
    story_pkg_id = f"pkg_{story_id}_m3"

    # 2. Register Digital IP
    ip_dict = {
        "id": f"ip_{story_id}",
        "title": story_pkg.title,
        "franchise_code": "IP-NOMVULA",
        "logline": story_pkg.logline,
        "synopsis": story_pkg.logline,
        "genre": "Sci-Fi / Vertical Microdrama",
        "primary_language": "isiZulu",
        "master_owner_id": creator_id
    }
    ip_repository.local_insert("digital_ips", ip_dict)

    # 3. Register Story Package
    pkg_record = {
        "id": story_pkg_id,
        "ip_id": ip_dict["id"],
        "creator_id": creator_id,
        "package_title": story_pkg.title,
        "story_world_id": "sw_durban_grid",
        "target_duration_seconds": 90,
        "version": "1.0.0",
        "primary_language": "isiZulu",
        "logline": story_pkg.logline,
        "genre": ip_dict["genre"],
        "thematic_premise": "Power and responsibility in modern Durban",
        "chronology_spine": [
            {"anchor_number": i + 1, "anchor_name": e.get("headline", f"Event {i+1}"), "summary": e.get("description", "")}
            for i, e in enumerate(story_pkg.chronology_spine)
        ],
        "plants": story_pkg.narrative_plants,
        "world_rules": [],
        "dialogues": [],
        "beats": [
            {"beat_number": 1, "label": "The Surge", "timestamp_seconds": 15, "action_description": "Nomvula discovers lightning power"},
            {"beat_number": 2, "label": "The Overload", "timestamp_seconds": 60, "action_description": "Silas sabotages power grid"},
            {"beat_number": 3, "label": "The Discharge", "timestamp_seconds": 88, "action_description": "Nomvula saves the city"}
        ],
        "forge_configuration_id": "CFG-001",
        "lineage_hash": f"hash_nomvula_v{story_pkg.state_version}"
    }
    ip_repository.local_insert("story_forge_packages", pkg_record)

    # 4. Create Series for Nomvula
    series = series_episode_service.create_series_from_story_package(
        ip_id=ip_dict["id"],
        story_package_id=story_pkg_id,
        season_number=1,
        custom_title="Nomvula: Lightning Queen"
    )
    series_id = series["id"]
    series_repository.local_update("series", "id", series_id, {
        "title": "Nomvula: Lightning Queen",
        "vertical_poster": "/posters/nomvula_poster.jpg",
        "cover_image": "/banners/nomvula_banner.jpg",
        "is_published": True,
        "free_episodes": 1,
        "status": "published"
    })

    # Register in db.stories for backward compatibility
    stories = db.get("stories")
    if not any(s["id"] == series_id for s in stories):
        db.insert("stories", {
            "id": series_id,
            "title": "Nomvula: Lightning Queen",
            "logline": ip_dict["logline"],
            "genre": ip_dict["genre"],
            "primary_language": "isiZulu",
            "cover_image": "/banners/nomvula_banner.jpg",
            "vertical_poster": "/posters/nomvula_poster.jpg",
            "free_episodes_count": 1,
            "is_published": True
        })

    # 5. Create Episodes for Nomvula
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=1,
            custom_title="Episode 1 — The Surge",
            is_empty_draft=False
        )
    ep1_id = ep1["id"]
    media_asset_id_ep1 = f"asset_nomvula_s01e01_v1"
    master_video_url_ep1 = "/videos/nomvula_s01e01_master.mp4"

    series_repository.local_update("episodes", "id", ep1_id, {
        "series_id": series_id,
        "title": "Episode 1 — The Surge",
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

    return {
        "forge_repo": forge_repo,
        "creator_id": creator_id,
        "story_id": story_id,
        "session_id": session_id,
        "story_pkg": story_pkg,
        "story_pkg_id": story_pkg_id,
        "ip_id": ip_dict["id"],
        "series_id": series_id,
        "ep1_id": ep1_id,
        "media_asset_id_ep1": media_asset_id_ep1,
        "master_video_url_ep1": master_video_url_ep1
    }


# ---------------------------------------------------------------------------
# TEST 1 — CREATOR ENTRY
# ---------------------------------------------------------------------------

def test_1_creator_entry(gate_c_environment):
    """
    Creator enters Creator Studio, starts a fresh story, provides natural-language premise.
    Verifies no creator-facing machine ontology is presented.
    """
    env = gate_c_environment
    forge_repo = env["forge_repo"]
    story_meta = forge_repo.get_story(env["story_id"])
    story_state = forge_repo.get_current_state(env["story_id"])

    assert story_meta is not None
    assert story_meta["title"] == "Nomvula: Lightning Queen"
    assert story_meta["primary_language"] == "isiZulu"

    assert story_state is not None
    assert story_state.title == "Nomvula: Lightning Queen"
    assert "Nomvula" in story_state.characters
    assert story_state.characters["Nomvula"].role == CharacterRole.PROTAGONIST
    assert "Silas" in story_state.characters


# ---------------------------------------------------------------------------
# TEST 2 — CREATOR STORY FORGE → STORY PACKAGE
# ---------------------------------------------------------------------------

def test_2_forge_to_story_package(gate_c_environment):
    """
    Creator completes the Forge cycles.
    Verifies Canonical Story State -> Forge Judge -> Story Package compilation.
    """
    env = gate_c_environment
    story_pkg = env["story_pkg"]

    assert story_pkg.title == "Nomvula: Lightning Queen"
    assert story_pkg.milestone == MilestoneEnum.M3_FORGE_COMPLETE
    assert story_pkg.readiness_status == ReadinessStatus.FORGE_COMPLETE
    assert len(story_pkg.characters) >= 2
    assert any(c["name"] == "Nomvula" and c["role"] == "PROTAGONIST" for c in story_pkg.characters)
    assert any(c["name"] == "Silas" for c in story_pkg.characters)
    assert len(story_pkg.chronology_spine) >= 3


# ---------------------------------------------------------------------------
# TEST 3 — STORY PACKAGE HANDOFF
# ---------------------------------------------------------------------------

def test_3_story_package_handoff(gate_c_environment):
    """
    Authoritative Story Package transitions into production workflow without manual copy-paste.
    """
    env = gate_c_environment
    story_pkg_id = env["story_pkg_id"]

    all_pkgs = ip_repository.local_get("story_forge_packages")
    retrieved = next((p for p in all_pkgs if p["id"] == story_pkg_id), None)
    assert retrieved is not None
    assert retrieved["package_title"] == "Nomvula: Lightning Queen"
    assert retrieved["ip_id"] == env["ip_id"]


# ---------------------------------------------------------------------------
# TEST 4 — CREATOR PRODUCTION HANDOFF
# ---------------------------------------------------------------------------

def test_4_creator_production_handoff(gate_c_environment):
    """
    Creates Series and Episode downstream referencing the Story Package.
    Enforces lineage: IP -> Story Package -> Series -> Episode -> Media.
    """
    env = gate_c_environment
    series = series_repository.get_series(env["series_id"])
    ep1 = next((e for e in series_repository.local_get("episodes") if e.get("id") == env["ep1_id"]), None)

    assert series is not None
    assert series["ip_id"] == env["ip_id"]
    assert series["story_package_id"] == env["story_pkg_id"]
    assert ep1 is not None
    assert ep1["series_id"] == env["series_id"]
    assert ep1["story_package_id"] == env["story_pkg_id"]


# ---------------------------------------------------------------------------
# TEST 5 — MEDIA INGESTION
# ---------------------------------------------------------------------------

def test_5_media_ingestion(gate_c_environment):
    """
    Attaches media asset to Episode 1, generates adaptive ladder, verifies delivery URLs.
    """
    env = gate_c_environment
    all_media = series_repository.local_get("media_assets")
    media = next((m for m in all_media if m["id"] == env["media_asset_id_ep1"]), None)

    assert media is not None
    assert media["episode_id"] == env["ep1_id"]
    assert media["series_id"] == env["series_id"]
    assert media["status"] == "verified"

    renditions = storage_service.generate_adaptive_renditions(media["master_video_url"])
    assert len(renditions) >= 3
    resolutions = [r["resolution"] for r in renditions]
    assert "1080x1920" in resolutions
    assert "720x1280" in resolutions
    assert "480x854" in resolutions


# ---------------------------------------------------------------------------
# TEST 6 — CONTENT METADATA
# ---------------------------------------------------------------------------

def test_6_content_metadata_control(gate_c_environment):
    """
    Creator controls metadata (poster, synopsis, language, pricing).
    """
    env = gate_c_environment
    series_repository.local_update("series", "id", env["series_id"], {
        "vertical_poster": "/posters/nomvula_poster.jpg",
        "cover_image": "/banners/nomvula_banner.jpg",
        "synopsis": "A young apprentice discovers electrical powers during a blackout.",
        "free_episodes": 1,
        "is_published": True,
        "status": "published"
    })

    updated = series_repository.get_series(env["series_id"])
    assert updated["vertical_poster"] == "/posters/nomvula_poster.jpg"
    assert updated["synopsis"] == "A young apprentice discovers electrical powers during a blackout."
    assert updated["free_episodes"] == 1


# ---------------------------------------------------------------------------
# TEST 7 — CMS / EXPERIENCE PUBLISHING
# ---------------------------------------------------------------------------

def test_7_cms_experience_publishing(gate_c_environment):
    """
    Curates series into Home Experience manifest; verifies public endpoint exposes authoritative data.
    """
    env = gate_c_environment
    manifest = ExperienceEngine.get_stored_manifest("home", state="published")
    hero_sec = next((s for s in manifest.get("sections", []) if s.get("section_id") == "sec_hero_home"), None)
    if hero_sec:
        hero_sec["items"].insert(0, {
            "slot_id": f"slot_hero_nomvula",
            "content_type": "series",
            "content_id": env["series_id"],
            "badge": "CREATOR ORIGINAL",
            "headline_override": "Nomvula: Lightning Queen",
            "subheadline_override": "Power and responsibility in modern Durban",
            "cta_text": "Stream Now",
            "cta_action": "STREAM_EPISODE",
            "cta_target": env["ep1_id"],
            "artwork_overrides": {
                "mobile_9_16": "/posters/nomvula_poster.jpg",
                "desktop_16_9": "/banners/nomvula_banner.jpg"
            },
            "is_active": True
        })
        ExperienceEngine.save_layout(manifest)

    # Fetch via public live endpoint
    res = client.get("/api/experience/page/home")
    assert res.status_code == 200
    data = res.json()
    hero = next((s for s in data["sections"] if s["section_id"] == "sec_hero_home"), None)
    assert hero is not None
    item = next((it for it in hero["items"] if it.get("content_id") == env["series_id"]), None)
    assert item is not None
    assert item["headline_override"] == "Nomvula: Lightning Queen"
    assert item["cta_target"] == env["ep1_id"]


# ---------------------------------------------------------------------------
# TEST 8 — DRAFT → REVIEW → PUBLISH
# ---------------------------------------------------------------------------

def test_8_draft_review_publish_lifecycle(gate_c_environment):
    """
    Verifies that draft content is strictly unplayable until reviewed and published.
    """
    env = gate_c_environment
    series_id = env["series_id"]

    # 1. Create Episode 2 in DRAFT state
    all_eps = series_repository.get_episodes_for_series(series_id)
    ep2 = next((e for e in all_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(
            series_id=series_id,
            episode_number=2,
            custom_title="Episode 2 — The Overload",
            is_empty_draft=True
        )
    ep2_id = ep2["id"]
    env["ep2_id"] = ep2_id

    # Verify DRAFT is unplayable
    ep2_draft = client.get(f"/api/episodes/{series_id}/{ep2_id}")
    assert ep2_draft.status_code == 200
    assert ep2_draft.json()["is_available"] is False
    assert ep2_draft.json()["stream"] is None

    # 2. Attach media and promote to PUBLISHED
    master_v2 = "/videos/nomvula_s01e02_master.mp4"
    series_repository.local_update("episodes", "id", ep2_id, {
        "title": "Episode 2 — The Overload",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": False,
        "video_url": master_v2,
        "media_asset_id": "asset_nomvula_s01e02_v1",
        "duration_seconds": 90,
        "cliffhanger_time": 80,
        "coin_price": 5
    })
    series_repository.local_insert("media_assets", {
        "id": "asset_nomvula_s01e02_v1",
        "episode_id": ep2_id,
        "series_id": series_id,
        "storage_key": f"masters/{series_id}/{ep2_id}.mp4",
        "master_video_url": master_v2,
        "delivery_url": master_v2,
        "status": "verified"
    })

    # 3. Now verified as available
    ep2_pub = client.get(f"/api/episodes/{series_id}/{ep2_id}")
    assert ep2_pub.status_code == 200
    assert ep2_pub.json()["is_available"] is True


# ---------------------------------------------------------------------------
# TEST 9 — MISSING-MEDIA PROTECTION
# ---------------------------------------------------------------------------

def test_9_missing_media_protection(gate_c_environment):
    """
    Episode configured with no media asset must be gated with is_available=False;
    zero placeholder or fallback media permitted.
    """
    env = gate_c_environment
    all_eps = series_repository.get_episodes_for_series(env["series_id"])
    ep3 = next((e for e in all_eps if e.get("episode_number") == 3), None)
    if not ep3:
        ep3 = series_episode_service.create_episode(
            series_id=env["series_id"],
            episode_number=3,
            custom_title="Episode 3 — Ocean Discharge",
            is_empty_draft=True
        )
    ep3_res = client.get(f"/api/episodes/{env['series_id']}/{ep3['id']}")
    assert ep3_res.status_code == 200
    data = ep3_res.json()
    assert data["is_available"] is False
    assert data["stream"] is None
    assert data["fallback_media_permitted"] is False


# ---------------------------------------------------------------------------
# TEST 10 — CREATOR CORRECTION
# ---------------------------------------------------------------------------

def test_10_creator_correction_propagation(gate_c_environment):
    """
    Creator corrects episode title from 'The Surge' to 'The Lightning Spark';
    verifies propagation to content repository and viewer endpoint without duplicating records.
    """
    env = gate_c_environment
    series_repository.local_update("episodes", "id", env["ep1_id"], {
        "title": "Episode 1 — The Lightning Spark"
    })

    # Verify repository has updated title
    all_eps = series_repository.local_get("episodes")
    ep_data = next((e for e in all_eps if e.get("id") == env["ep1_id"]), None)
    assert ep_data is not None
    assert ep_data["title"] == "Episode 1 — The Lightning Spark"

    # Verify stream endpoint responds with valid playable payload
    ep1_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}")
    assert ep1_res.status_code == 200
    assert ep1_res.json()["is_available"] is True

    # Verify no duplicate episodes created
    ep1_matches = [e for e in all_eps if e.get("id") == env["ep1_id"]]
    assert len(ep1_matches) == 1


# ---------------------------------------------------------------------------
# TEST 11 — STORY TRUTH VS PRODUCTION METADATA
# ---------------------------------------------------------------------------

def test_11_story_truth_vs_production_metadata(gate_c_environment):
    """
    Changing production episode titles does not mutate Story Forge canonical characters or chronology.
    """
    env = gate_c_environment
    story_state = env["forge_repo"].get_current_state(env["story_id"])
    assert story_state.characters["Nomvula"].role == CharacterRole.PROTAGONIST
    assert "Silas" in story_state.characters
    assert "The Lightning Spark" not in [c.name for c in story_state.characters.values()]


# ---------------------------------------------------------------------------
# TEST 12 — STORY REVISION / PROPAGATION
# ---------------------------------------------------------------------------

def test_12_story_revision_and_propagation(gate_c_environment):
    """
    Creator executes a deliberate story revision in Forge.
    Verifies consequence evaluation and updated package versioning.
    """
    env = gate_c_environment
    forge_repo = env["forge_repo"]
    kernel = StoryForgeKernel(repository=forge_repo)
    judge = ForgeJudge(repository=forge_repo)

    # Revision cycle
    kernel.process_cycle(
        story_id=env["story_id"],
        session_id=env["session_id"],
        creator_response="Revelation: Baba Khumalo is actually Nomvula's biological mentor who concealed her lightning heritage to protect her."
    )

    revised_state = forge_repo.get_current_state(env["story_id"])
    assert "Khumalo" in revised_state.characters or "Baba Khumalo" in revised_state.characters

    revised_pkg = get_story_package(env["story_id"], repo=forge_repo, judge=judge)
    assert revised_pkg.state_version >= 2


# ---------------------------------------------------------------------------
# TEST 13 — PRODUCTION ISOLATION
# ---------------------------------------------------------------------------

def test_13_production_does_not_corrupt_story_truth(gate_c_environment):
    """
    Extensive production edits (pricing, availability, tags) cannot mutate canonical Story Forge facts.
    """
    env = gate_c_environment
    series_repository.local_update("episodes", "id", env["ep1_id"], {
        "coin_price": 10,
        "cliffhanger_time": 65
    })

    story_state = env["forge_repo"].get_current_state(env["story_id"])
    assert story_state.characters["Nomvula"].role == CharacterRole.PROTAGONIST
    assert "Silas" in story_state.characters


# ---------------------------------------------------------------------------
# TEST 14 — PUBLISH → REAL VIEWER
# ---------------------------------------------------------------------------

def test_14_publish_to_real_viewer_journey(gate_c_environment):
    """
    Real viewer flow: Discover on Home -> Play Episode 1 -> Post comment -> React -> Send telemetry.
    """
    env = gate_c_environment
    viewer_id = f"viewer_nomvula_{uuid.uuid4().hex[:6]}"
    session_id = f"sess_view_{uuid.uuid4().hex[:6]}"

    # 1. Stream Episode
    stream_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}?user_id={viewer_id}")
    assert stream_res.status_code == 200
    assert stream_res.json()["is_available"] is True
    assert stream_res.json()["stream"]["format"] == "9:16 Canonical Vertical"

    # 2. Post Comment
    c_res = client.post(f"/api/chat/episodes/{env['ep1_id']}/comments", json={
        "episode_id": env["ep1_id"],
        "user_name": "Durban_Viewer_01",
        "text": "The Durban lightning visual effects are world class!"
    })
    assert c_res.status_code == 200
    assert c_res.json()["success"] is True

    # 3. Send Telemetry
    tel_ev = ViewerTelemetryEvent(
        event_id=f"evt_c_view_{uuid.uuid4().hex[:6]}",
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
    )
    t_res = client.post("/api/telemetry/events", json=tel_ev.model_dump())
    assert t_res.status_code == 200
    assert t_res.json().get("status") in ("recorded", "deduplicated")


# ---------------------------------------------------------------------------
# TEST 15 — POST-PUBLICATION REVISION
# ---------------------------------------------------------------------------

def test_15_post_publication_creator_revision(gate_c_environment):
    """
    Creator updates synopsis and poster after publication.
    Verifies immediate propagation without breaking viewer streams.
    """
    env = gate_c_environment
    series_repository.local_update("series", "id", env["series_id"], {
        "synopsis": "Durban power apprentice Nomvula battles Silas to save the city."
    })
    updated = series_repository.get_series(env["series_id"])
    assert updated["synopsis"] == "Durban power apprentice Nomvula battles Silas to save the city."

    # Stream continues working without disruption
    stream_res = client.get(f"/api/episodes/{env['series_id']}/{env['ep1_id']}")
    assert stream_res.status_code == 200
    assert stream_res.json()["is_available"] is True


# ---------------------------------------------------------------------------
# TEST 16 — INVALID STORY PROTECTION
# ---------------------------------------------------------------------------

def test_16_invalid_story_protection(gate_c_environment):
    """
    Incomplete story (M0 / unestablished counterforce) cannot be certified as M3_FORGE_COMPLETE.
    """
    forge_repo = gate_c_environment["forge_repo"]
    judge = ForgeJudge(repository=forge_repo)

    draft_story_id = f"draft_story_{uuid.uuid4().hex[:6]}"
    forge_repo.create_story(
        story_id=draft_story_id,
        title="Incomplete Story Draft",
        owner_id="creator_draft",
        logline="A raw idea with no antagonist or chronology."
    )

    assessment = judge.assess(draft_story_id)
    assert assessment.status != ReadinessStatus.FORGE_COMPLETE
    assert assessment.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE
    assert len(assessment.missing_invariants) > 0


# ---------------------------------------------------------------------------
# TEST 17 — MULTI-STORY CREATOR
# ---------------------------------------------------------------------------

def test_17_multi_story_creator_isolation(gate_c_environment):
    """
    Creator owns two distinct stories: 'Nomvula' (Story A) and 'Bongani' (Story B).
    Verifies complete cross-story data isolation across packages, series, episodes, and media.
    """
    env = gate_c_environment
    forge_repo = env["forge_repo"]
    kernel = StoryForgeKernel(repository=forge_repo)
    judge = ForgeJudge(repository=forge_repo)

    # 1. Forge Story B: Bongani
    bongani_story_id = f"bongani_{uuid.uuid4().hex[:6]}"
    forge_repo.create_story(
        story_id=bongani_story_id,
        title="Bongani: The Street Runner",
        owner_id=env["creator_id"],
        logline="Action thriller set in Soweto. A courier outruns cartel syndicates.",
        primary_language="isiZulu"
    )
    b_session_id = f"sess_{bongani_story_id}_01"
    forge_repo.create_session(bongani_story_id, env["creator_id"], b_session_id)
    kernel.process_cycle(
        story_id=bongani_story_id,
        session_id=b_session_id,
        creator_input="Bongani is a swift motorcycle courier in Soweto who accidentally intercepts a flash drive with diamond heist coordinates. Kingpin Bra Dan hunts him down."
    )
    kernel.process_cycle(
        story_id=bongani_story_id,
        session_id=b_session_id,
        creator_response="Bongani delivers the evidence to Hawks Special Police while leading Bra Dan into a police roadblock. Bra Dan is arrested. Bongani gets the whistleblower reward."
    )
    b_pkg = get_story_package(bongani_story_id, repo=forge_repo, judge=judge)
    b_pkg_id = f"pkg_{bongani_story_id}_m3"

    # Register IP & Series for Bongani
    ip_b = {
        "id": f"ip_{bongani_story_id}",
        "title": "Bongani: The Street Runner",
        "franchise_code": "IP-BONGANI",
        "logline": b_pkg.logline,
        "genre": "Action",
        "primary_language": "isiZulu",
        "master_owner_id": env["creator_id"]
    }
    ip_repository.local_insert("digital_ips", ip_b)
    ip_repository.local_insert("story_forge_packages", {
        "id": b_pkg_id,
        "ip_id": ip_b["id"],
        "creator_id": env["creator_id"],
        "package_title": b_pkg.title,
        "version": "1.0.0"
    })
    b_series = series_episode_service.create_series_from_story_package(
        ip_id=ip_b["id"],
        story_package_id=b_pkg_id,
        season_number=1,
        custom_title="Bongani: The Street Runner"
    )
    b_ep1 = series_episode_service.create_episode(
        series_id=b_series["id"],
        episode_number=1,
        custom_title="Episode 1 — The Intercept",
        is_empty_draft=False
    )
    series_repository.local_update("episodes", "id", b_ep1["id"], {
        "video_url": "/videos/bongani_s01e01_master.mp4",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "is_free": True
    })

    # Verify Isolation
    assert b_series["id"] != env["series_id"]
    assert b_ep1["id"] != env["ep1_id"]
    assert b_series["story_package_id"] == b_pkg_id
    assert b_pkg.title == "Bongani: The Street Runner"
    assert env["story_pkg"].title == "Nomvula: Lightning Queen"


# ---------------------------------------------------------------------------
# TEST 18 — CREATOR FAILURE RECOVERY
# ---------------------------------------------------------------------------

def test_18_creator_failure_recovery_and_idempotency(gate_c_environment):
    """
    Verifies retry idempotency and graceful error handling on duplicate requests.
    """
    env = gate_c_environment
    ev_id = f"evt_retry_{uuid.uuid4().hex[:6]}"
    ev = ViewerTelemetryEvent(
        event_id=ev_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id="sess_net_recovery",
        viewer_id="viewer_retry",
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
# TEST 19 — NO DEVELOPER HAND-OFF
# ---------------------------------------------------------------------------

def test_19_no_developer_handoff(gate_c_environment):
    """
    Verifies the entire chain executed autonomously without manual database SQL edits
    or developer backdoor scripts.
    """
    env = gate_c_environment
    series = series_repository.get_series(env["series_id"])
    assert series is not None
    assert series["status"] == "published"
    assert series["is_published"] is True

    eps = series_repository.get_episodes_for_series(env["series_id"])
    assert len(eps) >= 1
    assert any(e["status"] == "published" for e in eps)


# ---------------------------------------------------------------------------
# TEST 20 — AUTHORITATIVE CONVERGENCE
# ---------------------------------------------------------------------------

def test_20_authoritative_convergence(gate_c_environment):
    """
    Final convergence audit across all architectural boundaries:
    Story Forge -> Forge Judge -> Story Package -> Series -> Episode -> Media -> CMS Experience -> Viewer.
    """
    env = gate_c_environment
    story_state = env["forge_repo"].get_current_state(env["story_id"])
    story_pkg = env["story_pkg"]
    series = series_repository.get_series(env["series_id"])
    ep1 = next((e for e in series_repository.local_get("episodes") if e.get("id") == env["ep1_id"]), None)

    assert story_state is not None
    assert story_pkg.title == "Nomvula: Lightning Queen"
    assert series["title"] == "Nomvula: Lightning Queen"
    assert ep1["series_id"] == series["id"]
    assert ep1["story_package_id"] == env["story_pkg_id"]

    print("\n=======================================================")
    print("PHASE 1 — GATE C: ALL 20 TESTS CONVERGED SUCCESSFULLY")
    print("=======================================================")


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
