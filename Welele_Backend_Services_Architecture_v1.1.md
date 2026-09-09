# Welele Media™ --- Backend Services Architecture

**Version:** 1.1\
**Status:** LOCKED & CANONICAL\
**Architecture State:** Frozen\
**Target Platform:** Mobile-first React PWA / Pan-African Microdrama
Platform\
**Backend Runtime:** Python 3.11+ / FastAPI\
**Physical Hosting:** Cloudflare Pages + Railway + Cloudflare R2 +
Supabase\
**Core Principle:** **Technology enables the ecosystem. Content is the
ecosystem.**

------------------------------------------------------------------------

# 1. Purpose

This document defines and locks the backend services architecture for
**Welele Media™**.

The backend is the application brain connecting the Welele PWA, Creator
Hub, Admin platform, transactional database, media storage, realtime
services, analytics, AI processing and regional monetisation providers.

The architecture is intentionally designed as a **modular monolith
first**.

Welele does **not** begin with unnecessary microservices. Instead,
domain boundaries are established inside one FastAPI application so that
individual services can be extracted later when scale, operational
requirements or team structure justify doing so.

> **The backend authorises, orchestrates and records. It does not carry
> video traffic.**

------------------------------------------------------------------------

# 2. Architecture Position

``` text
                           USERS
                             │
                             ▼
                  ┌─────────────────────┐
                  │     CLOUDFLARE      │
                  │ DNS / SSL / WAF     │
                  │ Edge / CDN          │
                  └──────────┬──────────┘
                             │
                ┌────────────┴─────────────┐
                │                          │
                ▼                          ▼
       ┌─────────────────┐        ┌──────────────────┐
       │ CLOUDFLARE      │        │ CLOUDFLARE R2    │
       │ PAGES           │        │                  │
       │                 │        │ Video / HLS      │
       │ React PWA       │        │ Thumbnails       │
       │ Viewer          │        │ Subtitles        │
       │ Creator Hub     │        │ Creator Assets   │
       │ Admin           │        │                  │
       └────────┬────────┘        └──────────────────┘
                │
                │ REST / WebSocket
                ▼
       ┌────────────────────────────┐
       │          RAILWAY            │
       │                            │
       │       FastAPI Backend      │
       │                            │
       │ Auth / Content / Playback  │
       │ Wallet / Payments          │
       │ Creator / Chat / Analytics │
       │ AI / Administration        │
       │ Background Workers         │
       └────────────┬───────────────┘
                    │
             ┌──────┴─────────┐
             ▼                ▼
      ┌──────────────┐  ┌──────────────┐
      │   SUPABASE   │  │    REDIS     │
      │              │  │              │
      │ PostgreSQL   │  │ Cache        │
      │ Auth         │  │ Rate Limits  │
      │ RLS          │  │ Sessions     │
      │ Transactions │  │ Realtime*    │
      └──────────────┘  └──────────────┘
                    │
                    ▼
          ┌─────────────────────┐
          │ REGIONAL PAYMENTS   │
          │                     │
          │ Airtime / EFT       │
          │ Cards / Vouchers    │
          │ Regional Providers  │
          └─────────────────────┘
```

------------------------------------------------------------------------

# 3. Physical Hosting Architecture

The canonical Welele v1 infrastructure is:

  -----------------------------------------------------------------------
  Layer                   Platform                Responsibility
  ----------------------- ----------------------- -----------------------
  Edge                    **Cloudflare**          DNS, SSL, WAF, edge
                                                  routing and CDN

  Frontend                **Cloudflare Pages**    React PWA, Viewer,
                                                  Creator Hub, Admin

  Backend                 **Railway**             FastAPI application and
                                                  background workers

  Database                **Supabase PostgreSQL** Transactional and
                                                  relational source of
                                                  truth

  Identity                **Supabase Auth /       Authentication
                          managed auth layer**    primitives

  Media                   **Cloudflare R2**       Video, HLS, thumbnails,
                                                  subtitles and assets

  Cache / transient       **Redis-compatible      Cache, rate limits,
  services                managed service**       transient state,
                                                  realtime support

  Source Control          **GitHub**              Source code, CI/CD and
                                                  version control
  -----------------------------------------------------------------------

The exact infrastructure vendor may change in the future without
changing the logical Welele architecture.

------------------------------------------------------------------------

# 4. Why This Hosting Model

Welele is a content platform, not an infrastructure company.

