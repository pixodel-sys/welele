"""
Welele Media™ — Phase 3A: Make the Experiment Observable Test Suite
Verifies:
1. Missing events ingestion (APP_OPEN, FEED_IMPRESSION, GATED_CONTENT_PRESENTED, PAYMENT_INITIATED, NEXT_EPISODE_SELECTED, REACTION_ADDED, COMMENT_SUBMITTED)
2. Evidence protection & environment separation (production vs staging vs test)
3. Retention calculation with zero synthetic data and agnostic series/episode resolution
4. Complete 11-step funnel aggregation on GET /api/v1/admin/project40-funnel
5. Zero synthetic data policy enforcement
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from main import app
from schemas.viewer_telemetry_models import ViewerTelemetryEvent, EventSpineFamily, ViewerEventType, EventSource
from repositories.telemetry_repository import telemetry_repository
from repositories.event_repository import event_repository
from repositories.series_repository import series_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def test_telemetry_ingestion_with_environment_and_is_test():
    """Verify that events carry environment and is_test flags and are correctly persisted."""
    session_id = f"sess_obs_test_{uuid.uuid4().hex[:8]}"
    evt_id = f"evt_obs_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    event = ViewerTelemetryEvent(
        event_id=evt_id,
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.APP_OPEN,
        occurred_at=now_iso,
        session_id=session_id,
        viewer_id="viewer_obs_01",
        anonymous_id="anon_obs_01",
        content_type="PLATFORM",
        content_id="welele_pwa",
        environment="staging",
        is_test=True,
        metadata={"platform": "PWA_CHROME"}
    )

    res = client.post("/api/v1/telemetry/events", json=event.model_dump())
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"

    # Verify in repository
    stored = telemetry_repository.find_event_by_id(evt_id)
    assert stored is not None
    assert stored["environment"] == "staging"
    assert stored["is_test"] is True
    assert stored["event_type"] == "APP_OPEN"


def test_production_vs_test_environment_separation():
    """Prove that test-tagged events never pollute production funnel evidence."""
    test_session = f"sess_internal_canary_{uuid.uuid4().hex[:8]}"
    prod_session = f"sess_real_viewer_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Ingest test event
    test_evt = ViewerTelemetryEvent(
        event_id=f"evt_test_{uuid.uuid4().hex[:8]}",
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.APP_OPEN,
        occurred_at=now_iso,
        session_id=test_session,
        content_id="welele_pwa",
        environment="test",
        is_test=True
    )
    client.post("/api/v1/telemetry/events", json=test_evt.model_dump())

    # 2. Ingest genuine production event
    prod_evt = ViewerTelemetryEvent(
        event_id=f"evt_prod_{uuid.uuid4().hex[:8]}",
        event_family=EventSpineFamily.OPEN,
        event_type=ViewerEventType.APP_OPEN,
        occurred_at=now_iso,
        session_id=prod_session,
        content_id="welele_pwa",
        environment="production",
        is_test=False
    )
    client.post("/api/v1/telemetry/events", json=prod_evt.model_dump())

    # Auth as admin for funnel query
    admin_token = create_access_token(
        user_id="admin_test_p40",
        role="admin",
        market="ALL",
        kyc_status="SUPER_ADMIN"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Query production funnel
    prod_funnel = client.get("/api/v1/admin/project40-funnel?environment=production", headers=admin_headers).json()
    assert prod_funnel["provenance"]["zero_synthetic_data"] is True
    assert prod_funnel["provenance"]["environment_filter"] == "production"
    assert prod_funnel["provenance"]["test_events_excluded"] >= 1

    # Query test environment funnel
    test_funnel = client.get("/api/v1/admin/project40-funnel?environment=test", headers=admin_headers).json()
    assert test_funnel["provenance"]["environment_filter"] == "test"


def test_complete_viewer_journey_funnel_aggregation():
    """
    Simulates complete viewer journey:
    Entered → Discovered → Selected → Watched → Continued → Engaged → Paywall → Payment Attempt → Paid → Continued → Returned
    and verifies that GET /api/v1/admin/project40-funnel reports each step with empirical counts.
    """
    journey_session = f"sess_journey_{uuid.uuid4().hex[:8]}"
    viewer_id = f"viewer_j_{uuid.uuid4().hex[:6]}"
    series_id = "story_blood_ties"
    ep1_id = "ep_bt_1"
    ep2_id = "ep_bt_2"
    t0 = datetime.now(timezone.utc).isoformat()
    t1 = datetime.now(timezone.utc).isoformat()
    t2 = datetime.now(timezone.utc).isoformat()
    t3 = datetime.now(timezone.utc).isoformat()
    t4 = datetime.now(timezone.utc).isoformat()
    t5 = datetime.now(timezone.utc).isoformat()
    t6 = datetime.now(timezone.utc).isoformat()

    events = [
        # 1. Entered
        ViewerTelemetryEvent(
            event_id=f"e1_{journey_session}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.APP_OPEN,
            occurred_at=t0,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_type="PLATFORM",
            content_id="welele_pwa",
            environment="staging",
            is_test=False
        ),
        # 2. Discovered
        ViewerTelemetryEvent(
            event_id=f"e2_{journey_session}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.FEED_IMPRESSION,
            occurred_at=t1,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_type="CATALOG_FEED",
            content_id="home_feed",
            environment="staging",
            is_test=False
        ),
        # 3. Selected
        ViewerTelemetryEvent(
            event_id=f"e3_{journey_session}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.CONTENT_OPENED,
            occurred_at=t2,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_type="SERIES",
            content_id=series_id,
            series_id=series_id,
            environment="staging",
            is_test=False,
            metadata={"title": "Blood Ties"}
        ),
        # 4. Watched
        ViewerTelemetryEvent(
            event_id=f"e4_{journey_session}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=t3,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep1_id,
            series_id=series_id,
            episode_id=ep1_id,
            environment="staging",
            is_test=False
        ),
        # 5. Continued (Milestones)
        ViewerTelemetryEvent(
            event_id=f"e5_{journey_session}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=t4,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep1_id,
            series_id=series_id,
            episode_id=ep1_id,
            milestone_pct=25,
            position_seconds=22.5,
            environment="staging",
            is_test=False
        ),
        # 6. Engaged (Reaction)
        ViewerTelemetryEvent(
            event_id=f"e6_{journey_session}",
            event_family=EventSpineFamily.REACT,
            event_type=ViewerEventType.REACTION_ADDED,
            occurred_at=t4,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=series_id,
            series_id=series_id,
            environment="staging",
            is_test=False,
            metadata={"reaction_type": "LIKE"}
        ),
        # 7. Paywall
        ViewerTelemetryEvent(
            event_id=f"e7_{journey_session}",
            event_family=EventSpineFamily.CONTINUE,
            event_type=ViewerEventType.GATED_CONTENT_PRESENTED,
            occurred_at=t5,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep2_id,
            series_id=series_id,
            episode_id=ep2_id,
            environment="staging",
            is_test=False,
            metadata={"content_state": "LOCKED"}
        ),
        # 8. Payment Attempt
        ViewerTelemetryEvent(
            event_id=f"e8_{journey_session}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.PAYMENT_INITIATED,
            occurred_at=t5,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep2_id,
            series_id=series_id,
            episode_id=ep2_id,
            environment="staging",
            is_test=False,
            metadata={"method": "COINS", "cost": 5}
        ),
        # 9. Paid
        ViewerTelemetryEvent(
            event_id=f"e9_{journey_session}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.CONTENT_UNLOCKED,
            occurred_at=t6,
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep2_id,
            series_id=series_id,
            episode_id=ep2_id,
            environment="staging",
            is_test=False,
            metadata={"method": "COINS"}
        ),
        # 10. Continued after paying
        ViewerTelemetryEvent(
            event_id=f"e10_{journey_session}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=ep2_id,
            series_id=series_id,
            episode_id=ep2_id,
            environment="staging",
            is_test=False
        ),
        # 11. Returned
        ViewerTelemetryEvent(
            event_id=f"e11_{journey_session}",
            event_family=EventSpineFamily.RETURN,
            event_type=ViewerEventType.SESSION_RETURNED,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            session_id=journey_session,
            viewer_id=viewer_id,
            content_id=series_id,
            series_id=series_id,
            environment="staging",
            is_test=False
        ),
    ]

    # Ingest batch
    batch_res = client.post("/api/v1/telemetry/batch", json=[e.model_dump() for e in events])
    assert batch_res.status_code == 200
    assert batch_res.json()["recorded"] == len(events)

    # Auth admin
    admin_token = create_access_token(
        user_id="admin_test_p40",
        role="admin",
        market="ALL",
        kyc_status="SUPER_ADMIN"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Query funnel for staging environment
    funnel_res = client.get(
        f"/api/v1/admin/project40-funnel?environment=staging&series_id={series_id}",
        headers=admin_headers
    ).json()

    assert funnel_res["provenance"]["zero_synthetic_data"] is True
    assert funnel_res["provenance"]["has_data"] is True

    step_map = {s["key"]: s["sessions"] for s in funnel_res["funnel"]}
    assert step_map["ENTERED"] >= 1
    assert step_map["DISCOVERED"] >= 1
    assert step_map["SELECTED"] >= 1
    assert step_map["WATCHED"] >= 1
    assert step_map["CONTINUED"] >= 1
    assert step_map["ENGAGED"] >= 1
    assert step_map["PAYWALL"] >= 1
    assert step_map["PAYMENT_ATTEMPT"] >= 1
    assert step_map["PAID"] >= 1
    assert step_map["CONTINUED_POST_PAY"] >= 1
    assert step_map["RETURNED"] >= 1


def test_retention_agnostic_series_resolution_and_zero_synthetic():
    """
    Verifies that /creators/analytics/retention works against ANY series/episode
    without the hardcoded 'ep_bt_' prefix, and produces zero synthetic data when no events exist.
    """
    admin_token = create_access_token(
        user_id="admin_test_p40",
        role="admin",
        market="ALL",
        kyc_status="SUPER_ADMIN"
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Query for a series with 0 sessions
    res_zero = client.get(
        "/api/v1/creators/analytics/retention?series_id=story_empty_test_40&episode_number=1",
        headers=headers
    )
    assert res_zero.status_code == 200
    data_zero = res_zero.json()

    # Must NOT have fabricated starts=100 or completion=86.4%
    assert data_zero["total_starts"] == 0
    assert data_zero["completion_rate_pct"] == 0.0
    assert data_zero["cliffhanger_conversion_pct"] == 0.0
    assert len(data_zero["dropoff_curve"]) == 0
    assert len(data_zero["geo_distribution"]) == 0
    assert len(data_zero["telco_payment_mix"]) == 0

    # Also verify dynamic resolution for another series (Queen of Jozi resolves ep_qj_1, not hardcoded ep_bt_1)
    res_qj = client.get(
        "/api/v1/creators/analytics/retention?series_id=story_queen_of_jozi&episode_number=1",
        headers=headers
    )
    assert res_qj.status_code == 200
    data_qj = res_qj.json()
    assert data_qj["episode_id"] == "ep_qj_1"
    assert data_qj["series_id"] == "story_queen_of_jozi"
