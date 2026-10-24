"""
Welele Media™ — Phase 6J-2R-C Convergence Repair Automated Regression Test Suite

Governing Invariants:
1. PostgreSQL is the sole authoritative persisted catalogue in staging/production.
2. Dual-write asymmetry eliminated: PostgreSQL persistence must occur before local state update.
3. Failure invariant: If PostgreSQL persistence fails, local canonical catalogue MUST remain unchanged.
4. Read asymmetry eliminated: In live mode, Creator/WEE and Public Feed must NEVER resurrect
   or present unpersisted local records as authoritative catalogue data.
5. Degraded state explicit: Public feed database failures report degraded mode and do not silently
   substitute an arbitrary local catalogue.
6. Offline compatibility: Legitimate development and unit test local fixtures continue to function when is_live is False.
"""

import uuid
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from repositories.series_repository import SeriesRepository, to_uuid
from repositories.forge_configuration_repository import ForgeConfigurationRepository
from config import settings

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. Section 8: CREATE TEST — REQUIRED
# -----------------------------------------------------------------------------

def test_create_series_db_failure_leaves_local_store_unchanged():
    """
    Given: No canonical local series with ID X
    When:  create_series(X) is executed and PostgreSQL persistence is forced to fail
    Then:  Operation fails (raises RuntimeError)
    And:   Local canonical series X does NOT exist
    """
    repo = SeriesRepository()
    test_id = str(uuid.uuid4())
    series_payload = {
        "id": test_id,
        "title": "Unpersisted Ghost Story",
        "tagline": "Should never be persisted",
        "synopsis": "A story that fails PostgreSQL persistence",
        "genre": "Drama",
        "creator_id": "creator_zola"
    }

    # Verify ID does not exist initially in local store
    initial_local = repo.local_get("series") or []
    assert not any(s.get("id") == test_id or to_uuid(str(s.get("id", ""))) == to_uuid(test_id) for s in initial_local)

    # Mock failing PostgreSQL table upsert
    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_upsert.execute.side_effect = RuntimeError("PostgreSQL connection timeout: write aborted")
    mock_table.upsert.return_value = mock_upsert

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError) as exc_info:
                repo.create_series(series_payload)
            
            assert "Database write failure" in str(exc_info.value)

    # Invariant assertion: Local store MUST remain unchanged
    after_local = repo.local_get("series") or []
    persisted_in_local = any(s.get("id") == test_id or to_uuid(str(s.get("id", ""))) == to_uuid(test_id) for s in after_local)
    assert not persisted_in_local, "FAILURE INVARIANT VIOLATED: Local series was mutated despite PostgreSQL persistence failure!"


# -----------------------------------------------------------------------------
# 2. Section 9: UPDATE TEST — REQUIRED
# -----------------------------------------------------------------------------

def test_update_series_db_failure_leaves_local_store_unchanged():
    """
    Given: Existing series X with local title = "Original" and PostgreSQL title = "Original"
    When:  update_series(X, title="Changed") and PostgreSQL update is forced to fail
    Then:  Operation fails (raises RuntimeError)
    And:   Local title remains "Original"
    """
    repo = SeriesRepository()
    test_id = str(uuid.uuid4())
    target_uuid = to_uuid(test_id)

    # Seed baseline series in local store
    original_record = {
        "id": test_id,
        "title": "Original Title",
        "tagline": "Original Tagline",
        "synopsis": "Original Synopsis",
        "genre": "Drama",
        "creator_id": "creator_zola",
        "is_published": True
    }
    repo.local_insert("series", original_record)

    # Verify baseline in local store
    baseline_match = next((s for s in repo.local_get("series") if s.get("id") == test_id), None)
    assert baseline_match is not None
    assert baseline_match["title"] == "Original Title"

    # Mock failing PostgreSQL table update
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq = MagicMock()
    mock_eq.execute.side_effect = RuntimeError("PostgreSQL foreign key violation: update aborted")
    mock_update.eq.return_value = mock_eq
    mock_table.update.return_value = mock_update

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError) as exc_info:
                repo.update_series(test_id, {"title": "Changed Title"})

            assert "Database write failure" in str(exc_info.value)

    # Invariant assertion: Local title MUST remain "Original Title"
    after_local = repo.local_get("series") or []
    after_match = next((s for s in after_local if s.get("id") == test_id), None)
    assert after_match is not None
    assert after_match["title"] == "Original Title", f"FAILURE INVARIANT VIOLATED: Local title mutated to '{after_match['title']}' despite PostgreSQL failure!"


