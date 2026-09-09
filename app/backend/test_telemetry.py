"""
Welele Media™ — Audience Telemetry & Event Ingestion Tests (GAP-004)
Validates: Event Ingestion (/api/events/track), heartbeat tracking, and calculated retention drop-off heatmaps.
"""

import sys
import os
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

client = TestClient(app)

def test_telemetry_and_retention_aggregation():
    print("\n--- Running Telemetry & Retention Aggregation Tests ---")

    test_session = f"sess_{uuid.uuid4().hex[:8]}"

    # 1. Ingest Viewing Telemetry Beacons
    beacons = [
        {"event_name": "episode_started", "session_id": test_session, "series_id": "story_blood_ties", "episode_id": "ep_bt_1", "playback_second": 0, "region_code": "ZA"},
        {"event_name": "heartbeat", "session_id": test_session, "series_id": "story_blood_ties", "episode_id": "ep_bt_1", "playback_second": 15, "region_code": "ZA"},
        {"event_name": "heartbeat", "session_id": test_session, "series_id": "story_blood_ties", "episode_id": "ep_bt_1", "playback_second": 30, "region_code": "ZA"},
        {"event_name": "cliffhanger_reached", "session_id": test_session, "series_id": "story_blood_ties", "episode_id": "ep_bt_1", "playback_second": 58, "region_code": "ZA"},
        {"event_name": "unlock_completed", "session_id": test_session, "series_id": "story_blood_ties", "episode_id": "ep_bt_1", "playback_second": 58, "region_code": "ZA"}
    ]

    for b in beacons:
        res = client.post("/api/events/track", json=b)
        assert res.status_code == 200
        assert res.json()["status"] == "accepted"

    print(f"[PASS] Event Ingestion: Dispatched {len(beacons)} telemetry beacons via POST /api/events/track.")

    # 2. Query Retention Telemetry
    res_ret = client.get("/api/events/retention/story_blood_ties/ep_bt_1")
    assert res_ret.status_code == 200
    ret_data = res_ret.json()
    assert ret_data["total_starts"] > 0
    assert len(ret_data["retention_curve"]) > 10
    assert ret_data["cliffhanger_conversion_pct"] > 0
    assert ret_data["retention_curve"][0]["second"] == 0
    assert ret_data["retention_curve"][0]["retention_pct"] == 100.0

    print(f"[PASS] Retention Calculation: Generated true retention curve across {len(ret_data['retention_curve'])} timecode intervals with {ret_data['cliffhanger_conversion_pct']}% cliffhanger conversion.")

    print("=======================================================")
    print("ALL TELEMETRY & RETENTION TESTS PASSED (100% SUCCESS)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_telemetry_and_retention_aggregation()
