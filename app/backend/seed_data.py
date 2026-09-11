"""
Welele Media™ — Authentic African Micro-Drama Catalog & Seed Service
Strictly entity-level idempotent seeding. Protects all runtime data from deletion or overwrite.
"""

from config import settings
from database import db
from repositories.series_repository import series_repository
from data.fixtures.seed_fixtures import DEFAULT_CREATORS, DEFAULT_USERS

def seed_database_if_empty(force: bool = False):
    """
    Idempotently ensures baseline catalog fixtures exist without overwriting runtime data.
    Only executes if force=True or ENABLE_STARTUP_SEED=True in settings.
    """
    if not (force or settings.ENABLE_STARTUP_SEED):
        print("[SEED] Startup seeding skipped (ENABLE_STARTUP_SEED is disabled). Runtime data protected.")
        return

    print("[SEED] Running entity-level idempotent seed synchronization...")

    # 1. Idempotent Creators Seeding
    existing_creators = db.get("creators")
    existing_c_ids = {c.get("id") for c in existing_creators if c.get("id")}
    new_creators_count = 0
    for creator in DEFAULT_CREATORS:
        if creator["id"] not in existing_c_ids:
            db.insert("creators", creator)
            new_creators_count += 1

    # 2. Idempotent Users Seeding
    existing_users = db.get("users")
    existing_u_ids = {u.get("id") for u in existing_users if u.get("id")}
    new_users_count = 0
    for user in DEFAULT_USERS:
        if user["id"] not in existing_u_ids:
            db.insert("users", user)
            new_users_count += 1

    # 3. Idempotent Series & Episodes Seeding via Repository
    series_repository.seed_if_missing()

    print(
        f"[SEED] Complete. Inserted {new_creators_count} new creators, {new_users_count} new users. "
        "Existing creator drafts, published series, and transactions were preserved intact."
    )

if __name__ == "__main__":
    seed_database_if_empty(force=True)
