"""
Welele Media™ — Authoritative Supabase Target Validator & Fail-Closed Guard
Prevents unauthorized, unverified, or accidental connections to protected
Supabase environments across all execution contexts.
"""

import os
import re
import urllib.parse
from typing import Optional, Tuple

VALID_ENVIRONMENTS = ("test", "development", "staging", "production")

# Confirmed institutional project references
CONFIRMED_PRODUCTION_REF = "mngyyxqdhjgteezwkxdn"
CONFIRMED_STAGING_REF = "dbsnaidhznofvyffdfni"


def get_resolved_environment() -> str:
    """
    Explicitly resolves Python environment configuration.
    Enforces that:
    1. NODE_ENV is NOT used as a Python fallback.
    2. Conflicting environment declarations (ENVIRONMENT vs APP_ENV) raise RuntimeError.
    3. 'prod' is normalized to 'production'.
    4. Missing or invalid environments are NOT silently converted to 'development'.
    """
    env_var = os.getenv("ENVIRONMENT")
    app_env_var = os.getenv("APP_ENV")

    # Conflict check between explicit declarations
    if env_var and app_env_var:
        norm_env = env_var.strip().lower()
        norm_app = app_env_var.strip().lower()
        if norm_env == "prod":
            norm_env = "production"
        if norm_app == "prod":
            norm_app = "production"
        if norm_env != norm_app:
            raise RuntimeError(
                f"CRITICAL CONFIGURATION ERROR: Conflicting environment declarations detected: "
                f"ENVIRONMENT='{env_var}' vs APP_ENV='{app_env_var}'. Execution halted."
            )

    raw = env_var or app_env_var
    if not raw or not raw.strip():
        return ""

    val = raw.strip().lower()
    if val == "prod":
        val = "production"

    return val


def get_project_allowlist() -> Tuple[str, str]:
    """
    Resolves the allowed project references for production and staging.
    Enforces strict fail-closed deployment semantics:
    PRODUCTION_SUPABASE_REF and STAGING_SUPABASE_REF MUST be explicitly configured
    in the process environment. Missing allowlist configuration fails closed.
    """
    prod_ref = os.getenv("PRODUCTION_SUPABASE_REF", "").strip().lower()
    staging_ref = os.getenv("STAGING_SUPABASE_REF", "").strip().lower()

    if not prod_ref:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Missing required 'PRODUCTION_SUPABASE_REF' environment variable. "
            "Deployments must explicitly declare their authorized production Supabase reference."
        )
    if not staging_ref:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Missing required 'STAGING_SUPABASE_REF' environment variable. "
            "Deployments must explicitly declare their authorized staging Supabase reference."
        )

    if prod_ref == staging_ref:
        raise RuntimeError(
            f"CRITICAL SECURITY CONFIGURATION ERROR: PRODUCTION_SUPABASE_REF and STAGING_SUPABASE_REF cannot be identical ('{prod_ref}')."
        )

    # Independently pinned institutional guardrails:
    # Environment variables cannot be forged or misconfigured to cross project boundaries
    if prod_ref != CONFIRMED_PRODUCTION_REF:
        raise RuntimeError(
            f"CRITICAL SECURITY CONFIGURATION ERROR: PRODUCTION_SUPABASE_REF '{prod_ref}' does not match "
            f"the independently pinned institutional production reference '{CONFIRMED_PRODUCTION_REF}'."
        )
    if staging_ref != CONFIRMED_STAGING_REF:
        raise RuntimeError(
            f"CRITICAL SECURITY CONFIGURATION ERROR: STAGING_SUPABASE_REF '{staging_ref}' does not match "
            f"the independently pinned institutional staging reference '{CONFIRMED_STAGING_REF}'."
        )

    return prod_ref, staging_ref


