"""
Welele Media™ — Staging Persistent Catalogue DAL & Catalog Integration Test Suite
Proves that the Welele Experience can be powered by persistent staging Supabase
PostgreSQL data while maintaining 100% backward compatibility with static artwork,
video assets, cliffhanger metadata, and local fallback offline development.
"""

import os
import uuid
from unittest.mock import MagicMock, patch
import pytest

from repositories.series_repository import (
    SeriesRepository,
    series_repository,
    to_uuid,
    SERIES_UUID_TO_SLUG,
    EPISODE_UUID_TO_SLUG,
    KNOWN_SERIES_SLUGS
)
from services.experience_engine import ExperienceEngine
from services.merchandising_policy_service import merchandising_policy_service


# -----------------------------------------------------------------------------
# 1. Deterministic UUID & Slug Contract Verification
# -----------------------------------------------------------------------------

def test_deterministic_uuid_mapping_matches_postgresql_uuid_generate_v5():
    """
    Verifies that Python to_uuid() produces the exact RFC 4122 DNS namespace UUID5
    as PostgreSQL uuid_generate_v5(uuid_ns_dns(), 'welele.media.<name>').
    """
    blood_ties_uuid = to_uuid("story_blood_ties")
    assert blood_ties_uuid == "c3e9302a-9809-51c2-b219-4e2a3079787f"
    assert SERIES_UUID_TO_SLUG[blood_ties_uuid] == "story_blood_ties"

    # Idempotent on already valid UUIDs
    test_guid = str(uuid.uuid4())
    assert to_uuid(test_guid) == test_guid


def test_known_catalog_slugs_coverage():
    """All 14 canonical series slugs map bidirectionally to deterministic UUIDs."""
    assert len(KNOWN_SERIES_SLUGS) == 14
    for slug in KNOWN_SERIES_SLUGS:
        uid = to_uuid(slug)
        assert SERIES_UUID_TO_SLUG[uid] == slug


# -----------------------------------------------------------------------------
# 2. SeriesRepository Offline / Local Fallback Guarantee
# -----------------------------------------------------------------------------

def test_series_repository_offline_local_feed():
    """When offline (is_live=False), list_feed hydrates from local store cleanly."""
    repo = SeriesRepository()
    feed = repo.list_feed()
    assert len(feed) >= 11
    
    first = feed[0]
    assert first["id"] == "story_blood_ties"
    assert first["cover_image"].startswith("/banners/") or first["cover_image"].startswith("/posters/")
    assert first["vertical_poster"].startswith("/posters/")
    assert len(first["episodes"]) > 0
    
    ep1 = first["episodes"][0]
    assert ep1["video_url"].startswith("/videos/")
    assert ep1["cliffhanger_time"] > 0
    assert ep1["cliffhanger_hook"] != ""


def test_series_detail_lookup_by_slug_and_uuid():
    """get_series_detail resolves by slug, raw id, or deterministic UUID."""
    repo = SeriesRepository()
    # By slug
    s_by_slug = repo.get_series_detail("story_blood_ties")
    assert s_by_slug is not None
    assert s_by_slug["title"] == "Blood Ties"

    # By deterministic UUID
    uid = to_uuid("story_blood_ties")
    s_by_uuid = repo.get_series_detail(uid)
    assert s_by_uuid is not None
    assert s_by_uuid["title"] == "Blood Ties"


# -----------------------------------------------------------------------------
# 3. Live Supabase Persistent Catalog Simulation
# -----------------------------------------------------------------------------

def test_series_repository_live_supabase_hydration():
    """
    Simulates live Supabase connection with PostgreSQL UUID rows
    and verifies that SeriesRepository hydrates records, attaches slugs,
    preserves static media paths, and links episodes seamlessly.
    """
    repo = SeriesRepository()

    blood_ties_uuid = to_uuid("story_blood_ties")
    ep1_uuid = to_uuid("ep_bt_1")
    media1_uuid = to_uuid("media_ep_bt_1")

    mock_series_data = [
        {
            "id": blood_ties_uuid,
            "ip_id": to_uuid("ip_blood_ties"),
            "season_number": 1,
            "title": "Blood Ties (Persistent Supabase)",
            "tagline": "Two powerful families tied by blood.",
            "synopsis": "Dynasty showdown in Sandton.",
            "cover_image": "/banners/blood_ties_banner.jpg",
            "vertical_poster": "/posters/blood_ties.jpg",
            "genre": "Drama • Family",
            "rating": 4.98,
            "total_episodes": 1,
            "free_episodes": 1,
            "coin_price_per_episode": 5,
            "is_published": True,
            "available_languages": ["isiZulu", "English"],
            "tags": ["#BloodTies"]
        }
    ]

    mock_episodes_data = [
        {
            "id": ep1_uuid,
            "series_id": blood_ties_uuid,
            "episode_number": 1,
            "title": "The Golden Will",
            "synopsis": "The unsealed court document triggers panic.",
            "duration_seconds": 68,
            "is_free": True,
            "coin_price": 0,
            "cliffhanger_time_seconds": 58,
            "cliffhanger_hook": "Who authorized her DNA test?",
            "status": "published"
        }
    ]

    mock_media_data = [
        {
            "id": media1_uuid,
            "episode_id": ep1_uuid,
            "storage_key": "masters/story_blood_ties/ep_bt_1.mp4",
            "master_video_url": "/videos/sample_drama.mp4",
            "hls_master_manifest_url": "https://cdn.welele.media/hls/story_blood_ties/ep_bt_1/master.m3u8",
            "thumbnail_url": "/posters/blood_ties.jpg",
            "duration_seconds": 68,
            "transcoding_status": "READY",
            "renditions_json": {"1080p": "https://cdn.welele.media/hls/story_blood_ties/ep_bt_1/1080p.m3u8"}
        }
    ]

    # Mock the Supabase client query builder
    mock_supabase = MagicMock()
    
    def mock_table(table_name):
        builder = MagicMock()
        select_builder = MagicMock()
        if table_name == "series":
            select_builder.execute.return_value = MagicMock(data=mock_series_data)
        elif table_name == "episodes":
            select_builder.execute.return_value = MagicMock(data=mock_episodes_data)
        elif table_name == "media_assets":
            select_builder.execute.return_value = MagicMock(data=mock_media_data)
        builder.select.return_value = select_builder
        return builder

    mock_supabase.table.side_effect = mock_table

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", side_effect=mock_table):
            live_feed = repo.list_feed()

            assert len(live_feed) == 1
            s = live_feed[0]
            assert s["id"] == blood_ties_uuid
            assert s["slug"] == "story_blood_ties"
            assert s["title"] == "Blood Ties (Persistent Supabase)"
            assert s["cover_image"] == "/banners/blood_ties_banner.jpg"
            assert s["vertical_poster"] == "/posters/blood_ties.jpg"
            assert len(s["episodes"]) == 1

            ep = s["episodes"][0]
            assert ep["id"] == ep1_uuid
            assert ep["slug"] == "ep_bt_1"
            assert ep["video_url"] == "/videos/sample_drama.mp4"
            assert ep["cliffhanger_time"] == 58
            assert ep["cliffhanger_hook"] == "Who authorized her DNA test?"

            # Detail resolution works seamlessly with either slug or UUID
            assert repo.get_series_detail("story_blood_ties")["title"] == "Blood Ties (Persistent Supabase)"
            assert repo.get_series_detail(blood_ties_uuid)["title"] == "Blood Ties (Persistent Supabase)"


