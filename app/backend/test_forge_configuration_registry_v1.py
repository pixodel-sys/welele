"""
Welele Media™ — Forge Configuration Registry V1 Test Suite
Validates:
1. Immutable forge_configuration_id (CFG-001 baseline)
2. Snapshot storage & reproducibility contract
3. Story Package configuration ID attachment & lineage preservation
4. Exact configuration snapshot retrieval for Story Packages
5. Deterministic hashing & distinct ID generation for modified configurations
6. Strict boundary isolation: configuration internals shielded from Story Review
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from repositories.forge_configuration_repository import forge_config_repo
from repositories.ip_repository import ip_repository
from schemas.ip_schemas import CreateIPRequest, StoryWorldSchema, CharacterBibleSchema, RightsSplitSchema

client = TestClient(app)


def get_auth_headers(user_id: str = "creator_zola", role: str = "creator"):
    token = create_access_token(user_id=user_id, role=role, creator_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_forge_configuration_registry_v1_baseline():
    """Validates default CFG-001 immutable baseline configuration."""
    admin_headers = get_auth_headers("admin_supervisor", "admin")

    # 1. Query baseline configuration
    res = client.get("/api/v1/forge/configurations/CFG-001", headers=admin_headers)
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["forge_configuration_id"] == "CFG-001"
    assert cfg["forge_engine_version"] == "v2.4.0-kernel"
    assert cfg["creative_constitution_version"] == "v1.2.0-mzansi"
    assert "dramatic_engine" in cfg["skill_versions"]
    assert "cliffhanger_architecture" in cfg["skill_versions"]
    assert cfg["evaluation_framework_version"] == "v2.1.0-4dimension"
    assert len(cfg["config_hash"]) == 64
    assert cfg["is_active"] is True


def test_forge_configuration_immutability_and_idempotent_registration():
    """Validates that identical configuration payloads return the existing ID without mutation."""
    admin_headers = get_auth_headers("admin_supervisor", "admin")

    cfg_1_original = forge_config_repo.get_configuration("CFG-001")
    original_hash = cfg_1_original["config_hash"]

    # Attempt to re-register the identical CFG-001 configuration
    req_payload = {
        "forge_engine_version": "v2.4.0-kernel",
        "creative_constitution_version": "v1.2.0-mzansi",
        "skill_versions": cfg_1_original["skill_versions"],
        "evaluation_framework_version": "v2.1.0-4dimension",
        "description": "Attempted Duplicate CFG-001"
    }
    res = client.post("/api/v1/forge/configurations", json=req_payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["forge_configuration_id"] == "CFG-001"
    assert data["config_hash"] == original_hash

    # Verify CFG-001 remains unchanged
    cfg_1_after = forge_config_repo.get_configuration("CFG-001")
    assert cfg_1_after["config_hash"] == original_hash
    assert cfg_1_after["description"] == "Canonical Production Baseline Configuration v1"


def test_distinct_configuration_produces_new_immutable_id():
    """Validates that a modified configuration produces a new sequential ID (CFG-002)."""
    admin_headers = get_auth_headers("admin_supervisor", "admin")

    # Register updated configuration (e.g. engine v2.5.0-kernel, updated skills)
    modified_payload = {
        "forge_engine_version": "v2.5.0-kernel",
        "creative_constitution_version": "v1.3.0-pan-african",
        "skill_versions": {
            "chronology_anchor": "v1.1.0",
            "cliffhanger_architecture": "v1.1.0",
            "cultural_grounding": "v1.1.0",
            "dialogue_authenticity": "v1.1.0",
            "dramatic_engine": "v1.1.0"
        },
        "evaluation_framework_version": "v2.2.0-multi-genre",
        "description": "Next Generation Pan-African Production Configuration v2",
        "is_active": False
    }

    res = client.post("/api/v1/forge/configurations", json=modified_payload, headers=admin_headers)
    assert res.status_code == 200
    cfg_2 = res.json()
    assert cfg_2["forge_configuration_id"].startswith("CFG-")
    assert cfg_2["forge_configuration_id"] != "CFG-001"
    assert cfg_2["forge_engine_version"] == "v2.5.0-kernel"
    assert len(cfg_2["config_hash"]) == 64

    # Verify both configurations are listed
    res_list = client.get("/api/v1/forge/configurations", headers=admin_headers)
    assert res_list.status_code == 200
    all_cfgs = res_list.json()
    cfg_ids = [c["forge_configuration_id"] for c in all_cfgs]
    assert "CFG-001" in cfg_ids
    assert cfg_2["forge_configuration_id"] in cfg_ids


def test_story_package_retains_and_retrieves_exact_configuration():
    """Validates Story Package configuration attachment, lineage preservation, and snapshot retrieval."""
    creator_headers = get_auth_headers("creator_zola", "creator")

    # 1. Create a test IP
    test_ip_id = "ip_cfg_test_001"
    existing_ip = ip_repository.get_ip_detail(test_ip_id)
    if not existing_ip or not existing_ip.get("ip"):
        ip_req = CreateIPRequest(
            title="Provenance Ledger",
            franchise_code="IP-PROV-LEDGER",
            logline="Testing Story Package configuration provenance.",
            synopsis="Test synopsis for provenance verification.",
            genre="Mystery",
            primary_language="English",
            master_owner_id="creator_zola",
            story_world=StoryWorldSchema(
                world_name="Provenance Arena",
                geographical_setting="Johannesburg",
                time_period="2026",
                mythology_and_rules="All contracts are immutable.",
                cultural_context="Urban South Africa"
            ),
            characters=[
                CharacterBibleSchema(
                    name="Auditor Alpha",
                    role="protagonist",
                    archetype="The Verifier",
                    secret_motivation="Verify system integrity",
                    fatal_flaw="Over-reliance on automation",
                    signature_quote="Integrity is non-negotiable."
                )
            ]
        )
        created_ip = ip_repository.create_ip(ip_req)
        test_ip_id = created_ip["ip"]["id"]

    # 2. Save Story Package with default configuration (CFG-001)
    pkg_payload_1 = {
        "ip_id": test_ip_id,
        "creator_id": "creator_zola",
        "package_title": "Provenance Ledger: Ep 1",
        "target_duration_seconds": 90,
        "beats": [{"beat_number": 1, "description": "Verification starts."}],
        "dialogues": [{"character": "Auditor Alpha", "line": "Checking config snapshot."}],
        "cliffhanger_prompt": "Will the configuration snapshot verify?",
        "human_approved": True
    }
    res_pkg_1 = client.post(f"/api/ip/{test_ip_id}/story-forge/save", json=pkg_payload_1, headers=creator_headers)
    assert res_pkg_1.status_code == 200
    pkg_1 = res_pkg_1.json()["package"]
    pkg_1_id = pkg_1["id"]
    assert pkg_1["forge_configuration_id"] == "CFG-001"
    assert len(pkg_1["lineage_hash"]) == 64

    # 3. Retrieve exact configuration snapshot via /packages/{package_id}/configuration
    res_pkg_cfg = client.get(f"/api/v1/forge/packages/{pkg_1_id}/configuration", headers=creator_headers)
    assert res_pkg_cfg.status_code == 200
    attached_cfg = res_pkg_cfg.json()
    assert attached_cfg["forge_configuration_id"] == "CFG-001"
    assert attached_cfg["forge_engine_version"] == "v2.4.0-kernel"
    assert attached_cfg["creative_constitution_version"] == "v1.2.0-mzansi"


def test_story_review_does_not_leak_forge_configuration_provenance():
    """Validates that Story Review diagnostics and submissions do NOT leak Forge configuration internals."""
    creator_headers = get_auth_headers("creator_zola", "creator")

    draft = {
        "title": "Review Isolation Test",
        "logline": "Testing that Story Review remains isolated from Forge configuration internals.",
        "target_format": "VERTICAL_MICRODRAMA",
        "full_draft_text": "Draft content for isolation test..."
    }
    res_save = client.post("/api/v1/review/drafts", json=draft, headers=creator_headers)
    assert res_save.status_code == 200
    saved_draft = res_save.json()["draft"]

    res_diag = client.post("/api/v1/review/diagnose", json=saved_draft)
    assert res_diag.status_code == 200
    diag_data = res_diag.json()

    # Verify no Forge configuration internals exist in Story Review output
    assert "forge_configuration_id" not in diag_data
    assert "forge_engine_version" not in diag_data
    assert "creative_constitution_version" not in diag_data
    assert "config_hash" not in diag_data
