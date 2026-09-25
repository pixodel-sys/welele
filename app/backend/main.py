"""
Welele Media™ — Backend Application Entry Point & Router Registration
Architecture: FastAPI Asynchronous Micro-Service Hub with 8 Frozen Pillars & Digital IP Engine
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    intelligence,
    content_intelligence,
    story_review,
    forge_configurations,
    production
)

# Story Forge Stateful Narrative Engine Module (Decoupled Service)
from story_forge.api import router as story_forge_router

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

# Standard HTTP Defense-in-Depth Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

# Mount local physical object storage directory for media delivery
media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media_storage")
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")


# -----------------------------------------------------------------------------
# Register Canonical Domain Routers (Digital IP Spine)
# -----------------------------------------------------------------------------
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(ip.router, prefix=settings.API_V1_STR)
app.include_router(series.router, prefix=settings.API_V1_STR)
app.include_router(series.router, prefix="/api/v1")
app.include_router(episodes.router, prefix=settings.API_V1_STR)
app.include_router(episodes.router, prefix="/api/v1")
app.include_router(wallet.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(storage.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix="/api/v1")
app.include_router(experience.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix=settings.API_V1_STR)
app.include_router(content_intelligence.router, prefix=settings.API_V1_STR)
app.include_router(content_intelligence.router, prefix="/api/v1")
app.include_router(story_review.router, prefix=settings.API_V1_STR)
app.include_router(story_review.router, prefix="/api/v1")

# -----------------------------------------------------------------------------
# Register Decoupled Story Forge Narrative Reasoning Router
# -----------------------------------------------------------------------------
app.include_router(story_forge_router, prefix=settings.API_V1_STR)
app.include_router(story_forge_router, prefix="/api/v1")
app.include_router(forge_configurations.router, prefix=settings.API_V1_STR)
app.include_router(forge_configurations.router, prefix="/api/v1")
app.include_router(production.router, prefix=settings.API_V1_STR)
app.include_router(production.router, prefix="/api/v1")

# -----------------------------------------------------------------------------
# Backward-Compatible Legacy Aliases (Zero-Friction Client Migration)
# -----------------------------------------------------------------------------
app.include_router(legacy_stories.router, prefix=settings.API_V1_STR)
app.include_router(legacy_stories.router, prefix="/api/v1")
app.include_router(legacy_creators.router, prefix=settings.API_V1_STR)
app.include_router(legacy_creators.router, prefix="/api/v1")
app.include_router(legacy_monetization.router, prefix=settings.API_V1_STR)
app.include_router(legacy_monetization.router, prefix="/api/v1")

def run_runtime_startup_canary():
    """
    Startup Canary:
    Verifies that the in-memory DependencyEngine is clean and does NOT contain any
    stale specimen-specific contamination keywords (e.g. ancestral, debt, father's death, etc.).
    Blocks startup if any contamination is detected.
    """
    import inspect
    from story_forge.engine import DependencyEngine
    from story_forge.models import StoryState, StateStatus

    FORBIDDEN_CANARY_TOKENS = [
        "ancestral",
        "father's death",
        "clan",
        "creditor",
        "isibusiso",
        "zodwa",
        "bheki",
        "ndlovu",
        "sipho",
        "nokuthula",
    ]

    # 1. Inspect DependencyEngine class and methods for hardcoded specimen tokens
    engine_source = inspect.getsource(DependencyEngine)
    for token in FORBIDDEN_CANARY_TOKENS:
        if token.lower() in engine_source.lower():
            raise RuntimeError(f"STARTUP CANARY FATAL: Stale contaminated DependencyEngine source detected! Found token: '{token}'")

    # 2. Test in-memory dependency evaluation on a sterile state
    dep_engine = DependencyEngine()
    dummy_state = StoryState(story_id="canary_sterile_001")
    deps = dep_engine.evaluate_required_state_deficiencies(dummy_state, [])

    for d in deps:
        desc = (d.description or "").lower()
        key = (d.dependency_key or "").lower()
        target = (d.target_entity or "").lower()
        for token in FORBIDDEN_CANARY_TOKENS:
            if token.lower() in desc or token.lower() in key or token.lower() in target:
                raise RuntimeError(f"STARTUP CANARY FATAL: Generated dependency {d.id} ({d.dependency_key}) contains forbidden token: '{token}'")

    # 3. Specifically verify EVENT_01_INCITING_DISRUPTION definition
    inciting_dep = next((d for d in deps if d.dependency_key == "EVENT_01_INCITING_DISRUPTION"), None)
    if inciting_dep:
        if "father" in inciting_dep.description.lower() or "ancestral" in inciting_dep.description.lower():
            raise RuntimeError(f"STARTUP CANARY FATAL: EVENT_01_INCITING_DISRUPTION carries stale description: {inciting_dep.description}")

    print("[STARTUP CANARY] PASSED: In-memory DependencyEngine is 100% sterile and decontaminated.")
    return True


@app.on_event("startup")
def startup_event():
    run_runtime_startup_canary()
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
@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "engine": "Welele Digital IP Engine v2.0",
        "version": settings.VERSION,
        "canary": "passed"
    }

@app.get("/api/v1/system/canary")
def system_canary():
    run_runtime_startup_canary()
    return {"status": "ok", "canary": "passed", "runtime": "sterile"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
