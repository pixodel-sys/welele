"""
Welele Media™ — Backend Application Entry Point & Router Registration
Architecture: FastAPI Asynchronous Micro-Service Hub with 8 Frozen Pillars & Digital IP Engine
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from seed_data import seed_database_if_empty

# Canonical Domain Routers (Manifesto Specification 5.1 & Digital IP Spine)
from routers import (
    auth,
    ip,
    series,
    episodes,
    wallet,
    payments,
    storage,
    chat,
    ai,
    admin,
    experience,
    telemetry,
    intelligence
)

# Backward Compatibility Alias Routers for Legacy Clients
from routers import (
    stories as legacy_stories,
    creators as legacy_creators,
    monetization as legacy_monetization
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Welele Media™ — Vertical Micro-Drama Digital IP Engine & Monetisation Platform API"
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
# Register Canonical Domain Routers (Digital IP Spine)
# -----------------------------------------------------------------------------
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(ip.router, prefix=settings.API_V1_STR)
app.include_router(series.router, prefix=settings.API_V1_STR)
app.include_router(episodes.router, prefix=settings.API_V1_STR)
app.include_router(wallet.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(storage.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(experience.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(intelligence.router, prefix=settings.API_V1_STR)

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
        "engine": "Welele Digital IP Engine v2.0",
        "manifesto_version": "2.0 (Canonical IP Spine)",
        "domains": [
            "1. Digital IP Franchises",
            "2. Story World & Character Bibles",
            "3. 9:16 Canonical Viewer",
            "4. Decoupled Media Assets & HLS",
            "5. Double-Entry Accounting Journal",
            "6. WEE Context Decision Engine",
            "7. Audience Telemetry Spine",
            "8. Story Intelligence Loop"
        ],
        "status": "online",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "engine": "Welele Digital IP Engine v2.0",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
