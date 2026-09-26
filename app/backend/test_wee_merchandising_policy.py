"""
Unit & Integration Tests for WEE Merchandising Policy Layer (WEE Layer 2.5).

Asserts all implementation guardrails:
1. Architectural Invariant: Unified Event Spine → Audience Evidence → Merchandising Policy → WEE Experience Manifest
   (WEE consumes derived evidence and does not calculate telemetry metrics independently).
2. MANUAL immutability: hand-curated editorial slots preserved unchanged.
3. HYBRID pinned-item precedence: pinned editorial items stay at front (0..N).
4. Dynamic slot limits: resolved items never exceed max_items.
5. Genre filtering: strict matching before ranking, zero backfill leakage.
6. Duplicate prevention: pinned items never duplicated during dynamic fill.
7. Algorithm ordering:
   - velocity_24h using canonical audience evidence (starts + completions)
   - completion_rate using canonical completion_rate_pct
   - trending using versioned merchandising methodology 2026.1
   - new_releases using publication eligibility and release timestamps
8. Insufficient eligible inventory: defaults to fewer items rather than violating genre.
9. Evidence confidence / sample-size handling: low confidence items weighted down.
10. Published-content eligibility: unpublished or unreleased series excluded.
11. Deterministic resolution: repeatable ordering on identical inputs.
12. Provenance & methodology version propagation: POLICY_VERSION and METHODOLOGY_VERSION attached to manifests.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from services.merchandising_policy_service import MerchandisingPolicyService
from services.experience_engine import ExperienceEngine
from schemas.projection_models import (
    ContentEvidenceProjection,
    ProvenanceEnvelope,
    ConfidenceTier
)


@pytest.fixture
def mock_evidence_projections():
    """
    Sets up mock canonical ContentEvidenceProjection outputs for series.
    Demonstrates diverse sample sizes, confidence tiers, and metrics.
    """
    def make_provenance(has_data: bool, sample_size: int, tier: ConfidenceTier):
        return ProvenanceEnvelope(
            projection_version="1.0.0",
            methodology_version="2026.1",
            calculation_timestamp="2026-09-26T12:00:00Z",
            source_event_count=sample_size * 5,
            source_session_count=sample_size,
            confidence_tier=tier,
            confidence_disclosure="Test disclosure",
            has_data=has_data
        )

    projections = {
        # Series A: Established confidence, high completion rate (95%), high starts
        "series-a": ContentEvidenceProjection(
            projection_id="proj_a",
            target_entity_type="SERIES",
            target_id="series-a",
            series_id="series-a",
            starts=500,
            completions=475,
            completion_rate_pct=95.0,
            unlock_successes=120,
            provenance=make_provenance(True, 500, ConfidenceTier.ESTABLISHED)
        ),
        # Series B: Preliminary confidence (small sample size = 2), 100% completion rate
        # In a naive system, 100% would beat Series A (95%), but confidence weighting must suppress it.
        "series-b": ContentEvidenceProjection(
            projection_id="proj_b",
            target_entity_type="SERIES",
            target_id="series-b",
            series_id="series-b",
            starts=2,
            completions=2,
            completion_rate_pct=100.0,
            unlock_successes=0,
            provenance=make_provenance(True, 2, ConfidenceTier.PRELIMINARY)
        ),
        # Series C: Developing confidence, moderate velocity (starts=200, completions=100)
        "series-c": ContentEvidenceProjection(
            projection_id="proj_c",
            target_entity_type="SERIES",
            target_id="series-c",
            series_id="series-c",
            starts=200,
            completions=100,
            completion_rate_pct=50.0,
            unlock_successes=40,
            provenance=make_provenance(True, 200, ConfidenceTier.DEVELOPING)
        ),
        # Series D: No telemetry data (Cold start)
        "series-d": ContentEvidenceProjection(
            projection_id="proj_d",
            target_entity_type="SERIES",
            target_id="series-d",
            series_id="series-d",
            starts=0,
            completions=0,
            completion_rate_pct=0.0,
            unlock_successes=0,
            provenance=make_provenance(False, 0, ConfidenceTier.INSUFFICIENT)
        )
    }

    mock_service = MagicMock()
    def get_proj(series_id, days=30):
        if series_id in projections:
            return projections[series_id]
        return ContentEvidenceProjection(
            projection_id=f"proj_{series_id}",
            target_entity_type="SERIES",
            target_id=series_id,
            series_id=series_id,
            provenance=make_provenance(False, 0, ConfidenceTier.INSUFFICIENT)
        )
    mock_service.build_content_projection.side_effect = get_proj
    return mock_service


@pytest.fixture
def mock_catalog():
    """
    Catalog of test series with varying genres, publish states, and timestamps.
    """
    now = datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)
    return [
        {
            "id": "series-a",
            "title": "Drama Alpha",
            "genre": "Drama",
            "tags": ["emotional", "relationships"],
            "is_published": True,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        {
            "id": "series-b",
            "title": "Drama Beta",
            "genre": "Drama",
            "tags": ["intense"],
            "is_published": True,
            "created_at": (now - timedelta(days=2)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        {
            "id": "series-c",
            "title": "SciFi Gamma",
            "genre": "Sci-Fi",
            "tags": ["space", "future"],
            "is_published": True,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        {
            "id": "series-d",
            "title": "Comedy Delta",
            "genre": "Comedy",
            "tags": ["funny"],
            "is_published": True,
            "created_at": (now - timedelta(days=1)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        # Unpublished series
        {
            "id": "series-unpublished",
            "title": "Hidden Gem",
            "genre": "Drama",
            "is_published": False,
            "created_at": (now - timedelta(days=1)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        # Future-dated series
        {
            "id": "series-future",
            "title": "Future Hit",
            "genre": "Drama",
            "is_published": True,
            "start_at": (now + timedelta(days=3)).isoformat(),
            "episodes": [{"id": "ep1", "status": "published"}]
        },
        # Series with no published episodes
        {
            "id": "series-no-episodes",
            "title": "Draft Series",
            "genre": "Drama",
            "is_published": True,
            "episodes": [{"id": "ep1", "status": "draft"}]
        }
    ]


@pytest.fixture
def policy_service(mock_evidence_projections, mock_catalog):
    mock_repo = MagicMock()
    mock_repo.list_feed.return_value = mock_catalog
    return MerchandisingPolicyService(
        projection_service=mock_evidence_projections,
        series_repo=mock_repo
    )


# --- 1. Published Content Eligibility ---
def test_published_content_eligibility(policy_service):
    """Unpublished, future-dated, and draft-only series must be strictly excluded."""
    now = datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)
    eligible = policy_service.get_published_eligible_catalog(eval_time=now)
    eligible_ids = {s["id"] for s in eligible}

    assert "series-a" in eligible_ids
    assert "series-b" in eligible_ids
    assert "series-c" in eligible_ids
    assert "series-d" in eligible_ids
    assert "series-unpublished" not in eligible_ids
    assert "series-future" not in eligible_ids
    assert "series-no-episodes" not in eligible_ids


# --- 2. MANUAL Immutability ---
def test_manual_mode_immutability(policy_service, mock_catalog):
    """MANUAL mode must preserve explicit editorial slots without altering order or dynamic fill."""
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_manual_test",
        "title": "Staff Picks",
        "source": {
            "mode": "manual",
            "max_items": 3
        },
        "items": [
            {"slot_id": "slot_1", "content_type": "series", "content_id": "series-d"},
            {"slot_id": "slot_2", "content_type": "series", "content_id": "series-a"}
        ]
    }

    resolved = policy_service.resolve_section_items(section, catalog_map)
    assert len(resolved) == 2
    assert resolved[0]["content_id"] == "series-d"
    assert resolved[1]["content_id"] == "series-a"


# --- 3. HYBRID Pinned-Item Precedence & Duplicate Prevention ---
def test_hybrid_pinned_precedence_and_deduplication(policy_service, mock_catalog):
    """HYBRID mode must keep pinned items at the front and never duplicate them in dynamic fill."""
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_hybrid_test",
        "title": "Spotlight & Trending",
        "source": {
            "mode": "hybrid",
            "algo_type": "velocity_24h",
            "pinned_content_ids": ["series-c"],
            "max_items": 3
        },
        "items": []
    }

    resolved = policy_service.resolve_section_items(section, catalog_map)
    assert len(resolved) == 3
    # Pinned item must be slot 0
    assert resolved[0]["content_id"] == "series-c"
    assert resolved[0]["badge"] == "PINNED"
    
    # Remaining slots filled dynamically, no duplicates of series-c
    remaining_ids = [item["content_id"] for item in resolved[1:]]
    assert "series-c" not in remaining_ids
    assert len(set([item["content_id"] for item in resolved])) == 3


# --- 4. Dynamic Slot Limits ---
def test_dynamic_slot_limits(policy_service, mock_catalog):
    """Dynamic resolution must strictly obey max_items."""
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_limit_test",
        "source": {
            "mode": "algorithmic",
            "algo_type": "velocity_24h",
            "max_items": 2
        }
    }

    resolved = policy_service.resolve_section_items(section, catalog_map)
    assert len(resolved) == 2


# --- 5. Genre Filter Strictness & Insufficient Inventory ---
def test_genre_filtering_and_insufficient_inventory(policy_service, mock_catalog):
    """
    Genre constraints must be strictly applied before ranking.
    If only 1 series matches Sci-Fi and max_items is 5, exactly 1 must be returned.
    Zero backfill leakage allowed.
    """
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_genre_test",
        "source": {
            "mode": "algorithmic",
            "algo_type": "velocity_24h",
            "genre_filter": "Sci-Fi",
            "max_items": 5
        }
    }

    resolved = policy_service.resolve_section_items(section, catalog_map)
    assert len(resolved) == 1
    assert resolved[0]["content_id"] == "series-c"


# --- 6. Evidence Confidence & Sample-Size Weighting ---
def test_evidence_confidence_sample_size_handling(policy_service, mock_catalog):
    """
    High-variance preliminary sample sizes must not rank above established evidence.
    Series B (100% completion, sample_size=2, PRELIMINARY) vs Series A (95% completion, sample_size=500, ESTABLISHED).
    Series A weighted score: 95 * 1.0 = 95.0.
    Series B weighted score: 100 * 0.5 = 50.0.
    Therefore, Series A must rank ahead of Series B.
    """
    eligible = [s for s in mock_catalog if s["id"] in ["series-a", "series-b"]]
    ranked = policy_service.rank_candidates(eligible, algo_type="completion_rate")
    
    assert ranked[0]["id"] == "series-a"
    assert ranked[1]["id"] == "series-b"


# --- 7. Algorithm Ordering: velocity_24h, trending, new_releases ---
def test_algorithm_ordering_velocity_24h(policy_service, mock_catalog):
    """velocity_24h ranks by evidence starts and completions."""
    eligible = [s for s in mock_catalog if s["id"] in ["series-a", "series-c", "series-d"]]
    ranked = policy_service.rank_candidates(eligible, algo_type="velocity_24h")

    # Series A: starts=500, completions=475 -> ~1450 score
    # Series C: starts=200, completions=100 -> ~320 score
    # Series D: starts=0 -> 0 score
    assert [s["id"] for s in ranked] == ["series-a", "series-c", "series-d"]


def test_algorithm_ordering_trending_methodology(policy_service, mock_catalog):
    """trending methodology 2026.1 balances velocity, completion conviction, and unlocks."""
    eligible = [s for s in mock_catalog if s["id"] in ["series-a", "series-c", "series-d"]]
    ranked = policy_service.rank_candidates(eligible, algo_type="trending")
    assert ranked[0]["id"] == "series-a"


def test_algorithm_ordering_new_releases(policy_service, mock_catalog):
    """new_releases ranks strictly by release timestamp descending."""
    eligible = [s for s in mock_catalog if s["id"] in ["series-a", "series-b", "series-d"]]
    ranked = policy_service.rank_candidates(eligible, algo_type="new_releases")

    # series-d was created 1 day ago
    # series-b was created 2 days ago
    # series-a was created 10 days ago
    assert [s["id"] for s in ranked] == ["series-d", "series-b", "series-a"]


# --- 8. Deterministic Resolution ---
def test_deterministic_resolution(policy_service, mock_catalog):
    """Repeated calls with identical catalog and evidence must return identical order."""
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_determ",
        "source": {
            "mode": "algorithmic",
            "algo_type": "velocity_24h",
            "max_items": 4
        }
    }

    res1 = [item["content_id"] for item in policy_service.resolve_section_items(section, catalog_map)]
    res2 = [item["content_id"] for item in policy_service.resolve_section_items(section, catalog_map)]
    assert res1 == res2


# --- 9. Viewer Badges Separation ---
def test_viewer_badges_separated_from_merchandising_signals(policy_service, mock_catalog):
    """Dynamic algorithmic items must not have synthetic internal badges forced onto viewer cards."""
    catalog_map = {s["id"]: s for s in mock_catalog}
    section = {
        "section_id": "sec_badges",
        "source": {
            "mode": "algorithmic",
            "algo_type": "velocity_24h",
            "max_items": 2
        }
    }

    resolved = policy_service.resolve_section_items(section, catalog_map)
    for item in resolved:
        # Viewer badge is None for purely dynamic algorithmic fills
        assert item["badge"] is None


# --- 10. Manifest Provenance & Policy Version Propagation ---
def test_manifest_provenance_propagation(monkeypatch, mock_catalog):
    """Manifest compilation must attach policy and methodology versions to sections."""
    from repositories.series_repository import series_repository
    monkeypatch.setattr(series_repository, "list_feed", lambda: mock_catalog)

    manifest = ExperienceEngine.resolve_manifest(page_id="home", state="draft")
    assert "sections" in manifest
    assert len(manifest["sections"]) > 0

    for sec in manifest["sections"]:
        assert "merchandising_metadata" in sec
        meta = sec["merchandising_metadata"]
        assert meta["policy_version"] == MerchandisingPolicyService.POLICY_VERSION
        assert meta["methodology_version"] == MerchandisingPolicyService.METHODOLOGY_VERSION
        assert "mode" in meta
        assert "algo_type" in meta
        assert "resolved_item_count" in meta