The initial infrastructure must therefore optimise for:

-   low operational complexity;
-   low initial cost;
-   rapid deployment;
-   container portability;
-   global media delivery;
-   straightforward scaling;
-   strong database transactions;
-   direct media uploads;
-   developer velocity.

Railway provides managed container execution without forcing the project
into unnecessary infrastructure complexity.

Cloudflare handles the edge.

R2 handles the media.

Supabase handles PostgreSQL and identity primitives.

The application remains owned by Welele.

------------------------------------------------------------------------

# 5. Core Backend Principles

## 5.1 Stateless Application Tier

Every FastAPI instance must be disposable.

Business-critical state must never depend on:

-   Python process memory;
-   local container filesystem;
-   process globals;
-   container-local databases.

Any instance must be able to process any request.

``` text
User
  ↓
Cloudflare
  ↓
Railway
  ├── API Instance 1
  ├── API Instance 2
  └── API Instance 3
          ↓
   Shared Data Services
```

------------------------------------------------------------------------

## 5.2 PostgreSQL Is the Transactional Authority

Supabase PostgreSQL is authoritative for:

-   users;
-   wallets;
-   coins;
-   ledger transactions;
-   payment transactions;
-   episode unlocks;
-   creator earnings;
-   royalty allocations;
-   series;
-   episodes;
-   entitlements;
-   permissions;
-   important watch state.

Redis is an acceleration layer, never financial truth.

------------------------------------------------------------------------

## 5.3 Video Bypasses the Backend

FastAPI must never become the video streaming server.

The backend:

1.  authenticates the user;
2.  verifies entitlement;
3.  determines playback rights;
4.  generates a signed playback URL;
5.  returns the authorised stream location.

The client retrieves the actual video directly through Cloudflare/R2.

``` text
PWA
 ↓
"Can I watch EP07?"
 ↓
FastAPI
 ↓
PostgreSQL entitlement check
 ↓
FastAPI
 ↓
Signed URL
 ↓
Cloudflare Edge
 ↓
R2
 ↓
Video
```

This is a fundamental scalability rule.

------------------------------------------------------------------------

# 6. Backend Application Structure

``` text
backend/
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   ├── logging.py
│   │   └── exceptions.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── router.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── series.py
│   │   ├── episodes.py
│   │   ├── playback.py
│   │   ├── wallet.py
│   │   ├── payments.py
│   │   ├── creator.py
│   │   ├── chat.py
│   │   ├── analytics.py
│   │   ├── ai.py
│   │   └── admin.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── content_service.py
│   │   ├── episode_service.py
│   │   ├── playback_service.py
│   │   ├── wallet_service.py
│   │   ├── ledger_service.py
│   │   ├── payment_service.py
│   │   ├── creator_service.py
│   │   ├── royalty_service.py
│   │   ├── chat_service.py
│   │   ├── analytics_service.py
│   │   ├── ai_service.py
│   │   └── storage_service.py
│   │
│   ├── providers/
│   │   ├── payments/
│   │   │   ├── base.py
│   │   │   ├── za.py
│   │   │   ├── airtime.py
│   │   │   ├── ozow.py
│   │   │   ├── vouchers.py
│   │   │   └── registry.py
│   │   │
│   │   ├── storage/
│   │   │   ├── base.py
│   │   │   └── r2.py
│   │   │
│   │   └── ai/
│   │       └── base.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── wallet.py
│   │   ├── transaction.py
│   │   ├── series.py
│   │   ├── episode.py
│   │   ├── unlock.py
│   │   ├── creator.py
│   │   ├── payment.py
│   │   ├── comment.py
│   │   └── analytics.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── series.py
│   │   ├── episode.py
│   │   ├── wallet.py
│   │   ├── payment.py
│   │   ├── creator.py
│   │   └── chat.py
│   │
│   ├── workers/
│   │   ├── video.py
│   │   ├── analytics.py
│   │   ├── notifications.py
│   │   └── royalties.py
│   │
│   └── middleware/
│       ├── request_id.py
│       ├── rate_limit.py
│       └── audit.py
│
├── tests/
├── migrations/
├── Dockerfile
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

# 7. Domain Services

The initial deployment is one FastAPI application containing explicit
domains.

## 7.1 Auth Service

Responsibilities:

-   phone OTP;
-   Google authentication;
-   guest sessions;
-   session validation;
-   token verification;
-   account linking;
-   region assignment;
-   user identity.

------------------------------------------------------------------------

## 7.2 Content Service

Responsibilities:

-   series;
-   genres;
-   creators;
-   descriptions;
-   thumbnails;
-   languages;
-   age classification;
-   discovery metadata;
-   publication state.

Content metadata belongs in PostgreSQL.

Media binaries belong in R2.

------------------------------------------------------------------------

## 7.3 Episode Service

Responsibilities:

-   episode metadata;
-   ordering;
-   duration;
-   pricing;
-   free/gated status;
-   cliffhanger metadata;
-   subtitles;
-   processing state;
-   publication lifecycle.

Canonical episode lifecycle:

``` text
DRAFT
 ↓
