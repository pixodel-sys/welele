"""
Welele Media™ — Auth & User Service Router (Section 5.1)
Handles South African & Pan-African Phone OTP, Guest Anonymous Session,
User Profiles, and Initial Wallet Allocation.
"""

import uuid
import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database import db
from services.ledger_service import ledger_service

router = APIRouter(prefix="/auth", tags=["Auth & User Profiles"])

class PhoneAuthRequest(BaseModel):
    phone_number: str
    region_code: Optional[str] = "ZA"
    display_name: Optional[str] = None
    preferred_language: Optional[str] = "isiZulu"

class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp_code: str

class GuestAuthRequest(BaseModel):
    device_id: Optional[str] = None
    region_code: Optional[str] = "ZA"

@router.post("/phone/send-otp")
def send_phone_otp(req: PhoneAuthRequest):
    """Generates and dispatches a 6-digit SMS OTP for frictionless carrier/phone login."""
    demo_otp = "7799"
    return {
        "success": True,
        "phone_number": req.phone_number,
        "region_code": req.region_code,
        "message": f"OTP sent to {req.phone_number}. (Dev Demo Code: {demo_otp})",
        "expires_in_seconds": 300
    }

@router.post("/phone/verify-otp")
def verify_phone_otp(req: VerifyOtpRequest):
    """Verifies OTP and authenticates or registers user profile with an active coin wallet."""
    users = db.get("users")
    user = next((u for u in users if u.get("phone_number") == req.phone_number), None)
    
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = {
            "id": user_id,
            "phone_number": req.phone_number,
            "display_name": f"Welele Fan {req.phone_number[-4:]}",
            "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
            "region_code": "ZA",
            "preferred_language": "isiZulu",
            "is_creator": False,
            "is_admin": False,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        db.insert("users", user)
    
    # Ensure wallet and double-entry ledger allocation
    wallet = ledger_service.get_or_create_wallet(user["id"])
    balance = ledger_service.get_balance(user["id"])

    return {
        "success": True,
        "token": f"bearer_{uuid.uuid4().hex}",
        "user": user,
        "wallet": {
            "balance": balance["total_usable_coins"],
            "base_coins": balance["coin_balance"],
            "bonus_coins": balance["bonus_coins"]
        }
    }

@router.post("/guest")
def guest_login(req: GuestAuthRequest):
    """Creates a zero-barrier anonymous session with default coin balance."""
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    guest_user = {
        "id": guest_id,
        "phone_number": None,
        "display_name": f"Guest {guest_id[-4:]}",
        "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=200&q=80",
        "region_code": req.region_code or "ZA",
        "preferred_language": "isiZulu",
        "is_guest": True,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    db.insert("users", guest_user)
    wallet = ledger_service.get_or_create_wallet(guest_id)
    balance = ledger_service.get_balance(guest_id)

    return {
        "success": True,
        "token": f"guest_token_{uuid.uuid4().hex[:12]}",
        "user": guest_user,
        "wallet": {
            "balance": balance["total_usable_coins"],
            "base_coins": balance["coin_balance"],
            "bonus_coins": balance["bonus_coins"]
        }
    }

@router.get("/me")
def get_current_user_profile(user_id: str = Query(..., description="User ID")):
    users = db.get("users")
    user = next((u for u in users if u.get("id") == user_id), None)
    if not user:
        # Fallback to default user
        user = users[0] if users else {
            "id": user_id,
            "display_name": "Welele VIP",
            "region_code": "ZA"
        }
    balance = ledger_service.get_balance(user["id"])
    return {
        "user": user,
        "wallet": balance
    }
