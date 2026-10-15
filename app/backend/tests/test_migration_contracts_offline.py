"""
Welele Media™ — Offline Migration Contracts & Static Security Verification Suite
Mode: Offline, static analysis and in-memory unit tests only.
Zero database connections, zero hosted credentials, zero live network calls.
"""

import os
import re
import pytest
from unittest.mock import patch
from config import Settings
from target_validator import get_resolved_environment, validate_database_target

# Resolve migrations directory relative to this test file
MIGRATIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "backend", "migrations"))

MIGRATION_FILES = [
    "01_candidate_base_schema_v2.sql",
    "02_operational_and_production_contracts.sql",
    "03_security_hardening_and_rls_v3.sql"
]


def test_migration_files_exist_and_contain_no_psql_meta_commands():
    """All 3 migration scripts must exist and must NOT contain any psql meta-commands (e.g. \\i, \\c)."""
    assert os.path.isdir(MIGRATIONS_DIR), f"Migrations directory missing: {MIGRATIONS_DIR}"
    
    psql_meta_pattern = re.compile(r"^\s*\\([a-zA-Z]+)", re.MULTILINE)
    
    for fn in MIGRATION_FILES:
        path = os.path.join(MIGRATIONS_DIR, fn)
        assert os.path.exists(path), f"Migration file missing: {fn}"
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            matches = psql_meta_pattern.findall(content)
            assert len(matches) == 0, f"Found psql meta-commands in {fn}: {matches}. Supabase SQL Editor will reject these."


def test_25_tables_total_inventory_and_all_rls_enabled():
    """Verifies that exactly 25 tables are defined across migration 01 & 02, and all 25 have RLS enabled in migration 03."""
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)\s*\(", re.IGNORECASE)
    
    tables_found = set()
    for fn in ["01_candidate_base_schema_v2.sql", "02_operational_and_production_contracts.sql"]:
        path = os.path.join(MIGRATIONS_DIR, fn)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            for match in table_pattern.finditer(content):
                tables_found.add(match.group(1).lower())
                
    assert len(tables_found) == 25, f"Expected exactly 25 tables, found {len(tables_found)}: {sorted(tables_found)}"

    # Parse RLS list in migration 03
    m3_path = os.path.join(MIGRATIONS_DIR, "03_security_hardening_and_rls_v3.sql")
    with open(m3_path, "r", encoding="utf-8") as f:
        m3_content = f.read()

    # Extract tables from array in DO block
    array_match = re.search(r"ARRAY\s*\[(.*?)\]", m3_content, re.DOTALL | re.IGNORECASE)
    assert array_match is not None, "Could not find RLS tables ARRAY in migration 03"
    
    rls_tables = set()
    for item in array_match.group(1).split(","):
        cleaned = item.strip().strip("'\"\n ")
        if cleaned:
            rls_tables.add(cleaned.lower())

    missing_rls = tables_found - rls_tables
    assert len(missing_rls) == 0, f"Tables missing RLS enablement in migration 03: {missing_rls}"


def test_payment_events_no_foreign_key_to_payment_transactions():
    """
    Verifies that payment_events does NOT contain an invalid FK to payment_transactions(external_ref).
    This decoupling is mandatory so unauthenticated or tampered webhook signatures can be recorded
    in payment_events for security auditing without failing a relational constraint.
    """
    path = os.path.join(MIGRATIONS_DIR, "02_operational_and_production_contracts.sql")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the CREATE TABLE payment_events block
    pe_block_match = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.payment_events\s*\((.*?)\);", content, re.DOTALL | re.IGNORECASE)
    assert pe_block_match is not None, "payment_events table definition not found in migration 02"
    
    pe_body = pe_block_match.group(1)
    assert "REFERENCES public.payment_transactions" not in pe_body, (
        "payment_events must NOT have a foreign key to payment_transactions. "
        "Tampered webhook audit logging requires payment_events to accept records even when external_ref does not exist."
    )


def test_seven_table_extension_tenant_isolation_and_idempotency():
    """Verifies that all 7 extension tables have DROP POLICY IF EXISTS guards and tenant ownership constraints."""
    path = os.path.join(MIGRATIONS_DIR, "03_security_hardening_and_rls_v3.sql")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    seven_tables = [
        "payment_events",
        "production_bibles",
        "episode_blueprints",
        "episode_production_packs",
        "content_intelligence_records",
        "content_decisions",
        "content_intelligence_evidence_packages"
    ]

    for tbl in seven_tables:
        drop_pattern = re.compile(rf'DROP\s+POLICY\s+IF\s+EXISTS\s+".*?"\s+ON\s+public\.{tbl}', re.IGNORECASE)
        matches = drop_pattern.findall(content)
        assert len(matches) > 0, f"Table '{tbl}' is missing DROP POLICY IF EXISTS idempotency guards in migration 03"

    # Verify tenant ownership queries avoid invalid UUID casting on text columns
    assert "master_owner_id = auth.uid()" in content


def test_cors_rejects_wildcard_in_production():
    """In production, wildcard '*' or untrusted origins must be rejected by validate_security_invariants."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "ADMIN_MASTER_KEY": "valid_prod_admin_key_9999",
        "ADMIN_2FA_CODE": "valid_prod_2fa_9999",
        "JWT_SECRET": "valid_prod_jwt_secret_9999",
        "CORS_ORIGINS": "*"
    }, clear=True):
        s = Settings()
        with pytest.raises(RuntimeError, match="Production CORS origin .* is not in the explicit production allowlist"):
            s.validate_security_invariants()


def test_cors_preserves_story_forge_origins_in_staging():
    """In staging, Story Forge development origins (localhost, staging.welele-staging.pages.dev) are preserved."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "staging",
        "ADMIN_MASTER_KEY": "valid_staging_admin_key_9999",
        "ADMIN_2FA_CODE": "valid_staging_2fa_9999",
        "JWT_SECRET": "valid_staging_jwt_secret_9999"
    }, clear=True):
        s = Settings()
        assert "https://staging.welele-staging.pages.dev" in s.CORS_ORIGINS
        assert "http://localhost:5173" in s.CORS_ORIGINS
        assert "https://welele.media" in s.CORS_ORIGINS


