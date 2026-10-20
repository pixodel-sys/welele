"""
Welele Media™ — Experience Engine API Router (WEE Layer 3: Delivery & Institutional Trust)
Public client layout delivery, draft authoring, and simulated time-travel preview endpoints
with strict Admin RBAC protection and EXPERIENCE domain audit logging.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from services.experience_engine import ExperienceEngine
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service
from schemas.experience_schemas import (
    ExperienceManifest,
    SaveDraftRequest,
    PublishRequest
)

from repositories.series_repository import series_repository, to_uuid

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

@router.get("/page/{page_id}/draft", dependencies=[Depends(require_role(["admin"]))])
def get_page_draft_experience(page_id: str):
    """
    Retrieves the raw unhydrated editorial draft layout without executing runtime merchandising resolution.
    Used exclusively by Welele Admin Studio for authoring editorial configurations.
    """
    draft = ExperienceEngine.get_stored_manifest(page_id, state="draft")
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft experience '{page_id}' not found.")
    return draft

@router.get("/preview/{page_id}", dependencies=[Depends(require_role(["admin"]))])
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
    if not manifest:
        manifest = ExperienceEngine.resolve_manifest(page_id=page_id, state="published", eval_time=eval_dt)
    if not manifest:
        manifest = ExperienceEngine.get_default_home_manifest()
    return manifest

@router.put("/page/{page_id}/draft", dependencies=[Depends(require_role(["admin"]))])
def save_page_draft(page_id: str, request: SaveDraftRequest, auth_user: dict = Depends(get_current_user)):
    """Save working draft layout for a page in Welele Admin Studio and record audit event."""
    current_draft = ExperienceEngine.get_stored_manifest(page_id, state="draft")
    now_ts = datetime.now(timezone.utc).isoformat()
    
    # Update fields
    if request.meta:
        current_draft["meta"] = request.meta.model_dump()

    # Clean and canonicalize sections:
    # 1. Prevent dynamic merchandising output from being persisted as editorial configuration
    # 2. Canonicalize known series references to canonical series.id (UUID), preserving unresolved IDs
    feed = series_repository.list_feed()
    known_canonical_ids = {to_uuid(str(s.get("id", ""))) for s in feed}
    known_slugs = {str(s.get("slug")) for s in feed if s.get("slug")}

    clean_sections = []
    for s in request.sections:
        sec_dict = s.model_dump()
        mode = (sec_dict.get("source") or {}).get("mode", "manual").lower()
        items = sec_dict.get("items", [])

        # Strip dynamic fill items from persisted editorial configuration
        if mode in ("hybrid", "algorithmic"):
            items = [
                it for it in items
                if not it.get("slot_id", "").startswith("slot_dyn_")
                and not it.get("is_dynamic")
            ]

        # Canonicalize content_id to series.id (UUID) if known; preserve unresolved IDs exactly
        for it in items:
            cid = it.get("content_id")
            if cid:
                str_cid = str(cid)
                can_uuid = to_uuid(str_cid)
                if can_uuid in known_canonical_ids or str_cid in known_slugs:
                    it["content_id"] = can_uuid

        sec_dict["items"] = items
        clean_sections.append(sec_dict)

    current_draft["sections"] = clean_sections
    current_draft["status"] = "draft"
    current_draft["updated_at"] = now_ts

    try:
        ExperienceEngine.save_layout(current_draft)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    audit_service.record_trust_event(
        domain="EXPERIENCE",
        event_type="experience.layout_changed",
        actor_id=auth_user.get("sub", "admin_supervisor"),
        actor_role="admin",
        target_type="experience_draft",
        target_id=page_id,
        after_state={"sections_count": len(clean_sections), "page_id": page_id},
        metadata={"updated_at": now_ts}
    )

    return {"status": "saved", "page_id": page_id, "updated_at": current_draft["updated_at"]}

@router.post("/page/{page_id}/publish", dependencies=[Depends(require_role(["admin"]))])
def publish_page_experience(page_id: str, request: Optional[PublishRequest] = None, auth_user: dict = Depends(get_current_user)):
    """
    Promotes draft layout to LIVE production status.
    Increments layout version string, records timestamp, and emits EXPERIENCE audit event.
    """
    draft = ExperienceEngine.get_stored_manifest(page_id, state="draft")
    now_ts = datetime.now(timezone.utc).isoformat()
    
    # Generate new version tag
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y.%m.%d")
    version = f"{now_str}.v{int(now_dt.timestamp()) % 1000}"

    live_manifest = {
        **draft,
        "status": "published",
        "version": version,
        "published_at": now_ts,
        "updated_at": now_ts
    }

    try:
        ExperienceEngine.save_layout(live_manifest)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Cannot publish invalid layout: {e}")

    audit_service.record_trust_event(
        domain="EXPERIENCE",
        event_type="experience.draft_published",
        actor_id=auth_user.get("sub", "admin_supervisor"),
        actor_role="admin",
        target_type="experience_manifest",
        target_id=page_id,
        after_state={"version": version, "status": "published", "sections_count": len(live_manifest.get("sections", []))},
        metadata={"published_at": now_ts}
    )

    return {
        "status": "published",
        "page_id": page_id,
        "version": version,
        "published_at": live_manifest["published_at"]
    }

@router.post("/page/{page_id}/reset-default", dependencies=[Depends(require_role(["admin"]))])
def reset_page_to_default(page_id: str, auth_user: dict = Depends(get_current_user)):
    """Reset a page's layout back to canonical platform preset."""
    if page_id == "home":
        default_layout = ExperienceEngine.get_default_home_manifest()
    elif page_id == "discover":
        default_layout = ExperienceEngine.get_default_discover_manifest()
    else:
        raise HTTPException(status_code=400, detail=f"No default preset for page '{page_id}'.")

    ExperienceEngine.save_layout(default_layout)
    draft = {**default_layout, "status": "draft"}
    ExperienceEngine.save_layout(draft)

    audit_service.record_trust_event(
        domain="EXPERIENCE",
        event_type="experience.layout_reset",
        actor_id=auth_user.get("sub", "admin_supervisor"),
        actor_role="admin",
        target_type="experience_manifest",
        target_id=page_id,
        after_state={"status": "reset_default"},
        metadata={"preset": page_id}
    )

    return {"status": "reset_successful", "page_id": page_id}
