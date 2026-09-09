# Welele Media™ --- Backend Services Architecture

**Version:** 1.0\
**Status:** LOCKED & CANONICAL\
**Architecture State:** Frozen\
**Target Runtime:** Containerised Python 3.11+ / FastAPI\
**Primary Database:** PostgreSQL via Supabase\
**Primary Object Storage:** Cloudflare R2 / S3-compatible storage\
**Initial Compute:** Google Cloud Run (or equivalent container
platform)\
**Core Principle:** **The backend authorises, orchestrates and records.
It does not carry video traffic.**

------------------------------------------------------------------------

## 1. Purpose

This document locks the architecture of the Welele Media™ backend
application layer.

The backend is the authoritative application brain between the PWA,
persistent data systems, object storage, realtime infrastructure and
regional monetisation providers.

It is deliberately designed to begin as a **modular monolith** rather
than a collection of independently deployed microservices.

The architecture must remain:

-   stateless at the application tier;
-   horizontally scalable;
-   transactionally authoritative;
-   provider-agnostic for payments;
-   storage-agnostic where practical;
-   independent of video transport;
-   secure by default;
-   observable;
-   suitable for Pan-African expansion.

> **Architectural Rule:** Welele may start with one FastAPI deployment,
> but its internal domain boundaries must be clean enough that
> individual services can be extracted later without redesigning the
> business model.

------------------------------------------------------------------------

# 2. Backend Position in the Overall Architecture

``` text
                         USERS
                           │
                           ▼
                  ┌─────────────────┐
                  │    CLOUDFLARE   │
                  │ DNS / WAF / SSL │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌───────────────┐        ┌────────────────┐
       │    VERCEL     │        │  R2 / S3 + CDN │
       │ React PWA     │        │ Video Delivery │
       │ Creator Studio│        └────────────────┘
       └───────┬───────┘
               │
               │ REST / WebSocket
               ▼
       ┌───────────────────────┐
       │    FASTAPI BACKEND    │
       │                       │
       │ Auth                  │
       │ Content               │
       │ Episodes              │
       │ Wallet                │
       │ Payments              │
       │ Chat                  │
       │ Creator               │
       │ Analytics             │
       │ AI orchestration      │
       │ Administration        │
       └───────────┬───────────┘
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
     ┌────────┐ ┌───────┐ ┌─────────┐
     │Supabase│ │ Redis │ │ Workers │
     │Postgres│ │ Cache │ │ Jobs    │
     └────────┘ └───────┘ └─────────┘
          │
          ▼
   ┌─────────────────────┐
   │ PAYMENT PROVIDERS   │
   │ Regional Adapters   │
   └─────────────────────┘
```

------------------------------------------------------------------------

# 3. Non-Negotiable Backend Principles

## 3.1 Stateless Application Tier

FastAPI instances must not depend on local process memory for persistent
state.

Any instance must be able to process any request.

``` text
Request
   ↓
Cloud Load Balancer / Cloud Run
   ↓
Any FastAPI instance
   ↓
PostgreSQL / Redis / Object Storage
```

No business-critical state may live only inside:

-   Python globals;
-   process memory;
-   local filesystem;
-   container-local databases;
-   container-local uploaded files.

------------------------------------------------------------------------

## 3.2 PostgreSQL Is the Transactional Authority

PostgreSQL is authoritative for:

-   users;
-   wallets;
-   coin balances;
-   coin transactions;
-   payment transactions;
-   episode unlocks;
-   creator earnings;
-   royalty calculations;
-   series;
-   episodes;
-   permissions;
-   entitlement state;
-   important watch-state records.

Redis may accelerate access, but Redis is never the financial source of
truth.

------------------------------------------------------------------------

## 3.3 Video Bypasses the Backend

The FastAPI application must **never become the video streaming
server**.

The backend:

1.  authenticates the user;
2.  verifies entitlement;
3.  generates or requests a signed playback URL;
4.  returns the authorised stream location.

The client then retrieves video directly from the CDN/object-storage
layer.

