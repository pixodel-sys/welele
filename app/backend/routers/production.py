"""
Welele Media™ — Production Router
Exposes Production Bibles and 5-Track Episode Production Packs.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from services.production_bible_service import production_bible_service
from repositories.production_repository import production_repository
from schemas.production_schemas import (
    ProductionBibleCreateRequest,
    ProductionBibleModel,
    EpisodeProductionPackCreateRequest,
    EpisodeProductionPackModel
)
from services.rbac_service import require_role, get_current_user
from services.audit_service import audit_service

router = APIRouter(prefix="/production", tags=["Production Engine"])


@router.post("/bibles/generate", response_model=ProductionBibleModel, dependencies=[Depends(require_role(["creator", "admin"]))])
def generate_production_bible(req: ProductionBibleCreateRequest, auth_user: dict = Depends(get_current_user)):
    """Transforms an M3 8-pillar Story Package into a comprehensive 10-Section Production Bible."""
    try:
        bible = production_bible_service.generate_production_bible(
            ip_id=req.ip_id,
            story_package_id=req.story_package_id,
            version=req.version
        )

        audit_service.record_trust_event(
            domain="PRODUCTION",
            event_type="production.bible_generated",
            actor_id=auth_user.get("sub", "creator"),
            actor_role=auth_user.get("role", "creator"),
            target_type="production_bible",
            target_id=bible["id"],
            after_state={"title": bible["bible_title"], "version": bible["version"], "ip_id": req.ip_id},
            metadata={"forge_configuration_id": bible.get("forge_configuration_id", "CFG-001")}
        )

        return bible
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Production Bible: {str(e)}")


@router.get("/bibles/{ip_id}", response_model=ProductionBibleModel)
def get_production_bible_by_ip(ip_id: str):
    """Fetches the active Production Bible for a given Digital IP."""
    bible = production_repository.get_production_bible_by_ip(ip_id)
    if not bible:
        try:
            bible = production_bible_service.generate_production_bible(ip_id=ip_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Production Bible not found for IP '{ip_id}'.")
    return bible


@router.get("/bibles", response_model=List[ProductionBibleModel])
def list_production_bibles():
    """Returns all Production Bibles."""
    return production_repository.list_production_bibles()


@router.post("/packs/generate", response_model=EpisodeProductionPackModel, dependencies=[Depends(require_role(["creator", "admin"]))])
def generate_episode_production_pack(req: EpisodeProductionPackCreateRequest, auth_user: dict = Depends(get_current_user)):
    """Generates an Episode Production Pack using the 5-Track Production Model (VIDEO, DIALOGUE, NARRATION, AMBIENCE, MUSIC)."""
    try:
        pack = production_bible_service.generate_episode_production_pack(
            ip_id=req.ip_id,
            production_bible_id=req.production_bible_id,
            episode_number=req.episode_number
        )

        audit_service.record_trust_event(
            domain="PRODUCTION",
            event_type="production.episode_pack_generated",
            actor_id=auth_user.get("sub", "creator"),
            actor_role=auth_user.get("role", "creator"),
            target_type="episode_production_pack",
            target_id=pack["id"],
            after_state={"episode_number": pack["episode_number"], "title": pack["title"], "ip_id": req.ip_id},
            metadata={"forge_configuration_id": pack.get("forge_configuration_id", "CFG-001")}
        )

        return pack
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Episode Production Pack: {str(e)}")


@router.get("/packs/{ip_id}/episodes/{episode_number}", response_model=EpisodeProductionPackModel)
def get_episode_production_pack(ip_id: str, episode_number: int):
    """Fetches the 5-track Episode Production Pack for a given IP and episode number."""
    pack = production_repository.get_episode_pack(ip_id=ip_id, episode_number=episode_number)
    if not pack:
        try:
            pack = production_bible_service.generate_episode_production_pack(ip_id=ip_id, episode_number=episode_number)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Episode Production Pack not found: {str(e)}")
    return pack


@router.get("/packs/{ip_id}", response_model=List[EpisodeProductionPackModel])
def list_episode_packs_for_ip(ip_id: str):
    """Returns all Episode Production Packs for a given IP."""
    return production_repository.list_episode_packs(ip_id=ip_id)
