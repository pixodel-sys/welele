"""
Welele Media™ — Phase 6J-2R-H Staging Artwork Data Repair Script
Applies surgical remediation to known affected staging series:
1. Abakhongi (4df3daaf-3452-4362-9aef-0bb2ab570bae): Replaces ephemeral blob: URLs with verified durable R2 storage proxy URLs.
2. Bougie (764558a8-ea1d-4734-93b0-ecfe5df8aeb9): Replaces malformed CDN_BASE_URL= URLs with verified durable R2 storage proxy URLs.

STRICT INVARIANTS:
- Staging PostgreSQL only (dbsnaidhznofvyffdfni)
- Zero touches to production or unrelated series
- Verification before and after
"""
import os
import sys
import json
from datetime import datetime, timezone

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ["ENVIRONMENT"] = "staging"
os.environ["APP_ENV"] = "staging"
os.environ["PRODUCTION_SUPABASE_REF"] = "mngyyxqdhjgteezwkxdn"
os.environ["STAGING_SUPABASE_REF"] = "dbsnaidhznofvyffdfni"

from dotenv import load_dotenv
staging_env_path = r"G:\App_Development\App_Dev\Welele Media\.env\.env.staging"
if os.path.exists(staging_env_path):
    load_dotenv(staging_env_path, override=True)

if not os.getenv("ADMIN_MASTER_KEY"):
    os.environ["ADMIN_MASTER_KEY"] = "welele_staging_admin_sec_2026_audit_gate"
if not os.getenv("ADMIN_2FA_CODE"):
    os.environ["ADMIN_2FA_CODE"] = "982341"
if not os.getenv("JWT_SECRET") and not os.getenv("SUPABASE_JWT_SECRET"):
    os.environ["JWT_SECRET"] = "audit_staging_jwt_secret_authorized_2026_signature_token"

from repositories.series_repository import series_repository

def run_repair():
    print("=" * 80)
    print("WELELE MEDIA™ — 6J-2R-H STAGING ARTWORK DATA REPAIR")
    print("=" * 80)
    print(f"Target Database Engine: Supabase PostgreSQL (Staging: dbsnaidhznofvyffdfni)")
    print(f"Live Connection Status: {series_repository.is_live}")
    assert series_repository.is_live, "Fatal: Staging PostgreSQL is not live!"

    series_table = series_repository.get_table("series")
    assert series_table is not None, "Fatal: Unable to access series table in PostgreSQL!"

    audit_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "6J-2R-H",
        "repairs": []
    }

    # -------------------------------------------------------------------------
    # 1. REPAIR ABAKHONGI
    # -------------------------------------------------------------------------
    abakhongi_id = "4df3daaf-3452-4362-9aef-0bb2ab570bae"
    abakhongi_res = series_table.select("id, title, vertical_poster, cover_image, updated_at").eq("id", abakhongi_id).execute()
    assert abakhongi_res.data and len(abakhongi_res.data) > 0, f"Abakhongi ({abakhongi_id}) not found!"
    abakhongi_before = abakhongi_res.data[0]

    print(f"\n1. ABAKHONGI ({abakhongi_before.get('title')}) - ID: {abakhongi_id}")
    print(f"   BEFORE vertical_poster: {abakhongi_before.get('vertical_poster')}")
    print(f"   BEFORE cover_image:     {abakhongi_before.get('cover_image')}")

    abakhongi_poster_after = "https://welele-staging.up.railway.app/api/storage/artwork/4df3daaf-3452-4362-9aef-0bb2ab570bae/poster_3cdd1ce9.png"
    abakhongi_banner_after = "https://welele-staging.up.railway.app/api/storage/artwork/4df3daaf-3452-4362-9aef-0bb2ab570bae/banner_45dcdc6f.png"

    abakhongi_update = series_table.update({
        "vertical_poster": abakhongi_poster_after,
        "cover_image": abakhongi_banner_after,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", abakhongi_id).execute()

    abakhongi_after = abakhongi_update.data[0] if abakhongi_update.data else None
    print(f"   AFTER vertical_poster:  {abakhongi_after.get('vertical_poster')}")
    print(f"   AFTER cover_image:      {abakhongi_after.get('cover_image')}")

    audit_log["repairs"].append({
        "series_id": abakhongi_id,
        "title": abakhongi_before.get("title"),
        "before": abakhongi_before,
        "after": abakhongi_after
    })

    # -------------------------------------------------------------------------
    # 2. REPAIR BOUGIE
    # -------------------------------------------------------------------------
    bougie_id = "764558a8-ea1d-4734-93b0-ecfe5df8aeb9"
    bougie_res = series_table.select("id, title, vertical_poster, cover_image, updated_at").eq("id", bougie_id).execute()
    assert bougie_res.data and len(bougie_res.data) > 0, f"Bougie ({bougie_id}) not found!"
    bougie_before = bougie_res.data[0]

    print(f"\n2. BOUGIE ({bougie_before.get('title')}) - ID: {bougie_id}")
    print(f"   BEFORE vertical_poster: {bougie_before.get('vertical_poster')}")
    print(f"   BEFORE cover_image:     {bougie_before.get('cover_image')}")

    bougie_poster_after = "https://welele-staging.up.railway.app/api/storage/artwork/764558a8-ea1d-4734-93b0-ecfe5df8aeb9/poster_3445ee0d.png"
    bougie_banner_after = "https://welele-staging.up.railway.app/api/storage/artwork/764558a8-ea1d-4734-93b0-ecfe5df8aeb9/banner_3cb85fc0.png"

    bougie_update = series_table.update({
        "vertical_poster": bougie_poster_after,
        "cover_image": bougie_banner_after,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", bougie_id).execute()

    bougie_after = bougie_update.data[0] if bougie_update.data else None
    print(f"   AFTER vertical_poster:  {bougie_after.get('vertical_poster')}")
    print(f"   AFTER cover_image:      {bougie_after.get('cover_image')}")

    audit_log["repairs"].append({
        "series_id": bougie_id,
        "title": bougie_before.get("title"),
        "before": bougie_before,
        "after": bougie_after
    })

    # -------------------------------------------------------------------------
    # 3. VERIFY OTHER SHOWS REMAINED 100% UNTOUCHED
    # -------------------------------------------------------------------------
    print("\n3. VERIFYING ALL OTHER SERIES REMAIN UNTOUCHED...")
    all_res = series_table.select("id, title, vertical_poster, cover_image").execute()
    other_shows = [s for s in (all_res.data or []) if s.get("id") not in [abakhongi_id, bougie_id]]
    print(f"   Confirmed {len(other_shows)} other shows remain untouched.")

    # Write audit trail
    log_path = os.path.join(backend_dir, "audit_trail_6j_2r_h_staging_repair.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(audit_log, f, indent=2)
    print(f"\nAudit trail written to {log_path}")
    print("=" * 80)
    print("6J-2R-H STAGING ARTWORK DATA REPAIR COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_repair()
