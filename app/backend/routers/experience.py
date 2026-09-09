"""
Welele Media™ — Experience Engine API Router (WEE Layer 3: Delivery)
Public client layout delivery, draft authoring, and simulated time-travel preview endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime
from services.experience_engine import ExperienceEngine
from schemas.experience_schemas import (
    ExperienceManifest,
    SaveDraftRequest,
    PublishRequest
)

router = APIRouter(prefix="/experience", tags=["Experience Engine (WEE)"])

@router.get("/pages")
def list_managed_pages():
    """List all pages controlled by the Welele Experience Engine."""
    return {
        "pages": [
            {"page_id": "home", "title": "Home / Showcase", "route": "/"},
            {"page_id": "discover", "title": "Discovery / Catalog", "route": "/discover"}
        ]
    }

@router.get("/page/{page_id}")
def get_live_page_experience(page_id: str):
    """
    Public live layout delivery for client surface renderers (Mobile PWA, Desktop, TV).
    Resolves catalog hydration, active temporal windows, and merchandising overrides.
    """
    manifest = ExperienceEngine.resolve_manifest(page_id=page_id, state="published")
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Page experience '{page_id}' not found.")
    return manifest

@router.get("/preview/{page_id}")
def preview_page_experience(
    page_id: str,
    state: str = Query("draft", pattern="^(draft|published)$"),
    simulated_time: Optional[str] = Query(None, description="ISO 8601 simulated timestamp for time-travel testing")
):
    """
    Authenticated / Admin Studio endpoint for time-travel and draft simulation.
    Allows Content Managers to preview the exact UX as it will appear at any future date/time.
    """
    eval_dt = None
    if simulated_time:
        try:
            eval_dt = datetime.fromisoformat(simulated_time.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid ISO 8601 simulated_time format.")

    manifest = ExperienceEngine.resolve_manifest(page_id=page_id, state=state, eval_time=eval_dt)
    return manifest

@router.put("/page/{page_id}/draft")
def save_page_draft(page_id: str, request: SaveDraftRequest):
    """Save working draft layout for a page in Welele Admin Studio."""
    current_draft = ExperienceEngine.get_stored_manifest(page_id, state="draft")
    
    # Update fields
    if request.meta:
        current_draft["meta"] = request.meta.model_dump()
    current_draft["sections"] = [s.model_dump() for s in request.sections]
    current_draft["status"] = "draft"
    current_draft["updated_at"] = datetime.utcnow().isoformat() + "Z"

    ExperienceEngine.save_layout(current_draft)
    return {"status": "saved", "page_id": page_id, "updated_at": current_draft["updated_at"]}

@router.post("/page/{page_id}/publish")
def publish_page_experience(page_id: str, request: Optional[PublishRequest] = None):
    """
    Promotes draft layout to LIVE production status.
    Increments layout version string and records timestamp.
    """
    draft = ExperienceEngine.get_stored_manifest(page_id, state="draft")
    
    # Generate new version tag
    now_str = datetime.utcnow().strftime("%Y.%m.%d")
    version = f"{now_str}.v{int(datetime.utcnow().timestamp()) % 1000}"

    live_manifest = {
        **draft,
        "status": "published",
        "version": version,
        "published_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    ExperienceEngine.save_layout(live_manifest)
    return {
        "status": "published",
        "page_id": page_id,
        "version": version,
        "published_at": live_manifest["published_at"]
    }

@router.post("/page/{page_id}/reset-default")
def reset_page_to_default(page_id: str):
    """Reset a page's layout back to canonical platform preset."""
    if page_id == "home":
        default_layout = ExperienceEngine.get_default_home_manifest()
    elif page_id == "discover":
        default_layout = ExperienceEngine.get_default_discover_manifest()
    else:
        raise HTTPException(status_code=400, detail=f"No default preset for page '{page_id}'.")

    ExperienceEngine.save_layout(default_layout)
    # Also update draft
    draft = {**default_layout, "status": "draft"}
    ExperienceEngine.save_layout(draft)

    return {"status": "reset_successful", "page_id": page_id}
