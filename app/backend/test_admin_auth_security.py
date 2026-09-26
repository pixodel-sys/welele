"""
Welele Media™ — Admin Authentication & Security Fail-Closed Regression Suite
Validates:
1. Production configuration CANNOT start with known/default admin credentials.
2. Production configuration CANNOT start when required admin secrets are absent.
3. Admin authentication fails closed when required secrets are absent rather than falling back.
4. Development credentials exist solely via explicit environment configuration, never code defaults.
"""

import os
import pytest
from fastapi.testclient import TestClient
from config import Settings
from main import app

client = TestClient(app)

def test_production_fails_to_start_with_absent_admin_key(monkeypatch):
    """Asserts that production configuration cannot start when ADMIN_MASTER_KEY is missing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_MASTER_KEY", "")
    monkeypatch.setenv("ADMIN_2FA_CODE", "secure_prod_2fa_987654")

    prod_settings = Settings()
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_security_invariants()
    
    assert "ADMIN_MASTER_KEY is not configured" in str(exc_info.value)
    assert "must fail closed" in str(exc_info.value)


def test_production_fails_to_start_with_known_default_admin_key(monkeypatch):
    """Asserts that production configuration cannot start with known/default admin credentials."""
    for forbidden_key in ["admin_master_welele_2026", "dev_admin_secret_local_only", "admin", "password", "123456"]:
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ADMIN_MASTER_KEY", forbidden_key)
        monkeypatch.setenv("ADMIN_2FA_CODE", "secure_prod_2fa_987654")

        prod_settings = Settings()
        with pytest.raises(RuntimeError) as exc_info:
            prod_settings.validate_security_invariants()

        assert "prohibited default/dev secret" in str(exc_info.value)
        assert "Production configuration cannot start with known/default admin credentials" in str(exc_info.value)


def test_production_fails_to_start_with_absent_2fa_code(monkeypatch):
    """Asserts that production configuration cannot start without multi-factor authentication (2FA) configured."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_MASTER_KEY", "real_enterprise_entropy_super_secret_998877")
    monkeypatch.setenv("ADMIN_2FA_CODE", "")

    prod_settings = Settings()
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.validate_security_invariants()

    assert "ADMIN_2FA_CODE is not configured" in str(exc_info.value)
    assert "Multi-factor authentication (2FA) is mandatory" in str(exc_info.value)


def test_production_starts_cleanly_with_valid_custom_secrets(monkeypatch):
    """Asserts that production configuration validates cleanly when strong custom secrets are provided."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_MASTER_KEY", "xK9#mQ2$vL8*wP5!nZ4^enterprise_prod_master")
    monkeypatch.setenv("ADMIN_2FA_CODE", "839201")

    prod_settings = Settings()
    # Must not raise
    prod_settings.validate_security_invariants()
    assert prod_settings.IS_PRODUCTION_OR_STAGING is True


def test_admin_auth_endpoint_fails_closed_when_secret_absent(monkeypatch):
    """Asserts that /auth/admin/login rejects authentication if ADMIN_MASTER_KEY is not configured in environment."""
    from config import settings
    monkeypatch.setattr(settings, "ADMIN_MASTER_KEY", "")
    monkeypatch.setattr(settings, "ADMIN_2FA_CODE", "")

    res = client.post("/api/auth/admin/login", json={
        "admin_key": "admin_master_welele_2026",
        "two_factor_code": "999888"
    })
    assert res.status_code in [401, 500]
    assert "Admin authentication is disabled" in res.json().get("detail", "")


def test_admin_auth_endpoint_rejects_fallback_when_unconfigured(monkeypatch):
    """Asserts that dev fallback credentials (e.g. dev_admin_secret_local_only) do NOT authenticate when secret is unset."""
    from config import settings
    monkeypatch.setattr(settings, "ADMIN_MASTER_KEY", "")
    monkeypatch.setattr(settings, "ADMIN_2FA_CODE", "")

    res = client.post("/api/auth/admin/login", json={
        "admin_key": "dev_admin_secret_local_only",
        "two_factor_code": "999888"
    })
    assert res.status_code in [401, 500]
    assert "Admin authentication is disabled" in res.json().get("detail", "")
