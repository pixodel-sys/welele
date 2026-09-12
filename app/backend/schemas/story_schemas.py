from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PreflightHealthSchema(BaseModel):
    aspect_ratio_ok: bool = True
    aspect_ratio_label: str = "1080 × 1920 (9:16)"
    duration_ok: bool = True
    duration_seconds: int = 60
    audio_detected: bool = True
    thumbnail_present: bool = True
    cliffhanger_marker_ok: bool = True
    cliffhanger_time_seconds: int = 54
    cliffhanger_hook_copy: Optional[str] = None
    captions_present: bool = True

class EpisodeSchema(BaseModel):
    id: str
    series_id: str
    episode_number: int
    title: str
    synopsis: str
    duration_seconds: int
    video_url: str
    thumbnail_url: str
    is_free: bool = True
    coin_price: int = 0
    cliffhanger_time: int = 0
    cliffhanger_hook: Optional[str] = None
    status: str = "published"
    scheduled_at: Optional[str] = None
    story_package_id: Optional[str] = None
    preflight_health: Optional[PreflightHealthSchema] = None
    moderation_feedback: Optional[str] = None
    likes_count: int = 0
    views_count: int = 0
    comments_count: int = 0
    published_at: str
    subtitles: Optional[dict] = None

class StorySchema(BaseModel):
    id: str
    title: str
    tagline: str
    synopsis: str
    cover_image: str
    vertical_poster: str
    genre: str
    language: str
    available_languages: List[str] = ["English"]
    tags: List[str] = []
    creator_id: str
    creator_name: str
    creator_avatar: str
    is_verified_creator: bool = True
    rating: float = 4.9
    total_episodes: int = 10
    free_episodes_count: int = 3
    coin_price_per_episode: int = 5
    total_views: int = 0
    total_likes: int = 0
    is_original: bool = False
    is_trending: bool = False
    status: str = "published"
    episodes: List[EpisodeSchema] = []

class CreateSeriesRequest(BaseModel):
    title: str
    tagline: str = "Welele Original Microdrama"
    synopsis: str = ""
    cover_image: str = "/banners/blood_ties_banner.jpg"
    vertical_poster: str = "/posters/blood_ties.jpg"
    genre: str
    language: str = "isiZulu / English"
    available_languages: List[str] = ["English", "isiZulu"]
    tags: List[str] = []
    creator_id: Optional[str] = None
    coin_price_per_episode: int = 5

class CreateEpisodeRequest(BaseModel):
    series_id: str
    episode_number: int = 1
    title: str
    synopsis: str = ""
    video_url: str = "/videos/welele_placeholder.mp4"
    storage_key: Optional[str] = None
    media_asset_id: Optional[str] = None
    story_package_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: int = 60
    is_free: bool = True
    coin_price: int = 0
    cliffhanger_time: int = 0
    cliffhanger_hook: Optional[str] = None
    status: str = "under_review"
    scheduled_at: Optional[str] = None
    preflight_health: Optional[Dict[str, Any]] = None

