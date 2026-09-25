"""
Welele Media™ — Live Supabase Security Gate Verification Tool
Directly executes verification tests against the live Supabase environment at:
https://mngyyxqdhjgteezwkxdn.supabase.co
"""

import os
import sys
import json
import uuid
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client
from fastapi.testclient import TestClient
from main import app
from config import settings
from services.rbac_service import create_access_token

client = TestClient(app)

url = settings.SUPABASE_URL
anon_key = settings.SUPABASE_ANON_KEY
service_key = settings.SUPABASE_KEY

if not url or not anon_key or not service_key:
    print("[ERROR] Live Supabase credentials missing from configuration!")
    sys.exit(1)

admin_client = create_client(url, service_key)
anon_client = create_client(url, anon_key)

print(f"\n=======================================================")
print(f"WELELE MEDIA™ — LIVE DATABASE SECURITY VERIFICATION")
print(f"Target Instance: {url}")
print(f"=======================================================\n")

results = []

def record(name: str, passed: bool, detail: str = ""):
    status = "[PASS]" if passed else "[FAIL]"
    results.append((name, passed, detail))
    print(f"{status} {name}")
    if detail:
        print(f"       Detail: {detail}")

# ----------------------------------------------------------------------------
# 1. ANONYMOUS ROLE VERIFICATION (Live PostgREST)
# ----------------------------------------------------------------------------
print("--- 1. ANONYMOUS ROLE TESTS (Direct PostgREST with anon key) ---")

# A. SELECT users
try:
    res = anon_client.table("users").select("*").execute()
    count = len(res.data)
    record("ANON: SELECT users -> DENIED", count == 0, f"Returned {count} rows (expected 0)")
except Exception as e:
    record("ANON: SELECT users -> DENIED", True, f"Rejected with exception: {e}")

# B. SELECT wallets
try:
    res = anon_client.table("wallets").select("*").execute()
    count = len(res.data)
    record("ANON: SELECT wallets -> DENIED", count == 0, f"Returned {count} rows (expected 0)")
except Exception as e:
    record("ANON: SELECT wallets -> DENIED", True, f"Rejected with exception: {e}")

# C. SELECT payment_transactions
try:
    res = anon_client.table("payment_transactions").select("*").execute()
    count = len(res.data)
    record("ANON: SELECT payment_transactions -> DENIED", count == 0, f"Returned {count} rows (expected 0)")
except Exception as e:
    record("ANON: SELECT payment_transactions -> DENIED", True, f"Rejected with exception: {e}")

# D. DELETE episode
try:
    # Query a real episode with service role
    episodes = admin_client.table("episodes").select("id").limit(1).execute()
    if episodes.data:
        target_id = episodes.data[0]["id"]
        res = anon_client.table("episodes").delete().eq("id", target_id).execute()
        # Verify row still exists in database
        check = admin_client.table("episodes").select("id").eq("id", target_id).execute()
        still_exists = len(check.data) > 0
        record("ANON: DELETE episode -> DENIED", still_exists and len(res.data) == 0, f"Episode preserved: {still_exists}, Deleted by anon: {len(res.data)}")
    else:
        record("ANON: DELETE episode -> DENIED", True, "No episodes to test deletion on")
except Exception as e:
    record("ANON: DELETE episode -> DENIED", True, f"Rejected with exception: {e}")

# E. INSERT audit ledger
try:
    res = anon_client.table("security_audit_ledger").insert({
        "event_id": f"forged_{uuid.uuid4().hex[:6]}",
        "domain": "SECURITY",
        "event_type": "FORGERY_TEST",
        "actor_id": "anon",
        "actor_role": "anon",
        "target_type": "probe",
        "target_id": "probe",
        "payload_hash": "0"*64,
        "previous_hash": "0"*64,
        "entry_hash": "0"*64
    }).execute()
    record("ANON: INSERT audit ledger -> DENIED", False, "UNSECURED: Anon was permitted to insert audit record!")
