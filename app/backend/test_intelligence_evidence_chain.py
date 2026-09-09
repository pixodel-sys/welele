"""
Welele Media™ — Intelligence Evidence Chain & Diagnostic Test Suite (P2)
Tests: Telemetry Noise Filtering (Buffering vs Narrative Drops), Versioned Evidence Artifact Creation,
Confidence Threshold Gating, and Story Forge Contextual Guidance.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.event_repository import event_repository
from services.analytics_service import analytics_service
from services.intelligence_service import intelligence_service

def test_intelligence_evidence_chain():
    print("\n--- Running Intelligence Evidence Chain & Diagnostic Tests ---")

    test_series = "story_blood_ties"
    test_ep = f"ep_intel_{uuid.uuid4().hex[:6]}"

    # 1. Ingest Synthetic Telemetry Beacons: Clean Sessions with Drop at second 42
    # Ingest 10 sessions starting at 0s, 6 dropping at 42s, 4 finishing to end
    for i in range(10):
        sess_id = f"sess_clean_{i}"
        # All 10 start
        event_repository.ingest_event({
            "event_name": "episode_started", "session_id": sess_id,
            "series_id": test_series, "episode_id": test_ep, "playback_second": 0, "region_code": "ZA"
        })
        event_repository.ingest_event({
            "event_name": "heartbeat", "session_id": sess_id,
            "series_id": test_series, "episode_id": test_ep, "playback_second": 20, "region_code": "ZA"
        })
        # 4 sessions continue past second 42 to cliffhanger
        if i < 4:
            event_repository.ingest_event({
                "event_name": "heartbeat", "session_id": sess_id,
                "series_id": test_series, "episode_id": test_ep, "playback_second": 45, "region_code": "ZA"
            })
            event_repository.ingest_event({
                "event_name": "cliffhanger_reached", "session_id": sess_id,
                "series_id": test_series, "episode_id": test_ep, "playback_second": 65, "region_code": "ZA"
            })

    print(f"[PASS] Synthetic Playback Ingestion: Dispatched clean viewing beacons across 10 viewer sessions.")

    # 2. Run Analytics & Signal Correlation
    analysis = analytics_service.analyze_episode_performance(test_series, test_ep)
    assert analysis["total_views"] >= 10
    drops = analysis["detected_drops"]
    assert len(drops) > 0
    clean_drop = drops[0]
    assert clean_drop["classification"] == "CONFIRMED_NARRATIVE_DROP"
    assert clean_drop["confidence_score"] >= 0.70
    print(f"[PASS] Signal Correlation: Classified pacing drop ({clean_drop['drop_percentage']}% at {clean_drop['time_range']}) as 'CONFIRMED_NARRATIVE_DROP' (Confidence: {clean_drop['confidence_score']}).")

    # 3. Generate Versioned Evidence Artifact (Amendment 4)
    result = intelligence_service.generate_episode_diagnostic_evidence(
        ip_id="ip_blood_ties",
        series_id=test_series,
        episode_id=test_ep
    )
    evidence = result["evidence"]
    recommendation = result["recommendation"]

    assert evidence["id"] is not None
    assert evidence["analysis_version"] == "v2.1-evidence"
    assert evidence["sample_size"] >= 10
    assert recommendation is not None
    assert recommendation["confidence"] >= 0.70
    assert recommendation["evidence_id"] == evidence["id"]
    print(f"[PASS] Evidence Artifact: Generated immutable evidence record '{evidence['id']}' with recommendation '{recommendation['id']}'.")

    # 4. Confounding Factor Test: Buffering Spike Masquerading as Narrative Drop
    buffering_ep = f"ep_buffer_{uuid.uuid4().hex[:6]}"
    for i in range(10):
        sess_b = f"sess_buf_{i}"
        event_repository.ingest_event({
            "event_name": "episode_started", "session_id": sess_b,
            "series_id": test_series, "episode_id": buffering_ep, "playback_second": 0, "region_code": "ZA"
        })
        event_repository.ingest_event({
            "event_name": "heartbeat", "session_id": sess_b,
            "series_id": test_series, "episode_id": buffering_ep, "playback_second": 20, "region_code": "ZA"
        })
        # Simulate heavy network rebuffering stall at second 35
        event_repository.ingest_event({
            "event_name": "buffer_start", "session_id": sess_b,
            "series_id": test_series, "episode_id": buffering_ep, "playback_second": 35, "region_code": "ZA"
        })

    buf_analysis = analytics_service.analyze_episode_performance(test_series, buffering_ep)
    buf_drops = buf_analysis["detected_drops"]
    if buf_drops:
        assert buf_drops[0]["classification"] == "TECHNICAL_BUFFERING"
        assert buf_drops[0]["confidence_score"] < 0.70
        print(f"[PASS] Confounding Filter: Correctly identified buffering anomaly as 'TECHNICAL_BUFFERING' and lowered confidence to {buf_drops[0]['confidence_score']}.")

    # 5. Story Forge Context Injection
    sf_context = intelligence_service.get_story_forge_context(test_series)
    assert sf_context["has_recommendations"] is True
    assert "revelation" in sf_context["prompt_directive"].lower() or "drop" in sf_context["prompt_directive"].lower()
    print(f"[PASS] Story Forge Integration: Actionable directive prepared for prompt engine: \"{sf_context['prompt_directive'][:80]}...\"")

    print("=======================================================")
    print("ALL INTELLIGENCE EVIDENCE CHAIN TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_intelligence_evidence_chain()
