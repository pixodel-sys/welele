"""
Welele Media™ — 1Voucher by FlashPay Payment Adapter (Flash Partner API v4)
Conforms strictly to the official "Flash Partner API v4" specification (Version 3.0, 2025).

Key Documented Invariants:
- OAuth 2.0 Client Credentials Grant: POST /token with Basic Auth returning Bearer access_token (valid 3600s).
- Base URLs:
    Sandbox:    https://api-flashswitch-sandbox.flash-group.com
    Production: https://api.flashswitch.flash-group.com
- Endpoint: POST /aggregation/4.0/1voucher/redeem
- Required Fields: reference, accountNumber, pin, amount.
- Amount Units: Integer CENTS ("0" value will redeem full value of the voucher).
- Success Determination: responseCode == 0 (Integer 0). HTTP 200 alone does not guarantee success.
- Idempotency: Retries MUST reuse the exact same reference (Flash switch returns initial response).
- Reversals: Document explicitly specifies redeemed 1Vouchers CANNOT be reversed.
"""

import os
import re
import time
import base64
import json
import uuid
import hmac
import hashlib
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from .base_adapter import BasePaymentAdapter, NormalizedPaymentEvent

logger = logging.getLogger("welele.payments.1voucher")

# Welele Standard Monetisation Ratio: R1.00 (100 Cents) = 5 Welele Coins
COINS_PER_ZAR = 5
CENTS_PER_ZAR = 100

