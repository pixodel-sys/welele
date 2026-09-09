"""
Welele Media™ — Digital IP Engine API Router (GAP-001 & GAP-005)
Endpoints for canonical IP management, character bibles, multi-party rights,
and story package persistence with IP domain audit logging.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from repositories.ip_repository import ip_repository
from schemas.ip_schemas import (
    CreateIPRequest,
    StoryForgePackageCreateRequest,
    IPResponse,
    IPDetailResponse
)
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service

router = APIRouter(prefix="/ip", tags=["Digital IP Engine"])

@router.get("/list", response_model=List[Dict[str, Any]])
def list_digital_ips():
    """Returns list of all canonical Digital IP franchises."""
    return ip_repository.list_ips()

@router.get("/{ip_id}", response_model=IPDetailResponse)
def get_ip_detail(ip_id: str):
    """Returns full Digital IP hierarchy (Story World, Character Bibles, Rights Ledger, Series, Packages)."""
    detail = ip_repository.get_ip_detail(ip_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Digital IP franchise not found")
    return detail

@router.post("/create", response_model=IPDetailResponse, dependencies=[Depends(require_role(["creator", "admin"]))])
def create_digital_ip(req: CreateIPRequest, auth_user: dict = Depends(get_current_user)):
    """Creates a canonical Digital IP entity with story world rules, character bibles, and rights splits."""
    try:
        ip_detail = ip_repository.create_ip(req)

        audit_service.record_trust_event(
            domain="IP",
            event_type="ip.created",
            actor_id=auth_user.get("sub", req.master_owner_id),
            actor_role=auth_user.get("role", "creator"),
            target_type="digital_ip",
            target_id=ip_detail["ip"]["id"],
            after_state={"title": req.title, "master_owner_id": req.master_owner_id, "valuation": getattr(req, "global_valuation_usd", 0.0)},
            metadata={"franchise_code": req.franchise_code}
        )

        return ip_detail
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ip_id}/story-forge/save", dependencies=[Depends(require_role(["creator", "admin"]))])
def save_story_forge_package(ip_id: str, req: StoryForgePackageCreateRequest, auth_user: dict = Depends(get_current_user)):
    """Persists an AI-generated Story Forge package as a versioned institutional narrative asset."""
    req.ip_id = ip_id
    saved = ip_repository.save_story_forge_package(req)

    audit_service.record_trust_event(
        domain="IP",
        event_type="ip.story_package_created",
        actor_id=auth_user.get("sub", req.creator_id),
        actor_role=auth_user.get("role", "creator"),
        target_type="story_package",
        target_id=saved["id"],
        after_state={"package_title": req.package_title, "version": req.version, "ip_id": ip_id},
        metadata={"beats_count": len(req.beats), "ai_model": req.ai_model_used}
    )

    return {"success": True, "package": saved}
