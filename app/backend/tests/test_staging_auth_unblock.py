"""
Welele Media™ — Staging-Safe Authentication & Provisioning Verification Tests
Validates:
1. ZA Phone OTP send + verify succeeds with matching phone normalization.
2. OTP verification preserves the selected region_code (e.g. NG).
3. Single-use OTP invalidation (subsequent verification of same code is rejected).
4. Creator login succeeds using the Showrunner UI contract (studio_pin) when CREATOR_STUDIO_KEY is configured.
5. Invalid creator credentials remain strictly rejected (401 Unauthorized).
6. Staging/production security invariants remain intact (dev bypasses prohibited).
"""

import os
import re
import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from services.sms_service import sms_service, normalize_phone_number

client = TestClient(app)


def test_za_otp_send_and_verify_matching_normalization():
    """Confirms ZA phone number normalization agrees across send and verify."""
    phone_formatted = "082 555 1234"
    
    # 1. Send OTP
    send_res = client.post("/api/auth/phone/send-otp", json={
        "phone_number": phone_formatted,
        "region_code": "ZA"
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert data["status"] == "success"
    assert "demo_hint" in data
    
    import re
    # Extract the 4-digit code cleanly regardless of SMS dispatch status
    code_match = re.search(r'\b\d{4}\b', data["demo_hint"])
    assert code_match is not None
    code = code_match.group(0)
    assert len(code) == 4
    assert code.isdigit()
    
    # 2. Verify with matching normalized code
    verify_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone_formatted,
        "otp_code": code,
        "region_code": "ZA"
    })
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["status"] == "success"
    assert "access_token" in v_data
    assert v_data["user"]["role"] == "viewer"
    assert v_data["user"]["market"] == "ZA"


def test_otp_verification_preserves_region_code():
    """Confirms non-ZA region_code (e.g. NG) is preserved and agrees between send and verify."""
    phone_ng = "08012345678"
    
    # 1. Send OTP with region_code="NG"
    send_res = client.post("/api/auth/phone/send-otp", json={
        "phone_number": phone_ng,
        "region_code": "NG"
    })
    assert send_res.status_code == 200
    import re
    code = re.search(r'\b\d{4}\b', send_res.json()["demo_hint"]).group(0)
    
    # 2. Verify with region_code="NG" -> must succeed
    verify_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone_ng,
        "otp_code": code,
        "region_code": "NG"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "success"
    assert verify_res.json()["user"]["market"] == "NG"


def test_single_use_otp_rejects_duplicate_submission():
    """Confirms that once verified, an OTP code cannot be re-used (single-use guarantee)."""
    phone = "0829995544"
    send_res = client.post("/api/auth/phone/send-otp", json={
        "phone_number": phone,
        "region_code": "ZA"
    })
    code = re.search(r'\b\d{4}\b', send_res.json()["demo_hint"]).group(0)
    
    # First submission succeeds
    first_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone,
        "otp_code": code,
        "region_code": "ZA"
    })
    assert first_res.status_code == 200
    
    # Second submission with same code must be rejected with 400 Bad Request
    second_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone,
        "otp_code": code,
        "region_code": "ZA"
    })
    assert second_res.status_code == 400
    assert "No OTP request found" in second_res.json()["detail"] or "expired" in second_res.json()["detail"].lower()


def test_creator_login_showrunner_contract_with_configured_key(monkeypatch):
    """
    Confirms creator login succeeds when the legitimate staging CREATOR_STUDIO_KEY
    is supplied as studio_pin (the exact payload sent by Showrunner UI).
    """
    staging_key = "staging_showrunner_auth_secret_2026"
    monkeypatch.setenv("CREATOR_STUDIO_KEY", staging_key)
    
    # Showrunner UI sends { creator_id, studio_pin }
    login_res = client.post("/api/auth/creator/login", json={
        "creator_id": "creator_zola",
        "studio_pin": staging_key
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["user"]["role"] == "creator"
    assert data["user"]["creator_id"] == "creator_zola"


def test_invalid_creator_credentials_rejected(monkeypatch):
    """Confirms invalid creator credentials fail closed with 401 Unauthorized."""
    monkeypatch.setenv("CREATOR_STUDIO_KEY", "legitimate_secret_key")
    
    # Wrong studio_pin
    bad_res = client.post("/api/auth/creator/login", json={
        "creator_id": "creator_zola",
        "studio_pin": "wrong_pin_attempt"
    })
    assert bad_res.status_code == 401
    assert "Invalid Showrunner Studio PIN" in bad_res.json()["detail"]


def test_staging_production_dev_bypass_disabled(monkeypatch):
    """Confirms development bypass PIN ('1234') is strictly blocked when IS_PRODUCTION_OR_STAGING is True."""
    monkeypatch.setattr(settings, "IS_PRODUCTION_OR_STAGING", True)
    monkeypatch.delenv("CREATOR_STUDIO_KEY", raising=False)
    
    res = client.post("/api/auth/creator/login", json={
        "creator_id": "creator_zola",
        "studio_pin": "1234"
    })
    assert res.status_code == 401
    assert "Invalid Showrunner Studio PIN" in res.json()["detail"]
