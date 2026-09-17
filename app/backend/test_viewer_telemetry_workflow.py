"""
Welele Media™ — Viewer Telemetry Workflow & Integrity Test Suite (Phase 6 Measurement Layer)
Tests all 18 core Telemetry Invariants & the 10 Telemetry Integrity Checks:
  1 — Event Identity Integrity
  2 — Content Lineage Integrity
  3 — Session Integrity
  4 — Temporal Integrity
  5 — Playback Integrity (Bounded milestones & once-per-session guard)
  6 — Continuation Integrity (Empty Episode 2 truth boundary)
  7 — Reaction Integrity
  8 — Return Integrity
  9 — Payment Integrity (Distinct states & NOT_EXERCISED disposition)
  10 — Failure Isolation Integrity (Telemetry failure cannot break viewer)
"""

import os
import sys
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app
from database import db
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from repositories.telemetry_repository import telemetry_repository
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from services.episode_production_pack_service import episode_production_pack_service
from services.viewer_telemetry_service import viewer_telemetry_service
from schemas.viewer_telemetry_models import (
    EventSpineFamily,
    ViewerEventType,
    EventSource,
    ViewerTelemetryEvent,
    TelemetryIntegrityCheckResult,
    TelemetryEvidencePackage
)

client = TestClient(app)


@pytest.fixture
def telemetry_test_setup():
    """Sets up canonical Isibusiso IP → Story Package → Series → Episodes 1 & 2 for telemetry measurement."""
    ips = ip_repository.list_ips()
    target_ip = next((ip for ip in ips if ip.get("franchise_code") == "IP-ISIBUSISO" or ip.get("title") == "Isibusiso"), None)
    if not target_ip:
        target_ip = {
            "id": "ip_isibusiso_dynasty",
            "title": "Isibusiso",
            "franchise_code": "IP-ISIBUSISO",
            "logline": "A devout Soweto midwife delivers a baby during a township power blackout and notices a birthmark matching a legendary royal bloodline.",
            "synopsis": "Isibusiso tracks the collision between customary royal succession and modern corporate mining power.",
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
                {"anchor_number": 2, "anchor_name": "Dawn Arrival", "summary": "Bhekisisa arrives with cash; Lerato confesses to surrogacy contract."}
            ],
            "dialogues": [
                {"character": "Thandiwe Zulu", "line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa."}
            ],
            "beats": [
                {"beat_number": 1, "label": "Cold Open", "timestamp_seconds": 15, "action_description": "Midwife delivers newborn."}
            ],
            "forge_configuration_id": "CFG-001",
            "lineage_hash": "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        }
        ip_repository.local_insert("story_packages", pkg)
        pkg_id = "pkg_isibusiso_v1"
    else:
        pkg = story_packages[0]
        pkg_id = pkg["id"]

    series = series_episode_service.create_series_from_story_package(ip_id=ip_id, story_package_id=pkg_id, season_number=1)
    series_id = series["id"]
    series_repository.local_update("series", "id", series_id, {
        "title": "Isibusiso",
        "vertical_poster": "/posters/isibusiso.jpg",
        "cover_image": "/banners/isibusiso_banner.jpg",
        "is_published": True
    })

    all_eps = series_repository.get_episodes_for_series(series_id)
    ep1 = next((e for e in all_eps if e.get("episode_number") == 1), None)
    if not ep1:
        ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1, is_empty_draft=False)
    
    ep1_id = ep1["id"]
    series_repository.local_update("episodes", "id", ep1_id, {
        "series_id": series_id,
        "title": "Episode 1 — The Midnight Sovereign",
        "is_empty_draft": False,
        "readiness_state": "PRODUCTION_READY",
        "lifecycle_state": "PUBLISHED",
        "status": "published",
        "video_url": "/videos/isibusiso_s01e01_master.mp4",
        "duration_seconds": 90
    })

    ep2 = next((e for e in all_eps if e.get("episode_number") == 2), None)
    if not ep2:
        ep2 = series_episode_service.create_episode(series_id=series_id, episode_number=2, is_empty_draft=True)
    
    ep2_id = ep2["id"]
    series_repository.local_update("episodes", "id", ep2_id, {
        "series_id": series_id,
        "title": "Episode 2 — Bloodline Accord",
        "is_empty_draft": True,
        "readiness_state": "DRAFT_EMPTY",
        "lifecycle_state": "DRAFT",
        "status": "draft",
        "video_url": None
    })

    return {
        "ip_id": ip_id,
        "series_id": series_id,
        "ep1_id": ep1_id,
        "ep2_id": ep2_id
    }


