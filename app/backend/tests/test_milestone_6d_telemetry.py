"""
Milestone 6D: Focused Authoritative Telemetry Persistence & Lineage Validation Tests
Verifies:
1. Live PostgreSQL lineage validation with canonical episode
2. Invalid / nonexistent episode rejection (lineage_valid=False)
3. Series / episode lineage mismatch rejection
4. Durable telemetry schema mapping and sensitive data scrubbing
5. Duplicate event deduplication / idempotency
6. Telemetry persistence failure isolation (viewer playback continues)
7. Trailer / test session compatibility
8. Restart persistence lookup across process memory clearing
"""

import os
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

os.environ["ENVIRONMENT"] = "test"

from schemas.viewer_telemetry_models import (
    ViewerTelemetryEvent,
    EventSpineFamily,
    ViewerEventType,
    EventSource
)
from services.viewer_telemetry_service import viewer_telemetry_service
from repositories.telemetry_repository import telemetry_repository, _sanitize_metadata
from repositories.series_repository import series_repository, to_uuid


def test_lineage_validation_valid_canonical_episode():
    """Valid canonical episode and its matching series produces lineage_valid=True."""
    # Using seed canonical episode
    ep = series_repository.get_episode("ep_bt_1")
    assert ep is not None, "Canonical episode ep_bt_1 must exist"
    series_id = ep.get("series_id") or "story_blood_ties"

    event = ViewerTelemetryEvent(
        event_id=f"evt_lineage_valid_{uuid.uuid4().hex[:8]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_val_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id="ep_bt_1",
        series_id=series_id,
        episode_id="ep_bt_1",
        position_seconds=0.0,
        duration_seconds=90.0,
        event_source=EventSource.CLIENT,
        event_version="1.0"
    )

    is_valid = viewer_telemetry_service.validate_content_lineage(event)
    assert is_valid is True

    record_res = viewer_telemetry_service.record_event(event)
    assert record_res["status"] == "recorded"
    assert record_res["lineage_valid"] is True


def test_lineage_validation_invalid_nonexistent_episode():
    """Non-existent episode produces lineage_valid=False without crashing."""
    fake_ep_id = f"ep_nonexistent_{uuid.uuid4().hex[:12]}"
    event = ViewerTelemetryEvent(
        event_id=f"evt_invalid_{uuid.uuid4().hex[:8]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_inv_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id=fake_ep_id,
        series_id="story_blood_ties",
        episode_id=fake_ep_id,
        position_seconds=0.0,
        duration_seconds=90.0
    )

    is_valid = viewer_telemetry_service.validate_content_lineage(event)
    assert is_valid is False

    record_res = viewer_telemetry_service.record_event(event)
    assert record_res["status"] == "recorded"
    assert record_res["lineage_valid"] is False


def test_lineage_validation_series_mismatch():
    """Episode assigned to the wrong series fails lineage validation."""
    ep = series_repository.get_episode("ep_bt_1")
    assert ep is not None

    event = ViewerTelemetryEvent(
        event_id=f"evt_mismatch_{uuid.uuid4().hex[:8]}",
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_mis_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id="ep_bt_1",
        series_id="story_queen_of_jozi",  # Deliberate mismatch
        episode_id="ep_bt_1",
        position_seconds=0.0,
        duration_seconds=90.0
    )

    is_valid = viewer_telemetry_service.validate_content_lineage(event)
    assert is_valid is False


def test_durable_telemetry_schema_mapping_and_secret_scrubbing():
    """Payload correctly maps to canonical public.telemetry_events schema and scrubs sensitive secrets."""
    event_id = f"evt_map_{uuid.uuid4().hex[:8]}"
    event_dict = {
        "event_id": event_id,
        "event_family": "WATCH",
        "event_type": "PLAYBACK_PROGRESS",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "session_id": "sess_map_001",
        "viewer_id": "viewer_za_001",
        "anonymous_id": "anon_dev_001",
        "content_type": "EPISODE",
        "content_id": "ep_bt_1",
        "series_id": "story_blood_ties",
        "episode_id": "ep_bt_1",
        "position_seconds": 45.5,
        "duration_seconds": 90.0,
        "milestone_pct": 50,
        "event_source": "CLIENT",
        "event_version": "1.0",
        "source": "VERTICAL_PLAYER",
        "environment": "staging",
        "is_test": False,
        "metadata": {
            "bearer_token": "SHOULD_BE_SCRUBBED_SECRET",
            "api_key": "SHOULD_BE_SCRUBBED_KEY",
            "otp_code": "SHOULD_BE_SCRUBBED_OTP",
            "display_title": "Blood Ties Ep 1",
            "player_mode": "fullscreen"
        }
    }

    db_payload = telemetry_repository._map_to_db_payload(event_dict)

    # Required DB schema columns
    assert db_payload["id"] == to_uuid(event_id)
    assert db_payload["event_name"] == "PLAYBACK_PROGRESS"
    assert db_payload["session_id"] == "sess_map_001"
    assert db_payload["playback_second"] == 45
    assert db_payload["region_code"] == "ZA"
    assert db_payload["device_type"] in ("VERTICAL_PLAYER", "mobile_pwa")
    assert db_payload["series_id"] == to_uuid("story_blood_ties")
    assert db_payload["episode_id"] == to_uuid("ep_bt_1")

    # Sensitive data scrubbing in metadata
    meta = db_payload["metadata"]
    assert "bearer_token" not in meta
    assert "api_key" not in meta
    assert "otp_code" not in meta
    assert meta["display_title"] == "Blood Ties Ep 1"
    assert meta["player_mode"] == "fullscreen"
    assert meta["milestone_pct"] == 50
    assert meta["position_seconds"] == 45.5


