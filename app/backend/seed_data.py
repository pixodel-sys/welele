"""
Welele Media™ — Authentic African Micro-Drama Catalog & Seed Data
Featuring Vibrant South African, Nigerian, Ghanaian & Kenyan Original Stories.
"""

from database import db
from repositories.series_repository import series_repository

# ============================================================================
# CANONICAL CREATOR ROSTER
# ============================================================================
DEFAULT_CREATORS = [
    {
        "id": "creator_zola",
        "name": "Zola Dlamini",
        "handle": "@zola_cinemas",
        "bio": "Johannesburg crime & dynasty showrunner. Master of the 60-second Mzansi cliffhanger.",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
        "country": "South Africa",
        "verified": True,
        "followers_count": 420000,
        "total_views": 8420000,
        "coin_earnings": 284000,
        "payout_balance": 1890.00
    },
    {
        "id": "creator_amaka",
        "name": "Amaka Okafor",
        "handle": "@amaka_films",
        "bio": "Lagos-based romance & billionaire microdrama director. Creator of high-stakes African stories.",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
        "country": "Nigeria",
        "verified": True,
        "followers_count": 380000,
        "total_views": 6910000,
        "coin_earnings": 215000,
        "payout_balance": 1430.00
    },
    {
        "id": "creator_kofi",
        "name": "Kofi Mensah & Studio Accra",
        "handle": "@kofi_accra",
        "bio": "Afrofuturist action, heist thrillers, and young adult drama across West Africa.",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
        "country": "Ghana",
        "verified": True,
        "followers_count": 265000,
        "total_views": 4820000,
        "coin_earnings": 142000,
        "payout_balance": 945.00
    },
    {
        "id": "creator_wanjiku",
        "name": "Wanjiku Mwangi",
        "handle": "@wanjiku_tales",
        "bio": "Nairobi high-society romance & modern relationship drama. Stories that move hearts.",
        "avatar": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=400&q=80",
        "country": "Kenya",
        "verified": True,
        "followers_count": 210000,
        "total_views": 3950000,
        "coin_earnings": 98000,
        "payout_balance": 650.00
    }
]

# ============================================================================
# CANONICAL AFRICAN MICRODRAMA SERIES CATALOG
# Synchronized with SeriesRepository & Frontend mockData
# ============================================================================
DEFAULT_STORIES = series_repository.list_feed()

# ============================================================================
# CANONICAL USERS
# ============================================================================
DEFAULT_USERS = [
    {
        "id": "user_sa_01",
        "name": "Sipho Dlamini",
        "email": "sipho.dlamini@welele.media",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80",
        "country": "ZA",
        "coin_balance": 150,
        "is_creator": False
    },
    {
        "id": "user_sa_02",
        "name": "Lerato Khumalo",
        "email": "lerato.khumalo@welele.media",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
        "country": "ZA",
        "coin_balance": 280,
        "is_creator": True
    }
]

def seed_database_if_empty(force: bool = False):
    feed = series_repository.list_feed()
    db.set("creators", DEFAULT_CREATORS)
    db.set("stories", feed)
    db.set("users", DEFAULT_USERS)
    print(f"[SEED] Successfully seeded/synchronized {len(feed)} African microdrama series and {len(DEFAULT_CREATORS)} creators!")

if __name__ == "__main__":
    seed_database_if_empty(force=True)