``` text
PWA
 │
 │ "Can I watch EP07?"
 ▼
FastAPI
 │
 │ entitlement check
 ▼
PostgreSQL
 │
 │ authorised
 ▼
FastAPI
 │
 │ signed URL
 ▼
PWA
 │
 │ HLS
 ▼
Cloudflare CDN
 │
 ▼
R2 / S3
```

This separation is mandatory for cost, performance and scalability.

------------------------------------------------------------------------

# 4. Deployment Model

## Initial Production Deployment

``` text
Frontend
    → Vercel

DNS / WAF / Edge
    → Cloudflare

Backend
    → Containerised FastAPI on Cloud Run

Database
    → Supabase PostgreSQL

Object Storage
    → Cloudflare R2

Cache / Realtime Support
    → Redis-compatible managed service

Background Processing
    → Containerised Workers / Cloud Run Jobs

Source Control
    → GitHub
```

The exact cloud provider for compute may change without changing the
application architecture.

Equivalent container platforms include:

-   AWS ECS/Fargate;
-   Google Cloud Run;
-   Azure Container Apps;
-   another standards-compliant container platform.

The backend application must remain portable.

------------------------------------------------------------------------

# 5. FastAPI Application Structure

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

# 6. Domain Service Boundaries

The initial backend is one deployable application but contains explicit
domains.

## 6.1 Auth Service

Responsibilities:

-   phone OTP authentication;
-   Google authentication;
-   guest/anonymous sessions;
-   session validation;
-   token verification;
-   account linking;
-   region assignment;
-   user profile basics.

Authentication credentials should not be reinvented inside Welele when a
managed identity provider can securely provide the primitive.

------------------------------------------------------------------------

# 6.2 Content Service

Responsibilities:

-   series catalogue;
-   genres;
-   creators;
-   series metadata;
-   publication status;
-   episode ordering;
-   thumbnails;
-   languages;
-   age classifications;
-   discovery metadata.

Content metadata belongs in PostgreSQL.

Media binaries belong in object storage.

------------------------------------------------------------------------

# 6.3 Episode Service

Responsibilities:

-   episode metadata;
-   episode numbering;
-   duration;
-   coin price;
-   free/gated status;
-   cliffhanger timing;
-   subtitle references;
-   publication lifecycle;
-   watch-state association.

Example lifecycle:

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
UNPUBLISHED / ARCHIVED
```

An episode must not become publicly playable merely because an MP4
upload exists.

------------------------------------------------------------------------

# 6.4 Playback / Entitlement Service

This service is the security boundary between content ownership and
video delivery.

Responsibilities:

-   determine whether an episode is free;
-   determine whether the user has unlocked it;
-   verify account/session state;
-   generate signed playback URLs;
-   enforce expiry;
-   record playback initiation;
-   optionally enforce geographic/content restrictions.

Conceptual API:

``` text
GET /episodes/{episode_id}/playback
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

The URL must be short-lived.

------------------------------------------------------------------------

# 6.5 Wallet Service

Responsibilities:

-   wallet creation;
-   balance retrieval;
-   coin packs;
-   bonus coins;
-   balance checks;
-   unlock requests;
-   transaction coordination.

The wallet service must never modify balances through an unsafe
read/write sequence.

Incorrect:

``` text
read balance
subtract 5
write balance
```

Correct:

``` text
BEGIN

SELECT wallet
FOR UPDATE

verify balance

create ledger entries

update balance

create unlock

COMMIT
```

------------------------------------------------------------------------

# 6.6 Ledger Service

The ledger is the financial integrity boundary.

Every coin movement must have an immutable transaction record.

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

Each transaction must have:

-   unique ID;
-   wallet ID;
-   signed amount/direction;
-   transaction type;
-   reference;
-   idempotency key where applicable;
-   timestamp;
-   audit metadata.

No endpoint may silently mutate a wallet balance without creating the
corresponding ledger event.

------------------------------------------------------------------------

# 6.7 Payment Service

Payment Service orchestrates external payment providers.

It does not expose provider-specific concepts to the frontend.

