from typing import List, Optional, Dict
from pydantic import BaseModel

class SubtitleRequest(BaseModel):
    video_url: str
    target_languages: List[str] = ["English", "Swahili", "Yoruba", "Zulu", "French"]
    sample_text: Optional[str] = None

class SubtitleResponse(BaseModel):
    video_url: str
    subtitles_by_language: Dict[str, List[Dict[str, str]]]
    detected_language: str
    accuracy_score: float

class AnalyzeVideoRequest(BaseModel):
    video_url: str
    title: str
    synopsis: str

class AnalyzeVideoResponse(BaseModel):
    aspect_ratio: str
    is_vertical_valid: bool
    estimated_duration_seconds: int
    cliffhanger_suggested_timestamp: int
    content_safety_rating: str
    safety_flags: List[str]
    detected_genres: List[str]
    suggested_tags: List[str]
    african_cultural_context_tags: List[str]
