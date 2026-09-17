"""
Welele Media™ — Series & Episode Downstream Governance Service
Implements the canonical downstream layer: Story Package (M3) → Series → Episode.

Enforces the 5 Governance Corrections:
  1. Distinguishes upstream source_lineage_hash from downstream artifact_lineage_hash.
  2. Respects M3 Story Package completion as existing upstream authority; zero duplicate certification.
  3. References existing Episode Production Pack directly via production_pack_id.
  4. PACK_COORDINATED is strictly structural coordination, NOT production/distribution readiness.
  5. Continuity inheritance is stored as references (anchors, carried forward state) + explicit mutations, NOT duplicated lore.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.production_repository import production_repository
from schemas.production_schemas import ProvenanceType, CanonMutationError
from schemas.series_episode_schemas import (
    SeriesLifecycleState,
    EpisodeLifecycleState,
    EpisodeReadinessState,
    ContinuityReference,
    ReadinessAudit,
    SeriesModel,
    EpisodeModel
)


class SeriesEpisodeService:
    def __init__(self):
        self.ip_repo = ip_repository
        self.series_repo = series_repository
        self.prod_repo = production_repository

    def create_series_from_story_package(
        self,
        ip_id: str,
        story_package_id: str,
        season_number: int = 1,
        custom_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a downstream Series by referencing an authoritative upstream Story Package.
        Rejects unparented / orphan creation.
        """
        # 1. Validate upstream Digital IP
        ip_detail = self.ip_repo.get_ip_detail(ip_id)
        if not ip_detail or not ip_detail.get("ip"):
            raise ValueError(f"Orphan Error: Digital IP '{ip_id}' does not exist.")

        ip_data = ip_detail["ip"]

        # 2. Validate authoritative upstream Story Package
        story_packages = ip_detail.get("story_packages", [])
        target_pkg = next((p for p in story_packages if p.get("id") == story_package_id), None)
        if not target_pkg:
            raise ValueError(f"Orphan Error: Story Package '{story_package_id}' not found on IP '{ip_id}'.")

        # Check if series already exists for this (ip_id, story_package_id, season_number)
        all_series = self.series_repo.local_get("series") or []
        existing = next(
            (s for s in all_series if s.get("ip_id") == ip_id and s.get("story_package_id") == story_package_id and s.get("season_number") == season_number),
            None
        )
        if existing:
            return existing

        source_hash = target_pkg.get("lineage_hash") or "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        cfg_id = target_pkg.get("forge_configuration_id") or "CFG-001"

        # Unique downstream artifact lineage hash
        artifact_hash = SeriesModel.compute_artifact_hash(ip_id, story_package_id, season_number, source_hash)
        series_id = f"series_{ip_id.replace('ip_', '')}_s{season_number}_{uuid.uuid4().hex[:6]}"

        title_val = custom_title or target_pkg.get("package_title") or ip_data.get("title") or "Untitled Series"
        spine = target_pkg.get("chronology_spine") or []

        series_model = SeriesModel(
            id=series_id,
            ip_id=ip_id,
            story_package_id=story_package_id,
            season_number=season_number,
            title=title_val,
            tagline=target_pkg.get("thematic_premise") or ip_data.get("logline"),
            synopsis=target_pkg.get("logline") or ip_data.get("synopsis"),
            genre=target_pkg.get("genre") or ip_data.get("genre"),
            primary_language=target_pkg.get("primary_language") or ip_data.get("primary_language") or "isiZulu",
            format=target_pkg.get("format") or "9:16 Vertical Microdrama",
            target_duration_seconds=target_pkg.get("target_duration_seconds") or 90,
            total_episodes=0,
            lifecycle_state=SeriesLifecycleState.DRAFT,
            forge_configuration_id=cfg_id,
            source_lineage_hash=source_hash,
            artifact_lineage_hash=artifact_hash,
            provenance=ProvenanceType.CANON,
            chronology_spine_anchor_count=len(spine),
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )

        saved_series = self.series_repo.local_insert("series", series_model.model_dump())
        return saved_series

    def create_episode(
        self,
        series_id: str,
        episode_number: int,
        custom_title: Optional[str] = None,
        is_empty_draft: bool = True,
        link_existing_production_pack: bool = True,
        media_asset_id: Optional[str] = None,
        video_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a downstream Episode referencing its parent Series and upstream Story Package.
        Rejects orphan creation. Enforces identity uniqueness and sparse-input honesty.
        """
        # 1. Enforce parent Series existence (Orphan Rejection)
        series_data = self.series_repo.get_series(series_id)
        if not series_data:
            raise ValueError(f"Orphan Rejection: Parent Series '{series_id}' does not exist.")

        ip_id = series_data.get("ip_id")
        story_package_id = series_data.get("story_package_id")
        if not story_package_id:
            raise ValueError(f"Orphan Rejection: Parent Series '{series_id}' has no upstream Story Package reference.")

        # 2. Check identity uniqueness (series_id, episode_number)
        all_episodes = self.series_repo.get_episodes_for_series(series_id)
        duplicate = next((e for e in all_episodes if e.get("episode_number") == episode_number), None)
        if duplicate:
            raise ValueError(f"Identity Collision: Episode {episode_number} already exists in Series '{series_id}'.")

        # 3. Fetch upstream package continuity & previous episode state (Reference without duplicating canon)
        ip_detail = self.ip_repo.get_ip_detail(ip_id)
        story_packages = ip_detail.get("story_packages", []) if ip_detail else []
        target_pkg = next((p for p in story_packages if p.get("id") == story_package_id), {})

        chronology_spine = target_pkg.get("chronology_spine", [])
        anchor_entry = next((a for a in chronology_spine if a.get("anchor_number") == episode_number), None)
        anchor_name = anchor_entry.get("anchor_name") if anchor_entry else f"Episode {episode_number} Inception"

        # Previous episode reference
        previous_ep = next((e for e in all_episodes if e.get("episode_number") == episode_number - 1), None)
        previous_ep_id = previous_ep.get("id") if previous_ep else None

        carried_forward = None
        if previous_ep:
            carried_forward = f"Carried forward state from Episode {previous_ep.get('episode_number')} ({previous_ep.get('title')})"
        elif anchor_entry:
            carried_forward = anchor_entry.get("summary")

        continuity_ref = ContinuityReference(
            anchor_number_ref=episode_number if anchor_entry else None,
            anchor_name_ref=anchor_name,
            previous_episode_id_ref=previous_ep_id,
            carried_forward_state_ref=carried_forward,
            active_plant_refs=[p.get("plant") for p in target_pkg.get("plants", []) if isinstance(p, dict) and "plant" in p],
            episode_state_mutations=[f"Episode {episode_number} lifecycle established in Series '{series_id}'."],
            provenance=ProvenanceType.CANON,
            source_path=f"story_package.chronology_spine[{episode_number - 1}]" if anchor_entry else "story_package.beats"
        )

        # 4. Check for existing Episode Production Pack
        linked_pack_id = None
        if link_existing_production_pack:
            # Query existing packs
            existing_packs = self.prod_repo.local_get("episode_production_packs") or []
            matched_pack = next(
                (p for p in existing_packs if p.get("ip_id") == ip_id and p.get("episode_number") == episode_number),
                None
            )
            if matched_pack:
                linked_pack_id = matched_pack.get("id")

        # 5. Determine Readiness State & Build Honest Audit
        has_media = bool(media_asset_id or (video_url and not video_url.startswith("/videos/welele_placeholder")))
        has_pack = bool(linked_pack_id)
        
        # Sparse-input honesty: PACK_COORDINATED is structural coordination, NOT production ready!
        if has_media and has_pack:
            readiness_state = EpisodeReadinessState.PRODUCTION_READY
            lifecycle_state = EpisodeLifecycleState.SCHEDULED
            is_empty_draft_final = False
        elif has_pack:
            readiness_state = EpisodeReadinessState.PACK_COORDINATED
            lifecycle_state = EpisodeLifecycleState.DRAFT
            is_empty_draft_final = False
        elif target_pkg.get("beats"):
            readiness_state = EpisodeReadinessState.BEAT_OUTLINED
            lifecycle_state = EpisodeLifecycleState.DRAFT
            is_empty_draft_final = is_empty_draft
        else:
            readiness_state = EpisodeReadinessState.DRAFT_EMPTY
            lifecycle_state = EpisodeLifecycleState.DRAFT
            is_empty_draft_final = True

        missing_elements: List[str] = []
        if not has_media:
            missing_elements.append("Missing Master Video Asset (No High-DPI Camera Master)")
        if not has_pack:
            missing_elements.append("Missing Coordinated 5-Track Production Pack")
        if not thumbnail_url:
            missing_elements.append("Missing High-Resolution 9:16 Thumbnail")

        audit = ReadinessAudit(
            is_empty_draft=is_empty_draft_final,
            has_story_package_ref=True,
            has_production_pack_ref=has_pack,
            has_media_asset_ref=bool(media_asset_id),
            has_master_video=has_media,
            has_subtitles=False,
            missing_elements=missing_elements,
            readiness_state=readiness_state,
            audited_at=datetime.now(timezone.utc).isoformat()
        )

        source_hash = series_data.get("source_lineage_hash") or "f65ead9a0006d40f0647a2277eb2efc20443c174b32370ffdecd940199d892e6"
        cfg_id = series_data.get("forge_configuration_id") or "CFG-001"
        artifact_hash = EpisodeModel.compute_artifact_hash(series_id, episode_number, source_hash, linked_pack_id)

        title_val = custom_title or (f"Episode {episode_number}: {anchor_name}" if anchor_entry else f"Episode {episode_number}")
        ep_id = f"ep_{series_id}_{episode_number}"

        episode_model = EpisodeModel(
            id=ep_id,
            series_id=series_id,
            ip_id=ip_id,
            story_package_id=story_package_id,
            episode_number=episode_number,
            title=title_val,
            synopsis=anchor_entry.get("summary") if anchor_entry else f"Episode {episode_number} of {series_data.get('title')}",
            duration_seconds=series_data.get("target_duration_seconds", 90),
            lifecycle_state=lifecycle_state,
            readiness_state=readiness_state,
            continuity_reference=continuity_ref,
            production_pack_id=linked_pack_id,
            media_asset_id=media_asset_id,
            video_url=video_url or "/videos/welele_placeholder.mp4",
            thumbnail_url=thumbnail_url or "/posters/blood_ties.jpg",
            is_empty_draft=is_empty_draft_final,
            readiness_audit=audit,
            forge_configuration_id=cfg_id,
            source_lineage_hash=source_hash,
            artifact_lineage_hash=artifact_hash,
            provenance=ProvenanceType.CANON,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )

        saved_ep = self.series_repo.local_insert("episodes", episode_model.model_dump())
        # Increment series episode count
        current_count = len(all_episodes) + 1
        self.series_repo.local_update("series", "id", series_id, {"total_episodes": current_count})

        return saved_ep

    def audit_episode_readiness(self, episode_id: str) -> ReadinessAudit:
        """
        Performs a strictly honest evaluation of episode readiness.
        Guarantees that empty/draft episodes never receive false positive green lights.
        """
        all_eps = self.series_repo.local_get("episodes") or []
        ep = next((e for e in all_eps if e.get("id") == episode_id), None)
        if not ep:
            raise ValueError(f"Episode '{episode_id}' not found.")

        has_media = bool(ep.get("media_asset_id") or (ep.get("video_url") and not ep.get("video_url", "").startswith("/videos/welele_placeholder")))
        has_pack = bool(ep.get("production_pack_id"))
        is_empty = ep.get("is_empty_draft", True)

        missing: List[str] = []
        if not has_media:
            missing.append("Missing Master Video Asset (Camera Master 1080x1920)")
        if not has_pack:
            missing.append("Missing Coordinated 5-Track Production Pack")
        if not ep.get("thumbnail_url") or ep.get("thumbnail_url", "").startswith("/posters/blood_ties.jpg"):
            missing.append("Missing Certified Episode Thumbnail")

        if has_media and has_pack and not is_empty:
            readiness = EpisodeReadinessState.PRODUCTION_READY
        elif has_pack:
            readiness = EpisodeReadinessState.PACK_COORDINATED
        elif not is_empty:
            readiness = EpisodeReadinessState.BEAT_OUTLINED
        else:
            readiness = EpisodeReadinessState.DRAFT_EMPTY

        audit = ReadinessAudit(
            is_empty_draft=is_empty,
            has_story_package_ref=bool(ep.get("story_package_id")),
            has_production_pack_ref=has_pack,
            has_media_asset_ref=bool(ep.get("media_asset_id")),
            has_master_video=has_media,
            has_subtitles=bool(ep.get("subtitles")),
            missing_elements=missing,
            readiness_state=readiness,
            audited_at=datetime.now(timezone.utc).isoformat()
        )

        # Update episode audit cache
        self.series_repo.local_update("episodes", "id", episode_id, {
            "readiness_audit": audit.model_dump(),
            "readiness_state": readiness.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        return audit

    def validate_canonical_mutation_boundary(self, series_id: str, proposed_updates: Dict[str, Any]) -> None:
        """
        Enforces that downstream Series/Episode operations cannot mutate upstream Story Package facts
        (characters, logline, thematic premise, world rules, canon lineage).
        """
        forbidden_upstream_keys = {
            "characters",
            "character_bible",
            "world_rules",
            "lore",
            "logline",
            "thematic_premise",
            "dramatic_engine",
            "source_lineage_hash",
            "forge_configuration_id"
        }

        mutated = forbidden_upstream_keys.intersection(proposed_updates.keys())
        if mutated:
            raise CanonMutationError(
                f"Downstream Truth Boundary Violation: Attempted to mutate upstream canon fields {list(mutated)} via downstream Series/Episode layer."
            )

    def cascade_series_lifecycle(self, series_id: str, target_state: SeriesLifecycleState) -> Dict[str, Any]:
        """
        Updates series lifecycle state and cascades safely to non-published child episodes.
        """
        series = self.series_repo.get_series(series_id)
        if not series:
            raise ValueError(f"Series '{series_id}' not found.")

        updated_series = self.series_repo.local_update(
            "series",
            "id",
            series_id,
            {"lifecycle_state": target_state.value, "updated_at": datetime.now(timezone.utc).isoformat()}
        )

        # Cascade to child episodes if archiving
        if target_state == SeriesLifecycleState.ARCHIVED:
            episodes = self.series_repo.get_episodes_for_series(series_id)
            for ep in episodes:
                if ep.get("lifecycle_state") != EpisodeLifecycleState.PUBLISHED.value:
                    self.series_repo.local_update(
                        "episodes",
                        "id",
                        ep["id"],
                        {"lifecycle_state": EpisodeLifecycleState.ARCHIVED.value, "updated_at": datetime.now(timezone.utc).isoformat()}
                    )

        return updated_series


series_episode_service = SeriesEpisodeService()