# -----------------------------------------------------------------------------
# 3. Section 10: DELETE TEST — REQUIRED
# -----------------------------------------------------------------------------

def test_delete_series_db_failure_leaves_local_store_unchanged():
    """
    Given: Existing canonical series X
    When:  delete_series(X) and PostgreSQL deletion fails
    Then:  Operation fails (raises RuntimeError)
    And:   Local canonical representation is not silently deleted
    """
    repo = SeriesRepository()
    test_id = str(uuid.uuid4())
    target_uuid = to_uuid(test_id)

    # Seed baseline series in local store
    series_record = {
        "id": test_id,
        "title": "Preserved Series Before Delete",
        "genre": "Drama",
        "creator_id": "creator_zola"
    }
    repo.local_insert("series", series_record)

    # Mock failing PostgreSQL table delete
    mock_table = MagicMock()
    mock_delete = MagicMock()
    mock_eq = MagicMock()
    mock_eq.execute.side_effect = RuntimeError("PostgreSQL deadlock: delete aborted")
    mock_delete.eq.return_value = mock_eq
    mock_table.delete.return_value = mock_delete

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError) as exc_info:
                repo.delete_series(test_id)

            assert "Database write failure" in str(exc_info.value)

    # Invariant assertion: Local representation MUST NOT be deleted
    after_local = repo.local_get("series") or []
    persists = any(s.get("id") == test_id for s in after_local)
    assert persists, "FAILURE INVARIANT VIOLATED: Local series was silently deleted despite PostgreSQL failure!"


# -----------------------------------------------------------------------------
# 4. Section 12: CREATOR / WEE READ AUTHORITY TEST — REQUIRED
# -----------------------------------------------------------------------------

def test_creator_series_does_not_resurrect_local_only_canonical_series():
    """
    Given: Local canonical series X exists, PostgreSQL does NOT contain X
    When:  Creator series catalogue is requested
    Then:  X is NOT returned as an authoritative persisted series
    """
    repo = SeriesRepository()
    local_only_id = str(uuid.uuid4())
    local_only_title = "Local Ghost Story Unpersisted In Postgres"

    # Inject local-only record directly into local in-memory store
    repo.local_insert("series", {
        "id": local_only_id,
        "title": local_only_title,
        "creator_id": "creator_zola",
        "genre": "Drama",
        "is_published": True
    })

    # Mock PostgreSQL returning only canonical series (which does NOT include local_only_id)
    canonical_pg_series = [{
        "id": to_uuid("story_blood_ties"),
        "title": "Blood Ties",
        "creator_id": "creator_zola",
        "is_published": True,
        "genre": "Drama",
        "rating": 5.0,
        "total_episodes": 10
    }]
    mock_table = MagicMock()
    select_builder = MagicMock()
    select_builder.execute.return_value = MagicMock(data=canonical_pg_series)
    mock_table.select.return_value = select_builder

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "_fetch_live_catalog", return_value=(canonical_pg_series, [], [])):
            with patch.object(repo, "get_table", return_value=mock_table):
                # 1. Test get_creator_series()
                roster = repo.get_creator_series(creator_id="creator_zola")
                roster_ids = {str(s.get("id")) for s in roster}
                roster_titles = {s.get("title") for s in roster}

                assert local_only_id not in roster_ids, "READ ASYMMETRY: Local-only series resurrected in creator roster!"
                assert local_only_title not in roster_titles

                # 2. Test get_creator_series_detail()
                # Simulate direct query for local_only_id in PostgreSQL returning empty
                empty_select = MagicMock()
                empty_select.execute.return_value = MagicMock(data=[])
                empty_or_builder = MagicMock()
                empty_or_builder.execute.return_value = MagicMock(data=[])
                mock_table.select.return_value.or_.return_value = empty_or_builder

                detail = repo.get_creator_series_detail(local_only_id)
                assert detail is None, "READ ASYMMETRY: get_creator_series_detail resurrected local-only series!"


# -----------------------------------------------------------------------------
# 5. Section 14: PUBLIC FEED AUTHORITY TEST — REQUIRED
# -----------------------------------------------------------------------------