Frontend sees:

``` text
BUY COINS
```

Backend resolves:

``` text
country
currency
channel
provider
payment method
```

Example:

``` text
ZA
 │
 ├── Airtime
 ├── Ozow
 ├── Card
 └── Voucher
```

The provider-specific adapter remains behind the common interface.

------------------------------------------------------------------------

# 6.8 Creator Service

Responsibilities:

-   creator profiles;
-   series ownership;
-   episode creation;
-   upload authorisation;
-   content publishing;
-   creator dashboards;
-   earnings visibility;
-   content status.

Creator Studio communicates with the same backend API as the viewer
application.

------------------------------------------------------------------------

# 6.9 Storage Service

The storage service abstracts object storage.

Responsibilities:

-   presigned upload URLs;
-   upload validation;
-   object naming;
-   media lifecycle;
-   signed playback URLs;
-   thumbnails;
-   subtitles;
-   processed media references.

The application should not assume that storage is permanently tied to
one provider.

------------------------------------------------------------------------

# 6.10 Chat Service

Responsibilities:

-   time-coded comments;
-   reactions;
-   comment moderation;
-   thread metadata;
-   rate limiting;
-   realtime event delivery.

Realtime events may use Redis or another realtime layer.

Persistent moderation-relevant content remains in PostgreSQL.

------------------------------------------------------------------------

# 6.11 Analytics Service

The backend captures events such as:

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

The backend should capture events without placing analytics queries on
the critical transaction path.

High-volume analytics may later move to a dedicated event/warehouse
architecture.

------------------------------------------------------------------------

# 6.12 AI Service

AI capabilities are asynchronous wherever possible.

Examples:

-   subtitle generation;
-   language detection;
-   scene analysis;
-   hook detection;
-   cliffhanger verification;
-   content classification;
-   creator script assistance.

AI must not block the core publish path unnecessarily.

Example:

``` text
Upload
  ↓
Media Processing
  ↓
Technical Validation
  ↓
READY
  ↓
AI Analysis
  ↓
Insights / Flags
```

------------------------------------------------------------------------

# 7. Object Storage & Direct Upload Architecture

Creator uploads must use direct-to-object-storage ingestion.

``` text
Creator Studio
      │
      │ metadata
      ▼
FastAPI
      │
      │ presigned URL
      ▼
Cloudflare R2
      │
      │ upload
      ▼
Raw Media
```

The browser must not upload large media through FastAPI.

This prevents:

-   API bandwidth bottlenecks;
-   excessive container memory usage;
-   request timeout problems;
-   unnecessary compute costs.

------------------------------------------------------------------------

# 8. Background Worker Architecture

Long-running operations must not block normal API requests.

Worker candidates:

``` text
Video transcoding
HLS packaging
Thumbnail extraction
Subtitle generation
AI analysis
Analytics aggregation
Royalty calculations
Notifications
Email/SMS jobs
```

Conceptual queue:

``` text
FastAPI
   │
   ▼
Job Queue
   │
   ├── Video Worker
   ├── AI Worker
   ├── Analytics Worker
   └── Royalty Worker
```

Workers must be idempotent.

A failed job must be safely retryable.

------------------------------------------------------------------------

# 9. Payment Transaction Flow

``` text
User
 │
 │ Buy 100 Coins
 ▼
FastAPI
 │
 ▼
Payment Service
 │
 ▼
Regional Provider Adapter
 │
 ▼
External Provider
 │
 │ payment result
 ▼
Webhook
 │
 ▼
FastAPI
 │
 ├── verify signature
 ├── verify amount
 ├── verify currency
 ├── verify external reference
 ├── check idempotency
 │
 ▼
PostgreSQL Transaction
 │
 ├── payment = SUCCESS
 ├── ledger +100
 └── wallet balance +100
```

Coin allocation occurs **only after verified payment settlement**.

------------------------------------------------------------------------

# 10. Episode Unlock Transaction

An unlock is an atomic financial transaction.

