import os
from dotenv import load_dotenv

# Search for .env in parent root and current dir
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

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

    def __init__(self):
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT") or os.getenv("APP_ENV") or os.getenv("NODE_ENV") or "development"
        self.IS_PRODUCTION_OR_STAGING: bool = self.ENVIRONMENT.lower() in ("staging", "production", "prod")
        self.ENABLE_STARTUP_SEED: bool = os.getenv("ENABLE_STARTUP_SEED", "false").lower() in ("true", "1", "yes")

        self.CORS_ORIGINS: list = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://staging.welele-staging.pages.dev",
            "https://welele.pages.dev",
            "https://welele.media"
        ]
        self.DATA_FILE: str = os.path.join(os.path.dirname(__file__), "data", "welele_store.json")

        # Authoritative Supabase PostgreSQL Connection
        self.SUPABASE_URL: str = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
        self.SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""
        self.SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
        self.SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET") or ""
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

    def validate_security_invariants(self):
        """Enforces that production and staging environments fail closed and never use known/default admin secrets."""
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