def test_public_feed_does_not_silently_resurrect_local_canonical_series_on_db_failure():
    """
    Given: PostgreSQL catalogue is unavailable / fails, local catalogue contains series X
    When:  Public feed is requested
    Then:  X is NOT silently presented as authoritative catalogue data
    """
    repo = SeriesRepository()
    local_id = str(uuid.uuid4())
    local_title = "Local Ghost Series In Local Store"

    # Inject record in local store
    repo.local_insert("series", {
        "id": local_id,
        "title": local_title,
        "is_published": True,
        "genre": "Drama"
    })

    # Simulate live mode with PostgreSQL connection failure
    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "_fetch_live_catalog", return_value=None):
            feed = repo.list_feed()
            
            # The feed MUST be empty, not populated with local storage fallback
            assert len(feed) == 0, f"PUBLIC AUTHORITY VIOLATED: Live feed fell back to local storage and returned {len(feed)} items!"
            assert not any(s.get("id") == local_id for s in feed)
            assert not any(s.get("title") == local_title for s in feed)
            
            # Detail lookup for local item must also return None in live mode
            detail = repo.get_series_detail(local_id)
            assert detail is None, "PUBLIC AUTHORITY VIOLATED: get_series_detail resurrected local item during DB failure!"

            single = repo.get_series(local_id)
            assert single is None, "PUBLIC AUTHORITY VIOLATED: get_series resurrected local item during DB failure!"


def test_public_feed_endpoint_signals_degraded_state_without_local_catalog_substitution():
    """
    Verifies that the /stories/feed and /series/feed endpoints explicitly signal degraded
    state when PostgreSQL fails, without substituting unpersisted local records.
    """
    local_id = str(uuid.uuid4())
    repo = SeriesRepository()
    repo.local_insert("series", {
        "id": local_id,
        "title": "Secret Local Unpersisted Story",
        "is_published": True,
        "genre": "Drama"
    })

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(SeriesRepository, "is_degraded", True):
            with patch.object(SeriesRepository, "degraded_reason", "Database read exception: connection lost"):
                with patch("repositories.series_repository.series_repository.list_feed", return_value=[]):
                    # Test /stories/feed
                    resp_stories = client.get("/api/v1/stories/feed")
                    assert resp_stories.status_code == 200
                    data_stories = resp_stories.json()
                    assert data_stories["is_degraded"] is True
                    assert "connection lost" in data_stories["degraded_reason"]
                    assert len(data_stories["stories"]) == 0
                    assert not any(s.get("id") == local_id for s in data_stories["stories"])
                    assert data_stories["catalog_source"] == "postgresql_unavailable (degraded - no catalogue substituted)"
                    assert "local_fallback" not in data_stories["catalog_source"]

                    # Test /series/feed
                    resp_series = client.get("/api/v1/series/feed")
                    assert resp_series.status_code == 200
                    data_series = resp_series.json()
                    assert data_series["is_degraded"] is True
                    assert len(data_series["series"]) == 0
                    assert not any(s.get("id") == local_id for s in data_series["series"])
                    assert data_series["catalog_source"] == "postgresql_unavailable (degraded - no catalogue substituted)"
                    assert "local_fallback" not in data_series["catalog_source"]


# -----------------------------------------------------------------------------
# 6. Additional Persistence & Lifecycle Invariants
# -----------------------------------------------------------------------------

def test_episode_draft_creation_db_failure_leaves_local_episodes_unchanged():
    """Verifies that an episode draft is not inserted into local store if PostgreSQL upsert fails."""
    repo = SeriesRepository()
    ep_id = f"ep_{uuid.uuid4().hex[:8]}"
    series_id = str(uuid.uuid4())

    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_upsert.execute.side_effect = RuntimeError("PostgreSQL schema validation failed")
    mock_table.upsert.return_value = mock_upsert

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError):
                repo.create_episode_draft(
                    series_id=series_id,
                    story_package_id=None,
                    payload={"id": ep_id, "title": "Failed Episode Draft", "episode_number": 1}
                )

    local_eps = repo.local_get("episodes") or []
    assert not any(e.get("id") == ep_id for e in local_eps), "Local episodes mutated despite PostgreSQL failure!"


