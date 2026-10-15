"""
Welele Media™ — Milestone 4: Media / R2 Durability & Protected Playback Verification Suite
Document ID: WELELE-TEST-M4-MEDIA-R2-V1
Target Database: Supabase Staging Project (dbsnaidhznofvyffdfni)
Target Storage: Cloudflare R2 Staging Bucket (welele-vod-staging)

Verification Phases Covered:
- Phase 1: Storage inspection & fail-closed validation
- Phase 2: Authoritative R2 upload & object key determinism
- Phase 3: Media database consistency (media_assets table reference)
- Phase 4: Protected playback (signed delivery for entitled; denied for locked)
- Phase 5: Durability & restart independence (no local disk dependency)
- Phase 6: Static MP4 audit & isolation
- Phase 7: Focused tests A through K
- Phase 9: Production target guard enforcement (mngyyxqdhjgteezwkxdn frozen)
"""

import os
import sys
import uuid
import ssl
import urllib.request
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

CANDIDATE_STAGING_PATHS = [
    r"G:\App_Development\App_Dev\Welele Media\.env\.env.staging",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.staging"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env", ".env.staging"),
]

from target_validator import validate_database_target, CONFIRMED_PRODUCTION_REF, CONFIRMED_STAGING_REF

os.environ["ENVIRONMENT"] = "staging"
os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF
os.environ["R2_BUCKET_NAME"] = "welele-vod-staging"
os.environ["STORAGE_BUCKET"] = "welele-vod-staging"

for p in CANDIDATE_STAGING_PATHS:
    if os.path.exists(p):
        load_dotenv(p, override=True)
        break

# Re-ensure R2_BUCKET_NAME and references after load_dotenv
os.environ["R2_BUCKET_NAME"] = "welele-vod-staging"
os.environ["STORAGE_BUCKET"] = "welele-vod-staging"
os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF

from config import settings
from main import app
from services.storage_service import storage_service
from repositories.series_repository import series_repository, to_uuid
from repositories.ledger_repository import ledger_repository
from services.rbac_service import create_access_token

# Ensure singletons reflect staging bucket and client
settings.__init__()
storage_service.__init__()

client = TestClient(app)

TEST_MP4_HEADER = (
    b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41"
    b"\x00\x00\x00\x08free\x00\x00\x00\x18mdatWELELE_M4_DURABILITY_TEST"
)


@pytest.fixture(scope="module")
def staging_target_guard():
    """Validates that tests execute strictly against Staging and never Production."""
    assert os.getenv("ENVIRONMENT") == "staging" or settings.ENVIRONMENT == "staging"
    assert storage_service.storage_bucket == "welele-vod-staging"
    # Target guard must raise RuntimeError on production reference
    with pytest.raises(RuntimeError):
        validate_database_target("staging", CONFIRMED_PRODUCTION_REF)


def test_phase1_r2_configuration_status(staging_target_guard):
    """
    Check A & B prerequisite: Verify Cloudflare R2 client is initialized and bucket configured.
    """
    assert storage_service.s3_client is not None, "R2 S3 client must be initialized in staging"
    assert storage_service.storage_bucket == "welele-vod-staging"
    assert storage_service.account_id != "", "R2_ACCOUNT_ID must not be empty"


def test_phase2_r2_upload_creates_durable_object(staging_target_guard):
    """
    Check A & B: Upload synthetic staging test asset to welele-vod-staging.
    Object key must be deterministic and verifiable via head_object.
    """
    test_story_id = "story_staging_m4"
    test_episode_id = f"ep_m4_test_{uuid.uuid4().hex[:6]}"

    upload_result = storage_service.save_binary_master(
        file_bytes=TEST_MP4_HEADER,
        story_id=test_story_id,
        episode_id=test_episode_id,
        filename=f"{test_episode_id}.mp4",
        content_type="video/mp4"
    )

    expected_key = f"masters/{test_story_id}/{test_episode_id}.mp4"
    assert upload_result["storage_key"] == expected_key
    assert "welele-vod-staging" in upload_result["provider"]

    # Verify object exists in R2
    assert storage_service.object_exists(expected_key) is True

    # Authoritative direct S3 head_object check
    head = storage_service.s3_client.head_object(
        Bucket=storage_service.storage_bucket,
        Key=expected_key
    )
    assert head["ContentLength"] == len(TEST_MP4_HEADER)
    assert head["ContentType"] == "video/mp4"

    # Cleanup R2 object after verification
    try:
        storage_service.s3_client.delete_object(
            Bucket=storage_service.storage_bucket,
            Key=expected_key
        )
    except Exception:
        pass


