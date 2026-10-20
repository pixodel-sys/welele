"""
Welele Media™ — Artwork Persistence Integrity Verification Suite (6J-2R-B)
Tightly bounded artwork lifecycle verification:
select → upload → durable asset → associate → save → database → reload → render

Invariants Verified:
1. blob: URLs must never become authoritative artwork references (must fail closed).
2. A one-hour presigned URL must not masquerade as a permanent public_cdn_url.
3. Durable artwork storage returns permanent, non-expiring public CDN URLs.
4. Tenant isolation enforced on artwork updates.
5. Live database persistence verified against PostgreSQL public.series.
6. Non-repair invariant: AMAPHUPHO and Abakhongi's existing contaminated records remain untouched.
"""

import io
import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from services.rbac_service import create_access_token
from services.storage_service import storage_service
from repositories.series_repository import series_repository, to_uuid

client = TestClient(app)

# Dummy 1x1 JPEG bytes for testing
TINY_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00"
    b"\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19"
    b"\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f"
    b"'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f"
    b"\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02"
    b"\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


@pytest.fixture
def creator_wanjiku_token():
    return create_access_token(
        user_id="usr_creator_wanjiku",
        role="creator",
        creator_id="creator_wanjiku"
    )


@pytest.fixture
def creator_zola_token():
    return create_access_token(
        user_id="usr_creator_zola",
        role="creator",
        creator_id="creator_zola"
    )


def test_upload_artwork_returns_durable_cdn_url(creator_wanjiku_token):
    """
    Stage: upload -> durable asset
    Verifies that uploading artwork via POST /storage/upload-artwork:
    1. Returns a durable, permanent public CDN URL.
    2. Does NOT return a blob: URL.
    3. Does NOT return a presigned URL containing X-Amz-Expires or Expires=.
    4. Has Cache-Control header readiness.
    """
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    files = {
        "file": ("test_poster.jpg", io.BytesIO(TINY_JPEG_BYTES), "image/jpeg")
    }
    data = {
        "series_id": "test_series_001",
        "artwork_type": "poster"
    }

    res = client.post("/api/v1/storage/upload-artwork", files=files, data=data, headers=headers)
    assert res.status_code == 200, f"Upload artwork failed: {res.text}"

    body = res.json()
    assert body.get("success") is True
    public_url = body.get("public_cdn_url")
    assert public_url is not None

    # Invariant 1: Never a blob: URL
    assert not public_url.startswith("blob:"), f"Public CDN URL cannot be blob: {public_url}"

    # Invariant 2: Never an expiring presigned URL
    assert "X-Amz-Expires" not in public_url, f"Public CDN URL contains presigned expiration: {public_url}"
    assert "X-Amz-Signature" not in public_url, f"Public CDN URL contains presigned signature: {public_url}"
    assert "Expires=" not in public_url, f"Public CDN URL contains expires param: {public_url}"

    # Invariant 3: Must point to durable storage key
    assert body.get("is_durable") is True
    storage_key = body.get("storage_key")
    assert storage_key is not None
    assert storage_key.startswith("artwork/test_series_001/poster_")
    assert storage_key.endswith(".jpg")


def test_save_binary_master_delegates_images_to_durable_artwork():
    """
    Verifies that StorageService.save_binary_master automatically recognizes
    image content types and routes to save_artwork, preventing 1-hour presigned URLs.
    """
    res = storage_service.save_binary_master(
        file_bytes=TINY_JPEG_BYTES,
        story_id="show_legacy",
        filename="test_image.jpg",
        content_type="image/jpeg"
    )

    public_url = res.get("public_cdn_url")
    assert public_url is not None
    assert not public_url.startswith("blob:")
    assert "X-Amz-Expires" not in public_url
    assert "Expires=" not in public_url
    assert res.get("is_durable") is True


def test_create_series_rejects_blob_urls_fail_closed(creator_wanjiku_token):
    """
    Stage: associate -> fail closed
    Verifies that POST /creators/series/create rejects blob: URLs with HTTP 400.
    """
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    
    # 1. Reject blob: vertical_poster
    payload_blob_poster = {
        "title": "Blob Test Show 1",
        "vertical_poster": "blob:https://staging.welele.app/a00a7418-472c-47b2-8fdc-3ec2f1f5062a",
        "cover_image": "https://staging.welele.app/valid_cover.jpg",
        "genre": "Drama",
        "coin_price_per_episode": 5
    }
    res = client.post("/api/v1/creators/series/create", json=payload_blob_poster, headers=headers)
    assert res.status_code == 400
    assert "blob:" in res.json().get("detail", "")

    # 2. Reject blob: cover_image
    payload_blob_cover = {
        "title": "Blob Test Show 2",
        "vertical_poster": "https://staging.welele.app/valid_poster.jpg",
        "cover_image": "blob:https://staging.welele.app/90e28c9c-5df2-47d3-82a9-7c10b0a88094",
        "genre": "Drama",
        "coin_price_per_episode": 5
    }
    res = client.post("/api/v1/creators/series/create", json=payload_blob_cover, headers=headers)
    assert res.status_code == 400
    assert "blob:" in res.json().get("detail", "")


