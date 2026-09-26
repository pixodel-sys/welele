"""
Welele Media™ — Merchandising Policy Service (WEE Layer 2.5: Merchandising Policy)
Enforces the architectural invariant:
Unified Event Spine → Audience Evidence / Content Evidence Projection → Merchandising Policy → WEE Experience Manifest

Governing Principles:
1. WEE is NOT an analytics engine. Audience truth is computed strictly by the Evidence Projection layer.
2. Merchandising Policy derives candidate rankings from ContentEvidenceProjection models, not raw telemetry.
3. Candidate rankings strictly filter by genre, temporal/publication eligibility, and evidence confidence tiers.
4. Editorial items are immutable in MANUAL mode, and pinned items retain strict priority in HYBRID mode.
5. Dynamic fill never duplicates pinned or existing items, and never violates genre constraints.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone

from repositories.series_repository import series_repository
from services.evidence_projection_service import EvidenceProjectionService
from schemas.projection_models import ConfidenceTier, ContentEvidenceProjection


class MerchandisingPolicyService:
    POLICY_VERSION = "1.0.0"
    METHODOLOGY_VERSION = "2026.1"

    # Minimal sample size threshold required before evidence-based ranking is considered reliable
    # Insufficient evidence items receive lower ranking priority than items with established signal
    CONFIDENCE_WEIGHTS = {
        ConfidenceTier.ESTABLISHED: 1.0,
        ConfidenceTier.DEVELOPING: 0.8,
        ConfidenceTier.PRELIMINARY: 0.5,
        ConfidenceTier.INSUFFICIENT: 0.2
    }

    def __init__(self, projection_service: Optional[EvidenceProjectionService] = None, series_repo=None):
        self.projection_service = projection_service or EvidenceProjectionService()
        self.series_repo = series_repo or series_repository

    def get_published_eligible_catalog(self, eval_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all series eligible for publication:
        - Series must be marked is_published=True
        - Must possess at least one published episode
        - Respects temporal release window if start_at/published_at exists
        """
        feed = self.series_repo.list_feed()
        now_dt = eval_time or datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)

        eligible = []
        for s in feed:
            if not s.get("is_published", True):
                continue
            
            # Check temporal series availability
            start_at = s.get("start_at") or s.get("created_at")
            if start_at:
                try:
                    s_dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                    if s_dt > now_dt:
                        continue
                except Exception:
                    pass

            # Series must possess published episodes to be eligible for viewing
            episodes = s.get("episodes")
            if episodes is not None:
                has_published_ep = any(
                    (ep.get("status") == "published") or 
                    (ep.get("is_published") is True and ep.get("status") != "draft")
                    for ep in episodes
                )
            else:
                # If episodes array is not embedded in summary, allow series based on series is_published
                has_published_ep = True

            if has_published_ep:
                eligible.append(s)

        return eligible

    def filter_by_genre(self, candidates: List[Dict[str, Any]], genre_filter: Optional[str]) -> List[Dict[str, Any]]:
        """
        Strict genre enforcement:
        Does not silently violate constraints when insufficient candidates exist.
        """
        if not genre_filter or genre_filter.strip().upper() in ["ALL", "ALL GENRES", ""]:
            return candidates

        target_genre = genre_filter.strip().lower()
        filtered = []
        for c in candidates:
            c_genre = str(c.get("genre", "")).lower()
            c_tags = [str(t).lower() for t in c.get("tags", [])]
            if target_genre in c_genre or any(target_genre in t for t in c_tags):
                filtered.append(c)

        return filtered

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        algo_type: str,
        eval_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks candidate series according to versioned merchandising algorithms
        consuming canonical Content Evidence Projections.
        """
        if not candidates:
            return []

        algo = (algo_type or "velocity_24h").lower()

        if algo == "new_releases":
            return self._rank_new_releases(candidates)
        elif algo == "completion_rate":
            return self._rank_by_evidence_completion(candidates)
        elif algo == "velocity_24h":
            return self._rank_by_evidence_velocity(candidates, days=1)
        elif algo == "trending":
            return self._rank_by_trending_methodology(candidates)
        else:
            # Default deterministic order by release date or ID
            return sorted(candidates, key=lambda s: s.get("created_at") or s.get("id"), reverse=True)

    def _rank_new_releases(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        New Releases Policy:
        Strictly orders by publication eligibility and release timestamp descending.
        """
        def get_timestamp(s: Dict[str, Any]) -> str:
            # Find the latest published episode timestamp, or series created_at
            episodes = s.get("episodes") or []
            ep_times = [
                e.get("published_at") or e.get("created_at")
                for e in episodes if e.get("published_at") or e.get("created_at")
            ]
            if ep_times:
                return max(ep_times)
            return s.get("created_at") or "1970-01-01T00:00:00Z"

        return sorted(candidates, key=lambda s: (get_timestamp(s), s.get("id")), reverse=True)

    def _rank_by_evidence_completion(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Completion Rate Policy:
        Consumes canonical ContentEvidenceProjection completion_rate_pct derived from Unified Event Spine.
        Respects confidence tier weighting so high-variance small sample items do not unfairly jump ahead.
        """
        projections: Dict[str, ContentEvidenceProjection] = {}
        for s in candidates:
            sid = s["id"]
            proj = self.projection_service.build_content_projection(series_id=sid, days=30)
            projections[sid] = proj

        def score_series(s: Dict[str, Any]) -> tuple:
            sid = s["id"]
            proj = projections.get(sid)
            if not proj or not proj.provenance.has_data:
                # No evidence: fallback score is 0.0 with insufficient confidence
                return (0.0, 0, s.get("id"))
            
            conf_multiplier = self.CONFIDENCE_WEIGHTS.get(proj.provenance.confidence_tier, 0.2)
            raw_rate = proj.completion_rate_pct
            weighted_score = round(raw_rate * conf_multiplier, 4)
            return (weighted_score, proj.completions, s.get("id"))

        return sorted(candidates, key=score_series, reverse=True)

    def _rank_by_evidence_velocity(self, candidates: List[Dict[str, Any]], days: int = 1) -> List[Dict[str, Any]]:
        """
        Velocity Policy (velocity_24h):
        Consumes canonical Audience Evidence starts and completions over a bounded time window (e.g. 24h/1 day),
        NOT lifetime total_views.
        """
        projections: Dict[str, ContentEvidenceProjection] = {}
        for s in candidates:
            sid = s["id"]
            proj = self.projection_service.build_content_projection(series_id=sid, days=days)
            projections[sid] = proj

        def score_velocity(s: Dict[str, Any]) -> tuple:
            sid = s["id"]
            proj = projections.get(sid)
            if not proj or not proj.provenance.has_data:
                return (0.0, 0, s.get("id"))

            conf_multiplier = self.CONFIDENCE_WEIGHTS.get(proj.provenance.confidence_tier, 0.2)
            # Velocity = recent session starts + completion momentum
            velocity_volume = proj.starts + (proj.completions * 2)
            weighted_velocity = round(velocity_volume * conf_multiplier, 4)
            return (weighted_velocity, proj.starts, s.get("id"))

        return sorted(candidates, key=score_velocity, reverse=True)

    def _rank_by_trending_methodology(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Trending Policy (Versioned Methodology 2026.1):
        Combines 7-day evidence velocity, unlock conversion momentum, and viewer engagement.
        """
        projections: Dict[str, ContentEvidenceProjection] = {}
        for s in candidates:
            sid = s["id"]
            proj = self.projection_service.build_content_projection(series_id=sid, days=7)
            projections[sid] = proj

        def score_trending(s: Dict[str, Any]) -> tuple:
            sid = s["id"]
            proj = projections.get(sid)
            if not proj or not proj.provenance.has_data:
                # If no telemetry evidence has been logged yet, fall back cleanly to catalog flags
                initial_seed = 10.0 if s.get("is_trending") else (5.0 if s.get("is_original") else 0.0)
                return (initial_seed, 0, s.get("id"))

            conf = self.CONFIDENCE_WEIGHTS.get(proj.provenance.confidence_tier, 0.2)
            # Empirical 3-pillar formula:
            # 1. Start volume momentum (40%)
            # 2. Completion conviction (35%)
            # 3. Commercial unlock conversion (25%)
            v_score = proj.starts * 0.40
            c_score = (proj.completion_rate_pct / 10.0) * 0.35
            u_score = proj.unlock_successes * 0.25
            total = round((v_score + c_score + u_score) * conf, 4)
            return (total, proj.starts, s.get("id"))

        return sorted(candidates, key=score_trending, reverse=True)

    def resolve_section_items(
        self,
        section: Dict[str, Any],
        all_stories: Dict[str, Any],
        eval_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes Section Resolution according to mode:
        1. MANUAL: Pure hand-curated editorial slots. Preserves editorial items exactly as specified.
        2. HYBRID: Pinned editorial items take strict precedence (indices 0..N). Remaining slots auto-filled dynamically.
        3. ALGORITHMIC: Entirely dynamic candidates ranked by policy without hardcoded editorial slots.

        Guarantees:
        - Never duplicate pinned items during dynamic fill.
        - Respect max_items constraint strictly.
        - Enforce genre_filter before ranking/fill.
        - If insufficient eligible inventory matches genre, returns fewer items without violating genre.
        - Attaches merchandising provenance metadata to the section.
        """
        mode = section.get("source", {}).get("mode", "manual").lower()
        max_items = section.get("source", {}).get("max_items", 10)
        genre_filter = section.get("source", {}).get("genre_filter")
        algo_type = section.get("source", {}).get("algo_type", "velocity_24h")
        pinned_ids = section.get("source", {}).get("pinned_content_ids", [])
        explicit_items = section.get("items", [])

        # Step 1: In MANUAL mode, preserve explicitly configured editorial items
        if mode == "manual":
            # If explicit items exist, respect them
            if explicit_items:
                return explicit_items[:max_items]
            # If no items defined but pinned_ids exist, populate pinned
            resolved = []
            seen = set()
            for pid in pinned_ids:
                if pid in all_stories and pid not in seen and len(resolved) < max_items:
                    story = all_stories[pid]
                    resolved.append({
                        "slot_id": f"slot_{section.get('section_id', 'sec')}_{pid}",
                        "content_type": "series",
                        "content_id": pid,
                        "badge": "SPOTLIGHT" if story.get("is_original") else None,
                        "story": story,
                        "is_active": True
                    })
                    seen.add(pid)
            return resolved

        # Step 2: HYBRID or ALGORITHMIC
        resolved_items: List[Dict[str, Any]] = []
        existing_ids: Set[str] = set()

        # In HYBRID mode: Pinned items retain absolute precedence
        if mode == "hybrid":
            # First, any explicit items in section
            for item in explicit_items:
                cid = item.get("content_id")
                if cid and cid in all_stories and cid not in existing_ids and len(resolved_items) < max_items:
                    item_copy = dict(item)
                    item_copy["story"] = all_stories[cid]
                    resolved_items.append(item_copy)
                    existing_ids.add(cid)

            # Second, any pinned_ids in source
            for pid in pinned_ids:
                if pid in all_stories and pid not in existing_ids and len(resolved_items) < max_items:
                    story = all_stories[pid]
                    resolved_items.append({
                        "slot_id": f"slot_{section.get('section_id', 'sec')}_{pid}",
                        "content_type": "series",
                        "content_id": pid,
                        "badge": "PINNED",
                        "story": story,
                        "is_active": True
                    })
                    existing_ids.add(pid)

        # Step 3: Dynamic Fill for ALGORITHMIC or remaining HYBRID slots
        remaining_slots = max_items - len(resolved_items)
        if remaining_slots > 0:
            # 1. Fetch publication-eligible catalog
            eligible_catalog = self.get_published_eligible_catalog(eval_time=eval_time)
            
            # 2. Enforce genre filtering BEFORE ranking
            genre_filtered_catalog = self.filter_by_genre(eligible_catalog, genre_filter)

            # 3. Exclude already placed/pinned items (Strict duplicate prevention)
            candidates = [s for s in genre_filtered_catalog if s["id"] not in existing_ids]

            # 4. Rank candidates through policy algorithm
            ranked_candidates = self.rank_candidates(candidates, algo_type=algo_type, eval_time=eval_time)

            # 5. Populate remaining slots
            for story in ranked_candidates:
                if len(resolved_items) >= max_items:
                    break
                sid = story["id"]
                resolved_items.append({
                    "slot_id": f"slot_{section.get('section_id', 'sec')}_{sid}",
                    "content_type": "series",
                    "content_id": sid,
                    "badge": None,  # Separate viewer-facing badges from merchandising signals
                    "story": story,
                    "is_active": True
                })
                existing_ids.add(sid)

        return resolved_items


merchandising_policy_service = MerchandisingPolicyService()
