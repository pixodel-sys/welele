"""
Welele Media™ — Regional Payments & Carrier Dispatcher Router (Section 5.1 & Pillars 5/6)
Handles Airtime DCB (Vodacom, MTN, Cell C, Telkom), Ozow Instant EFT, Paystack Cards,
1Voucher redemption, and Idempotent Webhooks.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Header, Request
from pydantic import BaseModel
from services.payment_service import payment_service
from services.ledger_service import ledger_service
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
def process_airtime_direct_charge(req: AirtimeChargePayload):
    """Executes 1-Tap Direct Carrier Billing (DCB) micro-charge deducted from SIM airtime balance."""
    result = payment_service.process_airtime_charge(
        user_id=req.user_id,
        carrier_id=req.carrier_id,
        phone_number=req.phone_number,
        charge_type=req.charge_type,
        target_id=req.target_id,
        amount_zar=req.amount_zar,
        coins_equivalent=req.coins_equivalent or 0
    )

    # If charging for coin pack, credit the wallet & ledger
    if req.charge_type in ["coin_pack", "topup"] and req.coins_equivalent and req.coins_equivalent > 0:
        ledger_service.credit_coins(
            user_id=req.user_id,
            base_coins=req.coins_equivalent,
            bonus_coins=0,
            transaction_type="AIRTIME_TOPUP",
            reference_id=result["reference"],
            description=f"Purchased via {result['carrier_name']} Airtime (R{req.amount_zar:.2f})"
        )

    # Save payment transaction record
    db.insert("transactions", {
        "id": result["transaction_id"],
        "user_id": req.user_id,
        "type": f"airtime_{req.charge_type}",
        "carrier": result["carrier_name"],
        "phone": req.phone_number,
        "amount_zar": req.amount_zar,
        "coins": req.coins_equivalent or 0,
        "target_id": req.target_id,
        "reference": result["reference"],
        "timestamp": result["timestamp"]
    })

    return {
        "success": True,
        "message": f"Deducted R{req.amount_zar:.2f} via {result['carrier_name']} Airtime!",
        "transaction": result
    }

@router.post("/checkout")
def initiate_checkout(req: TopupCheckoutPayload):
    provider = payment_service.get_provider(req.region)
    result = provider.process_checkout(
        user_id=req.user_id,
        pack_id=req.pack_id,
        channel=req.channel,
        phone_or_email=req.phone_or_email
    )

    # Credit coins upon successful settlement
    coins = result.get("coins_credited", 0)
    if coins > 0:
        ledger_service.credit_coins(
            user_id=req.user_id,
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

@router.get("/events")
def get_payment_events_log(limit: int = 50):
    """Returns persistent audit log of all received payment provider webhook receipts."""
    from services.commerce_service import commerce_service
    events = commerce_service.get_payment_events(limit=limit)
    return {"total_events": len(events), "events": events}