``` text
User requests EP07
       │
       ▼
Check entitlement
       │
       ├── already unlocked → playback
       │
       └── not unlocked
                │
                ▼
          Check coin balance
                │
                ▼
          SELECT wallet FOR UPDATE
                │
                ▼
          Deduct coins
                │
                ├── ledger entry
                ├── unlock entry
                └── creator royalty entry
                │
                ▼
              COMMIT
                │
                ▼
        Generate playback URL
```

There must be no state in which:

-   coins are deducted but unlock is missing;
-   unlock exists but coins were not deducted;
-   payment webhook grants coins twice;
-   creator royalty is duplicated.

------------------------------------------------------------------------

# 11. Idempotency

All financial operations must support idempotency.

Examples:

``` text
payment_webhook:{provider}:{external_id}
coin_purchase:{user_id}:{client_request_id}
episode_unlock:{user_id}:{episode_id}
```

Repeated requests must return the original result rather than creating a
second transaction.

This is mandatory because mobile networks, payment providers and clients
can retry requests.

------------------------------------------------------------------------

# 12. API Design

The public API is versioned.

``` text
/api/v1/
```

Example:

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

API responses should use explicit Pydantic schemas.

Internal database models must not automatically become public API
contracts.

------------------------------------------------------------------------

# 13. Security Architecture

## Authentication

Every protected endpoint requires a validated user identity.

## Authorisation

Authentication answers:

> Who are you?

Authorisation answers:

> Are you allowed to do this?

Examples:

``` text
Viewer → watch
Viewer → unlock

Creator → manage own series
Creator → publish own episode

Admin → moderation
Admin → platform operations
```

Creators must never be able to access another creator's resources by
manipulating UUIDs.

------------------------------------------------------------------------

# 14. Signed Media URLs

Playback URLs should be:

-   signed;
-   short-lived;
-   scoped to the intended media;
-   impossible to infer from database IDs alone.

Target TTL:

``` text
~60 seconds
```

The exact TTL may be tuned based on playback behaviour.

The application must not expose permanent public master-video URLs.

------------------------------------------------------------------------

# 15. Rate Limiting

Rate limiting must exist at multiple levels.

``` text
Cloudflare
   ↓
API rate limits
   ↓
Endpoint-specific limits
```

Higher restrictions should apply to:

-   OTP requests;
-   login attempts;
-   payment initiation;
-   voucher redemption;
-   comment posting;
-   unlock requests;
-   administrative operations.

Financial endpoints require particularly strict controls.

------------------------------------------------------------------------

# 16. Audit Logging

Sensitive actions must generate audit events.

Examples:

``` text
LOGIN
PASSWORD/OTP_EVENT
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

Audit records must contain sufficient context to reconstruct important
events.

------------------------------------------------------------------------

# 17. Database Transaction Rules

The following operations require PostgreSQL transactions:

-   wallet mutation;
-   coin purchase allocation;
-   episode unlock;
-   refund;
-   royalty allocation;
-   creator payout state changes;
-   payment settlement.

Use row-level locking where concurrent writes can affect the same
financial resource.

``` sql
SELECT *
FROM wallets
WHERE user_id = :user_id
FOR UPDATE;
```

Do not rely on frontend state to prevent double spending.

------------------------------------------------------------------------

# 18. Caching Strategy

Redis may cache:

-   trending series;
-   catalogue fragments;
-   user session state;
-   rate-limit counters;
-   realtime presence;
-   temporary upload state;
-   frequently requested non-financial metadata.

Never cache authoritative wallet state as the only source.

Cache invalidation must occur when underlying content changes.

------------------------------------------------------------------------

# 19. Observability

Production backend must provide:

### Logs

Structured JSON logs containing:

``` text
timestamp
request_id
user_id where appropriate
route
status
latency
error_code
service
```

### Metrics

At minimum:

``` text
request latency
error rate
API throughput
database latency
Redis latency
payment success rate
payment failure rate
unlock success rate
video-authorisation failures
worker failures
queue depth
```

### Error Tracking

Use a dedicated error-monitoring system such as Sentry or equivalent.

------------------------------------------------------------------------

# 20. Health Endpoints

Required endpoints:

``` text
GET /health
GET /ready
```

`/health` verifies process availability.

`/ready` verifies that required dependencies are available sufficiently
for the instance to receive traffic.

Do not expose sensitive dependency details publicly.

------------------------------------------------------------------------

# 21. Configuration & Secrets

No secrets may be committed to Git.

Configuration is supplied through environment variables / managed secret
storage.

Examples:

``` text
DATABASE_URL
REDIS_URL

SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

R2_ENDPOINT
R2_ACCESS_KEY
R2_SECRET_KEY
R2_BUCKET

PAYMENT_PROVIDER_KEYS

JWT / AUTH CONFIGURATION

SENTRY_DSN
```

Production and development credentials must be completely separated.

------------------------------------------------------------------------

# 22. Container Architecture

The FastAPI application must be containerised.

Conceptual image:

``` text
Python 3.11+
     ↓
FastAPI
     ↓
Uvicorn
     ↓
Docker Image
     ↓
Container Registry
     ↓
Cloud Run / ECS / Container Apps
```

Containers must be disposable.

A container can be destroyed and recreated without losing application
state.

------------------------------------------------------------------------

# 23. Horizontal Scaling

The backend must support:

``` text
             Cloudflare
                  │
                  ▼
            API Platform
          ┌───────┼───────┐
          ▼       ▼       ▼
       API-01  API-02  API-03
          │       │       │
          └───────┼───────┘
                  ▼
              PostgreSQL
```

No sticky sessions should be required for ordinary REST requests.

Realtime connections may use the appropriate shared infrastructure.

------------------------------------------------------------------------

# 24. Failure Principles

The platform must assume components will fail.

### If Redis fails

Core financial operations remain functional using PostgreSQL.

### If a worker fails

The job remains retryable.

### If payment provider times out

The transaction remains pending and is resolved by webhook or
reconciliation.

### If CDN fails

The API remains operational, although video playback may be unavailable.

### If an API instance dies

Another stateless instance handles the next request.

### If an upload fails

The episode remains in an incomplete processing state and can be
retried.

------------------------------------------------------------------------

# 25. Reconciliation

Payment systems must support periodic reconciliation.

``` text
External Provider
       │
       ▼
Provider Transactions
       │
       ▼
Welele Reconciliation Worker
       │
       ▼
Compare against PostgreSQL
       │
       ├── MATCH
       ├── MISSING
       ├── DUPLICATE
       └── DISPUTED
```

Financial discrepancies must be surfaced rather than silently corrected.

------------------------------------------------------------------------

# 26. Creator Royalty Boundary

Creator revenue must be derived from verified commercial events.

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

Royalty calculations must be reproducible from immutable transaction
history.

Never rely on a mutable aggregate alone.

------------------------------------------------------------------------

# 27. API / Database Separation

The frontend communicates with the API.

The frontend should not directly manipulate protected financial tables.

``` text
React PWA
    │
    ▼
FastAPI
    │
    ▼
Domain Services
    │
    ▼
PostgreSQL
```

Supabase client functionality may be used where appropriate for managed
authentication or safe public data access, but business-critical
financial operations remain behind controlled backend transactions.

------------------------------------------------------------------------

# 28. Environment Architecture

At minimum:

``` text
LOCAL
  ↓
DEVELOPMENT
  ↓
STAGING
  ↓
PRODUCTION
```

Each environment must have isolated:

-   databases;
-   storage buckets;
-   payment credentials;
-   authentication configuration;
-   secrets;
-   API endpoints.

Production payment credentials must never be used in development.

------------------------------------------------------------------------

# 29. CI/CD

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
Deploy Staging
   ↓
Validation
   ↓
Production Deployment
```

Database migrations must be version-controlled.

Production migrations must be deliberate and reversible where practical.

------------------------------------------------------------------------

# 30. Modular Monolith → Selective Services

The initial architecture is:

``` text
                 FASTAPI
        ┌─────────┼──────────┐
        │         │          │
      Wallet    Content    Creator
        │         │          │
      Payment    Chat       AI
```