UPLOADING
 ↓
PROCESSING
 ↓
READY
 ↓
PUBLISHED
 ↓
ARCHIVED
```

An uploaded file alone does not make an episode playable.

------------------------------------------------------------------------

# 8. Playback & Entitlement Service

This is the security boundary between content ownership and media
delivery.

Responsibilities:

-   free-content checks;
-   unlock checks;
-   entitlement verification;
-   region restrictions;
-   signed URL generation;
-   playback initiation;
-   playback telemetry.

Example:

``` text
GET /api/v1/episodes/{episode_id}/playback
```

Response:

``` json
{
  "episode_id": "...",
  "authorized": true,
  "stream_type": "hls",
  "playback_url": "...",
  "expires_at": "..."
}
```

Playback URLs are short-lived and non-permanent.

------------------------------------------------------------------------

# 9. Wallet & Ledger Services

## Wallet

Responsibilities:

-   wallet creation;
-   balance retrieval;
-   coin packs;
-   bonus coins;
-   balance verification;
-   unlock coordination.

## Ledger

Every coin movement produces an immutable transaction.

Examples:

``` text
PURCHASE
BONUS
REWARD
UNLOCK
REFUND
ADJUSTMENT
ROYALTY
EXPIRY
```

Wallet mutation must use transactional locking.

``` sql
BEGIN;

SELECT *
FROM wallets
WHERE user_id = :user_id
FOR UPDATE;

-- Verify balance
-- Create ledger transaction
-- Update wallet
-- Create entitlement/related record

COMMIT;
```

There must never be an unsafe:

``` text
READ → SUBTRACT → WRITE
```

sequence.

------------------------------------------------------------------------

# 10. Payment Service & Regional Abstraction

The frontend does not know which payment provider is being used.

The frontend requests:

``` text
BUY COINS
```

The backend determines:

``` text
country
currency
payment channel
provider
payment method
```

Canonical abstraction:

``` python
class BaseMonetisationProvider(ABC):

    async def initiate_topup(
        self,
        user_id: str,
        pack_id: str,
        phone: str
    ):
        pass

    async def verify_webhook(
        self,
        payload: dict,
        headers: dict
    ):
        pass

    async def query_transaction(
        self,
        external_ref: str
    ):
        pass
```

Initial South African provider family:

``` text
ZA
 ├── Airtime / Direct Carrier Billing
 ├── Instant EFT
 ├── Card
 └── Voucher
```

The provider abstraction must support future:

``` text
Nigeria
Kenya
Ghana
Other African markets
Global USD
```

without rewriting wallet logic.

------------------------------------------------------------------------

# 11. Payment Settlement Flow

``` text
User
 ↓
PWA
 ↓
FastAPI
 ↓
Payment Service
 ↓
Regional Provider
 ↓
External Payment Network
 ↓
Webhook
 ↓
Verify signature
 ↓
Verify amount
 ↓
Verify currency
 ↓
Verify external reference
 ↓
Check idempotency
 ↓
PostgreSQL transaction
 ├── Payment = SUCCESS
 ├── Ledger +coins
 └── Wallet +coins
 ↓
Return / expose final state
```

Coins are granted only after verified settlement.

------------------------------------------------------------------------

# 12. Idempotency

All financial operations must be idempotent.

Examples:

``` text
payment_webhook:{provider}:{external_id}

coin_purchase:{user_id}:{request_id}

episode_unlock:{user_id}:{episode_id}
```

If a request is repeated, the original result must be returned rather
than creating another financial event.

This protects against:

-   mobile retries;
-   network duplication;
-   carrier retries;
-   provider webhook retries;
-   accidental double taps.

------------------------------------------------------------------------

# 13. Episode Unlock Flow

``` text
User
 ↓
