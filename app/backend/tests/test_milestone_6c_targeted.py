"""
Milestone 6C Targeted Fix Automated Verification
Tests:
1. Valid UUID generation for series.id
2. Resolution of valid digital_ips.id UUID and dynamic unique season_number
3. Enforcement of response contract ({"success": True, "story": created_series})
4. Full retrieval of created series via get_series_workspace
5. Non-masking error propagation (genuine failures raise HTTPException)
6. Canonical ownership resolution (series → digital_ips → master_owner_id → creator) without title heuristics
7. add_episode() succeeds for the authenticated owning creator
8. add_episode() by a different creator is strictly rejected with 403 Forbidden
"""

import os
import uuid
import pytest
os.environ["ENVIRONMENT"] = "test"

from routers.creators import create_series, get_series_workspace, add_episode
from repositories.series_repository import series_repository, to_uuid
from repositories.ip_repository import ip_repository
from schemas.story_schemas import CreateSeriesRequest, CreateEpisodeRequest
from fastapi import HTTPException

def test_milestone_6c_uuid_and_ip_resolution():
    """Existing 6C UUID/IP resolution remains intact."""
    ip_id = series_repository.resolve_valid_ip_id()
    # Must be valid RFC 4122 UUID
    val = uuid.UUID(ip_id)
    assert str(val) == ip_id, f"Invalid UUID: {ip_id}"

    season_num = series_repository.resolve_next_season_number(ip_id)
    assert isinstance(season_num, int)
    assert season_num >= 1

def test_milestone_6c_series_creation_contract_and_read_path():
    """Existing workspace retrieval remains working."""
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

def test_milestone_6c_canonical_creator_resolution_and_episode_submission():
    """
    Verification of Requirements 1, 2, 3, 4:
    1. Newly created Zola series resolves to creator_zola through canonical ownership relationship.
    2. add_episode() succeeds for the authenticated owning creator.
    3. A different creator is rejected with 403.
    4. No title-based creator heuristic is involved in creator episode submission.
    """
    zola_auth = {
        "sub": "user_zola",
        "creator_id": "creator_zola",
        "role": "creator",
        "name": "Zola Dlamini"
    }
    amaka_auth = {
        "sub": "user_amaka",
        "creator_id": "creator_amaka",
        "role": "creator",
        "name": "Amaka Okafor"
    }

    # 1. Create a series with a title completely devoid of "blood" or "queen" keywords
    series_req = CreateSeriesRequest(
        title="Cape Town Whistleblower Chronicles",
        tagline="Truth in the shadows",
        synopsis="Investigative noir set in the Western Cape docks",
        genre="Political Thriller",
        coin_price_per_episode=5
    )
    creation_res = create_series(series_req, zola_auth)
    assert creation_res["success"] is True
    created_series = creation_res["story"]
    series_id = created_series["id"]

    # Verify canonical ownership resolution: series -> digital_ips -> master_owner_id -> creator
    resolved_creator = series_repository.resolve_series_creator_id(created_series)
    assert resolved_creator == "creator_zola", f"Expected 'creator_zola', got '{resolved_creator}'"

    # Verify get_creator_series_detail resolves canonical owner
    detail = series_repository.get_creator_series_detail(series_id)
    assert detail is not None
    assert detail["creator_id"] == "creator_zola"

    # 2. add_episode() succeeds for the authenticated owning creator (Zola)
    ep_req = CreateEpisodeRequest(
        series_id=series_id,
        episode_number=1,
        title="Dockside Informant",
        synopsis="A midnight drop goes wrong at Pier 4",
        duration_seconds=85,
        video_url="https://r2.welele.media/masters/dockside_informant.mp4",
        storage_key=f"masters/{series_id}/ep1.mp4",
        status="under_review"
    )
    ep_res = add_episode(ep_req, zola_auth)
    assert ep_res.get("success") is True
    assert ep_res.get("episode") is not None
    assert ep_res["episode"]["series_id"] == series_id
    assert ep_res["episode"]["title"] == "Dockside Informant"
    assert ep_res["episode"]["storage_key"] == f"masters/{series_id}/ep1.mp4"

    # 3. A different creator (Amaka) is strictly rejected with 403 Forbidden
    ep_req_bad = CreateEpisodeRequest(
        series_id=series_id,
        episode_number=2,
        title="Compromised Frequency",
        duration_seconds=75,
        video_url="https://r2.welele.media/masters/dockside_ep2.mp4",
        storage_key=f"masters/{series_id}/ep2.mp4",
        status="under_review"
    )
    with pytest.raises(HTTPException) as exc_info:
        add_episode(ep_req_bad, amaka_auth)

    assert exc_info.value.status_code == 403
    assert "Tenant boundary violation" in str(exc_info.value.detail)
    assert "creator_amaka" in str(exc_info.value.detail)

def test_milestone_6c_no_title_heuristic_in_database_series_read():
    """
    Proves that even when a series dict has no creator_id populated (like raw PostgreSQL rows),
    it resolves to the canonical owner from digital_ips and NEVER infers based on title text.
    """
    # Create raw series dictionary simulating Supabase PostgreSQL row (no creator_id column)
    # Give it a title with "queen" or "blood", but link its ip_id to an IP owned by creator_amaka
    amaka_ip_id = to_uuid("ip_ceo_wife") # Seed IP owned by creator_amaka
    raw_series = {
        "id": str(uuid.uuid4()),
        "ip_id": amaka_ip_id,
        "title": "Queen of Blood: An Amaka Production", # Contains both "queen" and "blood"!
        "genre": "Drama",
        "season_number": 1
    }

    resolved_owner = series_repository.resolve_series_creator_id(raw_series)
    # If the legacy title heuristic was used, it would wrongly guess "creator_zola"
    # Because canonical resolution is used, it resolves to "creator_amaka" via digital_ips.master_owner_id
    assert resolved_owner == "creator_amaka", (
        f"Title heuristic failure: Series with 'queen'/'blood' in title but owned by Amaka IP "
        f"must resolve to 'creator_amaka', got '{resolved_owner}'"
    )
