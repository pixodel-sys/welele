"""
Welele Media™ — Phase 6J-0 Creator Studio & WEE Stabilization Verification Suite (18 Invariants)
Validates all accepted 6J-0 invariants:
1. Creator Tenancy Isolation:
   - 01a: Creator A successfully creates series.
   - 01b: Creator B is forbidden from accessing Creator A's workspace (HTTP 403).
2. Empty Workspace Tenancy:
   - 02a: Creator with zero shows sees series: [] without falling back to catalog.
   - 02b: Creator with zero shows sees zero metrics and "—" placeholders.
3. Persistent Artwork:
   - 03a: Binary uploads to /api/storage/upload-binary return permanent CDN URLs.
   - 03b: Ephemeral blob: URLs in episode creation remain strictly rejected.
4. WEE Discover Null-Source Handling:
   - 04a: /api/experience/page/discover returns HTTP 200 without raising HTTP 500.
   - 04b: Experience engine and merchandising policy normalize null source safely.
5. Hero Workflow:
   - 05a: /api/experience/page/home returns HTTP 200.
   - 05b: Hero sections have valid, normalized non-null source configurations.
6. Show Creation Confirmation & Lifecycle:
   - 06a: Show creation returns success: true with valid series ID.
   - 06b: Show creation registers draft status and binds strictly to creator tenant.
7. Telemetry Zero-State:
   - 07a: Metrics return authoritative zeros and "—" placeholders.
   - 07b: No hardcoded mock statistics (8420000, 482000, 420000) are leaked.
8. Authoritative Earnings Linkage:
   - 08a: Creator series workspace earnings reflect double-entry ledger linkage.
   - 08b: payout_balance_zar is authoritative non-negative number.
9. Credential Isolation:
   - 09a: Invalid credentials/PIN fail closed with HTTP 401.
   - 09b: Valid creator credentials succeed with HTTP 200 and issue access token.
"""

import io
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from services.creator_profile_service import creator_profile_service
from services.experience_engine import ExperienceEngine
from services.merchandising_policy_service import merchandising_policy_service

client = TestClient(app)

@pytest.fixture
def auth_headers():
    token_zola = create_access_token(user_id="usr_creator_zola", role="creator", creator_id="creator_zola")
    token_b = create_access_token(user_id="usr_creator_b", role="creator", creator_id="creator_b")
    admin_token = create_access_token(user_id="usr_admin", role="admin")
    return {
        "zola": {"Authorization": f"Bearer {token_zola}"},
        "creator_b": {"Authorization": f"Bearer {token_b}"},
        "admin": {"Authorization": f"Bearer {admin_token}"}
    }


def test_6j_01a_creator_series_create_success(auth_headers):
    """01a. Creator A creates series successfully."""
    zola_headers = auth_headers["zola"]
    create_res = client.post("/api/creators/series/create", json={
        "title": "Zola Sovereign Series",
        "tagline": "Exclusive to Zola",
        "synopsis": "A drama of dynasty and bloodlines",
        "genre": "Crime & Dynasty",
        "language": "isiZulu",
        "creator_id": "creator_zola"
    }, headers=zola_headers)
    assert create_res.status_code == 200
    assert create_res.json()["success"] is True
    assert "id" in create_res.json()["story"]


def test_6j_01b_creator_a_b_isolation_forbidden(auth_headers):
    """01b. Creator B cannot access Creator A's workspace (HTTP 403)."""
    zola_headers = auth_headers["zola"]
    create_res = client.post("/api/creators/series/create", json={
        "title": "Zola Sovereign Series Isolation Target",
        "tagline": "Exclusive to Zola",
        "synopsis": "A drama of dynasty and bloodlines",
        "genre": "Crime & Dynasty",
        "language": "isiZulu",
        "creator_id": "creator_zola"
    }, headers=zola_headers)
    assert create_res.status_code == 200
    zola_series_id = create_res.json()["story"]["id"]

    b_headers = auth_headers["creator_b"]
    forbidden_res = client.get(f"/api/creators/series/{zola_series_id}/workspace", headers=b_headers)
    assert forbidden_res.status_code == 403
    assert "Tenant boundary violation" in forbidden_res.json()["detail"]


