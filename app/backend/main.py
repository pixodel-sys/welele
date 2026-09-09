"""
Welele Media™ — Backend Application Entry Point & Router Registration
Architecture: FastAPI Asynchronous Micro-Service Hub with 8 Frozen Pillars
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from seed_data import seed_database_if_empty

# Canonical Domain Routers (Section 5.1 of ARCHITECTURE.md)
from routers import (
    auth,
    series,
    episodes,
    wallet,
    payments,
    storage,
    chat,
    ai,
    admin,
    experience
)

# Backward Compatibility Alias Routers for Frontend Legacy Clients
from routers import (
    stories as legacy_stories,
    creators as legacy_creators,
    monetization as legacy_monetization
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Welele Media™ — Vertical Micro-Drama Streaming & Monetisation Platform API"
)

# CORS configuration for PWA Mobile & Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Register Canonical Domain Routers (Manifesto Specification 5.1)
# -----------------------------------------------------------------------------
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(series.router, prefix=settings.API_V1_STR)
app.include_router(episodes.router, prefix=settings.API_V1_STR)
app.include_router(wallet.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(storage.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(experience.router, prefix=settings.API_V1_STR)

# -----------------------------------------------------------------------------
# Backward-Compatible Legacy Aliases (Zero-Friction Client Migration)
# -----------------------------------------------------------------------------
app.include_router(legacy_stories.router, prefix=settings.API_V1_STR)
app.include_router(legacy_creators.router, prefix=settings.API_V1_STR)
app.include_router(legacy_monetization.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    seed_database_if_empty()

@app.get("/")
def root():
    return {
        "brand": "Welele™",
        "parent": "Welele Media™",
        "manifesto_version": "1.0 (Frozen)",
        "pillars": [
            "1. 9:16 Canonical Viewer",
            "2. PWA First Architecture",
            "3. Relational Transaction Core",
            "4. Object Storage + CDN Media",
            "5. Unified Payment Abstraction",
            "6. Regional Monetisation Provider Pattern",
            "7. Content as the Primary Asset",
            "8. Community Embedded in the Stream"
        ],
        "status": "online",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
