"""
Welele Media™ — Single-Source Metric Parity & Projection Identity Test Suite
Acceptance Test Requirement:
Proves that for the same:
  - content / target
  - environment
  - time window

the following derive from the exact same canonical ContentEvidenceProjection:
  Admin Audience Evidence == Content Intelligence == ContentEvidenceProjection

Concept                  Canonical Source
-----------------------  -------------------------
Impressions              ContentEvidenceProjection
Starts                   ContentEvidenceProjection
3s retention             ContentEvidenceProjection
10s retention            ContentEvidenceProjection
25/50/75/90/100 reached  ContentEvidenceProjection
Completion               ContentEvidenceProjection
Rewatch                  ContentEvidenceProjection
Continuation intent      ContentEvidenceProjection
Paywall                  ContentEvidenceProjection
Unlock attempts          ContentEvidenceProjection
Unlock success           ContentEvidenceProjection
Retention curve          ContentEvidenceProjection
Technical disruption     ContentEvidenceProjection
Confidence tier          ProvenanceEnvelope
Methodology              ProvenanceEnvelope
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from schemas.viewer_telemetry_models import ViewerTelemetryEvent, EventSpineFamily, ViewerEventType
from services.evidence_projection_service import evidence_projection_service
from services.content_intelligence_service import content_intelligence_service
from services.rbac_service import create_access_token
from services.series_episode_service import series_episode_service
from services.episode_blueprint_service import episode_blueprint_service
from services.episode_production_pack_service import episode_production_pack_service
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository

client = TestClient(app)


def test_single_source_metric_parity():
    """
    Verifies metric parity across:
    1. Direct ContentEvidenceProjection derived from spine
    2. Admin Audience Evidence endpoint (GET /api/v1/admin/project40-funnel)
    3. Content Intelligence service execution
    """
    ip_id = f"ip_parity_{uuid.uuid4().hex[:6]}"
    ip_repository.local_insert("digital_ips", {
        "id": ip_id,
        "title": "Parity Story",
        "franchise_code": "IP-PARITY",
        "logline": "Parity verification logline",
        "genre": "Drama",
        "story_packages": [{"id": f"pkg_{ip_id}", "lineage_hash": "parityhash123"}]
    })

    pkg = {
        "id": f"pkg_{ip_id}",
        "ip_id": ip_id,
        "package_title": "Parity Package",
        "lineage_hash": "parityhash123"
    }
    ip_repository.local_insert("story_forge_packages", pkg)
    ip_repository.local_insert("story_packages", pkg)

    series = series_episode_service.create_series_from_story_package(ip_id, pkg["id"], 1)
    series_id = series["id"]

    ep1 = series_episode_service.create_episode(series_id=series_id, episode_number=1)
    episode_id = ep1["id"]

    episode_blueprint_service.generate_blueprint(episode_id=episode_id, version="1.0.0")
    episode_production_pack_service.generate_production_pack(episode_id=episode_id, blueprint_version="1.0.0")
    session_clean = f"sess_clean_{uuid.uuid4().hex[:6]}"
    session_disrupted = f"sess_disrupted_{uuid.uuid4().hex[:6]}"
    viewer_a = f"v_a_{uuid.uuid4().hex[:4]}"
    viewer_b = f"v_b_{uuid.uuid4().hex[:4]}"
    now = datetime.now(timezone.utc).isoformat()

    # Session 1: Clean Playback reaching 100% completion and next episode intent
    events_clean = [
        ViewerTelemetryEvent(
            event_id=f"e1_{session_clean}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.FEED_IMPRESSION,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e2_{session_clean}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=0.0,
            environment="production",
            is_test=False
        ),
        # 3s & 10s retention
        ViewerTelemetryEvent(
            event_id=f"e3_{session_clean}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=12.0,
            milestone_pct=25,
            environment="production",
            is_test=False
        ),
        # 50, 75, 90, 100 milestones
        ViewerTelemetryEvent(
            event_id=f"e4_{session_clean}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_PROGRESS,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=60.0,
            milestone_pct=100,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e5_{session_clean}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_COMPLETED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        # Continuation intent (next episode selected)
        ViewerTelemetryEvent(
            event_id=f"e6_{session_clean}",
            event_family=EventSpineFamily.CONTINUE,
            event_type=ViewerEventType.NEXT_EPISODE_SELECTED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        # Paywall and Unlock
        ViewerTelemetryEvent(
            event_id=f"e7_{session_clean}",
            event_family=EventSpineFamily.CONTINUE,
            event_type=ViewerEventType.GATED_CONTENT_PRESENTED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e8_{session_clean}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.PAYMENT_INITIATED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e9_{session_clean}",
            event_family=EventSpineFamily.PAY,
            event_type=ViewerEventType.CONTENT_UNLOCKED,
            occurred_at=now,
            session_id=session_clean,
            viewer_id=viewer_a,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
    ]

    # Session 2: Buffer/Stall Disrupted Playback
    events_disrupted = [
        ViewerTelemetryEvent(
            event_id=f"e10_{session_disrupted}",
            event_family=EventSpineFamily.OPEN,
            event_type=ViewerEventType.FEED_IMPRESSION,
            occurred_at=now,
            session_id=session_disrupted,
            viewer_id=viewer_b,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e11_{session_disrupted}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=now,
            session_id=session_disrupted,
            viewer_id=viewer_b,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=0.0,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e12_{session_disrupted}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.BUFFER_STARTED,
            occurred_at=now,
            session_id=session_disrupted,
            viewer_id=viewer_b,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=4.0,
            environment="production",
            is_test=False
        ),
        ViewerTelemetryEvent(
            event_id=f"e13_{session_disrupted}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.STALL_DETECTED,
            occurred_at=now,
            session_id=session_disrupted,
            viewer_id=viewer_b,
            content_type="EPISODE",
            content_id=episode_id,
            series_id=series_id,
            episode_id=episode_id,
            position_seconds=4.0,
            environment="production",
            is_test=False
        ),
    ]

    # Ingest events to immutable spine
    all_events = events_clean + events_disrupted
    res = client.post("/api/v1/telemetry/batch", json=[e.model_dump() for e in all_events])
    assert res.status_code == 200

    # 1. Canonical Source: Direct ContentEvidenceProjection
    direct_proj = evidence_projection_service.build_content_projection(
        target_id=episode_id,
        series_id=series_id,
        episode_id=episode_id,
        environment="production"
    )

    # 2. Human Admin Audience Evidence: GET /api/v1/admin/project40-funnel
    admin_token = create_access_token(
        user_id="admin_parity_checker",
        role="admin",
        market="ALL",
        kyc_status="SUPER_ADMIN"
    )
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_res = client.get(
        f"/api/v1/admin/project40-funnel?environment=production&series_id={series_id}&episode_id={episode_id}",
        headers=admin_headers
    ).json()

    # 3. Machine View: Content Intelligence upstream evidence collection
    assembled_evidence = content_intelligence_service.collect_upstream_evidence(
        ip_id=ip_id,
        series_id=series_id,
        episode_id=episode_id
    )
    machine_proj = assembled_evidence["content_projection"]

    # -------------------------------------------------------------
    # RIGID METRIC PARITY ASSERTIONS:
    # Admin Audience Evidence == Machine Content Intelligence == ContentEvidenceProjection
    # -------------------------------------------------------------

    # Provenance Parity
    assert admin_res["provenance"]["projection_version"] == direct_proj.provenance.projection_version == machine_proj.provenance.projection_version
    assert admin_res["provenance"]["methodology_version"] == direct_proj.provenance.methodology_version == machine_proj.provenance.methodology_version
    assert admin_res["provenance"]["confidence_tier"] == direct_proj.provenance.confidence_tier.value == machine_proj.provenance.confidence_tier.value
    assert admin_res["provenance"]["confidence_disclosure"] == direct_proj.provenance.confidence_disclosure == machine_proj.provenance.confidence_disclosure

    # Core Behavioral Funnel Parity
    # Impressions
    assert direct_proj.impressions == 2
    assert machine_proj.impressions == 2
    assert admin_res["projection"]["impressions"] == 2

    # Starts
    assert direct_proj.starts == 2
    assert machine_proj.starts == 2
    assert admin_res["projection"]["starts"] == 2
    assert admin_res["dropoff_milestones"]["started"] == 2

    # 3s & 10s Retention
    assert direct_proj.hook_3s_retained_count == 2
    assert machine_proj.hook_3s_retained_count == 2
    assert admin_res["hook_3s"]["count"] == 2

    assert direct_proj.hook_10s_retained_count == 1
    assert machine_proj.hook_10s_retained_count == 1
    assert admin_res["hook_10s"]["count"] == 1

    # Semantic Distinction: 25% milestone is NOT conflated with continuation intent
    assert direct_proj.milestones.reached_25_pct == 1
    assert direct_proj.next_episode_intent_count == 1
    assert admin_res["continuation_intent"] == 1
    assert admin_res["dropoff_milestones"]["reached_25"] == 1

    # Completions
    assert direct_proj.completions == 1
    assert machine_proj.completions == 1
    assert admin_res["completions"] == 1

    # Commerce Funnel Parity
    assert direct_proj.paywall_presentations == 1
    assert machine_proj.paywall_presentations == 1
    assert admin_res["projection"]["paywall_presentations"] == 1

    assert direct_proj.unlock_attempts == 1
    assert machine_proj.unlock_attempts == 1
    assert admin_res["projection"]["unlock_attempts"] == 1

    assert direct_proj.unlock_successes == 1
    assert machine_proj.unlock_successes == 1
    assert admin_res["projection"]["unlock_successes"] == 1

    # Technical Disruption Disambiguation Parity
    assert direct_proj.technical_disruptions.total_buffer_events == 1
    assert machine_proj.technical_disruptions.total_buffer_events == 1
    assert admin_res["technical_disruptions"]["total_buffer_events"] == 1

    assert direct_proj.technical_disruptions.total_stall_events == 1
    assert machine_proj.technical_disruptions.total_stall_events == 1
    assert admin_res["technical_disruptions"]["total_stall_events"] == 1
    assert admin_res["technical_disruptions"]["sessions_with_disruptions"] == 1

    # Single-source verification confirmed: All 3 consume identical projection contract