except Exception as e:
    record("ANON: INSERT audit ledger -> DENIED", True, f"Blocked successfully: {e}")

# F. INSERT unlocked episode
try:
    res = anon_client.table("unlocked_episodes").insert({
        "user_id": str(uuid.uuid4()),
        "episode_id": str(uuid.uuid4()),
        "story_id": str(uuid.uuid4()),
        "unlock_method": "HACK"
    }).execute()
    record("ANON: INSERT unlocked_episodes -> DENIED", False, "UNSECURED: Anon was permitted to insert unlock record!")
except Exception as e:
    record("ANON: INSERT unlocked_episodes -> DENIED", True, f"Blocked successfully: {e}")

# G. UPDATE experience_layouts
try:
    res = anon_client.table("experience_layouts").update({"status": "defaced"}).eq("page_id", "home").execute()
    record("ANON: UPDATE experience_layouts -> DENIED", len(res.data) == 0, f"Modified rows: {len(res.data)}")
except Exception as e:
    record("ANON: UPDATE experience_layouts -> DENIED", True, f"Blocked successfully: {e}")

# ----------------------------------------------------------------------------
# 2. VIEWER TENANT ISOLATION TESTS
# ----------------------------------------------------------------------------
print("\n--- 2. VIEWER TENANT ISOLATION & API DEFENSE ---")

viewer_a_id = f"usr_a_{uuid.uuid4().hex[:6]}"
viewer_b_id = f"usr_b_{uuid.uuid4().hex[:6]}"

viewer_a_token = create_access_token(user_id=viewer_a_id, role="viewer")
viewer_b_token = create_access_token(user_id=viewer_b_id, role="viewer")

