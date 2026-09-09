"""
Welele Media™ — Pillars 5 & 6: Payment & Regional Monetisation Abstraction
Architecture Rule:
- Airtime, cards, wallets, coins and subscriptions all sit behind a common payment layer.
- Region abstraction: Regional Monetisation Provider with South Africa as the first implementation (001).
"""

import uuid
import datetime
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

# ============================================================================
# BASE REGIONAL MONETISATION PROVIDER (Abstract Interface)
# ============================================================================
class BaseMonetisationProvider(ABC):
    @property
    @abstractmethod
    def region_code(self) -> str:
        """Two-letter ISO region code, e.g. 'ZA', 'KE', 'NG'."""
        pass

    @property
    @abstractmethod
    def currency(self) -> str:
        """Three-letter ISO currency code, e.g. 'ZAR', 'KES', 'NGN', 'USD'."""
        pass

    @abstractmethod
    def get_supported_channels(self) -> List[Dict[str, Any]]:
        """Returns regional payment channels (e.g. Airtime DCB, Instant EFT, MoMo, Cards)."""
        pass

    @abstractmethod
    def get_coin_packs(self) -> List[Dict[str, Any]]:
        """Returns coin pricing packs converted and denominated for this region."""
        pass

    @abstractmethod
    def get_subscription_passes(self) -> List[Dict[str, Any]]:
        """Returns time-based binge passes (daily, weekend, monthly VIP)."""
        pass

    @abstractmethod
    def process_airtime_charge(
        self,
        user_id: str,
        carrier_id: str,
        phone_number: str,
        charge_type: str,
        target_id: str,
        amount: float,
        coins_grant: int = 0
    ) -> Dict[str, Any]:
        """Direct Carrier Billing (DCB) micro-charge deducted from SIM airtime."""
        pass

    @abstractmethod
    def process_checkout(
        self,
        user_id: str,
        pack_id: str,
        channel: str,
        phone_or_email: str
    ) -> Dict[str, Any]:
        """Handles card, instant EFT, or mobile money top-up checkout."""
        pass


