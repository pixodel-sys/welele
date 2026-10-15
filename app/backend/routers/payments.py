"""
Welele Media™ — Regional Payments & Carrier Dispatcher Router (Section 5.1 & Pillars 5/6)
Handles Airtime DCB (Vodacom, MTN, Cell C, Telkom), Ozow Instant EFT, Paystack Cards,
1Voucher redemption, and Idempotent Webhooks.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Header, Request, Depends
from pydantic import BaseModel
from services.payment_service import payment_service
from services.ledger_service import ledger_service
from services.rbac_service import require_authenticated_user, require_role
from database import db

router = APIRouter(prefix="/payments", tags=["Regional Payments & Carrier Billing"])

class AirtimeChargePayload(BaseModel):
    user_id: str
    carrier_id: str
    phone_number: str
    charge_type: str  # 'episode_unlock', 'coin_pack', 'story_pass'
    target_id: str
    series_id: Optional[str] = None
    amount_zar: float
    coins_equivalent: Optional[int] = 0

class TopupCheckoutPayload(BaseModel):
    user_id: str
    pack_id: str
    channel: str  # 'airtime_dcb', 'ozow_eft', 'card_paystack', 'voucher_1voucher', 'momo_mtn', 'mpesa'
    phone_or_email: str
    region: Optional[str] = "ZA"

class VoucherRedeemPayload(BaseModel):
    voucher_pin: str
    phone_number: Optional[str] = None
    idempotency_key: Optional[str] = None
    user_id: Optional[str] = None

class WebhookPayload(BaseModel):
    event_type: str
    reference: str
    user_id: str
    amount: float
    currency: str
    status: str
    coins_grant: int

@router.get("/channels")
def get_supported_payment_channels(region: Optional[str] = "ZA"):
    provider = payment_service.get_provider(region)
    return {
        "region": provider.region_code,
        "currency": provider.currency,
        "channels": provider.get_supported_channels()
    }

@router.get("/airtime/carriers")
def get_airtime_carriers():
    return {
        "country": "ZA",
        "currency": "ZAR",
        "carriers": payment_service.SA_AIRTIME_CARRIERS
    }

@router.get("/airtime/detect")
def detect_airtime_carrier(phone: str = Query(..., description="South African Phone Number")):
    carrier = payment_service.detect_carrier_from_phone(phone)
    return {
        "phone": phone,
        "carrier": carrier
    }

@router.post("/airtime/charge")
def process_airtime_direct_charge(
    req: AirtimeChargePayload,
    auth_user: dict = Depends(require_authenticated_user)
):
    """Executes 1-Tap Direct Carrier Billing (DCB) micro-charge deducted from SIM airtime balance."""
    target_user_id = auth_user["sub"]
    user_role = auth_user.get("role", "viewer")
    if req.user_id and user_role == "admin":
        target_user_id = req.user_id
    elif req.user_id and req.user_id != auth_user["sub"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot initiate carrier charges on behalf of another user."
        )

    result = payment_service.process_airtime_charge(
        user_id=target_user_id,
        carrier_id=req.carrier_id,
        phone_number=req.phone_number,
        charge_type=req.charge_type,
        target_id=req.target_id,
        amount_zar=req.amount_zar,
        coins_equivalent=req.coins_equivalent or 0
    )

    # 1. Authoritative payment failure check
    if result.get("status") == "failed":
        db.insert("transactions", {
            "id": result["transaction_id"],
            "user_id": target_user_id,
            "type": f"airtime_{req.charge_type}",
            "carrier": result.get("carrier_name", req.carrier_id),
            "phone": req.phone_number,
            "amount_zar": req.amount_zar,
            "coins": 0,
            "target_id": req.target_id,
            "status": "FAILED",
            "error": result.get("error", "Declined"),
            "reference": result.get("reference"),
            "timestamp": result["timestamp"]
        })
        raise HTTPException(
            status_code=402,
            detail=result.get("error", "Payment could not be completed by carrier.")
        )

    # 2. Process Successful Payment Entitlements
    if req.charge_type in ["coin_pack", "topup"] and req.coins_equivalent and req.coins_equivalent > 0:
        ledger_service.credit_coins(
            user_id=target_user_id,
            base_coins=req.coins_equivalent,
            bonus_coins=0,
            transaction_type="AIRTIME_TOPUP",
            reference_id=result["reference"],
            description=f"Purchased via {result['carrier_name']} Airtime (R{req.amount_zar:.2f})"
        )
    elif req.charge_type == "episode_unlock":
        existing_unlocks = db.get("unlocked_episodes") or []
        already = any(u.get("user_id") == target_user_id and u.get("episode_id") == req.target_id for u in existing_unlocks)
        if not already:
            db.insert("unlocked_episodes", {
                "user_id": target_user_id,
                "episode_id": req.target_id,
                "series_id": req.series_id,
                "unlocked_at": result["timestamp"],
                "payment_reference": result["reference"]
            })

    # Save payment transaction record
    db.insert("transactions", {
        "id": result["transaction_id"],
        "user_id": target_user_id,
        "type": f"airtime_{req.charge_type}",
        "carrier": result["carrier_name"],
        "phone": req.phone_number,
        "amount_zar": req.amount_zar,
        "coins": req.coins_equivalent or 0,
        "target_id": req.target_id,
        "status": "COMPLETED",
        "reference": result["reference"],
        "timestamp": result["timestamp"]
    })

    from services.audit_service import audit_service
    audit_service.record_trust_event(
        domain="COMMERCE",
        event_type="payment.airtime_charge",
        actor_id=target_user_id,
        actor_role=user_role,
        target_type=req.charge_type,
        target_id=req.target_id,
        after_state={"status": "completed", "amount_zar": req.amount_zar, "transaction_id": result["transaction_id"]},
        metadata={"carrier": result["carrier_name"], "reference": result["reference"]}
    )

    return {
        "success": True,
        "message": f"Deducted R{req.amount_zar:.2f} via {result['carrier_name']} Airtime!",
        "transaction": result
    }

@router.post("/checkout")
def initiate_checkout(
    req: TopupCheckoutPayload,
    auth_user: dict = Depends(require_authenticated_user)
):
    target_user_id = auth_user["sub"]
    user_role = auth_user.get("role", "viewer")
    if req.user_id and user_role == "admin":
        target_user_id = req.user_id
    elif req.user_id and req.user_id != auth_user["sub"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot initiate checkout on behalf of another user."
        )

    provider = payment_service.get_provider(req.region)
    result = provider.process_checkout(
        user_id=target_user_id,
        pack_id=req.pack_id,
        channel=req.channel,
        phone_or_email=req.phone_or_email
    )

    # Credit coins upon successful settlement
    coins = result.get("coins_credited", 0)
    if coins > 0:
        ledger_service.credit_coins(
            user_id=target_user_id,
            base_coins=coins,
            bonus_coins=0,
            transaction_type="TOPUP",
            reference_id=result["reference"],
            description=f"Top-up via {req.channel}"
        )

    return {
        "success": True,
        "message": f"Topup complete via {req.channel}!",
        "transaction": result
    }

@router.post("/webhook/{provider_id}")
async def process_provider_webhook(
    provider_id: str,
    request: Request,
    x_welele_signature: Optional[str] = Header(None, alias="X-Welele-Signature")
):
    """
    Cryptographically authenticated, idempotent webhook receiver for regional payment providers.
    """
    from services.commerce_service import commerce_service
    body_bytes = await request.body()
    try:
        body_json = await request.json()
    except Exception:
        body_json = {}

    success, message, data = commerce_service.process_webhook(
        provider_id=provider_id,
        raw_body=body_bytes,
        raw_json=body_json,
        signature_header=x_welele_signature
    )

    if not success:
        raise HTTPException(status_code=400, detail={"error": message, "details": data})

    return {"status": "accepted", "message": message, "data": data}

@router.post("/webhook")
async def process_legacy_webhook(
    request: Request,
    x_welele_signature: Optional[str] = Header(None, alias="X-Welele-Signature")
):
    """
    Generic webhook router defaulting to Vodacom DCB.
    """
    return await process_provider_webhook("vodacom_dcb", request, x_welele_signature)

@router.get("/events", dependencies=[Depends(require_role(["admin"]))])
def get_payment_events_log(limit: int = 50):
    """Returns persistent audit log of all received payment provider webhook receipts (Admin Only)."""
    from services.commerce_service import commerce_service
    events = commerce_service.get_payment_events(limit=limit)
    return {"total_events": len(events), "events": events}

@router.get("/1voucher/status")
def get_1voucher_provider_status():
    """
    Returns the FlashPay / 1Voucher provider configuration boundary status (Milestone 5A).
    Reports FLASH_SANDBOX_STATUS without exposing any secrets.
    """
    from services.payment_adapters.onevoucher_adapter import onevoucher_adapter
    return {
        "provider": "1voucher_flash",
        "flash_sandbox_status": onevoucher_adapter.sandbox_status,
        "environment": onevoucher_adapter.environment,
        "sandbox_base_url": onevoucher_adapter.SANDBOX_BASE_URL,
        "production_base_url": onevoucher_adapter.PRODUCTION_BASE_URL,
        "token_endpoint": onevoucher_adapter.token_url,
        "redeem_endpoint": f"{onevoucher_adapter.base_url}/aggregation/4.0/1voucher/redeem",
        "timeout_seconds": 15,
        "credentials_configured": onevoucher_adapter.has_credentials_configured,
        "message": (
            "FlashPay sandbox credentials not yet provisioned. Integration ready; "
            "verification blocked pending partner sandbox access."
            if not onevoucher_adapter.has_credentials_configured else "FlashPay credentials configured."
        )
    }

@router.post("/1voucher/redeem")
@router.post("/voucher/redeem")
def redeem_1voucher_pin(
    req: VoucherRedeemPayload,
    auth_user: dict = Depends(require_authenticated_user)
):
    """
    Synchronously redeems a 16-digit 1Voucher cash PIN against FlashPay switch,
    clears the transaction via double-entry accounting, and instantly credits user coins.
    """
    if not req.voucher_pin or not str(req.voucher_pin).strip():
        raise HTTPException(
            status_code=400,
            detail="Voucher PIN is required."
        )

    target_user_id = auth_user["sub"]
    user_role = auth_user.get("role", "viewer")
    if req.user_id and user_role == "admin":
        target_user_id = req.user_id
    elif req.user_id and req.user_id != auth_user["sub"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You cannot redeem vouchers on behalf of another user."
        )

    from services.commerce_service import commerce_service
    ok, message, data = commerce_service.redeem_1voucher(
        user_id=target_user_id,
        voucher_pin=req.voucher_pin,
        phone_number=req.phone_number,
        idempotency_key=req.idempotency_key
    )

    if not ok:
        raise HTTPException(
            status_code=400,
            detail={"error": message, "details": data}
        )

    return {
        "success": True,
        "message": message,
        "transaction": data
    }



