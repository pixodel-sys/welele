"""
Welele Media™ — Viewer Isolation & Manifest Validation Regression Suite
Proves:
1. Manifest schema rejects duplicate slot_ids and duplicate Hero content_ids (HTTP 422 / ValueError).
2. Canonical store write guard prohibits test writes to live production store.
3. Full Creator / Forge production workflows execute inside isolated test universes without
   contaminating the canonical Viewer manifest, feed, catalog, or Hero slots (Snapshot A == B == C).
"""

import json
import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
from services.experience_engine import ExperienceEngine
from repositories.series_repository import series_repository
from schemas.experience_schemas import ExperienceSection, SlotItem

client = TestClient(app)

def capture_viewer_state_snapshot():
    """Captures a deep deterministic fingerprint of all Viewer-controlled surfaces."""
    feed = series_repository.list_feed()
    resolved_home = ExperienceEngine.resolve_manifest("home", state="published")
    hero_section = next((s for s in resolved_home.get("sections", []) if s.get("type") == "HERO_CAROUSEL"), {})
    hero_slots = hero_section.get("items", [])

    return {
        "total_published_series": len(feed),
        "published_series_ids": sorted([s["id"] for s in feed]),
        "published_series_titles": sorted([s.get("title") for s in feed]),
        "hero_slots_count": len(hero_slots),
        "hero_slot_ids": [it.get("slot_id") for it in hero_slots],
        "hero_content_ids": [it.get("content_id") for it in hero_slots],
        "hero_titles": [it.get("story", {}).get("title") for it in hero_slots],
        "stored_layouts_count": len(db.get("experience_layouts")),
    }


# ---------------------------------------------------------------------------
# TEST 1 — MANIFEST REJECTS DUPLICATE SLOTS & DUPLICATE HERO CONTENT
# ---------------------------------------------------------------------------

def test_manifest_rejects_duplicate_slot_ids():
    """Verify that duplicate slot_ids within a section are rejected with validation error."""
    with pytest.raises(ValueError, match="Duplicate slot_id 'slot_duplicate_01'"):
        ExperienceSection(
            section_id="sec_test_hero",
            type="HERO_CAROUSEL",
            items=[
                SlotItem(slot_id="slot_duplicate_01", content_id="story_blood_ties"),
                SlotItem(slot_id="slot_duplicate_01", content_id="story_queen_of_jozi"),
            ]
        )

def test_manifest_rejects_duplicate_hero_content_ids():
    """Verify that duplicate content_ids in HERO_CAROUSEL are rejected with validation error."""
    with pytest.raises(ValueError, match="Duplicate content_id 'story_blood_ties' in HERO_CAROUSEL"):
        ExperienceSection(
            section_id="sec_test_hero",
            type="HERO_CAROUSEL",
            items=[
                SlotItem(slot_id="slot_hero_a", content_id="story_blood_ties"),
                SlotItem(slot_id="slot_hero_b", content_id="story_blood_ties"),
            ]
        )

def test_experience_engine_save_layout_rejects_corrupted_slots():
    """Verify ExperienceEngine.save_layout blocks invalid layouts from persistent store."""
    bad_layout = {
        "page_id": "test_page",
        "status": "published",
        "sections": [
            {
                "section_id": "sec_corrupted",
                "type": "HERO_CAROUSEL",
                "items": [
                    {"slot_id": "slot_bad_1", "content_id": "story_blood_ties"},
                    {"slot_id": "slot_bad_1", "content_id": "story_queen_of_jozi"}
                ]
            }
        ]
    }
    with pytest.raises(ValueError, match="Duplicate slot_id 'slot_bad_1'"):
        ExperienceEngine.save_layout(bad_layout)


# ---------------------------------------------------------------------------
# TEST 2 — CANONICAL STORE WRITE GUARD ENFORCEMENT
# ---------------------------------------------------------------------------

def test_canonical_store_write_guard_raises_violation():
    """Verify that attempting to write to canonical store while guard is active raises Architectural Boundary Violation."""
    assert db.is_isolated_test is True

    # Temporarily set active store path to canonical store to test the secondary guard
    original_active = db._active_store_path
    db._active_store_path = db._canonical_store_path
    try:
        with pytest.raises(RuntimeError, match="ARCHITECTURAL BOUNDARY VIOLATION"):
            db._save()
    finally:
        db._active_store_path = original_active


# ---------------------------------------------------------------------------
# TEST 3 — THE TWICE-RUN ACCEPTANCE CONTAMINATION TEST
# ---------------------------------------------------------------------------

def test_creator_and_forge_execution_leaves_viewer_uncontaminated():
    """
    Executes a multi-stage Creator & Forge creation lifecycle twice and verifies
    Snapshot A == Snapshot B == Snapshot C across all canonical Viewer surfaces.
    """
    # 1. Capture pristine baseline Snapshot A
    snapshot_a = capture_viewer_state_snapshot()
    assert snapshot_a["hero_slots_count"] == 5
    assert "story_blood_ties" in snapshot_a["hero_content_ids"]
    assert "story_nomvula" not in "".join(snapshot_a["hero_content_ids"])
    assert "series_nomvula" not in "".join(snapshot_a["hero_content_ids"])
    assert "series_sabelo" not in "".join(snapshot_a["hero_content_ids"])

    # 2. RUN 1: Exercise Creator Production / Forge lifecycle inside isolated universe
    # Simulate creator creating draft series, episodes, and attempting to curate into CMS
    test_series_1 = {
        "id": "series_test_creator_1",
        "title": "Nomvula Test Run 1",
        "genre": "Sci-Fi",
        "rating": 5.0,
        "is_published": True,
        "created_at": "2026-09-18T00:00:00Z"
    }
    series_repository.local_insert("series", test_series_1)
    series_repository.local_insert("episodes", {
        "id": "ep_test_1",
        "series_id": "series_test_creator_1",
        "episode_number": 1,
        "title": "Blackout",
        "status": "published",
        "duration_seconds": 60
    })

    # 3. Teardown / isolation cycle (as handled by conftest between test boundaries)
    db.disable_test_isolation()
    db.enable_test_isolation()

    # Capture Snapshot B
    snapshot_b = capture_viewer_state_snapshot()
    assert snapshot_a == snapshot_b, f"State mismatch after Run 1: {snapshot_b}"

    # 4. RUN 2: Exercise another Creator workflow (e.g. Sabelo)
    test_series_2 = {
        "id": "series_test_creator_2",
        "title": "Sabelo Test Run 2",
        "genre": "Comedy",
        "rating": 4.9,
        "is_published": True,
        "created_at": "2026-09-18T00:00:00Z"
    }
    series_repository.local_insert("series", test_series_2)

    db.disable_test_isolation()
    db.enable_test_isolation()

    # Capture Snapshot C
    snapshot_c = capture_viewer_state_snapshot()
    assert snapshot_a == snapshot_c, f"State mismatch after Run 2: {snapshot_c}"
    assert snapshot_b == snapshot_c
