from typing import Optional
from pydantic import BaseModel

class TopupRequest(BaseModel):
    user_id: str
    pack_id: str
    coins: int
    amount_local: float
    currency: str
    payment_method: str  # 'momo_mtn', 'mpesa', 'airtel_money', 'paystack_card'
    phone_or_account: str

class UnlockEpisodeRequest(BaseModel):
    user_id: str
    episode_id: str
    series_id: str
    coins: int

class SendGiftRequest(BaseModel):
    user_id: str
    creator_id: str
    series_id: str
    episode_id: str
    gift_id: str
    gift_name: str
    gift_icon: str
    coin_cost: int
    message: Optional[str] = ""

class PayoutRequest(BaseModel):
    creator_id: str
    amount_coins: int
    amount_local: float
    currency: str
    payout_method: str
    account_details: str

class AirtimeChargeRequest(BaseModel):
    user_id: str
    carrier_id: str  # 'vodacom', 'mtn_sa', 'cellc', 'telkom'
    phone_number: str
    charge_type: str  # 'episode_unlock', 'coin_pack', 'story_pass'
    target_id: str   # episode_id, pack_id, or pass_id
    series_id: Optional[str] = None
    amount_zar: float
    coins_equivalent: Optional[int] = 0

class AirtimePassRequest(BaseModel):
    user_id: str
    pass_id: str
    carrier_id: str
    phone_number: str

class USSDSessionRequest(BaseModel):
    phone_number: str
    ussd_string: str
    user_id: Optional[str] = "user_sa_01"

