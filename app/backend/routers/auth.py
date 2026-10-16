"""
Welele Media™ — Multi-Role Auth & User Service Router
Handles Viewer Phone OTP, Guest Sessions, Creator Showrunner Login,
Enterprise Admin 2FA, Session Introspection, and emits comprehensive AUTH domain audit events.
"""

import os
import hmac
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from database import db
from config import settings
from services.ledger_service import ledger_service
from services.audit_service import audit_service
from services.rbac_service import (
    create_access_token,
    get_current_user,
    require_authenticated_user
)

import logging
from services.sms_service import sms_service

logger = logging.getLogger("welele.auth")

router = APIRouter(prefix="/auth", tags=["Auth & RBAC Identity"])

class PhoneAuthRequest(BaseModel):
    phone_number: str
    region_code: Optional[str] = "ZA"
    display_name: Optional[str] = None
    preferred_language: Optional[str] = "isiZulu"

class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp_code: str
    display_name: Optional[str] = "Welele Viewer"
    region_code: Optional[str] = "ZA"

class GuestAuthRequest(BaseModel):
    device_id: Optional[str] = None
    region_code: Optional[str] = "ZA"

class CreatorLoginRequest(BaseModel):
    creator_id: str
    studio_pin: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class AdminLoginRequest(BaseModel):
    admin_key: str
    email: Optional[str] = "ops@welele.media"
    two_factor_code: Optional[str] = None

@router.post("/phone/send-otp")
def send_phone_otp(req: PhoneAuthRequest):
    """Generates and dispatches an authentic SMS OTP via SMSPortal for phone login."""
    code, sms_sent, err_msg = sms_service.generate_otp(
        phone_number=req.phone_number,
        region_code=req.region_code or "ZA"
    )
    
    env = (settings.ENVIRONMENT or "").lower()
    is_prod = env in ("production", "prod")

    # In production, fail closed with honest 502 Bad Gateway if carrier SMS delivery failed
    if is_prod and not sms_sent:
        logger.error("[send_phone_otp] SMS delivery failed in production for %s: %s", req.phone_number, err_msg)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"SMS Gateway Error: {err_msg or 'Failed to deliver SMS to carrier.'}"
        )

    resp = {
        "status": "success",
        "message": f"Verification code sent to {req.phone_number}",
        "phone_number": req.phone_number,
        "region_code": req.region_code or "ZA",
        "sms_dispatched": sms_sent
    }
    
    if err_msg and not sms_sent:
        logger.warning("[send_phone_otp] SMS notice for %s: %s", req.phone_number, err_msg)
        resp["warning"] = err_msg

    # In development and staging environments, supply demo_hint so QA and testing are never blocked
    if not is_prod:
        if not sms_sent:
            resp["demo_hint"] = f"{code} (SMS: {err_msg})"
        else:
            resp["demo_hint"] = f"OTP: {code}"
            
    return resp

@router.post("/phone/verify-otp")
def verify_phone_otp(req: VerifyOtpRequest):
    """Verifies OTP, issues a signed JWT with ROLE_VIEWER, and records an AUTH audit event."""
    is_valid, msg = sms_service.verify_otp(
        phone_number=req.phone_number,
        submitted_code=req.otp_code,
        region_code=req.region_code or "ZA"
    )
    
    env = (settings.ENVIRONMENT or "").lower()
    is_prod = env in ("production", "prod")

    # Allow test harness bypass code '5542' strictly in automated unit test environment (ENVIRONMENT=test)
    if not is_valid and env == "test" and req.otp_code == "5542":
        is_valid = True
        
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg or "Invalid or expired verification code."
        )

    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    
    # Initialize wallet with promotional coins if not existing
    ledger_service.create_wallet_for_user(user_id, initial_coins=50)
    
    token = create_access_token(
        user_id=user_id,
        role="viewer",
        phone=req.phone_number,
        market=req.region_code or "ZA"
    )

    audit_service.record_trust_event(
        domain="AUTH",
        event_type="auth.login",
        actor_id=user_id,
        actor_role="viewer",
        target_type="user_session",
        target_id=user_id,
        after_state={"phone": req.phone_number, "market": req.region_code or "ZA", "role": "viewer"},
        metadata={"method": "sms_otp", "carrier_region": req.region_code or "ZA"}
    )
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "name": req.display_name or "Welele Viewer",
            "phone": req.phone_number,
            "role": "viewer",
            "coins": 50,
            "market": req.region_code or "ZA"
        }
    }

@router.post("/guest")
def guest_login(req: GuestAuthRequest):
    """Issues an anonymous guest trial token bound to device fingerprint and records audit event."""
    guest_id = f"guest_{uuid.uuid4().hex[:8]}"
    ledger_service.create_wallet_for_user(guest_id, initial_coins=25)
    
    token = create_access_token(
        user_id=guest_id,
        role="viewer",
        market=req.region_code or "ZA",
        kyc_status="GUEST"
    )

    audit_service.record_trust_event(
        domain="AUTH",
        event_type="auth.guest_session",
        actor_id=guest_id,
        actor_role="viewer",
        target_type="guest_session",
        target_id=guest_id,
        after_state={"market": req.region_code or "ZA", "device_id": req.device_id},
        metadata={"onboarding": "frictionless_trial"}
    )
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": guest_id,
            "name": "Guest Viewer",
            "role": "viewer",
            "coins": 25,
            "market": req.region_code or "ZA"
        },
        "wallet": {
            "balance": 25,
            "coin_balance": 25,
            "bonus_coins": 0
        }
    }

