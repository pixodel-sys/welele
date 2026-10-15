import os
import logging
from typing import Optional
from dotenv import load_dotenv
from target_validator import get_resolved_environment, validate_database_target, VALID_ENVIRONMENTS

logger = logging.getLogger("welele.config")

# Environment resolution and loader design:
# - The server loads app/.env.{ENVIRONMENT}, never a bare .env.
# - ENVIRONMENT must be explicitly set. NODE_ENV is NOT used as a Python fallback.
# - Conflicting environment declarations fail closed.
# - 'test' loads NO cloud env file and may not construct a cloud client.
# - 'development' loads app/.env.development (pointing at staging).
# - 'staging' loads app/.env.staging.
# - 'production' loads app/.env.production.
# - Unset or unrecognised environments load NO file.
_resolved_env = get_resolved_environment()

if _resolved_env in ("development", "staging", "production"):
    _root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _env_file = os.path.join(_root_dir, f".env.{_resolved_env}")
    if os.path.exists(_env_file):
        load_dotenv(dotenv_path=_env_file, override=False)


class Settings:
    PROJECT_NAME: str = "Welele™ Media Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Known development-only credential tokens that are strictly prohibited in production/staging
    FORBIDDEN_PROD_ADMIN_KEYS: tuple = (
        "admin_master_welele_2026",
        "dev_admin_secret_local_only",
        "admin",
        "password",
        "123456",
        "welele_dev_pass"
    )

    # Known insecure/default JWT secrets prohibited in production/staging
    FORBIDDEN_PROD_JWT_SECRETS: tuple = (
        "welele_dev_secret_key_local_only",
        "dev_secret_insecure_local_only",
        "secret",
        "jwt_secret",
        "changeme",
        "123456",
        "password",
        "default"
    )

    _is_prod_staging_override: Optional[bool] = None

    @property
    def IS_PRODUCTION_OR_STAGING(self) -> bool:
        if getattr(self, "_is_prod_staging_override", None) is not None:
            return self._is_prod_staging_override
        return self.ENVIRONMENT in ("staging", "production")

    @IS_PRODUCTION_OR_STAGING.setter
    def IS_PRODUCTION_OR_STAGING(self, val: bool):
        self._is_prod_staging_override = val

    @IS_PRODUCTION_OR_STAGING.deleter
    def IS_PRODUCTION_OR_STAGING(self):
        self._is_prod_staging_override = None

    def __init__(self):
        self._is_prod_staging_override = None
        self.ENVIRONMENT: str = get_resolved_environment()
        self.ENABLE_STARTUP_SEED: bool = os.getenv("ENABLE_STARTUP_SEED", "false").lower() in ("true", "1", "yes")

        if self.ENVIRONMENT in ("production", "prod"):
            base_origins = [
                "https://welele.media",
                "https://welele.pages.dev"
            ]
        elif self.ENVIRONMENT == "staging":
            base_origins = [
                "https://staging.welele-staging.pages.dev",
                "https://welele-staging.pixodel.workers.dev",
                "https://staging.welele.app",
                "https://welele.pages.dev",
                "https://welele.media",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]
        else:
            base_origins = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "https://staging.welele-staging.pages.dev",
                "https://welele.pages.dev",
                "https://welele.media"
            ]

        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url:
            cleaned_frontend = frontend_url.strip().rstrip("/")
            if cleaned_frontend and cleaned_frontend not in base_origins:
                base_origins.append(cleaned_frontend)

        env_cors = os.getenv("CORS_ORIGINS")
        if env_cors:
            for origin in env_cors.split(","):
                cleaned = origin.strip().rstrip("/")
                if cleaned and cleaned not in base_origins:
                    base_origins.append(cleaned)

        self.CORS_ORIGINS: list = base_origins
        self.DATA_FILE: str = os.path.join(os.path.dirname(__file__), "data", "welele_store.json")

        # Authoritative Supabase PostgreSQL Connection
        # Test environment NEVER receives cloud URLs or keys, even if present in process env
        if self.ENVIRONMENT == "test":
            self.SUPABASE_URL: str = ""
            self.SUPABASE_KEY: str = ""
            self.SUPABASE_ANON_KEY: str = ""
            self.SUPABASE_JWT_SECRET: str = ""
        elif self.ENVIRONMENT == "production":
            # In production: URL fallback is logged; service key requires explicit SUPABASE_SERVICE_ROLE_KEY
            supabase_url = os.getenv("SUPABASE_URL")
            if not supabase_url:
                if os.getenv("NEXT_PUBLIC_SUPABASE_URL"):
                    logger.warning("[Config:Production] SUPABASE_URL not set; using fallback variable NEXT_PUBLIC_SUPABASE_URL")
                    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
                else:
                    supabase_url = ""
            self.SUPABASE_URL: str = supabase_url or ""

            # Explicit service role key: ambiguous fallbacks to SUPABASE_KEY or anon keys are removed
            self.SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
            self.SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""
            self.SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET") or ""
        else:
            # Non-production (development, staging, or unrecognised):
            # Strictly NO fallback to NEXT_PUBLIC_* or legacy aliases
            self.SUPABASE_URL: str = os.getenv("SUPABASE_URL") or ""
            self.SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
            self.SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY") or ""
            self.SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET") or ""

        self.JWT_SECRET: str = os.getenv("JWT_SECRET") or self.SUPABASE_JWT_SECRET or ("dev_secret_insecure_local_only" if not self.IS_PRODUCTION_OR_STAGING else "")

        # Security & Administration
        # Required secrets must be supplied via environment variables; never hardcoded in code.
        self.ADMIN_MASTER_KEY: str = os.getenv("ADMIN_MASTER_KEY", "")
        self.ADMIN_2FA_CODE: str = os.getenv("ADMIN_2FA_CODE", "")

        # Cloud Object Storage (Pillar 4 / Cloudflare R2)
        self.CDN_BASE_URL: str = os.getenv("CDN_BASE_URL", "https://cdn.welele.media").rstrip("/")
        self.STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET") or os.getenv("R2_BUCKET_NAME", "welele-vod-masters")
        self.R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID") or ""
        self.R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID") or ""
        self.R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY") or ""
        self.R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME") or self.STORAGE_BUCKET

        # Google Gemini AI (Pillar 8)
        self.GEMINI_API_KEY: str = (
            os.getenv("GEMINI_API_KEY") or 
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("VITE_GEMINI_API_KEY") or 
            ""
        )
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        # SMSPortal Integration (Viewer Phone OTP)
        self.SMSPORTAL_CLIENT_ID: str = (
            os.getenv("SMSPORTAL_CLIENT_ID") or
            os.getenv("Client ID (username)") or
            os.getenv("SMSPORTAL_USERNAME") or
            ""
        )
        self.SMSPORTAL_API_SECRET: str = (
            os.getenv("SMSPORTAL_API_SECRET") or
            os.getenv("API Secret (password)") or
            os.getenv("SMSPORTAL_PASSWORD") or
            ""
        )

    def validate_security_invariants(self):
        """Enforces that environments fail closed, environments are explicitly declared, and admin secrets are guarded."""
        if self.ENVIRONMENT not in VALID_ENVIRONMENTS:
            raise RuntimeError(
                f"CRITICAL CONFIGURATION ERROR: ENVIRONMENT must be explicitly set to one of {VALID_ENVIRONMENTS}. "
                f"Got: '{self.ENVIRONMENT}'. Silent fallback to development is prohibited."
            )

        # Validate production origins against explicit allowlist
        if self.ENVIRONMENT in ("production", "prod"):
            import urllib.parse
            allowed_prod_domains = ("welele.media", "welele.app", "welele.pages.dev", "pixodel.workers.dev")
            for origin in self.CORS_ORIGINS:
                parsed = urllib.parse.urlsplit(origin)
                host = parsed.hostname or ""
                if not any(host == d or host.endswith("." + d) for d in allowed_prod_domains):
                    raise RuntimeError(
                        f"CRITICAL SECURITY HALT: Production CORS origin '{origin}' is not in the explicit production allowlist. "
                        f"Production origins must belong to one of: {allowed_prod_domains}"
                    )

        # Validate database target against fail-closed guard
        if self.SUPABASE_URL:
            validate_database_target(self.ENVIRONMENT, self.SUPABASE_URL)
            if self.IS_PRODUCTION_OR_STAGING:
                if not self.SUPABASE_KEY or not self.SUPABASE_KEY.strip():
                    raise RuntimeError(
                        f"CRITICAL SECURITY HALT: SUPABASE_SERVICE_ROLE_KEY must be explicitly configured when SUPABASE_URL is set in {self.ENVIRONMENT}. "
                        "Ambiguous service key fallbacks are prohibited."
                    )

        if self.IS_PRODUCTION_OR_STAGING:
            if not self.ADMIN_MASTER_KEY or not self.ADMIN_MASTER_KEY.strip():
                raise RuntimeError(
                    f"CRITICAL SECURITY HALT: ADMIN_MASTER_KEY is not configured in {self.ENVIRONMENT}. "
                    "Production/staging environments must fail closed when required administrative secrets are absent."
                )
            if self.ADMIN_MASTER_KEY.strip() in self.FORBIDDEN_PROD_ADMIN_KEYS:
                raise RuntimeError(
                    f"CRITICAL SECURITY HALT: ADMIN_MASTER_KEY in {self.ENVIRONMENT} is set to a prohibited default/dev secret ('{self.ADMIN_MASTER_KEY}'). "
                    "Production configuration cannot start with known/default admin credentials."
                )
            if not self.ADMIN_2FA_CODE or not self.ADMIN_2FA_CODE.strip():
                raise RuntimeError(
                    f"CRITICAL SECURITY HALT: ADMIN_2FA_CODE is not configured in {self.ENVIRONMENT}. "
                    "Multi-factor authentication (2FA) is mandatory for enterprise administration in production/staging."
                )
            jwt_sec = (self.JWT_SECRET or self.SUPABASE_JWT_SECRET or "").strip()
            if not jwt_sec:
                raise RuntimeError(
                    f"CRITICAL SECURITY HALT: JWT_SECRET or SUPABASE_JWT_SECRET is not configured in {self.ENVIRONMENT}. "
                    "Production/staging environments must fail closed when required JWT signing secrets are absent."
                )
            if jwt_sec in self.FORBIDDEN_PROD_JWT_SECRETS:
                raise RuntimeError(
                    f"CRITICAL SECURITY HALT: JWT secret in {self.ENVIRONMENT} is set to a prohibited default/dev secret ('{jwt_sec}'). "
                    "Production/staging configuration cannot start with known insecure/fallback JWT secrets."
                )

    # Cloud Object Storage (Pillar 4 / Cloudflare R2)
    CDN_BASE_URL: str = os.getenv("CDN_BASE_URL", "https://cdn.welele.media").rstrip("/")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET") or os.getenv("R2_BUCKET_NAME", "welele-vod-masters")
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID") or ""
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID") or ""
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY") or ""
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME") or STORAGE_BUCKET

    # Google Gemini AI (Pillar 8)
    GEMINI_API_KEY: str = (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("VITE_GEMINI_API_KEY") or 
        ""
    )
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

settings = Settings()
settings.validate_security_invariants()