def test_media_asset_attachment_db_failure_leaves_local_store_unchanged():
    """Verifies that a media asset is not attached locally if PostgreSQL upsert fails."""
    repo = SeriesRepository()
    ep_id = str(uuid.uuid4())
    media_id = f"media_{ep_id}"

    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_upsert.execute.side_effect = RuntimeError("PostgreSQL storage quota exceeded")
    mock_table.upsert.return_value = mock_upsert

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError):
                repo.attach_media_asset(
                    episode_id=ep_id,
                    storage_key="test/key.mp4",
                    master_url="https://cdn.welele.media/test.mp4"
                )

    local_media = repo.local_get("media_assets") or []
    assert not any(m.get("id") == media_id or m.get("episode_id") == ep_id for m in local_media)


def test_artwork_update_db_failure_leaves_local_artwork_unchanged():
    """Verifies that series artwork is not updated locally if PostgreSQL update fails."""
    repo = SeriesRepository()
    test_id = str(uuid.uuid4())

    original_poster = "https://cdn.welele.media/original_poster.jpg"
    repo.local_insert("series", {
        "id": test_id,
        "title": "Artwork Test Series",
        "vertical_poster": original_poster,
        "cover_image": "https://cdn.welele.media/original_cover.jpg"
    })

    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq = MagicMock()
    mock_eq.execute.side_effect = RuntimeError("PostgreSQL update failed: connection reset")
    mock_update.eq.return_value = mock_eq
    mock_table.update.return_value = mock_update

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            with pytest.raises(RuntimeError):
                repo.update_series_artwork(
                    series_id=test_id,
                    vertical_poster="https://cdn.welele.media/new_poster.jpg"
                )

    after_s = next(s for s in repo.local_get("series") if s.get("id") == test_id)
    assert after_s["vertical_poster"] == original_poster, "Local vertical_poster mutated despite PostgreSQL update failure!"


# -----------------------------------------------------------------------------
# 7. Compatibility Guarantee: Offline / Unit Test Operation
# -----------------------------------------------------------------------------

def test_offline_unit_testing_local_store_still_functions():
    """
    Proves that legitimate offline / development / test flows remain 100% operational
    when is_live is False without attempting any PostgreSQL network calls.
    """
    repo = SeriesRepository()
    test_id = str(uuid.uuid4())

    with patch.object(SeriesRepository, "is_live", False):
        # 1. Create series in offline mode
        created = repo.create_series({
            "id": test_id,
            "title": "Offline Unit Test Story",
            "genre": "Drama",
            "creator_id": "creator_zola"
        })
        assert created["id"] == test_id

        # 2. Verify it exists in local store and offline feed
        local_series = repo.local_get("series")
        assert any(s.get("id") == test_id for s in local_series)

        # 3. Update series in offline mode
        updated = repo.update_series(test_id, {"title": "Updated Offline Title"})
        assert updated["title"] == "Updated Offline Title"
        local_updated = next(s for s in repo.local_get("series") if s.get("id") == test_id)
        assert local_updated["title"] == "Updated Offline Title"

        # 4. Detail lookups resolve in offline mode
        detail = repo.get_series_detail(test_id)
        assert detail is not None
        assert detail["title"] == "Updated Offline Title"

        # 5. Delete series in offline mode
        del_res = repo.delete_series(test_id)
        assert del_res["deleted"] is True
        assert not any(s.get("id") == test_id for s in repo.local_get("series"))


# -----------------------------------------------------------------------------
# 8. Empty Catalogue & Reinitialization Lifecycle Invariants
# -----------------------------------------------------------------------------

def test_empty_postgresql_catalog_is_healthy_and_authoritative_not_degraded():
    """
    Invariant: An empty PostgreSQL catalogue (0 rows) is a healthy, authoritative state.
    It MUST NOT be flagged as degraded, and must return an empty list.
    """
    repo = SeriesRepository()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_select.execute.return_value = MagicMock(data=[])
    mock_table.select.return_value = mock_select

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(repo, "get_table", return_value=mock_table):
            live_data = repo._fetch_live_catalog()
            assert live_data == ([], [], []), "Expected healthy empty catalogue tuple"
            assert repo.is_degraded is False, "Empty catalogue must NOT be marked as degraded!"
            assert repo.degraded_reason is None

            feed = repo.list_feed()
            assert feed == [], "Empty catalogue must return empty feed"
            assert repo.is_degraded is False

    # Also test API endpoint returns healthy empty feed without degraded flag
    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(SeriesRepository, "is_degraded", False):
            with patch.object(SeriesRepository, "degraded_reason", None):
                with patch("repositories.series_repository.series_repository.list_feed", return_value=[]):
                    resp = client.get("/api/v1/stories/feed")
                    assert resp.status_code == 200
                    data = resp.json()
                    assert data["is_degraded"] is False
                    assert data["degraded_reason"] is None
                    assert data["stories"] == []
                    assert data["total"] == 0
                    assert "postgres" in data["catalog_source"]