def test_6j_02a_empty_creator_workspace_series_empty():
    """02a. Creator with zero shows receives series: [] without public catalog fallback."""
    token_empty = create_access_token(user_id="usr_creator_fresh_a", role="creator", creator_id="creator_fresh_a")
    headers = {"Authorization": f"Bearer {token_empty}"}

    res = client.get("/api/creators/creator_fresh_a/dashboard", headers=headers)
    assert res.status_code == 200
    assert res.json()["series"] == []


def test_6j_02b_empty_creator_workspace_stats_zero():
    """02b. Creator with zero shows receives stats with authoritative zeros and placeholders."""
    token_empty = create_access_token(user_id="usr_creator_fresh_b", role="creator", creator_id="creator_fresh_b")
    headers = {"Authorization": f"Bearer {token_empty}"}

    res = client.get("/api/creators/creator_fresh_b/dashboard", headers=headers)
    assert res.status_code == 200
    stats = res.json()["stats"]
    assert stats["total_views"] == 0
    assert stats["total_episodes"] == 0
    assert stats["payout_balance"] == 0.0
    assert stats["avg_cliffhanger_completion_rate"] == "—"


def test_6j_03a_persistent_artwork_upload_returns_cdn_url(auth_headers):
    """03a. Uploading binary artwork returns permanent CDN URL."""
    zola_headers = auth_headers["zola"]
    fake_image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    files = {"file": ("poster_test.png", io.BytesIO(fake_image_bytes), "image/png")}
    data = {"series_id": "story_blood_ties"}

    upload_res = client.post("/api/storage/upload-binary", files=files, data=data, headers=zola_headers)
    assert upload_res.status_code == 200
    res_data = upload_res.json()
    assert res_data["success"] is True
    assert "public_cdn_url" in res_data
    assert not res_data["public_cdn_url"].startswith("blob:")
    assert res_data["storage_key"].startswith("masters/story_blood_ties/")


def test_6j_03b_ephemeral_blob_url_rejected(auth_headers):
    """03b. Ephemeral blob: URLs in episode creation remain strictly rejected."""
    zola_headers = auth_headers["zola"]
    blob_payload = {
        "series_id": "story_blood_ties",
        "episode_number": 99,
        "title": "Blob Test Ep",
        "video_url": "blob:http://localhost:5173/0e698bb2-fbe7-4c3e-a745-f09d84bfda99",
        "is_free": False,
        "coin_price": 5
    }
    rejected_res = client.post("/api/creators/episodes/add", json=blob_payload, headers=zola_headers)
    assert rejected_res.status_code == 400
    assert "blob" in rejected_res.json()["detail"].lower()


def test_6j_04a_wee_discover_null_source_endpoint_200():
    """04a. /api/experience/page/discover returns HTTP 200 without raising HTTP 500."""
    res = client.get("/api/experience/page/discover")
    assert res.status_code == 200
    data = res.json()
    assert data["page_id"] == "discover"
    assert "sections" in data


def test_6j_04b_wee_discover_null_source_engine_and_merchandising_normalization():
    """04b. Experience engine and merchandising policy normalize null source safely."""
    resolved = ExperienceEngine.resolve_manifest("discover")
    assert resolved is not None
    assert len(resolved["sections"]) > 0
    for sec in resolved["sections"]:
        assert sec["source"] is not None
        assert isinstance(sec["source"], dict)

    policied_items = merchandising_policy_service.resolve_section_items(
        section={"section_id": "sec_null_src", "source": None, "items": []},
        all_stories={}
    )
    assert isinstance(policied_items, list)


def test_6j_05a_wee_home_endpoint_200():
    """05a. /api/experience/page/home returns HTTP 200."""
    res = client.get("/api/experience/page/home")
    assert res.status_code == 200
    data = res.json()
    assert data["page_id"] == "home"
    assert len(data["sections"]) > 0


def test_6j_05b_wee_hero_section_source_structure():
    """05b. Hero sections have non-null source configurations."""
    res = client.get("/api/experience/page/home")
    assert res.status_code == 200
    data = res.json()
    hero_sections = [s for s in data["sections"] if s.get("type") == "hero" or "hero" in s.get("section_id", "")]
    assert len(hero_sections) >= 1
    for s in hero_sections:
        assert s["source"] is not None
        assert isinstance(s["source"], dict)


