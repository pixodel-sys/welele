"""
Welele Media™ — Authoritative Database Target Guard & Test Isolation Regression Suite

Validates complete fail-closed security invariants:
1. Explicit Python environment resolution (no NODE_ENV fallback, conflict detection, 'prod' normalization, no silent conversion).
2. Strict deployment-variable allowlist enforcement:
   - Missing PRODUCTION_SUPABASE_REF or STAGING_SUPABASE_REF fails closed.
   - Identical refs fail closed.
   - Test: NO cloud access under any circumstances.
   - Development & Staging: Staging project ONLY (dbsnaidhznofvyffdfni).
   - Production: Production project ONLY (mngyyxqdhjgteezwkxdn).
3. Rejection of malformed URLs, unsupported schemes, invalid hosts, and conflicting configs.
4. Fallback sanitization (non-production never falls back; production logs variable NAME; anon key never promoted to service role).
5. All Supabase client construction paths and singletons blocked in test mode.
6. Audit service startup genesis and test isolation proof (purely local, zero remote sync).
7. Invalid production administrative security invariants (missing master key, forbidden dev keys, missing 2FA code).
"""

import os
import pytest
from unittest.mock import patch

from target_validator import (
    validate_database_target,
    extract_project_ref,
    get_resolved_environment,
    get_project_allowlist,
    CONFIRMED_PRODUCTION_REF,
    CONFIRMED_STAGING_REF,
    VALID_ENVIRONMENTS
)
from config import Settings
from repositories.base_repository import BaseRepository
from services.audit_service import AuditService
from database import Database, db


PROD_REF = CONFIRMED_PRODUCTION_REF
STAGING_REF = CONFIRMED_STAGING_REF


# ==============================================================================
# 1. Project Reference Extraction & URL Validation
# ==============================================================================

def test_extract_project_ref_valid_targets():
    """Extracts valid references from standard Supabase URLs and bare 20-char tokens."""
    assert extract_project_ref(f"https://{PROD_REF}.supabase.co") == PROD_REF
    assert extract_project_ref(f"https://{STAGING_REF}.supabase.co") == STAGING_REF
    assert extract_project_ref(f"https://{PROD_REF}.supabase.in:443") == PROD_REF
    assert extract_project_ref(PROD_REF) == PROD_REF
    assert extract_project_ref(STAGING_REF) == STAGING_REF
    assert extract_project_ref("") is None
    assert extract_project_ref(None) is None


def test_extract_project_ref_rejects_malformed_and_unsupported_urls():
    """Fails closed on malformed URLs, unsupported schemes, and non-Supabase hosts."""
    # Unsupported URL schemes
    with pytest.raises(RuntimeError, match="Unsupported URL scheme"):
        extract_project_ref(f"ftp://{PROD_REF}.supabase.co")

    with pytest.raises(RuntimeError, match="Unsupported URL scheme"):
        extract_project_ref(f"postgres://user:pass@{PROD_REF}.supabase.co:5432/db")

    # Malformed URL structure
    with pytest.raises(RuntimeError, match="Unsupported or malformed target URL"):
        extract_project_ref("https://")

    # Unrecognized / deceptive hosts
    with pytest.raises(RuntimeError, match="not a recognized Supabase cloud endpoint"):
        extract_project_ref("https://evil-supabase.com")

    with pytest.raises(RuntimeError, match="not a recognized Supabase cloud endpoint"):
        extract_project_ref(f"https://attacker.org/path/{PROD_REF}.supabase.co")


# ==============================================================================
# 2. Python Environment Resolution & Invariant Enforcement
# ==============================================================================

def test_environment_resolution_normalizes_prod():
    """Normalizes 'prod' to 'production'."""
    with patch.dict(os.environ, {"ENVIRONMENT": "prod"}, clear=True):
        assert get_resolved_environment() == "production"

    with patch.dict(os.environ, {"APP_ENV": "prod"}, clear=True):
        assert get_resolved_environment() == "production"


def test_environment_resolution_does_not_use_node_env():
    """Verifies that NODE_ENV is ignored by the Python backend."""
    with patch.dict(os.environ, {"NODE_ENV": "production"}, clear=True):
        assert get_resolved_environment() == ""


def test_environment_resolution_detects_conflicting_declarations():
    """Detects and fails closed on conflicting ENVIRONMENT vs APP_ENV declarations."""
    with patch.dict(os.environ, {"ENVIRONMENT": "test", "APP_ENV": "production"}):
        with pytest.raises(RuntimeError, match="Conflicting environment declarations"):
            get_resolved_environment()


