"""
Welele Media™ — Role-Based Access Control (RBAC) & Security Service
Implements JWT Token Generation, Verification, and Route Guards
per Section 4 of docs/RBAC_SECURITY_ARCHITECTURE.md
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
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "role": role,
        "phone": phone,
        "email": email,
        "market": market,
        "creator_id": creator_id,
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")
        
        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET.encode('utf-8'), message, hashlib.sha256).digest()
        
        if not hmac.compare_digest(_b64_decode(sig_b64), expected_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cryptographic signature")
        
        payload = json.loads(_b64_decode(payload_b64).decode('utf-8'))
        
        # Expiry Check
        if payload.get("exp") and int(time.time()) > payload["exp"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
        return payload
    except HTTPException:
        raise
    except Exception as e:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with your phone or credentials."
        )
    return user

def require_role(allowed_roles: List[str]):
    """FastAPI Dependency Guard enforcing role whitelisting."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", "viewer")
        
        # Super-admin bypass
        if user_role == "admin":
            return user
            
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles {allowed_roles}, but session role is '{user_role}'."
            )
        return user
    return role_checker

def require_permission(permission: str):
    """FastAPI Dependency Guard enforcing granular permission capabilities."""
    def perm_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_perms = user.get("permissions", [])
        user_role = user.get("role", "viewer")
        
        if "*" in user_perms or user_role == "admin" or permission in user_perms:
            return user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Missing required permission: '{permission}'."
        )
    return perm_checker
