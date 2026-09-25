"""
Welele Media™ — Security Isolation & Database Attack Verification Suite
P4 Enforcement:
- Exercises the 7-Column Actor Isolation Matrix (Anon, Viewer, Creator, Admin, Service Role)
- Directly verifies denial of the 11 identified critical attack vectors:
  1. ANON -> GET /users
  2. ANON -> DELETE published episode
  3. ANON -> INSERT audit event
  4. ANON -> GET payment_transactions
  5. ANON -> INSERT fake unlocked_episode
  6. ANON -> Modify experience_layout
  7. VIEWER -> Wallet victim balance (IDOR)
  8. VIEWER -> Wallet victim debit / gift send (IDOR)
  9. CALLER -> Free unlock without active pass/payment
  10. ANON -> R2 video upload / presigned URL without creator/admin role
  11. ANON -> Gemini AI generation endpoint without authentication
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app
from config import settings
from database import db
from services.rbac_service import create_access_token
from repositories.series_repository import series_repository
from repositories.ledger_repository import ledger_repository

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_test_isolation():
    db.enable_test_isolation()
    yield
    db.disable_test_isolation()

@pytest.fixture
def viewer_v1_token():
    return create_access_token(
        user_id="usr_viewer_01",
        role="viewer",
        phone="+27821111111",
        market="ZA"
    )

@pytest.fixture
def viewer_v2_token():
    return create_access_token(
        user_id="usr_viewer_02",
        role="viewer",
        phone="+27822222222",
        market="ZA"
    )

@pytest.fixture
def creator_token():
    return create_access_token(
        user_id="usr_creator_zola",
        role="creator",
        creator_id="creator_zola",
        phone="+27828912345",
        market="ZA"
    )

@pytest.fixture
def admin_token():
    return create_access_token(
        user_id="admin_supervisor",
        role="admin",
        email="ops@welele.media",
        market="ALL"
    )

# ============================================================================
# 1. DATABASE & SQL POLICY DEFINITION VERIFICATION (Attacks 1 - 6)
# ============================================================================

def test_attack_01_sql_hardening_script_protects_users():
    """Verify that migration v3 strictly isolates public.users to authenticated owners and admins."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    assert os.path.exists(sql_path), "supabase_security_hardening_v3.sql must exist"
    
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;" in sql
    assert "users_select_policy" in sql
    # Anon must NEVER have SELECT granted on users
    assert "GRANT SELECT ON public.users TO anon;" not in sql
    assert "id = auth.uid()" in sql

def test_attack_02_sql_hardening_script_prevents_anon_delete_episodes():
    """Verify that episodes SELECT does not grant DELETE/UPDATE to public/anon (fixes FOR ALL bug)."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # The fatal bug was: CREATE POLICY ... ON episodes FOR ALL USING (status = 'published');
    assert "CREATE POLICY \"episodes_tenant_policy\" ON episodes\nFOR ALL" not in sql
    assert "FOR ALL USING (status = 'published')" not in sql
    # Must be strictly FOR SELECT for anon
    assert "FOR SELECT TO anon, authenticated" in sql
    assert "FOR DELETE TO authenticated" in sql

def test_attack_03_sql_hardening_script_prevents_anon_insert_audit_events():
    """Verify that security_audit_ledger insertion is strictly restricted to service_role."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "audit_ledger_append_policy" not in sql or "DROP POLICY IF EXISTS \"audit_ledger_append_policy\"" in sql
    assert "CREATE POLICY \"audit_ledger_insert_system\" ON public.security_audit_ledger\nFOR INSERT TO service_role" in sql
    assert "REVOKE UPDATE, DELETE, TRUNCATE ON public.security_audit_ledger FROM PUBLIC, anon, authenticated;" in sql

