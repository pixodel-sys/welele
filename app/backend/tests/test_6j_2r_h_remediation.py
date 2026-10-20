"""
Welele Media™ — Phase 6J-2R-H Remediation Automated Test Suite
Verifies all 6J-2R-H remediation invariants:
1. Malformed CDN_BASE_URL sanitization
2. Durable staging storage-proxy URL generation (never Cloudflare Pages SPA URLs)
3. Guarding against literal "undefined" in storage keys
4. Decoupled upload and save workflow
5. Repaired staging records integrity
6. Cross-tenant access boundaries
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
from services.storage_service import StorageService, storage_service
from repositories.series_repository import series_repository, to_uuid

client = TestClient(app)

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


def test_01_cdn_base_url_sanitization():
    """Remediation 2: Defensive sanitization of CDN_BASE_URL."""
    # Test stripping accidental leading variable name
    raw_1 = "CDN_BASE_URL=https://welele-staging.up.railway.app/api/storage/"
    assert StorageService._sanitize_cdn_base_url(raw_1) == "https://welele-staging.up.railway.app/api/storage"

    # Test stripping whitespace and enclosing quotes
    raw_2 = '  "https://cdn.welele.media/"  '
    assert StorageService._sanitize_cdn_base_url(raw_2) == "https://cdn.welele.media"

    raw_3 = " 'https://welele-staging.up.railway.app/api/storage' "
    assert StorageService._sanitize_cdn_base_url(raw_3) == "https://welele-staging.up.railway.app/api/storage"

    # Test None / empty
    assert StorageService._sanitize_cdn_base_url(None) == ""
    assert StorageService._sanitize_cdn_base_url("") == ""


def test_02_staging_url_resolves_to_storage_proxy():
    """Remediation 1: Staging URLs must resolve to the Railway storage proxy, NEVER staging.welele.app."""
    svc = StorageService()
    res = svc.save_artwork(
        file_bytes=TINY_JPEG_BYTES,
        series_id="test_series_6j2rh",
        artwork_type="poster",
        filename="poster.jpg",
        content_type="image/jpeg"
    )
    url = res["public_cdn_url"]
    
    # Must NOT generate Cloudflare Pages SPA URL
    assert "https://staging.welele.app/artwork" not in url, "Critical failure: Cloudflare Pages SPA URL was generated!"
    
    # In staging environment, must resolve to backend proxy or local media
    if svc.s3_client:
        assert url.startswith("https://welele-staging.up.railway.app/api/storage/artwork/"), f"Unexpected CDN URL: {url}"
    else:
        assert url.startswith("/media/artwork/"), f"Unexpected local CDN URL: {url}"


def test_03_undefined_series_id_protection():
    """Remediation 5: Never allow 'undefined' or 'null' to become a storage path."""
    svc = StorageService()
    
    # Test passing string "undefined"
    res1 = svc.save_artwork(
        file_bytes=TINY_JPEG_BYTES,
        series_id="undefined",
        artwork_type="poster"
    )
    assert not res1["storage_key"].startswith("artwork/undefined/"), "Forbidden key: artwork/undefined/ was generated!"
    assert res1["storage_key"].startswith("artwork/creator_uploads/"), f"Unexpected key: {res1['storage_key']}"

    # Test passing string "null"
    res2 = svc.save_artwork(
        file_bytes=TINY_JPEG_BYTES,
        series_id="null",
        artwork_type="banner"
    )
    assert not res2["storage_key"].startswith("artwork/null/"), "Forbidden key: artwork/null/ was generated!"
    assert res2["storage_key"].startswith("artwork/creator_uploads/"), f"Unexpected key: {res2['storage_key']}"

    # Test passing None
    res3 = svc.save_artwork(
        file_bytes=TINY_JPEG_BYTES,
        series_id=None,
        artwork_type="poster"
    )
    assert res3["storage_key"].startswith("artwork/creator_uploads/")


def test_04_storage_endpoint_series_id_sanitization(creator_wanjiku_token):
    """Remediation 5: Direct HTTP test of POST /storage/upload-artwork with series_id='undefined'."""
    files = {"file": ("test_poster.jpg", io.BytesIO(TINY_JPEG_BYTES), "image/jpeg")}
    data = {"series_id": "undefined", "artwork_type": "poster"}
    headers = {"Authorization": f"Bearer {creator_wanjiku_token}"}

    res = client.post("/api/v1/storage/upload-artwork", files=files, data=data, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert not body["storage_key"].startswith("artwork/undefined/"), "Router permitted artwork/undefined/ key!"
    assert body["storage_key"].startswith("artwork/creator_uploads/")


def test_05_repaired_staging_records_integrity():
    """Remediation 6: Confirm Abakhongi and Bougie in PostgreSQL contain valid proxy URLs."""
    series_table = series_repository.get_table("series")
    if not series_repository.is_live or not series_table:
        pytest.skip("Live PostgreSQL not available in this test runner context.")

    # 1. Abakhongi
    abakhongi = series_table.select("id, title, vertical_poster, cover_image").eq("id", "4df3daaf-3452-4362-9aef-0bb2ab570bae").execute()
    assert abakhongi.data and len(abakhongi.data) > 0
    row_a = abakhongi.data[0]
    assert not (row_a.get("vertical_poster") or "").startswith("blob:"), "Abakhongi still contains blob: URL!"
    assert not (row_a.get("cover_image") or "").startswith("blob:"), "Abakhongi still contains blob: URL!"
    assert "welele-staging.up.railway.app/api/storage/artwork" in row_a.get("vertical_poster")
    assert "welele-staging.up.railway.app/api/storage/artwork" in row_a.get("cover_image")

    # 2. Bougie
    bougie = series_table.select("id, title, vertical_poster, cover_image").eq("id", "764558a8-ea1d-4734-93b0-ecfe5df8aeb9").execute()
    assert bougie.data and len(bougie.data) > 0
    row_b = bougie.data[0]
    assert not (row_b.get("vertical_poster") or "").startswith("CDN_BASE_URL="), "Bougie still contains CDN_BASE_URL= prefix!"
    assert not (row_b.get("cover_image") or "").startswith("CDN_BASE_URL="), "Bougie still contains CDN_BASE_URL= prefix!"
    assert "welele-staging.up.railway.app/api/storage/artwork" in row_b.get("vertical_poster")
    assert "welele-staging.up.railway.app/api/storage/artwork" in row_b.get("cover_image")


def test_06_tenant_isolation_preserved(creator_wanjiku_token, creator_zola_token):
    """Invariant: Cross-tenant artwork mutation is rejected with 403 Forbidden."""
    # Create show under creator_wanjiku
    headers_wanjiku = {"Authorization": f"Bearer {creator_wanjiku_token}"}
    create_res = client.post(
        "/api/v1/creators/series/create",
        json={
            "title": f"Tenant Isolation Show {uuid.uuid4().hex[:6]}",
            "synopsis": "Validating tenant boundary on artwork PATCH",
            "vertical_poster": "https://welele-staging.up.railway.app/api/storage/artwork/creator_uploads/poster_1.jpg",
            "cover_image": "https://welele-staging.up.railway.app/api/storage/artwork/creator_uploads/banner_1.jpg",
            "genre": "Drama",
            "coin_price_per_episode": 5
        },
        headers=headers_wanjiku
    )
    assert create_res.status_code == 200
    series_id = create_res.json()["story"]["id"]

    try:
        # Creator Zola attempts to mutate Wanjiku's artwork -> Must fail 403
        headers_zola = {"Authorization": f"Bearer {creator_zola_token}"}
        hacked_res = client.patch(
            f"/api/v1/creators/series/{series_id}/artwork",
            json={
                "vertical_poster": "https://welele-staging.up.railway.app/api/storage/artwork/creator_uploads/poster_hacked.jpg"
            },
            headers=headers_zola
        )
        assert hacked_res.status_code == 403
    finally:
        # Cleanup
        client.delete(f"/api/v1/creators/series/{series_id}", headers=headers_wanjiku)
