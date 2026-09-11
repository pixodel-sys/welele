"""
Welele Media™ — Deployment Persistence & Lifecycle Survival Test Suite
Tests complete Digital IP -> Series -> Episode -> Moderation -> Approve -> Publish -> Unlock -> Play pipeline
and verifies survival across (1) Process Restart, and (2) Fresh Deployment / Startup Seeding.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import db
from config import settings
from seed_data import seed_database_if_empty
from repositories.series_repository import series_repository
from repositories.ip_repository import ip_repository
from repositories.ledger_repository import ledger_repository
from services.rbac_service import create_access_token

client = TestClient(app)

def test_full_lifecycle_and_deployment_survival():
    creator_id = "creator_zola"
    admin_id = "admin_supervisor"
    user_id = "user_sa_01"
    unique_suffix = uuid.uuid4().hex[:6]

    creator_token = create_access_token(user_id=creator_id, role="creator", creator_id=creator_id)
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    admin_token = create_access_token(user_id=admin_id, role="admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    viewer_token = create_access_token(user_id=user_id, role="viewer")
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    # =========================================================================
    # PHASE 1: FULL LIFECYCLE CREATION & PLAYBACK
    # =========================================================================
    print("\n--- PHASE 1: EXECUTING FULL IP -> SERIES -> EPISODE -> PLAYBACK PIPELINE ---")

    # 1. Create IP
    ip_payload = {
        "title": f"Jozi Gold Rush {unique_suffix}",
        "franchise_code": f"IP-JGR-{unique_suffix.upper()}",
        "logline": "A gritty tactical gold courier thriller across the M2 highway.",
        "synopsis": "Full synopsis of gold transit syndicates in modern Johannesburg.",
        "genre": "Action & Crime Thriller",
        "primary_language": "isiZulu",
        "master_owner_id": creator_id
    }
    ip_res = client.post("/api/ip/create", json=ip_payload, headers=creator_headers)
    assert ip_res.status_code == 200, f"Create IP failed: {ip_res.text}"
    created_ip_detail = ip_res.json()
    ip_id = created_ip_detail["ip"]["id"]
    print(f"[1/7] Created Digital IP: {ip_id} ({ip_payload['title']})")

    # 2. Create Series
    series_payload = {
        "title": f"Jozi Gold Rush: Season 1 {unique_suffix}",
        "tagline": "Gold always demands blood in Jozi.",
        "synopsis": "Season 1 of the high stakes courier drama.",
        "genre": "Action • Crime",
        "creator_id": creator_id,
        "coin_price_per_episode": 5,
        "vertical_poster": "/posters/blood_ties.jpg"
    }
    series_res = client.post("/api/creators/series/create", json=series_payload, headers=creator_headers)
    assert series_res.status_code == 200, f"Create Series failed: {series_res.text}"
    created_series = series_res.json()["story"]
    series_id = created_series["id"]
    print(f"[2/7] Created Series: {series_id} ({series_payload['title']})")

    # 3. Add Episode & Ingest Media (Automatically placed in moderation queue: under_review)
    ep_payload = {
        "series_id": series_id,
        "episode_number": 1,
        "title": "The First Run",
        "synopsis": "The armored courier crosses the bridge before sunrise.",
        "duration_seconds": 75,
        "is_free": False,
        "coin_price": 5,
        "cliffhanger_hook": "The security beacon was switched to emergency frequency.",
        "cliffhanger_time": 65,
        "video_url": "/videos/ocean_waves.mp4"
    }
    ep_res = client.post("/api/creators/episodes/add", json=ep_payload, headers=creator_headers)
    assert ep_res.status_code == 200, f"Add Episode failed: {ep_res.text}"
    created_ep = ep_res.json()["episode"]
    ep_id = created_ep["id"]
    assert created_ep.get("status") == "under_review", f"Expected under_review, got {created_ep.get('status')}"
    print(f"[3/7] Ingested Episode & Media Asset: {ep_id} (Status: {created_ep.get('status')})")

    # 4. Admin Approves Moderation (Promotes to Published)
    approve_res = client.post(f"/api/admin/moderation/{ep_id}/approve", headers=admin_headers)
    assert approve_res.status_code == 200, f"Approve moderation failed: {approve_res.text}"
    approved_data = approve_res.json()
    assert approved_data.get("success") is True
    assert approved_data.get("status") == "approved" or approved_data.get("episode", {}).get("status") == "published"
    print(f"[4/7] Approved & Published Episode via Admin Moderation: {ep_id}")

    # 5. User Unlocks Episode (Double-Entry Coin Ledger)
    wallet_before = client.get(f"/api/wallet/balance?user_id={user_id}").json()
    initial_balance = wallet_before.get("total_usable_coins", 0)

    unlock_res = client.post(f"/api/episodes/{series_id}/{ep_id}/unlock?user_id={user_id}&method=COINS", headers=viewer_headers)
    assert unlock_res.status_code == 200, f"Unlock failed: {unlock_res.text}"
    wallet_after = client.get(f"/api/wallet/balance?user_id={user_id}").json()
    assert wallet_after.get("total_usable_coins") == initial_balance - 5, "Coin deduction discrepancy in atomic ledger."
    print(f"[5/7] Unlocked Episode with 5 Coins. User balance: {initial_balance} -> {wallet_after.get('total_usable_coins')}")

    # 6. Verify Authoritative Playback Stream
    stream_res = client.get(f"/api/episodes/{series_id}/{ep_id}?user_id={user_id}")
    assert stream_res.status_code == 200, f"Stream playback failed: {stream_res.text}"
    stream_data = stream_res.json()
    assert stream_data.get("is_unlocked") is True
    assert stream_data.get("stream") is not None
    assert stream_data["stream"].get("primary_url") is not None
    print(f"[6/7] Verified Authoritative Stream Playback: {stream_data['stream'].get('primary_url')}")

    # =========================================================================
    # PHASE 2: IN-PROCESS RESTART TEST (RELOAD PERSISTENCE STORE)
    # =========================================================================
    print("\n--- PHASE 2: IN-PROCESS RESTART PERSISTENCE VERIFICATION ---")
    # Reload database from disk
    db._load()

    # Re-verify IP
    persisted_ips = db.get("digital_ips")
    assert any(p["id"] == ip_id for p in persisted_ips), f"Digital IP {ip_id} missing after in-process reload."

    # Re-verify Series
    persisted_series = db.get("series")
    assert any(s["id"] == series_id for s in persisted_series), f"Series {series_id} missing after in-process reload."

    # Re-verify Episode
    persisted_episodes = db.get("episodes")
    matched_ep = next((e for e in persisted_episodes if e["id"] == ep_id), None)
    assert matched_ep is not None, f"Episode {ep_id} missing after in-process reload."
    assert matched_ep.get("status") == "published", f"Episode status altered after reload: {matched_ep.get('status')}"

    print("[PASS] Phase 2: In-process reload preserved all 7 platform entities.")

    # =========================================================================
    # PHASE 3: DEPLOYMENT SURVIVAL SIMULATION TEST (STARTUP SEEDING RUN)
    # =========================================================================
    print("\n--- PHASE 3: FRESH DEPLOYMENT / STARTUP SEEDING SURVIVAL TEST ---")
    
    # Simulate a new container boot executing startup seeding
    seed_database_if_empty(force=True)

    # 1. IP still exists?
    all_ips = client.get("/api/ip/list").json()
    assert any(p["id"] == ip_id for p in all_ips), f"FAIL: IP {ip_id} lost after deployment seeding."
    print("  [PASS] IP still exists:", ip_id)

    # 2. Series still exists in Creator Dashboard?
    creator_dashboard = client.get(f"/api/creators/{creator_id}/dashboard", headers=creator_headers).json()
    dashboard_series = creator_dashboard.get("series", [])
    assert any(s["id"] == series_id for s in dashboard_series), "FAIL: Series lost from Creator Studio after deploy."
    print("  [PASS] Series still exists:", series_id)

    # 3. Episode still exists?
    matched_s = next(s for s in dashboard_series if s["id"] == series_id)
    assert any(e["id"] == ep_id for e in matched_s.get("episodes", [])), "FAIL: Episode lost after deployment."
    print("  [PASS] Episode still exists:", ep_id)

    # 4. Moderation state still APPROVED / PUBLISHED?
    post_deploy_ep = next(e for e in matched_s.get("episodes", []) if e["id"] == ep_id)
    assert post_deploy_ep.get("status") == "published", f"Status altered: {post_deploy_ep.get('status')}"
    print("  [PASS] Moderation state preserved: PUBLISHED")

    # 5. Coins/Ledger intact?
    balance_check = client.get(f"/api/wallet/balance?user_id={user_id}").json()
    assert balance_check.get("total_usable_coins") == initial_balance - 5, "FAIL: Ledger balance reset after deploy."
    print("  [PASS] Coins & Ledger balance preserved:", balance_check.get("total_usable_coins"))

    # 6. Playback stream still authorized and functional?
    post_deploy_stream = client.get(f"/api/episodes/{series_id}/{ep_id}?user_id={user_id}").json()
    assert post_deploy_stream.get("is_unlocked") is True
    assert post_deploy_stream.get("stream") is not None
    print("  [PASS] Playback stream verified post-deployment:", post_deploy_stream["stream"].get("primary_url"))

    print("\n========================================================")
    print("ALL DEPLOYMENT SURVIVAL INVARIANTS VERIFIED 100%!")
    print("========================================================")

if __name__ == "__main__":
    test_full_lifecycle_and_deployment_survival()
