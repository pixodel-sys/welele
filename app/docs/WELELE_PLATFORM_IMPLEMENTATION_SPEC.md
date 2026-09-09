# WELELE MEDIA™ — PLATFORM IMPLEMENTATION SPECIFICATION
**Document ID:** `WELELE-SPEC-v1.0`  
**Governing Architecture:** `ARCHITECTURE.md` (System Architecture & Engineering Manifesto v1.0)  
**Status:** Canonical Engineering Contract  
**Target Environment:** Cloudflare Pages + Railway (FastAPI) + Cloudflare R2 + Supabase (PostgreSQL)

---

## 1. Scope & Purpose

This document serves as the **unbreakable engineering implementation contract** underneath the *Welele Architecture Manifesto*. All human engineers and AI coding agents MUST conform to the data contracts, operational boundaries, and system pipelines specified across the `/docs` suite:

```
/docs
├── WELELE_ARCHITECTURE.md                   # Frozen architectural principles & manifesto
├── WELELE_PLATFORM_IMPLEMENTATION_SPEC.md   # This document: Primary engineering contract
├── DATABASE_SCHEMA.md                       # PostgreSQL relational schema & migrations
├── API_CONTRACT.md                          # FastAPI OpenAPI specifications & payload rules
├── PAYMENT_ARCHITECTURE.md                  # Double-entry ledger, coins & SA airtime carrier billing
├── VIDEO_PIPELINE.md                        # Media asset reference model, HLS ladders & R2 CDN
├── EVENT_ANALYTICS.md                       # Platform-wide event ingestion & retention engine
└── SECURITY_MODEL.md                        # Auth, signed keys, DRM & screen capture defense
```

---

## 2. Core Architectural Tightenings

### 2.1 Media Asset Reference Model (`EPISODE` ➔ `VIDEO_ASSET`)
Episodes **NEVER** store naked video URLs directly as their primary truth. Every playable episode references a strongly typed `video_asset` entity containing storage metadata, multi-rendition HLS ladders (`1080p`, `720p`, `480p`, `360p`), transcoding status, and duration metrics.

```
EPISODE (Relational Entity)
   │
   └──► video_asset_id (FK)
             │
             ▼
        VIDEO_ASSET
             ├── id: UUID
             ├── storage_key: string (e.g. "stories/{id}/episodes/{ep}/master.mp4")
             ├── master_url: string
             ├── hls_manifest_url: string (e.g. "https://cdn.welele.media/.../playlist.m3u8")
             ├── thumbnail_url: string
             ├── duration_seconds: number
             ├── resolution_w: number
             ├── resolution_h: number
             ├── codec: string (e.g. "H.264/AAC" or "AV1")
             ├── bitrate_kbps: number
             ├── renditions: JSONB (1080p, 720p, 480p_data_saver, 360p)
             └── processing_status: ENUM ("QUEUED", "TRANSCODING", "READY", "FAILED")
```

---

### 2.2 Financial Truth: Immutable Double-Entry Ledger
The user or creator `wallet.coin_balance` is **never** manipulated as the foundational financial truth. 
- **The Source of Truth**: `coin_ledger` table (immutable credit/debit audit journal entries).
- **The Wallet Balance**: A calculated / materialized projection derived from summing all ledger entries for a given `user_id`.

```
                    LEDGER (Source of Truth)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
     CREDIT ENTRY                          DEBIT ENTRY
   (Top-up / Bonus / Grant)               (Episode Unlock / Gift)
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                       WALLET PROJECTION
                (Materialized State / Cached Balance)
```

---

### 2.3 Platform-Wide Event Ingestion Model
To calculate viewing retention curves, cliffhanger drop-offs, and creator performance, all user interactions dispatch standard telemetry events to the ingestion engine:

```
                            WELELE TELEMETRY EVENTS
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
    STREAMING METRICS          MONETIZATION FLOWS          COMMUNITY ACTIONS
     - episode_started          - unlock_attempted          - comment_posted
     - episode_25_percent       - unlock_completed          - reaction_sent
     - episode_50_percent       - coin_purchase             - series_followed
     - episode_completed        - airtime_payment           - episode_shared
     - cliffhanger_reached      - gift_sent                 - creator_upload
```

---

### 2.4 The Creator Flywheel Moat
The platform's sustainable business moat is the closed-loop feedback engine connecting African creators with immediate audience monetization:

```
                      ┌───────────────────────────┐
                      │          CREATOR          │
                      │  (Story & Episode Upload) │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │       AI PROCESSING       │
                      │ (Auto Subtitles, AI QC)   │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │          PUBLISH          │
                      │   (9:16 Vertical Feed)    │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │          AUDIENCE         │
                      │     (Pan-African Mobile)  │
                      └──────┬─────────────┬──────┘
                             │             │
                    ┌────────┴──────┐   ┌──┴────────────┐
                    ▼               │   │               ▼
                WATCH (9:16)        │   │             ENGAGE
                    │               │   │      (Bullet Comments &
                    ▼               │   │      Floating Reactions)
             Cliffhanger Reach      │   │               │
                    │               │   │               │
                    ▼               │   │               │
             1-TAP UNLOCK           │   │               │
        (Coins / Vodacom/MTN)       │   │               │
                    │               │   │               │
                    └───────────────┼───┼───────────────┘
                                    │   │
                                    ▼   ▼
                      ┌───────────────────────────┐
                      │      REVENUE & METRICS    │
                      │   (Double-Entry Payouts)  │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │     CREATOR CREATE MORE   │
                      │ (Sustainable African IP)  │
                      └───────────────────────────┘
```

---

## 3. Platform Hierarchy & Device Experience

1. **Mobile Web PWA (Primary Consumer Surface)**:
   - Form-factor: Ultra-fast vertical viewport (9:16 aspect ratio).
   - Core behavior: Swipe-to-next, instant chunked preloading, 1-tap Airtime & Coin unlock, localized subtitle toggle (isiZulu, isiXhosa, Afrikaans, Sesotho, Swahili, English), bullet comments, and DRM anti-screen-capture protection.

2. **Desktop Workstation (Operational & Creator Surface)**:
   - Form-factor: 16:9 responsive widescreen console.
   - Core behavior:
     - **Creator Studio**: 4K master uploads, AI subtitle timeline editor, revenue analytics & withdrawal requests.
     - **Admin Console**: Content moderation queues, automated KYC approvals, carrier airtime transaction telemetry, and financial ledger audits.
     - **Advertiser Portal**: Sponsored micro-drama placements & brand integration performance.

---

## 4. Production Deployment Stack

| Role | Technology | Infrastructure Provider | Rationale |
|---|---|---|---|
| **Frontend UI** | Vite + React + TypeScript + Tailwind | **Cloudflare Pages** | Zero-latency edge CDN with points-of-presence in Jo'burg, Cape Town, Lagos, Nairobi, and Accra. |
| **Backend Services** | FastAPI + Uvicorn (Python 3.12) | **Railway / Fly.io** | Low-latency containerized execution with direct PostgreSQL connection pooling. |
| **Database & Auth** | PostgreSQL 15+ & Row-Level Security | **Supabase** | Multi-region managed database, UUID primitives, and automated backup schedules. |
| **Media Storage & CDN** | HLS (.m3u8 / .ts) & Poster Assets | **Cloudflare R2** | **$0 egress fees**, enabling high-volume video streaming at low operational cost. |
| **Billing & Airtime** | USSD / Direct Operator Billing | **Direct Carrier Gateways** | Vodacom, MTN, Telkom, Cell C 1-tap micro-deductions. |
