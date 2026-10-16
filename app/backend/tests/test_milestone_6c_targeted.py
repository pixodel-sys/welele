"""
Milestone 6C Targeted Fix Automated Verification
Tests:
1. Valid UUID generation for series.id
2. Resolution of valid digital_ips.id UUID and dynamic unique season_number
3. Enforcement of response contract ({"success": True, "story": created_series})
4. Full retrieval of created series via get_series_workspace
5. Non-masking error propagation (genuine failures raise HTTPException)
"""

import os
import uuid
import pytest
os.environ["ENVIRONMENT"] = "test"

from routers.creators import create_series, get_series_workspace
from repositories.series_repository import series_repository, to_uuid
from schemas.story_schemas import CreateSeriesRequest
from fastapi import HTTPException

def test_milestone_6c_uuid_and_ip_resolution():
    ip_id = series_repository.resolve_valid_ip_id()
    # Must be valid RFC 4122 UUID
    val = uuid.UUID(ip_id)
    assert str(val) == ip_id, f"Invalid UUID: {ip_id}"

    season_num = series_repository.resolve_next_season_number(ip_id)
    assert isinstance(season_num, int)
    assert season_num >= 1

def test_milestone_6c_series_creation_contract_and_read_path():
    req = CreateSeriesRequest(
        title="[STAGING TEST] Milestone 6C Smoke Series",
        tagline="End-to-End Staging Ingestion Verification",
        synopsis="Automated targeted verification of Milestone 6C fixes",
        cover_image="https://example.com/cover.jpg",
        vertical_poster="https://example.com/poster.jpg",
        genre="Crime & Dynasty",
        coin_price_per_episode=5
    )
    auth_user = {
        "sub": "user_zola",
        "creator_id": "creator_zola",
        "role": "creator",
        "name": "Zola Dlamini"
    }

    # Exercise creation
    res = create_series(req, auth_user)
    assert res.get("success") is True
    assert "story" in res, "Contract violation: response must include 'story'"
    created_story = res["story"]
    created_id = created_story.get("id")
    assert created_id is not None
    # Verify ID is a real UUID
    uuid_obj = uuid.UUID(created_id)
    assert str(uuid_obj) == created_id

    # Verify IP ID is a real UUID
    assert created_story.get("ip_id") is not None
    uuid.UUID(created_story["ip_id"])

    # Exercise workspace read path
    ws = get_series_workspace(created_id, auth_user)
    assert ws.get("series") is not None
    assert ws["series"]["id"] == created_id
    assert ws["series"]["title"] == "[STAGING TEST] Milestone 6C Smoke Series"
    assert ws["series"]["creator_id"] == "creator_zola"

def test_milestone_6c_error_non_masking():
    bad_auth = {
        "sub": "user_amaka",
        "creator_id": "creator_amaka",
        "role": "creator",
        "name": "Amaka"
    }
    bad_req = CreateSeriesRequest(title="Forbidden Show", genre="Drama", creator_id="creator_zola")

    with pytest.raises(HTTPException) as exc_info:
        create_series(bad_req, bad_auth)

    assert exc_info.value.status_code == 403
