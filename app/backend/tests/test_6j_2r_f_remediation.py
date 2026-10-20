"""
Welele Media™ — Phase 6J-2R-F Remediation Automated Test Suite
Show Edit, Allowlisted Persistence, and Guarded Deletion.

Verifies:
1. Allowlisted Show Metadata Updates:
   - title, tagline, synopsis, genre, coin_price_per_episode, available_languages, tags.
2. Strict Sanitization:
   - Non-existent database columns (creator_id, creator_name, episodes, hydrated IP) are stripped.
3. Access Control & Tenant Isolation:
   - Update requires authenticated creator or admin.
   - Cross-tenant update rejected with 403.
4. Guarded Deletion Lifecycle:
   - Delete endpoint requires authenticated creator or admin.
   - Cross-tenant delete rejected with 403.
   - Deletes series and cascades to series-owned episodes.
   - Master Digital IP franchise and rights records strictly preserved.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from repositories.series_repository import series_repository, to_uuid
from repositories.ip_repository import ip_repository

client = TestClient(app)


def test_series_repository_update_allowlisted_fields():
    """DAL test: update_series accurately mutates allowlisted fields and sanitizes others."""
    series_id = f"test_series_{uuid.uuid4().hex[:8]}"
    ip_id = str(uuid.uuid4())
    
    initial = {
        "id": series_id,
        "ip_id": ip_id,
        "title": "Original Title",
        "tagline": "Original Tagline",
        "synopsis": "Original Synopsis",
        "genre": "Drama",
        "coin_price_per_episode": 5,
        "available_languages": ["English"],
        "tags": ["#Original"],
        "creator_id": "creator_test_f"
    }
    series_repository.local_insert("series", initial)
    
    # Apply allowlisted updates
    updates = {
        "title": "Updated Forensic Title",
        "tagline": "Updated Forensic Tagline",
        "synopsis": "Updated Forensic Synopsis",
        "genre": "Thriller • Suspense",
        "coin_price_per_episode": 10,
        "available_languages": ["isiZulu", "English"],
        "tags": ["#Updated", "#Forensic"],
        # Forbidden / read-only fields that must NOT overwrite
        "creator_id": "creator_hacker",
        "episodes": [{"id": "fake_ep"}]
    }
    
    updated = series_repository.update_series(series_id, updates)
    assert updated["title"] == "Updated Forensic Title"
    assert updated["tagline"] == "Updated Forensic Tagline"
    assert updated["synopsis"] == "Updated Forensic Synopsis"
    assert updated["genre"] == "Thriller • Suspense"
    assert updated["coin_price_per_episode"] == 10
    assert updated["available_languages"] == ["isiZulu", "English"]
    assert updated["tags"] == ["#Updated", "#Forensic"]
    # creator_id must remain unchanged
    assert updated["creator_id"] == "creator_test_f"


def test_api_patch_series_endpoint_authorized():
    """API test: Authenticated creator successfully updates their own series metadata."""
    series_id = f"test_series_{uuid.uuid4().hex[:8]}"
    creator_id = "creator_zola"
    
    series_repository.local_insert("series", {
        "id": series_id,
        "ip_id": str(uuid.uuid4()),
        "title": "Zola Pre-Edit Show",
        "tagline": "Old Tagline",
        "synopsis": "Old Synopsis",
        "genre": "Drama",
        "coin_price_per_episode": 5,
        "creator_id": creator_id
    })
    
    token = create_access_token(user_id=creator_id, role="creator", creator_id=creator_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    patch_payload = {
        "title": "Zola Post-Edit Show Verified",
        "synopsis": "New persistent synopsis for Zola.",
        "coin_price_per_episode": 8
    }
    
    resp = client.patch(f"/api/v1/creators/series/{series_id}", json=patch_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["series"]["title"] == "Zola Post-Edit Show Verified"
    assert data["series"]["synopsis"] == "New persistent synopsis for Zola."
    assert data["series"]["coin_price_per_episode"] == 8


def test_api_patch_series_cross_tenant_rejected():
    """API test: Non-owner creator attempting to edit another creator's show is rejected 403."""
    series_id = f"test_series_{uuid.uuid4().hex[:8]}"
    owner_id = "creator_zola"
    attacker_id = "creator_amaka"
    
    series_repository.local_insert("series", {
        "id": series_id,
        "ip_id": str(uuid.uuid4()),
        "title": "Zola Sacred Show",
        "creator_id": owner_id
    })
    
    token = create_access_token(user_id=attacker_id, role="creator", creator_id=attacker_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    patch_payload = {
        "title": "Hacked Title"
    }
    
    resp = client.patch(f"/api/v1/creators/series/{series_id}", json=patch_payload, headers=headers)
    assert resp.status_code == 403
    assert "Tenant boundary violation" in resp.json().get("detail", "")


def test_api_patch_series_unauthorized_rejected():
    """API test: Unauthenticated or viewer caller is rejected."""
    series_id = f"test_series_{uuid.uuid4().hex[:8]}"
    series_repository.local_insert("series", {
        "id": series_id,
        "ip_id": str(uuid.uuid4()),
        "title": "Protected Show",
        "creator_id": "creator_zola"
    })
    
    # 1. No token (anonymous guest defaults to viewer role)
    resp = client.patch(f"/api/v1/creators/series/{series_id}", json={"title": "No Auth"})
    assert resp.status_code == 403
    
    # 2. Viewer token
    viewer_token = create_access_token(user_id="viewer_1", role="viewer")
    resp2 = client.patch(f"/api/v1/creators/series/{series_id}", json={"title": "Viewer Hack"}, headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp2.status_code == 403


def test_guarded_delete_series_authorized():
    """Lifecycle test: Guarded deletion removes series & episodes, strictly preserves Digital IP."""
    series_id = f"test_del_series_{uuid.uuid4().hex[:8]}"
    digital_ip_id = str(uuid.uuid4())
    creator_id = "creator_zola"
    
    # Seed Digital IP
    ip_repository.local_insert("digital_ips", {
        "id": digital_ip_id,
        "title": "Preserved IP Franchise",
        "master_owner_id": creator_id
    })
    
    # Seed Series
    series_repository.local_insert("series", {
        "id": series_id,
        "ip_id": digital_ip_id,
        "title": "Series To Be Deleted",
        "creator_id": creator_id
    })
    
    # Seed Episode owned by series
    ep_id = f"ep_{uuid.uuid4().hex[:8]}"
    series_repository.local_insert("episodes", {
        "id": ep_id,
        "series_id": series_id,
        "title": "Episode Owned By Series"
    })
    
    token = create_access_token(user_id=creator_id, role="creator", creator_id=creator_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Execute DELETE
    resp = client.delete(f"/api/v1/creators/series/{series_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["deleted"] is True
    assert data["preserved_ip_id"] == digital_ip_id
    
    # Verify series is gone
    all_series = series_repository.local_get("series") or []
    assert not any(s.get("id") == series_id for s in all_series)
    
    # Verify owned episodes are gone
    all_eps = series_repository.local_get("episodes") or []
    assert not any(e.get("series_id") == series_id for e in all_eps)
    
    # Verify Digital IP is PRESERVED
    all_ips = ip_repository.local_get("digital_ips") or []
    assert any(ip.get("id") == digital_ip_id for ip in all_ips), "Protected Invariant Violated: Digital IP must NOT be deleted!"


def test_guarded_delete_cross_tenant_rejected():
    """Security test: Cross-tenant deletion attempt is strictly rejected 403."""
    series_id = f"test_del_series_{uuid.uuid4().hex[:8]}"
    owner_id = "creator_zola"
    attacker_id = "creator_amaka"
    
    series_repository.local_insert("series", {
        "id": series_id,
        "ip_id": str(uuid.uuid4()),
        "title": "Zola Protected Series",
        "creator_id": owner_id
    })
    
    token = create_access_token(user_id=attacker_id, role="creator", creator_id=attacker_id)
    headers = {"Authorization": f"Bearer {token}"}
    
    resp = client.delete(f"/api/v1/creators/series/{series_id}", headers=headers)
    assert resp.status_code == 403
    assert "Tenant boundary violation" in resp.json().get("detail", "")
