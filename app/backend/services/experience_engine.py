"""
Welele Media™ — Experience Engine Core Service (WEE Layer 2: Logic)
Handles Slot Ingestion, Catalog Hydration, Temporal Gatekeeping, and Publishing Lifecycle.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import copy
from database import db
from repositories.series_repository import series_repository
from schemas.experience_schemas import (
    ExperienceManifest,
    ExperienceSection,
    SlotItem,
    ArtworkOverrides
)
from services.merchandising_policy_service import merchandising_policy_service

class ExperienceEngine:
    """Intelligent layout resolver and merchandising manager."""

    @staticmethod
    def get_default_brand_config() -> Dict[str, Any]:
        """Canonical Global Platform Brand Ident configuration."""
        return {
            "play_brand_ident": True,
            "brand_ident_url": "/videos/welele_ident_v2.mp4",
            "brand_ident_duration": 5.2,
            "ident_frequency": 5,
            "failsafe_buffer": 1.0,
            "experience_rule": "standard",
            "asset": {
                "id": "welele-brand-ident-v2",
                "asset_type": "sonic_visual_ident",
                "name": "Welele Sonic Visual Ident v2",
                "url": "/videos/welele_ident_v2.mp4",
                "version": 2,
                "active": True,
                "duration": 5.2
            }
        }

    @classmethod
    def get_default_home_manifest(cls) -> Dict[str, Any]:
        """Canonical default layout for the Welele home experience."""
        return {
            "page_id": "home",
            "version": "1.0.0",
            "status": "published",
            "published_at": "2026-08-01T00:00:00Z",
            "updated_at": "2026-09-08T10:00:00Z",
            "meta": {
                "title": "Welele™ | Short African Dramas",
                "theme": "dark_gold_glow",
                "description": "Stream high-octane vertical micro-dramas produced across South Africa, Nigeria, and Ghana."
            },
            "brand_config": cls.get_default_brand_config(),
            "sections": [
                {
                    "section_id": "sec_hero_home",
                    "type": "HERO_CAROUSEL",
                    "title": None,
                    "subtitle": None,
                    "is_visible": True,
                    "order": 0,
                    "config": {
                        "auto_play_seconds": 8,
                        "aspect_ratio": "9:16",
                        "card_size": "large",
                        "show_rank_numbers": False
                    },
                    "source": {
                        "mode": "manual",
                        "pinned_content_ids": ["story_blood_ties", "story_queen_of_jozi", "story_ceo_wife", "story_umembeso", "story_lagos_confidential"],
                        "max_items": 5
                    },
                    "items": [
                        {
                            "slot_id": "slot_hero_1",
                            "content_type": "series",
                            "content_id": "story_blood_ties",
                            "badge": "SPOTLIGHT ORIGINAL",
                            "headline_override": None,
                            "subheadline_override": None,
                            "cta_text": "Watch Now",
                            "cta_action": "STREAM_EPISODE",
                            "cta_target": "ep_bt_1",
                            "artwork_overrides": {
                                "mobile_9_16": "/posters/blood_ties.jpg",
                                "desktop_16_9": "/banners/blood_ties_banner.jpg",
                                "trailer_video_url": "/videos/welele_placeholder.mp4"
                            },
                            "is_active": True
                        },
                        {
                            "slot_id": "slot_hero_2",
                            "content_type": "series",
                            "content_id": "story_queen_of_jozi",
                            "badge": "TOP RATED #1",
                            "headline_override": None,
                            "subheadline_override": None,
                            "cta_text": "Watch Now",
                            "cta_action": "STREAM_EPISODE",
                            "cta_target": "ep_qj_1",
                            "artwork_overrides": {
                                "mobile_9_16": "/posters/queen_of_jozi.jpg",
                                "desktop_16_9": "/banners/queen_of_jozi_banner.jpg",
                                "trailer_video_url": "/videos/ocean_waves.mp4"
                            },
                            "is_active": True
                        },
                        {
                            "slot_id": "slot_hero_3",
                            "content_type": "series",
                            "content_id": "story_ceo_wife",
                            "badge": "ROMANCE HIT",
                            "headline_override": None,
                            "subheadline_override": None,
                            "cta_text": "Watch Now",
                            "cta_action": "STREAM_EPISODE",
                            "cta_target": "ep_ceo_1",
                            "artwork_overrides": {
                                "mobile_9_16": "/posters/ceo_secret_wife.jpg",
                                "desktop_16_9": "/banners/ceo_secret_wife_banner.jpg",
                                "trailer_video_url": "/videos/welele_placeholder.mp4"
                            },
                            "is_active": True
                        }
                    ]
                },
                {
                    "section_id": "sec_promo_airtime",
                    "type": "EDITORIAL_BANNER",
                    "title": None,
                    "subtitle": None,
                    "is_visible": True,
                    "order": 1,
                    "config": {
                        "banner_style": "glass_gradient",
                        "background_color": "#FF5722",
                        "cta_primary_color": "#FF9800"
                    },
                    "source": {"mode": "manual", "max_items": 1},
                    "items": [
                        {
                            "slot_id": "slot_promo_vodacom",
                            "content_type": "promo",
                            "badge": "MZANSI FLASH DROP",
                            "headline_override": "Unlock 50 Coins for R15 with Vodacom & MTN Airtime",
                            "subheadline_override": "Instant one-tap checkout. No credit card required.",
                            "cta_text": "Claim Special Pack",
                            "cta_action": "OPEN_PAYMENT_MODAL",
                            "cta_target": "tier_standard",
                            "is_active": True
                        }
                    ]
                },
                {
                    "section_id": "sec_trending_row",
                    "type": "HORIZONTAL_ROW",
                    "title": "Trending in South Africa 🔥",
                    "subtitle": "Most watched micro-dramas across the continent this week",
                    "is_visible": True,
                    "order": 2,
                    "config": {
                        "card_size": "medium",
                        "show_rank_numbers": True,
                        "aspect_ratio": "9:16"
                    },
                    "source": {
                        "mode": "hybrid",
                        "algo_type": "velocity_24h",
                        "pinned_content_ids": ["story_queen_of_jozi", "story_ceo_wife", "story_heist_game", "story_barrio_billionaire", "story_lagos_confidential"],
                        "max_items": 10
                    },
                    "items": []
                },
                {
                    "section_id": "sec_spotlight_editorial",
                    "type": "EDITORIAL_SPOTLIGHT",
                    "title": "Editor's Pick of the Week ⭐",
                    "subtitle": "Curated by Welele Editorial Desk",
                    "is_visible": True,
                    "order": 3,
                    "config": {
                        "aspect_ratio": "16:9",
                        "banner_style": "editorial_dark"
                    },
                    "source": {
                        "mode": "manual",
                        "pinned_content_ids": ["story_blood_ties"]
                    },
                    "items": [
                        {
                            "slot_id": "slot_spotlight_1",
                            "content_type": "series",
                            "content_id": "story_blood_ties",
                            "badge": "WELELE ORIGINAL",
                            "headline_override": "Blood Ties: The Dynasty That Redefined Jozi Drama",
                            "subheadline_override": "Director Zola Dlamini delivers a masterclass in 90-second cliffhanger storytelling.",
                            "cta_text": "Watch From Episode 1",
                            "cta_action": "STREAM_EPISODE",
                            "cta_target": "ep_bt_1",
                            "is_active": True
                        }
                    ]
                },
                {
                    "section_id": "sec_originals_row",
                    "type": "HORIZONTAL_ROW",
                    "title": "Welele Originals 🎬",
                    "subtitle": "Exclusive short-form productions made for vertical viewing",
                    "is_visible": True,
                    "order": 4,
                    "config": {
                        "card_size": "medium",
                        "show_rank_numbers": False,
                        "aspect_ratio": "9:16"
                    },
                    "source": {
                        "mode": "manual",
                        "pinned_content_ids": ["story_blood_ties", "story_umembeso", "story_durban_heat", "story_the_hustlers"],
                        "max_items": 8
                    },
                    "items": []
                },
                {
                    "section_id": "sec_coming_soon",
                    "type": "COMING_SOON_RADAR",
                    "title": "Coming Soon to Welele 🚀",
                    "subtitle": "Dropping next week — Turn on episode reminders",
                    "is_visible": True,
                    "order": 5,
                    "config": {
                        "card_size": "medium"
                    },
                    "source": {
                        "mode": "manual",
                        "pinned_content_ids": ["story_accra_nights", "story_nairobi_hustle"],
                        "max_items": 4
                    },
                    "items": []
                }
            ]
        }

    @classmethod
    def get_default_discover_manifest(cls) -> Dict[str, Any]:
        """Default layout for Discover page."""
        return {
            "page_id": "discover",
            "version": "1.0.0",
            "status": "published",
            "published_at": "2026-08-01T00:00:00Z",
            "updated_at": "2026-09-08T10:00:00Z",
            "meta": {
                "title": "Discover | Welele™",
                "theme": "dark_gold_glow",
                "description": "Explore African short dramas by genre, country, and creator."
            },
            "brand_config": cls.get_default_brand_config(),
            "sections": [
                {
                    "section_id": "sec_genre_pills",
                    "type": "GENRE_PILLS_ROW",
                    "title": "Browse by Category",
                    "is_visible": True,
                    "order": 0,
                    "config": {},
                    "source": {"mode": "manual"},
                    "items": []
                },
                {
                    "section_id": "sec_discover_grid",
                    "type": "POSTER_GRID",
                    "title": "All Series Catalog",
                    "subtitle": "Browse 9:16 micro-series with free introductory episodes",
                    "is_visible": True,
                    "order": 1,
                    "config": {
                        "columns": 2,
                        "card_size": "medium"
                    },
                    "source": {
                        "mode": "algorithmic",
                        "algo_type": "new_releases",
                        "max_items": 24
                    },
                    "items": []
                }
            ]
        }

    @classmethod
    def get_stored_manifest(cls, page_id: str, state: str = "published") -> Dict[str, Any]:
        """Fetch saved manifest from database or initialize default."""
        layouts = db.get("experience_layouts")
        match = None
        for l in layouts:
            if l.get("page_id") == page_id and l.get("status") == state:
                match = l
                break
        
        # If no draft found but requesting draft, fall back to published copy
        if not match and state == "draft":
            match = cls.get_stored_manifest(page_id, state="published")
            if match:
                draft_copy = copy.deepcopy(match)
                draft_copy["status"] = "draft"
                return draft_copy

        if not match:
            if page_id == "home":
                match = cls.get_default_home_manifest()
            elif page_id == "discover":
                match = cls.get_default_discover_manifest()
            else:
                match = {
                    "page_id": page_id,
                    "version": "1.0.0",
                    "status": "published",
                    "meta": {"title": f"Welele™ | {page_id.title()}"},
                    "sections": []
                }
            # Persist default
            cls.save_layout(match)
        
        return copy.deepcopy(match)

    @classmethod
    def validate_layout(cls, layout_data: Dict[str, Any]):
        """Strictly validates sections, slots, and hero uniqueness before persistence."""
        sections = layout_data.get("sections", [])
        for sec in sections:
            sec_id = sec.get("section_id", "unknown")
            sec_type = sec.get("type")
            items = sec.get("items", [])
            seen_slot_ids = set()
            for it in items:
                sid = it.get("slot_id")
                if sid:
                    if sid in seen_slot_ids:
                        raise ValueError(
                            f"Duplicate slot_id '{sid}' detected in section '{sec_id}'. "
                            "Each slot in a layout must possess a globally unique slot_id."
                        )
                    seen_slot_ids.add(sid)
            if sec_type == "HERO_CAROUSEL":
                seen_content_ids = set()
                for it in items:
                    cid = it.get("content_id")
                    if cid:
                        if cid in seen_content_ids:
                            raise ValueError(
                                f"Duplicate content_id '{cid}' in HERO_CAROUSEL section '{sec_id}'. "
                                "Hero carousel slides must feature distinct series/content."
                            )
                        seen_content_ids.add(cid)

    @classmethod
    def save_layout(cls, layout_data: Dict[str, Any]):
        """Save or update layout in db after validating structural integrity."""
        cls.validate_layout(layout_data)
        layouts = db.get("experience_layouts")
        new_layouts = [
            l for l in layouts 
            if not (l.get("page_id") == layout_data.get("page_id") and l.get("status") == layout_data.get("status"))
        ]
        new_layouts.append(layout_data)
        db.set("experience_layouts", new_layouts)

    @classmethod
    def resolve_manifest(
        cls, 
        page_id: str, 
        state: str = "published", 
        eval_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Hydrates and compiles the manifest:
        1. Temporal gatekeeping (filters expired/future sections & slots)
        2. Catalog hydration (links series metadata to slots)
        3. Algorithmic fallback filling
        """
        raw_manifest = cls.get_stored_manifest(page_id, state=state)
        now_dt = eval_time or datetime.utcnow()

        feed = series_repository.list_feed()
        all_stories = {s["id"]: s for s in feed}
        stories_list = feed

        resolved_sections = []

        # Sort sections by order
        raw_sections = sorted(raw_manifest.get("sections", []), key=lambda s: s.get("order", 0))

        for sec in raw_sections:
            if not sec.get("is_visible", True) and state == "published":
                continue

            # Check temporal window of section
            sec_start = sec.get("start_at")
            sec_end = sec.get("end_at")
            if sec_start and datetime.fromisoformat(sec_start.replace("Z", "+00:00")) > now_dt.replace(tzinfo=None):
                continue
            if sec_end and datetime.fromisoformat(sec_end.replace("Z", "+00:00")) < now_dt.replace(tzinfo=None):
                continue

            sec_copy = dict(sec)

            # Resolve items using the canonical MerchandisingPolicyService boundary
            sec_copy["items"] = merchandising_policy_service.resolve_section_items(
                section=sec_copy,
                all_stories=all_stories,
                eval_time=now_dt
            )
            # Propagate Merchandising Provenance & Policy metadata
            sec_copy["merchandising_metadata"] = {
                "policy_version": merchandising_policy_service.POLICY_VERSION,
                "methodology_version": merchandising_policy_service.METHODOLOGY_VERSION,
                "mode": sec_copy.get("source", {}).get("mode", "manual"),
                "algo_type": sec_copy.get("source", {}).get("algo_type", "velocity_24h"),
                "resolved_item_count": len(sec_copy["items"])
            }
            resolved_sections.append(sec_copy)

        raw_manifest["sections"] = resolved_sections
        if "brand_config" not in raw_manifest or not raw_manifest["brand_config"]:
            raw_manifest["brand_config"] = cls.get_default_brand_config()
        return raw_manifest

