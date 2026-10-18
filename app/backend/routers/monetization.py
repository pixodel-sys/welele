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
import logging
from decimal import Decimal
from services.payment_service import payment_service
from services.commercial_accounting_service import commercial_accounting_service
from schemas.commercial_accounting_schemas import RevenueEventSource, RevenueEventType

logger = logging.getLogger("welele.monetization")

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

    # Authoritative Commercial Accounting (Workstream 6I-E)
    # Airtime unlock uses actual monetary consideration (req.amount_zar) per Section 11
    if req.charge_type == "episode_unlock" and req.series_id:
        try:
            commercial_accounting_service.process_commercial_event(
                series_id=req.series_id,
                episode_id=req.target_id,
                source=RevenueEventSource.AIRTIME_UNLOCK,
                source_transaction_id=result["transaction_id"],
                event_type=RevenueEventType.AIRTIME_CHARGE,
                gross_amount=Decimal(str(req.amount_zar)),
                currency="ZAR",
                idempotency_key=f"airtime_unlock_{result['transaction_id']}",
                metadata={
                    "user_id": req.user_id,
                    "carrier": result.get("carrier_name"),
                    "coins_equivalent": req.coins_equivalent or 0
                }
            )
        except Exception as e:
            logger.error(f"[CommercialAccounting] Airtime commercial event error: {e}")

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
    
    # Authoritative Commercial Accounting (Workstream 6I-E)
    tx_id = f"tx_unlock_{uuid.uuid4().hex[:8]}"
    try:
        commercial_accounting_service.process_episode_unlock(
            series_id=req.series_id,
            episode_id=req.episode_id,
            viewer_id=req.user_id,
            coin_price=req.coins,
            source_transaction_id=tx_id,
            idempotency_key=f"ep_unlock_{req.series_id}_{req.episode_id}_{req.user_id}_{tx_id}"
        )
    except Exception as e:
        logger.error(f"[CommercialAccounting] Error processing unlock accounting: {e}")
        
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
    # Authoritative Commercial Accounting (Workstream 6I-E)
    # Per Section 12: Do NOT invent gift revenue share entitlement. Record commercial event with exception.
    gift_tx_id = f"gift_{uuid.uuid4().hex[:8]}"
    try:
        gross_zar = Decimal(str(req.coin_cost)) * Decimal("0.1300")
        commercial_accounting_service.process_commercial_event(
            series_id=req.series_id,
            episode_id=req.episode_id,
            source=RevenueEventSource.GIFT,
            source_transaction_id=gift_tx_id,
            event_type=RevenueEventType.GIFT_SENT,
            gross_amount=gross_zar,
            currency="ZAR",
            idempotency_key=f"gift_{gift_tx_id}",
            metadata={
                "gift_id": req.gift_id,
                "gift_name": req.gift_name,
                "coin_cost": req.coin_cost,
                "user_id": req.user_id,
                "creator_id": req.creator_id
            },
            creator_id_override=req.creator_id
        )
    except Exception as e:
        logger.error(f"[CommercialAccounting] Error processing gift accounting: {e}")

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
    idemp_key = req.idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}"
    existing_payout = commercial_accounting_service.repo.get_payout_by_idempotency(idemp_key)
    if existing_payout:
        return {
            "success": True,
            "payout_id": existing_payout["id"],
            "is_idempotent_replay": True,
            "transaction": existing_payout,
            "remaining_coin_balance": req.amount_coins,
            "message": f"Idempotent replay: Payout of {existing_payout.get('requested_amount')} {existing_payout.get('currency')} is currently {existing_payout.get('status')}."
        }

    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == req.creator_id), None)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    # Authoritative balance evaluation (Workstream 6I-E)
    balances = commercial_accounting_service.get_creator_balances(req.creator_id, req.currency)
    legacy_coins = creator.get("coin_earnings", 0)

    # Shadow mode evaluation (Section 21)
    effective_available_zar = balances.available
    if effective_available_zar == Decimal("0.0000") and legacy_coins > 0:
        # Shadow conversion for legacy test compatibility
        effective_available_zar = Decimal(str(legacy_coins)) * Decimal("0.0260")

    payout_amt_zar = Decimal(str(req.amount_local)) if req.amount_local else (Decimal(str(req.amount_coins)) * Decimal("0.0260"))
    if payout_amt_zar <= Decimal("0"):
        raise HTTPException(status_code=400, detail="Payout amount must be greater than zero.")

    if payout_amt_zar > effective_available_zar:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coin balance: Requested {req.amount_coins} coins, but creator only has {legacy_coins} coins available."
        )

    # 2. Record Authoritative Creator Payout (Accounting Object Only — External Rails Inactive)
    payout_res = commercial_accounting_service.request_payout(
        creator_id=req.creator_id,
        requested_amount=payout_amt_zar,
        currency=req.currency,
        payout_method=req.payout_method,
        account_details=req.account_details,
        idempotency_key=idemp_key,
        allow_legacy_shadow=True
    )
    payout_record = payout_res["payout"]
    payout_id = payout_record["id"]

    # Calculate remaining balance projection for client response
    remaining_zar = max(Decimal("0.0000"), effective_available_zar - payout_amt_zar)
    remaining_coins = max(0, legacy_coins - req.amount_coins) if req.amount_coins else int(remaining_zar / Decimal("0.0260"))
    # Invariant: No active financial write paths to creators.coin_earnings (Workstream 6I-E Section 19)
    # Creator financial balance is authoritatively tracked in creator_ledger and creator_payouts

    # Also maintain legacy transaction projection for compatibility without modifying viewer payment tables
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
        "idempotency_key": idemp_key,
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
        before_state={"coin_earnings_before": legacy_coins},
        after_state={"coin_earnings_after": remaining_coins, "payout_amount_coins": req.amount_coins, "amount_local": req.amount_local, "currency": req.currency},
        metadata={"payout_method": req.payout_method, "idempotency_key": idemp_key}
    )

    return {
        "success": True,
        "payout_id": payout_id,
        "transaction": tx_record,
        "remaining_coin_balance": remaining_coins,
        "remaining_available_zar": float(remaining_zar),
        "message": f"Payout of {req.amount_local} {req.currency} requested to {req.payout_method}. Settlement status: Pending External Proof."
    }
