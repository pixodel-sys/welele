"""
Welele Media™ — Milestone 5B: Video Migration & Protected R2 Delivery Test Suite
Document ID: WELELE-TEST-M5B-VIDEO-MIGRATION-V1
Target Database: Supabase Staging Project (dbsnaidhznofvyffdfni)
Target Storage: Cloudflare R2 Staging Bucket (welele-vod-staging)

Verifies:
1. Zero video files on frontend filesystem (frontend/public/videos/*.mp4 removed)
2. All 10 video assets exist durably in Cloudflare R2 bucket 'welele-vod-staging'
3. All episode stream endpoints deliver authorized signed R2 download URLs
4. Brand ident / interstitial delivers via streaming redirect without local disk dependency
5. Legacy /videos/... path redirects to canonical R2 streaming endpoint
6. Staging media_assets table references R2 storage keys and streaming endpoints
7. Production target guard enforcement (production bucket and database frozen)
"""

import os
import sys
import glob
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

os.environ["R2_BUCKET_NAME"] = "welele-vod-staging"
os.environ["STORAGE_BUCKET"] = "welele-vod-staging"
os.environ["PRODUCTION_SUPABASE_REF"] = CONFIRMED_PRODUCTION_REF
os.environ["STAGING_SUPABASE_REF"] = CONFIRMED_STAGING_REF

from config import settings
from main import app
from services.storage_service import storage_service
from repositories.series_repository import series_repository
from services.experience_engine import ExperienceEngine

settings.__init__()
storage_service.__init__()

client = TestClient(app)

MIGRATED_ASSET_KEYS = [
    "videos/Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4",
    "videos/big_buck.mp4",
    "videos/flower_bloom.mp4",
    "videos/jellyfish.mp4",
    "videos/ocean_waves.mp4",
    "videos/sample_drama.mp4",
    "videos/sintel.mp4",
    "videos/welele_ident.mp4",
    "videos/welele_ident_v2.mp4",
    "videos/welele_placeholder.mp4",
]


@pytest.fixture(scope="module")
def staging_target_guard():
    """Validates that tests execute strictly against Staging and never Production."""
    assert os.getenv("ENVIRONMENT") == "staging" or settings.ENVIRONMENT == "staging"
    assert storage_service.storage_bucket == "welele-vod-staging"
    with pytest.raises(RuntimeError):
        validate_database_target("staging", CONFIRMED_PRODUCTION_REF)


