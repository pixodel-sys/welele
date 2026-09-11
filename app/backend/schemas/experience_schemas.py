"""
Welele Media™ — Experience Engine Pydantic Schemas (WEE Layer 4: Contract)
Defines the strict data structures for Sections, Slots, Overrides, and Layout Manifests.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

SectionType = Literal[
    "HERO_CAROUSEL",
    "HORIZONTAL_ROW",
    "POSTER_GRID",
    "EDITORIAL_SPOTLIGHT",
    "EDITORIAL_BANNER",
    "GENRE_PILLS_ROW",
    "COMING_SOON_RADAR",
    "CONTINUE_WATCHING"
]

CtaAction = Literal[
    "STREAM_EPISODE",
    "OPEN_STORY_DETAIL",
    "OPEN_PAYMENT_MODAL",
    "OPEN_CREATOR_PROFILE",
    "FILTER_GENRE",
    "EXTERNAL_LINK"
]

class ArtworkOverrides(BaseModel):
    mobile_9_16: Optional[str] = None
    desktop_16_9: Optional[str] = None
    banner_wide: Optional[str] = None
    trailer_video_url: Optional[str] = None

class SlotItem(BaseModel):
    slot_id: str
    content_type: Literal["series", "episode", "creator", "promo", "genre"] = "series"
    content_id: Optional[str] = None
    badge: Optional[str] = None  # e.g., "SEASON FINALE", "EXCLUSIVE", "NEW", "TOP 10"
    headline_override: Optional[str] = None
    subheadline_override: Optional[str] = None
    cta_text: Optional[str] = None
    cta_action: Optional[CtaAction] = "STREAM_EPISODE"
    cta_target: Optional[str] = None
    artwork_overrides: Optional[ArtworkOverrides] = None
    is_active: bool = True
    start_at: Optional[str] = None  # ISO 8601 string
    end_at: Optional[str] = None    # ISO 8601 string

class SectionSource(BaseModel):
    mode: Literal["manual", "algorithmic", "hybrid"] = "manual"
    algo_type: Optional[Literal["velocity_24h", "completion_rate", "new_releases", "trending", "personalized"]] = None
    pinned_content_ids: List[str] = Field(default_factory=list)
    genre_filter: Optional[str] = None
    max_items: int = 10

class SectionConfig(BaseModel):
    auto_play_seconds: Optional[int] = 8
    aspect_ratio: Optional[str] = "9:16"
    card_size: Optional[Literal["small", "medium", "large"]] = "medium"
    show_rank_numbers: Optional[bool] = False
    banner_style: Optional[Literal["glass_gradient", "solid", "neon_glow", "editorial_dark"]] = "glass_gradient"
    background_color: Optional[str] = None
    cta_primary_color: Optional[str] = None
    columns: Optional[int] = 2

class ExperienceSection(BaseModel):
    section_id: str
    type: SectionType
    title: Optional[str] = None
    subtitle: Optional[str] = None
    is_visible: bool = True
    order: int = 0
    config: SectionConfig = Field(default_factory=SectionConfig)
    source: SectionSource = Field(default_factory=SectionSource)
    items: List[SlotItem] = Field(default_factory=list)
    start_at: Optional[str] = None
    end_at: Optional[str] = None

class BrandAsset(BaseModel):
    id: str = "welele-brand-ident"
    asset_type: Literal["sonic_visual_ident", "originals_ident", "welcome_ident", "campaign_ident"] = "sonic_visual_ident"
    name: str = "Welele Sonic Visual Ident"
    url: str = "/videos/welele_ident.mp4"
    version: int = 1
    active: bool = True
    duration: float = 5.2

class BrandIdentConfig(BaseModel):
    play_brand_ident: bool = True
    brand_ident_url: str = "/videos/welele_ident.mp4"
    brand_ident_duration: Optional[float] = 5.2
    ident_frequency: int = 5
    failsafe_buffer: float = 1.0
    experience_rule: Literal["standard", "first_visit", "originals", "special_event", "creator_premiere"] = "standard"
    asset: Optional[BrandAsset] = None

class PageMeta(BaseModel):
    title: str = "Welele™ | Short African Dramas"
    theme: str = "dark_gold_glow"
    description: Optional[str] = None

class ExperienceManifest(BaseModel):
    page_id: str
    version: str
    status: Literal["draft", "published", "archived"] = "published"
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    meta: PageMeta = Field(default_factory=PageMeta)
    brand_config: BrandIdentConfig = Field(default_factory=BrandIdentConfig)
    sections: List[ExperienceSection] = Field(default_factory=list)

class SaveDraftRequest(BaseModel):
    meta: Optional[PageMeta] = None
    brand_config: Optional[BrandIdentConfig] = None
    sections: List[ExperienceSection]

class PublishRequest(BaseModel):
    scheduled_for: Optional[str] = None