This is a **modular monolith**.

If scale requires extraction, domains can become independently deployed
services:

``` text
                 API Gateway
                     │
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
 Content Service  Wallet Service  Creator Service
      │              │               │
      └──────────────┼───────────────┘
                     ▼
                Shared Data
```

Extraction is driven by:

-   scale;
-   deployment independence;
-   team ownership;
-   fault isolation;
-   measurable performance requirements.

Microservices are not an architectural goal by themselves.

------------------------------------------------------------------------

# 31. Explicit Anti-Patterns

The following are prohibited:

### ❌ Streaming video through FastAPI

### ❌ Storing video binaries in PostgreSQL

### ❌ Using Redis as the financial ledger

### ❌ Trusting the frontend to calculate coin balances

### ❌ Granting coins before verified payment settlement

### ❌ Processing payment webhooks without idempotency

### ❌ Storing permanent public video URLs

### ❌ Uploading large video files through the API container

### ❌ Putting long-running FFmpeg/AI jobs inside HTTP requests

### ❌ Building microservices merely for architectural appearance

### ❌ Allowing creator access without ownership checks

------------------------------------------------------------------------

# 32. Canonical Backend Request Patterns

## Viewer Playback

``` text
PWA
 ↓
GET episode
 ↓
FastAPI
 ↓
PostgreSQL metadata
 ↓
Return episode state
 ↓
Request playback
 ↓
Entitlement check
 ↓
Signed URL
 ↓
CDN
 ↓
R2
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
 ├── lock wallet
 ├── verify balance
 ├── deduct coins
 ├── create ledger entry
 ├── create unlock
 └── create royalty event
 ↓
COMMIT
 ↓
Signed playback URL
```

## Creator Upload

``` text
Creator Studio
 ↓
POST presign
 ↓
FastAPI
 ↓
R2 signed upload URL
 ↓
Browser → R2
 ↓
Processing job
 ↓
Worker / FFmpeg
 ↓
HLS assets
 ↓
R2
 ↓
Episode READY
```

## Payment

``` text
PWA
 ↓
POST payment
 ↓
FastAPI
 ↓
Regional Provider Adapter
 ↓
External Provider
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

# 33. Backend Architectural Contract

The Welele backend SHALL satisfy the following:

1.  **FastAPI is the application orchestration layer.**
2.  **PostgreSQL is the transactional source of truth.**
3.  **The financial ledger is immutable and auditable.**
4.  **Wallet mutations are transactional and concurrency-safe.**
5.  **Payment processing is provider-agnostic through adapters.**
6.  **Payment webhooks are cryptographically verified and idempotent.**
7.  **Video binaries never pass through FastAPI during normal
    playback.**
8.  **Large media uploads go directly to object storage.**
9.  **Playback is authorised through short-lived signed URLs.**
10. **Background processing is asynchronous and retryable.**
11. **Application instances are stateless and horizontally scalable.**
12. **Redis accelerates the system but never becomes financial truth.**
13. **Creator ownership and authorisation are enforced server-side.**
14. **Production secrets are managed outside source control.**
15. **The API is versioned.**
16. **Observability is built into production deployment.**
17. **The initial deployment is a modular monolith.**
18. **Services may be extracted only when measurable requirements
    justify extraction.**

------------------------------------------------------------------------

# 34. Architecture Freeze

This document forms part of the canonical Welele Media™ architecture.

The backend implementation may evolve internally, but changes to the
following require an explicit architecture review:

-   database authority;
-   wallet/ledger model;
-   payment abstraction;
-   video delivery path;
-   object-storage strategy;
-   stateless application principle;
-   direct media ingestion;
-   entitlement architecture;
-   provider abstraction;
-   modular-monolith boundary.

**Architecture Version:** 1.0\
**Status:** LOCKED\
**Date:** 2026-09-07

> **Final Principle:**\
> **Welele's backend exists to protect the transaction, orchestrate the
> ecosystem and unlock the content. It does not need to carry the
> content itself.**
