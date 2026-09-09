-- ============================================================================
-- WELELE MEDIA™ — CANONICAL DIGITAL IP ENGINE SCHEMA v2.0
-- Database Engine: PostgreSQL 15+ (Supabase Managed Instance)
-- Architecture: Digital IP Franchise Core, Relational Series/Media Separation,
--               Double-Entry Accounting Journal, and Telemetry Event Spine.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. USERS & PROFILES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(32) UNIQUE,
    email VARCHAR(255) UNIQUE,
    display_name VARCHAR(128) NOT NULL,
    avatar_url TEXT,
    region_code VARCHAR(8) NOT NULL DEFAULT 'ZA',
    preferred_language VARCHAR(32) NOT NULL DEFAULT 'isiZulu',
    role VARCHAR(32) NOT NULL DEFAULT 'viewer' CHECK (role IN ('viewer', 'creator', 'admin', 'auditor')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON public.users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- ----------------------------------------------------------------------------
-- 2. CANONICAL DIGITAL IP ASSET ROOT (GAP-001)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.digital_ips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    franchise_code VARCHAR(64) UNIQUE NOT NULL, -- e.g. 'IP-BLOOD-TIES', 'IP-JOZI-QUEEN'
    logline TEXT NOT NULL,
    synopsis TEXT NOT NULL,
    genre VARCHAR(64) NOT NULL,
    primary_language VARCHAR(32) NOT NULL DEFAULT 'isiZulu',
    master_owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    global_valuation_usd NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('development', 'active', 'licensed', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_digital_ips_franchise ON public.digital_ips(franchise_code);
CREATE INDEX IF NOT EXISTS idx_digital_ips_owner ON public.digital_ips(master_owner_id);

-- ----------------------------------------------------------------------------
-- 3. STORY WORLDS & UNIVERSE CANON (GAP-001)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.story_worlds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    world_name VARCHAR(128) NOT NULL,
    geographical_setting VARCHAR(128) NOT NULL, -- e.g. 'Alexandra & Sandton, Johannesburg'
    time_period VARCHAR(64) NOT NULL DEFAULT 'Contemporary',
    mythology_and_rules TEXT NOT NULL,
    cultural_context TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_story_worlds_ip ON public.story_worlds(ip_id);

-- ----------------------------------------------------------------------------
-- 4. CHARACTER BIBLES & ARCHETYPES (GAP-005)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.character_bibles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL CHECK (role IN ('protagonist', 'antagonist', 'confidant', 'catalyst')),
    archetype VARCHAR(64) NOT NULL,
    secret_motivation TEXT NOT NULL,
    fatal_flaw TEXT NOT NULL,
    signature_quote TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_characters_ip ON public.character_bibles(ip_id);

-- ----------------------------------------------------------------------------
-- 5. RIGHTS LEDGER & MULTI-PARTY ROYALTY SPLITS (GAP-001 / GAP-007)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.rights_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    beneficiary_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    stakeholder_role VARCHAR(64) NOT NULL, -- 'Showrunner', 'Lead Writer', 'Director', 'Co-Producer'
    royalty_split_pct NUMERIC(5, 2) NOT NULL CHECK (royalty_split_pct > 0 AND royalty_split_pct <= 100),
    territory VARCHAR(32) NOT NULL DEFAULT 'GLOBAL',
    medium VARCHAR(64) NOT NULL DEFAULT 'ALL_MEDIA',
    contract_ref VARCHAR(128) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_ip_beneficiary_role UNIQUE (ip_id, beneficiary_user_id, stakeholder_role)
);

CREATE INDEX IF NOT EXISTS idx_rights_ip ON public.rights_ledger(ip_id);

-- ----------------------------------------------------------------------------
-- 6. STORY FORGE PACKAGES (Persistent AI Synthesis) (GAP-005)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.story_forge_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    package_title VARCHAR(255) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT 'v1.0.0',
    target_duration_seconds INT NOT NULL DEFAULT 90,
    beats_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    dialogues_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    cliffhanger_prompt TEXT NOT NULL,
    ai_model_used VARCHAR(64) NOT NULL,
    human_approved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_story_forge_ip ON public.story_forge_packages(ip_id);

-- ----------------------------------------------------------------------------
-- 7. SERIES & SEASONS (Catalog Entity)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE RESTRICT,
    season_number INT NOT NULL DEFAULT 1,
    title VARCHAR(255) NOT NULL,
    tagline VARCHAR(255),
    synopsis TEXT NOT NULL,
    cover_image TEXT NOT NULL,
    vertical_poster TEXT NOT NULL,
    genre VARCHAR(64) NOT NULL,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 4.90,
    total_episodes INT NOT NULL DEFAULT 0,
    free_episodes INT NOT NULL DEFAULT 3,
    coin_price_per_episode INT NOT NULL DEFAULT 5,
    is_published BOOLEAN NOT NULL DEFAULT TRUE,
    available_languages TEXT[] NOT NULL DEFAULT '{"isiZulu", "English", "isiXhosa"}',
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_ip_season UNIQUE (ip_id, season_number)
);

CREATE INDEX IF NOT EXISTS idx_series_ip ON public.series(ip_id);

