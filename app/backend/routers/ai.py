from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from schemas.ai_schemas import SubtitleRequest, SubtitleResponse, AnalyzeVideoRequest, AnalyzeVideoResponse
from services.ai_service import ai_service
from services.rbac_service import require_authenticated_user

router = APIRouter(prefix="/ai", tags=["Welele AI™"])

class StoryForgeGenerateRequest(BaseModel):
    genre: str = "Township Hustle & Revenge"
    target_duration_seconds: int = 90
    prompt: str = ""
    language: Optional[str] = "English"

class StoryForgeTranslateRequest(BaseModel):
    line: str
    target_dialect: str = "zu"

@router.get("/status")
def get_ai_status():
    """Returns real-time status of live Google Gemini connection vs offline simulation fallback."""
    return ai_service.get_status()

@router.post("/subtitles", response_model=SubtitleResponse, dependencies=[Depends(require_authenticated_user)])
def generate_subtitles(req: SubtitleRequest):
    return ai_service.generate_subtitles(
        video_url=req.video_url,
        target_languages=req.target_languages
    )

@router.post("/analyze-video", response_model=AnalyzeVideoResponse, dependencies=[Depends(require_authenticated_user)])
def analyze_video(req: AnalyzeVideoRequest):
    return ai_service.analyze_video_content(
        video_url=req.video_url,
        title=req.title,
        synopsis=req.synopsis
    )

@router.post("/story-forge/generate", dependencies=[Depends(require_authenticated_user)])
def generate_story_forge_script(req: StoryForgeGenerateRequest):
    return ai_service.generate_story_forge_script(
        genre=req.genre,
        target_duration_seconds=req.target_duration_seconds,
        prompt=req.prompt,
        language=req.language or "English"
    )

@router.post("/story-forge/translate", dependencies=[Depends(require_authenticated_user)])
def translate_story_forge_dialogue(req: StoryForgeTranslateRequest):
    return ai_service.translate_dialogue(
        line=req.line,
        target_dialect=req.target_dialect
    )


class CompileAIPlanRequest(BaseModel):
    ip_id: str
    episode_number: int = 1
    production_bible_id: Optional[str] = None


class ClassifyInquiryRequest(BaseModel):
    inquiry_text: str


@router.post("/production/compile-plan", dependencies=[Depends(require_authenticated_user)])
def compile_ai_production_plan(req: CompileAIPlanRequest):
    """
    Compiles an authoritative Welele Production Document into an executable AI plan.
    Extracts all camera, lighting, audio, and character embeddings without creator round-trips.
    """
    from services.production_bible_service import production_bible_service
    from services.ai_production_adapter_service import ai_production_adapter_compiler
    from schemas.production_schemas import ProductionBibleModel, EpisodeProductionPackModel

    bible_dict = None
    if req.production_bible_id:
        bible_dict = production_bible_service.prod_repo.get_production_bible_by_id(req.production_bible_id)
    if not bible_dict:
        bible_dict = production_bible_service.generate_production_bible(req.ip_id)

    pack_dict = production_bible_service.generate_episode_production_pack(
        ip_id=req.ip_id,
        production_bible_id=bible_dict["id"],
        episode_number=req.episode_number
    )

    bible = ProductionBibleModel(**bible_dict)
    pack = EpisodeProductionPackModel(**pack_dict)

    plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)
    return plan.model_dump()


@router.post("/production/classify-inquiry", dependencies=[Depends(require_authenticated_user)])
def classify_ai_inquiry(req: ClassifyInquiryRequest):
    """
    Classifies an AI engine inquiry into Category A (Canonical), Category B (Production),
    or Category C (AI-runtime adapter requirement).
    """
    from services.ai_production_adapter_service import ai_production_adapter_compiler
    return ai_production_adapter_compiler.classify_inquiry(req.inquiry_text)


@router.post("/production/render-and-audit", dependencies=[Depends(require_authenticated_user)])
def render_and_audit_episode_media(req: CompileAIPlanRequest):
    """
    Renders/Assembles the 88-second vertical episode from the compiled AI plan
    and executes the comprehensive 10-Point Media Continuity Audit.
    """
    from services.production_bible_service import production_bible_service
    from services.ai_production_adapter_service import ai_production_adapter_compiler
    from services.media_production_audit_service import media_production_audit_service
    from schemas.production_schemas import ProductionBibleModel, EpisodeProductionPackModel

    bible_dict = None
    if req.production_bible_id:
        bible_dict = production_bible_service.prod_repo.get_production_bible_by_id(req.production_bible_id)
    if not bible_dict:
        bible_dict = production_bible_service.generate_production_bible(req.ip_id)

    pack_dict = production_bible_service.generate_episode_production_pack(
        ip_id=req.ip_id,
        production_bible_id=bible_dict["id"],
        episode_number=req.episode_number
    )

    bible = ProductionBibleModel(**bible_dict)
    pack = EpisodeProductionPackModel(**pack_dict)

    plan = ai_production_adapter_compiler.compile_production_pack_to_ai_plan(bible, pack)
    rendered = media_production_audit_service.render_episode_media(plan)
    audit_report = media_production_audit_service.audit_rendered_media_against_source(
        rendered=rendered,
        plan=plan,
        bible=bible,
        pack=pack
    )
    return audit_report.model_dump()


