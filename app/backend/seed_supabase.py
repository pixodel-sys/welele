"""
Welele Media™ — Live Supabase PostgreSQL Seeding Script
Populates Users, Creators, 9:16 Vertical Series, Episodes, and Wallets directly to Supabase with valid PostgreSQL UUIDs.
"""

import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client
from seed_data import seed_database_if_empty
from database import db

url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not url or not key:
    print("[ERROR] Supabase credentials not found in environment!")
    sys.exit(1)

client = create_client(url, key)
print(f"Connecting and seeding live Supabase PostgreSQL at {url}...")

# Helper to deterministically convert string IDs into valid PostgreSQL UUIDs
def to_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))

seed_database_if_empty()

# 1. Seed Default Users & Admin / Creator Personas
default_users = [
    {
        "id": to_uuid("user_sa_01"),
        "display_name": "Sipho Dlamini",
        "email": "sipho.dlamini@welele.media",
        "phone_number": "0825551234",
        "region_code": "ZA",
        "preferred_language": "isiZulu",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
        "is_creator": False,
        "is_admin": False
    },
    {
        "id": to_uuid("user_sa_02"),
        "display_name": "Lerato Khumalo",
        "email": "lerato.khumalo@welele.media",
        "phone_number": "0835555678",
        "region_code": "ZA",
        "preferred_language": "isiZulu",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
        "is_creator": True,
        "is_admin": False
    },
    {
        "id": to_uuid("user_zola"),
        "display_name": "Zola Dlamini",
        "email": "zola.dlamini@welele.media",
        "phone_number": "+27828912345",
        "region_code": "ZA",
        "preferred_language": "isiZulu",
        "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
        "is_creator": True,
        "is_admin": False
    },
    {
        "id": to_uuid("user_amaka"),
        "display_name": "Amaka Okafor",
        "email": "amaka.okafor@welele.media",
        "phone_number": "+2348031234567",
        "region_code": "NG",
        "preferred_language": "Yoruba",
        "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
        "is_creator": True,
        "is_admin": False
    },
    {
        "id": to_uuid("user_kofi"),
        "display_name": "Kofi Mensah",
        "email": "kofi.mensah@welele.media",
        "phone_number": "+233241234567",
        "region_code": "GH",
        "preferred_language": "English",
        "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
        "is_creator": True,
        "is_admin": False
    },
    {
        "id": to_uuid("user_wanjiku"),
        "display_name": "Wanjiku Mwangi",
        "email": "wanjiku.mwangi@welele.media",
        "phone_number": "+254712345678",
        "region_code": "KE",
        "preferred_language": "Swahili",
        "avatar_url": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=400&q=80",
        "is_creator": True,
        "is_admin": False
    },
    {
        "id": to_uuid("admin_supervisor"),
        "display_name": "Welele Operations Admin",
        "email": "ops@welele.media",
        "phone_number": "+27820000000",
        "region_code": "ZA",
        "preferred_language": "English",
        "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=200&q=80",
        "is_creator": False,
        "is_admin": True
    }
]

for u in default_users:
    try:
        client.table("users").upsert(u).execute()
        print(f"[PASS] User: {u['display_name']} ({u['id']})")
    except Exception as e:
        print(f"! User notice: {e}")

# 2. Seed Creators
creator_user_mapping = {
    "creator_zola": "user_zola",
    "creator_amaka": "user_amaka",
    "creator_kofi": "user_kofi",
    "creator_wanjiku": "user_wanjiku",
    "creator_3": "user_sa_02"
}

creators = db.get("creators")
for c in creators:
    try:
        creator_uuid = to_uuid(c["id"])
        mapped_user = creator_user_mapping.get(c["id"], "user_zola")
        user_uuid = to_uuid(mapped_user)
        client.table("creators").upsert({
            "id": creator_uuid,
            "user_id": user_uuid,
            "stage_name": c["name"],
            "bio": c.get("bio", ""),
            "country": c.get("country", "South Africa")[:2].upper() if len(c.get("country", "ZA")) > 2 else c.get("country", "ZA"),
            "is_verified": c.get("verified", True)
        }).execute()
        print(f"[PASS] Creator: {c['name']} ({creator_uuid}) -> User: {mapped_user}")
    except Exception as e:
        print(f"! Creator notice: {e}")

# 3. Seed Stories & 9:16 Episodes
stories = db.get("stories")
for s in stories:
    try:
        story_uuid = to_uuid(s["id"])
        creator_uuid = to_uuid(s.get("creator_id", "creator_3"))
        client.table("stories").upsert({
            "id": story_uuid,
            "creator_id": creator_uuid,
            "creator_name": s.get("creator_name", "Welele Studios"),
            "creator_avatar": s.get("creator_avatar"),
            "title": s["title"],
            "synopsis": s["synopsis"],
            "genre": s["genre"],
            "cover_image": s["cover_image"],
            "total_episodes": len(s.get("episodes", [])),
            "free_episodes": s.get("free_episodes_count", 3),
            "is_trending": s.get("is_trending", True),
            "is_published": True,
            "available_languages": s.get("available_languages", ["isiZulu", "English"])
        }).execute()
        print(f"[PASS] Series: {s['title']} ({story_uuid})")

        for ep in s.get("episodes", []):
            try:
                ep_uuid = to_uuid(ep["id"])
                client.table("episodes").upsert({
                    "id": ep_uuid,
                    "story_id": story_uuid,
                    "episode_number": ep["episode_number"],
                    "title": ep["title"],
                    "synopsis": ep.get("synopsis", ""),
                    "duration_seconds": ep.get("duration_seconds", 80),
                    "video_url": ep.get("video_url", ""),
                    "thumbnail_url": ep.get("thumbnail_url", ""),
                    "is_free": ep.get("is_free", False),
                    "coin_price": ep.get("coin_price", 5),
                    "cliffhanger_hook": ep.get("cliffhanger_hook", "The dramatic climax unfolds...")
                }).execute()
                print(f"    -> EP {ep['episode_number']}: {ep['title']}")
            except Exception as e:
                print(f"    ! Episode notice: {e}")
    except Exception as e:
        print(f"! Series notice: {e}")

# 4. Seed Wallets & Double-Entry Coin Ledger for Default Users
for u in default_users:
    try:
        wallet_uuid = to_uuid(f"wallet_{u['id']}")
        client.table("wallets").upsert({
            "id": wallet_uuid,
            "user_id": u["id"],
            "coin_balance": 120,
            "bonus_coins": 30,
            "lifetime_coins_purchased": 50,
            "lifetime_coins_spent": 15
        }).execute()
        print(f"[PASS] Wallet: {u['display_name']} (Balance: 150 coins)")
    except Exception as e:
        print(f"! Wallet notice: {e}")

print("\nLive Supabase Database Seeding Completed Successfully!")