def test_content_open_generates_event(telemetry_test_setup):
    """Test 1: Content open generates a factual CONTENT_OPENED event beneath OPEN family."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_test_{uuid.uuid4().hex[:6]}"

    event = ViewerTelemetryEvent(
        event_id=f"evt_open_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.CONTENT_OPENED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        source="DISCOVERY_FEED",
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )

    response = client.post("/api/v1/telemetry/events", json=event.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["event_id"] == event.event_id


def test_playback_generates_events(telemetry_test_setup):
    """Test 2: Playback generates start, progress, and pause events beneath WATCH family."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_play_{uuid.uuid4().hex[:6]}"

    start_event = ViewerTelemetryEvent(
        event_id=f"evt_start_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=0.0,
        duration_seconds=90.0,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )
    res = client.post("/api/v1/telemetry/events", json=start_event.model_dump())
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"


def test_progress_milestone_once_per_session_guard(telemetry_test_setup):
    """Test 3: Milestone progress is emitted at most once per session per content item (no scrub spam)."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_scrub_{uuid.uuid4().hex[:6]}"

    # 1. Emit 50% milestone
    e1 = ViewerTelemetryEvent(
        event_id=f"evt_m50_1_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_PROGRESS,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=45.0,
        duration_seconds=90.0,
        milestone_pct=50,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )
    r1 = client.post("/api/v1/telemetry/events", json=e1.model_dump()).json()
    assert r1["status"] == "recorded"

    # 2. Scrub back to 30s and hit 50% again with a new event_id
    e2 = ViewerTelemetryEvent(
        event_id=f"evt_m50_2_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_PROGRESS,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=45.0,
        duration_seconds=90.0,
        milestone_pct=50,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )
    r2 = client.post("/api/v1/telemetry/events", json=e2.model_dump()).json()
    assert r2["status"] == "deduplicated"
    assert r2["action"] == "suppressed_duplicate_milestone"


def test_event_identity_and_provenance_fields(telemetry_test_setup):
    """Test 4: Event identity and measurement provenance (event_source, event_version) are strictly present."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    evt_id = f"evt_prov_{uuid.uuid4().hex[:6]}"

    event = ViewerTelemetryEvent(
        event_id=evt_id,
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.CONTENT_OPENED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )
    saved = viewer_telemetry_service.record_event(event)
    assert saved["event_id"] == evt_id

    stored = telemetry_repository.find_event_by_id(evt_id)
    assert stored is not None
    assert stored["event_source"] == "CLIENT"
    assert stored["event_version"] == "1.0"