-- ----------------------------------------------------------------------------
-- 8. EPISODES & CLIFFHANGER GATES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    series_id UUID NOT NULL REFERENCES public.series(id) ON DELETE CASCADE,
    episode_number INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    synopsis TEXT,
    duration_seconds INT NOT NULL DEFAULT 80,
    is_free BOOLEAN NOT NULL DEFAULT FALSE,
    coin_price INT NOT NULL DEFAULT 5,
    cliffhanger_time_seconds INT NOT NULL DEFAULT 65,
    cliffhanger_hook TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'under_review', 'approved', 'published', 'changes_requested', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_series_episode UNIQUE (series_id, episode_number)
);

CREATE INDEX IF NOT EXISTS idx_episodes_series ON public.episodes(series_id, episode_number);

-- ----------------------------------------------------------------------------
-- 9. MEDIA ASSETS (Decoupled HLS Ladder & Renditions) (GAP-006)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.media_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID UNIQUE NOT NULL REFERENCES public.episodes(id) ON DELETE CASCADE,
    storage_key VARCHAR(512) NOT NULL,
    master_video_url TEXT NOT NULL,
    hls_master_manifest_url TEXT,
    thumbnail_url TEXT,
    duration_seconds NUMERIC(6, 2) NOT NULL DEFAULT 80.0,
    transcoding_status VARCHAR(32) NOT NULL DEFAULT 'READY' CHECK (transcoding_status IN ('QUEUED', 'PROCESSING', 'READY', 'FAILED')),
    renditions_json JSONB DEFAULT '{"1080p": "", "720p": "", "480p": ""}'::jsonb,
    subtitles_vtt_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_assets_episode ON public.media_assets(episode_id);

-- ----------------------------------------------------------------------------
-- 10. WALLETS & DOUBLE-ENTRY COIN LEDGER (GAP-002 / GAP-003)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    coin_balance INT NOT NULL DEFAULT 100 CHECK (coin_balance >= 0),
    bonus_coins INT NOT NULL DEFAULT 25 CHECK (bonus_coins >= 0),
    lifetime_coins_purchased INT NOT NULL DEFAULT 0,
    lifetime_coins_spent INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.coin_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES public.wallets(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    amount INT NOT NULL, -- Positive for credit, negative for debit
    balance_before INT NOT NULL,
    balance_after INT NOT NULL,
    transaction_type VARCHAR(32) NOT NULL CHECK (transaction_type IN ('TOPUP_PURCHASE', 'AIRTIME_PASS', 'EPISODE_UNLOCK', 'GIFT_SENT', 'ROYALTY_CREDIT', 'ONBOARDING_REWARD', 'REFUND')),
    reference_id VARCHAR(128) NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ledger_wallet ON public.coin_ledger(wallet_id);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON public.coin_ledger(user_id);
CREATE INDEX IF NOT EXISTS idx_ledger_ref ON public.coin_ledger(reference_id);

-- ----------------------------------------------------------------------------
-- 11. UNLOCKED EPISODES GATEWAY
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.unlocked_episodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    episode_id UUID NOT NULL REFERENCES public.episodes(id) ON DELETE CASCADE,
    series_id UUID NOT NULL REFERENCES public.series(id) ON DELETE CASCADE,
    unlock_method VARCHAR(32) NOT NULL DEFAULT 'COINS',
    coins_spent INT NOT NULL DEFAULT 0,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_episode_unlock UNIQUE (user_id, episode_id)
);

CREATE INDEX IF NOT EXISTS idx_unlocked_user ON public.unlocked_episodes(user_id);

-- ----------------------------------------------------------------------------
-- 12. AUDIENCE TELEMETRY EVENT LOG (GAP-004)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name VARCHAR(64) NOT NULL, -- 'episode_started', 'heartbeat', 'cliffhanger_reached', 'unlock_completed'
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    session_id VARCHAR(64) NOT NULL,
    ip_id UUID REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    series_id UUID REFERENCES public.series(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES public.episodes(id) ON DELETE CASCADE,
    playback_second INT NOT NULL DEFAULT 0,
    region_code VARCHAR(8) NOT NULL DEFAULT 'ZA',
    device_type VARCHAR(32) NOT NULL DEFAULT 'mobile_pwa',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_telemetry_episode_event ON public.telemetry_events(episode_id, event_name);
CREATE INDEX IF NOT EXISTS idx_telemetry_time ON public.telemetry_events(created_at);

-- ----------------------------------------------------------------------------
-- 13. TIME-SYNCED BULLET COMMENTS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.bullet_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_id UUID NOT NULL REFERENCES public.episodes(id) ON DELETE CASCADE,
    series_id UUID NOT NULL REFERENCES public.series(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    user_name VARCHAR(128) NOT NULL,
    user_avatar TEXT,
    timestamp_ms INT NOT NULL DEFAULT 0,
    message VARCHAR(280) NOT NULL,
    emotion_tag VARCHAR(32) DEFAULT 'FLAME',
    is_moderated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bullet_comments_ep ON public.bullet_comments(episode_id, timestamp_ms);

-- ----------------------------------------------------------------------------
-- 14. WEE EXPERIENCE LAYOUT MANIFESTS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.experience_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id VARCHAR(64) NOT NULL, -- 'home', 'discover'
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(32) NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    manifest_json JSONB NOT NULL,
    published_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_page_status UNIQUE (page_id, status)
);

CREATE INDEX IF NOT EXISTS idx_experience_page ON public.experience_layouts(page_id, status);