def test_environment_resolution_does_not_silently_convert_missing_to_development():
    """Missing or invalid environment returns empty or invalid string, not 'development'."""
    with patch.dict(os.environ, {}, clear=True):
        assert get_resolved_environment() == ""

    with patch.dict(os.environ, {"ENVIRONMENT": "invalid_env"}, clear=True):
        assert get_resolved_environment() == "invalid_env"


def test_settings_fails_closed_on_unrecognized_or_missing_environment():
    """Settings.validate_security_invariants fails closed when ENVIRONMENT is unset or not in VALID_ENVIRONMENTS."""
    with patch.dict(os.environ, {"ENVIRONMENT": "qa"}, clear=True):
        s = Settings()
        assert s.ENVIRONMENT == "qa"
        with pytest.raises(RuntimeError, match="ENVIRONMENT must be explicitly set to one of"):
            s.validate_security_invariants()

    with patch.dict(os.environ, {}, clear=True):
        s = Settings()
        assert s.ENVIRONMENT == ""
        with pytest.raises(RuntimeError, match="ENVIRONMENT must be explicitly set to one of"):
            s.validate_security_invariants()


# ==============================================================================
# 3. Fallback Sanitization & Anonymous Key Protection
# ==============================================================================

def test_non_production_empty_string_does_not_fallback():
    """In non-production, empty SUPABASE_URL must NOT fall back to NEXT_PUBLIC_SUPABASE_URL."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "SUPABASE_URL": "",
        "NEXT_PUBLIC_SUPABASE_URL": f"https://{STAGING_REF}.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": "anon-token-secret"
    }, clear=True):
        s = Settings()
        assert s.SUPABASE_URL == ""
        assert s.SUPABASE_KEY == ""


def test_production_url_fallback_logs_variable_name_and_service_key_requires_explicit_variable():
    """Production URL fallback logs variable NAME, ambiguous SUPABASE_KEY fallback is removed, and anon keys are never promoted."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "PRODUCTION_SUPABASE_REF": PROD_REF,
        "STAGING_SUPABASE_REF": STAGING_REF,
        "SUPABASE_URL": "",
        "NEXT_PUBLIC_SUPABASE_URL": f"https://{PROD_REF}.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "explicit-service-role-key-9999",
        "SUPABASE_KEY": "legacy-ambiguous-key",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": "anon-key-that-must-never-be-service-role",
        "ADMIN_MASTER_KEY": "secure_prod_admin_key_12345",
        "ADMIN_2FA_CODE": "secure_prod_2fa_67890",
        "JWT_SECRET": "secure_prod_jwt_secret_9999"
    }, clear=True):
        with patch("config.logger.warning") as mock_logger:
            s = Settings()
            assert s.SUPABASE_URL == f"https://{PROD_REF}.supabase.co"
            assert s.SUPABASE_KEY == "explicit-service-role-key-9999"
            # Verify URL fallback variable NAME is logged
            assert any("NEXT_PUBLIC_SUPABASE_URL" in call[0][0] for call in mock_logger.call_args_list)

    # Prove that ambiguous SUPABASE_KEY alone is ignored and not used as a fallback
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "PRODUCTION_SUPABASE_REF": PROD_REF,
        "STAGING_SUPABASE_REF": STAGING_REF,
        "SUPABASE_URL": f"https://{PROD_REF}.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "",
        "SUPABASE_KEY": "legacy-ambiguous-key-alone",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY": "public-anon-token-only",
        "ADMIN_MASTER_KEY": "secure_prod_admin_key_12345",
        "ADMIN_2FA_CODE": "secure_prod_2fa_67890"
    }, clear=True):
        s = Settings()
        assert s.SUPABASE_KEY == ""
        assert s.SUPABASE_ANON_KEY == "public-anon-token-only"


def test_server_environments_fail_closed_without_explicit_service_role_key():
    """In production or staging, targeting a cloud database without SUPABASE_SERVICE_ROLE_KEY fails closed."""
    for env, ref in [("production", PROD_REF), ("staging", STAGING_REF)]:
        with patch.dict(os.environ, {
            "ENVIRONMENT": env,
            "PRODUCTION_SUPABASE_REF": PROD_REF,
            "STAGING_SUPABASE_REF": STAGING_REF,
            "SUPABASE_URL": f"https://{ref}.supabase.co",
            "SUPABASE_SERVICE_ROLE_KEY": "",
            "ADMIN_MASTER_KEY": "secure_admin_key_12345",
            "ADMIN_2FA_CODE": "secure_2fa_67890",
            "JWT_SECRET": "secure_jwt_secret_9999"
        }, clear=True):
            s = Settings()
            with pytest.raises(RuntimeError, match="SUPABASE_SERVICE_ROLE_KEY must be explicitly configured"):
                s.validate_security_invariants()


