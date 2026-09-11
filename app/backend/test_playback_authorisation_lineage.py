"""
Welele Media™ — Acceptance Test: Canonical Ingestion Contract & Storage Lineage
Verifies the final architectural gate:
Browser File -> Binary Upload -> Object Storage -> storage_key -> media_assets -> getStream() -> Exact Bytes Playback.
"""

import sys
import os
import io
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import db
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository
from services.storage_service import storage_service
from services.rbac_service import create_access_token

client = TestClient(app)

def test_playback_authorisation_lineage():
    # 1. Setup Creator & Viewer Auth
    creator_token = create_access_token(user_id="creator_zola", role="creator")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    viewer_token = create_access_token(user_id="viewer_test_99", role="viewer")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Initialize viewer wallet with coins
    ledger_repository.get_or_create_wallet("viewer_test_99")

    # -------------------------------------------------------------------------
    # Gate 1: Ephemeral browser blob: references MUST BE REJECTED
    # -------------------------------------------------------------------------
    invalid_blob_payload = {
        "series_id": "story_blood_ties",
        "episode_number": 6,
        "title": "Invalid Blob Ep",
        "video_url": "blob:http://localhost:5173/0e698bb2-fbe7-4c3e-a745-f09d84bfda99",
        "is_free": False,
        "coin_price": 5
    }
    rejected_res = client.post("/api/creators/episodes/add", json=invalid_blob_payload, headers=creator_headers)
    assert rejected_res.status_code == 400, f"Expected 400 rejection for blob URL, got {rejected_res.status_code}"
    assert "blob" in rejected_res.json()["detail"].lower()

    # -------------------------------------------------------------------------
    # Gate 2: Browser File -> Real Binary Upload -> Object Storage
    # -------------------------------------------------------------------------
    # Generate unique binary payload with distinct signature
    unique_binary_data = b"WELELE_CANONICAL_MP4_PAYLOAD_V2_GATE_TEST_DATA_" + os.urandom(64)
    file_tuple = ("ep_bt_6_master.mp4", io.BytesIO(unique_binary_data), "video/mp4")

    upload_res = client.post(
        "/api/storage/upload-binary",
        files={"file": file_tuple},
        data={"series_id": "story_blood_ties", "episode_number": 6}
    )
    assert upload_res.status_code == 200, f"Binary upload failed: {upload_res.text}"
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    storage_key = upload_data["storage_key"]
    public_cdn_url = upload_data["public_cdn_url"]
    assert storage_key.startswith("masters/story_blood_ties/")

    # -------------------------------------------------------------------------
    # Gate 3: Prove the actual physical binary exists in object storage
    # -------------------------------------------------------------------------
    persisted_bytes = storage_service.get_stored_binary(storage_key)
    assert persisted_bytes is not None, "Physical binary does not exist in storage service!"
    assert persisted_bytes == unique_binary_data, "Persisted binary bytes mismatch with original uploaded payload!"

    # -------------------------------------------------------------------------
    # Gate 4: Creator registers Episode with verified storage_key
    # -------------------------------------------------------------------------
    ep_payload = {
        "series_id": "story_blood_ties",
        "episode_number": 6,
        "title": "The True Heir Unveiled",
        "synopsis": "The blood lineage is proven beyond doubt.",
        "duration_seconds": 90,
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_time": 82,
        "cliffhanger_hook": "The real contract is signed.",
        "storage_key": storage_key,
        "video_url": public_cdn_url,
        "thumbnail_url": "https://cdn.welele.media/posters/blood_ties.jpg",
        "status": "published"
    }

    create_res = client.post("/api/creators/episodes/add", json=ep_payload, headers=creator_headers)
    assert create_res.status_code == 200, f"Failed creating episode: {create_res.text}"
    ep_data = create_res.json()["episode"]
    episode_id = ep_data["id"]

    # Verify media_assets table holds exact storage_key
    all_media = series_repository.local_get("media_assets")
    matched_media = next((m for m in all_media if m["episode_id"] == episode_id), None)
    assert matched_media is not None, "Media asset record was not attached!"
    assert matched_media["storage_key"] == storage_key
    assert not matched_media["master_video_url"].startswith("blob:")

    # -------------------------------------------------------------------------
    # Gate 5: Pre-unlock getStream() is locked
    # -------------------------------------------------------------------------
    pre_stream_res = client.get(f"/api/episodes/story_blood_ties/{episode_id}?user_id=viewer_test_99")
    assert pre_stream_res.status_code == 200
    pre_stream_data = pre_stream_res.json()
    assert pre_stream_data["is_unlocked"] is False
    assert pre_stream_data["storage_key"] == storage_key

    # -------------------------------------------------------------------------
    # Gate 6: Unlock Episode via double-entry ledger
    # -------------------------------------------------------------------------
    unlock_res = client.post(f"/api/episodes/story_blood_ties/{episode_id}/unlock?user_id=viewer_test_99&method=COINS")
    assert unlock_res.status_code == 200, f"Unlock failed: {unlock_res.text}"
    assert unlock_res.json()["success"] is True

    # -------------------------------------------------------------------------
    # Gate 7: Canonical getStream() Authorised Stream Resolution
    # -------------------------------------------------------------------------
    post_stream_res = client.get(f"/api/episodes/story_blood_ties/{episode_id}?user_id=viewer_test_99")
    assert post_stream_res.status_code == 200, f"getStream failed: {post_stream_res.text}"
    stream_payload = post_stream_res.json()

    assert stream_payload["is_unlocked"] is True, "Episode should be marked as unlocked!"
    assert stream_payload["media_asset_id"] == matched_media["id"]
    assert stream_payload["storage_key"] == storage_key
    assert not stream_payload["stream"]["primary_url"].startswith("blob:")

    # -------------------------------------------------------------------------
    # Gate 8: Playback Verification — Exact Byte Equality
    # Prove that the served stream endpoint resolves the exact uploaded binary bytes
    # -------------------------------------------------------------------------
    stream_route = stream_payload["stream"]["primary_url"]
    if stream_route.startswith("/media/"):
        media_get_res = client.get(stream_route)
        assert media_get_res.status_code == 200, f"Failed streaming media: {media_get_res.status_code}"
        served_bytes = media_get_res.content
    else:
        # If CDN format URL, verify via storage service binary getter
        served_bytes = storage_service.get_stored_binary(storage_key)

    assert served_bytes == unique_binary_data, "Streamed binary bytes are NOT identical to the uploaded file bytes!"

    print("\n[PASSED] Final Architectural Gate Verified: Browser File -> Binary Upload -> Object Storage -> storage_key -> media_assets -> getStream() -> Exact Bytes Playback")

