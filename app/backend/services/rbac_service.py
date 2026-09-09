"""
Welele Media™ — Role-Based Access Control (RBAC) & Trust Guard Service
Implements Cryptographic JWT Token Generation, Verification, Tenant Boundary Enforcement,
and Automatic Security Audit Event Emission (Security & Trust Foundation).
"""

import time
import json
import base64
import hmac
import hashlib
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from services.audit_service import audit_service

security = HTTPBearer(auto_error=False)

JWT_SECRET = getattr(settings, "JWT_SECRET", "welele_production_jwt_secret_key_2026_za_pan_africa")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 60 * 60 * 24 * 7  # 7 Days

# Role Definitions & Default Permission Sets
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "viewer": [
        "stream:episode:free",
        "stream:episode:unlock",
        "wallet:recharge",
        "social:gift:send",
        "social:chat:participate",
    ],
    "creator": [
        "stream:episode:free",
        "stream:episode:unlock",
        "wallet:recharge",
        "social:gift:send",
        "social:chat:participate",
        "series:create",
        "series:update:own",
        "episode:upload",
        "ai:storyforge:execute",
        "analytics:read:own",
        "settlement:payout:request",
    ],
    "admin": [
        "*",  # Super-admin wildcard
        "experience:layout:publish",
        "moderation:queue:review",
        "creator:kyc:approve",
        "ledger:audit:read",
        "series:manage:all",
    ],
}

def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _b64_decode(data: str) -> bytes:
    padding = '=' * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(
    user_id: str,
    role: str = "viewer",
    phone: Optional[str] = None,
    email: Optional[str] = None,
    market: str = "ZA",
    creator_id: Optional[str] = None,
    custom_permissions: Optional[List[str]] = None,
    kyc_status: str = "VERIFIED",
    expires_in: int = JWT_EXPIRATION_SECONDS
) -> str:
    """Generates a cryptographically signed HS256 JWT Token."""
    now = int(time.time())
    permissions = custom_permissions or ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])
    
    # Set default creator_id if creator role
    effective_creator_id = creator_id
    if role == "creator" and not effective_creator_id:
        effective_creator_id = user_id if user_id.startswith("creator_") or user_id.startswith("cr_") else f"cr_{user_id}"

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "phone": phone,
        "email": email,
        "market": market,
        "creator_id": effective_creator_id,
        "permissions": permissions,
        "kyc_status": kyc_status,
        "iat": now,
        "exp": now + expires_in,
        "iss": "welele.media/auth"
    }

    header_b64 = _b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    message = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).digest()
    sig_b64 = _b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> Dict[str, Any]:
    """Verifies cryptographic signature and expiration of JWT."""
    try:
        parts = token.strip().split('.')
        if len(parts) != 3:
            audit_service.record_trust_event(
                domain="SECURITY",
                event_type="security.signature_failure",
                actor_id="anonymous",
                actor_role="unauthenticated",
                target_type="auth_token",
                target_id="malformed_jwt",
                metadata={"reason": "Invalid token structure"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")
        
        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).digest()
        
        if not hmac.compare_digest(_b64_decode(sig_b64), expected_sig):
            audit_service.record_trust_event(
                domain="SECURITY",
                event_type="security.signature_failure",
                actor_id="anonymous",
                actor_role="unauthenticated",
                target_type="auth_token",
                target_id="tampered_signature",
                metadata={"reason": "Cryptographic signature mismatch"}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cryptographic signature")
        
        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))
        
        # Expiry Check
        if payload.get("exp") and int(time.time()) > payload["exp"]:
            audit_service.record_trust_event(
                domain="SECURITY",
                event_type="security.signature_failure",
                actor_id=payload.get("sub", "unknown"),
                actor_role=payload.get("role", "viewer"),
                target_type="auth_token",
                target_id="expired_jwt",
                metadata={"exp": payload.get("exp"), "now": int(time.time())}
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
        audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.signature_failure",
            actor_id="anonymous",
            actor_role="unauthenticated",
            target_type="auth_token",
            target_id="validation_exception",
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token validation failed: {str(e)}")

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    """Extracts and verifies the currently authenticated user session. Defaults to Guest Viewer if unauthenticated."""
    if not credentials or not credentials.credentials:
        # Provide fallback anonymous guest context for frictionless onboarding
        return {
            "sub": "guest_anonymous",
            "role": "viewer",
            "market": "ZA",
            "creator_id": None,
            "permissions": ROLE_PERMISSIONS["viewer"],
            "kyc_status": "GUEST",
            "is_authenticated": False
        }
    
    payload = verify_access_token(credentials.credentials)
    payload["is_authenticated"] = True
    return payload

def require_authenticated_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Requires an explicit authenticated session (rejects anonymous guest)."""
    if not user.get("is_authenticated"):
        audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.permission_denied",
            actor_id="guest_anonymous",
            actor_role="viewer",
            target_type="endpoint",
            target_id="authenticated_route",
            metadata={"reason": "Guest session attempted protected action"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your phone or credentials."
        )
    return user

def require_role(allowed_roles: List[str]):
    """FastAPI Dependency Guard enforcing role whitelisting with automatic audit logging."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", "viewer")
        
        # Super-admin bypass
        if user_role == "admin":
            return user
            
        if user_role not in allowed_roles:
            audit_service.record_trust_event(
                domain="SECURITY",
                event_type="security.permission_denied",
                actor_id=user.get("sub", "anonymous"),
                actor_role=user_role,
                target_type="role_guard",
                target_id=",".join(allowed_roles),
                metadata={"required_roles": allowed_roles, "session_role": user_role}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles {allowed_roles}, but session role is '{user_role}'."
            )
        return user
    return role_checker

def require_permission(permission: str):
    """FastAPI Dependency Guard enforcing granular permission capabilities with audit logging."""
    def perm_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_perms = user.get("permissions", [])
        user_role = user.get("role", "viewer")
        
        if "*" in user_perms or user_role == "admin" or permission in user_perms:
            return user
            
        audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.permission_denied",
            actor_id=user.get("sub", "anonymous"),
            actor_role=user_role,
            target_type="permission_capability",
            target_id=permission,
            metadata={"missing_permission": permission, "user_permissions": user_perms}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Missing required permission: '{permission}'."
        )
    return perm_checker

def enforce_tenant_access(
    auth_user: Dict[str, Any],
    resource_creator_id: Optional[str],
    domain: str = "CONTENT",
    action: str = "mutate"
) -> bool:
    """
    Enforces strict Creator Tenant Isolation.
    A creator can only read/mutate their own IP/series/episodes/analytics.
    Admins hold universal administrative override.
    """
    user_role = auth_user.get("role", "viewer")
    if user_role == "admin":
        return True

    user_sub = auth_user.get("sub")
    user_creator_id = auth_user.get("creator_id") or user_sub

    if not resource_creator_id or (user_creator_id != resource_creator_id and user_sub != resource_creator_id):
        audit_service.record_trust_event(
            domain="SECURITY",
            event_type="security.ownership_violation",
            actor_id=user_sub or "unknown",
            actor_role=user_role,
            target_type="creator_tenant_boundary",
            target_id=resource_creator_id or "unknown_resource",
            metadata={
                "actor_creator_id": user_creator_id,
                "resource_creator_id": resource_creator_id,
                "domain": domain,
                "action": action
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant boundary violation: Creator '{user_creator_id}' is not authorized to {action} resources owned by '{resource_creator_id}'."
        )

    return True