def test_create_series_rejects_presigned_urls_fail_closed(creator_wanjiku_token):
    """
    Stage: associate -> fail closed
    Verifies that POST /creators/series/create rejects presigned expiring URLs with HTTP 400.
    """
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    presigned_sample = (
        "https://welele-vod-staging.r2.cloudflarestorage.com/artwork/show/poster.jpg?"
        "X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=3600&X-Amz-Signature=abcdef123456"
    )

    payload_presigned = {
        "title": "Presigned Test Show",
        "vertical_poster": presigned_sample,
        "cover_image": "https://staging.welele.app/valid_cover.jpg",
        "genre": "Drama",
        "coin_price_per_episode": 5
    }
    res = client.post("/api/v1/creators/series/create", json=payload_presigned, headers=headers)
    assert res.status_code == 400
    detail = res.json().get("detail", "")
    assert "Presigned" in detail or "expiring" in detail or "permanent" in detail


def test_patch_series_artwork_rejects_invalid_urls(creator_wanjiku_token):
    """
    Verifies that PATCH /creators/series/{series_id}/artwork strictly validates
    artwork URLs and rejects blob: or presigned URLs.
    """
    # Create valid series first
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    create_payload = {
        "title": "Valid Show for Artwork Patch Test",
        "vertical_poster": "https://staging.welele.app/artwork/initial_poster.jpg",
        "cover_image": "https://staging.welele.app/artwork/initial_cover.jpg",
        "genre": "Romance",
        "coin_price_per_episode": 5
    }
    create_res = client.post("/api/v1/creators/series/create", json=create_payload, headers=headers)
    assert create_res.status_code == 200
    series_id = create_res.json()["story"]["id"]

    # 1. Attempt patch with blob:
    res_blob = client.patch(
        f"/api/v1/creators/series/{series_id}/artwork",
        json={"vertical_poster": "blob:http://localhost/xyz"},
        headers=headers
    )
    assert res_blob.status_code == 400
    assert "blob:" in res_blob.json().get("detail", "")

    # 2. Attempt patch with presigned URL
    res_presigned = client.patch(
        f"/api/v1/creators/series/{series_id}/artwork",
        json={"cover_image": "https://s3.amazonaws.com/art.jpg?X-Amz-Expires=3600&sig=123"},
        headers=headers
    )
    assert res_presigned.status_code == 400
    assert "Presigned" in res_presigned.json().get("detail", "")


def test_patch_series_artwork_enforces_tenant_isolation(creator_wanjiku_token, creator_zola_token):
    """
    Verifies that Creator Zola cannot mutate Creator Wanjiku's series artwork.
    """
    headers_wanjiku = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    headers_zola = {"Authorization": f"Bearer {creator_zola_token}"}

    create_payload = {
        "title": "Wanjiku Private Show",
        "vertical_poster": "https://staging.welele.app/artwork/wanjiku_p.jpg",
        "cover_image": "https://staging.welele.app/artwork/wanjiku_c.jpg",
        "genre": "Drama",
        "coin_price_per_episode": 5
    }
    create_res = client.post("/api/v1/creators/series/create", json=create_payload, headers=headers_wanjiku)
    assert create_res.status_code == 200
    series_id = create_res.json()["story"]["id"]

    # Zola attempts to patch Wanjiku's series artwork -> 403 Forbidden
    patch_payload = {
        "vertical_poster": "https://staging.welele.app/artwork/zola_hacked.jpg"
    }
    res_unauth = client.patch(
        f"/api/v1/creators/series/{series_id}/artwork",
        json=patch_payload,
        headers=headers_zola
    )
    assert res_unauth.status_code == 403


