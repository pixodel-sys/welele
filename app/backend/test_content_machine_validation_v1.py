"""
Welele Media™ — Content Machine Validation V1 Suite
Golden Specimen: The Ancestral Ledger

Validates the full connected content pipeline:
Story Review™ -> Creator Draft -> Diagnostic -> Submission -> IP Pipeline -> Admin Intake ->
Story Forge™ -> Canonical Story Package -> Production -> Episode 1 -> Media Asset -> Viewer -> Telemetry -> Analytics/Intelligence
"""

import os
import pytest
from fastapi.testclient import TestClient
from main import app
from services.rbac_service import create_access_token
from services.storage_service import storage_service
from services.intelligence_service import intelligence_service
from repositories.ip_repository import ip_repository
from repositories.series_repository import series_repository
from repositories.event_repository import event_repository
from routers.story_review import story_review_repo
from schemas.ip_schemas import CreateIPRequest, RightsSplitSchema

client = TestClient(app)


def get_auth_headers(user_id: str = "creator_zola", role: str = "creator"):
    token = create_access_token(user_id=user_id, role=role, creator_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_welele_content_machine_pipeline_the_ancestral_ledger():
    creator_headers = get_auth_headers("creator_zola", "creator")
    admin_headers = get_auth_headers("admin_supervisor", "admin")

    # =========================================================================
    # STEP 1: Story Review™ Creator Draft & Diagnostic
    # =========================================================================
    draft_id = "draft_ancestral_ledger_machine_v1"
    ancestral_draft = {
        "draft_id": draft_id,
        "creator_id": "creator_zola",
        "creator_name": "Zola Dlamini",
        "title": "The Ancestral Ledger",
        "logline": "When a modern Johannesburg accountant discovers an ancient spiritual ledger detailing unpayable ancestral debts, he must outwit both township loan sharks and ancestral spirits before his family name is erased.",
        "target_format": "VERTICAL_MICRODRAMA",
        "tone": "Supernatural Comedy / High Stakes Thriller",
        "themes": ["Ancestral Duty", "Modern Finance", "Family Honor"],
        "protagonist_name": "Sipho Ndlovu",
        "protagonist_want": "Clear his family debt within 48 hours to secure a corporate promotion.",
        "protagonist_need": "Accept his ancestral heritage and reconcile with his estranged family.",
        "counterforce_or_antagonist": "Gogo MaMthembu and Bra Mike",
        "world_setting": "Modern Sandton corporate offices juxtaposed against an ancient ancestral shrine in Soweto",
        "episode_hooks": [
            "Ep 1 Hook: Sipho receives a gold ledger stamped with his late grandfather blood print.",
            "Ep 2 Hook: Bra Mike henchmen corner Sipho, only for the lights to shatter as spirits intervene.",
            "Ep 3 Hook: Sipho discovers the debt requires solving a 19th-century murder."
        ],
        "full_draft_text": "ACT I: Sipho is on the verge of making partner at a Sandton accounting firm. His estranged uncle passes away, leaving him a mysterious locked safe deposit box. Inside is a glowing, leather-bound ledger written in isiZulu and high financial accounting notation.",
        "version": 1
    }

    res_save_draft = client.post("/api/v1/review/drafts", json=ancestral_draft, headers=creator_headers)
    assert res_save_draft.status_code == 200
    saved_draft = res_save_draft.json()["draft"]
    assert saved_draft["title"] == "The Ancestral Ledger"

    res_diag = client.post("/api/v1/review/diagnose", json=saved_draft)
    assert res_diag.status_code == 200
    diag_data = res_diag.json()
    assert 0 <= diag_data["readiness_score"] <= 100
    assert diag_data["readiness_tier"] in ("READY_FOR_SUBMISSION", "SOLID_FOUNDATION", "NEEDS_REVISION")
    assert diag_data["evaluation_mode"] in ("AI_ASSISTED", "BASELINE_HEURISTIC")
    readiness_score = diag_data["readiness_score"]

    # =========================================================================
    # STEP 2: Submission to IP Pipeline ("Submit for Greenlight")
    # =========================================================================
    submit_payload = {
        "draft_id": draft_id,
        "creator_id": "creator_zola",
        "creator_name": "Zola Dlamini",
        "title": "The Ancestral Ledger",
        "logline": ancestral_draft["logline"],
        "target_format": "VERTICAL_MICRODRAMA",
        "diagnostic_score": readiness_score,
        "creator_notes": "Groundbreaking African supernatural financial thriller for mobile 9:16 audiences.",
        "pitch_package": {
            "synopsis": ancestral_draft["logline"],
            "target_audience": "Mobile-first vertical microdrama viewers",
            "primary_locations": ancestral_draft["world_setting"],
            "estimated_episodes": 6,
            "key_characters": [
                {"name": "Sipho Ndlovu", "role": "Protagonist", "arc": "From Sandton corporate denial to ancestral defender"},
                {"name": "Bra Mike", "role": "Antagonist", "arc": "Ruthless township loan shark enforcing blood debts"}
            ]
        }
    }

    res_sub = client.post("/api/v1/review/submit-pitch", json=submit_payload, headers=creator_headers)
    assert res_sub.status_code == 200
    sub_data = res_sub.json()
    submission_id = sub_data["submission_id"]
    assert sub_data["status"] == "SUBMITTED_FOR_REVIEW"

    # =========================================================================
    # STEP 3: Admin Intake & Editorial Triage
    # =========================================================================
    res_intake = client.get("/api/v1/review/submissions", headers=admin_headers)
    assert res_intake.status_code == 200
    intake_list = res_intake.json()
    matching_intake = next((s for s in intake_list if s["submission_id"] == submission_id), None)
    assert matching_intake is not None
    assert matching_intake["title"] == "The Ancestral Ledger"

    # =========================================================================
    # STEP 4: Story Forge™ Development & Narrative Reasoning
    # =========================================================================
    forge_story_payload = {
        "title": "The Ancestral Ledger",
        "owner_id": "creator_zola",
        "logline": ancestral_draft["logline"],
        "primary_language": "isiZulu"
    }
    res_forge_story = client.post("/api/v1/forge/stories", json=forge_story_payload)
    assert res_forge_story.status_code == 200
    forge_story = res_forge_story.json()
    forge_story_id = forge_story["story_id"]

    # Start Session
    session_payload = {
        "creator_id": "creator_zola",
        "initial_premise": ancestral_draft["logline"]
    }
    res_session = client.post(f"/api/v1/forge/stories/{forge_story_id}/sessions", json=session_payload)
    assert res_session.status_code == 200
    session_id = res_session.json()["id"]

    # Ingest creator decision
    res_input = client.post(
        f"/api/v1/forge/sessions/{session_id}/input",
        json={"input_text": "Sipho opens the 1892 codicil and discovers his family name is collateral for the Sandton mine shaft."}
    )
    assert res_input.status_code == 200

    # =========================================================================
    # STEP 5: Canonical Digital IP & Story Package Persistence
    # =========================================================================
    canonical_ip_id = "ip_ancestral_ledger_canonical"
    existing_ips = ip_repository.list_ips()
    ip_match = next((ip for ip in existing_ips if ip["id"] == canonical_ip_id), None)
    if not ip_match:
        from schemas.ip_schemas import StoryWorldSchema, CharacterBibleSchema, RightsSplitSchema
        ip_req = CreateIPRequest(
            title="The Ancestral Ledger",
            franchise_code="IP-ANCESTRAL-LEDGER",
            logline=ancestral_draft["logline"],
            synopsis=ancestral_draft["full_draft_text"],
            genre="Supernatural Crime Drama",
            primary_language="isiZulu",
            master_owner_id="creator_zola",
            story_world=StoryWorldSchema(
                world_name="Johannesburg Ancestral Arena",
                geographical_setting=ancestral_draft["world_setting"],
                time_period="Contemporary 2026",
                mythology_and_rules="Ancestral ledgers glow in the presence of blood heirs. Spiritual debts double in interest if contested in civil courts.",
                cultural_context="isiZulu traditions colliding with Sandton corporate banking."
            ),
            characters=[
                CharacterBibleSchema(
                    name="Sipho Ndlovu",
                    role="protagonist",
                    archetype="Reluctant Heir / Corporate Auditor",
                    secret_motivation="Prove he is more than his late uncle legacy",
                    fatal_flaw="Obsession with balance sheet control",
                    signature_quote="You cannot audit an ancestral debt with modern debit orders."
                ),
                CharacterBibleSchema(
                    name="Bra Mike",
                    role="antagonist",
                    archetype="Ruthless Debt Collector",
                    secret_motivation="Secure the Sandton gold transit route rights",
                    fatal_flaw="Underestimates ancestral spiritual power",
                    signature_quote="Your grandfather signed in blood, boy. We collect today."
                )
            ],
            rights_splits=[
                RightsSplitSchema(
                    beneficiary_user_id="creator_zola",
                    stakeholder_role="Showrunner",
                    royalty_split_pct=70.0,
                    contract_ref="WELELE-CTR-2026-ANC01"
                ),
                RightsSplitSchema(
                    beneficiary_user_id="welele_platform",
                    stakeholder_role="Co-Producer",
                    royalty_split_pct=30.0,
                    contract_ref="WELELE-CTR-2026-PLAT01"
                )
            ]
        )
        created_ip_detail = ip_repository.create_ip(ip_req)
        target_ip_id = created_ip_detail["ip"]["id"]
    else:
        target_ip_id = ip_match["id"]

    # Save Canonical Story Package
    story_package_payload = {
        "ip_id": target_ip_id,
        "creator_id": "creator_zola",
        "package_title": "The Ancestral Ledger: Episode 1 Package",
        "target_duration_seconds": 90,
        "beats": [
            {"beat_number": 1, "description": "Sipho receives the locked safe deposit box in his Sandton office."},
            {"beat_number": 2, "description": "The glowing isiZulu ledger reveals an unpaid spiritual debt from 1892."},
            {"beat_number": 3, "description": "Bra Mike and two enforcers corner Sipho in the parking garage."}
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
        f"/api/ip/{target_ip_id}/story-forge/save",
        json=story_package_payload,
        headers=creator_headers
    )
    assert res_pkg.status_code == 200
    pkg_res = res_pkg.json()
    assert pkg_res["success"] is True
    canonical_package = pkg_res["package"]
    canonical_package_id = canonical_package["id"]
    lineage_hash = canonical_package["lineage_hash"]
    assert len(lineage_hash) == 64

    # =========================================================================
    # STEP 6: Production Layer — Series & Episode 1 Creation
    # =========================================================================
    series_id = "story_ancestral_ledger"
    all_series = series_repository.local_get("series")
    existing_s = next((s for s in all_series if s["id"] == series_id), None)
    if not existing_s:
        new_series = {
            "id": series_id,
            "ip_id": target_ip_id,
            "season_number": 1,
            "title": "The Ancestral Ledger",
            "tagline": "Debt transcends generations.",
            "synopsis": ancestral_draft["logline"],
            "cover_image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
            "vertical_poster": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80",
            "genre": "Supernatural Crime Drama",
            "rating": 5.0,
            "total_episodes": 1,
            "free_episodes": 1,
            "coin_price_per_episode": 5,
            "is_published": True,
            "creator_id": "creator_zola",
            "creator_name": "Zola Dlamini",
            "available_languages": ["isiZulu", "English"],
            "tags": ["Supernatural", "Finance", "Johannesburg", "Microdrama"],
            "created_at": "2026-09-16T15:00:00Z",
            "updated_at": "2026-09-16T15:00:00Z"
        }
        series_repository.local_insert("series", new_series)

    # Ingest real video master binary payload into storage
    dummy_video_bytes = b"WELELE_AUTHENTIC_ANCESTRAL_LEDGER_EP01_MASTER_VIDEO_PAYLOAD_9_16"
    stored_media = storage_service.save_binary_master(
        file_bytes=dummy_video_bytes,
        story_id=series_id,
        episode_id="ep_ancestral_01",
        filename="ep_ancestral_01.mp4"
    )
    storage_key = stored_media["storage_key"]
    assert storage_key == "masters/story_ancestral_ledger/ep_ancestral_01.mp4"

    # Add Episode 1 linked to story_package_id
    ep_payload = {
        "series_id": series_id,
        "episode_number": 1,
        "title": "The Unsealed Safe Deposit Box",
        "synopsis": "Sipho receives a glowing isiZulu ledger in his Sandton office.",
        "duration_seconds": 90,
        "is_free": True,
        "coin_price": 0,
        "cliffhanger_time": 75,
        "cliffhanger_hook": "Will Sipho sign the second ledger page or let the spirits take his office?",
        "story_package_id": canonical_package_id,
        "status": "published",
        "storage_key": storage_key,
        "video_url": f"/media/{storage_key}"
    }

    res_ep = client.post("/api/creators/episodes/add", json=ep_payload, headers=admin_headers)
    assert res_ep.status_code == 200
    created_ep = res_ep.json()["episode"]
    episode_id = created_ep["id"]
    assert created_ep["story_package_id"] == canonical_package_id

    # =========================================================================
    # STEP 7: Media & Stream Verification
    # =========================================================================
    res_stream = client.get(f"/api/episodes/{series_id}/{episode_id}?user_id=user_viewer_01")
    assert res_stream.status_code == 200
    stream_data = res_stream.json()
    assert stream_data["is_unlocked"] is True
    assert stream_data["storage_key"] == storage_key
    assert stream_data["stream"]["primary_url"].endswith(storage_key) or stream_data["stream"]["primary_url"] == f"/media/{storage_key}"
    assert stream_data["stream"]["format"] == "9:16 Canonical Vertical"
    assert stream_data["cliffhanger"]["timestamp_seconds"] == 75

    # Verify binary exists in storage
    binary_content = storage_service.get_stored_binary(storage_key)
    assert binary_content == dummy_video_bytes

    # =========================================================================
    # STEP 8: Telemetry Generation & Attribution
    # =========================================================================
    test_session_id = "sess_ancestral_validation_001"
    telemetry_events = [
        {"event_name": "episode_started", "session_id": test_session_id, "user_id": "user_viewer_01", "series_id": series_id, "episode_id": episode_id, "playback_second": 0},
        {"event_name": "heartbeat", "session_id": test_session_id, "user_id": "user_viewer_01", "series_id": series_id, "episode_id": episode_id, "playback_second": 30},
        {"event_name": "cliffhanger_reached", "session_id": test_session_id, "user_id": "user_viewer_01", "series_id": series_id, "episode_id": episode_id, "playback_second": 75},
        {"event_name": "episode_completed", "session_id": test_session_id, "user_id": "user_viewer_01", "series_id": series_id, "episode_id": episode_id, "playback_second": 90}
    ]

    for evt in telemetry_events:
        res_track = client.post("/api/events/track", json=evt)
        assert res_track.status_code == 200

    # Query retention curve from repository
    retention_resp = event_repository.get_episode_retention(series_id, episode_id)
    assert retention_resp.series_id == series_id
    assert retention_resp.episode_id == episode_id
    assert len(retention_resp.retention_curve) > 0

    # =========================================================================
    # STEP 9: Analytics & Intelligence Handoff
    # =========================================================================
    diag_evidence = intelligence_service.generate_episode_diagnostic_evidence(
        ip_id=target_ip_id,
        series_id=series_id,
        episode_id=episode_id
    )
    assert "evidence" in diag_evidence
    evidence = diag_evidence["evidence"]
    assert evidence["series_id"] == series_id
    assert evidence["episode_id"] == episode_id
    assert evidence["ip_id"] == target_ip_id

    # =========================================================================
    # STEP 10: Complete Lineage & Provenance Chain Verification
    # =========================================================================
    # 1. Creator Draft -> Submission -> IP -> Package -> Series -> Episode -> Media -> Telemetry
    all_drafts = story_review_repo.get_drafts("creator_zola")
    draft_match = next((d for d in all_drafts if d["id"] == draft_id or d.get("title") == "The Ancestral Ledger"), None)
    assert draft_match is not None

    all_submissions = story_review_repo.get_submissions("creator_zola")
    sub_match = next((s for s in all_submissions if s["submission_id"] == submission_id), None)
    assert sub_match is not None
    assert sub_match["draft_id"] == draft_id

    ip_detail = ip_repository.get_ip_detail(target_ip_id)
    assert ip_detail["ip"]["title"] == "The Ancestral Ledger"
    pkg_in_ip = next((p for p in ip_detail["story_packages"] if p["id"] == canonical_package_id), None)
    assert pkg_in_ip is not None
    assert pkg_in_ip["lineage_hash"] == lineage_hash

    episodes_in_series = series_repository.local_get("episodes")
    ep_persisted = next((e for e in episodes_in_series if e["id"] == episode_id), None)
    assert ep_persisted is not None
    assert ep_persisted["story_package_id"] == canonical_package_id
    assert ep_persisted["storage_key"] == storage_key

    media_assets = series_repository.local_get("media_assets")
    media_persisted = next((m for m in media_assets if m.get("episode_id") == episode_id), None)
    assert media_persisted is not None
    assert media_persisted["storage_key"] == storage_key

    events_persisted = event_repository.get_events_for_episode(episode_id)
    assert len(events_persisted) >= 4
    for ev in events_persisted:
        assert ev["series_id"] == series_id
        assert ev["episode_id"] == episode_id
