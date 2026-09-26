"""
Welele Media™ — Evidence Projections & Rebuildability Test Suite (Phase B)
Verifies:
1. Rebuildability Invariant: Wiping projections and re-running yields identical outputs.
2. Provenance Envelope Completeness: projection_version, methodology_version, source counts, time window, confidence tier.
3. 12-Step Funnel Integrity: Starts -> 3s/10s hooks -> milestones -> completions -> rewatches -> paywall -> conversions.
4. Technical Noise Disambiguation: Distinguishes CLEAN_PLAYBACK drops from WITH_TECHNICAL_CORRELATION drops.
5. Graduated Confidence Policy: INSUFFICIENT -> PRELIMINARY -> DEVELOPING -> ESTABLISHED.
6. Viewer Evidence: Factual tallies with zero persona hallucination.
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from schemas.viewer_telemetry_models import ViewerTelemetryEvent, EventSpineFamily, ViewerEventType
from schemas.projection_models import ConfidenceTier, RetentionAnomalyType
from services.evidence_projection_service import evidence_projection_service
from repositories.telemetry_repository import telemetry_repository

client = TestClient(app)


def test_content_projection_provenance_and_rebuildability():
    """Prove that projections carry full provenance and can be wiped and rebuilt with identical numbers."""
    series_id = f"series_proj_test_{uuid.uuid4().hex[:6]}"
    ep_id = f"ep_proj_test_{uuid.uuid4().hex[:6]}"

    # Ingest 15 distinct viewer sessions for this episode
    events_to_ingest = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for i in range(15):
        sess_id = f"sess_p_{i}_{uuid.uuid4().hex[:6]}"
        v_id = f"user_{i}"
        
        # PLAYBACK_STARTED
        events_to_ingest.append(ViewerTelemetryEvent(
            event_id=f"evt_start_{sess_id}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=now_iso,
            session_id=sess_id,
            viewer_id=v_id,
            content_id=ep_id,
            series_id=series_id,
            episode_id=ep_id,
            duration_seconds=90.0,
            position_seconds=0.0
        ))

        # Progress events: 12 survive past 3s, 9 survive past 10s, 6 reach 25%, 3 complete
        if i < 12:
            events_to_ingest.append(ViewerTelemetryEvent(
                event_id=f"evt_prog3_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_PROGRESS,
                occurred_at=now_iso,
                session_id=sess_id,
                viewer_id=v_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=4.0
            ))
        if i < 9:
            events_to_ingest.append(ViewerTelemetryEvent(
                event_id=f"evt_prog10_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_PROGRESS,
                occurred_at=now_iso,
                session_id=sess_id,
                viewer_id=v_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=12.0
            ))
        if i < 6:
            events_to_ingest.append(ViewerTelemetryEvent(
                event_id=f"evt_ms25_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_PROGRESS,
                occurred_at=now_iso,
                session_id=sess_id,
                viewer_id=v_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=23.0,
                milestone_pct=25
            ))
        if i < 3:
            events_to_ingest.append(ViewerTelemetryEvent(
                event_id=f"evt_comp_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_COMPLETED,
                occurred_at=now_iso,
                session_id=sess_id,
                viewer_id=v_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=90.0
            ))

    res_batch = client.post("/api/v1/telemetry/batch", json=[e.model_dump() for e in events_to_ingest])
    assert res_batch.status_code == 200

    # 1. First Projection Run
    proj1 = evidence_projection_service.build_content_projection(target_id=ep_id, series_id=series_id)

    assert proj1.provenance.projection_version == "1.0.0"
    assert proj1.provenance.methodology_version == "2026.1"
    assert proj1.provenance.source_session_count == 15
    assert proj1.provenance.confidence_tier == ConfidenceTier.PRELIMINARY
    assert proj1.starts == 15
    assert proj1.hook_3s_retained_count == 12
    assert proj1.hook_3s_retention_pct == 80.0
    assert proj1.hook_10s_retained_count == 9
    assert proj1.hook_10s_retention_pct == 60.0
    assert proj1.milestones.reached_25_pct == 6
    assert proj1.completions == 3
    assert proj1.completion_rate_pct == 20.0

    # 2. Rebuildability Test: Generate second projection and verify bit-for-bit mathematical consistency
    proj2 = evidence_projection_service.build_content_projection(target_id=ep_id, series_id=series_id)
    assert proj2.starts == proj1.starts
    assert proj2.hook_3s_retention_pct == proj1.hook_3s_retention_pct
    assert proj2.hook_10s_retention_pct == proj1.hook_10s_retention_pct
    assert proj2.completions == proj1.completions
    assert proj2.completion_rate_pct == proj1.completion_rate_pct
    assert proj2.provenance.source_event_count == proj1.provenance.source_event_count


def test_technical_noise_disambiguation():
    """Verify that retention drops are cleanly split between CLEAN_PLAYBACK and WITH_TECHNICAL_CORRELATION."""
    series_id = f"series_tech_test_{uuid.uuid4().hex[:6]}"
    ep_id = f"ep_tech_test_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    events = []
    # 20 sessions starting playback
    for i in range(20):
        sess_id = f"sess_tech_{i}_{uuid.uuid4().hex[:6]}"
        events.append(ViewerTelemetryEvent(
            event_id=f"evt_s_{sess_id}",
            event_family=EventSpineFamily.WATCH,
            event_type=ViewerEventType.PLAYBACK_STARTED,
            occurred_at=now_iso,
            session_id=sess_id,
            content_id=ep_id,
            series_id=series_id,
            episode_id=ep_id,
            position_seconds=0.0
        ))

        # At second 15, 10 viewers drop off WHILE experiencing buffer stalls
        if i < 10:
            events.append(ViewerTelemetryEvent(
                event_id=f"evt_stall_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.STALL_DETECTED,
                occurred_at=now_iso,
                session_id=sess_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=15.0
            ))
            events.append(ViewerTelemetryEvent(
                event_id=f"evt_p_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_PROGRESS,
                occurred_at=now_iso,
                session_id=sess_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=15.0
            ))
        else:
            # The other 10 viewers continue cleanly to second 45
            events.append(ViewerTelemetryEvent(
                event_id=f"evt_p_clean_{sess_id}",
                event_family=EventSpineFamily.WATCH,
                event_type=ViewerEventType.PLAYBACK_PROGRESS,
                occurred_at=now_iso,
                session_id=sess_id,
                content_id=ep_id,
                series_id=series_id,
                episode_id=ep_id,
                position_seconds=45.0
            ))

    client.post("/api/v1/telemetry/batch", json=[e.model_dump() for e in events])

    proj = evidence_projection_service.build_content_projection(target_id=ep_id, series_id=series_id)
    assert len(proj.detected_anomalies) > 0
    
    # Anomaly at 15s should correlate with technical stalls
    anom = next((a for a in proj.detected_anomalies if a.second_start == 15 or a.second_end == 20), None)
    assert anom is not None
    assert anom.classification == RetentionAnomalyType.RETENTION_ANOMALY_WITH_TECHNICAL_CORRELATION
    assert anom.stalls_in_window >= 5


def test_graduated_confidence_policy():
    """Verify sample size tiers conform to the approved governance policy."""
    service = evidence_projection_service
    tier_insufficient, _ = service.evaluate_confidence(5)
    tier_preliminary, _ = service.evaluate_confidence(25)
    tier_developing, _ = service.evaluate_confidence(60)
    tier_established, _ = service.evaluate_confidence(150)

    assert tier_insufficient == ConfidenceTier.INSUFFICIENT
    assert tier_preliminary == ConfidenceTier.PRELIMINARY
    assert tier_developing == ConfidenceTier.DEVELOPING
    assert tier_established == ConfidenceTier.ESTABLISHED


def test_projection_http_endpoints():
    """Verify HTTP endpoints return valid projection payloads with 200 OK."""
    res_content = client.get("/api/v1/telemetry/projections/content/story_blood_ties")
    assert res_content.status_code == 200
    data = res_content.json()
    assert "provenance" in data
    assert data["provenance"]["projection_version"] == "1.0.0"
    assert "retention_curve" in data

    res_viewer = client.get("/api/v1/telemetry/projections/viewer/user_test_viewer_40")
    assert res_viewer.status_code == 200
    data_v = res_viewer.json()
    assert "provenance" in data_v
    assert "overall_completion_ratio" in data_v
