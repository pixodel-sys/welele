from typing import Optional, List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from schemas.ai_schemas import SubtitleRequest, SubtitleResponse, AnalyzeVideoRequest, AnalyzeVideoResponse
from services.ai_service import ai_service

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

@router.post("/subtitles", response_model=SubtitleResponse)
def generate_subtitles(req: SubtitleRequest):
    return ai_service.generate_subtitles(
        video_url=req.video_url,
        target_languages=req.target_languages
    )

@router.post("/analyze-video", response_model=AnalyzeVideoResponse)
def analyze_video(req: AnalyzeVideoRequest):
    return ai_service.analyze_video_content(
        video_url=req.video_url,
        title=req.title,
        synopsis=req.synopsis
    )

@router.post("/story-forge/generate")
def generate_story_forge_script(req: StoryForgeGenerateRequest):
    return ai_service.generate_story_forge_script(
        genre=req.genre,
        target_duration_seconds=req.target_duration_seconds,
        prompt=req.prompt,
        language=req.language or "English"
    )

@router.post("/story-forge/translate")
def translate_story_forge_dialogue(req: StoryForgeTranslateRequest):
    return ai_service.translate_dialogue(
        line=req.line,
        target_dialect=req.target_dialect
    )
