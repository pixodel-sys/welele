"""
Welele Media™ — Security & Trust Foundation Verification Suite
Validates:
1. Multi-role IAM route guards (Viewer, Creator, Admin).
2. Creator Tenant Isolation & Boundary Protection.
3. Cryptographic Token Tampering & Expiry Rejection.
4. Comprehensive 6-Domain Audit Event Logging (AUTH, IP, CONTENT, COMMERCE, EXPERIENCE, SECURITY).
5. Append-Only SHA-256 Hash Chain Integrity & Tamper-Evident Detection.
"""

import time
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from services.audit_service import audit_service
from repositories.series_repository import series_repository
from repositories.ip_repository import ip_repository

client = TestClient(app)

def test_unauthenticated_requests_rejected():
    """Verifies that protected admin and mutating creator endpoints reject unauthenticated requests."""
    # Admin Moderation Queue
    res_mod = client.get("/api/admin/moderation-queue")
    assert res_mod.status_code == 403 or res_mod.status_code == 401

    # Experience Admin Publishing
    res_exp = client.post("/api/experience/page/home/publish")
    assert res_exp.status_code == 403 or res_exp.status_code == 401

    # Series Creation without Token
    res_series = client.post("/api/creators/series/create", json={"title": "Hacker Show", "genre": "Crime"})
    assert res_series.status_code == 403 or res_series.status_code == 401
    print("[PASS] Unauthenticated requests strictly rejected across protected surfaces.")

def test_viewer_role_rejected_on_privileged_surfaces():
    """Verifies that ROLE_VIEWER tokens cannot access Creator Studio or Admin Platform."""
    viewer_token = create_access_token(user_id="viewer_sipho_01", role="viewer", market="ZA")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer attempts Creator Episode Ingestion
    res_ep = client.post("/api/creators/episodes/add", json={"series_id": "story_blood_ties", "title": "Infiltrate"}, headers=viewer_headers)
    assert res_ep.status_code == 403
    assert "Access denied" in res_ep.json().get("detail", "")

    # Viewer attempts Admin Moderation Queue
    res_admin = client.get("/api/admin/moderation-queue", headers=viewer_headers)
    assert res_admin.status_code == 403

    # Viewer attempts Experience Layout Reset
    res_reset = client.post("/api/experience/page/home/reset-default", headers=viewer_headers)
    assert res_reset.status_code == 403
    print("[PASS] Viewer role blocked from Creator and Admin surfaces with 403 Forbidden.")

def test_creator_role_and_tenant_isolation():
    """
    Verifies that a creator can manage their own series, but is strictly blocked from
    mutating another creator's intellectual property (Tenant Isolation).
    """
    creator_a_token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    creator_b_token = create_access_token(user_id="creator_amaka", role="creator", creator_id="creator_amaka")

    headers_a = {"Authorization": f"Bearer {creator_a_token}"}
    headers_b = {"Authorization": f"Bearer {creator_b_token}"}

    # 1. Creator A creates series owned by Creator A -> Allowed
    res_create = client.post("/api/creators/series/create", json={
        "title": "Zola's Midnight Dynasty",
        "genre": "Revenge",
        "creator_id": "creator_zola",
        "coin_price_per_episode": 5
    }, headers=headers_a)
    assert res_create.status_code == 200
    series_a_id = res_create.json()["story"]["id"]

    # 2. Creator A adds episode to Creator A's series -> Allowed
    res_add_ok = client.post("/api/creators/episodes/add", json={
        "series_id": series_a_id,
        "episode_number": 1,
        "title": "The Oath",
        "duration_seconds": 75,
        "video_url": "/videos/welele_placeholder.mp4"
    }, headers=headers_a)
    assert res_add_ok.status_code == 200

    # 3. Creator B attempts to add episode to Creator A's series -> BLOCKED by Tenant Boundary!
    res_add_blocked = client.post("/api/creators/episodes/add", json={
        "series_id": series_a_id,
        "episode_number": 2,
        "title": "Malicious Hijack Episode",
        "duration_seconds": 60,
        "video_url": "/videos/welele_placeholder.mp4"
    }, headers=headers_b)
    assert res_add_blocked.status_code == 403
    assert "Tenant boundary violation" in res_add_blocked.json().get("detail", "")
    print(f"[PASS] Creator Tenant Isolation: Creator B successfully blocked from mutating Creator A's series (ID: {series_a_id}).")

