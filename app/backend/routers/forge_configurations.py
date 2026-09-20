"""
Welele Media™ — Forge Configuration Registry Router (v1)
Internal provenance endpoints for retrieving and registering immutable Forge configurations.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from repositories.forge_configuration_repository import forge_config_repo
from repositories.ip_repository import ip_repository
from schemas.forge_configuration_schemas import ForgeConfigurationSnapshot, CreateForgeConfigurationRequest
from services.rbac_service import require_role, get_current_user

router = APIRouter(prefix="/forge", tags=["Forge Configuration Registry"])


@router.get("/configurations", response_model=List[ForgeConfigurationSnapshot], dependencies=[Depends(require_role(["creator", "admin"]))])
def list_configurations():
    """Returns all immutable Forge configuration snapshots."""
    return forge_config_repo.list_configurations()


@router.get("/configurations/{forge_configuration_id}", response_model=ForgeConfigurationSnapshot, dependencies=[Depends(require_role(["creator", "admin"]))])
def get_configuration(forge_configuration_id: str):
    """Retrieves a specific immutable configuration snapshot by ID."""
    cfg = forge_config_repo.get_configuration(forge_configuration_id)
    if not cfg:
        raise HTTPException(status_code=404, detail=f"Forge configuration '{forge_configuration_id}' not found.")
    return cfg


@router.post("/configurations", response_model=ForgeConfigurationSnapshot, dependencies=[Depends(require_role(["admin"]))])
def register_configuration(req: CreateForgeConfigurationRequest):
    """
    Registers a new immutable Forge configuration snapshot.
    If an identical configuration exists, returns existing snapshot without mutation.
    """
    return forge_config_repo.register_configuration(
        forge_engine_version=req.forge_engine_version,
        creative_constitution_version=req.creative_constitution_version,
        skill_versions=req.skill_versions,
        evaluation_framework_version=req.evaluation_framework_version,
        description=req.description,
        is_active=bool(req.is_active)
    )


@router.get("/packages/{package_id}/configuration", response_model=ForgeConfigurationSnapshot, dependencies=[Depends(require_role(["creator", "admin"]))])
def get_package_configuration(package_id: str):
    """Retrieves the exact immutable Forge configuration snapshot associated with a Story Package."""
    packages = ip_repository.local_get("story_forge_packages")
    pkg = next((p for p in packages if p.get("id") == package_id), None)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Story Package '{package_id}' not found.")

    config_id = pkg.get("forge_configuration_id") or "CFG-001"
    cfg = forge_config_repo.get_configuration(config_id)
    if not cfg:
        cfg = forge_config_repo.get_active_configuration()
    return cfg
