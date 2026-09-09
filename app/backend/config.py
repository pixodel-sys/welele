import os
from dotenv import load_dotenv

# Search for .env in parent root and current dir
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

class Settings:
    PROJECT_NAME: str = "Welele™ Media Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    DATA_FILE: str = os.path.join(os.path.dirname(__file__), "data", "welele_store.json")

    # Live Supabase PostgreSQL Connection
    SUPABASE_URL: str = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
    SUPABASE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or ""
    SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""

    # Cloud Object Storage (Pillar 4)
    CDN_BASE_URL: str = os.getenv("CDN_BASE_URL", "https://cdn.welele.media")
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "welele-vod-masters")

    # Live Google Gemini AI (Pillar 8)
    GEMINI_API_KEY: str = (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("VITE_GEMINI_API_KEY") or 
        ""
    )
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

settings = Settings()