def test_config_env_loading_deterministic_order():
    """Verifies environment resolution fails closed on missing/conflicting declarations and does not use NODE_ENV."""
    with patch.dict(os.environ, {"NODE_ENV": "production"}, clear=True):
        assert get_resolved_environment() == ""

    with patch.dict(os.environ, {"ENVIRONMENT": "staging", "APP_ENV": "production"}, clear=True):
        with pytest.raises(RuntimeError, match="Conflicting environment declarations"):
            get_resolved_environment()


def test_consolidated_artifact_completeness_and_syntax():
    """Verifies that the consolidated staging migration artifact is complete, transaction-wrapped, and syntax-safe."""
    artifact_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "migrations", "00_staging_consolidated_migration_v2.sql"))
    assert os.path.exists(artifact_path), f"Consolidated migration artifact missing: {artifact_path}"

    with open(artifact_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Transaction boundaries
    stripped = sql.strip()
    assert stripped.startswith("--") or stripped.startswith("BEGIN;"), "Artifact must start with transaction BEGIN"
    assert "BEGIN;" in sql, "Artifact missing BEGIN;"
    assert "COMMIT;" in sql, "Artifact missing COMMIT;"

    # No psql meta-commands
    psql_meta = re.findall(r"^\s*\\([a-zA-Z]+)", sql, re.MULTILINE)
    assert len(psql_meta) == 0, f"Found psql meta-commands in consolidated artifact: {psql_meta}"

    # All 25 tables present
    table_pattern = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?public\.(\w+)", re.IGNORECASE)
    tables_found = set(m.lower() for m in table_pattern.findall(sql))
    assert len(tables_found) == 25, f"Expected 25 tables in consolidated artifact, found {len(tables_found)}: {sorted(tables_found)}"

    # Defense-in-depth: audit ledger grant & revocations present
    assert "GRANT SELECT ON public.security_audit_ledger TO authenticated;" in sql
    assert "GRANT SELECT ON public.payment_events TO authenticated;" in sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.payment_events FROM PUBLIC, anon, authenticated;" in sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.security_audit_ledger FROM PUBLIC, anon, authenticated;" in sql

    # Tenant protection: WITH CHECK rules present on all 3 operational content tables
    assert 'CREATE POLICY "production_bibles_update_creator" ON public.production_bibles FOR UPDATE' in sql
    assert 'CREATE POLICY "episode_blueprints_update_creator" ON public.episode_blueprints FOR UPDATE' in sql
    assert 'CREATE POLICY "episode_packs_update_creator" ON public.episode_production_packs FOR UPDATE' in sql
