# WELELE MEDIA™ — PAYMENT & MONETIZATION ARCHITECTURE
**Document ID:** `WELELE-DOCS-PAY-001`  
**Governing Principle:** Immutable Double-Entry Ledger + Unified African Multi-Provider Orchestration

---

## 1. The Financial Core: Double-Entry Immutable Ledger

In accordance with strict fintech compliance, wallet balances are **never** treated as mutable variables in isolation. 

### 1.1 Invariant Rules
1. **Append-Only Principle**: No row in `coin_ledger` can ever be updated or deleted (`UPDATE` and `DELETE` queries on `coin_ledger` are disabled via database triggers).
2. **Idempotency Guarantee**: Every financial transaction must carry a unique client-generated `idempotency_key` (UUIDv4) to prevent double-charging on spotty mobile network reconnections.
3. **Atomic Balance Calculations**:
   $$\text{Wallet Balance} = \sum(\text{Credits}) - \sum(\text{Debits})$$

### 1.2 Ledger Transaction Structure
```sql
INSERT INTO coin_ledger (
    user_id,
    transaction_type,     -- 'PURCHASE', 'AIRTIME_PASS', 'EPISODE_UNLOCK', 'GIFT_SENT', 'CREATOR_PAYOUT'
    entry_type,           -- 'CREDIT' or 'DEBIT'
    coins_amount,         -- Positive integer
    balance_after,        -- Snapshot of calculated balance after transaction
    currency,             -- 'ZAR', 'NGN', 'KES', 'GHS', 'USD'
    local_amount,         -- Decimal fiat amount charged
    payment_method,       -- 'vodacom_airtime', 'mtn_momo', 'paystack', 'flutterwave', 'card'
    reference_id,         -- Gateway transaction ID
    idempotency_key
) VALUES (...);
```

---

## 2. Pan-African Payment Orchestration Matrix

```
                     WELELE PAYMENT ORCHESTRATOR
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
SOUTH AFRICA (ZA)          NIGERIA & GHANA (NG/GHS)     KENYA & EAST AFRICA (KE)
 ├── Vodacom Direct Airtime  ├── Paystack Card & USSD    ├── M-Pesa Direct STK Push
 ├── MTN MoMo & Airtime      ├── Flutterwave Bank Pay    ├── Airtel Money
 ├── Telkom Direct Airtime   └── OPay / Moniepoint       └── Equitel USSD
 └── Ozow Instant EFT
```

---

## 3. South African 1-Tap Direct Airtime Billing (DOB)

South Africa operates on direct telco micro-billing to eliminate credit card friction:

### 3.1 Supported Telcos
- **Vodacom South Africa** (`vodacom_airtime`): Direct API gateway integration.
- **MTN South Africa** (`mtn_airtime`): MoMo & Direct carrier billing.
- **Telkom Mobile** (`telkom_airtime`): Direct carrier airtime billing.
- **Cell C** (`cellc_airtime`): Direct USSD / SMS billing.

### 3.2 Pricing Packs & Pass Tiers
| Pass ID | Name | ZAR Price | Coins Equivalent | Validity |
|---|---|---|---|---|
| `ep_unlock_micro` | Single Episode Unlock | **R3.00** | 5 Coins | Permanent Unlock |
| `pass_daily_binge` | 24-Hour Binge Pass | **R15.00** | 35 Coins | 24 Hours Unlimited |
| `pass_weekend_unlimited` | Weekend Drama Pass | **R49.00** | 120 Coins | Friday–Sunday |
| `pass_monthly_royal` | Monthly VIP Access | **R149.00** | 450 Coins | 30 Days |

---

## 4. Creator Revenue Distribution Engine

1. **Gross Revenue Collection**: Fiat collected via Airtime/M-Pesa/Card.
2. **Platform Fee**: Retained for CDN bandwidth, transcoding compute, and platform operations (30%).
3. **Creator Share (70%)**: Distributed to Creator Wallets via automated monthly payouts (Direct Bank EFT, MoMo, or Paystack Payout API).
