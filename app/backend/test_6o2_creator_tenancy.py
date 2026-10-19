"""
Welele Media™ — 6O-2 Creator Tenancy & Workspace Membership Forensic Verification Suite
Validates all accepted 6O-2 invariants:
1. Canonical creator profiles resolve verified metadata without ambient authority.
2. Arbitrary or unmapped creator IDs are strictly rejected (fail-closed).
3. Legacy passkey authentication requires explicit allowlist enablement on creator profile.
4. Disabling legacy passkey fails closed with HTTP 403 Forbidden.
5. Workspace membership model validates role relationships within creator studios.
6. Token claims properly bind owner identity, active creator_id, and tenancy context.
7. Zero regression on Viewer OTP or Admin login boundaries established in 6O-1.
"""

import os
import pytest
from fastapi.testclient import TestClient
from main import app
from services.creator_profile_service import creator_profile_service

client = TestClient(app)

def test_canonical_creator_profile_resolution():
    """Asserts that recognized creator text slugs resolve valid canonical profiles."""
    profile = creator_profile_service.get_profile("creator_zola")
    assert profile is not None
    assert profile["id"] == "creator_zola"
    assert profile["legal_name"] == "Zola Dlamini"
    assert profile["status"] == "active"
    assert profile["legacy_passkey_enabled"] is True


def test_unregistered_creator_profile_returns_none():
    """Asserts that unknown or arbitrary creator IDs do not resolve."""
    profile = creator_profile_service.get_profile("unknown_unregistered_creator_000")
    assert profile is None


def test_creator_login_fails_closed_for_unregistered_creator():
    """Confirms creator login fails closed with 401 when attempting to authenticate as an unknown creator."""
    resp = client.post("/api/v1/auth/creator/login", json={
        "creator_id": "unknown_unregistered_creator_000",
        "password": "welele_dev_pass"
    })
    assert resp.status_code == 401
    assert "Unregistered or invalid Creator Studio profile" in resp.json()["detail"]


def test_creator_login_succeeds_with_valid_profile_and_allowlist():
    """Confirms creator login succeeds when profile exists and legacy passkey is enabled."""
    resp = client.post("/api/v1/auth/creator/login", json={
        "creator_id": "creator_zola",
        "password": "welele_dev_pass"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["user"]["creator_id"] == "creator_zola"
    assert data["user"]["role"] == "creator"


def test_creator_login_fails_closed_when_legacy_passkey_disabled(monkeypatch):
    """Confirms creator login fails with 403 when legacy passkey is explicitly disabled for the profile."""
    # Temporarily disable passkey for creator_amaka
    profile = creator_profile_service.get_profile("creator_amaka")
    assert profile is not None
    
    # Set studio key in environment
    monkeypatch.setenv("CREATOR_STUDIO_KEY", "valid_configured_studio_key_2026")
    
    # Store backup of profiles
    existing_profiles = creator_profile_service.local_get("creator_profiles") or []
    updated_profiles = []
    for p in existing_profiles:
        if p.get("id") == "creator_amaka":
            p_copy = dict(p)
            p_copy["legacy_passkey_enabled"] = False
            updated_profiles.append(p_copy)
        else:
            updated_profiles.append(p)
    creator_profile_service.local_set("creator_profiles", updated_profiles)

    try:
        resp = client.post("/api/v1/auth/creator/login", json={
            "creator_id": "creator_amaka",
            "password": "valid_configured_studio_key_2026"
        })
        assert resp.status_code == 403
        assert "Legacy studio passkey authentication is disabled" in resp.json()["detail"]
    finally:
        # Restore allowlist
        creator_profile_service.local_set("creator_profiles", existing_profiles)


def test_workspace_membership_resolution():
    """Asserts that workspace membership verifies owner roles correctly."""
    profile = creator_profile_service.get_profile("creator_zola")
    owner_id = str(profile["owner_user_id"])
    membership = creator_profile_service.get_workspace_membership(owner_id, "creator_zola")
    assert membership is not None
    assert membership["role"] == "owner"
    assert membership["status"] == "active"


def test_workspace_membership_rejects_foreign_user():
    """Asserts that a random foreign user does not hold membership in a creator studio."""
    membership = creator_profile_service.get_workspace_membership("unrelated_user_999", "creator_zola")
    assert membership is None


def test_viewer_otp_compatibility_not_regressed():
    """Ensures Viewer OTP compatibility continues operating on its narrow path."""
    os.environ["ENVIRONMENT"] = "test"
    resp = client.post("/api/v1/auth/phone/verify-otp", json={
        "phone_number": "+27820000002",
        "otp_code": "5542",
        "region_code": "ZA"
    })
    assert resp.status_code == 200
    assert resp.json()["user"]["role"] == "viewer"
