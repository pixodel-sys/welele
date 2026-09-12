import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from database import db
from schemas.monetization_schemas import (
    TopupRequest,
    UnlockEpisodeRequest,
    SendGiftRequest,
    PayoutRequest,
    AirtimeChargeRequest,
    AirtimePassRequest,
    USSDSessionRequest
)
from services.payment_service import payment_service

router = APIRouter(prefix="/monetization", tags=["Monetization & Welele Coins"])

@router.get("/packs")
def get_coin_packs(currency: Optional[str] = "USD"):
    packs = payment_service.get_coin_packs(currency)
    gifts = payment_service.VIRTUAL_GIFTS
    sa_carriers = payment_service.SA_AIRTIME_CARRIERS
    sa_passes = payment_service.SA_AIRTIME_PASSES
    return {
        "packs": packs,
        "gifts": gifts,
        "currencies": list(payment_service.EXCHANGE_RATES.keys()),
        "sa_airtime_carriers": sa_carriers,
        "sa_airtime_passes": sa_passes
    }

@router.get("/airtime/carriers")
def get_airtime_carriers():
    return {
        "country": "ZA",
        "currency": "ZAR",
        "carriers": payment_service.SA_AIRTIME_CARRIERS
    }

@router.get("/airtime/passes")
def get_airtime_passes():
    return {
        "country": "ZA",
        "currency": "ZAR",
        "passes": payment_service.SA_AIRTIME_PASSES
    }

@router.get("/airtime/detect-carrier")
def detect_carrier(phone: str = Query(..., description="South African phone number")):
    carrier = payment_service.detect_carrier_from_phone(phone)
    return {
        "phone": phone,
        "carrier": carrier
    }

@router.post("/airtime/charge")
def charge_airtime(req: AirtimeChargeRequest):
    result = payment_service.process_airtime_charge(
        user_id=req.user_id,
        carrier_id=req.carrier_id,
        phone_number=req.phone_number,
        charge_type=req.charge_type,
        target_id=req.target_id,
        amount_zar=req.amount_zar,
        coins_equivalent=req.coins_equivalent or 0
    )

    # Handle specific charge types
    if req.charge_type == "episode_unlock" and req.series_id:
        stories = db.get("stories")
        story = next((s for s in stories if s["id"] == req.series_id), None)
        if story:
            creator_id = story.get("creator_id")
            creators = db.get("creators")
            creator = next((c for c in creators if c["id"] == creator_id), None)
            if creator:
                new_earnings = creator.get("coin_earnings", 0) + (req.coins_equivalent or 5)
                db.update("creators", creator_id, {"coin_earnings": new_earnings})

    # Save transaction record
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

@router.post("/airtime/ussd")
def simulate_ussd(req: USSDSessionRequest):
    session = payment_service.simulate_ussd_session(req.phone_number, req.ussd_string)
    return {
        "success": True,
        "session": session
    }

@router.post("/topup")
def topup_coins(req: TopupRequest):
    result = payment_service.process_topup(
        user_id=req.user_id,
        pack_id=req.pack_id,
        payment_method=req.payment_method,
        phone=req.phone_or_account
    )
    
    db.insert("transactions", {
        "id": result["transaction_id"],
        "user_id": req.user_id,
        "type": "topup",
        "coins": result["coins_credited"],
        "amount_local": req.amount_local,
        "currency": req.currency,
        "payment_method": req.payment_method,
        "timestamp": result["timestamp"]
    })
    
    return {
        "success": True,
        "message": f"Successfully purchased {result['coins_credited']} Welele Coins via {req.payment_method.replace('_', ' ').title()}!",
        "transaction": result
    }

