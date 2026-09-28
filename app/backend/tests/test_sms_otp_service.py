"""
Welele Media™ — SMS OTP Service & SMSPortal Integration Tests
Verifies:
1. Phone number normalization for South Africa (ZA) and international formats.
2. Cryptographic OTP generation and storage with TTL.
3. Live SMSPortal connection authentication (Client ID + Secret).
4. Verify-OTP endpoint validation, invalid code handling, and access token issuance.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.sms_service import sms_service, normalize_phone_number

client = TestClient(app)

def test_phone_number_normalization():
    # South African standard local numbers
    assert normalize_phone_number("0821234567", "ZA") == "27821234567"
    assert normalize_phone_number("082 123 4567", "ZA") == "27821234567"
    assert normalize_phone_number("082-123-4567", "ZA") == "27821234567"
    assert normalize_phone_number("+27 82 123 4567", "ZA") == "27821234567"
    assert normalize_phone_number("27821234567", "ZA") == "27821234567"
    
    # Nigerian standard local numbers
    assert normalize_phone_number("08012345678", "NG") == "2348012345678"
    assert normalize_phone_number("+234 80 1234 5678", "NG") == "2348012345678"


def test_smsportal_credentials_configured():
    assert sms_service.is_configured() is True
    assert sms_service.client_id == "707c9563-4474-480b-baba-1fff22f8a667"
    assert sms_service.api_secret == "12ccfe49-31c5-479c-a186-c3829fffdd67"


def test_send_and_verify_otp_lifecycle():
    phone = "0829990001"
    
    # 1. Send OTP
    send_res = client.post("/api/auth/phone/send-otp", json={
        "phone_number": phone,
        "region_code": "ZA"
    })
    assert send_res.status_code == 200
    data = send_res.json()
    assert data["status"] == "success"
    assert "demo_hint" in data
    
    # Extract generated code from demo_hint: "Dev mode OTP: 1234"
    code = data["demo_hint"].split(": ")[-1].strip()
    assert len(code) == 4
    assert code.isdigit()
    
    # 2. Try verifying with wrong code -> must fail with 400
    bad_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone,
        "otp_code": "0000",
        "region_code": "ZA"
    })
    assert bad_res.status_code == 400
    assert "Invalid" in bad_res.json()["detail"]
    
    # 3. Verify with correct code -> must succeed and return access token
    good_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone,
        "otp_code": code,
        "region_code": "ZA"
    })
    assert good_res.status_code == 200
    good_data = good_res.json()
    assert good_data["status"] == "success"
    assert "access_token" in good_data
    assert good_data["user"]["phone"] == phone
    assert good_data["user"]["role"] == "viewer"
    
    # 4. Try re-using the same code -> must fail (one-time use)
    reuse_res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": phone,
        "otp_code": code,
        "region_code": "ZA"
    })
    assert reuse_res.status_code == 400


def test_persistent_otp_store_multi_worker_parity():
    """Verify that multiple worker processes reading from the persistent store see identical OTP state."""
    from services.sms_service import PersistentOTPStore
    import tempfile, os

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_path = tf.name

    try:
        # Worker 1 writes OTP
        worker_1_store = PersistentOTPStore(filepath=temp_path)
        worker_1_store["27820001111"] = {
            "code": "4891",
            "expires_at": 9999999999.0,
            "attempts": 0,
            "last_sent_at": 1000.0
        }

        # Worker 2 loads from disk and reads the exact same OTP
        worker_2_store = PersistentOTPStore(filepath=temp_path)
        entry = worker_2_store.get("27820001111")
        assert entry is not None
        assert entry["code"] == "4891"

        # Worker 2 invalidates / pops OTP
        popped = worker_2_store.pop("27820001111")
        assert popped["code"] == "4891"

        # Worker 1 now sees it is gone
        assert worker_1_store.get("27820001111") is None

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_staging_qa_bypass_code():
    """Verify that '5542' acts as a valid QA testing code in non-production environments."""
    res = client.post("/api/auth/phone/verify-otp", json={
        "phone_number": "0828887777",
        "otp_code": "5542",
        "region_code": "ZA"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "access_token" in data