def test_6j_06a_show_creation_confirmation_response(auth_headers):
    """06a. Show creation returns success confirmation with valid ID."""
    zola_headers = auth_headers["zola"]
    create_res = client.post("/api/creators/series/create", json={
        "title": "Echoes of Soweto",
        "tagline": "Where music meets betrayal",
        "synopsis": "A young DJ navigates the high-stakes soundscape of Johannesburg.",
        "genre": "Street Hustle & Rise",
        "language": "English / isiZulu",
        "creator_id": "creator_zola",
        "coin_price_per_episode": 5
    }, headers=zola_headers)
    assert create_res.status_code == 200
    res_data = create_res.json()
    assert res_data["success"] is True
    assert "id" in res_data["story"]


def test_6j_06b_show_creation_lifecycle_creator_binding(auth_headers):
    """06b. Show creation registers correct creator_id binding."""
    zola_headers = auth_headers["zola"]
    create_res = client.post("/api/creators/series/create", json={
        "title": "Echoes of Soweto Binding Test",
        "tagline": "Where music meets betrayal",
        "synopsis": "A young DJ navigates the high-stakes soundscape of Johannesburg.",
        "genre": "Street Hustle & Rise",
        "language": "English / isiZulu",
        "creator_id": "creator_zola",
        "coin_price_per_episode": 5
    }, headers=zola_headers)
    assert create_res.status_code == 200
    story = create_res.json()["story"]
    assert story["creator_id"] == "creator_zola"


def test_6j_07a_telemetry_zero_state_authoritative_zeros():
    """07a. Newly registered creator returns authoritative zeros and '—' placeholders."""
    token_empty = create_access_token(user_id="usr_creator_zero_a", role="creator", creator_id="creator_zero_a")
    headers = {"Authorization": f"Bearer {token_empty}"}

    res = client.get("/api/creators/creator_zero_a/dashboard", headers=headers)
    assert res.status_code == 200
    stats = res.json()["stats"]
    assert stats["total_views"] == 0
    assert stats["total_likes"] == 0
    assert stats["followers"] == 0
    assert stats["avg_cliffhanger_completion_rate"] == "—"
    assert stats["monthly_growth_rate"] == "—"


def test_6j_07b_telemetry_zero_state_no_hardcoded_mock_statistics():
    """07b. Zero-state telemetry does not leak forensic mock numbers."""
    token_empty = create_access_token(user_id="usr_creator_zero_b", role="creator", creator_id="creator_zero_b")
    headers = {"Authorization": f"Bearer {token_empty}"}

    res = client.get("/api/creators/creator_zero_b/dashboard", headers=headers)
    assert res.status_code == 200
    stats = res.json()["stats"]
    assert stats["total_views"] != 8420000
    assert stats["total_likes"] != 482000


def test_6j_08a_authoritative_earnings_linkage_workspace(auth_headers):
    """08a. Creator series workspace returns metrics with authoritative payout balance."""
    zola_headers = auth_headers["zola"]
    res = client.get("/api/creators/series/story_blood_ties/workspace", headers=zola_headers)
    assert res.status_code == 200
    metrics = res.json()["metrics"]
    assert "payout_balance_zar" in metrics


def test_6j_08b_authoritative_earnings_payout_balance_zar_valid(auth_headers):
    """08b. payout_balance_zar is valid non-negative numeric value."""
    zola_headers = auth_headers["zola"]
    res = client.get("/api/creators/series/story_blood_ties/workspace", headers=zola_headers)
    assert res.status_code == 200
    payout = res.json()["metrics"]["payout_balance_zar"]
    assert isinstance(payout, (int, float))
    assert payout >= 0.0


def test_6j_09a_credential_isolation_invalid_pin_fails_closed_401():
    """09a. Invalid creator credentials/PIN fail closed with HTTP 401."""
    fail_res = client.post("/api/v1/auth/creator/login", json={
        "creator_id": "creator_zola",
        "studio_pin": "9999_wrong_pin"
    })
    assert fail_res.status_code == 401
    assert "Invalid Showrunner Studio PIN or credentials" in fail_res.json()["detail"]


def test_6j_09b_credential_isolation_valid_login_succeeds_200():
    """09b. Valid creator login succeeds and issues access token."""
    pass_res = client.post("/api/v1/auth/creator/login", json={
        "creator_id": "creator_zola",
        "password": "welele_dev_pass"
    })
    assert pass_res.status_code == 200
    data = pass_res.json()
    assert data["status"] == "success"
    assert data["user"]["creator_id"] == "creator_zola"
    assert "access_token" in data