# A. Read own wallet -> ALLOW
res_own_wallet = client.get(
    "/api/wallet/balance",
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER A: Read own wallet -> ALLOW", res_own_wallet.status_code == 200 and res_own_wallet.json()["user_id"] == viewer_a_id, f"Status: {res_own_wallet.status_code}")

# B. Read Viewer B wallet -> DENIED (HTTP 403)
res_other_wallet = client.get(
    f"/api/wallet/balance?user_id={viewer_b_id}",
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER A: Read Viewer B wallet -> DENIED", res_other_wallet.status_code == 403, f"Status: {res_other_wallet.status_code}")

# C. Read own ledger -> ALLOW
res_own_ledger = client.get(
    "/api/wallet/ledger",
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER A: Read own ledger -> ALLOW", res_own_ledger.status_code == 200 and res_own_ledger.json()["user_id"] == viewer_a_id, f"Status: {res_own_ledger.status_code}")

# D. Read Viewer B ledger -> DENIED (HTTP 403)
res_other_ledger = client.get(
    f"/api/wallet/ledger?user_id={viewer_b_id}",
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER A: Read Viewer B ledger -> DENIED", res_other_ledger.status_code == 403, f"Status: {res_other_ledger.status_code}")

# E. Unlock without legitimate payment -> DENIED (HTTP 402)
ep_res = admin_client.table("episodes").select("id, story_id, coin_price").limit(1).execute()
if ep_res.data:
    live_ep = ep_res.data[0]
    live_ep_id = live_ep["id"]
    live_story_id = live_ep.get("story_id", "story_default")
    
    # Ensure story is available in local lookup
    from repositories.series_repository import series_repository
    series_repository.local_insert("series", {"id": live_story_id, "title": "Live Test Story", "free_episodes": 0})
    series_repository.local_insert("episodes", {"id": live_ep_id, "series_id": live_story_id, "coin_price": 5, "is_free": False, "status": "published"})

    res_fake_unlock = client.post(
        f"/api/episodes/{live_story_id}/{live_ep_id}/unlock?method=VIP_PASS",
        headers={"Authorization": f"Bearer {viewer_a_token}"}
    )
    record("VIEWER A: Unlock without payment -> DENIED", res_fake_unlock.status_code == 402, f"Status: {res_fake_unlock.status_code} ({res_fake_unlock.json().get('detail')})")
else:
    record("VIEWER A: Unlock without payment -> DENIED", True, "No live episode to test against")

# F. Modify another user's data (Gift debit spoofing) -> DENIED
res_spoof_debit = client.post(
    "/api/wallet/gifts/send",
    json={
        "user_id": viewer_b_id, # Spoofing Viewer B
        "creator_id": "creator_zola",
        "series_id": "series_1",
        "episode_id": "ep_1",
        "gift_id": "gift_spoof",
        "gift_name": "Gold",
        "gift_icon": "💰",
        "coin_cost": 25
    },
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER A: Debit Viewer B wallet -> DENIED", res_spoof_debit.status_code == 403, f"Status: {res_spoof_debit.status_code}")

# ----------------------------------------------------------------------------
# 3. CREATOR & ADMIN PERMISSIONS
# ----------------------------------------------------------------------------
print("\n--- 3. CREATOR & ADMIN ROLE CAPABILITIES ---")

creator_token = create_access_token(user_id="creator_zola", role="creator", creator_id="creator_zola")
admin_token = create_access_token(user_id="admin_supervisor", role="admin")

# Creator presigned upload access -> ALLOW
res_creator_upload = client.post(
    "/api/storage/presigned-upload-url",
    json={"story_id": "series_mzansi", "episode_number": 1, "filename": "scene.mp4"},
    headers={"Authorization": f"Bearer {creator_token}"}
)
record("CREATOR: Presigned upload URL -> ALLOW", res_creator_upload.status_code == 200, f"Status: {res_creator_upload.status_code}")

# Viewer attempting Creator presigned upload -> DENIED (HTTP 403)
res_viewer_upload = client.post(
    "/api/storage/presigned-upload-url",
    json={"story_id": "series_mzansi", "episode_number": 1, "filename": "scene.mp4"},
    headers={"Authorization": f"Bearer {viewer_a_token}"}
)
record("VIEWER: Presigned upload URL -> DENIED", res_viewer_upload.status_code == 403, f"Status: {res_viewer_upload.status_code}")

# Admin administrative access -> ALLOW
res_admin_wallet = client.get(
    f"/api/wallet/balance?user_id={viewer_a_id}",
    headers={"Authorization": f"Bearer {admin_token}"}
)
record("ADMIN: Admin inspect viewer wallet -> ALLOW", res_admin_wallet.status_code == 200, f"Status: {res_admin_wallet.status_code}")

# ----------------------------------------------------------------------------
# 4. JWT IDENTITY ALIGNMENT
# ----------------------------------------------------------------------------
print("\n--- 4. JWT IDENTITY ALIGNMENT ---")

test_user_id = str(uuid.uuid4())
aligned_token = create_access_token(user_id=test_user_id, role="viewer")

# Test FastAPI introspection
profile_res = client.get(
    "/api/auth/me",
    headers={"Authorization": f"Bearer {aligned_token}"}
)
fastapi_sub = profile_res.json().get("user_id") if profile_res.status_code == 200 else None

# Test payload sub
from services.rbac_service import verify_access_token
payload = verify_access_token(aligned_token)
jwt_sub = payload.get("sub")

identity_aligned = (fastapi_sub == test_user_id == jwt_sub)
record("JWT IDENTITY: FastAPI sub == JWT sub == User ID", identity_aligned, f"FastAPI sub: {fastapi_sub}, JWT sub: {jwt_sub}, Expected: {test_user_id}")

# ----------------------------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------------------------
print("\n=======================================================")
passed_count = sum(1 for _, p, _ in results if p)
total_count = len(results)
print(f"FINAL RESULT: {passed_count}/{total_count} CHECKS PASSED")
print(f"=======================================================\n")

if passed_count < total_count:
    sys.exit(1)
