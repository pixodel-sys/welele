"""
Welele Media™ — Creator Profile & Tenancy Service (Phase 6O-2)
Manages canonical creator profiles, studio tenancy membership, and migration allowlists.
Preserves 100% compatibility with accepted 6I text creator_id references.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from database import db
from repositories.base_repository import BaseRepository
from data.fixtures.seed_fixtures import DEFAULT_CREATORS

logger = logging.getLogger("welele.creator_tenancy")

# Deterministic namespace UUID helper
def to_uuid(name: str) -> str:
    try:
        uuid.UUID(str(name))
        return str(name)
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))

class CreatorProfileService(BaseRepository):
    def __init__(self):
        super().__init__()
        self._ensure_baseline_profiles()

    def _ensure_baseline_profiles(self):
        """Idempotently seeds baseline creator profiles in local storage if not present."""
        existing_profiles = self.local_get("creator_profiles") or []
        existing_ids = {p["id"] for p in existing_profiles if p.get("id")}

        for c in DEFAULT_CREATORS:
            cid = c["id"]
            if cid not in existing_ids:
                profile = {
                    "id": cid,
                    "owner_user_id": to_uuid(f"user_{cid}"),
                    "legal_name": c.get("name", "Studio Owner"),
                    "display_name": c.get("name", "Studio Owner"),
                    "handle": c.get("handle", f"@{cid}"),
                    "country": c.get("country", "ZA"),
                    "business_type": "individual",
                    "legacy_passkey_enabled": True,  # Grace period allowlist
                    "status": "active"
                }
                self.local_insert("creator_profiles", profile)
                
                # Default workspace membership as owner
                member = {
                    "id": f"mem_{uuid.uuid4().hex[:10]}",
                    "user_id": profile["owner_user_id"],
                    "creator_id": cid,
                    "role": "owner",
                    "status": "active"
                }
                self.local_insert("workspace_members", member)

    def get_profile(self, creator_id: str) -> Optional[Dict[str, Any]]:
        """Resolves a canonical creator profile by creator_id text slug."""
        profiles = self.local_get("creator_profiles") or []
        profile = next((p for p in profiles if p.get("id") == creator_id), None)
        if profile:
            return profile

        # Fallback to DEFAULT_CREATORS fixture if not yet in store
        fixture = next((c for c in DEFAULT_CREATORS if c.get("id") == creator_id), None)
        if fixture:
            new_profile = {
                "id": creator_id,
                "owner_user_id": to_uuid(f"user_{creator_id}"),
                "legal_name": fixture.get("name"),
                "display_name": fixture.get("name"),
                "handle": fixture.get("handle"),
                "country": fixture.get("country", "ZA"),
                "business_type": "individual",
                "legacy_passkey_enabled": True,
                "status": "active"
            }
            self.local_insert("creator_profiles", new_profile)
            return new_profile
        return None

    def is_legacy_passkey_allowed(self, creator_id: str) -> bool:
        """Asserts whether a creator profile is allowlisted for legacy passkey authentication."""
        profile = self.get_profile(creator_id)
        if not profile:
            return False
        return bool(profile.get("legacy_passkey_enabled", False)) and profile.get("status") == "active"

    def get_workspace_membership(self, user_id: str, creator_id: str) -> Optional[Dict[str, Any]]:
        """Validates that a user holds an active membership in the creator studio."""
        members = self.local_get("workspace_members") or []
        match = next(
            (m for m in members if str(m.get("user_id")) in (user_id, to_uuid(user_id)) and m.get("creator_id") == creator_id),
            None
        )
        if match and match.get("status") == "active":
            return match

        # Grace period fallback: If user_id matches creator's owner_user_id or synthetic creator user_id
        profile = self.get_profile(creator_id)
        if profile:
            owner_id = str(profile.get("owner_user_id"))
            if user_id in (owner_id, to_uuid(f"user_{creator_id}"), f"usr_{creator_id}"):
                return {
                    "user_id": user_id,
                    "creator_id": creator_id,
                    "role": "owner",
                    "status": "active"
                }
        return None

creator_profile_service = CreatorProfileService()