# ============================================================================
# SOUTH AFRICA MONETISATION PROVIDER (Instance 001 - Canonical Implementation)
# ============================================================================
class SouthAfricaMonetisationProvider(BaseMonetisationProvider):
    @property
    def region_code(self) -> str:
        return "ZA"

    @property
    def currency(self) -> str:
        return "ZAR"

    AIRTIME_CARRIERS = [
        {
            "id": "vodacom_airtime",
            "name": "Vodacom SA",
            "brand_color": "#E60000",
            "icon": "🔴",
            "country": "ZA",
            "speed": "Instant 1-Tap",
            "ussd_code": "*130*9353*1#",
            "prefixes": ["082", "072", "076", "079", "0711", "0712", "0713", "0714", "0715", "0716", "0811", "0812", "0813", "0814", "0815"],
            "support_note": "Direct debit from prepaid airtime or monthly Vodacom contract bill"
        },
        {
            "id": "mtn_sa_airtime",
            "name": "MTN South Africa",
            "brand_color": "#FFCC00",
            "icon": "🟡",
            "country": "ZA",
            "speed": "Instant 1-Tap",
            "ussd_code": "*130*9353*2#",
            "prefixes": ["083", "073", "078", "0710", "0717", "0718", "0719", "0810"],
            "support_note": "Everywhere You Go - 1-tap PIN or SMS confirmation"
        },
        {
            "id": "cellc_airtime",
            "name": "Cell C",
            "brand_color": "#000000",
            "icon": "⚫",
            "country": "ZA",
            "speed": "Instant 1-Tap",
            "ussd_code": "*130*9353*3#",
            "prefixes": ["084", "074", "061", "062"],
            "support_note": "Deduct directly from Cell C airtime balance"
        },
        {
            "id": "telkom_airtime",
            "name": "Telkom Mobile",
            "brand_color": "#0072C6",
            "icon": "🔵",
            "country": "ZA",
            "speed": "Instant 1-Tap",
            "ussd_code": "*130*9353*4#",
            "prefixes": ["081", "065", "067", "068"],
            "support_note": "Telkom Direct Airtime carrier billing supported"
        }
    ]

    PASSES = [
        {
            "id": "pass_daily_r5",
            "name": "Daily Mzansi Pass",
            "price_zar": 5.0,
            "duration": "24 Hours",
            "benefits": "Unlimited unlock of any single chosen drama series for 24 hours",
            "badge": "⚡ Quick Daily",
            "popular": False,
            "coins_grant": 30
        },
        {
            "id": "pass_weekend_r15",
            "name": "Weekend Binge Pass",
            "price_zar": 15.0,
            "duration": "72 Hours (Fri-Sun)",
            "benefits": "All-access streaming to all trending African & Mzansi original shorts + 100 Coins",
            "badge": "🔥 Most Popular",
            "popular": True,
            "coins_grant": 150
        },
        {
            "id": "pass_vip_r49",
            "name": "Monthly VIP Airtime Pass",
            "price_zar": 49.0,
            "duration": "30 Days",
            "benefits": "Zero wait time, HD 4K vertical streaming, 500 Welele Coins, Creator Tipping VIP badge",
            "badge": "👑 VIP Patron",
            "popular": False,
            "coins_grant": 500
        }
    ]

    COIN_PACKS_ZA = [
        {
            "id": "pack_starter",
            "coins": 50,
            "bonus": 0,
            "price_zar": 5.0,
            "price_usd": 0.99,
            "popular": False,
            "label": "Starter Flame",
            "zar_airtime_price": 5.0,
            "description": "Unlock up to 10 cliffhanger episodes"
        },
        {
            "id": "pack_fan",
            "coins": 150,
            "bonus": 25,
            "price_zar": 15.0,
            "price_usd": 2.99,
            "popular": True,
            "label": "Fan Favorite",
            "zar_airtime_price": 15.0,
            "description": "Best value for bingeing hot Mzansi series"
        },
        {
            "id": "pack_binge",
            "coins": 450,
            "bonus": 100,
            "price_zar": 40.0,
            "price_usd": 7.99,
            "popular": False,
            "label": "Binge Master",
            "zar_airtime_price": 40.0,
            "description": "Never pause the drama - bonus 100 coins"
        },
        {
            "id": "pack_royal",
            "coins": 1000,
            "bonus": 300,
            "price_zar": 99.0,
            "price_usd": 14.99,
            "popular": False,
            "label": "Royal Patron",
            "zar_airtime_price": 99.0,
            "description": "VIP creator tipping & full season pass"
        }
    ]

    def get_supported_channels(self) -> List[Dict[str, Any]]:
        return [
            {"id": "airtime_dcb", "name": "Airtime (Vodacom, MTN, Cell C, Telkom)", "type": "CARRIER_BILLING", "instant": True},
            {"id": "ozow_eft", "name": "Ozow Instant EFT", "type": "BANK_EFT", "instant": True},
            {"id": "card_paystack", "name": "Debit / Credit Card (Visa/Mastercard)", "type": "CARD", "instant": True},
            {"id": "voucher_1voucher", "name": "1Voucher / OTT Voucher PIN", "type": "VOUCHER", "instant": True}
        ]

    def get_coin_packs(self) -> List[Dict[str, Any]]:
        packs = []
        for p in self.COIN_PACKS_ZA:
            cp = p.copy()
            cp["price_local"] = cp["price_zar"]
            cp["currency"] = "ZAR"
            packs.append(cp)
        return packs

    def get_subscription_passes(self) -> List[Dict[str, Any]]:
        return self.PASSES

    def detect_carrier(self, phone: str) -> Dict[str, Any]:
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        if cleaned.startswith('27'):
            cleaned = '0' + cleaned[2:]
        for carrier in self.AIRTIME_CARRIERS:
            for prefix in carrier["prefixes"]:
                if cleaned.startswith(prefix):
                    return carrier
        return self.AIRTIME_CARRIERS[0]

    def process_airtime_charge(
        self,
        user_id: str,
        carrier_id: str,
        phone_number: str,
        charge_type: str,
        target_id: str,
        amount: float,
        coins_grant: int = 0
    ) -> Dict[str, Any]:
        carrier = next((c for c in self.AIRTIME_CARRIERS if c["id"] == carrier_id), self.detect_carrier(phone_number))
        tx_id = f"tx_za_airtime_{uuid.uuid4().hex[:10]}"
        ref = f"ZA-{carrier['name'][:3].upper()}-{uuid.uuid4().hex[:6].upper()}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return {
            "transaction_id": tx_id,
            "status": "completed",
            "region": "ZA",
            "charge_type": charge_type,
            "target_id": target_id,
            "carrier_id": carrier["id"],
            "carrier_name": carrier["name"],
            "phone_number": phone_number,
            "amount_zar": amount,
            "currency": "ZAR",
            "coins_credited": coins_grant,
            "reference": ref,
            "sms_notification": f"Welele Media: R{amount:.2f} deducted from your {carrier['name']} airtime. Ref: {ref}.",
            "timestamp": timestamp
        }

    def process_checkout(
        self,
        user_id: str,
        pack_id: str,
        channel: str,
        phone_or_email: str
    ) -> Dict[str, Any]:
        pack = next((p for p in self.COIN_PACKS_ZA if p["id"] == pack_id), self.COIN_PACKS_ZA[0])
        total_coins = pack["coins"] + pack.get("bonus", 0)
        tx_id = f"tx_za_{uuid.uuid4().hex[:10]}"
        ref = f"ZA-{channel.upper()[:4]}-{uuid.uuid4().hex[:6].upper()}"

        return {
            "transaction_id": tx_id,
            "status": "completed",
            "region": "ZA",
            "currency": "ZAR",
            "amount": pack["price_zar"],
            "coins_credited": total_coins,
            "payment_method": channel,
            "reference": ref,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }


