"""
Welele Media™ — Asynchronous Media Transcoding & HLS Production Pipeline (P0)
Handles out-of-band video processing, multi-bitrate ladder encoding (1080p, 720p, 480p),
and multivariant HLS manifest generation while decoupling media jobs from canonical media assets.
"""

import os
import sys
import uuid
import time
import asyncio
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories.series_repository import series_repository

class TranscodingProfile:
    PROFILES = [
        {"profile": "1080p", "width": 1080, "height": 1920, "bitrate": 3500000, "label": "High 9:16"},
        {"profile": "720p", "width": 720, "height": 1280, "bitrate": 1800000, "label": "Standard Mobile 9:16"},
        {"profile": "480p", "width": 480, "height": 854, "bitrate": 800000, "label": "Data-Saver Mzansi 9:16"}
    ]

class TranscodingService:
    def __init__(self):
        self._active_jobs: Dict[str, threading.Thread] = {}

    def dispatch_transcoding_job(
        self,
        media_asset_id: str,
        provider: str = "CloudflareStream",
        idempotency_key: Optional[str] = None,
        max_retries: int = 3,
        simulate_failure_attempts: int = 0
    ) -> Dict[str, Any]:
        """
        Creates and enqueues an asynchronous media transcoding job outside FastAPI request lifecycles.
        """
        # Create media job record
        job = series_repository.create_media_job(
            media_asset_id=media_asset_id,
            provider=provider,
            idempotency_key=idempotency_key
        )

        # Update media asset status to processing
        series_repository.update_media_asset_status(media_asset_id, status="processing")

        # Start asynchronous background thread worker
        worker_thread = threading.Thread(
            target=self._run_transcoding_worker,
            args=(job["id"], media_asset_id, max_retries, simulate_failure_attempts),
            daemon=True
        )
        self._active_jobs[job["id"]] = worker_thread
        worker_thread.start()

        return job

    def _run_transcoding_worker(
        self,
        job_id: str,
        media_asset_id: str,
        max_retries: int,
        simulate_failure_attempts: int
    ):
        """
        Asynchronous worker executing transcoding, handling retries, and recording renditions.
        """
        attempt = 1
        while attempt <= max_retries:
            try:
                series_repository.update_media_job(job_id, status="processing", attempt=attempt)

                # Simulate transcoding processing latency
                time.sleep(0.05)

                # Check if simulated failure is triggered for resilience testing
                if attempt <= simulate_failure_attempts:
                    raise RuntimeError(f"Transcoding worker transient network error (attempt {attempt}/{max_retries})")

                # Successful encoding: generate renditions
                for p in TranscodingProfile.PROFILES:
                    profile_name = p["profile"]
                    rendition_url = f"https://cdn.welele.tv/renditions/{media_asset_id}_{profile_name}.m3u8"
                    series_repository.add_rendition(
                        media_asset_id=media_asset_id,
                        profile=profile_name,
                        width=p["width"],
                        height=p["height"],
                        bitrate=p["bitrate"],
                        playlist_url=rendition_url
                    )

                master_manifest = f"https://cdn.welele.tv/hls/{media_asset_id}_master.m3u8"

                # Mark media job as completed
                series_repository.update_media_job(job_id, status="completed", attempt=attempt)

                # Mark canonical media asset as ready
                series_repository.update_media_asset_status(
                    media_asset_id=media_asset_id,
                    status="ready",
                    hls_manifest_url=master_manifest
                )
                return

            except Exception as e:
                if attempt >= max_retries:
                    # Job permanently failed
                    series_repository.update_media_job(job_id, status="failed", attempt=attempt, error=str(e))
                    series_repository.update_media_asset_status(media_asset_id, status="failed")
                    return
                else:
                    attempt += 1
                    time.sleep(0.02)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return series_repository.get_media_job(job_id)

    def get_asset_renditions(self, media_asset_id: str) -> List[Dict[str, Any]]:
        return series_repository.get_renditions_for_asset(media_asset_id)

transcoding_service = TranscodingService()