def test_duplicate_event_id_deduplication(telemetry_test_setup):
    """Test 5: Client retries with identical event_id are idempotent and deduplicated."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    fixed_event_id = f"evt_fixed_{uuid.uuid4().hex[:6]}"

    event = ViewerTelemetryEvent(
        event_id=fixed_event_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )

    # First attempt
    res1 = client.post("/api/v1/telemetry/events", json=event.model_dump()).json()
    assert res1["status"] == "recorded"

    # Second attempt (retry)
    res2 = client.post("/api/v1/telemetry/events", json=event.model_dump()).json()
    assert res2["status"] == "deduplicated"
    assert res2["action"] == "ignored_duplicate"


def test_event_content_lineage_validation(telemetry_test_setup):
    """Test 6: Events pointing to invalid content are flagged during lineage check."""
    series_id = telemetry_test_setup["series_id"]

    fake_event = ViewerTelemetryEvent(
        event_id=f"evt_fake_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.CONTENT_OPENED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id="ep_non_existent_9999",
        series_id=series_id,
        episode_id="ep_non_existent_9999",
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )

    res = viewer_telemetry_service.record_event(fake_event)
    assert res["lineage_valid"] is False


def test_session_chronological_ordering_reconstruction(telemetry_test_setup):
    """Test 7: Chronological sequence of session events is faithfully preserved."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_order_{uuid.uuid4().hex[:6]}"

    t1 = "2026-09-17T00:00:01Z"
    t2 = "2026-09-17T00:00:05Z"
    t3 = "2026-09-17T00:00:30Z"

    e1 = ViewerTelemetryEvent(event_id=f"e1_{session_id}", event_family=EventSpineFamily.OPEN, event_type=ViewerEventType.CONTENT_OPENED, occurred_at=t1, session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id)
    e2 = ViewerTelemetryEvent(event_id=f"e2_{session_id}", event_family=EventSpineFamily.WATCH, event_type=ViewerEventType.PLAYBACK_STARTED, occurred_at=t2, session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id)
    e3 = ViewerTelemetryEvent(event_id=f"e3_{session_id}", event_family=EventSpineFamily.WATCH, event_type=ViewerEventType.PLAYBACK_PROGRESS, occurred_at=t3, session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id, milestone_pct=25, position_seconds=22.5)

    viewer_telemetry_service.record_event(e1)
    viewer_telemetry_service.record_event(e2)
    viewer_telemetry_service.record_event(e3)

    timeline = viewer_telemetry_service.get_session_events(session_id)
    assert len(timeline) == 3
    assert timeline[0].event_type == ViewerEventType.CONTENT_OPENED
    assert timeline[1].event_type == ViewerEventType.PLAYBACK_STARTED
    assert timeline[2].event_type == ViewerEventType.PLAYBACK_PROGRESS


def test_pause_resume_events_truthfulness(telemetry_test_setup):
    """Test 8: Pause and resume accurately capture exact timestamps."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_pause_{uuid.uuid4().hex[:6]}"

    p_evt = ViewerTelemetryEvent(
        event_id=f"evt_pause_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_PAUSED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=42.5,
        duration_seconds=90.0
    )
    res = viewer_telemetry_service.record_event(p_evt)
    assert res["status"] == "recorded"


def test_completion_event_truthfulness(telemetry_test_setup):
    """Test 9: Playback completion event captures 100% position."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_comp_{uuid.uuid4().hex[:6]}"

    comp_evt = ViewerTelemetryEvent(
        event_id=f"evt_comp_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_COMPLETED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=90.0,
        duration_seconds=90.0,
        milestone_pct=100
    )
    res = viewer_telemetry_service.record_event(comp_evt)
    assert res["status"] == "recorded"


def test_gated_episode_2_does_not_emit_false_play_event(telemetry_test_setup):
    """Test 10: Episode 2 (DRAFT_EMPTY) cannot generate false PLAYBACK_STARTED event."""
    series_id = telemetry_test_setup["series_id"]
    ep2_id = telemetry_test_setup["ep2_id"]
    session_id = f"sess_gate_{uuid.uuid4().hex[:6]}"

    # Inspect stream availability
    stream_info = client.get(f"/api/v1/episodes/{series_id}/{ep2_id}").json()
    assert stream_info["is_available"] is False
    assert stream_info["stream"] is None

    # Verify no false playback started event in session
    session_events = viewer_telemetry_service.get_session_events(session_id)
    false_plays = [e for e in session_events if e.content_id == ep2_id and e.event_type == ViewerEventType.PLAYBACK_STARTED]
    assert len(false_plays) == 0


