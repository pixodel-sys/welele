"""
Welele Media™ — Admin Profile & Staff Identity Service (Phase 6O-6)
Manages individual administrative staff identities, permissions, and maker-checker separation of duties.
"""

import uuid
from typing import Optional, Dict, Any, List
from database import db
from repositories.base_repository import BaseRepository

class AdminProfileService(BaseRepository):
    def __init__(self):
        super().__init__()
        self._seed_default_staff_profiles()

    def _seed_default_staff_profiles(self):
        existing = self.local_get("admin_profiles")
        if not existing:
            default_profiles = [
                {
                    "id": "adm_prof_preparer",
                    "user_id": "adm_preparer_01",
                    "staff_email": "preparer@welele.media",
                    "full_name": "Finance Preparer",
                    "department": "Finance Operations",
                    "role": "admin",
                    "permissions": ["payment_run.create", "payment_run.read"],
                    "is_active": True
                },
                {
                    "id": "adm_prof_supervisor",
                    "user_id": "adm_supervisor_02",
                    "staff_email": "supervisor@welele.media",
                    "full_name": "Finance Supervisor",
                    "department": "Treasury",
                    "role": "admin_supervisor",
                    "permissions": ["payment_run.approve", "payment_run.cancel", "payment_run.read"],
                    "is_active": True
                },
                {
                    "id": "adm_prof_ops",
                    "user_id": "adm_ops_global",
                    "staff_email": "ops@welele.media",
                    "full_name": "Global Operations Executive",
                    "department": "Executive Operations",
                    "role": "admin",
                    "permissions": ["*"],
                    "is_active": True
                }
            ]
            for p in default_profiles:
                self.local_insert("admin_profiles", p)

    def resolve_admin_id(self, email: Optional[str] = None) -> str:
        """
        Resolves individual administrative identity from staff email.
        Ensures each staff member has a distinct persistent identity for dual-control separation.
        """
        if not email:
            return "adm_ops_global"
        
        email_clean = email.strip().lower()
        profiles = self.local_get("admin_profiles") or []
        for p in profiles:
            if p.get("staff_email", "").lower() == email_clean:
                return str(p.get("user_id") or p.get("id"))
                
        # Generate deterministic staff identifier if not pre-seeded
        username = email_clean.split("@")[0].replace(".", "_")
        return f"adm_{username}"

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        profiles = self.local_get("admin_profiles") or []
        for p in profiles:
            if p.get("user_id") == user_id or p.get("id") == user_id or p.get("staff_email") == user_id:
                return p
        return None

    def is_active_admin(self, user_id: str) -> bool:
        prof = self.get_profile(user_id)
        if prof:
            return bool(prof.get("is_active", True))
        return user_id.startswith("adm_") or user_id in ["admin_supervisor", "admin_operator", "admin_system"]

admin_profile_service = AdminProfileService()