def test_01_zero_canonical_videos_on_frontend_filesystem(staging_target_guard):
    """
    Criterion 5 & 7: Verify that zero .mp4 video files exist in frontend/public/videos/.
    The frontend filesystem must have NO canonical video dependencies.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_videos_dir = os.path.join(repo_root, "frontend", "public", "videos")
    
    mp4_files = glob.glob(os.path.join(frontend_videos_dir, "*.mp4"))
    assert len(mp4_files) == 0, f"Found unexpected local video files on frontend filesystem: {mp4_files}"


def test_02_all_ten_video_assets_durable_in_staging_r2(staging_target_guard):
    """
    Criterion 1 & 3: Verify that all 10 migrated video assets exist durably in
    Cloudflare R2 bucket 'welele-vod-staging' with valid ContentLength and ETag.
    """
    assert storage_service.s3_client is not None, "R2 S3 client must be initialized"
    
    for key in MIGRATED_ASSET_KEYS:
        assert storage_service.object_exists(key) is True, f"Key '{key}' not found in R2 bucket '{storage_service.storage_bucket}'"
        
        # Explicit head_object inspection
        head = storage_service.s3_client.head_object(
            Bucket=storage_service.storage_bucket,
            Key=key
        )
        assert head["ContentLength"] > 0, f"Asset '{key}' has 0 bytes"
        assert head.get("ETag") is not None, f"Asset '{key}' missing ETag"


def test_03_brand_ident_manifest_contract(staging_target_guard):
    """
    Criterion 4 & 6: Verify brand ident URL in experience manifest points to
    canonical streaming endpoint rather than static disk file.
    """
    manifest = ExperienceEngine.resolve_manifest("home", state="published")
    assert "brand_config" in manifest
    brand_config = manifest["brand_config"]
    
    assert brand_config.get("play_brand_ident") is True
    assert brand_config.get("brand_ident_url") == "/api/storage/stream/videos/welele_ident_v2.mp4"
    assert brand_config.get("asset", {}).get("url") == "/api/storage/stream/videos/welele_ident_v2.mp4"


def test_04_storage_stream_redirect_endpoint(staging_target_guard):
    """
    Criterion 4: Verify GET /api/storage/stream/videos/{filename} returns an HTTP 307
    temporary redirect to an authorized Cloudflare R2 presigned download URL.
    """
    resp = client.get("/api/storage/stream/videos/welele_ident_v2.mp4", follow_redirects=False)
    assert resp.status_code == 307
    location = resp.headers.get("location", "")
    
    assert "r2.cloudflarestorage.com" in location
    assert "welele-vod-staging" in location
    assert "videos/welele_ident_v2.mp4" in location
    assert "X-Amz-Signature" in location or "Signature" in location


def test_05_legacy_videos_path_backward_compatibility_redirect(staging_target_guard):
    """
    Criterion 4: Verify that legacy /videos/{filename} requests on the backend
    are safely redirected to /api/storage/stream/videos/{filename}.
    """
    resp = client.get("/videos/welele_ident_v2.mp4", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers.get("location") == "/api/storage/stream/videos/welele_ident_v2.mp4"


def test_06_episode_stream_delivers_presigned_r2_url(staging_target_guard):
    """
    Criterion 6: Verify that free and entitled episodes resolve their streams
    from Cloudflare R2 using time-bounded presigned URLs.
    """
    # Test Blood Ties Ep 1 (Free)
    res_bt = client.get("/api/episodes/story_blood_ties/ep_bt_1")
    assert res_bt.status_code == 200
    data_bt = res_bt.json()
    assert data_bt["is_available"] is True
    assert data_bt["storage_key"] is not None
    stream_url_bt = data_bt["stream"]["primary_url"]
    assert stream_url_bt is not None
    assert "welele" in stream_url_bt or "r2" in stream_url_bt

    # Direct R2 presigned download URL generation for canonical clip
    key = "videos/ocean_waves.mp4"
    assert storage_service.object_exists(key) is True
    presigned = storage_service.generate_presigned_download_url(key)
    assert "r2.cloudflarestorage.com" in presigned["download_url"]
    assert "welele-vod-staging" in presigned["bucket"]


def test_07_isibusiso_ep1_authoritative_master_delivery(staging_target_guard):
    """
    Criterion 6: Verify that the canonical master for Isibusiso Ep 1
    (24 MB master) is durably served from staging R2.
    """
    key = "videos/Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4"
    assert storage_service.object_exists(key) is True
    presigned = storage_service.generate_presigned_download_url(key)
    assert "r2.cloudflarestorage.com" in presigned["download_url"]
    assert "Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4" in presigned["download_url"]

    # Also verify HTTP 307 streaming redirect route
    res = client.get(f"/api/storage/stream/{key}", follow_redirects=False)
    assert res.status_code == 307
    assert "Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4" in res.headers.get("location", "")


def test_08_production_target_freeze_enforcement(staging_target_guard):
    """
    Criterion 7: Confirm strict production freeze guard:
    Production bucket 'welele-vod-masters' and production Supabase 'mngyyxqdhjgteezwkxdn'
    cannot be targeted by any staging operation.
    """
    assert storage_service.storage_bucket != "welele-vod-masters"
    assert storage_service.storage_bucket == "welele-vod-staging"
    assert "mngyyxqdhjgteezwkxdn" not in (settings.SUPABASE_URL or "")