# ============================================================================
# PAN-AFRICAN MONETISATION PROVIDER (Instance 002 - Extension Adapter)
# ============================================================================
class PanAfricanMonetisationProvider(BaseMonetisationProvider):
    def __init__(self, region: str = "GLOBAL", currency: str = "USD"):
        self._region = region
        self._currency = currency

    @property
    def region_code(self) -> str:
        return self._region

    @property
    def currency(self) -> str:
        return self._currency

    def get_supported_channels(self) -> List[Dict[str, Any]]:
        return [
            {"id": "momo_mtn", "name": "MTN MoMo (West/East Africa)", "type": "MOMO", "instant": True},
            {"id": "mpesa", "name": "M-Pesa (Kenya/Tanzania)", "type": "MOMO", "instant": True},
            {"id": "airtel_money", "name": "Airtel Money", "type": "MOMO", "instant": True},
            {"id": "card_global", "name": "International Visa / Mastercard", "type": "CARD", "instant": True}
        ]

    def get_coin_packs(self) -> List[Dict[str, Any]]:
        rates = {"KES": 130.0, "NGN": 1500.0, "GHS": 15.5, "USD": 1.0}
        rate = rates.get(self._currency, 1.0)
        
        base_packs = [
            {"id": "pack_starter", "coins": 50, "bonus": 0, "price_usd": 0.99, "label": "Starter Flame"},
            {"id": "pack_fan", "coins": 150, "bonus": 25, "price_usd": 2.99, "label": "Fan Favorite", "popular": True},
            {"id": "pack_binge", "coins": 450, "bonus": 100, "price_usd": 7.99, "label": "Binge Master"},
            {"id": "pack_royal", "coins": 1000, "bonus": 300, "price_usd": 14.99, "label": "Royal Patron"}
        ]
        
        for p in base_packs:
            p["price_local"] = round(p["price_usd"] * rate, 2)
            p["currency"] = self._currency
        return base_packs

    def get_subscription_passes(self) -> List[Dict[str, Any]]:
        return [
            {"id": "pass_daily_global", "name": "24H Global Pass", "price_local": 0.99, "currency": self._currency, "duration": "24 Hours", "coins_grant": 30},
            {"id": "pass_monthly_global", "name": "VIP Monthly All-Access", "price_local": 4.99, "currency": self._currency, "duration": "30 Days", "coins_grant": 500}
        ]

    def process_airtime_charge(self, user_id: str, carrier_id: str, phone_number: str, charge_type: str, target_id: str, amount: float, coins_grant: int = 0) -> Dict[str, Any]:
        tx_id = f"tx_pan_{uuid.uuid4().hex[:10]}"
        return {
            "transaction_id": tx_id,
            "status": "completed",
            "region": self._region,
            "carrier_id": carrier_id,
            "phone_number": phone_number,
            "amount": amount,
            "coins_credited": coins_grant,
            "reference": f"AFR-{uuid.uuid4().hex[:6].upper()}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def process_checkout(self, user_id: str, pack_id: str, channel: str, phone_or_email: str) -> Dict[str, Any]:
        tx_id = f"tx_pan_{uuid.uuid4().hex[:10]}"
        return {
            "transaction_id": tx_id,
            "status": "completed",
            "region": self._region,
            "coins_credited": 150,
            "payment_method": channel,
            "reference": f"AFR-{uuid.uuid4().hex[:6].upper()}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }


# ============================================================================
# PAYMENT ORCHESTRATOR & UNIFIED PAYMENT ABSTRACTION LAYER (Pillar 5 & 6)
# ============================================================================
class PaymentService:
    def __init__(self):
        # Register Regional Providers
        self._providers: Dict[str, BaseMonetisationProvider] = {
            "ZA": SouthAfricaMonetisationProvider(),
            "GLOBAL": PanAfricanMonetisationProvider(region="GLOBAL", currency="USD"),
            "KE": PanAfricanMonetisationProvider(region="KE", currency="KES"),
            "NG": PanAfricanMonetisationProvider(region="NG", currency="NGN"),
            "GH": PanAfricanMonetisationProvider(region="GH", currency="GHS"),
        }
        self.default_provider = self._providers["ZA"]

    def get_provider(self, region_code: Optional[str] = None) -> BaseMonetisationProvider:
        if not region_code:
            return self.default_provider
        return self._providers.get(region_code.upper(), self.default_provider)

    # Proxy helper methods for backward compatibility and clean API routing
    def get_coin_packs(self, currency: str = "ZAR") -> list:
        if currency == "ZAR":
            return self._providers["ZA"].get_coin_packs()
        provider = self.get_provider("GLOBAL")
        return provider.get_coin_packs()

    @property
    def SA_AIRTIME_CARRIERS(self):
        return SouthAfricaMonetisationProvider.AIRTIME_CARRIERS

    @property
    def SA_AIRTIME_PASSES(self):
        return SouthAfricaMonetisationProvider.PASSES

    @property
    def VIRTUAL_GIFTS(self):
        return [
            {"id": "gift_flame", "name": "Welele Flame", "icon": "🔥", "cost": 5, "description": "Ignite the story!"},
            {"id": "gift_crown", "name": "Royal Crown", "icon": "👑", "cost": 25, "description": "Cinema royalty!"},
            {"id": "gift_drum", "name": "Djembe Beat", "icon": "🪘", "cost": 50, "description": "Honor the rhythm!"},
            {"id": "gift_thunder", "name": "Shango Lightning", "icon": "⚡", "cost": 100, "description": "Electric cliffhanger!"},
            {"id": "gift_gold", "name": "African Gold", "icon": "🏆", "cost": 250, "description": "Ultimate appreciation!"}
        ]

    def detect_carrier_from_phone(self, phone: str) -> Dict[str, Any]:
        za_provider = self._providers["ZA"]
        if isinstance(za_provider, SouthAfricaMonetisationProvider):
            return za_provider.detect_carrier(phone)
        return SouthAfricaMonetisationProvider.AIRTIME_CARRIERS[0]

    def process_topup(self, user_id: str, pack_id: str, payment_method: str, phone: str, region: str = "ZA") -> Dict[str, Any]:
        provider = self.get_provider(region)
        return provider.process_checkout(user_id=user_id, pack_id=pack_id, channel=payment_method, phone_or_email=phone)

    def process_airtime_charge(
        self,
        user_id: str,
        carrier_id: str,
        phone_number: str,
        charge_type: str,
        target_id: str,
        amount_zar: float,
        coins_equivalent: int = 0
    ) -> Dict[str, Any]:
        provider = self.get_provider("ZA")
        return provider.process_airtime_charge(
            user_id=user_id,
            carrier_id=carrier_id,
            phone_number=phone_number,
            charge_type=charge_type,
            target_id=target_id,
            amount=amount_zar,
            coins_grant=coins_equivalent
        )

    def simulate_ussd_session(self, phone_number: str, ussd_string: str) -> Dict[str, Any]:
        carrier = self.detect_carrier_from_phone(phone_number)
        return {
            "session_id": f"ussd_{uuid.uuid4().hex[:8]}",
            "carrier": carrier["name"],
            "phone": phone_number,
            "ussd_code": ussd_string or "*130*9353#",
            "menu_text": f"Welcome to Welele Media ZA on {carrier['name']}\n1. R5 Daily Pass (Unlimited Series)\n2. R15 Weekend Binge (175 Coins)\n3. R40 Binge Master (550 Coins)\n4. Check Airtime Balance\nReply with number:",
            "options": [
                {"choice": "1", "label": "R5 Daily Pass", "amount": 5.0, "coins": 30},
                {"choice": "2", "label": "R15 Weekend Binge", "amount": 15.0, "coins": 175},
                {"choice": "3", "label": "R40 Binge Master", "amount": 40.0, "coins": 550}
            ]
        }

payment_service = PaymentService()
