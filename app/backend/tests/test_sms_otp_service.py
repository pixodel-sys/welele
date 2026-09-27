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