def test_production_cors_allowlist_enforcement():
    """In production, CORS origins must match the explicit allowlist pattern; untrusted origins fail closed."""
    # Valid production origins succeed
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "ADMIN_MASTER_KEY": "secure_prod_admin_key_12345",
        "ADMIN_2FA_CODE": "secure_prod_2fa_67890",
        "JWT_SECRET": "secure_prod_jwt_secret_9999",
        "FRONTEND_URL": "https://app.welele.media"
    }, clear=True):
        s = Settings()
        s.validate_security_invariants()
        assert "https://app.welele.media" in s.CORS_ORIGINS

    # Untrusted domain fails closed
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "ADMIN_MASTER_KEY": "secure_prod_admin_key_12345",
        "ADMIN_2FA_CODE": "secure_prod_2fa_67890",
        "JWT_SECRET": "secure_prod_jwt_secret_9999",
        "FRONTEND_URL": "https://attacker.example.com"
    }, clear=True):
        s = Settings()
        with pytest.raises(RuntimeError, match="Production CORS origin .* is not in the explicit production allowlist"):
            s.validate_security_invariants()


# ==============================================================================
# 4. Strict Allowlist Enforcement & Deployment Variables
# ==============================================================================

def test_missing_allowlist_configuration_fails_closed():
    """Missing PRODUCTION_SUPABASE_REF or STAGING_SUPABASE_REF environment variables fails closed."""
    # Missing PRODUCTION_SUPABASE_REF
    with patch.dict(os.environ, {"STAGING_SUPABASE_REF": STAGING_REF}, clear=True):
        with pytest.raises(RuntimeError, match="Missing required 'PRODUCTION_SUPABASE_REF'"):
            validate_database_target("production", f"https://{PROD_REF}.supabase.co")

    # Missing STAGING_SUPABASE_REF
    with patch.dict(os.environ, {"PRODUCTION_SUPABASE_REF": PROD_REF}, clear=True):
        with pytest.raises(RuntimeError, match="Missing required 'STAGING_SUPABASE_REF'"):
            validate_database_target("staging", f"https://{STAGING_REF}.supabase.co")


def test_test_environment_permanently_blocks_cloud_access():
    """In test mode, any cloud target URL or project ref raises RuntimeError even without allowlist."""
    with pytest.raises(RuntimeError, match="Test environment cannot target cloud Supabase instance"):
        validate_database_target("test", f"https://{PROD_REF}.supabase.co")

    with pytest.raises(RuntimeError, match="Test environment cannot target cloud Supabase instance"):
        validate_database_target("test", f"https://{STAGING_REF}.supabase.co")


def test_production_environment_restricted_to_production_project():
    """Production may ONLY target production project. Fails closed on staging or arbitrary targets."""
    with patch.dict(os.environ, {
        "PRODUCTION_SUPABASE_REF": PROD_REF,
        "STAGING_SUPABASE_REF": STAGING_REF
    }):
        # Targeting production succeeds
        validate_database_target("production", f"https://{PROD_REF}.supabase.co")

        # Targeting staging from production fails closed
        with pytest.raises(RuntimeError, match="Production environment attempted connection to staging project"):
            validate_database_target("production", f"https://{STAGING_REF}.supabase.co")

        # Targeting arbitrary ref fails closed
        with pytest.raises(RuntimeError, match="Production environment configured with unapproved project ref"):
            validate_database_target("production", "https://unauthorized-ref.supabase.co")


def test_development_and_staging_restricted_to_staging_project():
    """Development and staging may ONLY target staging project. Fails closed on production or arbitrary targets."""
    with patch.dict(os.environ, {
        "PRODUCTION_SUPABASE_REF": PROD_REF,
        "STAGING_SUPABASE_REF": STAGING_REF
    }):
        for env in ("development", "staging"):
            # Targeting staging succeeds
            validate_database_target(env, f"https://{STAGING_REF}.supabase.co")

            # Targeting production fails closed
            with pytest.raises(RuntimeError, match="PROTECTED PRODUCTION Supabase project"):
                validate_database_target(env, f"https://{PROD_REF}.supabase.co")

            # Targeting arbitrary ref fails closed
            with pytest.raises(RuntimeError, match="Non-production cloud access is restricted strictly to staging project"):
                validate_database_target(env, "https://unauthorized-ref.supabase.co")