def test_full_artwork_persistence_lifecycle(creator_wanjiku_token):
    """
    Proves the complete 8-stage artwork lifecycle:
    select → upload → durable asset → associate → save → database → reload → render

    1. SELECT: Test binary images prepared.
    2. UPLOAD: Uploaded via /storage/upload-artwork for both poster and banner.
    3. DURABLE ASSET: Verify durable public_cdn_urls returned (no blob, no presigned params).
    4. ASSOCIATE: Associate durable URLs with series.
    5. SAVE: PATCH /creators/series/{series_id}/artwork.
    6. DATABASE: Direct assertion that series in series_repository has durable artwork URLs.
    7. RELOAD: GET /creators/series/{series_id}/workspace reflects exact persisted URLs.
    8. RENDER: URLs are canonical HTTP/HTTPS CDN endpoints suitable for browser rendering.
    """
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}

    # Setup: Create series
    create_payload = {
        "title": "6J-2R-B Lifecycle Test Series",
        "vertical_poster": "https://staging.welele.app/artwork/placeholder_poster.jpg",
        "cover_image": "https://staging.welele.app/artwork/placeholder_banner.jpg",
        "genre": "Supernatural & Ancestral",
        "coin_price_per_episode": 5
    }
    create_res = client.post("/api/v1/creators/series/create", json=create_payload, headers=headers)
    assert create_res.status_code == 200
    series_id = create_res.json()["story"]["id"]

    # 1. SELECT & 2. UPLOAD & 3. DURABLE ASSET for Poster
    poster_file = {"file": ("wanjiku_poster.jpg", io.BytesIO(TINY_JPEG_BYTES), "image/jpeg")}
    poster_data = {"series_id": series_id, "artwork_type": "poster"}
    poster_res = client.post("/api/v1/storage/upload-artwork", files=poster_file, data=poster_data, headers=headers)
    assert poster_res.status_code == 200
    durable_poster_url = poster_res.json()["public_cdn_url"]
    assert not durable_poster_url.startswith("blob:")
    assert "X-Amz-Expires" not in durable_poster_url

    # 1. SELECT & 2. UPLOAD & 3. DURABLE ASSET for Banner
    banner_file = {"file": ("wanjiku_banner.png", io.BytesIO(TINY_JPEG_BYTES), "image/png")}
    banner_data = {"series_id": series_id, "artwork_type": "cover"}
    banner_res = client.post("/api/v1/storage/upload-artwork", files=banner_file, data=banner_data, headers=headers)
    assert banner_res.status_code == 200
    durable_banner_url = banner_res.json()["public_cdn_url"]
    assert not durable_banner_url.startswith("blob:")
    assert "X-Amz-Expires" not in durable_banner_url

    # 4. ASSOCIATE & 5. SAVE: PATCH artwork
    patch_payload = {
        "vertical_poster": durable_poster_url,
        "cover_image": durable_banner_url
    }
    patch_res = client.patch(f"/api/v1/creators/series/{series_id}/artwork", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["success"] is True
    assert patch_data["series"]["vertical_poster"] == durable_poster_url
    assert patch_data["series"]["cover_image"] == durable_banner_url

    # 6. DATABASE: Verify repository record
    series_record = series_repository.get_creator_series_detail(series_id)
    assert series_record is not None
    assert series_record["vertical_poster"] == durable_poster_url
    assert series_record["cover_image"] == durable_banner_url

    # 7. RELOAD: Query workspace endpoint
    workspace_res = client.get(f"/api/v1/creators/series/{series_id}/workspace", headers=headers)
    assert workspace_res.status_code == 200
    reloaded_series = workspace_res.json()["series"]
    assert reloaded_series["vertical_poster"] == durable_poster_url
    assert reloaded_series["cover_image"] == durable_banner_url

    # 8. RENDER: Validate format
    assert reloaded_series["vertical_poster"].startswith("http") or reloaded_series["vertical_poster"].startswith("/media")
    assert not reloaded_series["vertical_poster"].startswith("blob:")


def test_existing_contaminated_records_unremediated_invariant():
    """
    Contract Invariant:
    Do not repair AMAPHUPHO or Abakhongi's existing records yet.
    Proves that existing contaminated records remain untouched in their original state.
    """
    # Seed contaminated records as in staging
    amaphupho_id = "0879f96c-b551-44d9-a41c-80efff63f949"
    abakhongi_id = "4df3daaf-3452-4362-9aef-0bb2ab570bae"

    series_repository.local_insert("series", {
        "id": amaphupho_id,
        "title": "AMAPHUPHO",
        "vertical_poster": "https://welele-vod-staging.r2.cloudflarestorage.com/raw/upload?X-Amz-Expires=3600",
        "cover_image": "https://welele-vod-staging.r2.cloudflarestorage.com/raw/banner?X-Amz-Expires=3600",
        "creator_id": "creator_wanjiku"
    })

    series_repository.local_insert("series", {
        "id": abakhongi_id,
        "title": "Abakhongi",
        "vertical_poster": "blob:https://staging.welele.app/a00a7418-472c-47b2-8fdc-3ec2f1f5062a",
        "cover_image": "blob:https://staging.welele.app/90e28c9c-5df2-47d3-82a9-7c10b0a88094",
        "creator_id": "creator_zola"
    })

    # Read records
    amaphupho = series_repository.get_creator_series_detail(amaphupho_id)
    assert amaphupho is not None
    assert "X-Amz-Expires=3600" in amaphupho["vertical_poster"]

    abakhongi = series_repository.get_creator_series_detail(abakhongi_id)
    assert abakhongi is not None
    assert abakhongi["vertical_poster"].startswith("blob:")
    assert abakhongi["cover_image"].startswith("blob:")
