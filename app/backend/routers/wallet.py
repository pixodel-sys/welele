"""
Welele Media™ — Wallet, Coins & Ledger Router (Section 5.1 & Pillar 3)
Handles user coin balances, purchase packs, gift transfers, and double-entry transaction ledgers.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.ledger_service import ledger_service
from services.payment_service import payment_service
from database import db

router = APIRouter(prefix="/wallet", tags=["Wallet & Ledger"])

class SendGiftPayload(BaseModel):
    user_id: str
    creator_id: str
    series_id: str
    episode_id: str
    gift_id: str
    gift_name: str
    gift_icon: str
    coin_cost: int
    message: Optional[str] = ""

@router.get("/balance")
def get_wallet_balance(user_id: str = Query(..., description="User ID")):
    wallet = ledger_service.get_or_create_wallet(user_id)
    balance = ledger_service.get_balance(user_id)
    return {
        "user_id": user_id,
        "coin_balance": balance["coin_balance"],
        "bonus_coins": balance["bonus_coins"],
        "total_usable_coins": balance["total_usable_coins"],
        "wallet_id": wallet["id"]
    }

@router.get("/ledger")
def get_coin_ledger_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Max entries")
):
    """Returns immutable double-entry audit history of all coin movements for the user."""
    history = ledger_service.get_ledger_history(user_id, limit=limit)
    return {
        "user_id": user_id,
        "total_entries": len(history),
        "ledger": history
    }

@router.get("/packs")
def get_available_coin_packs(region: Optional[str] = "ZA"):
    provider = payment_service.get_provider(region)
    packs = provider.get_coin_packs()
    passes = provider.get_subscription_passes()
    gifts = payment_service.VIRTUAL_GIFTS
    return {
        "region": region,
        "currency": provider.currency,
        "packs": packs,
        "passes": passes,
        "gifts": gifts
    }

@router.post("/gifts/send")
def send_virtual_gift(req: SendGiftPayload):
    """Deducts coins from user wallet, credits creator earnings, and records double-entry ledger."""
    success, msg, ledger_entry = ledger_service.debit_coins(
        user_id=req.user_id,
        amount=req.coin_cost,
        transaction_type="GIFT_SENT",
        reference_id=req.gift_id,
        description=f"Sent {req.gift_name} {req.gift_icon} to creator {req.creator_id}"
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    # Credit creator coin balance
    creators = db.get("creators")
    creator = next((c for c in creators if c["id"] == req.creator_id), None)
    if creator:
        new_earnings = creator.get("coin_earnings", 0) + req.coin_cost
        db.update("creators", req.creator_id, {"coin_earnings": new_earnings})

    gift_record = {
        "id": f"gift_{req.gift_id}",
        "user_id": req.user_id,
        "creator_id": req.creator_id,
        "series_id": req.series_id,
        "episode_id": req.episode_id,
        "gift_name": req.gift_name,
        "gift_icon": req.gift_icon,
        "cost_coins": req.coin_cost,
        "message": req.message
    }
    db.insert("gifts", gift_record)

    balance = ledger_service.get_balance(req.user_id)
    return {
        "success": True,
        "message": f"Sent {req.gift_name} {req.gift_icon}!",
        "gift": gift_record,
        "remaining_balance": balance["total_usable_coins"]
    }
