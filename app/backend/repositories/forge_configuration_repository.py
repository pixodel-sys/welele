"""
Welele Media™ — Forge Configuration Registry Repository (v1)
Foundational provenance layer managing immutable configuration snapshots.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .base_repository import BaseRepository


class ForgeConfigurationRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self._seed_default_configuration()

    def _compute_config_hash(
        self,
        forge_engine_version: str,
        creative_constitution_version: str,
        skill_versions: Dict[str, str],
        evaluation_framework_version: str
    ) -> str:
        canonical_dict = {
            "creative_constitution_version": creative_constitution_version,
            "evaluation_framework_version": evaluation_framework_version,
            "forge_engine_version": forge_engine_version,
            "skill_versions": {k: skill_versions[k] for k in sorted(skill_versions.keys())}
        }
        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def _seed_default_configuration(self):
        existing = self.local_get("forge_configurations")
        if not existing:
            default_skills = {
                "chronology_anchor": "v1.0.0",
                "cliffhanger_architecture": "v1.0.0",
                "cultural_grounding": "v1.0.0",
                "dialogue_authenticity": "v1.0.0",
                "dramatic_engine": "v1.0.0"
            }
            config_hash = self._compute_config_hash(
                forge_engine_version="v2.4.0-kernel",
                creative_constitution_version="v1.2.0-mzansi",
                skill_versions=default_skills,
                evaluation_framework_version="v2.1.0-4dimension"
            )
            cfg_1 = {
                "forge_configuration_id": "CFG-001",
                "forge_engine_version": "v2.4.0-kernel",
                "creative_constitution_version": "v1.2.0-mzansi",
                "skill_versions": default_skills,
                "evaluation_framework_version": "v2.1.0-4dimension",
                "created_at": "2026-09-16T12:00:00Z",
                "config_hash": config_hash,
                "description": "Canonical Production Baseline Configuration v1",
                "is_active": True
            }
            self.local_insert("forge_configurations", cfg_1)

    def list_configurations(self) -> List[Dict[str, Any]]:
        return self.local_get("forge_configurations")

    def get_configuration(self, forge_configuration_id: str) -> Optional[Dict[str, Any]]:
        configs = self.local_get("forge_configurations")
        return next((c for c in configs if c.get("forge_configuration_id") == forge_configuration_id), None)

    def get_active_configuration(self) -> Dict[str, Any]:
        configs = self.local_get("forge_configurations")
        active = next((c for c in configs if c.get("is_active") is True), None)
        if not active and configs:
            active = configs[0]
        if not active:
            self._seed_default_configuration()
            active = self.local_get("forge_configurations")[0]
        return active

    def register_configuration(
        self,
        forge_engine_version: str,
        creative_constitution_version: str,
        skill_versions: Dict[str, str],
        evaluation_framework_version: str,
        description: Optional[str] = None,
        is_active: bool = False
    ) -> Dict[str, Any]:
        """
        Registers a configuration snapshot. If an identical snapshot exists (by config_hash),
        returns the existing immutable record. Otherwise, generates next sequential CFG-xxx.
        """
        config_hash = self._compute_config_hash(
            forge_engine_version=forge_engine_version,
            creative_constitution_version=creative_constitution_version,
            skill_versions=skill_versions,
            evaluation_framework_version=evaluation_framework_version
        )

        configs = self.local_get("forge_configurations")
        existing = next((c for c in configs if c.get("config_hash") == config_hash), None)
        if existing:
            return existing

        # Determine next sequential identifier
        max_num = 0
        for c in configs:
            cid = c.get("forge_configuration_id", "")
            if cid.startswith("CFG-"):
                try:
                    num = int(cid.split("-")[1])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass
        new_id = f"CFG-{max_num + 1:03d}"
        now_ts = datetime.now(timezone.utc).isoformat()

        if is_active:
            for c in configs:
                c["is_active"] = False

        new_config = {
            "forge_configuration_id": new_id,
            "forge_engine_version": forge_engine_version,
            "creative_constitution_version": creative_constitution_version,
            "skill_versions": {k: skill_versions[k] for k in sorted(skill_versions.keys())},
            "evaluation_framework_version": evaluation_framework_version,
            "created_at": now_ts,
            "config_hash": config_hash,
            "description": description or f"Forge Configuration Snapshot {new_id}",
            "is_active": is_active
        }
        self.local_insert("forge_configurations", new_config)
        return new_config


forge_config_repo = ForgeConfigurationRepository()