# -----------------------------------------------------------------------------
# 4. ExperienceEngine Manifest Hydration with Persistent Data
# -----------------------------------------------------------------------------

def test_experience_engine_resolves_both_uuid_and_slug_manifests():
    """
    Proves that ExperienceEngine compiles layouts correctly whether slot items
    reference UUIDs (from persistent Supabase seed) or slugs (from default layout).
    """
    manifest = ExperienceEngine.resolve_manifest("home")
    assert manifest["page_id"] == "home"
    assert len(manifest["sections"]) > 0

    hero_sec = next(s for s in manifest["sections"] if s["type"] == "HERO_CAROUSEL")
    assert len(hero_sec["items"]) > 0

    for item in hero_sec["items"]:
        assert "story" in item, f"Slot {item.get('slot_id')} failed catalog hydration"
        story = item["story"]
        assert "cover_image" in story
        assert "vertical_poster" in story
        assert len(story.get("episodes", [])) > 0
        assert story["episodes"][0]["video_url"].startswith("/videos/")


# -----------------------------------------------------------------------------
# 5. Degraded-State Signaling & Error Behavior (Instruction 8)
# -----------------------------------------------------------------------------

def test_staging_database_read_failure_triggers_observable_degraded_state():
    """
    Instruction 8: Test what happens when a live database read fails.
    Ensure failure is logged and detectable. Do not silently serve in-memory mock data
    in live staging without a clearly observable degraded-state signal.
    """
    from fastapi.testclient import TestClient
    from main import app
    from config import settings

    repo = SeriesRepository()

    # Configure staging environment
    with patch.object(settings, "ENVIRONMENT", "staging"):
        with patch.object(SeriesRepository, "is_live", True):
            # Simulate database raising an exception on query
            mock_table = MagicMock()
            mock_table.select.side_effect = RuntimeError("Supabase connection timeout / read error")

            with patch.object(repo, "get_table", return_value=mock_table):
                # Trigger a read that will fail
                feed = repo.list_feed()

                # Verify failure is detected and logged
                assert repo.is_degraded is True
                assert "Supabase connection timeout" in repo.degraded_reason
                assert repo.catalog_source == "local_fallback (DEGRADED)"
                
                # Verify that fallback items are returned so app doesn't hard-crash,
                # but degraded state is fully observable
                assert len(feed) > 0

    # Test API HTTP response headers and /health status under degraded state
    with patch("main.series_repository", repo):
        client = TestClient(app)

        # 1. Probe /health
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "degraded"
        assert health_data["database"] == "degraded"
        assert health_data["catalog_source"] == "local_fallback (DEGRADED)"
        assert "degraded_reason" in health_data

        # 2. Probe API endpoint and verify HTTP response headers
        stories_resp = client.get("/api/stories/feed")
        assert stories_resp.status_code == 200
        assert stories_resp.headers.get("X-Welele-Degraded-State") == "1"
        assert stories_resp.headers.get("X-Welele-Catalog-Source") == "local_fallback (DEGRADED)"


def test_development_database_fallback_retains_clean_offline_behavior():
    """
    Instruction 8: Retain intended offline/local development behaviour.
    In local development, fallback is expected and should NOT trigger a degraded alarm.
    """
    from fastapi.testclient import TestClient
    from main import app
    from config import settings

    repo = SeriesRepository()

    with patch.object(settings, "ENVIRONMENT", "development"):
        with patch.object(SeriesRepository, "is_live", False):
            feed = repo.list_feed()

            assert repo.is_degraded is False
            assert repo.degraded_reason is None
            assert repo.catalog_source == "offline_fixtures"
            assert len(feed) > 0

    with patch("main.series_repository", repo):
        client = TestClient(app)
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["status"] == "healthy"
        assert health_data["database"] == "offline_fixtures"
        assert health_data["catalog_source"] == "offline_fixtures"
        assert "degraded_reason" not in health_data