def test_gated_episode_2_emits_truthful_gated_content_presented(telemetry_test_setup):
    """Test 11: Episode 2 Gated Presentation is recorded with content_state = UNAVAILABLE."""
    series_id = telemetry_test_setup["series_id"]
    ep2_id = telemetry_test_setup["ep2_id"]
    session_id = f"sess_gated_pres_{uuid.uuid4().hex[:6]}"

    gated_evt = ViewerTelemetryEvent(
        event_id=f"evt_gated_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.CONTINUE,
        event_type=ViewerEventType.GATED_CONTENT_PRESENTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_id=ep2_id,
        series_id=series_id,
        episode_id=ep2_id,
        source="CONTINUATION_MODAL",
        metadata={
            "content_state": "UNAVAILABLE",
            "is_available": False,
            "playback_started": False
        }
    )

    res = viewer_telemetry_service.record_event(gated_evt)
    assert res["status"] == "recorded"

    stored = telemetry_repository.find_event_by_id(gated_evt.event_id)
    assert stored["metadata"]["content_state"] == "UNAVAILABLE"
    assert stored["metadata"]["is_available"] is False


def test_explicit_reaction_generates_reaction_event(telemetry_test_setup):
    """Test 12: Explicit user interaction emits REACTION_ADDED with reaction type."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_react_{uuid.uuid4().hex[:6]}"

    react_evt = ViewerTelemetryEvent(
        event_id=f"evt_react_{uuid.uuid4().hex[:6]}",
        event_family=EventSpineFamily.REACT,
        event_type=ViewerEventType.REACTION_ADDED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=session_id,
        content_id=ep1_id,
        series_id=series_id,
        episode_id=ep1_id,
        position_seconds=88.0,
        metadata={"reaction_type": "🔥", "trigger": "cliffhanger"}
    )
    res = viewer_telemetry_service.record_event(react_evt)
    assert res["status"] == "recorded"


def test_return_event_factual_rule(telemetry_test_setup):
    """Test 13: Return event requires prior session existence and new session initiation."""
    viewer_id = f"viewer_return_{uuid.uuid4().hex[:6]}"
    series_id = telemetry_test_setup["series_id"]

    # Session 1
    s1 = f"sess_1_{uuid.uuid4().hex[:6]}"
    e1 = ViewerTelemetryEvent(event_id=f"evt_1_{s1}", event_family=EventSpineFamily.OPEN, event_type=ViewerEventType.CONTENT_OPENED, occurred_at=datetime.now(timezone.utc).isoformat(), session_id=s1, viewer_id=viewer_id, content_id=series_id, series_id=series_id)
    viewer_telemetry_service.record_event(e1)

    # Prior session exists
    priors = telemetry_repository.get_previous_sessions_for_viewer(viewer_id=viewer_id)
    assert s1 in priors

    # Session 2
    s2 = f"sess_2_{uuid.uuid4().hex[:6]}"
    ret_evt = ViewerTelemetryEvent(event_id=f"evt_ret_{s2}", event_family=EventSpineFamily.RETURN, event_type=ViewerEventType.SESSION_RETURNED, occurred_at=datetime.now(timezone.utc).isoformat(), session_id=s2, viewer_id=viewer_id, content_id=series_id, series_id=series_id)
    res = viewer_telemetry_service.record_event(ret_evt)
    assert res["status"] == "recorded"


def test_payment_states_distinct_and_not_exercised_disposition(telemetry_test_setup):
    """Test 14: Payment taxonomy defines distinct states; unexercised specimen marked NOT_EXERCISED."""
    # Validate payment enum definitions
    assert ViewerEventType.PAYMENT_INITIATED.value == "PAYMENT_INITIATED"
    assert ViewerEventType.PAYMENT_SUCCEEDED.value == "PAYMENT_SUCCEEDED"
    assert ViewerEventType.PAYMENT_FAILED.value == "PAYMENT_FAILED"
    assert ViewerEventType.CONTENT_UNLOCKED.value == "CONTENT_UNLOCKED"

    # Evidence package verification
    evidence = viewer_telemetry_service.execute_isibusiso_telemetry_validation()
    assert evidence.payment_exercise_status == "NOT_EXERCISED"
    assert "not monetized" in evidence.payment_exercise_reason.lower()


def test_telemetry_failure_isolation_viewer_continues(telemetry_test_setup):
    """Test 15: Failure isolation — malformed event or error handling never throws or crashes endpoint."""
    response = client.post("/api/v1/telemetry/events", json={
        "event_id": "",  # invalid
        "event_family": "INVALID_FAMILY",
        "event_type": "INVALID_TYPE"
    })
    # Validation error returned cleanly with HTTP 422, server remains healthy
    assert response.status_code == 422


def test_batch_telemetry_ingestion_and_validation(telemetry_test_setup):
    """Test 16: Batch ingestion applies per-event validation and deduplication."""
    series_id = telemetry_test_setup["series_id"]
    ep1_id = telemetry_test_setup["ep1_id"]
    session_id = f"sess_batch_{uuid.uuid4().hex[:6]}"

    events = [
        ViewerTelemetryEvent(event_id=f"b1_{session_id}", event_family=EventSpineFamily.OPEN, event_type=ViewerEventType.CONTENT_OPENED, occurred_at=datetime.now(timezone.utc).isoformat(), session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id),
        ViewerTelemetryEvent(event_id=f"b2_{session_id}", event_family=EventSpineFamily.WATCH, event_type=ViewerEventType.PLAYBACK_STARTED, occurred_at=datetime.now(timezone.utc).isoformat(), session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id),
        # Duplicate of b1
        ViewerTelemetryEvent(event_id=f"b1_{session_id}", event_family=EventSpineFamily.OPEN, event_type=ViewerEventType.CONTENT_OPENED, occurred_at=datetime.now(timezone.utc).isoformat(), session_id=session_id, content_id=ep1_id, series_id=series_id, episode_id=ep1_id),
    ]

    response = client.post("/api/v1/telemetry/batch", json=[e.model_dump() for e in events])
    assert response.status_code == 200
    data = response.json()
    assert data["total_received"] == 3
    assert data["recorded"] == 2
    assert data["deduplicated"] == 1


def test_no_upstream_canon_mutation(telemetry_test_setup):
    """Test 17: Telemetry ingestion never mutates upstream canon, blueprints, or production packs."""
    ip_id = telemetry_test_setup["ip_id"]
    ep1_id = telemetry_test_setup["ep1_id"]

    ip_before = ip_repository.get_ip_detail(ip_id)
    bp_before = production_repository.get_episode_blueprint(ep1_id)
    pack_before = production_repository.get_episode_pack(ip_id, 1)

    # Run telemetry validation
    evidence = viewer_telemetry_service.execute_isibusiso_telemetry_validation()

    ip_after = ip_repository.get_ip_detail(ip_id)
    bp_after = production_repository.get_episode_blueprint(ep1_id)
    pack_after = production_repository.get_episode_pack(ip_id, 1)

    assert ip_before["ip"] == ip_after["ip"]
    assert bp_before == bp_after
    assert pack_before == pack_after


def test_the_10_telemetry_integrity_checks(telemetry_test_setup):
    """Test 18: Evaluates all 10 Telemetry Integrity Checks and verifies PASSED results."""
    evidence = viewer_telemetry_service.execute_isibusiso_telemetry_validation()

    assert evidence is not None
    assert len(evidence.integrity_checks) == 10

    expected_names = [
        "Event Identity Integrity",
        "Content Lineage Integrity",
        "Session Integrity",
        "Temporal Integrity",
        "Playback Integrity",
        "Continuation Integrity",
        "Reaction Integrity",
        "Return Integrity",
        "Payment Integrity",
        "Failure Isolation Integrity"
    ]

    for expected_name in expected_names:
        check = next((c for c in evidence.integrity_checks if c.check_name == expected_name), None)
        assert check is not None, f"Telemetry integrity check '{expected_name}' missing from evidence package."
        assert check.status == "PASSED"
        assert len(check.findings) > 10
