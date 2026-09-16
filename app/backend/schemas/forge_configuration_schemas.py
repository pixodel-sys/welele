"""
Welele Media™ — Forge Configuration Registry Schemas (v1)
Provenance metadata contract for reproducing Story Forge execution environments.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ForgeConfigurationSnapshot(BaseModel):
    forge_configuration_id: str = Field(..., description="Immutable snapshot identifier, e.g. CFG-001")
    forge_engine_version: str = Field(..., description="Version of the narrative reasoning engine")
    creative_constitution_version: str = Field(..., description="Version of the dramatic & cultural constitution")
    skill_versions: Dict[str, str] = Field(..., description="Map of reasoning skill names to version strings")
    evaluation_framework_version: str = Field(..., description="Version of the scoring & milestone evaluation rubric")
    created_at: str = Field(..., description="ISO-8601 UTC creation timestamp")
    config_hash: str = Field(..., description="Deterministic SHA-256 hash of configuration attributes")
    description: Optional[str] = Field(None, description="Internal summary of the configuration target")
    is_active: bool = Field(True, description="Whether this configuration is currently the active default")


class CreateForgeConfigurationRequest(BaseModel):
    forge_engine_version: str = Field(..., description="Version of the narrative reasoning engine")
    creative_constitution_version: str = Field(..., description="Version of the dramatic & cultural constitution")
    skill_versions: Dict[str, str] = Field(..., description="Map of reasoning skill names to version strings")
    evaluation_framework_version: str = Field(..., description="Version of the scoring & milestone evaluation rubric")
    description: Optional[str] = Field(None, description="Internal summary of the configuration target")
    is_active: Optional[bool] = Field(False, description="Whether to make this configuration active")
