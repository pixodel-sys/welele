-- ============================================================================
-- WELELE MEDIA™ — POSTGRESQL / SUPABASE PRODUCTION DATABASE SCHEMA
-- Canonical Architecture Freeze v1.0
-- Core: Relational Transactional Integrity, Double-Entry Coin Ledgers,
--       CDN Video Pointers, and Time-synced Stream Comments.
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. USERS & PROFILES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(32) UNIQUE,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    region_code VARCHAR(8) NOT NULL DEFAULT 'ZA', -- e.g. ZA, NG, KE, GH
    preferred_language VARCHAR(32) NOT NULL DEFAULT 'isiZulu',
    is_creator BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON public.users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_region ON public.users(region_code);

-- ----------------------------------------------------------------------------
-- 2. CREATORS & STUDIOS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stage_name VARCHAR(120) NOT NULL,
    bio TEXT,
    country VARCHAR(8) NOT NULL DEFAULT 'ZA',
    is_verified BOOLEAN NOT NULL DEFAULT TRUE,
    total_views BIGINT NOT NULL DEFAULT 0,
    lifetime_earnings_zar NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. STORIES / SERIES CATALOG (Metadata Only - No video binaries)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES public.creators(id) ON DELETE SET NULL,
    creator_name VARCHAR(120) NOT NULL,
    creator_avatar TEXT,
    title VARCHAR(200) NOT NULL,
    synopsis TEXT NOT NULL,
    genre VARCHAR(60) NOT NULL, -- e.g. 'Dynasty & Thriller', 'Crime & Action'
    cover_image TEXT NOT NULL,  -- Object Storage / CDN URI
    rating NUMERIC(3, 1) NOT NULL DEFAULT 4.8,
    total_views BIGINT NOT NULL DEFAULT 0,
    total_episodes INT NOT NULL DEFAULT 0,
    free_episodes INT NOT NULL DEFAULT 3,
    is_trending BOOLEAN NOT NULL DEFAULT FALSE,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    available_languages TEXT[] NOT NULL DEFAULT '{"isiZulu", "English", "isiXhosa"}',
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stories_genre ON public.stories(genre);
CREATE INDEX IF NOT EXISTS idx_stories_trending ON public.stories(is_trending);

-- ----------------------------------------------------------------------------
-- 4. EPISODES (Strict 9:16 Vertical Video Pointers)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.stories(id) ON DELETE CASCADE,
    episode_number INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    synopsis TEXT,
    duration_seconds INT NOT NULL DEFAULT 80,
    video_url TEXT NOT NULL,        -- CDN / HLS manifest pointer (.m3u8 or .mp4)
    thumbnail_url TEXT,            -- CDN Image URI
    is_free BOOLEAN NOT NULL DEFAULT FALSE,
    coin_price INT NOT NULL DEFAULT 15,
    cliffhanger_rating NUMERIC(3, 1) NOT NULL DEFAULT 4.9,
    cliffhanger_hook TEXT,
    subtitles_json JSONB DEFAULT '{}', -- Localized subtitles { "isiZulu": "...", "English": "..." }
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_story_episode UNIQUE (story_id, episode_number)
);

CREATE INDEX IF NOT EXISTS idx_episodes_story ON public.episodes(story_id, episode_number);

-- ----------------------------------------------------------------------------
-- 5. WALLETS & DOUBLE-ENTRY COIN LEDGER (Transactional Integrity Core)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    coin_balance INT NOT NULL DEFAULT 100 CHECK (coin_balance >= 0),
    bonus_coins INT NOT NULL DEFAULT 0 CHECK (bonus_coins >= 0),
    lifetime_coins_purchased INT NOT NULL DEFAULT 0,
    lifetime_coins_spent INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wallets_user ON public.wallets(user_id);

-- Immutable audit log for all coin balance movements
CREATE TABLE IF NOT EXISTS public.coin_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES public.wallets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    amount INT NOT NULL, -- Positive for topup/bonus, negative for unlocks/gifts
    balance_before INT NOT NULL,
    balance_after INT NOT NULL,
    transaction_type VARCHAR(32) NOT NULL, -- 'TOPUP', 'EPISODE_UNLOCK', 'GIFT_SENT', 'DAILY_REWARD', 'REFUND'
    reference_id VARCHAR(100) NOT NULL,    -- Payment TX ID, Episode ID, or Gift ID
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coin_ledger_wallet ON public.coin_ledger(wallet_id);
CREATE INDEX IF NOT EXISTS idx_coin_ledger_ref ON public.coin_ledger(reference_id);

-- ----------------------------------------------------------------------------
-- 6. UNLOCKED EPISODES (Paywall Gates)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.unlocked_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    episode_id UUID NOT NULL REFERENCES public.episodes(id) ON DELETE CASCADE,
    story_id UUID NOT NULL REFERENCES public.stories(id) ON DELETE CASCADE,
    unlock_method VARCHAR(32) NOT NULL, -- 'COINS', 'AIRTIME_DCB', 'VIP_PASS', 'FREE_PROMO'
    coins_spent INT NOT NULL DEFAULT 0,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_episode_unlock UNIQUE (user_id, episode_id)
);

CREATE INDEX IF NOT EXISTS idx_unlocked_user ON public.unlocked_episodes(user_id);

-- ----------------------------------------------------------------------------
-- 7. EXTERNAL PAYMENT TRANSACTIONS (Regional Monetisation Layer)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider_id VARCHAR(32) NOT NULL, -- 'ZA_AIRTIME_VODACOM', 'ZA_AIRTIME_MTN', 'OZOW_EFT', 'PAYSTACK'
    region_code VARCHAR(8) NOT NULL DEFAULT 'ZA',
    external_ref VARCHAR(128) UNIQUE NOT NULL,
    phone_number VARCHAR(32),
    amount_currency NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    coins_granted INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'
    provider_payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settled_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payment_ext_ref ON public.payment_transactions(external_ref);
CREATE INDEX IF NOT EXISTS idx_payment_user ON public.payment_transactions(user_id);

-- ----------------------------------------------------------------------------
-- 8. WELELE CHAT & TIME-SYNCED BULLET COMMENTS (Pillar 8)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.bullet_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID NOT NULL REFERENCES public.episodes(id) ON DELETE CASCADE,
    story_id UUID NOT NULL REFERENCES public.stories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    user_name VARCHAR(100) NOT NULL,
    user_avatar TEXT,
    timestamp_ms INT NOT NULL DEFAULT 0, -- Exact video playback millisecond for flying bullet
    message VARCHAR(280) NOT NULL,
    emotion_tag VARCHAR(32) DEFAULT 'FLAME', -- 'FLAME', 'SHOCK', 'LAUGH', 'HEART', 'CRY'
    is_moderated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bullet_episode_time ON public.bullet_comments(episode_id, timestamp_ms);

-- ----------------------------------------------------------------------------
-- 9. ROW-LEVEL SECURITY (RLS) POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coin_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.unlocked_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bullet_comments ENABLE ROW LEVEL SECURITY;

-- Public read policies for published catalog
CREATE POLICY "Public can view published stories" ON public.stories FOR SELECT USING (is_published = true);
CREATE POLICY "Public can view episodes" ON public.episodes FOR SELECT USING (true);
CREATE POLICY "Public can view bullet comments" ON public.bullet_comments FOR SELECT USING (is_moderated = false);