def extract_project_ref(url_or_ref: Optional[str]) -> Optional[str]:
    """
    Parses and extracts the lowercase project reference from a Supabase URL or token.
    Strictly validates URL forms and rejects malformed or unrecognised cloud targets.
    """
    if not url_or_ref or not url_or_ref.strip():
        return None

    val = url_or_ref.strip()

    # Standalone 20-character lowercase alphanumeric project reference
    if re.match(r"^[a-z0-9]{20}$", val, re.IGNORECASE):
        return val.lower()

    # Strict URL parsing
    try:
        parsed = urllib.parse.urlsplit(val)
    except Exception as e:
        raise RuntimeError(f"CRITICAL SECURITY HALT: Malformed database target URL '{val}': {e}")

    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError(f"CRITICAL SECURITY HALT: Unsupported or malformed target URL format: '{val}'.")

    if parsed.scheme not in ("http", "https"):
        raise RuntimeError(f"CRITICAL SECURITY HALT: Unsupported URL scheme '{parsed.scheme}' in database target: '{val}'.")

    netloc = parsed.netloc.lower()
    match = re.match(r"^([a-z0-9-]+)\.supabase\.(?:co|in)(?::\d+)?$", netloc)
    if not match:
        raise RuntimeError(
            f"CRITICAL SECURITY HALT: Target host '{netloc}' is not a recognized Supabase cloud endpoint."
        )

    return match.group(1).lower()


def validate_database_target(environment: Optional[str], target_url_or_ref: Optional[str]) -> None:
    """
    Authoritative, reusable fail-closed guard for Supabase database targets.
    Enforces strict project allowlist:
    - Test: NO cloud database access permitted under any circumstance.
    - Development and Staging: Staging project ONLY.
    - Production: Production project ONLY.
    """
    ref = extract_project_ref(target_url_or_ref)
    if not ref:
        # Purely local/in-memory operation, no cloud target
        return

    # Normalize environment
    raw_env = (environment or "").strip().lower()
    if raw_env == "prod":
        raw_env = "production"

    # Invariant 1: In 'test' mode, NO cloud connection is permitted under any circumstances
    if raw_env == "test":
        raise RuntimeError(
            f"CRITICAL SECURITY HALT: Test environment cannot target cloud Supabase instance "
            f"(target ref: '{ref}'). All tests must run in isolated local/in-memory mode."
        )

    # Invariant 2: Unset or unrecognised environment fails closed
    if raw_env not in VALID_ENVIRONMENTS:
        raise RuntimeError(
            f"CRITICAL SECURITY HALT: Unrecognised or unset ENVIRONMENT ('{environment}'). "
            f"Cloud database connection to ref '{ref}' is strictly prohibited. "
            f"Must be one of {VALID_ENVIRONMENTS}."
        )

    # Load validated allowlist
    prod_ref, staging_ref = get_project_allowlist()

    # Invariant 3: Production environment: production project ONLY
    if raw_env == "production":
        if ref == CONFIRMED_STAGING_REF or ref == staging_ref:
            raise RuntimeError(
                f"CRITICAL SECURITY HALT: Production environment attempted connection to staging project (ref: '{ref}'). "
                f"Production is restricted strictly to production project '{CONFIRMED_PRODUCTION_REF}'."
            )
        if ref != CONFIRMED_PRODUCTION_REF or ref != prod_ref:
            raise RuntimeError(
                f"CRITICAL SECURITY HALT: Production environment configured with unapproved project ref: '{ref}'. "
                f"Expected production project ref: '{CONFIRMED_PRODUCTION_REF}'."
            )
        return

    # Invariant 4: Development and Staging environments: staging project ONLY
    if raw_env in ("development", "staging"):
        if ref == CONFIRMED_PRODUCTION_REF or ref == prod_ref:
            raise RuntimeError(
                f"CRITICAL SECURITY HALT: Non-production environment '{raw_env}' attempted connection to "
                f"PROTECTED PRODUCTION Supabase project (ref: '{ref}'). Operation permanently blocked."
            )
        if ref != CONFIRMED_STAGING_REF or ref != staging_ref:
            raise RuntimeError(
                f"CRITICAL SECURITY HALT: Environment '{raw_env}' attempted connection to unapproved project ref: '{ref}'. "
                f"Non-production cloud access is restricted strictly to staging project '{CONFIRMED_STAGING_REF}'."
            )
        return