Unlock EP07
 ↓
FastAPI
 ↓
Check entitlement
 ↓
Check wallet
 ↓
SELECT wallet FOR UPDATE
 ↓
Deduct coins
 ├── Ledger entry
 ├── Unlock entry
 └── Royalty event
 ↓
COMMIT
 ↓
Generate signed playback URL
 ↓
Return playback authorization
```

The transaction must be atomic.

------------------------------------------------------------------------

# 14. Creator Service

Responsibilities:

-   creator profiles;
-   creator verification;
-   series ownership;
-   episode creation;
-   upload authorisation;
-   publishing;
-   creator dashboard data;
-   earnings;
-   royalty statements;
-   payout status.

Creator authorisation is always enforced server-side.

A creator must never gain access to another creator's content by
changing an ID in a request.

------------------------------------------------------------------------

# 15. Direct-to-R2 Media Ingestion

Large media files must bypass FastAPI.

``` text
Creator Hub
    │
    │ Request upload authorization
    ▼
FastAPI
    │
    │ Presigned upload URL
    ▼
Cloudflare R2
    ▲
    │
    │ Direct browser upload
    │
Creator
```

This prevents:

-   API bandwidth bottlenecks;
-   container memory pressure;
-   long HTTP requests;
-   unnecessary infrastructure cost.

------------------------------------------------------------------------

# 16. Video Processing Pipeline

``` text
RAW 9:16 MASTER
       │
       ▼
Cloudflare R2
       │
       ▼
Processing Job
       │
       ├── Validate dimensions
       ├── Validate duration
       ├── Generate thumbnail
       ├── Transcode
       ├── Generate HLS
       ├── Generate subtitles
       └── AI analysis
       │
       ▼
R2 / HLS
       │
       ▼
CDN
       │
       ▼
PWA Player
```

Target output:

``` text
1080 × 1920
720 × 1280
480 × 854
360 × 640
```

HLS is the canonical delivery format.

------------------------------------------------------------------------

# 17. Background Workers

Long-running tasks must not block HTTP requests.

Worker responsibilities may include:

``` text
Video transcoding
HLS packaging
Thumbnail generation
Subtitle generation
AI analysis
Analytics aggregation
Royalty calculations
Notifications
Email / SMS
Content moderation
```

Workers must be retryable and idempotent.

Railway may initially host both the API and worker processes.

As volume grows, worker capacity can scale independently.

------------------------------------------------------------------------

# 18. Chat & Community Service

Responsibilities:

-   flying comments;
-   time-coded comments;
-   reactions;
-   threads;
-   moderation;
-   rate limiting;
-   realtime event delivery.

Architecture:

``` text
Viewer
 ↓
FastAPI
 ↓
Chat Service
 ├── PostgreSQL → persistent comments
 └── Redis/realtime layer → transient delivery
```

Community is part of the viewing experience, not merely a separate
social tab.

------------------------------------------------------------------------

# 19. Analytics Service

The platform captures events such as:

``` text
episode_impression
play_started
play_3s
play_15s
play_45s
play_completed
episode_unlocked
episode_shared
series_followed
comment_created
payment_started
payment_completed
```

These events support:

-   retention curves;
-   creator analytics;
-   content ranking;
-   cliffhanger effectiveness;
-   monetisation analysis;
-   product analytics.

High-volume analytical processing must eventually be separated from the
transactional database if scale requires it.

------------------------------------------------------------------------

# 20. AI Service

AI is an asynchronous capability.

Potential functions:

-   subtitle generation;
-   translation;
-   language detection;
-   scene analysis;
-   hook detection;
-   cliffhanger analysis;
-   content classification;
-   creator script assistance;
-   metadata generation.

AI failures must not unnecessarily destroy the core content publishing
pipeline.

Example:

``` text
Upload
 ↓
Technical validation
 ↓
Media READY
 ↓
Publish
 ↓
AI analysis asynchronously
 ↓