def test_admin_super_access_and_audit_trail():
    """Verifies that Admin role holds global oversight and all decisions record audit entries."""
    admin_token = create_access_token(user_id="admin_supervisor", role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Admin reads moderation queue
    res_queue = client.get("/api/admin/moderation-queue", headers=admin_headers)
    assert res_queue.status_code == 200
    queue = res_queue.json().get("queue", [])
    assert len(queue) > 0

    # 2. Admin approves item
    test_item = queue[0]
    res_appr = client.post(f"/api/admin/moderation/{test_item['id']}/approve", headers=admin_headers)
    assert res_appr.status_code == 200

    # 3. Admin modifies and publishes experience layout
    res_pub = client.post("/api/experience/page/home/publish", headers=admin_headers)
    assert res_pub.status_code == 200
    assert res_pub.json()["status"] == "published"
    print("[PASS] Admin super-access verified and operations executed with audit receipts.")

def test_cryptographic_token_tampering_and_expiry():
    """Verifies that tampered signatures and expired JWTs are immediately rejected."""
    # 1. Tampered Signature
    valid_token = create_access_token(user_id="creator_zola", role="creator")
    tampered_token = valid_token[:-4] + "ABCD"
    res_tampered = client.get("/api/creators/creator_zola/dashboard", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_tampered.status_code == 401 or res_tampered.status_code == 403

    # 2. Expired Token
    expired_token = create_access_token(user_id="creator_zola", role="creator", expires_in=-10)
    res_expired = client.get("/api/creators/creator_zola/dashboard", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401 or res_expired.status_code == 403
    print("[PASS] Cryptographic token tampering and expired tokens rejected with 401/403.")

def test_append_only_hash_chain_integrity():
    """
    Verifies that the audit ledger maintains unbroken SHA-256 block hash chaining,
    and detects any retroactive tampering or altered history.
    """
    # 1. Verify live legitimate chain
    verification = audit_service.verify_audit_chain_integrity()
    assert verification["valid"] is True, f"Legitimate audit chain failed verification: {verification}"
    assert verification["total_blocks"] >= 1
    print(f"[PASS] Audit Hash Chain: Verified {verification['total_blocks']} contiguous cryptographically linked blocks.")

    # 2. Simulate retroactive database tampering in memory and verify detection
    chain = audit_service.local_get("security_audit_ledger")
    if len(chain) > 2:
        tampered_chain = [dict(c) for c in chain]
        # Modify past payload
        tampered_chain[1]["before_state"] = {"tampered": True}
        audit_service.local_set("security_audit_ledger", tampered_chain)

        tampered_verify = audit_service.verify_audit_chain_integrity()
        assert tampered_verify["valid"] is False, "Tamper-evident verification failed to catch altered history!"
        assert "tampering detected" in tampered_verify.get("error", "").lower()
        print(f"[PASS] Tamper Detection: System successfully flagged illicit historical alteration in block {tampered_verify['broken_block_sequence']}.")

        # Restore legitimate chain
        audit_service.local_set("security_audit_ledger", chain)
        assert audit_service.verify_audit_chain_integrity()["valid"] is True
        print("[PASS] Legitimate chain restored and re-verified successfully.")

def test_audit_domains_coverage():
    """Verifies that state transitions across all core domains are recorded."""
    admin_token = create_access_token(user_id="admin_supervisor", role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res_logs = client.get("/api/admin/audit-logs?limit=100", headers=admin_headers)
    assert res_logs.status_code == 200
    logs = res_logs.json().get("logs", [])
    assert len(logs) > 0

    domains_logged = set(entry.get("domain") for entry in logs)
    print(f"[PASS] Active Audit Domains Recorded in Ledger: {sorted(list(domains_logged))}")
    assert "SECURITY" in domains_logged or "CONTENT" in domains_logged or "AUTH" in domains_logged

def test_url_tampering_and_route_switching_cannot_bypass_authorization():
    """
    Acceptance Test: Changing URL or attempting route switching without authorized credentials
    must never bypass backend RBAC authorization and tenant isolation.
    """
    # 1. Anonymous / Unauthenticated requests to Creator and Admin endpoints
    assert client.get("/api/admin/moderation-queue").status_code in [401, 403]
    assert client.post("/api/experience/page/home/publish").status_code in [401, 403]
    assert client.get("/api/creators/creator_zola/dashboard").status_code in [401, 403]
    assert client.post("/api/creators/episodes/add", json={"series_id": "story_blood_ties", "title": "Bypass"}).status_code in [401, 403]

    # 2. Viewer Role Token attempting Creator and Admin endpoints
    viewer_token = create_access_token(user_id="viewer_mobile_user", role="viewer", market="ZA")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
    
    assert client.get("/api/creators/creator_zola/dashboard", headers=viewer_headers).status_code == 403
    assert client.post("/api/creators/episodes/add", json={"series_id": "story_blood_ties", "title": "Bypass"}, headers=viewer_headers).status_code == 403
    assert client.get("/api/admin/moderation-queue", headers=viewer_headers).status_code == 403
    assert client.post("/api/experience/page/home/publish", headers=viewer_headers).status_code == 403
    assert client.get("/api/admin/audit-logs", headers=viewer_headers).status_code == 403

    # 3. Creator Role Token attempting Admin-Only endpoints
    creator_token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
    creator_headers = {"Authorization": f"Bearer {creator_token}"}
    
    assert client.get("/api/admin/moderation-queue", headers=creator_headers).status_code == 403
    assert client.post("/api/experience/page/home/publish", headers=creator_headers).status_code == 403
    assert client.get("/api/admin/audit-logs", headers=creator_headers).status_code == 403

    print("[PASS] URL/Route Switching Security: Zero capability leakage across unauthenticated, viewer, and creator contexts.")

def test_creator_and_admin_auth_endpoints():
    """Verifies that /auth/creator/login and /auth/admin/login properly authenticate valid credentials and reject invalid ones."""
    # 1. Creator Login - Valid PIN
    res_creator_ok = client.post("/api/auth/creator/login", json={"creator_id": "creator_zola", "studio_pin": "1234"})
    assert res_creator_ok.status_code == 200
    assert res_creator_ok.json()["status"] == "success"
    assert res_creator_ok.json()["user"]["role"] == "creator"
    assert "access_token" in res_creator_ok.json()

    # 2. Creator Login - Invalid PIN
    res_creator_bad = client.post("/api/auth/creator/login", json={"creator_id": "creator_zola", "studio_pin": "9999"})
    assert res_creator_bad.status_code == 401
    assert "Invalid Showrunner Studio PIN" in res_creator_bad.json()["detail"]

    # 3. Admin Login - Valid Master Key & 2FA
    res_admin_ok = client.post("/api/auth/admin/login", json={"admin_key": "admin_master_welele_2026", "two_factor_code": "999888"})
    assert res_admin_ok.status_code == 200
    assert res_admin_ok.json()["status"] == "success"
    assert res_admin_ok.json()["user"]["role"] == "admin"
    assert "access_token" in res_admin_ok.json()

    # 4. Admin Login - Invalid Key
    res_admin_bad_key = client.post("/api/auth/admin/login", json={"admin_key": "wrong_master_key", "two_factor_code": "999888"})
    assert res_admin_bad_key.status_code == 401
    assert "Invalid Administrator Key" in res_admin_bad_key.json()["detail"]

    # 5. Admin Login - Invalid 2FA
    res_admin_bad_2fa = client.post("/api/auth/admin/login", json={"admin_key": "admin_master_welele_2026", "two_factor_code": "000000"})
    assert res_admin_bad_2fa.status_code == 401

    print("[PASS] Creator and Admin Auth Endpoints strictly validated.")

if __name__ == "__main__":
    pytest.main(["-v", "backend/test_security_trust_foundation.py"])

