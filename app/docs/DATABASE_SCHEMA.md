# WELELE MEDIA™ — DATABASE SCHEMA SPECIFICATION
**Document ID:** `WELELE-DOCS-DB-001`  
**Database Engine:** PostgreSQL 15+ (Supabase Managed Instance)  
**Primary Extensions:** `uuid-ossp`, `pgcrypto`

---

## 1. Relational Entity Architecture

```
                               ┌───────────────┐
                               │     USERS     │
                               └───────┬───────┘
                                       │ 1:1
                                       ▼
 ┌──────────────┐ 1:N ┌────────────────┴───────────────┐ 1:1 ┌───────────────┐
 │ COIN_LEDGER  │◄────┤            WALLETS            ├────►│   CREATORS    │
 └──────────────┘     │   (Materialized Projection)   │     └───────┬───────┘
                      └───────────────────────────────┘             │
                                                                    │ 1:N
                                                                    ▼
 ┌──────────────┐ 1:N ┌───────────────────────────────┐ 1:N ┌───────────────┐
 │ VIDEO_ASSETS │◄────┤            EPISODES           │◄────┤    STORIES    │
 └──────────────┘     └───────────────┬───────────────┘     └───────────────┘
                                      │ 1:N
                                      ▼
                      ┌───────────────────────────────┐
                      │    EVENTS / COMMENTS / LIKES  │
                      └───────────────────────────────┘
```

---

## 2. Table Definitions

### 2.1 `users`
Represents viewer accounts across mobile and desktop.
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(32) UNIQUE,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(128) NOT NULL,
    avatar_url TEXT,
    region_code VARCHAR(8) DEFAULT 'ZA',
    preferred_language VARCHAR(32) DEFAULT 'isiZulu',
    is_creator BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.2 `creators`
Stores verified African showrunners, directors, and production houses.
```sql
CREATE TABLE creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stage_name VARCHAR(128) NOT NULL,
    bio TEXT,
    country VARCHAR(64) NOT NULL DEFAULT 'South Africa',
    payout_account_details JSONB DEFAULT '{}'::jsonb,
    is_verified BOOLEAN DEFAULT FALSE,
    total_views BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.3 `stories` (Series Catalog)
High-level micro-drama series metadata.
```sql
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES creators(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    tagline VARCHAR(255),
    synopsis TEXT NOT NULL,
    cover_image TEXT NOT NULL,
    vertical_poster TEXT NOT NULL,
    genre VARCHAR(64) NOT NULL,
    language VARCHAR(64) NOT NULL DEFAULT 'isiZulu',
    available_languages TEXT[] DEFAULT ARRAY['isiZulu', 'English'],
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    rating NUMERIC(3,2) DEFAULT 4.95,
    total_episodes INT DEFAULT 0,
    free_episodes INT DEFAULT 3,
    coin_price_per_episode INT DEFAULT 5,
    is_original BOOLEAN DEFAULT TRUE,
    is_trending BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.4 `video_assets` (Media Reference Model)
Encapsulates transcoding status, HLS manifests, and rendition ladders.
```sql
CREATE TABLE video_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    storage_key VARCHAR(512) UNIQUE NOT NULL,
    master_url TEXT NOT NULL,
    hls_manifest_url TEXT,
    thumbnail_url TEXT,
    duration_seconds NUMERIC(6,2) NOT NULL,
    resolution_w INT DEFAULT 1080,
    resolution_h INT DEFAULT 1920,
    codec VARCHAR(64) DEFAULT 'H.264/AAC',
    bitrate_kbps INT DEFAULT 4500,
    renditions JSONB DEFAULT '{
        "1080p": {"width": 1080, "height": 1920, "bitrate_kbps": 4500},
        "720p":  {"width": 720,  "height": 1280, "bitrate_kbps": 2200},
        "480p":  {"width": 480,  "height": 854,  "bitrate_kbps": 900},
        "360p":  {"width": 360,  "height": 640,  "bitrate_kbps": 450}
    }'::jsonb,
    processing_status VARCHAR(32) DEFAULT 'READY' CHECK (processing_status IN ('QUEUED', 'TRANSCODING', 'READY', 'FAILED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 `episodes`
Individual 60-to-90 second vertical micro-drama chapters.
```sql
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    video_asset_id UUID REFERENCES video_assets(id) ON DELETE RESTRICT,
    episode_number INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    synopsis TEXT,
    is_free BOOLEAN DEFAULT FALSE,
    coin_price INT DEFAULT 5,
    cliffhanger_time INT DEFAULT 60,
    cliffhanger_hook TEXT,
    views_count BIGINT DEFAULT 0,
    likes_count BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(story_id, episode_number)
);
```

### 2.6 `coin_ledger` (Financial Source of Truth)
Immutable append-only ledger tracking all credit and debit entries.
```sql
CREATE TABLE coin_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE RESTRICT,
    transaction_type VARCHAR(32) NOT NULL CHECK (transaction_type IN ('PURCHASE', 'AIRTIME_PASS', 'EPISODE_UNLOCK', 'GIFT_SENT', 'CREATOR_PAYOUT', 'BONUS_GRANT')),
    entry_type VARCHAR(8) NOT NULL CHECK (entry_type IN ('CREDIT', 'DEBIT')),
    coins_amount INT NOT NULL CHECK (coins_amount > 0),
    balance_after INT NOT NULL,
    currency VARCHAR(8) DEFAULT 'ZAR',
    local_amount NUMERIC(10,2) DEFAULT 0.00,
    payment_method VARCHAR(64) NOT NULL,
    reference_id VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.7 `wallets` (Materialized Balance Cache)
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    coin_balance INT DEFAULT 0,
    bonus_coins INT DEFAULT 0,
    lifetime_coins_purchased INT DEFAULT 0,
    lifetime_coins_spent INT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.8 `platform_events` (Telemetry Ingestion Engine)
```sql
CREATE TABLE platform_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name VARCHAR(64) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    story_id UUID REFERENCES stories(id) ON DELETE SET NULL,
    episode_id UUID REFERENCES episodes(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_region VARCHAR(8) DEFAULT 'ZA',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```