Creator insights / moderation flags
```

------------------------------------------------------------------------

# 21. Storage Architecture

## PostgreSQL / Supabase

Stores:

``` text
Users
Creators
Series
Episodes
Wallets
Coin Transactions
Payments
Unlocks
Royalties
Comments
Watch State
Analytics Metadata
```

## Cloudflare R2

Stores:

``` text
masters/
hls/
thumbnails/
subtitles/
creator-assets/
```

### Rule

**The database never stores video binaries.**

------------------------------------------------------------------------

# 22. Signed Media Security

Playback URLs must be:

-   signed;
-   short-lived;
-   scoped;
-   non-guessable;
-   generated only after entitlement verification.

Target expiry:

``` text
~60 seconds
```

The precise value can be tuned based on real playback behaviour.

Permanent public master-video URLs are prohibited.

------------------------------------------------------------------------

# 23. Security Architecture

## Authentication

Protected endpoints require validated identity.

## Authorisation

The backend verifies:

``` text
Who are you?
        +
Are you allowed to perform this action?
```

Examples:

``` text
Viewer → watch / unlock
Creator → manage own content
Admin → moderation / operations
```

------------------------------------------------------------------------

# 24. Rate Limiting

Rate limits should exist at:

``` text
Cloudflare
    ↓
API
    ↓
Endpoint
```

Strict limits apply to:

-   OTP;
-   authentication attempts;
-   payments;
-   voucher redemption;
-   unlock requests;
-   comments;
-   administrative endpoints.

Financial endpoints receive particularly strong protection.

------------------------------------------------------------------------

# 25. Audit Logging

Sensitive operations generate immutable audit events.

Examples:

``` text
LOGIN
OTP_EVENT
PAYMENT_INITIATED
PAYMENT_SETTLED
COINS_GRANTED
EPISODE_UNLOCKED
REFUND
CREATOR_PAYOUT
CONTENT_PUBLISHED
CONTENT_UNPUBLISHED
ADMIN_ACTION
```

Audit records must contain enough context to reconstruct important
events.

------------------------------------------------------------------------

# 26. Observability

Production must expose structured observability.

## Logs

``` text
timestamp
request_id
route
status
latency
service
error_code
user_id where appropriate
```

## Metrics

``` text
API latency
API error rate
throughput
database latency
payment success rate
payment failure rate
unlock success rate
playback authorization failures
worker failures
queue depth
```

A dedicated error-monitoring service such as Sentry or equivalent may be
used.

------------------------------------------------------------------------

# 27. Health Endpoints

``` text
GET /health
GET /ready
```

`/health` confirms process availability.

`/ready` confirms sufficient dependency availability to accept traffic.

Sensitive dependency information must not be exposed publicly.

------------------------------------------------------------------------

# 28. API Architecture

The API is versioned:

``` text
/api/v1/
```

Representative endpoints:

``` text
POST   /api/v1/auth/otp

GET    /api/v1/series
GET    /api/v1/series/{id}

GET    /api/v1/episodes/{id}
GET    /api/v1/episodes/{id}/playback

GET    /api/v1/wallet
GET    /api/v1/wallet/transactions
POST   /api/v1/wallet/purchase

POST   /api/v1/episodes/{id}/unlock

POST   /api/v1/payments/initiate
POST   /api/v1/payments/webhooks/{provider}

GET    /api/v1/creator/series
POST   /api/v1/creator/series
POST   /api/v1/creator/episodes
POST   /api/v1/creator/uploads/presign

GET    /api/v1/chat/{episode_id}
POST   /api/v1/chat/{episode_id}/comments

GET    /api/v1/admin/analytics
```

Pydantic schemas define public API contracts.

Internal database models must not automatically become public API
contracts.

------------------------------------------------------------------------

# 29. Configuration & Secrets

Secrets must never be committed to Git.

Production configuration uses managed environment variables/secrets.

Representative configuration:

``` text
DATABASE_URL

SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

REDIS_URL

R2_ENDPOINT
R2_ACCESS_KEY
R2_SECRET_KEY
R2_BUCKET

PAYMENT_PROVIDER_KEYS

AUTH_CONFIGURATION

SENTRY_DSN
```

Development, staging and production credentials are completely
separated.

------------------------------------------------------------------------

# 30. Environment Model

``` text
LOCAL
  ↓
DEVELOPMENT
  ↓
STAGING
  ↓
PRODUCTION
```

Each environment has isolated:

-   databases;
-   storage buckets;
-   authentication configuration;
-   payment credentials;
-   secrets;
-   API endpoints.

Development must use test/sandbox payment credentials.

------------------------------------------------------------------------

# 31. Railway Deployment Model

Railway is the canonical initial application compute platform.

Conceptually:

``` text
GitHub
   ↓
Railway
   ↓
Docker Build
   ↓
FastAPI Service
   │
   ├── API
   ├── Worker
   └── Scheduled Jobs