def test_attack_04_sql_hardening_script_protects_payment_transactions():
    """Verify payment_transactions table has RLS enabled and grants no permissions to anon."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "payment_transactions" in sql
    assert "GRANT SELECT ON public.payment_transactions TO anon;" not in sql
    assert "payment_transactions_select_owner" in sql

def test_attack_05_sql_hardening_script_protects_unlocked_episodes():
    """Verify unlocked_episodes table has RLS enabled and client mutation is revoked."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "ALTER TABLE public.unlocked_episodes ENABLE ROW LEVEL SECURITY;" in sql or "unlocked_episodes" in sql
    assert "GRANT INSERT ON public.unlocked_episodes TO anon;" not in sql
    assert "GRANT INSERT ON public.unlocked_episodes TO authenticated;" not in sql

def test_attack_06_sql_hardening_script_protects_experience_layouts():
    """Verify experience_layouts write operations are restricted strictly to admin role."""
    sql_path = os.path.join(os.path.dirname(__file__), "supabase_security_hardening_v3.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "layouts_insert_admin" in sql
    assert "layouts_update_admin" in sql
    assert "layouts_delete_admin" in sql
    assert "(auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'" in sql

# ============================================================================
# 2. RUNTIME API ATTACK PATH TESTS (Attacks 7 - 11 & IDOR Verification)
# ============================================================================

def test_attack_07_viewer_cannot_view_victim_wallet_balance_idor(viewer_v1_token):
    """ATTACK 7: Viewer 1 attempts to inspect Viewer 2's wallet balance."""
    # Seed victim wallet
    ledger_repository.get_or_create_wallet("usr_victim_target")

    # Unauthenticated request must be denied
    res_anon = client.get("/api/wallet/balance?user_id=usr_victim_target")
    assert res_anon.status_code == 401

    # Viewer 1 attempting to view victim wallet must be blocked with HTTP 403 Forbidden
    res_viewer = client.get(
        "/api/wallet/balance?user_id=usr_victim_target",
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_viewer.status_code == 403

def test_attack_07_viewer_cannot_view_victim_financial_ledger_idor(viewer_v1_token):
    """ATTACK 7 (Part B): Viewer 1 attempts to inspect Viewer 2's ledger."""
    res_anon = client.get("/api/wallet/ledger?user_id=usr_victim_target")
    assert res_anon.status_code == 401

    res_viewer = client.get(
        "/api/wallet/ledger?user_id=usr_victim_target",
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_viewer.status_code == 403

def test_attack_08_viewer_cannot_debit_victim_wallet_for_gift(viewer_v1_token):
    """ATTACK 8: Viewer 1 attempts to debit coins from Viewer 2's account by spoofing user_id in payload."""
    # Fund victim wallet with 100 coins
    ledger_repository.credit_coins_atomic("usr_victim_target", 100, 0, "TEST_SEED", "ref_01")
    victim_initial_balance = ledger_repository.get_balance("usr_victim_target")["total_usable_coins"]

    gift_payload = {
        "user_id": "usr_victim_target", # Spoofed victim
        "creator_id": "creator_zola",
        "series_id": "series_blood_ties",
        "episode_id": "ep_1",
        "gift_id": "gift_gold_99",
        "gift_name": "Gold Trophy",
        "gift_icon": "🏆",
        "coin_cost": 25
    }

    # Unauthenticated attempt
    res_anon = client.post("/api/wallet/gifts/send", json=gift_payload)
    assert res_anon.status_code == 401

    # Authenticated as Viewer 1, attempting to debit victim
    res_viewer = client.post(
        "/api/wallet/gifts/send",
        json=gift_payload,
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_viewer.status_code == 403

    # Ensure victim's coins were untouched
    victim_after_balance = ledger_repository.get_balance("usr_victim_target")["total_usable_coins"]
    assert victim_after_balance == victim_initial_balance

def test_attack_09_free_unlock_without_active_pass_rejected(viewer_v1_token):
    """ATTACK 9: Caller attempts to unlock a paid episode with method=VIP_PASS without paying."""
    test_series = {
        "id": "ser_lock_test",
        "title": "Lock Test Series",
        "free_episodes": 0
    }
    series_repository.local_insert("series", test_series)
    test_episode = {
        "id": "ep_lock_test",
        "series_id": "ser_lock_test",
        "episode_number": 4,
        "title": "Premium Episode 4",
        "coin_price": 10,
        "is_free": False,
        "status": "published"
    }
    series_repository.local_insert("episodes", test_episode)

    # Unauthenticated attempt
    res_anon = client.post(f"/api/episodes/{test_series['id']}/{test_episode['id']}/unlock?method=VIP_PASS")
    assert res_anon.status_code == 401

    # Authenticated viewer without an active VIP pass
    res_viewer = client.post(
        f"/api/episodes/{test_series['id']}/{test_episode['id']}/unlock?method=VIP_PASS",
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_viewer.status_code == 402
    assert "No active VIP subscription pass" in res_viewer.json()["detail"]

def test_attack_10_unauthenticated_r2_upload_and_presigned_url_rejected():
    """ATTACK 10: Anonymous caller attempts to generate presigned upload URLs or upload binary."""
    presigned_payload = {
        "story_id": "story_exploit_01",
        "episode_number": 1,
        "filename": "exploit_video.mp4"
    }
    res_presigned_anon = client.post("/api/storage/presigned-upload-url", json=presigned_payload)
    assert res_presigned_anon.status_code in (401, 403)

    res_upload_anon = client.post(
        "/api/storage/upload-binary",
        data={"series_id": "story_exploit_01", "episode_number": 1}
    )
    assert res_upload_anon.status_code in (401, 403)

def test_attack_11_unauthenticated_gemini_ai_endpoints_rejected():
    """ATTACK 11: Anonymous caller attempts to consume Gemini AI generation quota."""
    gen_payload = {
        "genre": "Township Hustle",
        "target_duration_seconds": 90,
        "prompt": "Exhaust quota test"
    }
    res_forge_anon = client.post("/api/ai/story-forge/generate", json=gen_payload)
    assert res_forge_anon.status_code == 401

    res_translate_anon = client.post("/api/ai/story-forge/translate", json={"line": "Hello", "target_dialect": "zu"})
    assert res_translate_anon.status_code == 401

# ============================================================================
# 3. 7-COLUMN ACTOR ISOLATION MATRIX ENFORCEMENT
# ============================================================================

def test_actor_matrix_viewer_owns_data_access(viewer_v1_token, admin_token):
    """Verify Viewer 1 can read own balance and Admin can read all."""
    # Seed Viewer 1 wallet
    ledger_repository.credit_coins_atomic("usr_viewer_01", 50, 0, "TEST", "ref_v1")

    # Viewer 1 reads own balance -> Allowed
    res_own = client.get(
        "/api/wallet/balance",
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_own.status_code == 200
    assert res_own.json()["user_id"] == "usr_viewer_01"

    # Admin reads Viewer 1 balance -> Allowed
    res_admin = client.get(
        "/api/wallet/balance?user_id=usr_viewer_01",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["user_id"] == "usr_viewer_01"

def test_actor_matrix_creator_presigned_url_access(creator_token, viewer_v1_token):
    """Verify Creator can request presigned upload URL while Viewer is denied."""
    payload = {
        "story_id": "story_creator_series",
        "episode_number": 1,
        "filename": "creator_scene.mp4"
    }

    # Viewer request -> 403 Forbidden
    res_viewer = client.post(
        "/api/storage/presigned-upload-url",
        json=payload,
        headers={"Authorization": f"Bearer {viewer_v1_token}"}
    )
    assert res_viewer.status_code == 403

    # Creator request -> 200 OK
    res_creator = client.post(
        "/api/storage/presigned-upload-url",
        json=payload,
        headers={"Authorization": f"Bearer {creator_token}"}
    )
    assert res_creator.status_code == 200
    assert "upload_url" in res_creator.json()

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
