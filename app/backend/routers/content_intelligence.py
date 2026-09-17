"""
Welele Media™ — Content Intelligence Router (Phase 7)
Endpoints for evaluating evidence, retrieving intelligence records, and logging decisions.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from services.content_intelligence_service import content_intelligence_service
from repositories.content_intelligence_repository import content_intelligence_repository
from schemas.content_intelligence_models import DecisionTargetLayer, DecisionStatus

router = APIRouter(prefix="/api/v1/intelligence", tags=["Content Intelligence"])


@router.post("/evaluate")
def evaluate_content_intelligence(payload: Dict[str, Any]):
    """
    Evaluates upstream evidence and compiles traceable Content Intelligence.
    """
    ip_id = payload.get("ip_id")
    if not ip_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ip_id is required")
    
    series_id = payload.get("series_id")
    episode_id = payload.get("episode_id")

    try:
        package = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation(
            ip_id=ip_id,
            series_id=series_id,
            episode_id=episode_id
        )
        return package.model_dump()
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/records/{intelligence_id}")
def get_intelligence_record(intelligence_id: str):
    record = content_intelligence_repository.get_intelligence_record(intelligence_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Intelligence record '{intelligence_id}' not found")
    return record


@router.post("/decisions")
def create_content_decision(payload: Dict[str, Any]):
    """
    Creates an authoritative ContentDecision transitioning into a New Objective.
    """
    decision_id = payload.get("decision_id")
    decision_type = payload.get("decision_type", "CREATIVE_OBJECTIVE")
    target_layer_str = payload.get("target_layer", "STORY_FORGE")
    intelligence_refs = payload.get("intelligence_refs", [])
    evidence_refs = payload.get("evidence_refs", [])
    statement = payload.get("decision_statement")
    rationale = payload.get("rationale", "")
    owner = payload.get("decision_owner", "Welele Editorial")
    transition_payload = payload.get("transition_payload", {})

    if not statement:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="decision_statement is required")

    try:
        target_layer = DecisionTargetLayer(target_layer_str)
        decision = content_intelligence_service.create_content_decision(
            decision_id=decision_id or f"dec_{uuid.uuid4().hex[:10]}",
            decision_type=decision_type,
            target_layer=target_layer,
            intelligence_refs=intelligence_refs,
            evidence_refs=evidence_refs,
            decision_statement=statement,
            rationale=rationale,
            decision_owner=owner,
            transition_payload=transition_payload
        )
        return decision.model_dump()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/decisions/{decision_id}")
def get_content_decision(decision_id: str):
    decision = content_intelligence_repository.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Content decision '{decision_id}' not found")
    return decision


@router.get("/evaluation/isibusiso")
def get_isibusiso_intelligence_evaluation():
    """
    Direct evaluation endpoint for Isibusiso Season 1 Episode 1 specimen.
    """
    try:
        package = content_intelligence_service.execute_isibusiso_content_intelligence_evaluation()
        return package.model_dump()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
