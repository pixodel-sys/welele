"""
Welele Media™ — Digital IP Engine API Router (GAP-001 & GAP-005)
Endpoints for canonical IP management, character bibles, multi-party rights, and story package persistence.
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
def create_digital_ip(req: CreateIPRequest):
    """Creates a canonical Digital IP entity with story world rules, character bibles, and rights splits."""
    try:
        return ip_repository.create_ip(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ip_id}/story-forge/save", dependencies=[Depends(require_role(["creator", "admin"]))])
def save_story_forge_package(ip_id: str, req: StoryForgePackageCreateRequest):
    """Persists an AI-generated Story Forge package as a versioned institutional narrative asset."""
    req.ip_id = ip_id
    saved = ip_repository.save_story_forge_package(req)
    return {"success": True, "package": saved}