```

The API and workers may begin as separate Railway services using the
same codebase/container image.

This permits independent scaling without forcing a microservices
architecture.

------------------------------------------------------------------------

# 32. Cloudflare Pages Deployment

The React application is deployed independently:

``` text
GitHub
 ↓
Cloudflare Pages
 ↓
React / Vite build
 ↓
Global Edge
 ↓
User
```

The PWA must remain independently deployable from the backend.

Frontend deployment must not require backend downtime.

------------------------------------------------------------------------

# 33. Supabase Boundary

Supabase provides the PostgreSQL platform and managed services around
it.

The architectural boundary is:

``` text
React PWA
     ↓
FastAPI
     ↓
Supabase PostgreSQL
```

For sensitive financial operations, business logic remains behind the
controlled FastAPI service.

Supabase Row Level Security remains an additional defence layer where
appropriate.

------------------------------------------------------------------------

# 34. Failure Model

The architecture assumes components will fail.

## Redis failure

Financial operations remain functional through PostgreSQL.

## Worker failure

Jobs remain retryable.

## Payment timeout

Transaction remains pending until webhook or reconciliation resolves it.

## API instance failure

Another stateless instance handles subsequent requests.

## Upload failure

Episode remains in a recoverable processing state.

## CDN/media failure

The application remains operational even if playback is temporarily
degraded.

------------------------------------------------------------------------

# 35. Financial Reconciliation

Payment systems require periodic reconciliation.

``` text
External Provider
       ↓
Provider Transactions
       ↓
Reconciliation Worker
       ↓
Compare with PostgreSQL
       ↓
 ┌─────────┬──────────┬──────────┐
 │ MATCH   │ MISSING  │ DUPLICATE│
 └─────────┴──────────┴──────────┘
             ↓
          DISPUTED
```

Discrepancies must be surfaced for investigation rather than silently
overwritten.

------------------------------------------------------------------------

# 36. Creator Royalty Architecture

Creator revenue derives from verified commercial events.

``` text
Payment
 ↓
Coins
 ↓
Episode Unlock
 ↓
Eligible Revenue
 ↓
Royalty Calculation
 ↓
Creator Ledger
 ↓
Payout
```

Royalty statements must be reproducible from transaction history.

Mutable aggregates alone are insufficient as the financial record.

------------------------------------------------------------------------

# 37. CI/CD

``` text
Developer
 ↓
GitHub
 ↓
Pull Request
 ↓
Tests
 ↓
Lint / Type Checks
 ↓
Docker Build
 ↓
Security Checks
 ↓
Staging
 ↓
Validation
 ↓
Production
```

Database migrations are version-controlled.

Production migrations are deliberate and tested.

------------------------------------------------------------------------

# 38. Scaling Path

## Stage 1 --- Launch

``` text
Cloudflare Pages
       +
Railway FastAPI
       +
Supabase
       +
R2
```

## Stage 2 --- Growing Audience

``` text
Cloudflare
     ↓
Railway API × N
     ↓
Supabase
     +
Redis
     +
Railway Workers × N
```

## Stage 3 --- High Volume

Extract only the domains that justify independent scaling:

``` text
                 API Gateway
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 Content Service   Wallet Service   Creator Service
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Data Platform
```

Possible extraction candidates:

-   video processing;
-   analytics;
-   chat/realtime;
-   payments;
-   creator processing.

Extraction is driven by measurable requirements, not fashion.

------------------------------------------------------------------------

# 39. Explicit Anti-Patterns

The following are prohibited:

### ❌ Streaming video through FastAPI

### ❌ Storing video binaries in PostgreSQL

### ❌ Using Redis as the financial ledger

### ❌ Trusting the frontend to calculate balances

### ❌ Granting coins before verified payment settlement

### ❌ Processing payment webhooks without idempotency

### ❌ Storing permanent public video URLs

### ❌ Uploading large media through the API container

### ❌ Running FFmpeg/AI jobs inside normal HTTP requests

### ❌ Building microservices merely for appearance

### ❌ Allowing creator access without server-side ownership checks

### ❌ Committing production secrets to source control

------------------------------------------------------------------------

# 40. Canonical End-to-End Flows

## Viewer Playback

``` text
PWA
 ↓
GET episode metadata
 ↓
FastAPI
 ↓
PostgreSQL
 ↓
Episode state
 ↓
Request playback
 ↓