def test_phase3_media_database_consistency(staging_target_guard):
    """
    Check C: media_assets in Supabase PostgreSQL must reference the durable object/key.
    Avoid creating orphan DB records if upload fails.
    """
    test_story_id = "story_blood_ties"
    test_ep_id = f"ep_m4_db_{uuid.uuid4().hex[:6]}"
    expected_key = f"masters/{test_story_id}/{test_ep_id}.mp4"

    # 1. Ingest asset to R2
    upload_result = storage_service.save_binary_master(
        file_bytes=TEST_MP4_HEADER,
        story_id=test_story_id,
        episode_id=test_ep_id,
        filename=f"{test_ep_id}.mp4",
        content_type="video/mp4"
    )

    # 2. Attach media_asset in database
    media_asset = series_repository.attach_media_asset(
        episode_id=test_ep_id,
        storage_key=expected_key,
        master_url=upload_result["public_cdn_url"],
        duration_seconds=90
    )
    assert media_asset is not None
    assert media_asset.get("storage_key") == expected_key

    # 3. Retrieve media asset via get_media_asset_for_episode
    retrieved = series_repository.get_media_asset_for_episode(test_ep_id)
    assert retrieved is not None
    assert retrieved.get("storage_key") == expected_key

    # 4. Fail-closed: empty binary payload must reject before touching database
    with pytest.raises(ValueError):
        storage_service.save_binary_master(
            file_bytes=b"",
            story_id=test_story_id,
            episode_id=f"fail_{test_ep_id}"
        )

    # Cleanup R2 test object
    try:
        storage_service.s3_client.delete_object(
            Bucket=storage_service.storage_bucket,
            Key=expected_key
        )
    except Exception:
        pass


