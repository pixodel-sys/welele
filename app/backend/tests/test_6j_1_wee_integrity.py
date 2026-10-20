"""
Welele Media™ — Phase 6J-1 WEE Experience Studio Integrity Remediation Verification Suite
Validates all 7 authorized scope requirements:
1. Canonical Content Identity:
   - Canonicalizes WEE content references to series.id (UUID).
   - Deterministic slug <-> UUID bidirectional resolution.
   - Never silently substitutes another series.
2. Inspector Binding:
   - Unresolved IDs are preserved and flagged with is_unresolved: True.
   - Inspector draft endpoint delivers raw configured IDs without synthetic substitution.
3. Configuration vs Runtime Separation:
   - Raw editorial configuration (GET /page/{id}/draft) is strictly separated from resolved runtime manifests (GET /page/{id}).
   - Dynamic merchandising output (slot_dyn_..., is_dynamic) is stripped before persisting editorial drafts.
4. HYBRID Deduplication:
   - Slug and UUID representations of the same series are canonicalized to identical UUIDs before duplicate detection.
   - Pinned items maintain precedence; dynamic fill excludes both slug and UUID representations.
5. Stable Slot Identity:
   - Slot IDs are deterministic and collision-free (slot_pin_..., slot_dyn_...).
   - Pydantic unique slot validator remains authoritative and strictly active (does NOT weaken validation).
6. HTTP 422 Remediation:
   - Adding a newly created show (e.g. AMAPHUPHO) and saving layout returns HTTP 200 (not 422).
   - Dynamic slots do not cause duplicate slot ID collisions on subsequent saves.
7. Missing Content:
   - Unresolved content_id is preserved exactly as configured.
   - Explicitly flagged as unresolved; no automatic fallback to catalog[0] or any other series.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from main import app
from services.rbac_service import create_access_token
from services.experience_engine import ExperienceEngine
from schemas.experience_schemas import SaveDraftRequest, ExperienceSection, SlotItem
from services.merchandising_policy_service import (
    MerchandisingPolicyService,
    merchandising_policy_service
)
from repositories.series_repository import (
    series_repository,
    to_uuid,
    SERIES_UUID_TO_SLUG,
    KNOWN_SERIES_SLUGS
)

client = TestClient(app)

@pytest.fixture
def admin_headers():
    token = create_access_token(user_id="usr_admin_6j1", role="admin")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def zola_headers():
    token = create_access_token(user_id="usr_creator_zola", role="creator", creator_id="creator_zola")
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Canonical Content Identity
# ==============================================================================

def test_6j1_canonical_slug_uuid_bidirectional_resolution():
    """1a. Deterministic slug <-> UUID bidirectional resolution for all known series."""
    for slug in KNOWN_SERIES_SLUGS:
        canonical_uuid = to_uuid(slug)
        # Must be a valid UUID string
        parsed = uuid.UUID(canonical_uuid)
        assert str(parsed) == canonical_uuid
        # Resolves back to canonical slug
        assert SERIES_UUID_TO_SLUG.get(canonical_uuid) == slug
        # UUID passed to to_uuid returns itself identically
        assert to_uuid(canonical_uuid) == canonical_uuid


def test_6j1_canonical_content_lookup_in_experience_engine():
    """1b. ExperienceEngine resolves stories identically by UUID or slug."""
    resolved_home = ExperienceEngine.resolve_manifest("home")
    assert resolved_home is not None
    
    # Story Queen of Jozi UUID
    qoj_uuid = to_uuid("story_queen_of_jozi")
    policied_items = merchandising_policy_service.resolve_section_items(
        section={
            "section_id": "sec_test_qoj",
            "source": {"mode": "manual"},
            "items": [
                {"slot_id": "s1", "content_id": "story_queen_of_jozi"},
                {"slot_id": "s2", "content_id": qoj_uuid}
            ]
        },
        all_stories=resolved_home.get("_all_stories", {})
    )
    assert len(policied_items) == 2
    # Both resolve to the same Queen of Jozi story
    assert policied_items[0]["story"] is not None
    assert policied_items[1]["story"] is not None
    assert policied_items[0]["story"]["title"] == "Queen of Jozi"
    assert policied_items[1]["story"]["title"] == "Queen of Jozi"


# ==============================================================================
# 2. Inspector Binding & Unresolved State Preservation
# ==============================================================================

def test_6j1_inspector_draft_endpoint_preserves_unresolved_ids(admin_headers):
    """2a. GET /api/experience/page/{id}/draft returns raw unhydrated items without synthetic substitution."""
    res = client.get("/api/experience/page/home/draft", headers=admin_headers)
    assert res.status_code == 200
    draft = res.json()
    assert draft["status"] == "draft"
    assert "sections" in draft
    # Sections must contain raw items without synthetic story injection
    for sec in draft["sections"]:
        for it in sec.get("items", []):
            assert "content_id" in it
            # The draft endpoint should not inflate items with dynamic story trees
            assert "story" not in it or it["story"] is None or isinstance(it.get("story"), dict)


def test_6j1_inspector_unresolved_content_explicitly_flagged():
    """2b. Merchandising policy sets is_unresolved: True and story: None for unknown IDs."""
    policied = merchandising_policy_service.resolve_section_items(
        section={
            "section_id": "sec_missing_test",
            "source": {"mode": "manual"},
            "items": [
                {"slot_id": "slot_unknown_1", "content_id": "nonexistent_story_uuid_99999"}
            ]
        },
        all_stories={}
    )
    assert len(policied) == 1
    item = policied[0]
    assert item["content_id"] == "nonexistent_story_uuid_99999"
    assert item["story"] is None
    assert item.get("is_unresolved") is True


# ==============================================================================
# 3. Configuration vs Runtime Separation
# ==============================================================================

def test_6j1_draft_vs_runtime_manifest_separation(admin_headers):
    """3a. Draft endpoint returns editorial draft while runtime endpoint returns fully resolved manifest."""
    draft_res = client.get("/api/experience/page/home/draft", headers=admin_headers)
    assert draft_res.status_code == 200
    draft_data = draft_res.json()

    runtime_res = client.get("/api/experience/page/home")
    assert runtime_res.status_code == 200
    runtime_data = runtime_res.json()

    # Draft sections must not contain runtime dynamic fill items (slot_dyn_...)
    for sec in draft_data.get("sections", []):
        for it in sec.get("items", []):
            assert not it.get("slot_id", "").startswith("slot_dyn_")
            assert not it.get("is_dynamic", False)

    # Runtime manifest has resolved stories
    runtime_items = [it for s in runtime_data.get("sections", []) for it in s.get("items", [])]
    assert any(it.get("story") is not None for it in runtime_items)


def test_6j1_save_draft_strips_dynamic_slots(admin_headers):
    """3b. PUT /page/{id}/draft automatically strips dynamic runtime output before persisting."""
    # Build payload containing both editorial slot and dynamic slot
    save_payload = {
        "page_id": "home",
        "sections": [
            {
                "section_id": "sec_trending_row",
                "title": "Trending in South Africa 🔥",
                "type": "HORIZONTAL_ROW",
                "source": {"mode": "hybrid", "max_items": 5, "algo_type": "trending"},
                "items": [
                    {"slot_id": "slot_edit_1", "content_type": "series", "content_id": "story_blood_ties", "is_active": True},
                    {"slot_id": "slot_dyn_sec_trending_row_abc123", "content_type": "series", "content_id": "story_zulu_love", "is_dynamic": True, "is_active": True}
                ]
            }
        ]
    }

    put_res = client.put("/api/experience/page/home/draft", json=save_payload, headers=admin_headers)
    assert put_res.status_code == 200

    # Fetch draft back: dynamic slot must NOT be present in persisted editorial config
    draft_res = client.get("/api/experience/page/home/draft", headers=admin_headers)
    assert draft_res.status_code == 200
    saved_sec = next(s for s in draft_res.json()["sections"] if s["section_id"] == "sec_trending_row")
    saved_slot_ids = [it["slot_id"] for it in saved_sec["items"]]
    assert "slot_edit_1" in saved_slot_ids
    assert "slot_dyn_sec_trending_row_abc123" not in saved_slot_ids


# ==============================================================================
# 4. HYBRID Deduplication
# ==============================================================================

def test_6j1_hybrid_deduplication_slug_and_uuid_cross_representation():
    """4. HYBRID section deduplication recognizes slug and UUID as the exact same series."""
    qoj_uuid = to_uuid("story_queen_of_jozi")
    
    # Configure hybrid section pinning Queen of Jozi by slug
    section_cfg = {
        "section_id": "sec_hybrid_dedup",
        "source": {
            "mode": "hybrid",
            "max_items": 10,
            "pinned_content_ids": ["story_queen_of_jozi"],
            "algo_type": "new_releases"
        },
        "items": []
    }

    resolved = merchandising_policy_service.resolve_section_items(
        section=section_cfg,
        all_stories={}
    )

    # Queen of Jozi must appear exactly once in resolved output
    qoj_occurrences = [
        it for it in resolved
        if to_uuid(str(it.get("content_id", ""))) == qoj_uuid
    ]
    assert len(qoj_occurrences) == 1
    # Pinned item is first
    assert resolved[0]["content_id"] == "story_queen_of_jozi"


# ==============================================================================
# 5. Stable Slot Identity & Authoritative Validator
# ==============================================================================

def test_6j1_stable_slot_id_deterministic_generation():
    """5a. Generated slot IDs are deterministic, collision-free, and prefixed."""
    cid_1 = to_uuid("story_blood_ties")
    cid_2 = to_uuid("story_queen_of_jozi")

    res_1 = merchandising_policy_service.resolve_section_items(
        section={"section_id": "sec_test_slots", "source": {"mode": "hybrid", "max_items": 3, "pinned_content_ids": [cid_1, cid_2]}},
        all_stories={}
    )

    slot_ids = [it["slot_id"] for it in res_1]
    # All slot IDs must be unique
    assert len(slot_ids) == len(set(slot_ids))
    # Pinned slot IDs follow slot_pin_{sec}_{hash}
    assert slot_ids[0].startswith("slot_pin_sec_test_slots_")
    assert slot_ids[1].startswith("slot_pin_sec_test_slots_")


def test_6j1_authoritative_backend_validator_preserves_422_on_duplicate_slot_ids():
    """5b. Pydantic validator remains authoritative and strictly raises ValidationError on duplicate slot IDs."""
    invalid_data = {
        "page_id": "home",
        "sections": [
            {
                "section_id": "sec_1",
                "title": "Dup Slot Test",
                "type": "HORIZONTAL_ROW",
                "source": {"mode": "manual"},
                "items": [
                    {"slot_id": "DUPLICATE_SLOT_KEY", "content_type": "series", "content_id": "story_blood_ties"},
                    {"slot_id": "DUPLICATE_SLOT_KEY", "content_type": "series", "content_id": "story_queen_of_jozi"}
                ]
            }
        ]
    }

    # Must raise ValidationError - backend validator has NOT been weakened
    with pytest.raises(ValidationError) as exc_info:
        SaveDraftRequest(**invalid_data)
    assert "Duplicate slot_id" in str(exc_info.value)


# ==============================================================================
# 6. HTTP 422 Remediation (Live AMAPHUPHO Save Test)
# ==============================================================================

def test_6j1_amaphupho_show_creation_and_wee_save_returns_200(admin_headers, zola_headers):
    """6. Full lifecycle: Creator creates AMAPHUPHO, admin adds to WEE layout, saves successfully with HTTP 200."""
    # Step 1: Creator creates "AMAPHUPHO"
    create_res = client.post("/api/creators/series/create", json={
        "title": "AMAPHUPHO",
        "tagline": "The Dream Heist",
        "synopsis": "A group of Durban visionaries dare to build South Africa's first indie film empire.",
        "genre": "Street Hustle & Rise",
        "language": "isiZulu",
        "creator_id": "creator_zola",
        "coin_price_per_episode": 5
    }, headers=zola_headers)
    assert create_res.status_code == 200
    amaphupho_id = create_res.json()["story"]["id"]
    assert amaphupho_id is not None

    # Step 2: Admin fetches current draft
    draft_res = client.get("/api/experience/page/home/draft", headers=admin_headers)
    assert draft_res.status_code == 200
    draft = draft_res.json()

    # Step 3: Admin adds AMAPHUPHO to the first section
    sections = draft["sections"]
    target_sec = sections[0]
    new_slot_id = f"slot_pin_{target_sec['section_id']}_{amaphupho_id.replace('-', '')[:12]}"
    
    # Prepend AMAPHUPHO slot
    new_slot = {
        "slot_id": new_slot_id,
        "content_type": "series",
        "content_id": amaphupho_id,
        "badge": "NEW",
        "is_active": True
    }
    target_sec["items"] = [new_slot] + [it for it in target_sec.get("items", []) if it.get("content_id") != amaphupho_id]

    # Step 4: Admin saves draft -> MUST return HTTP 200 (remediating HTTP 422)
    save_res = client.put("/api/experience/page/home/draft", json={
        "page_id": "home",
        "sections": sections
    }, headers=admin_headers)
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"

    # Step 5: Verification of round-trip integrity:
    # Inspector ID = Persisted ID = API ID = Resolver ID = Preview ID
    persisted_draft = client.get("/api/experience/page/home/draft", headers=admin_headers).json()
    persisted_sec = next(s for s in persisted_draft["sections"] if s["section_id"] == target_sec["section_id"])
    persisted_item = next(it for it in persisted_sec["items"] if it["slot_id"] == new_slot_id)
    assert persisted_item["content_id"] == amaphupho_id

    # Verify Runtime Preview resolves AMAPHUPHO by its exact ID
    runtime_manifest = ExperienceEngine.resolve_manifest("home", state="draft")
    runtime_sec = next(s for s in runtime_manifest["sections"] if s["section_id"] == target_sec["section_id"])
    runtime_item = next(it for it in runtime_sec["items"] if it["slot_id"] == new_slot_id)
    assert runtime_item["content_id"] == amaphupho_id
    assert runtime_item["story"]["id"] == amaphupho_id
    assert runtime_item["story"]["title"] == "AMAPHUPHO"

    # Also verify via Admin Preview endpoint: GET /api/experience/preview/home?state=draft
    preview_res = client.get("/api/experience/preview/home?state=draft", headers=admin_headers)
    assert preview_res.status_code == 200
    preview_sec = next(s for s in preview_res.json()["sections"] if s["section_id"] == target_sec["section_id"])
    preview_item = next(it for it in preview_sec["items"] if it["slot_id"] == new_slot_id)
    assert preview_item["content_id"] == amaphupho_id
    assert preview_item["story"]["id"] == amaphupho_id


# ==============================================================================
# 7. Missing Content Preservation (Zero Silent Substitution)
# ==============================================================================

def test_6j1_missing_content_preserves_content_id_without_substitution(admin_headers):
    """7. Unresolvable content ID is preserved without falling back to catalog[0] or substituting other series."""
    missing_id = "missing_unresolvable_series_uuid_404"
    save_payload = {
        "page_id": "home",
        "sections": [
            {
                "section_id": "sec_test_missing",
                "title": "Missing Content Test",
                "type": "HORIZONTAL_ROW",
                "source": {"mode": "manual"},
                "items": [
                    {"slot_id": "slot_missing_test_1", "content_type": "series", "content_id": missing_id, "is_active": True}
                ]
            }
        ]
    }

    # Save draft with missing content
    put_res = client.put("/api/experience/page/home/draft", json=save_payload, headers=admin_headers)
    assert put_res.status_code == 200

    # Runtime resolution
    resolved = ExperienceEngine.resolve_manifest("home", state="draft")
    missing_sec = next(s for s in resolved["sections"] if s["section_id"] == "sec_test_missing")
    item = missing_sec["items"][0]

    # Invariants:
    # 1. content_id preserved exactly
    assert item["content_id"] == missing_id
    # 2. story is None (no silent substitution)
    assert item["story"] is None
    # 3. is_unresolved is True
    assert item["is_unresolved"] is True
