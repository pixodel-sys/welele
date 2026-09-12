"""
Welele Media™ — Media Production Worker & Resilience Test Suite (P0)
Tests: Asynchronous Media Jobs, Rendition Generations (1080p, 720p, 480p), Retry Logic, and Worker Failure Resilience.
"""

import sys
import os
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.series_repository import series_repository
from services.transcoding_service import transcoding_service

def test_media_worker_resilience():
    print("\n--- Running Media Production Worker & Resilience Tests ---")

    # Setup test media asset
    test_ep_id = f"ep_test_{uuid.uuid4().hex[:6]}"
    asset = series_repository.register_media_asset(
        episode_id=test_ep_id,
        master_video_url="https://r2.welele.tv/masters/scene_raw_01.mp4",
        thumbnail_url="https://r2.welele.tv/thumbs/poster_916.jpg"
    )
    asset_id = asset["id"]
    print(f"[PASS] Master Asset Ingestion: Registered media asset '{asset_id}' for episode '{test_ep_id}'.")

    # 1. Happy-Path Asynchronous Transcoding & Rendition Generation
    job = transcoding_service.dispatch_transcoding_job(
        media_asset_id=asset_id,
        provider="CloudflareStream",
        idempotency_key=f"idemp_media_{asset_id}"
    )
    job_id = job["id"]
    print(f"[PASS] Asynchronous Job Enqueue: Created media job '{job_id}' (Status: {job['status']}).")

    # Wait for asynchronous worker thread to complete
    completed_job = None
    for _ in range(30):
        completed_job = transcoding_service.get_job_status(job_id)
        if completed_job and completed_job.get("status") == "completed":
            break
        time.sleep(0.05)

    assert completed_job is not None
    assert completed_job["status"] == "completed"
    assert completed_job["attempt"] == 1
    print(f"[PASS] Worker Completion: Media job '{job_id}' completed with status '{completed_job['status']}'.")

    # Verify Renditions generated
    renditions = transcoding_service.get_asset_renditions(asset_id)
    assert len(renditions) == 3
    profiles = [r["profile"] for r in renditions]
    assert "1080p" in profiles
    assert "720p" in profiles
    assert "480p" in profiles
    print(f"[PASS] Rendition Profiles: Generated 3 HLS renditions ({', '.join(profiles)}).")

    # Verify media asset updated to ready with master manifest
    assets = series_repository.local_get("media_assets")
    updated_asset = next((a for a in assets if a["id"] == asset_id), None)
    assert updated_asset["status"] == "ready"
    assert "master.m3u8" in updated_asset.get("hls_master_manifest", "")
    print(f"[PASS] Asset State: Canonical media asset transitioned to 'ready' with HLS manifest '{updated_asset.get('hls_master_manifest')}'.")

    # 2. Failure-Path: Worker Transient Failure & Successful Retry
    retry_asset = series_repository.register_media_asset(
        episode_id=f"ep_retry_{uuid.uuid4().hex[:6]}",
        master_video_url="https://r2.welele.tv/masters/scene_retry.mp4"
    )
    retry_job = transcoding_service.dispatch_transcoding_job(
        media_asset_id=retry_asset["id"],
        max_retries=3,
        simulate_failure_attempts=1 # Fails on attempt 1, recovers on attempt 2
    )

    for _ in range(40):
        retry_job_status = transcoding_service.get_job_status(retry_job["id"])
        if retry_job_status and retry_job_status.get("status") == "completed":
            break
        time.sleep(0.05)

    assert retry_job_status is not None
    assert retry_job_status["status"] == "completed"
    assert retry_job_status["attempt"] == 2
    print(f"[PASS] Resilience Retry: Job '{retry_job['id']}' recovered from simulated worker error on attempt {retry_job_status['attempt']}.")


    # 3. Failure-Path: Permanent Failure (Max Retries Exceeded)
    fail_asset = series_repository.register_media_asset(
        episode_id=f"ep_fail_{uuid.uuid4().hex[:6]}",
        master_video_url="https://r2.welele.tv/masters/corrupt_video.mp4"
    )
    fail_job = transcoding_service.dispatch_transcoding_job(
        media_asset_id=fail_asset["id"],
        max_retries=2,
        simulate_failure_attempts=5 # Exceeds max retries
    )

    for _ in range(40):
        fail_job_status = transcoding_service.get_job_status(fail_job["id"])
        if fail_job_status and fail_job_status.get("status") == "failed":
            break
        time.sleep(0.05)

    assert fail_job_status is not None
    assert fail_job_status["status"] == "failed"
    assert fail_job_status["error"] is not None
    print(f"[PASS] Failure Isolation: Job '{fail_job['id']}' gracefully marked 'failed' after {fail_job_status['attempt']} retries without corrupting system.")


    print("=======================================================")
    print("ALL MEDIA PRODUCTION & RESILIENCE TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_media_worker_resilience()