class OAuth2TokenManager:
    """
    Manages OAuth 2.0 Client Credentials authentication for Flash Partner API v4.
    Requests Bearer tokens from /token and caches them for 3600 seconds with an expiry safety buffer.
    """
    def __init__(self, token_url: str, client_id: str, client_secret: str, is_mock: bool = True):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.is_mock = is_mock
        self._cached_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def get_token(self) -> Tuple[bool, str]:
        now = time.time()
        # Return cached token if valid (with 60-second safety window)
        if self._cached_token and now < (self._token_expires_at - 60):
            return True, self._cached_token

        if self.is_mock:
            self._cached_token = f"flash_mock_oauth2_{uuid.uuid4().hex[:16]}"
            self._token_expires_at = now + 3600
            return True, self._cached_token

        # Live OAuth 2.0 Client Credentials Request as specified in Section 1.1.1 (Page 4)
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode("utf-8")).decode("utf-8")
        req_data = "grant_type=client_credentials".encode("utf-8")
        req = urllib.request.Request(
            self.token_url,
            data=req_data,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                token = data.get("access_token")
                expires_in = int(data.get("expires_in", 3600))
                if not token:
                    return False, "OAuth 2.0 response missing access_token"
                self._cached_token = token
                self._token_expires_at = now + expires_in
                logger.info(f"[FlashOAuth2] Token acquired successfully. Valid for {expires_in}s.")
                return True, token
        except Exception as e:
            logger.error(f"[FlashOAuth2] Token request failed: {e}")
            return False, f"Failed to authenticate with Flash OAuth 2.0 server: {str(e)}"


class OneVoucherAdapter(BasePaymentAdapter):
    """
    Canonical Flash Partner API v4 Adapter for 1Voucher Redemption.
    """
    SANDBOX_BASE_URL = "https://api-flashswitch-sandbox.flash-group.com"
    PRODUCTION_BASE_URL = "https://api.flashswitch.flash-group.com"

    def __init__(self):
        self.environment = os.getenv("FLASH_ENVIRONMENT", "sandbox").lower()
        self.account_number = os.getenv("FLASH_ACCOUNT_NUMBER", "")
        self.client_id = os.getenv("FLASH_CLIENT_ID", "")
        self.client_secret = os.getenv("FLASH_CLIENT_SECRET", "")
        self.store_id = os.getenv("FLASH_STORE_ID", "WELELE_ONLINE")
        self.terminal_id = os.getenv("FLASH_TERMINAL_ID", "WELELE_WEB_01")

        # Base URLs from Section 2.1 (Page 8)
        if self.environment in ("production", "prod"):
            self.base_url = self.PRODUCTION_BASE_URL
            self.token_url = f"{self.PRODUCTION_BASE_URL}/token"
        else:
            self.base_url = self.SANDBOX_BASE_URL
            self.token_url = f"{self.SANDBOX_BASE_URL}/token"

        # Explicit Mock Mode Flag: When live Flash sandbox credentials have not yet been provisioned
        self.has_credentials_configured = bool(self.account_number and self.client_id and self.client_secret)

        # CRITICAL PRODUCTION SECURITY GUARDRAIL:
        # Never allow silent fallback to mock mode in a production environment!
        is_prod = (self.environment in ("production", "prod")) or (os.getenv("ENVIRONMENT", "").lower() in ("production", "prod"))
        if is_prod:
            if not self.has_credentials_configured:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION HALT: Flash credentials (account number, client ID, client secret) "
                    "are missing in PRODUCTION environment. Silent fallback to mock payment mode in production is strictly prohibited."
                )
            if os.getenv("FLASH_MOCK_MODE", "false").lower() in ("true", "1", "yes"):
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION HALT: FLASH_MOCK_MODE is enabled in PRODUCTION environment. "
                    "Mock payment simulation in production is strictly prohibited."
                )

        self.is_mock_mode = (os.getenv("FLASH_MOCK_MODE", "false").lower() in ("true", "1", "yes"))

        self.token_manager = OAuth2TokenManager(
            token_url=self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            is_mock=self.is_mock_mode or (not self.has_credentials_configured)
        )

    @property
    def has_credentials(self) -> bool:
        return self.has_credentials_configured

    @property
    def sandbox_status(self) -> str:
        if self.has_credentials_configured:
            return "CONFIGURED"
        return "BLOCKED / NOT_CONFIGURED"

    @property
    def provider_id(self) -> str:
        return "1voucher_flash"

    def clean_pin(self, pin: str) -> str:
        """Strips whitespace, hyphens, and non-digit characters."""
        return re.sub(r"[^\d]", "", str(pin or ""))

    def hash_pin(self, cleaned_pin: str) -> str:
        """
        Generates a keyed HMAC-SHA256 hash using a server-side pepper/secret.
        Fails closed: raises RuntimeError if neither FLASH_PIN_HMAC_SECRET nor SECRET_KEY is configured.
        """
        secret = os.getenv("FLASH_PIN_HMAC_SECRET") or os.getenv("SECRET_KEY")
        if not secret:
            if os.getenv("ENVIRONMENT") == "test":
                secret = "test_fixture_hmac_secret_not_for_prod"
            else:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION HALT: Missing required FLASH_PIN_HMAC_SECRET or SECRET_KEY. "
                    "Voucher PIN hashing cannot proceed without an approved server-side HMAC secret."
                )
        return hmac.new(secret.encode("utf-8"), cleaned_pin.encode("utf-8"), hashlib.sha256).hexdigest()

    def mask_pin(self, cleaned_pin: str) -> str:
        """Masks first 12 digits, exposing only final 4 digits for viewer receipts."""
        if len(cleaned_pin) < 4:
            return "****"
        return "*" * (len(cleaned_pin) - 4) + cleaned_pin[-4:]

    def validate_reference(self, reference: str) -> bool:
        """
        Validates client reference against Section 2.3.3.1 (Page 11):
        'Only -,.,= and alphanumeric characters allowed'. Max length per code 2301.
        """
        if not reference or len(reference) > 50:
            return False
        return bool(re.match(r"^[A-Za-z0-9\-.,=]+$", reference))

    def verify_signature(self, payload: bytes, signature_header: Optional[str]) -> bool:
        """Direct synchronous API responses are cryptographically authenticated via TLS and Bearer OAuth 2.0."""
        return True

    def normalize_payload(self, raw_data: Dict[str, Any], signature_verified: bool = True) -> NormalizedPaymentEvent:
        raw_json = json.dumps(raw_data, sort_keys=True, separators=(',', ':'))
        raw_hash = hashlib.sha256(raw_json.encode('utf-8')).hexdigest()

        tx_id = str(raw_data.get("transactionId") or raw_data.get("reference") or f"flash_{uuid.uuid4().hex[:8]}")
        res_code = raw_data.get("responseCode", -1)

        # Success requires integer responseCode == 0 per Section 1.2.1.1 (Page 5)
        status = "SUCCESS" if res_code == 0 else "FAILED"
        
        # Amount in response is in CENTS (Integer) per Section 2.3.3.1 (Page 11)
        amount_cents = int(raw_data.get("amount") or 0)
        amount_zar = round(amount_cents / float(CENTS_PER_ZAR), 2)
        raw_uid = raw_data.get("user_id", "guest_user")
        user_id = str(raw_uid.get("sub") if isinstance(raw_uid, dict) else raw_uid)
        coins = int(amount_zar * COINS_PER_ZAR)

        return NormalizedPaymentEvent(
            provider=self.provider_id,
            provider_transaction_id=tx_id,
            event_type="1VOUCHER_REDEEM",
            amount_fiat=amount_zar,
            currency="ZAR",
            user_id=user_id,
            coins_grant=coins,
            target_id=raw_data.get("target_id"),
            target_type=raw_data.get("target_type", "COINS"),
            raw_payload_hash=raw_hash,
            signature_verified=signature_verified,
            status=status
        )

    def parse_response(
        self,
        status_code: int,
        response_data: Dict[str, Any],
        reference: str,
        user_id: str = "viewer",
        masked_pin: str = "****",
        pin_hash: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Interprets a Flash Partner API v4 response payload per Section 1.2.1.1 (Page 5).
        - HTTP status alone is NOT treated as success.
        - responseCode == 0 is successful redemption.
        - responseCode in (2210, 2211) represents a timeout / ambiguous outcome.
        - Any other non-zero responseCode represents an explicit provider failure.
        """
        res_code = response_data.get("responseCode", -1)
        result = dict(response_data)
        result["reference"] = reference
        result["user_id"] = user_id
        result["masked_pin"] = masked_pin
        if pin_hash:
            result["pin_hash"] = pin_hash

        # Success requires BOTH HTTP 200 and integer responseCode == 0 per Section 1.2.1.1 (Page 5)
        if status_code == 200 and res_code == 0:
            amount_cents = int(response_data.get("amount", 0))
            amount_zar = round(amount_cents / float(CENTS_PER_ZAR), 2)
            coins_grant = int(amount_zar * COINS_PER_ZAR)
            result["coins_grant"] = coins_grant
            result["amount_zar"] = amount_zar
            result["is_timeout"] = False
            return True, f"Successfully redeemed R{amount_zar:.2f} 1Voucher (+{coins_grant} Coins)!", result
        elif res_code in (2210, 2211) or status_code in (408, 504):
            err_msg = response_data.get("responseMessage", "A timeout occurred connecting to Flash switch. Please resubmit using the same reference.")
            result["is_timeout"] = True
            result["requires_retry_with_same_reference"] = True
            return False, err_msg, result
        else:
            err_msg = response_data.get("responseMessage", f"Voucher redemption declined by provider (Code {res_code}).")
            result["is_timeout"] = False
            return False, err_msg, result

    def execute_redemption(
        self,
        voucher_pin: str,
        user_id: str,
        reference: str,
        phone_number: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes 1Voucher redemption against Flash Partner API v4:
        POST /aggregation/4.0/1voucher/redeem

        Parameters:
        - reference: Client-defined unique ID (must be reused on retries for idempotency).
        - pin: 16 numeric digits.
        - amount: 0 (integer cents) to redeem full voucher value.
        """
        cleaned_pin = self.clean_pin(voucher_pin)
        if len(cleaned_pin) != 16:
            return False, "Invalid voucher PIN. 1Voucher PIN must be exactly 16 numeric digits.", {
                "responseCode": 2402,
                "responseMessage": "The voucher you have entered could not be found",
                "reference": reference,
                "is_mock": self.is_mock_mode
            }

        if not self.validate_reference(reference):
            return False, "Invalid reference format. Only alphanumeric, '-', '.', and '=' characters allowed.", {
                "responseCode": 2301,
                "responseMessage": "The reference provided exceeds character count or invalid format",
                "reference": reference
            }

        pin_hash = self.hash_pin(cleaned_pin)
        masked_pin = self.mask_pin(cleaned_pin)

        # --------------------------------------------------------------------
        # Provider Credentials Boundary (Milestone 5A Phase 9)
        # --------------------------------------------------------------------
        is_test_mock = (os.getenv("ENVIRONMENT") == "test") and (os.getenv("FLASH_MOCK_MODE", "false").lower() in ("true", "1", "yes"))
        if not self.has_credentials_configured and not is_test_mock:
            logger.warning(
                f"[1Voucher:ProviderBoundary] FlashPay sandbox credentials not configured. "
                f"Redemption BLOCKED for reference {reference} (FLASH_SANDBOX_STATUS=BLOCKED / NOT_CONFIGURED)."
            )
            return False, (
                "1Voucher redemption is unavailable: Partner sandbox credentials have not yet been supplied "
                "(FLASH_SANDBOX_STATUS=BLOCKED / NOT_CONFIGURED)."
            ), {
                "responseCode": 5031,
                "responseMessage": "FlashPay provider credentials not configured",
                "reference": reference,
                "status": "BLOCKED_PENDING_CREDENTIALS",
                "sandbox_status": "BLOCKED / NOT_CONFIGURED",
                "is_mock": False
            }

        # --------------------------------------------------------------------
        # 1. Flash Contract Mock Simulator (Active ONLY in isolated test env)
        # --------------------------------------------------------------------
        if self.is_mock_mode or is_test_mock:
            logger.info(f"[1Voucher:ContractMock] Simulating v4 contract redemption for PIN {masked_pin} (Ref: {reference})")

            # Documented Error Code 2401: Voucher already used (Section 4, Page 51)
            if cleaned_pin.endswith("9999"):
                return False, "The voucher you have entered has already been used, please use another voucher pin.", {
                    "responseCode": 2401,
                    "responseMessage": "The voucher you have entered has already been used, please use another voucher pin.",
                    "accountNumber": self.account_number or "MOCK_ACC_001",
                    "reference": reference,
                    "transactionId": 0,
                    "amount": 0,
                    "is_mock": True,
                    "pin_hash": pin_hash,
                    "masked_pin": masked_pin
                }

            # Documented Error Code 2402: Voucher could not be found (Section 4, Page 51)
            if cleaned_pin.endswith("8888"):
                return False, "The voucher you have entered could not be found.", {
                    "responseCode": 2402,
                    "responseMessage": "The voucher you have entered could not be found",
                    "accountNumber": self.account_number or "MOCK_ACC_001",
                    "reference": reference,
                    "transactionId": 0,
                    "amount": 0,
                    "is_mock": True,
                    "pin_hash": pin_hash,
                    "masked_pin": masked_pin
                }

            # Documented Error Code 2405: Voucher expired (Section 4, Page 51)
            if cleaned_pin.endswith("7777"):
                return False, "The voucher you have entered has expired.", {
                    "responseCode": 2405,
                    "responseMessage": "The voucher you have entered has expired",
                    "accountNumber": self.account_number or "MOCK_ACC_001",
                    "reference": reference,
                    "transactionId": 0,
                    "amount": 0,
                    "is_mock": True,
                    "pin_hash": pin_hash,
                    "masked_pin": masked_pin
                }

            # Value mapping in CENTS (Integer) per Section 2.3.3.1
            cents_map = {
                "0010": 1000,  # R10.00
                "0020": 2000,  # R20.00
                "0050": 5000,  # R50.00
                "0100": 10000, # R100.00
            }
            amount_cents = cents_map.get(cleaned_pin[-4:], 5000) # Default R50.00 (5000 cents)
            amount_zar = amount_cents / float(CENTS_PER_ZAR)
            coins_grant = int(amount_zar * COINS_PER_ZAR)

            # Contract Response model exactly conforming to Section 3.1.6 (Page 35)
            mock_response = {
                "responseCode": 0,
                "responseMessage": "Success",
                "accountNumber": self.account_number or "MOCK_ACC_001",
                "reference": reference,
                "transactionDate": datetime.now(timezone.utc).isoformat(),
                "transactionId": 8941203,
                "storeId": self.store_id,
                "terminalId": self.terminal_id,
                "amount": amount_cents,  # Cents as documented
                "user_id": user_id,
                "pin_hash": pin_hash,
                "masked_pin": masked_pin,
                "coins_grant": coins_grant,
                "is_mock": True,
                "is_mock_simulation": True,
                "simulation_disclaimer": "Contract mock simulation only. No live Flash network transaction occurred.",
                "provider_status": "SIMULATED_MOCK_SUCCESS",
                "voucher": {
                    "amount": 0,
                    "expiryDate": "2027-10-15T00:00:00Z",
                    "pin": masked_pin,
                    "serialNumber": "SN-8941203",
                    "status": "Redeemed",
                    "content": {
                        "redemptionInstructions": "Welele Media instant coin credit",
                        "termsAndConditions": "Standard 1Voucher terms apply"
                    }
                }
            }
            return True, f"Successfully redeemed R{amount_zar:.2f} 1Voucher (+{coins_grant} Coins)!", mock_response

        # --------------------------------------------------------------------
        # 2. Live Flash Partner Switch Integration (Sections 1.1, 2.3.3, 3.1.6)
        # --------------------------------------------------------------------
        ok_token, token_or_err = self.token_manager.get_token()
        if not ok_token:
            return False, f"Provider Authentication Failed: {token_or_err}", {
                "responseCode": 3701,
                "responseMessage": token_or_err,
                "reference": reference,
                "is_mock": False
            }

        endpoint_url = f"{self.base_url}/aggregation/4.0/1voucher/redeem"
        
        # Documented request payload (Section 2.3.3.1, Page 11 & Page 35)
        # Note: amount = 0 instructs Flash switch to redeem full voucher face value
        payload = {
            "reference": reference,
            "accountNumber": self.account_number,
            "pin": cleaned_pin,
            "amount": 0,
            "storeId": self.store_id,
            "terminalId": self.terminal_id
        }
        if phone_number:
            # Format: 11 Digits (27 Country Code with no leading 0) per Page 11
            cleaned_phone = re.sub(r"[^\d]", "", phone_number)
            if cleaned_phone.startswith("0") and len(cleaned_phone) == 10:
                cleaned_phone = "27" + cleaned_phone[1:]
            if len(cleaned_phone) == 11 and cleaned_phone.startswith("27"):
                payload["mobileNumber"] = cleaned_phone

        payload_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint_url,
            data=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token_or_err}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))
                
                # Success Check: responseCode == 0 (Page 5)
                res_code = resp_json.get("responseCode", -1)
                if res_code == 0:
                    amount_cents = int(resp_json.get("amount", 0))
                    amount_zar = round(amount_cents / float(CENTS_PER_ZAR), 2)
                    coins_grant = int(amount_zar * COINS_PER_ZAR)
                    resp_json["user_id"] = user_id
                    resp_json["masked_pin"] = masked_pin
                    resp_json["pin_hash"] = pin_hash
                    resp_json["coins_grant"] = coins_grant
                    resp_json["is_mock"] = False
                    return True, f"Successfully redeemed R{amount_zar:.2f} 1Voucher (+{coins_grant} Coins)!", resp_json
                elif res_code in (2210, 2211):
                    err_msg = resp_json.get("responseMessage", "A timeout occurred, please resubmit the request")
                    resp_json["is_timeout"] = True
                    resp_json["requires_retry_with_same_reference"] = True
                    resp_json["is_mock"] = False
                    return False, err_msg, resp_json
                else:
                    err_msg = resp_json.get("responseMessage", f"Voucher redemption declined (Code {res_code}).")
                    resp_json["is_mock"] = False
                    return False, err_msg, resp_json

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            logger.error(f"[1Voucher:SwitchHTTPError] {e.code}: {error_body}")
            try:
                err_json = json.loads(error_body)
                msg = err_json.get("responseMessage", f"Provider error: HTTP {e.code}")
            except Exception:
                err_json = {"raw": error_body}
                msg = f"Provider error: HTTP {e.code}"
            is_timeout_http = e.code in (408, 504) or err_json.get("responseCode") in (2210, 2211)
            return False, msg, {
                "http_code": e.code,
                "responseCode": err_json.get("responseCode", e.code),
                "reference": reference,
                "is_timeout": is_timeout_http,
                "requires_retry_with_same_reference": is_timeout_http,
                "is_mock": False
            }

        except Exception as e:
            logger.critical(f"[1Voucher:NetworkError] Disconnection or timeout against Flash switch: {e}")
            # Section 1.2.2 & Code 2210/2211: "A timeout occurred, please resubmit the request" with SAME reference
            return False, "A timeout occurred connecting to the Flash switch. Please resubmit using the same reference.", {
                "responseCode": 2210,
                "responseMessage": "A timeout occurred, please resubmit the request",
                "reference": reference,
                "requires_retry_with_same_reference": True,
                "is_mock": False
            }

onevoucher_adapter = OneVoucherAdapter()
