"""
WELELE MEDIA — PHASE 6O-5 FORENSIC VERIFICATION SUITE
Media Streaming & Storage Access Gateway Authorization

Verifies:
1. Unauthenticated client cannot stream paid episodes (HTTP 401).
2. Authenticated viewer without entitlement cannot stream paid episodes (HTTP 402).
3. Authenticated viewer with verified entitlement receives short-lived (60s TTL) playback token.
4. Free published episodes are accessible for streaming.
5. Unreleased/draft episodes return HTTP 403 even if storage key is known.
6. Direct raw master streaming via GET /storage/stream/masters/* is forbidden (HTTP 403).
7. Direct streaming of unallowlisted/private assets is forbidden (HTTP 403).
8. Allowlisted public marketing/ident assets remain streamable (HTTP 307).
9. Non-existent series/episodes return HTTP 404.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database import db
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository
from services.rbac_service import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_media_catalog():
    """Seeds test series, episodes, and entitlements in memory."""
    # 1. Seed Published Series with Free and Paid Episodes
    series_repository.local_insert("series", {
        "id": "ser_6o5_catalog",
        "slug": "ser_6o5_catalog",
        "title": "6O-5 Test Series",
        "free_episodes": 1,
        "status": "published"
    })

    # Ep 1: Free & Published
    series_repository.local_insert("episodes", {
        "id": "ep_6o5_free",
        "slug": "ep_6o5_free",
        "series_id": "ser_6o5_catalog",
        "episode_number": 1,
        "title": "Episode 1 (Free)",
        "is_free": True,
        "status": "published",
        "lifecycle_state": "PUBLISHED",
        "storage_key": "masters/ser_6o5_catalog/ep_6o5_free.mp4",
        "video_url": "/videos/ocean_waves.mp4"
    })

    # Ep 2: Paid & Published
    series_repository.local_insert("episodes", {
        "id": "ep_6o5_paid",
        "slug": "ep_6o5_paid",
        "series_id": "ser_6o5_catalog",
        "episode_number": 2,
        "title": "Episode 2 (Paid)",
        "is_free": False,
        "status": "published",
        "lifecycle_state": "PUBLISHED",
        "storage_key": "masters/ser_6o5_catalog/ep_6o5_paid.mp4",
        "video_url": "/videos/ocean_waves.mp4"
    })

    # Ep 3: Draft / Unreleased
    series_repository.local_insert("episodes", {
        "id": "ep_6o5_draft",
        "slug": "ep_6o5_draft",
        "series_id": "ser_6o5_catalog",
        "episode_number": 3,
        "title": "Episode 3 (Draft)",
        "is_free": False,
        "status": "draft",
        "lifecycle_state": "DRAFT",
        "is_empty_draft": False,
        "storage_key": "masters/ser_6o5_catalog/ep_6o5_draft.mp4",
        "video_url": "/videos/ocean_waves.mp4"
    })

    # Ep 4: Empty Draft
    series_repository.local_insert("episodes", {
        "id": "ep_6o5_empty",
        "slug": "ep_6o5_empty",
        "series_id": "ser_6o5_catalog",
        "episode_number": 4,
        "title": "Episode 4 (Empty Draft)",
        "is_free": False,
        "status": "draft",
        "is_empty_draft": True,
        "storage_key": "masters/ser_6o5_catalog/ep_6o5_empty.mp4"
    })

    yield

@pytest.fixture
def viewer_token():
    return create_access_token(user_id="usr_viewer_6o5_active", role="viewer")

@pytest.fixture
def unentitled_viewer_token():
    return create_access_token(user_id="usr_viewer_6o5_broke", role="viewer")

def test_unauthenticated_client_cannot_stream_paid_episode():
    """Acceptance Gate 6O-5: Unauthenticated client cannot stream paid video files."""
    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_paid"
    }
    resp = client.post("/api/v1/media/sessions/create", json=payload)
    assert resp.status_code == 401
    assert "Authentication required" in resp.json()["detail"]

def test_authenticated_viewer_without_entitlement_cannot_stream_paid_episode(unentitled_viewer_token):
    """Acceptance Gate 6O-5: Authenticated viewer without entitlement is rejected with HTTP 402."""
    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_paid"
    }
    resp = client.post(
        "/api/v1/media/sessions/create",
        json=payload,
        headers={"Authorization": f"Bearer {unentitled_viewer_token}"}
    )
    assert resp.status_code == 402
    assert "Payment required" in resp.json()["detail"]

def test_authenticated_viewer_with_entitlement_receives_time_bounded_token(viewer_token):
    """Acceptance Gate 6O-5: Entitled viewer receives short-lived (60s TTL) playback token."""
    # Grant entitlement
    ledger_repository.local_insert("unlocked_episodes", {
        "id": "unlock_6o5_01",
        "user_id": "usr_viewer_6o5_active",
        "episode_id": "ep_6o5_paid"
    })

    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_paid"
    }
    resp = client.post(
        "/api/v1/media/sessions/create",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["ttl_seconds"] == 60
    assert data["expires_in_seconds"] == 60
    assert "playback_url" in data
    assert data["storage_key"] == "masters/ser_6o5_catalog/ep_6o5_paid.mp4"

def test_free_episode_accessible_without_payment():
    """Acceptance Gate 6O-5: Published free episode accessible to viewer."""
    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_free"
    }
    resp = client.post("/api/v1/media/sessions/create", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_free"] is True
    assert data["ttl_seconds"] == 60

def test_unreleased_draft_episode_rejected_even_if_storage_key_known(viewer_token):
    """Acceptance Gate 6O-5: Unreleased/draft episodes return 403 even if storage key is known."""
    # Even with entitlement in place, unreleased content cannot be streamed
    ledger_repository.local_insert("unlocked_episodes", {
        "id": "unlock_6o5_draft",
        "user_id": "usr_viewer_6o5_active",
        "episode_id": "ep_6o5_draft"
    })

    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_draft"
    }
    resp = client.post(
        "/api/v1/media/sessions/create",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 403
    assert "not published" in resp.json()["detail"].lower()

def test_empty_draft_episode_rejected(viewer_token):
    """Empty draft episodes return HTTP 403."""
    payload = {
        "series_id": "ser_6o5_catalog",
        "episode_id": "ep_6o5_empty"
    }
    resp = client.post(
        "/api/v1/media/sessions/create",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert resp.status_code == 403

def test_direct_storage_stream_rejects_master_keys():
    """Direct streaming of masters via GET /storage/stream is blocked with HTTP 403."""
    resp = client.get("/api/storage/stream/masters/ser_6o5_catalog/ep_6o5_paid.mp4", follow_redirects=False)
    assert resp.status_code == 403
    assert "Direct streaming of protected media assets is prohibited" in resp.json()["detail"]

def test_direct_storage_stream_rejects_unallowlisted_keys():
    """Direct streaming of arbitrary/private keys via GET /storage/stream is blocked with HTTP 403."""
    resp = client.get("/api/storage/stream/private/confidential.mp4", follow_redirects=False)
    assert resp.status_code == 403

def test_direct_storage_stream_allows_public_ident_assets():
    """Allowlisted public branding assets remain accessible with HTTP 307 redirect."""
    resp = client.get("/api/storage/stream/videos/welele_ident_v2.mp4", follow_redirects=False)
    assert resp.status_code == 307
    assert "location" in resp.headers

def test_nonexistent_series_or_episode_returns_404():
    """Nonexistent series or episode returns HTTP 404."""
    resp = client.post("/api/v1/media/sessions/create", json={"series_id": "none", "episode_id": "none"})
    assert resp.status_code == 404