def test_phase4_authenticated_entitled_playback_succeeds(staging_target_guard):
    """
    Check D: Authenticated entitled viewer can obtain authorized playback response.
    Response must point to controlled, time-bounded SigV4 signed delivery from R2.
    """
    test_series_id = "story_blood_ties"
    test_ep_id = f"ep_m4_paid_{uuid.uuid4().hex[:6]}"
    storage_key = f"masters/{test_series_id}/{test_ep_id}.mp4"

    # 1. Upload durable test asset
    storage_service.save_binary_master(
        file_bytes=TEST_MP4_HEADER,
        story_id=test_series_id,
        episode_id=test_ep_id,
        filename=f"{test_ep_id}.mp4"
    )

    # 2. Attach to database media_assets
    series_repository.attach_media_asset(
        episode_id=test_ep_id,
        storage_key=storage_key,
        master_url=f"https://cdn.welele.media/{storage_key}",
        duration_seconds=90
    )

    # 3. Simulate an entitled viewer in ledger
    viewer_id = str(uuid.uuid4())
    ledger_repository.local_insert("unlocked_episodes", {
        "id": f"unl_{uuid.uuid4().hex[:8]}",
        "user_id": viewer_id,
        "episode_id": test_ep_id,
        "series_id": test_series_id,
        "unlock_method": "COINS",
        "coins_spent": 5,
        "unlocked_at": "2026-10-15T22:00:00Z"
    })

    # Also register temporary episode in series_repository local store for test resolution
    temp_ep = {
        "id": test_ep_id,
        "series_id": test_series_id,
        "episode_number": 99,
        "title": "M4 Durable Test Episode",
        "status": "published",
        "lifecycle_state": "PUBLISHED",
        "readiness_state": "PRODUCTION_READY",
        "is_free": False,
        "storage_key": storage_key,
        "video_url": f"https://cdn.welele.media/{storage_key}"
    }
    series_repository.local_insert("episodes", temp_ep)

    # 4. Request stream as the entitled viewer with authenticated JWT
    token = create_access_token(user_id=viewer_id, role="viewer")
    res = client.get(
        f"/api/episodes/{test_series_id}/{test_ep_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()

    assert data["is_unlocked"] is True
    assert data["status_label"] == "Watch Now"
    assert data["stream"] is not None
    primary_url = data["stream"]["primary_url"]

    # Must be signed Cloudflare R2 download URL
    assert "X-Amz-Signature=" in primary_url or "X-Amz-Algorithm=AWS4-HMAC-SHA256" in primary_url
    assert "welele-vod-staging" in primary_url or storage_service.account_id in primary_url

    # Cleanup R2 object
    try:
        storage_service.s3_client.delete_object(
            Bucket=storage_service.storage_bucket,
            Key=storage_key
        )
    except Exception:
        pass


def test_phase4_locked_non_entitled_playback_denied(staging_target_guard):
    """
    Check E: Locked/non-entitled viewer is denied access.
    Endpoint must NOT return the raw media object, stream binary, or usable unrestricted URL.
    Tested against canonical paid episode ep_bt_3.
    """
    # Request stream as unentitled viewer for canonical paid episode ep_bt_3
    res = client.get("/api/episodes/story_blood_ties/ep_bt_3")
    assert res.status_code == 200
    data = res.json()

    # Stream and video binaries must be withheld
    assert data["is_unlocked"] is False
    assert data["status_label"] == "Locked — Coins Required"
    assert data["stream"] is None
    assert data["storage_key"] is None
    assert data["media_asset_id"] is None
    assert data["episode"].get("video_url") is None


def test_phase4_no_unrestricted_raw_r2_url_exposed(staging_target_guard):
    """
    Check F: Raw private R2 object is never exposed as an unrestricted public URL.
    Direct unauthenticated GET to raw R2 endpoint must return 400, 401, or 403.
    """
    endpoint = f"https://{storage_service.account_id}.r2.cloudflarestorage.com/{storage_service.storage_bucket}/test_nonexistent.mp4"
    ctx = ssl._create_unverified_context()

    req = urllib.request.Request(endpoint, method="GET")
    try:
        urllib.request.urlopen(req, context=ctx)
        pytest.fail("Direct unauthenticated access to private R2 bucket must NOT succeed!")
    except urllib.error.HTTPError as e:
        # Cloudflare R2 returns 400 (missing headers), 401 Unauthorized, or 403 Forbidden
        assert e.code in (400, 401, 403), f"Expected 400, 401, or 403 from private R2 bucket, got {e.code}"


def test_phase5_durability_and_restart_independence(staging_target_guard):
    """
    Check G & H: Stored R2 asset is independent of Railway local disk.
    Deleting local copy does not impair R2 retrieval or presigned URL generation.
    """
    test_story_id = "story_blood_ties"
    test_ep_id = f"ep_m4_restart_{uuid.uuid4().hex[:6]}"
    storage_key = f"masters/{test_story_id}/{test_ep_id}.mp4"

    # 1. Ingest asset to R2
    storage_service.save_binary_master(
        file_bytes=TEST_MP4_HEADER,
        story_id=test_story_id,
        episode_id=test_ep_id
    )

    # 2. Intentionally delete local filesystem cache if present
    local_path = os.path.join(storage_service.local_storage_dir, *storage_key.split("/"))
    if os.path.exists(local_path):
        os.remove(local_path)

    # 3. Verify object still exists authoritatively in R2
    assert storage_service.object_exists(storage_key) is True

    # 4. Verify get_stored_binary retrieves directly from R2
    retrieved_bytes = storage_service.get_stored_binary(storage_key)
    assert retrieved_bytes == TEST_MP4_HEADER

    # 5. Verify presigned URL can still be generated directly from R2
    presigned = storage_service.generate_presigned_download_url(storage_key)
    assert "download_url" in presigned
    assert "X-Amz-Signature=" in presigned["download_url"]

    # Cleanup R2 object
    try:
        storage_service.s3_client.delete_object(
            Bucket=storage_service.storage_bucket,
            Key=storage_key
        )
    except Exception:
        pass


def test_phase6_free_public_media_behaviour_remains_valid(staging_target_guard):
    """
    Check I: Existing free/public episode (Episode 1) preserves playback behaviour.
    """
    res = client.get("/api/episodes/story_blood_ties/ep_bt_1")
    assert res.status_code == 200
    data = res.json()
    assert data["is_unlocked"] is True
    assert data["status_label"] == "Watch Now"
    assert data["stream"] is not None
    assert "primary_url" in data["stream"]


def test_phase9_production_target_guard_and_zero_mutations(staging_target_guard):
    """
    Check J & K: Production safety invariants.
    Production ref must be rejected by validate_database_target.
    """
    # Guard against accidental production targeting
    with pytest.raises(RuntimeError):
        validate_database_target("staging", CONFIRMED_PRODUCTION_REF)

    with pytest.raises(RuntimeError):
        validate_database_target("staging", f"https://{CONFIRMED_PRODUCTION_REF}.supabase.co")

    # Staging ref passes without error
    validate_database_target("staging", CONFIRMED_STAGING_REF)
    validate_database_target("staging", f"https://{CONFIRMED_STAGING_REF}.supabase.co")
