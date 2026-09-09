"""
Welele Media™ — Series & Media Catalog Repository (GAP-001 & GAP-006)
Normalized relational data access for Series, Episodes, decoupled Media Assets, and Moderation Lifecycle.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from .base_repository import BaseRepository

class SeriesRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self._seed_default_series()

    def _seed_default_series(self):
        existing = self.local_get("series")
        if not existing:
            # Seed canonical series linked to ip_blood_ties
            series_1 = {
                "id": "story_blood_ties",
                "ip_id": "ip_blood_ties",
                "season_number": 1,
                "title": "Blood Ties",
                "tagline": "Gold. Betrayal. Legacy.",
                "synopsis": "When an Alexandra mechanic inherits Johannesburg’s wealthiest taxi empire, rival cartels and family loyalty collide.",
                "cover_image": "/banners/blood_ties_banner.jpg",
                "vertical_poster": "/posters/blood_ties.jpg",
                "genre": "Dynasty & Revenge Thriller",
                "rating": 4.95,
                "total_episodes": 3,
                "free_episodes": 2,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "English", "isiXhosa"],
                "tags": ["Dynasty", "Revenge", "Township", "Crime"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            self.local_insert("series", series_1)

            # Seed episodes
            episodes_data = [
                {
                    "id": "ep_bt_1",
                    "series_id": "story_blood_ties",
                    "story_package_id": "sfp_bt_01",
                    "episode_number": 1,
                    "title": "The Golden Will",
                    "synopsis": "The unsealed court document triggers panic in the boardroom.",
                    "duration_seconds": 68,
                    "is_free": True,
                    "coin_price": 0,
                    "cliffhanger_time_seconds": 58,
                    "cliffhanger_hook": "Who authorized her DNA test before the funeral?",
                    "status": "published",
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "ep_bt_2",
                    "series_id": "story_blood_ties",
                    "story_package_id": "sfp_bt_01",
                    "episode_number": 2,
                    "title": "Midnight at the Rank",
                    "synopsis": "Sipho confronts the convoy blocking the workshop.",
                    "duration_seconds": 74,
                    "is_free": True,
                    "coin_price": 0,
                    "cliffhanger_time_seconds": 64,
                    "cliffhanger_hook": "Will Bra Oupa draw his weapon first?",
                    "status": "published",
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "ep_bt_3",
                    "series_id": "story_blood_ties",
                    "story_package_id": "sfp_bt_01",
                    "episode_number": 3,
                    "title": "The Cartel Route",
                    "synopsis": "The hidden ledger exposes illicit transit lines across Gauteng.",
                    "duration_seconds": 82,
                    "is_free": False,
                    "coin_price": 5,
                    "cliffhanger_time_seconds": 72,
                    "cliffhanger_hook": "The security camera reveals the traitor in the family.",
                    "status": "published",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]

            for ep in episodes_data:
                self.local_insert("episodes", ep)
                self.local_insert("media_assets", {
                    "id": f"media_{ep['id']}",
                    "episode_id": ep["id"],
                    "storage_key": f"masters/blood_ties/{ep['id']}.mp4",
                    "master_video_url": "/videos/welele_placeholder.mp4",
                    "hls_master_manifest_url": f"https://cdn.welele.media/hls/blood_ties/{ep['id']}/master.m3u8",
                    "thumbnail_url": "/posters/blood_ties.jpg",
                    "duration_seconds": ep["duration_seconds"],
                    "transcoding_status": "READY",
                    "renditions_json": {
                        "1080p": f"https://cdn.welele.media/hls/blood_ties/{ep['id']}/1080p.m3u8",
                        "720p": f"https://cdn.welele.media/hls/blood_ties/{ep['id']}/720p.m3u8",
                        "480p": f"https://cdn.welele.media/hls/blood_ties/{ep['id']}/480p.m3u8"
                    },
                    "subtitles_vtt_json": {
                        "isiZulu": f"https://cdn.welele.media/subs/blood_ties/{ep['id']}_zu.vtt",
                        "English": f"https://cdn.welele.media/subs/blood_ties/{ep['id']}_en.vtt"
                    },
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })

    def list_feed(self, genre: Optional[str] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
        all_series = self.local_get("series")
        all_episodes = self.local_get("episodes")
        all_media = self.local_get("media_assets")

        media_map = {m["episode_id"]: m for m in all_media}

        result = []
        for s in all_series:
            if not s.get("is_published", True):
                continue
            if genre and s.get("genre") != genre:
                continue

            s_copy = dict(s)
            s_episodes = [e for e in all_episodes if e.get("series_id") == s["id"] and e.get("status") == "published"]
            s_episodes.sort(key=lambda x: x.get("episode_number", 0))

            hydrated_eps = []
            for ep in s_episodes:
                ep_copy = dict(ep)
                media = media_map.get(ep["id"])
                if media:
                    ep_copy["video_url"] = media.get("master_video_url", "/videos/welele_placeholder.mp4")
                    ep_copy["hls_url"] = media.get("hls_master_manifest_url")
                    ep_copy["thumbnail_url"] = media.get("thumbnail_url", s_copy.get("vertical_poster"))
                    ep_copy["renditions"] = media.get("renditions_json")
                else:
                    ep_copy["video_url"] = "/videos/welele_placeholder.mp4"
                hydrated_eps.append(ep_copy)

            s_copy["episodes"] = hydrated_eps
            s_copy["total_episodes"] = len(hydrated_eps)
            result.append(s_copy)

        return result

    def get_series_detail(self, series_id: str) -> Optional[Dict[str, Any]]:
        all_series = self.list_feed()
        return next((s for s in all_series if s["id"] == series_id), None)

    def create_episode_draft(
        self,
        series_id: str,
        story_package_id: Optional[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates an auditable Episode Draft linked to parent Series and Story Package.
        """
        ep_id = payload.get("id") or f"ep_{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        ep_record = {
            "id": ep_id,
            "series_id": series_id,
            "story_package_id": story_package_id,
            "episode_number": payload.get("episode_number", 1),
            "title": payload.get("title", f"Episode {payload.get('episode_number', 1)}"),
            "synopsis": payload.get("synopsis", ""),
            "duration_seconds": payload.get("duration_seconds", 80),
            "is_free": payload.get("is_free", False),
            "coin_price": payload.get("coin_price", 5) if not payload.get("is_free") else 0,
            "cliffhanger_time_seconds": payload.get("cliffhanger_time", payload.get("cliffhanger_time_seconds", 65)),
            "cliffhanger_hook": payload.get("cliffhanger_hook", "What happens next?"),
            "status": "draft",
            "preflight_health": payload.get("preflight_health"),
            "created_at": now_ts,
            "updated_at": now_ts
        }
        self.local_insert("episodes", ep_record)
        return ep_record

    def attach_media_asset(
        self,
        episode_id: str,
        storage_key: str,
        master_url: str,
        thumbnail_url: Optional[str] = None,
        duration_seconds: float = 80.0
    ) -> Dict[str, Any]:
        """
        Attaches a decoupled media asset to an episode.
        """
        media_id = f"media_{episode_id}"
        now_ts = datetime.now(timezone.utc).isoformat()

        media_record = {
            "id": media_id,
            "episode_id": episode_id,
            "storage_key": storage_key,
            "master_video_url": master_url,
            "hls_master_manifest_url": f"https://cdn.welele.media/hls/{storage_key}/master.m3u8",
            "thumbnail_url": thumbnail_url,
            "duration_seconds": duration_seconds,
            "transcoding_status": "READY",
            "renditions_json": {
                "1080p": f"https://cdn.welele.media/hls/{storage_key}/1080p.m3u8",
                "720p": f"https://cdn.welele.media/hls/{storage_key}/720p.m3u8",
                "480p": f"https://cdn.welele.media/hls/{storage_key}/480p.m3u8"
            },
            "created_at": now_ts,
            "updated_at": now_ts
        }
        self.local_insert("media_assets", media_record)
        return media_record

    def register_media_asset(
        self,
        episode_id: str,
        master_video_url: str,
        thumbnail_url: Optional[str] = None,
        storage_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.attach_media_asset(
            episode_id=episode_id,
            storage_key=storage_key or f"masters/{episode_id}.mp4",
            master_url=master_video_url,
            thumbnail_url=thumbnail_url
        )

    def submit_for_moderation(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Transitions episode status to 'under_review' for administrative review.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        updated = self.local_update("episodes", "id", episode_id, {
            "status": "under_review",
            "submitted_at": now_ts,
            "updated_at": now_ts
        })
        return updated

    def review_episode(
        self,
        episode_id: str,
        decision: str, # 'approved' | 'changes_requested' | 'rejected'
        feedback: Optional[str] = None,
        reviewer_id: str = "admin_supervisor"
    ) -> Optional[Dict[str, Any]]:
        """
        Applies an auditable moderation decision. If approved, promotes status to 'published'.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        target_status = "published" if decision == "approved" else decision

        updated = self.local_update("episodes", "id", episode_id, {
            "status": target_status,
            "moderation_decision": decision,
            "moderation_feedback": feedback,
            "reviewed_by": reviewer_id,
            "reviewed_at": now_ts,
            "updated_at": now_ts
        })
        return updated

    def get_moderation_queue(self) -> List[Dict[str, Any]]:
        """
        Returns normalized queue of episodes currently under review with attached series and media data.
        """
        episodes = self.local_get("episodes")
        series_list = self.local_get("series")
        media_list = self.local_get("media_assets")

        series_map = {s["id"]: s for s in series_list}
        media_map = {m["episode_id"]: m for m in media_list}

        queue = []
        for ep in episodes:
            if ep.get("status") in ["under_review", "pending_review", "submitted"]:
                s = series_map.get(ep.get("series_id"), {})
                m = media_map.get(ep.get("id"), {})
                queue.append({
                    "id": f"mod_{ep['id']}",
                    "episode_id": ep["id"],
                    "series_id": ep.get("series_id"),
                    "series_title": s.get("title", "Untitled Series"),
                    "episode_number": ep.get("episode_number", 1),
                    "episode_title": ep.get("title", ""),
                    "creator_name": s.get("creator_name", "Showrunner"),
                    "creator_id": s.get("creator_id", "creator_zola"),
                    "submitted_at": ep.get("submitted_at", ep.get("created_at")),
                    "aspect_ratio": "9:16 (1080x1920)",
                    "duration": f"{ep.get('duration_seconds', 80)}s",
                    "duration_seconds": ep.get("duration_seconds", 80),
                    "video_url": m.get("master_video_url", "/videos/welele_placeholder.mp4"),
                    "thumbnail_url": m.get("thumbnail_url", s.get("vertical_poster")),
                    "cliffhanger_time": ep.get("cliffhanger_time_seconds", 65),
                    "cliffhanger_hook": ep.get("cliffhanger_hook", ""),
                    "ai_safety_score": 98.5,
                    "status": "pending_review",
                    "preflight_health": ep.get("preflight_health", {
                        "aspect_ratio_ok": True,
                        "duration_ok": True,
                        "audio_detected": True,
                        "thumbnail_present": True,
                        "cliffhanger_marker_ok": True,
                        "captions_present": True
                    })
                })
    # --- Media Jobs & Rendition Operations (Amendment 1) ---

    def create_media_job(
        self,
        media_asset_id: str,
        provider: str = "CloudflareStream",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if idempotency_key:
            jobs = self.local_get("media_jobs")
            existing = next((j for j in jobs if j.get("idempotency_key") == idempotency_key), None)
            if existing:
                return existing

        now_ts = datetime.now(timezone.utc).isoformat()
        job = {
            "id": f"job_{uuid.uuid4().hex[:10]}",
            "media_asset_id": media_asset_id,
            "provider": provider,
            "status": "queued",
            "attempt": 1,
            "started_at": now_ts,
            "completed_at": None,
            "error": None,
            "idempotency_key": idempotency_key or f"job_idemp_{uuid.uuid4().hex[:8]}",
            "created_at": now_ts
        }
        self.local_insert("media_jobs", job)
        return job

    def update_media_job(
        self,
        job_id: str,
        status: str,
        attempt: Optional[int] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        now_ts = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {
            "status": status,
            "updated_at": now_ts
        }
        if status in ["completed", "ready"]:
            updates["completed_at"] = now_ts
        if attempt is not None:
            updates["attempt"] = attempt
        if error is not None:
            updates["error"] = error

        return self.local_update("media_jobs", "id", job_id, updates)

    def get_media_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        jobs = self.local_get("media_jobs")
        return next((j for j in jobs if j.get("id") == job_id), None)

    def add_rendition(
        self,
        media_asset_id: str,
        profile: str,
        width: int,
        height: int,
        bitrate: int,
        playlist_url: str
    ) -> Dict[str, Any]:
        rendition = {
            "id": f"rend_{uuid.uuid4().hex[:8]}",
            "media_asset_id": media_asset_id,
            "profile": profile,
            "width": width,
            "height": height,
            "bitrate": bitrate,
            "playlist_url": playlist_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.local_insert("media_renditions", rendition)
        return rendition

    def get_renditions_for_asset(self, media_asset_id: str) -> List[Dict[str, Any]]:
        renditions = self.local_get("media_renditions")
        return [r for r in renditions if r.get("media_asset_id") == media_asset_id]

    def update_media_asset_status(
        self,
        media_asset_id: str,
        status: str,
        hls_manifest_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        now_ts = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {
            "status": status,
            "updated_at": now_ts
        }
        if hls_manifest_url:
            updates["hls_master_manifest"] = hls_manifest_url
        return self.local_update("media_assets", "id", media_asset_id, updates)

series_repository = SeriesRepository()