Entitlement check
 ↓
Signed URL
 ↓
Cloudflare
 ↓
R2
 ↓
HLS playback
```

## Episode Unlock

``` text
PWA
 ↓
POST unlock
 ↓
FastAPI
 ↓
PostgreSQL transaction
 ├── Lock wallet
 ├── Verify balance
 ├── Deduct coins
 ├── Ledger
 ├── Unlock
 └── Royalty event
 ↓
COMMIT
 ↓
Playback authorization
```

## Creator Upload

``` text
Creator Hub
 ↓
Request presigned upload
 ↓
FastAPI
 ↓
R2 upload URL
 ↓
Browser → R2
 ↓
Worker
 ↓
Validate / Transcode / HLS
 ↓
AI / Subtitle processing
 ↓
Episode READY
 ↓
Creator publishes
```

## Payment

``` text
PWA
 ↓
Payment request
 ↓
FastAPI
 ↓
Regional Provider
 ↓
External network
 ↓
Webhook
 ↓
Verify + Idempotency
 ↓
PostgreSQL transaction
 ↓
Coins
```

------------------------------------------------------------------------

# 41. Backend Architectural Contract

The Welele backend SHALL satisfy the following:

1.  **FastAPI is the application orchestration layer.**
2.  **Railway is the canonical initial compute platform.**
3.  **Cloudflare Pages is the canonical frontend deployment platform.**
4.  **Cloudflare R2 is the canonical media object-storage platform.**
5.  **Supabase PostgreSQL is the transactional source of truth.**
6.  **The financial ledger is immutable and auditable.**
7.  **Wallet mutations are transactional and concurrency-safe.**
8.  **Payment processing is provider-agnostic through adapters.**
9.  **Payment webhooks are verified and idempotent.**
10. **Video binaries never pass through FastAPI during normal
    playback.**
11. **Large media uploads go directly to R2.**
12. **Playback uses short-lived signed URLs.**
13. **Background processing is asynchronous and retryable.**
14. **Application instances are stateless.**
15. **Redis accelerates the platform but never becomes financial
    truth.**
16. **Creator ownership and permissions are enforced server-side.**
17. **Production secrets remain outside source control.**
18. **The API is versioned.**
19. **Observability is part of production architecture.**
20. **The initial backend is a modular monolith.**
21. **Service extraction occurs only when measurable requirements
    justify it.**
22. **The logical architecture must remain portable independently of
    infrastructure vendors.**

------------------------------------------------------------------------

# 42. Relationship to the Welele 8-Pillar Architecture

This backend architecture directly implements the eight frozen Welele
pillars:

``` text
1. 9:16 Canonical Viewer
       ↓
   Playback + Media Pipeline

2. PWA First
       ↓
   Cloudflare Pages

3. Relational Transaction Core
       ↓
   Supabase PostgreSQL

4. Object Storage + CDN
       ↓
   Cloudflare R2 + Edge

5. Unified Payment Abstraction
       ↓
   Payment Service + Provider Interface

6. Regional Monetisation
       ↓
   Regional Provider Adapters

7. Content as Primary Asset
       ↓
   Content + Creator + Media Services

8. Community Embedded in Stream
       ↓
   Chat + Realtime + Analytics
```

------------------------------------------------------------------------

# 43. Architecture Freeze

This document is part of the canonical Welele Media™ engineering
documentation.

The following decisions are considered frozen for v1:

``` text
Frontend
    → Cloudflare Pages

Backend
    → FastAPI on Railway

Database
    → Supabase PostgreSQL

Media
    → Cloudflare R2

Edge
    → Cloudflare

Architecture Pattern
    → Modular Monolith

Video Path
    → CDN/R2 direct delivery

Financial Authority
    → PostgreSQL Ledger

Payment Pattern
    → Regional Provider Abstraction
```

Changes to these architectural principles require explicit architecture
review.

------------------------------------------------------------------------

# 44. Final Engineering Principle

> **Welele's backend exists to protect the transaction, orchestrate the
> ecosystem, empower creators and unlock the content.**

> **It does not need to carry the content itself.**

The platform should remain technically quiet while the stories become
culturally loud.

------------------------------------------------------------------------

**Document:** Welele Media™ --- Backend Services Architecture\
**Version:** 1.1\
**Status:** LOCKED & CANONICAL\
**Date:** 2026-09-07\
**Architecture Owner:** Welele Engineering & Leadership