@router.post("/creator/login")
def creator_login(req: CreatorLoginRequest):
    """Authenticates an African Showrunner / Production Studio account and issues a ROLE_CREATOR JWT."""
    creator_id = req.creator_id
    if not creator_id:
        raise HTTPException(status_code=400, detail="Creator ID is required")
        
    creators = db.get("creators")
    creator = next((c for c in creators if c.get("id") == creator_id), None)
    
    # Secure check: Verify against stored studio PIN/pass or configured studio key
    expected_pin = creator.get("studio_pin") if creator else None
    configured_key = os.getenv("CREATOR_STUDIO_KEY")
    supplied_credential = req.studio_pin or req.password
    
    is_valid = False
    if expected_pin and req.studio_pin and hmac.compare_digest(str(req.studio_pin), str(expected_pin)):
        is_valid = True
    elif configured_key and supplied_credential and hmac.compare_digest(str(supplied_credential), str(configured_key)):
        is_valid = True
    elif not settings.IS_PRODUCTION_OR_STAGING and settings.ENVIRONMENT in ("development", "test") and (req.studio_pin == "1234" or req.password == "welele_dev_pass"):
        # Explicitly allowed ONLY in non-staging local development / test mock environments
        is_valid = True

    if not is_valid:
        audit_service.record_trust_event(
            domain="AUTH",
            event_type="auth.failed_login",
            actor_id=creator_id,
            actor_role="creator",
            target_type="creator_account",
            target_id=creator_id,
            metadata={"reason": "Invalid studio PIN or password"}
        )
        raise HTTPException(status_code=401, detail="Invalid Showrunner Studio PIN or credentials.")

    user_id = f"usr_{creator_id}"
    token = create_access_token(
        user_id=user_id,
        role="creator",
        creator_id=creator_id,
        phone="+27828912345",
        market="ZA",
        kyc_status="VERIFIED"
    )

    audit_service.record_trust_event(
        domain="AUTH",
        event_type="auth.login",
        actor_id=user_id,
        actor_role="creator",
        target_type="creator_workstation",
        target_id=creator_id,
        after_state={"creator_id": creator_id, "role": "creator", "kyc_status": "VERIFIED"},
        metadata={"method": "studio_pin", "studio": creator.get("stage_name", "Studio") if creator else "Studio"}
    )
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "creator_id": creator_id,
            "name": creator.get("stage_name", "Creator") if creator else "Creator",
            "studio_name": creator.get("stage_name", "Studio") if creator else "Studio",
            "role": "creator",
            "kyc_status": "VERIFIED"
        }
    }

@router.post("/admin/login")
def admin_login(req: AdminLoginRequest):
    """Authenticates platform executive/operations account and issues a ROLE_ADMIN JWT."""
    master_key = settings.ADMIN_MASTER_KEY
    expected_2fa = settings.ADMIN_2FA_CODE

    # Fail closed: If ADMIN_MASTER_KEY is not configured in the environment, reject all admin login attempts
    if not master_key or not master_key.strip():
        audit_service.record_trust_event(
            domain="AUTH",
            event_type="auth.failed_login",
            actor_id=req.email or "ops@welele.media",
            actor_role="admin",
            target_type="admin_console",
            target_id="enterprise_ops",
            metadata={"reason": "Admin authentication unconfigured (fail closed)"}
        )
        raise HTTPException(
            status_code=500 if settings.IS_PRODUCTION_OR_STAGING else 401,
            detail="Admin authentication is disabled: ADMIN_MASTER_KEY environment variable is not configured."
        )

    is_key_valid = bool(req.admin_key and master_key and hmac.compare_digest(str(req.admin_key), str(master_key)))
    
    # 2FA Enforcement: When configured or in production/staging, 2FA must match strictly
    if settings.IS_PRODUCTION_OR_STAGING or expected_2fa:
        is_2fa_valid = bool(expected_2fa and req.two_factor_code and hmac.compare_digest(str(req.two_factor_code), str(expected_2fa)))
    else:
        is_2fa_valid = True  # Optional only in local dev if ADMIN_2FA_CODE is unset

    if not (is_key_valid and is_2fa_valid):
        audit_service.record_trust_event(
            domain="AUTH",
            event_type="auth.failed_login",
            actor_id=req.email or "ops@welele.media",
            actor_role="admin",
            target_type="admin_console",
            target_id="enterprise_ops",
            metadata={"reason": "Invalid admin master key or 2FA token"}
        )
        raise HTTPException(status_code=401, detail="Invalid Administrator Key or 2FA Token.")

    admin_id = "admin_supervisor"
    token = create_access_token(
        user_id=admin_id,
        role="admin",
        email=req.email or "ops@welele.media",
        market="ALL",
        kyc_status="SUPER_ADMIN"
    )

    audit_service.record_trust_event(
        domain="AUTH",
        event_type="auth.login",
        actor_id=admin_id,
        actor_role="admin",
        target_type="admin_console",
        target_id="global_operations",
        after_state={"role": "admin", "kyc_status": "SUPER_ADMIN"},
        metadata={"method": "enterprise_2fa", "operator": req.email or "ops@welele.media"}
    )
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": admin_id,
            "name": "Welele Operations Admin",
            "email": req.email or "ops@welele.media",
            "role": "admin",
            "permissions": ["*"]
        }
    }

@router.get("/me")
def get_current_user_profile(user: dict = Depends(get_current_user)):
    wallet = ledger_service.get_or_create_wallet(user.get("sub", "guest_anonymous"))
    balance = ledger_service.get_balance(user.get("sub", "guest_anonymous"))
    coins = balance.get("total_usable_coins", 0)
    
    return {
        "user_id": user.get("sub"),
        "role": user.get("role", "viewer"),
        "market": user.get("market", "ZA"),
        "creator_id": user.get("creator_id"),
        "permissions": user.get("permissions", []),
        "kyc_status": user.get("kyc_status", "GUEST"),
        "is_authenticated": user.get("is_authenticated", False),
        "coins": coins
    }
