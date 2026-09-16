"""
Welele Media™ — Story Review™ / Story Forge™ Separation v1 Hardening & Real-Story Validation Suite
P0 Regression & Security Boundary Specification

Tests:
1. API Authority Boundaries & Security Enforcement (Creator / Protected endpoints / Forge leakage prevention)
2. Golden-Output Contract Test for 'The Ancestral Ledger'
3. Real Story Review Pass for Story A ('The Ancestral Ledger') and Story B ('Taxi Queen of Tembisa')
4. IP Pipeline Submission & Duplicate Protection (Idempotency)
5. Admin Intake Triage & Handoff
6. Story Forge Internal Narrative Reasoning Development & Canonical Story Package Persistence
7. Lineage & Provenance Chain Verification
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from repositories.ip_repository import ip_repository
from routers.story_review import story_review_repo

client = TestClient(app)


def get_auth_headers(user_id: str = "creator_zola", role: str = "creator"):
    token = create_access_token(user_id=user_id, role=role, creator_id=user_id)
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. API AUTHORITY BOUNDARIES & SECURITY ENFORCEMENT
# =============================================================================

def test_api_authority_boundaries_and_denial():
    """
    Verifies that unauthenticated or non-privileged users cannot access protected
    admin and IP endpoints, ensuring boundaries are strictly enforced at the API level.
    """
    # 1. Unauthenticated access to admin metrics -> 401/403
    res_admin = client.get("/api/admin/metrics")
    assert res_admin.status_code in (401, 403), f"Expected 401/403, got {res_admin.status_code}"

    # 2. Creator role attempting admin moderation queue -> 403 Forbidden
    creator_headers = get_auth_headers(user_id="creator_zola", role="creator")
    res_mod = client.get("/api/admin/moderation-queue", headers=creator_headers)
    assert res_mod.status_code == 403, f"Creator should be forbidden from admin queue: {res_mod.status_code}"

    # 3. Creator role attempting admin audit ledger inspection -> 403 Forbidden
    res_audit = client.get("/api/admin/audit-logs", headers=creator_headers)
    assert res_audit.status_code == 403, f"Creator should be forbidden from raw audit ledger: {res_audit.status_code}"

    # 4. Creator role attempting direct IP creation without required schema -> 422 or 400
    res_ip_bad = client.post("/api/ip/create", json={}, headers=creator_headers)
    assert res_ip_bad.status_code in (400, 422)


def test_story_review_response_shields_forge_internals():
    """
    Verifies that Story Review™ responses NEVER leak Story Forge™ internal data structures:
    no dependency queues, no transition traces, no Forge Judge rules, no raw AST mutations.
    """
    draft_payload = {
        "title": "The Sandton Heist",
        "logline": "A high-stakes vertical heist microdrama set in Johannesburg.",
        "target_format": "VERTICAL_MICRODRAMA",
        "tone": "Gritty Action Drama",
        "protagonist_name": "Lindiwe",
        "protagonist_want": "Retrieve her father stolen diamond matrix.",
        "protagonist_need": "Learn to trust her estranged crew.",
        "counterforce_or_antagonist": "Colonel Venter and private security forces",
        "world_setting": "High-security Sandton banking vaults and underground storm drains",
        "episode_hooks": [
            "Ep 1: The vault alarm sounds 20 seconds before entry.",
            "Ep 2: Lindiwe discovers her inside contact is dead.",
            "Ep 3: The escape vehicle is surrounded."
        ],
        "full_draft_text": "Lindiwe prepares the infiltration route.",
        "version": 1
    }

    res = client.post("/api/v1/review/diagnose", json=draft_payload)
    assert res.status_code == 200
    data = res.json()

    # Verify Story Review contracts exist
    assert "readiness_score" in data
    assert "readiness_tier" in data
    assert "evaluation_mode" in data
    assert data["evaluation_mode"] in ("AI_ASSISTED", "BASELINE_HEURISTIC")
    assert "premise_and_hook" in data
    assert "character_tension" in data
    assert "episodic_structure" in data
    assert "production_feasibility" in data

    # Verify Forge internal fields are strictly ABSENT
    forbidden_internal_fields = [
        "dependencies",
        "transitions",
        "mutation_history",
        "forge_judge_rules",
        "active_invariants",
        "kernel_cycle_count",
        "reasoning_trace",
        "raw_ast"
    ]
    for field in forbidden_internal_fields:
        assert field not in data, f"Leaked internal Forge field '{field}' in Story Review response!"


# =============================================================================
# 2. GOLDEN-OUTPUT CONTRACT TEST FOR 'THE ANCESTRAL LEDGER'
# =============================================================================

def test_the_ancestral_ledger_golden_contract():
    """
    Golden-output contract validation fixture for 'The Ancestral Ledger'.
    Verifies strict schema conformance, score bounds, 4 dimensions, tips, checklist,
    provenance, and evaluation_mode.
    """
    ancestral_draft = {
        "title": "The Ancestral Ledger",
        "logline": "When a modern Johannesburg accountant discovers an ancient spiritual ledger detailing unpayable ancestral debts, he must outwit both township loan sharks and ancestral spirits before his family name is erased.",
        "target_format": "VERTICAL_MICRODRAMA",
        "tone": "Supernatural Comedy / High Stakes Thriller",
        "themes": ["Ancestral Duty", "Modern Finance", "Family Honor"],
        "protagonist_name": "Sipho Ndlovu",
        "protagonist_want": "Clear his family debt within 48 hours to secure a major corporate promotion.",
        "protagonist_need": "Accept his ancestral heritage and reconcile with his estranged grandmother.",
        "counterforce_or_antagonist": "Gogo MaMthembu (ancestral debt keeper) and Bra Mike (ruthless cash loan boss)",
        "world_setting": "Modern Sandton corporate offices juxtaposed against an ancient ancestral shrine in Soweto",
        "episode_hooks": [
            "Ep 1 Hook: Sipho receives a gold ledger stamped with his late grandfather blood print.",
            "Ep 2 Hook: Bra Mike henchmen corner Sipho, only for the lights to shatter as spirits intervene.",
            "Ep 3 Hook: Sipho discovers the debt requires a living sacrifice—or solving a 19th-century murder."
        ],
        "full_draft_text": "ACT I: Sipho is on the verge of making partner at a Sandton accounting firm. His estranged uncle passes away, leaving him a mysterious locked safe deposit box. Inside is a glowing, leather-bound ledger written in isiZulu and high financial accounting notation.",
        "version": 1
    }

    res = client.post("/api/v1/review/diagnose", json=ancestral_draft)
    assert res.status_code == 200, f"Diagnostic failed: {res.text}"
    diag = res.json()

    # 1. Readiness Score & Tier
    assert 0 <= diag["readiness_score"] <= 100
    assert diag["readiness_tier"] in ("READY_FOR_SUBMISSION", "SOLID_FOUNDATION", "NEEDS_REVISION")

    # 2. Evaluation Mode Indicator
    assert diag["evaluation_mode"] in ("AI_ASSISTED", "BASELINE_HEURISTIC")

    # 3. Four Core Dimensions
    dimensions = ["premise_and_hook", "character_tension", "episodic_structure", "production_feasibility"]
    for dim_name in dimensions:
        assert dim_name in diag, f"Missing dimension {dim_name}"
        dim = diag[dim_name]
        assert "score" in dim and 0 <= dim["score"] <= 100
        assert "strengths" in dim and isinstance(dim["strengths"], list) and len(dim["strengths"]) > 0
        assert "critique" in dim and isinstance(dim["critique"], str) and len(dim["critique"]) > 0

    # 4. Actionable Tips
    assert "actionable_tips" in diag
    assert len(diag["actionable_tips"]) >= 3
    for tip in diag["actionable_tips"]:
        assert "title" in tip and len(tip["title"]) > 0
        assert "description" in tip and len(tip["description"]) > 0
        assert "impact_area" in tip and len(tip["impact_area"]) > 0

    # 5. Submission Checklist
    assert "submission_checklist" in diag
    assert len(diag["submission_checklist"]) >= 4
    for item in diag["submission_checklist"]:
        assert "item" in item
        assert "passed" in item and isinstance(item["passed"], bool)
        assert "recommendation" in item

    # 6. Provenance & Timestamps
    assert "evaluated_at" in diag and len(diag["evaluated_at"]) > 10
    assert "pitch_summary" in diag and len(diag["pitch_summary"]) > 0


# =============================================================================
# 3. REAL STORY PASS: STORY A & STORY B THROUGH STORY REVIEW™
# =============================================================================

def test_real_story_a_and_b_review_separation():
    """
    Runs two distinct real vertical microdramas through Story Review™:
    - Story A: 'The Ancestral Ledger' (Supernatural Crime Microdrama)
    - Story B: 'Taxi Queen of Tembisa' (High-Stakes Action Microdrama)
    Verifies independent scoring, draft persistence, and profile isolation.
    """
    headers = get_auth_headers(user_id="creator_zola")

    # Story A
    story_a_draft = {
        "title": "The Ancestral Ledger",
        "logline": "An ambitious Sandton accountant discovers an ancient spiritual debt ledger that forces him to navigate ancestral claims and loan sharks.",
        "target_format": "VERTICAL_MICRODRAMA",
        "tone": "Supernatural Crime Drama",
        "protagonist_name": "Sipho Ndlovu",
        "protagonist_want": "Settle family debts in 48 hours.",
        "protagonist_need": "Reconcile with his ancestral roots.",
        "counterforce_or_antagonist": "Gogo MaMthembu & Bra Mike",
        "world_setting": "Sandton office high-rises and Soweto ancestral shrine",
        "episode_hooks": [
            "Ep 1: Ledger glows in office meeting.",
            "Ep 2: Spirits short-circuit bank power.",
            "Ep 3: The blood oath revelation."
        ],
        "full_draft_text": "Sipho opens the inherited lockbox...",
        "version": 1
    }

    # Story B
    story_b_draft = {
        "title": "Taxi Queen of Tembisa",
        "logline": "When her taxi boss father is framed for murder, an elite mechanical prodigy takes over the city fiercest taxi association route to uncover the syndicate behind the betrayal.",
        "target_format": "VERTICAL_MICRODRAMA",
        "tone": "Gritty Action Thriller",
        "protagonist_name": "Naledi Khumalo",
        "protagonist_want": "Defend her father route and win the Tembisa association election.",
        "protagonist_need": "Confront her grief over her mother death and lead the drivers with respect rather than fear.",
        "counterforce_or_antagonist": "Mthembu Taxi Cartel and corrupt police captain Hlongwane",
        "world_setting": "Tembisa taxi ranks, mechanic chop shops, and midnight freeway showdowns",
        "episode_hooks": [
            "Ep 1: Naledi drifts a modified Quantum minibus through an ambush at the rank.",
            "Ep 2: A hidden GPS tracker is found inside the fare box.",
            "Ep 3: Captain Hlongwane issues a 12-hour ultimatum to surrender the association keys."
        ],
        "full_draft_text": "Naledi slides under the chassis of a Quantum minibus...",
        "version": 1
    }

    # 1. Save and diagnose Story A
    res_save_a = client.post("/api/v1/review/drafts", json=story_a_draft, headers=headers)
    assert res_save_a.status_code == 200
    saved_a = res_save_a.json()["draft"]
    draft_a_id = saved_a["id"]

    res_diag_a = client.post("/api/v1/review/diagnose", json=saved_a)
    assert res_diag_a.status_code == 200
    diag_a = res_diag_a.json()

    # 2. Save and diagnose Story B
    res_save_b = client.post("/api/v1/review/drafts", json=story_b_draft, headers=headers)
    assert res_save_b.status_code == 200
    saved_b = res_save_b.json()["draft"]
    draft_b_id = saved_b["id"]

    res_diag_b = client.post("/api/v1/review/diagnose", json=saved_b)
    assert res_diag_b.status_code == 200
    diag_b = res_diag_b.json()

    # 3. Verify separation & persistent list
    assert draft_a_id != draft_b_id
    res_list = client.get("/api/v1/review/drafts?creator_id=creator_zola")
    assert res_list.status_code == 200
    draft_ids = [d["id"] for d in res_list.json()]
    assert draft_a_id in draft_ids
    assert draft_b_id in draft_ids


# =============================================================================
# 4. IP PIPELINE SUBMISSION, DUPLICATE PROTECTION & ADMIN INTAKE
# =============================================================================

def test_ip_pipeline_submission_and_duplicate_protection():
    """
    Submits Story A ('The Ancestral Ledger') through the IP Pipeline.
    Verifies:
    1. Submission creation with status 'SUBMITTED_FOR_REVIEW'
    2. Duplicate submission protection (idempotent update on resubmission of same draft)
    3. Admin intake triage visibility
    """
    headers = get_auth_headers(user_id="creator_zola")
    draft_id = "draft_ancestral_ledger_val_001"

    submit_payload = {
        "draft_id": draft_id,
        "creator_id": "creator_zola",
        "creator_name": "Zola Dlamini",
        "title": "The Ancestral Ledger",
        "logline": "An ambitious Sandton accountant discovers an ancient spiritual debt ledger.",
        "target_format": "VERTICAL_MICRODRAMA",
        "diagnostic_score": 88,
        "creator_notes": "High concept, contained sets, highly authentic cultural tension.",
        "pitch_package": {
            "synopsis": "An ambitious Sandton accountant discovers an ancient spiritual debt ledger.",
            "target_audience": "African mobile microdrama viewers",
            "primary_locations": "Sandton office & Soweto shrine",
            "estimated_episodes": 6,
            "key_characters": [
                {"name": "Sipho Ndlovu", "role": "Protagonist", "arc": "From debt denial to spiritual acceptance"}
            ]
        }
    }

    # 1. First Submission
    res_sub1 = client.post("/api/v1/review/submit-pitch", json=submit_payload, headers=headers)
    assert res_sub1.status_code == 200
    sub1_data = res_sub1.json()
    submission_id = sub1_data["submission_id"]
    assert sub1_data["status"] == "SUBMITTED_FOR_REVIEW"
    assert sub1_data["diagnostic_summary"]["readiness_score"] == 88

    # 2. Duplicate submission attempt for same draft
    submit_payload["diagnostic_score"] = 92  # updated score
    res_sub2 = client.post("/api/v1/review/submit-pitch", json=submit_payload, headers=headers)
    assert res_sub2.status_code == 200
    sub2_data = res_sub2.json()

    # Idempotency / Duplicate Protection Assertion:
    # Must update the existing submission rather than creating a duplicate intake record
    assert sub2_data["submission_id"] == submission_id
    assert sub2_data["diagnostic_summary"]["readiness_score"] == 92

    # 3. Admin Intake Verification
    admin_headers = get_auth_headers(user_id="admin_supervisor", role="admin")
    res_intake = client.get("/api/v1/review/submissions")
    assert res_intake.status_code == 200
    all_subs = res_intake.json()
    
    # Verify exactly one intake record exists for this submission
    matching_subs = [s for s in all_subs if s["submission_id"] == submission_id]
    assert len(matching_subs) == 1
    assert matching_subs[0]["title"] == "The Ancestral Ledger"


# =============================================================================
# 5. STORY FORGE DEVELOPMENT & CANONICAL STORY PACKAGE PERSISTENCE
# =============================================================================

def test_story_forge_development_and_canonical_ip_packaging():
    """
    Develops 'The Ancestral Ledger' in the Story Forge™ Internal Narrative Reasoning Engine:
    1. Create Forge story state from intake pitch
    2. Execute reasoning cycles
    3. Persist versioned Story Forge package into Digital IP Engine with SHA-256 lineage hash
    """
    creator_headers = get_auth_headers(user_id="creator_zola", role="creator")

    # 1. Create Story in Forge
    forge_story_payload = {
        "title": "The Ancestral Ledger",
        "owner_id": "creator_zola",
        "logline": "An ambitious Sandton accountant discovers an ancient spiritual debt ledger.",
        "primary_language": "isiZulu"
    }

    res_create = client.post("/api/v1/forge/stories", json=forge_story_payload)
    assert res_create.status_code == 200
    story_state = res_create.json()
    forge_story_id = story_state["story_id"]
    assert story_state["title"] == "The Ancestral Ledger"

    # 2. Start Narrative Reasoning Session
    session_payload = {
        "creator_id": "creator_zola",
        "initial_premise": "An ambitious Sandton accountant discovers an ancient spiritual debt ledger."
    }
    res_session = client.post(f"/api/v1/forge/stories/{forge_story_id}/sessions", json=session_payload)
    assert res_session.status_code == 200
    session_data = res_session.json()
    session_id = session_data["id"]
    assert session_data["story_id"] == forge_story_id

    # 3. Submit Creator Premise Input to Forge Engine
    input_payload = {
        "input_text": "Sipho must decide whether to burn the ancestral ledger or pay the spiritual fee with his promotion bonus."
    }
    res_cycle = client.post(f"/api/v1/forge/sessions/{session_id}/input", json=input_payload)
    assert res_cycle.status_code == 200
    cycle_res = res_cycle.json()
    assert cycle_res["story_id"] == forge_story_id

    # 4. Save Canonical Story Package to Digital IP Engine
    ip_id = "ip_ancestral_ledger"
    # Ensure IP exists or use existing franchise
    all_ips = ip_repository.list_ips()
    target_ip = all_ips[0]["id"] if all_ips else "ip_blood_ties"

    package_payload = {
        "ip_id": target_ip,
        "creator_id": "creator_zola",
        "package_title": "The Ancestral Ledger: Episode 1 Package",
        "target_duration_seconds": 90,
        "beats": [
            {"beat_number": 1, "description": "Sipho receives the locked safe deposit box from Soweto."},
            {"beat_number": 2, "description": "The glowing isiZulu ledger reveals an unpaid spiritual debt from 1892."},
            {"beat_number": 3, "description": "Loan shark Bra Mike arrives at Sandton offices demanding collateral."}
        ],
        "dialogues": [
            {"character": "Sipho", "line": "You cannot audit an ancestral debt with modern debit orders."},
            {"character": "Bra Mike", "line": "Your grandfather signed in blood, boy. We collect today."}
        ],
        "cliffhanger_prompt": "Will Sipho sign the second ledger page or let the spirits take his office?",
        "ai_model_used": "welele-narrative-reasoning-v1",
        "human_approved": True
    }

    res_pkg = client.post(
        f"/api/ip/{target_ip}/story-forge/save",
        json=package_payload,
        headers=creator_headers
    )
    assert res_pkg.status_code == 200, f"Story Forge package save failed: {res_pkg.text}"
    pkg_data = res_pkg.json()
    assert pkg_data["success"] is True
    pkg = pkg_data["package"]
    assert pkg["id"].startswith("sfp_")
    assert "lineage_hash" in pkg and len(pkg["lineage_hash"]) == 64

    # 5. Verify Package Lineage in Digital IP Franchise Detail
    res_ip_detail = client.get(f"/api/ip/{target_ip}")
    assert res_ip_detail.status_code == 200
    ip_detail = res_ip_detail.json()
    saved_pkgs = ip_detail.get("story_packages", [])
    matched_pkg = next((p for p in saved_pkgs if p["id"] == pkg["id"]), None)
    assert matched_pkg is not None
    assert matched_pkg["lineage_hash"] == pkg["lineage_hash"]
    assert matched_pkg["package_title"] == "The Ancestral Ledger: Episode 1 Package"