def test_duplicate_event_deduplication():
    """Duplicate event submissions with identical event_id are strictly deduplicated."""
    event_id = f"evt_dedup_{uuid.uuid4().hex[:10]}"
    event = ViewerTelemetryEvent(
        event_id=event_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_STARTED,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id=f"sess_dedup_{uuid.uuid4().hex[:6]}",
        content_type="EPISODE",
        content_id="ep_bt_1",
        series_id="story_blood_ties",
        episode_id="ep_bt_1",
        position_seconds=0.0,
        duration_seconds=90.0
    )

    first_res = viewer_telemetry_service.record_event(event)
    assert first_res["status"] == "recorded"

    second_res = viewer_telemetry_service.record_event(event)
    assert second_res["status"] == "deduplicated"
    assert second_res["action"] == "ignored_duplicate"
    assert second_res["event_id"] == event_id


def test_telemetry_failure_isolation():
    """If database persistence raises an exception, viewer playback is never broken."""
    event_id = f"evt_fail_iso_{uuid.uuid4().hex[:8]}"
    event_dict = {
        "event_id": event_id,
        "event_family": "WATCH",
        "event_type": "PLAYBACK_STARTED",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "session_id": "sess_fail_001",
        "content_type": "EPISODE",
        "content_id": "ep_bt_1",
        "series_id": "story_blood_ties",
        "episode_id": "ep_bt_1",
        "position_seconds": 0.0,
        "duration_seconds": 90.0
    }

    # Simulate is_live=True and an operational database connection error
    with patch.object(type(telemetry_repository), "is_live", new_callable=PropertyMock, return_value=True):
        with patch.object(telemetry_repository, "get_table") as mock_get_table:
            mock_table = MagicMock()
            mock_table.insert.side_effect = Exception("PostgreSQL simulated network connection timeout")
            mock_get_table.return_value = mock_table

            # save_event must catch the error and not raise
            saved = telemetry_repository.save_event(event_dict)
            assert saved is not None
            assert saved.get("event_id") == event_id


def test_trailer_test_compatibility():
    """Trailer and test events with is_test=True maintain compatibility and provenance."""
    event_id = f"evt_trailer_{uuid.uuid4().hex[:8]}"
    event = ViewerTelemetryEvent(
        event_id=event_id,
        event_family=EventSpineFamily.WATCH,
        event_type=ViewerEventType.PLAYBACK_PROGRESS,
        occurred_at=datetime.now(timezone.utc).isoformat(),
        session_id="sess_trailer_001",
        content_type="EPISODE",
        content_id="ep_bt_1",
        series_id="story_blood_ties",
        episode_id="ep_bt_1",
        position_seconds=15.0,
        duration_seconds=30.0,
        is_test=True,
        metadata={"content_mode": "TRAILER", "trailer_cut": "teaser_30s"}
    )

    res = viewer_telemetry_service.record_event(event)
    assert res["status"] == "recorded"

    found = telemetry_repository.find_event_by_id(event_id)
    assert found is not None
    assert found.get("is_test") is True
    assert found.get("metadata", {}).get("content_mode") == "TRAILER"


def test_restart_persistence_lookup():
    """Simulating process restart (empty memory cache) retrieves event from remote DB store."""
    event_id = f"evt_restart_{uuid.uuid4().hex[:8]}"
    event_uuid = to_uuid(event_id)

    db_row = {
        "id": event_uuid,
        "event_name": "PLAYBACK_STARTED",
        "user_id": None,
        "session_id": "sess_restart_001",
        "ip_id": None,
        "series_id": to_uuid("story_blood_ties"),
        "episode_id": to_uuid("ep_bt_1"),
        "playback_second": 0,
        "region_code": "ZA",
        "device_type": "mobile_pwa",
        "metadata": {
            "event_id": event_id,
            "session_id": "sess_restart_001",
            "position_seconds": 0.0,
            "environment": "staging"
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Simulate live lookup after in-memory events are empty
    with patch.object(type(telemetry_repository), "is_live", new_callable=PropertyMock, return_value=True):
        with patch.object(telemetry_repository, "_get_all_events", return_value=[]):
            with patch.object(telemetry_repository, "get_table") as mock_get_table:
                mock_table = MagicMock()
                mock_select = MagicMock()
                mock_eq = MagicMock()
                mock_limit = MagicMock()
                mock_limit.execute.return_value = MagicMock(data=[db_row])
                mock_eq.limit.return_value = mock_limit
                mock_select.eq.return_value = mock_eq
                mock_table.select.return_value = mock_select
                mock_get_table.return_value = mock_table

                found = telemetry_repository.find_event_by_id(event_id)
                assert found is not None
                assert found.get("event_id") == event_id
                assert found.get("session_id") == "sess_restart_001"