def test_unset_or_invalid_environment_fails_closed():
    """Unset or unrecognised environments fail closed against any cloud target."""
    with patch.dict(os.environ, {
        "PRODUCTION_SUPABASE_REF": PROD_REF,
        "STAGING_SUPABASE_REF": STAGING_REF
    }):
        for bad_env in ("", "qa", "preview", "unknown", None):
            with pytest.raises(RuntimeError, match="Unrecognised or unset ENVIRONMENT"):
                validate_database_target(bad_env, f"https://{PROD_REF}.supabase.co")

            with pytest.raises(RuntimeError, match="Unrecognised or unset ENVIRONMENT"):
                validate_database_target(bad_env, f"https://{STAGING_REF}.supabase.co")


def test_allowlist_identical_refs_fails_closed():
    """Fails closed if misconfigured with identical staging and production refs."""
    with patch.dict(os.environ, {
        "PRODUCTION_SUPABASE_REF": "same_reference_00000",
        "STAGING_SUPABASE_REF": "same_reference_00000"
    }):
        with pytest.raises(RuntimeError, match="cannot be identical"):
            get_project_allowlist()


# ==============================================================================
# 5. Invalid Production Configuration Fail-Closed Tests
# ==============================================================================

def test_production_fails_closed_on_missing_admin_master_key():
    """Production fails closed if ADMIN_MASTER_KEY is missing or empty."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "ADMIN_MASTER_KEY": "",
        "ADMIN_2FA_CODE": "prod_2fa_secure_123"
    }, clear=True):
        s = Settings()
        with pytest.raises(RuntimeError, match="ADMIN_MASTER_KEY is not configured in production"):
            s.validate_security_invariants()


def test_production_fails_closed_on_forbidden_dev_admin_key():
    """Production fails closed if ADMIN_MASTER_KEY uses known dev/default secrets."""
    for forbidden_key in Settings.FORBIDDEN_PROD_ADMIN_KEYS:
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "ADMIN_MASTER_KEY": forbidden_key,
            "ADMIN_2FA_CODE": "prod_2fa_secure_123"
        }, clear=True):
            s = Settings()
            with pytest.raises(RuntimeError, match="prohibited default/dev secret"):
                s.validate_security_invariants()


def test_production_fails_closed_on_missing_2fa_code():
    """Production fails closed if ADMIN_2FA_CODE is missing or empty."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "ADMIN_MASTER_KEY": "valid_prod_admin_master_key_9999",
        "ADMIN_2FA_CODE": ""
    }, clear=True):
        s = Settings()
        with pytest.raises(RuntimeError, match="ADMIN_2FA_CODE is not configured in production"):
            s.validate_security_invariants()


# ==============================================================================
# 6. Client Construction Paths & Test Mode Protection
# ==============================================================================

def test_database_singleton_and_repositories_cannot_instantiate_client_in_test_mode():
    """Database singleton and BaseRepository refuse cloud client construction in test mode."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "test",
        "SUPABASE_URL": f"https://{STAGING_REF}.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "fake-key"
    }):
        # Database singleton
        db_instance = Database()
        assert db_instance.is_live is False
        assert db_instance.supabase_client is None

        # Base repository
        repo = BaseRepository()
        assert repo.is_live is False
        assert repo._supabase is None


def test_audit_service_genesis_is_purely_local_and_zero_remote_sync_in_test():
    """AuditService.__init__ and genesis creation are 100% local, and record_trust_event never syncs remotely in test."""
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        audit = AuditService()
        assert audit.is_live is False
        assert audit._supabase is None

        # Genesis block was created in local database
        local_entries = db.get("security_audit_ledger")
        assert len(local_entries) >= 1
        genesis = local_entries[0]
        assert genesis["event_type"] == "trust_ledger.genesis"
        assert genesis["sequence_id"] == 1

        # Recording new trust event in test mode
        event = audit.record_trust_event(
            domain="SECURITY",
            event_type="test.isolated.audit",
            actor_id="test_suite",
            actor_role="qa",
            target_type="system",
            target_id="isolation_guard",
            after_state={"isolated": True}
        )

        assert event["event_id"].startswith("aud_")
        assert any(e["event_id"] == event["event_id"] for e in db.get("security_audit_ledger"))
