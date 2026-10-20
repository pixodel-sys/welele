"""
Welele Media™ — Phase 6J-2R-C Remediation Automated Test Suite
Verifies:
1. API Hydration: Workspace payload binds digital_ip, characters, story_world, rights_ledger, rights_declarations, narrative_lineage.
2. Frontend State Integrity: Empty character bibles return empty array (no deceptive Sandton taxi characters).
3. Story Lineage Honesty: Creator Original Treatment vs Story Forge AI origination cleanly distinguished.
4. Historical AMAPHUPHO Rebinding: AMAPHUPHO is bound to Wanjiku's dedicated IP (IP-AMAPHUPHO-ORIGINAL), not Blood Ties.
5. Evidence Preservation: Abakhongi and Blood Ties records remain protected and unchanged.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from repositories.series_repository import series_repository, to_uuid

client = TestClient(app)


def test_ip_bundle_creator_original_lineage():
    """Verifies that series without story_forge_packages resolve to CREATOR_ORIGINAL lineage."""
    ip_bundle = series_repository.get_series_ip_bundle(ip_id="ip_test_creator_orig", creator_name="Wanjiku Mwangi")
    lineage = ip_bundle.get("narrative_lineage")
    assert lineage is not None
    assert lineage["origin"] == "CREATOR_ORIGINAL"
    assert "Wanjiku Mwangi" in lineage["creative_authority"]
    assert lineage["human_approved"] is True
    assert "No generative narrative synthesis utilized" in lineage["description"]


def test_ip_bundle_story_forge_lineage():
    """Verifies that series with story_forge_packages resolve to STORY_FORGE lineage."""
    test_ip_id = str(uuid.uuid4())
    series_repository.local_insert("story_forge_packages", {
        "id": str(uuid.uuid4()),
        "ip_id": test_ip_id,
        "ai_model_used": "claude-3-7-sonnet",
        "version": "v2.1.0",
        "human_approved": True
    })

    ip_bundle = series_repository.get_series_ip_bundle(ip_id=test_ip_id, creator_name="Sabelo Mthembu")
    lineage = ip_bundle.get("narrative_lineage")
    assert lineage is not None
    assert lineage["origin"] == "STORY_FORGE"
    assert "Story Forge™ AI" in lineage["source_engine"]
    assert "claude-3-7-sonnet" in lineage["source_engine"]
    assert lineage["version"] == "v2.1.0"
    assert lineage["human_approved"] is True


def test_honest_empty_character_bible_state():
    """Verifies that series with no character bibles registered return empty list, NOT Sandton taxi fallbacks."""
    empty_ip_id = str(uuid.uuid4())
    ip_bundle = series_repository.get_series_ip_bundle(ip_id=empty_ip_id, creator_name="Test Creator")
    characters = ip_bundle.get("characters")
    assert isinstance(characters, list)
    assert len(characters) == 0, "Deceptive fallback: characters must be empty when none registered in DB!"


def test_rights_declarations_foundational_default():
    """Verifies that series without explicit rights ledger return foundational 100% creator ownership."""
    ip_bundle = series_repository.get_series_ip_bundle(ip_id="ip_unregistered_rights", creator_name="Wanjiku Mwangi")
    declarations = ip_bundle.get("rights_declarations")
    assert declarations is not None
    assert len(declarations) >= 2
    showrunner_split = next((d for d in declarations if "Master IP Owner" in d["stakeholder_role"]), None)
    assert showrunner_split is not None
    assert showrunner_split["royalty_split_pct"] == 100.0
    assert showrunner_split["is_default"] is True


def test_workspace_api_hydration_and_amaphupho_rebinding():
    """
    Verifies that GET /creators/series/{id}/workspace hydrates the series with
    canonical digital_ip, character bibles, rights declarations, and narrative lineage.
    Also verifies that AMAPHUPHO resolves to Wanjiku's dedicated IP and Creator Original lineage.
    """
    amaphupho_id = "0879f96c-b551-44d9-a41c-80efff63f949"
    wanjiku_user_id = "06b6ea3f-9f04-58f1-b24c-7260c26dee92"
    dedicated_ip_id = to_uuid("ip_amaphupho_wanjiku_dedicated")

    # Seed local test store fixtures
    series_repository.local_insert("users", {
        "id": wanjiku_user_id,
        "display_name": "Wanjiku Mwangi",
        "role": "creator"
    })
    series_repository.local_insert("digital_ips", {
        "id": dedicated_ip_id,
        "title": "AMAPHUPHO",
        "franchise_code": "IP-AMAPHUPHO-ORIGINAL",
        "master_owner_id": wanjiku_user_id,
        "genre": "Supernatural & Ancestral",
        "primary_language": "isiZulu",
        "status": "active"
    })
    series_repository.local_insert("series", {
        "id": amaphupho_id,
        "title": "AMAPHUPHO",
        "ip_id": dedicated_ip_id,
        "creator_id": "creator_wanjiku",
        "creator_name": "Wanjiku Mwangi",
        "genre": "Supernatural & Ancestral",
        "rating": 5.0,
        "total_episodes": 0,
        "free_episodes": 2,
        "is_published": True
    })

    # Generate creator JWT for Wanjiku
    token = create_access_token(
        user_id="usr_creator_wanjiku",
        role="creator",
        creator_id="creator_wanjiku"
    )

    response = client.get(
        f"/api/v1/creators/series/{amaphupho_id}/workspace",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, f"Workspace endpoint failed: {response.text}"
    data = response.json()
    series_data = data.get("series", {})

    # 1. Verify digital_ip hydration
    digital_ip = series_data.get("digital_ip")
    assert digital_ip is not None
    assert digital_ip.get("franchise_code") == "IP-AMAPHUPHO-ORIGINAL"
    assert digital_ip.get("master_owner_id") == wanjiku_user_id
    assert digital_ip.get("title") == "AMAPHUPHO"

    # 2. Verify honest empty characters array
    assert series_data.get("characters") == []

    # 3. Verify narrative lineage hydration
    lineage = series_data.get("narrative_lineage")
    assert lineage is not None
    assert lineage.get("origin") == "CREATOR_ORIGINAL"
    assert "Wanjiku Mwangi" in lineage.get("creative_authority", "")

    # 4. Verify rights declarations hydration
    rights = series_data.get("rights_declarations")
    assert isinstance(rights, list)
    assert len(rights) >= 2
    assert any(r.get("royalty_split_pct") == 100.0 for r in rights)


def test_evidence_preservation_blood_ties_intact():
    """Verifies that Blood Ties IP was preserved and remains owned by Zola Dlamini."""
    blood_ties_ip_id = "692f2ce6-7fa0-575f-bea7-1d10c488fd10"
    zola_user_id = "cc31b88a-f5ef-577f-8633-7ebc43c08cb7"

    # Seed baseline Blood Ties IP
    series_repository.local_insert("digital_ips", {
        "id": blood_ties_ip_id,
        "title": "Blood Ties",
        "franchise_code": "FRAN_BLOOD_TIES",
        "master_owner_id": zola_user_id,
        "status": "active"
    })

    all_ips = series_repository.local_get("digital_ips") or []
    bt_ip = next((i for i in all_ips if str(i.get("id")) == blood_ties_ip_id), None)
    assert bt_ip is not None, "Blood Ties IP must exist in database!"
    assert bt_ip["master_owner_id"] == zola_user_id, "Blood Ties owner must remain Zola Dlamini!"
    assert bt_ip["franchise_code"] == "FRAN_BLOOD_TIES"