@router.post("/unlock")
def unlock_episode(req: UnlockEpisodeRequest):
    stories = db.get("stories")
    story = next((s for s in stories if s["id"] == req.series_id), None)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    episode = next((ep for ep in story.get("episodes", []) if ep["id"] == req.episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Credit creator
    creator_id = story.get("creator_id")
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == creator_id), None)
    if creator:
        new_earnings = creator.get("coin_earnings", 0) + req.coins
        db.update("creators", creator_id, {"coin_earnings": new_earnings})
        
    db.insert("transactions", {
        "id": f"tx_unlock_{uuid.uuid4().hex[:8]}",
        "user_id": req.user_id,
        "type": "episode_unlock",
        "episode_id": req.episode_id,
        "series_id": req.series_id,
        "coins": req.coins
    })
    
    return {
        "success": True,
        "unlocked_episode_id": req.episode_id,
        "coins_spent": req.coins,
        "message": f"Unlocked Episode {episode.get('episode_number')} of {story.get('title')}!"
    }

@router.post("/gift")
def send_gift(req: SendGiftRequest):
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == req.creator_id), None)
    if creator:
        new_earnings = creator.get("coin_earnings", 0) + req.coin_cost
        db.update("creators", req.creator_id, {"coin_earnings": new_earnings})

    gift_record = {
        "id": f"gift_{uuid.uuid4().hex[:8]}",
        "user_id": req.user_id,
        "creator_id": req.creator_id,
        "series_id": req.series_id,
        "episode_id": req.episode_id,
        "gift_id": req.gift_id,
        "gift_name": req.gift_name,
        "gift_icon": req.gift_icon,
        "coin_cost": req.coin_cost,
        "message": req.message
    }
    db.insert("gifts", gift_record)
    
    return {
        "success": True,
        "message": f"Sent {req.gift_name} {req.gift_icon} to the creator!",
        "gift": gift_record
    }

@router.post("/payout")
def request_payout(req: PayoutRequest):
    from datetime import datetime, timezone
    from services.audit_service import audit_service

    # 1. Idempotency Check
    if req.idempotency_key:
        existing_txs = db.get("transactions")
        match = next((tx for tx in existing_txs if tx.get("idempotency_key") == req.idempotency_key), None)
        if match:
            return {
                "success": True,
                "payout_id": match["id"],
                "is_idempotent_replay": True,
                "transaction": match,
                "message": f"Idempotent replay: Payout of {match.get('amount_local')} {match.get('currency')} is currently {match.get('status')}."
            }

    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == req.creator_id), None)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    available_coins = creator.get("coin_earnings", 0)
    if req.amount_coins <= 0:
        raise HTTPException(status_code=400, detail="Payout amount must be greater than zero.")
    if req.amount_coins > available_coins:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coin balance: Requested {req.amount_coins} coins, but creator only has {available_coins} coins available."
        )

    # 2. Atomically lock / deduct creator coins
    new_balance = available_coins - req.amount_coins
    db.update("creators", req.creator_id, {"coin_earnings": new_balance})

    payout_id = f"payout_{uuid.uuid4().hex[:8]}"
    now_ts = datetime.now(timezone.utc).isoformat()

    tx_record = {
        "id": payout_id,
        "type": "payout",
        "creator_id": req.creator_id,
        "coins": req.amount_coins,
        "amount_local": req.amount_local,
        "currency": req.currency,
        "method": req.payout_method,
        "account": req.account_details,
        "status": "processing",
        "settlement_status": "Settlement Pending (External Rails Unproven)",
        "idempotency_key": req.idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}",
        "created_at": now_ts,
        "updated_at": now_ts
    }
    db.insert("transactions", tx_record)

    # 3. Emit immutable COMMERCE audit event
    audit_service.record_trust_event(
        domain="COMMERCE",
        event_type="commerce.payout_requested",
        actor_id=req.creator_id,
        actor_role="creator",
        target_type="payout_transaction",
        target_id=payout_id,
        before_state={"coin_earnings_before": available_coins},
        after_state={"coin_earnings_after": new_balance, "payout_amount_coins": req.amount_coins, "amount_local": req.amount_local, "currency": req.currency},
        metadata={"payout_method": req.payout_method, "idempotency_key": tx_record["idempotency_key"]}
    )

    return {
        "success": True,
        "payout_id": payout_id,
        "transaction": tx_record,
        "remaining_coin_balance": new_balance,
        "message": f"Payout of {req.amount_local} {req.currency} requested to {req.payout_method}. Settlement status: Pending External Proof."
    }
