"""
Welele Media™ — SMS OTP Service & SMSPortal Integration
Provides secure OTP generation, phone number normalization, SMSPortal REST API dispatch,
expiring memory storage with brute-force protection and rate limiting.
"""

import os
import re
import hmac
import time
import base64
import secrets
import logging
import urllib.request
import urllib.error
import json
from typing import Dict, Any, Optional, Tuple
from config import settings

logger = logging.getLogger("welele.sms")

# In-memory store for OTPs:
# normalized_phone -> { "code": str, "expires_at": float, "attempts": int, "last_sent_at": float }
_otp_store: Dict[str, Dict[str, Any]] = {}

OTP_EXPIRY_SECONDS = 300  # 5 minutes
MAX_VERIFY_ATTEMPTS = 5
MIN_RESEND_INTERVAL_SECONDS = 30


def normalize_phone_number(phone: str, region_code: str = "ZA") -> str:
    """
    Normalizes phone numbers into E.164 digits without leading '+' or punctuation.
    Supports South Africa (ZA), Nigeria (NG), and generic international formats.
    Examples:
      '082 123 4567' (ZA) -> '27821234567'
      '+27 82 123 4567' -> '27821234567'
      '080 1234 5678' (NG) -> '2348012345678'
    """
    if not phone:
        return ""
    # Strip any whitespace, parentheses, dashes, plus signs
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone.strip())
    
    region = (region_code or "ZA").upper()
    
    if region == "ZA":
        if cleaned.startswith("0") and len(cleaned) == 10:
            return "27" + cleaned[1:]
        elif cleaned.startswith("27") and len(cleaned) == 11:
            return cleaned
        elif len(cleaned) == 9 and cleaned.startswith(("6", "7", "8")):
            return "27" + cleaned
    elif region == "NG":
        if cleaned.startswith("0") and len(cleaned) == 11:
            return "234" + cleaned[1:]
        elif cleaned.startswith("234") and len(cleaned) == 13:
            return cleaned

    # Fallback: remove leading zero if country code was not prepended
    if cleaned.startswith("00"):
        return cleaned[2:]
    return cleaned


class SMSService:
    def __init__(self):
        self.api_url = "https://rest.smsportal.com/v3/BulkMessages"

    @property
    def client_id(self) -> str:
        return getattr(settings, "SMSPORTAL_CLIENT_ID", "") or os.getenv("SMSPORTAL_CLIENT_ID", "")

    @property
    def api_secret(self) -> str:
        return getattr(settings, "SMSPORTAL_API_SECRET", "") or os.getenv("SMSPORTAL_API_SECRET", "")

    def is_configured(self) -> bool:
        return bool(self.client_id and self.api_secret)

    def _get_auth_header(self) -> str:
        credentials = f"{self.client_id}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    def send_sms_via_smsportal(self, destination: str, content: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Dispatches an SMS message through SMSPortal REST API v3.
        Returns: (success: bool, error_message: Optional[str], status_code: Optional[int])
        """
        if not self.is_configured():
            logger.warning("[SMSService] SMSPortal credentials not configured. SMS will not be dispatched to carrier.")
            return False, "SMSPortal credentials not configured", None

        payload = {
            "messages": [
                {
                    "content": content,
                    "destination": destination
                }
            ]
        }
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
            "User-Agent": "WeleleMedia-OTP/1.0"
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.api_url, data=req_data, headers=headers, method="POST")
            
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_body = response.read().decode("utf-8")
                status_code = response.status
                logger.info("[SMSService] SMSPortal dispatch success to %s: HTTP %s", destination, status_code)
                return True, None, status_code

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error("[SMSService] SMSPortal HTTP Error %s: %s", e.code, err_body)
            return False, f"SMSPortal HTTP {e.code}: {err_body}", e.code
        except Exception as ex:
            logger.error("[SMSService] SMSPortal connection error: %s", ex)
            return False, str(ex), None

    def generate_otp(self, phone_number: str, region_code: str = "ZA") -> Tuple[str, bool, Optional[str]]:
        """
        Generates a 4-digit OTP, stores it with TTL, and dispatches it via SMSPortal.
        Returns (otp_code, sms_sent_successfully, error_message).
        """
        normalized = normalize_phone_number(phone_number, region_code)
        now = time.time()

        # Rate-limiting check: enforce minimum interval between SMS requests
        existing = _otp_store.get(normalized)
        if existing:
            last_sent = existing.get("last_sent_at", 0)
            if now - last_sent < MIN_RESEND_INTERVAL_SECONDS:
                wait_seconds = int(MIN_RESEND_INTERVAL_SECONDS - (now - last_sent))
                return existing["code"], False, f"Please wait {wait_seconds}s before requesting a new OTP."

        # Generate a cryptographically secure 4-digit OTP
        code = f"{secrets.randbelow(9000) + 1000}"

        _otp_store[normalized] = {
            "code": code,
            "expires_at": now + OTP_EXPIRY_SECONDS,
            "attempts": 0,
            "last_sent_at": now
        }

        message = f"Your Welele verification code is {code}. Valid for 5 minutes. Enjoy South Africa's finest micro-dramas!"
        
        # Dispatch via SMSPortal
        sms_sent, err_msg, _ = self.send_sms_via_smsportal(destination=normalized, content=message)
        
        return code, sms_sent, err_msg

    def verify_otp(self, phone_number: str, submitted_code: str, region_code: str = "ZA") -> Tuple[bool, str]:
        """
        Verifies the user's submitted OTP code.
        Validates expiration, attempt counters, and constant-time match.
        """
        normalized = normalize_phone_number(phone_number, region_code)
        entry = _otp_store.get(normalized)

        if not entry:
            return False, "No OTP request found for this phone number. Please request a new code."

        now = time.time()
        if now > entry.get("expires_at", 0):
            _otp_store.pop(normalized, None)
            return False, "Verification code has expired. Please request a new one."

        if entry.get("attempts", 0) >= MAX_VERIFY_ATTEMPTS:
            _otp_store.pop(normalized, None)
            return False, "Too many incorrect attempts. Please request a new verification code."

        stored_code = entry.get("code", "")
        # Constant-time comparison to prevent timing attacks
        if hmac.compare_digest(stored_code.strip(), submitted_code.strip()):
            # One-time use: invalidate immediately on success
            _otp_store.pop(normalized, None)
            return True, "Verification successful."

        # Increment attempts on mismatch
        entry["attempts"] = entry.get("attempts", 0) + 1
        remaining = MAX_VERIFY_ATTEMPTS - entry["attempts"]
        return False, f"Invalid verification code. {remaining} attempt(s) remaining."


# Global singleton
sms_service = SMSService()