def test_process_reinitialization_lifecycle_invariant():
    """
    Invariant: On worker startup, restart, or reinitialization, the repository MUST
    bind directly to authoritative PostgreSQL state and MUST NOT resurrect stale in-memory
    or local-only ghost data from prior process lifetimes.
    """
    # 1. Simulate prior process state with an unpersisted ghost record in local store
    prior_repo = SeriesRepository()
    ghost_id = str(uuid.uuid4())
    prior_repo.local_insert("series", {
        "id": ghost_id,
        "title": "Ghost From Previous Lifetime",
        "genre": "Supernatural",
        "creator_id": "creator_zola"
    })

    # 2. Simulate process restart / reinitialization: a fresh SeriesRepository is instantiated
    fresh_repo = SeriesRepository()
    assert fresh_repo.is_degraded is False
    assert fresh_repo.degraded_reason is None

    # 3. Simulate authoritative PostgreSQL holding 1 canonical story (different from ghost)
    canonical_id = str(uuid.uuid4())
    canonical_title = "Authoritative Postgres Story"
    pg_canonical_data = [{
        "id": canonical_id,
        "title": canonical_title,
        "slug": "authoritative-story",
        "genre": "Drama",
        "creator_id": "creator_zola",
        "is_published": True,
        "rating": 5.0,
        "total_episodes": 1
    }]

    with patch.object(SeriesRepository, "is_live", True):
        with patch.object(fresh_repo, "_fetch_live_catalog", return_value=(pg_canonical_data, [], [])):
            # Feed must return authoritative PostgreSQL item exclusively
            live_feed = fresh_repo.list_feed()
            assert len(live_feed) == 1
            assert live_feed[0]["id"] == canonical_id
            assert live_feed[0]["title"] == canonical_title

            # Stale ghost record MUST NOT be present in live feed
            feed_ids = {s.get("id") for s in live_feed}
            assert ghost_id not in feed_ids, "LIFECYCLE VIOLATION: Ghost record resurrected after reinitialization!"

            # Creator roster must also query PostgreSQL exclusively
            creator_roster = fresh_repo.get_creator_series("creator_zola")
            roster_ids = {s.get("id") for s in creator_roster}
            assert ghost_id not in roster_ids, "LIFECYCLE VIOLATION: Ghost record resurrected in creator roster!"
            assert canonical_id in roster_ids



# -----------------------------------------------------------------------------
# 6J-2R-C STARTUP REGRESSIONS — LIVE ENVIRONMENTS MUST NOT SEED FIXTURES
# -----------------------------------------------------------------------------

def test_live_series_repository_constructor_does_not_seed_fixture_catalogue():
    """A cold local cache must not be mistaken for an empty canonical PostgreSQL catalogue."""
    with patch.object(settings, "IS_PRODUCTION_OR_STAGING", True):
        with patch.object(SeriesRepository, "seed_if_missing") as seed:
            SeriesRepository()
            seed.assert_not_called()


def test_live_series_fixture_seed_entrypoint_is_a_noop():
    """Explicit fixture seed helpers must not insert synthetic catalogue rows into live PostgreSQL."""
    with patch.object(settings, "IS_PRODUCTION_OR_STAGING", True):
        repo = SeriesRepository()
        with patch.object(repo, "local_insert") as insert:
            repo.seed_if_missing()
            insert.assert_not_called()


def test_live_forge_repository_does_not_seed_missing_registry_at_startup():
    """A missing Forge schema must not trigger an implicit startup write."""
    with patch.object(settings, "IS_PRODUCTION_OR_STAGING", True):
        with patch.object(ForgeConfigurationRepository, "local_insert") as insert:
            repo = ForgeConfigurationRepository()
            insert.assert_not_called()
            with pytest.raises(RuntimeError, match="No persisted Forge configuration"):
                repo.get_active_configuration()
            insert.assert_not_called()
