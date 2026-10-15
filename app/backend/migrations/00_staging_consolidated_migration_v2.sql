-- ============================================================================
-- WELELE MEDIA™ — CONSOLIDATED PRE-STAGING MIGRATION ARTIFACT (v2.0)
-- Target Platform: PostgreSQL 15+ (Supabase Staging Project Ref: dbsnaidhznofvyffdfni)
-- Execution Method: Supabase SQL Editor (Single Contiguous Transaction Block)
-- Scope: 25 Tables (15 Base Domain + 10 Operational Contracts)
--        + Principle of Least Privilege Grants (anon / authenticated / service_role)
--        + Granular Row Level Security Policies (Op-by-Op, Tenant-Guarded)
--        + Supabase Custom Access Token Hook for RBAC Claims Injection
-- Pre-conditions: extensions "uuid-ossp" and "pgcrypto" available
-- Rollback Limitation: In-flight abort rolls back via PostgreSQL transaction.
--                      Post-commit rollback requires compensating SQL or PITR.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- STEP 1: PREREQUISITES & EXTENSIONS
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- STEP 2: 15 BASE REPOSITORY TABLES (Migration 01)
-- ----------------------------------------------------------------------------

-- 1. USERS & PROFILES
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

-- 2. CANONICAL DIGITAL IP ASSET ROOT
CREATE TABLE IF NOT EXISTS public.digital_ips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    franchise_code VARCHAR(64) UNIQUE NOT NULL,
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

-- 3. STORY WORLDS & UNIVERSE CANON
CREATE TABLE IF NOT EXISTS public.story_worlds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    world_name VARCHAR(128) NOT NULL,
    geographical_setting VARCHAR(128) NOT NULL,
    time_period VARCHAR(64) NOT NULL DEFAULT 'Contemporary',
    mythology_and_rules TEXT NOT NULL,
    cultural_context TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_story_worlds_ip ON public.story_worlds(ip_id);

-- 4. CHARACTER BIBLES & ARCHETYPES
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

-- 5. RIGHTS LEDGER & MULTI-PARTY ROYALTY SPLITS
CREATE TABLE IF NOT EXISTS public.rights_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_id UUID NOT NULL REFERENCES public.digital_ips(id) ON DELETE CASCADE,
    beneficiary_user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    stakeholder_role VARCHAR(64) NOT NULL,
    royalty_split_pct NUMERIC(5, 2) NOT NULL CHECK (royalty_split_pct > 0 AND royalty_split_pct <= 100),
    territory VARCHAR(32) NOT NULL DEFAULT 'GLOBAL',
    medium VARCHAR(64) NOT NULL DEFAULT 'ALL_MEDIA',
    contract_ref VARCHAR(128) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_ip_beneficiary_role UNIQUE (ip_id, beneficiary_user_id, stakeholder_role)
);
CREATE INDEX IF NOT EXISTS idx_rights_ip ON public.rights_ledger(ip_id);

-- 6. STORY FORGE PACKAGES (Persistent AI Synthesis)
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

-- 7. SERIES & SEASONS (Catalog Entity)
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

-- 8. EPISODES & CLIFFHANGER GATES
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
    status VARCHAR(32) NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'under_review', 'approved', 'published', 'changes_requested', 'rejected', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_series_episode UNIQUE (series_id, episode_number)
);
CREATE INDEX IF NOT EXISTS idx_episodes_series ON public.episodes(series_id, episode_number);

-- 9. MEDIA ASSETS
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

-- 10. WALLETS & DOUBLE-ENTRY COIN LEDGER
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
    amount INT NOT NULL,
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

-- 11. UNLOCKED EPISODES GATEWAY
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

-- 12. AUDIENCE TELEMETRY EVENT LOG
CREATE TABLE IF NOT EXISTS public.telemetry_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_name VARCHAR(64) NOT NULL,
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

-- 13. TIME-SYNCED BULLET COMMENTS
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

-- 14. EXPERIENCE LAYOUT MANIFESTS
CREATE TABLE IF NOT EXISTS public.experience_layouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(32) NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published', 'archived')),
    manifest_json JSONB NOT NULL,
    published_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_page_status UNIQUE (page_id, status)
);
CREATE INDEX IF NOT EXISTS idx_experience_page ON public.experience_layouts(page_id, status);

-- ----------------------------------------------------------------------------
-- STEP 3: 10 OPERATIONAL & PRODUCTION CONTRACT TABLES (Migration 02)
-- ----------------------------------------------------------------------------

-- 15. CREATORS IDENTITY & STUDIO PROFILE
CREATE TABLE IF NOT EXISTS public.creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stage_name VARCHAR(128) NOT NULL,
    bio TEXT,
    country VARCHAR(8) NOT NULL DEFAULT 'ZA',
    is_verified BOOLEAN NOT NULL DEFAULT TRUE,
    total_views BIGINT NOT NULL DEFAULT 0,
    lifetime_earnings_zar NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_creators_user ON public.creators(user_id);

-- 16. PAYMENT TRANSACTIONS (Regional Fiat & Airtime Billing)
CREATE TABLE IF NOT EXISTS public.payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider_id VARCHAR(32) NOT NULL,
    region_code VARCHAR(8) NOT NULL DEFAULT 'ZA',
    external_ref VARCHAR(128) UNIQUE NOT NULL,
    phone_number VARCHAR(32),
    amount_currency NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    coins_granted INT NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')),
    provider_payload JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settled_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_payment_ext_ref ON public.payment_transactions(external_ref);
CREATE INDEX IF NOT EXISTS idx_payment_user ON public.payment_transactions(user_id);

-- 17. PAYMENT EVENTS (Webhook Receipts & Idempotency Audit Ledger)
-- Intentionally decoupled from payment_transactions to record fraudulent/invalid webhook attempts
CREATE TABLE IF NOT EXISTS public.payment_events (
    id VARCHAR(64) PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    provider_transaction_id VARCHAR(128),
    event_type VARCHAR(64) NOT NULL,
    user_id VARCHAR(64),
    amount_fiat NUMERIC(10, 2),
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    coins_grant INT NOT NULL DEFAULT 0,
    signature_verified BOOLEAN NOT NULL DEFAULT FALSE,
    payload_hash CHAR(64) NOT NULL,
    normalized_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    processing_status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED',
    idempotency_key VARCHAR(128) UNIQUE,
    ledger_transaction_id VARCHAR(128),
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_payment_events_provider_tx ON public.payment_events(provider_transaction_id);
CREATE INDEX IF NOT EXISTS idx_payment_events_user ON public.payment_events(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_events_idemp ON public.payment_events(idempotency_key);

-- 18. SECURITY AUDIT LEDGER (Append-Only Cryptographic Trust Spine)
CREATE TABLE IF NOT EXISTS public.security_audit_ledger (
    sequence_id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    domain VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id VARCHAR(64) NOT NULL,
    payload_hash CHAR(64) NOT NULL,
    previous_hash CHAR(64) NOT NULL,
    entry_hash CHAR(64) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_domain ON public.security_audit_ledger(domain);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON public.security_audit_ledger(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON public.security_audit_ledger(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_target_id ON public.security_audit_ledger(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON public.security_audit_ledger(created_at DESC);

-- 19. PRODUCTION BIBLES (Phase 4 10-Section Specification)
CREATE TABLE IF NOT EXISTS public.production_bibles (
    id VARCHAR(64) PRIMARY KEY,
    ip_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    story_title VARCHAR(255),
    section_1_title_identity JSONB,
    section_2_creative_dna JSONB,
    section_3_character_bible JSONB,
    section_4_location_bible JSONB,
    section_5_world_rules JSONB,
    section_6_visual_language JSONB,
    section_7_audio_language JSONB,
    section_8_continuity_bible JSONB,
    section_9_production_constraints JSONB,
    section_10_prompt_constitution JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_production_bibles_ip ON public.production_bibles(ip_id);

-- 20. EPISODE BLUEPRINTS (Downstream Dramatic Structure Planning)
CREATE TABLE IF NOT EXISTS public.episode_blueprints (
    id VARCHAR(64) PRIMARY KEY,
    episode_id VARCHAR(64) NOT NULL,
    series_id VARCHAR(64),
    blueprint_version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    title VARCHAR(255),
    episode_number INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    dramatic_objective JSONB,
    beats JSONB DEFAULT '[]'::jsonb,
    continuity JSONB,
    artifact_lineage_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_episode_blueprints_ep ON public.episode_blueprints(episode_id);
CREATE INDEX IF NOT EXISTS idx_episode_blueprints_series ON public.episode_blueprints(series_id);

-- 21. EPISODE PRODUCTION PACKS (5-Track Coordinated Execution Engine)
CREATE TABLE IF NOT EXISTS public.episode_production_packs (
    id VARCHAR(64) PRIMARY KEY,
    production_bible_id VARCHAR(64),
    ip_id VARCHAR(64) NOT NULL,
    episode_id VARCHAR(64),
    episode_number INT NOT NULL DEFAULT 1,
    pack_version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    title VARCHAR(255),
    duration_seconds INT NOT NULL DEFAULT 90,
    cliffhanger_prompt TEXT,
    story_brief TEXT,
    beats JSONB DEFAULT '[]'::jsonb,
    narrative_continuity JSONB,
    five_tracks JSONB,
    production_units JSONB,
    forge_configuration_id VARCHAR(64) DEFAULT 'CFG-001',
    lineage_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_episode_packs_ip ON public.episode_production_packs(ip_id, episode_number);
CREATE INDEX IF NOT EXISTS idx_episode_packs_ep_id ON public.episode_production_packs(episode_id);

-- 22. CONTENT INTELLIGENCE RECORDS (Phase 7 Telemetry & Signals)
CREATE TABLE IF NOT EXISTS public.content_intelligence_records (
    intelligence_id VARCHAR(64) PRIMARY KEY,
    ip_id VARCHAR(64),
    series_id VARCHAR(64),
    episode_id VARCHAR(64),
    domain VARCHAR(64) NOT NULL,
    classification VARCHAR(32) DEFAULT 'FACT',
    confidence VARCHAR(32) DEFAULT 'HIGH',
    observations JSONB DEFAULT '[]'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    provenance_hash VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ci_records_ip ON public.content_intelligence_records(ip_id);
CREATE INDEX IF NOT EXISTS idx_ci_records_domain ON public.content_intelligence_records(domain);

-- 23. CONTENT DECISIONS (Institutional Governance Log)
CREATE TABLE IF NOT EXISTS public.content_decisions (
    decision_id VARCHAR(64) PRIMARY KEY,
    intelligence_id VARCHAR(64) REFERENCES public.content_intelligence_records(intelligence_id) ON DELETE SET NULL,
    domain VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PROPOSED' CHECK (status IN ('PROPOSED', 'UNDER_REVIEW', 'APPROVED', 'IMPLEMENTED', 'SUPERSEDED', 'REJECTED')),
    decision_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT,
    actor_id VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL,
    action_items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_decisions_int ON public.content_decisions(intelligence_id);
CREATE INDEX IF NOT EXISTS idx_content_decisions_status ON public.content_decisions(status);

-- 24. CONTENT INTELLIGENCE EVIDENCE PACKAGES (Full Verification Packs)
CREATE TABLE IF NOT EXISTS public.content_intelligence_evidence_packages (
    package_id VARCHAR(64) PRIMARY KEY,
    decision_id VARCHAR(64) REFERENCES public.content_decisions(decision_id) ON DELETE CASCADE,
    evidence_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    root_cause_analysis TEXT,
    verification_hash CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ci_evidence_decision ON public.content_intelligence_evidence_packages(decision_id);

-- ----------------------------------------------------------------------------
-- STEP 4: REVOKE DEFAULT PRIVILEGES & ENABLE RLS (ALL 25 TABLES)
-- ----------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'users', 'creators', 'digital_ips', 'story_worlds', 'character_bibles',
        'rights_ledger', 'story_forge_packages', 'series', 'episodes',
        'media_assets', 'wallets', 'coin_ledger', 'unlocked_episodes',
        'payment_transactions', 'payment_events', 'telemetry_events', 'bullet_comments',
        'experience_layouts', 'security_audit_ledger',
        'production_bibles', 'episode_blueprints', 'episode_production_packs',
        'content_intelligence_records', 'content_decisions', 'content_intelligence_evidence_packages'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = tbl) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl);
        END IF;
    END LOOP;
END $$;

-- ----------------------------------------------------------------------------
-- STEP 5: EXPLICIT ROLE GRANTS (anon vs authenticated vs service_role)
-- ----------------------------------------------------------------------------

-- A. Anonymous Role (Published public catalog and unmoderated comments read-only)
GRANT SELECT ON public.digital_ips TO anon;
GRANT SELECT ON public.series TO anon;
GRANT SELECT ON public.episodes TO anon;
GRANT SELECT ON public.experience_layouts TO anon;
GRANT SELECT ON public.bullet_comments TO anon;
GRANT SELECT ON public.creators TO anon;

-- B. Authenticated Role (Viewers, Creators, Admins)
GRANT SELECT, UPDATE ON public.users TO authenticated;
GRANT SELECT, UPDATE ON public.creators TO authenticated;
GRANT SELECT ON public.digital_ips TO authenticated;
GRANT SELECT ON public.story_worlds TO authenticated;
GRANT SELECT ON public.character_bibles TO authenticated;
GRANT SELECT ON public.series TO authenticated;
GRANT SELECT ON public.episodes TO authenticated;
GRANT SELECT ON public.experience_layouts TO authenticated;
GRANT SELECT, INSERT ON public.bullet_comments TO authenticated;
GRANT SELECT, INSERT ON public.telemetry_events TO authenticated;
GRANT SELECT ON public.wallets TO authenticated;
GRANT SELECT ON public.coin_ledger TO authenticated;
GRANT SELECT ON public.unlocked_episodes TO authenticated;
GRANT SELECT ON public.payment_transactions TO authenticated;
GRANT SELECT ON public.payment_events TO authenticated;
GRANT SELECT ON public.rights_ledger TO authenticated;
GRANT SELECT ON public.security_audit_ledger TO authenticated;

-- Creator & Admin specific table privileges
GRANT ALL ON public.digital_ips TO authenticated;
GRANT ALL ON public.story_worlds TO authenticated;
GRANT ALL ON public.character_bibles TO authenticated;
GRANT ALL ON public.story_forge_packages TO authenticated;
GRANT ALL ON public.series TO authenticated;
GRANT ALL ON public.episodes TO authenticated;
GRANT ALL ON public.media_assets TO authenticated;
GRANT ALL ON public.production_bibles TO authenticated;
GRANT ALL ON public.episode_blueprints TO authenticated;
GRANT ALL ON public.episode_production_packs TO authenticated;
GRANT ALL ON public.content_intelligence_records TO authenticated;
GRANT ALL ON public.content_decisions TO authenticated;
GRANT ALL ON public.content_intelligence_evidence_packages TO authenticated;

-- Explicitly revoke mutation on immutable audit journals
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.payment_events FROM PUBLIC, anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.security_audit_ledger FROM PUBLIC, anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.coin_ledger FROM PUBLIC, anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.wallets FROM PUBLIC, anon, authenticated;

-- C. Service Role (Full privileges for trusted backend daemons)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO service_role;

-- ----------------------------------------------------------------------------
-- STEP 6: GRANULAR ROW LEVEL SECURITY POLICIES (ALL 25 TABLES)
-- ----------------------------------------------------------------------------

-- 1. USERS
DROP POLICY IF EXISTS "users_select_policy" ON public.users;
DROP POLICY IF EXISTS "users_update_policy" ON public.users;
CREATE POLICY "users_select_policy" ON public.users FOR SELECT TO authenticated
USING (id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "users_update_policy" ON public.users FOR UPDATE TO authenticated
USING (id = auth.uid())
WITH CHECK (id = auth.uid() AND role IS NOT DISTINCT FROM (SELECT role FROM public.users WHERE id = auth.uid()));

-- 2. CREATORS
DROP POLICY IF EXISTS "creators_select_public" ON public.creators;
DROP POLICY IF EXISTS "creators_manage_own" ON public.creators;
CREATE POLICY "creators_select_public" ON public.creators FOR SELECT TO anon, authenticated USING (TRUE);
CREATE POLICY "creators_manage_own" ON public.creators FOR ALL TO authenticated
USING (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 3. DIGITAL IPS
DROP POLICY IF EXISTS "digital_ips_select_public" ON public.digital_ips;
DROP POLICY IF EXISTS "digital_ips_manage_creator" ON public.digital_ips;
CREATE POLICY "digital_ips_select_public" ON public.digital_ips FOR SELECT TO anon, authenticated
USING (status = 'active' OR master_owner_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "digital_ips_manage_creator" ON public.digital_ips FOR ALL TO authenticated
USING (master_owner_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (master_owner_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 4. STORY WORLDS
DROP POLICY IF EXISTS "story_worlds_select_owner" ON public.story_worlds;
DROP POLICY IF EXISTS "story_worlds_manage_owner" ON public.story_worlds;
CREATE POLICY "story_worlds_select_owner" ON public.story_worlds FOR SELECT TO authenticated
USING (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "story_worlds_manage_owner" ON public.story_worlds FOR ALL TO authenticated
USING (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 5. CHARACTER BIBLES
DROP POLICY IF EXISTS "character_bibles_select_owner" ON public.character_bibles;
DROP POLICY IF EXISTS "character_bibles_manage_owner" ON public.character_bibles;
CREATE POLICY "character_bibles_select_owner" ON public.character_bibles FOR SELECT TO authenticated
USING (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "character_bibles_manage_owner" ON public.character_bibles FOR ALL TO authenticated
USING (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 6. RIGHTS LEDGER
DROP POLICY IF EXISTS "rights_ledger_select" ON public.rights_ledger;
CREATE POLICY "rights_ledger_select" ON public.rights_ledger FOR SELECT TO authenticated
USING (beneficiary_user_id = auth.uid() OR ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 7. STORY FORGE PACKAGES
DROP POLICY IF EXISTS "story_forge_manage_creator" ON public.story_forge_packages;
CREATE POLICY "story_forge_manage_creator" ON public.story_forge_packages FOR ALL TO authenticated
USING (creator_id = auth.uid() OR ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (creator_id = auth.uid() OR ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 8. SERIES
DROP POLICY IF EXISTS "series_select_public" ON public.series;
DROP POLICY IF EXISTS "series_manage_creator" ON public.series;
CREATE POLICY "series_select_public" ON public.series FOR SELECT TO anon, authenticated
USING (is_published = TRUE OR ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "series_manage_creator" ON public.series FOR ALL TO authenticated
USING (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (ip_id IN (SELECT id FROM public.digital_ips WHERE master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 9. EPISODES (Granular Op-by-Op)
DROP POLICY IF EXISTS "episodes_select_public" ON public.episodes;
DROP POLICY IF EXISTS "episodes_insert_creator" ON public.episodes;
DROP POLICY IF EXISTS "episodes_update_creator" ON public.episodes;
DROP POLICY IF EXISTS "episodes_delete_creator" ON public.episodes;

CREATE POLICY "episodes_select_public" ON public.episodes FOR SELECT TO anon, authenticated
USING (status = 'published' OR series_id IN (SELECT s.id FROM public.series s JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "episodes_insert_creator" ON public.episodes FOR INSERT TO authenticated
WITH CHECK (series_id IN (SELECT s.id FROM public.series s JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "episodes_update_creator" ON public.episodes FOR UPDATE TO authenticated
USING (series_id IN (SELECT s.id FROM public.series s JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (series_id IN (SELECT s.id FROM public.series s JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "episodes_delete_creator" ON public.episodes FOR DELETE TO authenticated
USING (((series_id IN (SELECT s.id FROM public.series s JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid())) AND status IN ('draft', 'under_review', 'rejected')) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 10. MEDIA ASSETS
DROP POLICY IF EXISTS "media_assets_select" ON public.media_assets;
DROP POLICY IF EXISTS "media_assets_manage_creator" ON public.media_assets;
CREATE POLICY "media_assets_select" ON public.media_assets FOR SELECT TO anon, authenticated
USING (transcoding_status = 'READY' OR episode_id IN (SELECT e.id FROM public.episodes e JOIN public.series s ON e.series_id = s.id JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "media_assets_manage_creator" ON public.media_assets FOR ALL TO authenticated
USING (episode_id IN (SELECT e.id FROM public.episodes e JOIN public.series s ON e.series_id = s.id JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK (episode_id IN (SELECT e.id FROM public.episodes e JOIN public.series s ON e.series_id = s.id JOIN public.digital_ips ip ON s.ip_id = ip.id WHERE ip.master_owner_id = auth.uid()) OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 11. WALLETS & DOUBLE-ENTRY COIN LEDGER
DROP POLICY IF EXISTS "wallets_select_owner" ON public.wallets;
DROP POLICY IF EXISTS "coin_ledger_select_owner" ON public.coin_ledger;
CREATE POLICY "wallets_select_owner" ON public.wallets FOR SELECT TO authenticated
USING (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "coin_ledger_select_owner" ON public.coin_ledger FOR SELECT TO authenticated
USING (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 12. UNLOCKED EPISODES
DROP POLICY IF EXISTS "unlocked_episodes_select_owner" ON public.unlocked_episodes;
CREATE POLICY "unlocked_episodes_select_owner" ON public.unlocked_episodes FOR SELECT TO authenticated
USING (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 13. PAYMENT TRANSACTIONS
DROP POLICY IF EXISTS "payment_transactions_select_owner" ON public.payment_transactions;
CREATE POLICY "payment_transactions_select_owner" ON public.payment_transactions FOR SELECT TO authenticated
USING (user_id = auth.uid() OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 14. PAYMENT EVENTS (Webhook Receipts)
DROP POLICY IF EXISTS "payment_events_select_admin" ON public.payment_events;
CREATE POLICY "payment_events_select_admin" ON public.payment_events FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 15. SECURITY AUDIT LEDGER
DROP POLICY IF EXISTS "audit_ledger_select_admin" ON public.security_audit_ledger;
CREATE POLICY "audit_ledger_select_admin" ON public.security_audit_ledger FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 16. EXPERIENCE LAYOUTS
DROP POLICY IF EXISTS "layouts_select_public" ON public.experience_layouts;
DROP POLICY IF EXISTS "layouts_manage_admin" ON public.experience_layouts;
CREATE POLICY "layouts_select_public" ON public.experience_layouts FOR SELECT TO anon, authenticated
USING (status = 'published' OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "layouts_manage_admin" ON public.experience_layouts FOR ALL TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 17. TELEMETRY EVENTS
DROP POLICY IF EXISTS "telemetry_insert_owner" ON public.telemetry_events;
DROP POLICY IF EXISTS "telemetry_select_admin" ON public.telemetry_events;
CREATE POLICY "telemetry_insert_owner" ON public.telemetry_events FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid() OR user_id IS NULL);
CREATE POLICY "telemetry_select_admin" ON public.telemetry_events FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 18. BULLET COMMENTS
DROP POLICY IF EXISTS "bullet_comments_select_public" ON public.bullet_comments;
DROP POLICY IF EXISTS "bullet_comments_insert_user" ON public.bullet_comments;
CREATE POLICY "bullet_comments_select_public" ON public.bullet_comments FOR SELECT TO anon, authenticated
USING (is_moderated = FALSE OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');
CREATE POLICY "bullet_comments_insert_user" ON public.bullet_comments FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid());

-- 19. PRODUCTION BIBLES (Granular Op-by-Op)
DROP POLICY IF EXISTS "production_bibles_select_creator" ON public.production_bibles;
DROP POLICY IF EXISTS "production_bibles_insert_creator" ON public.production_bibles;
DROP POLICY IF EXISTS "production_bibles_update_creator" ON public.production_bibles;
DROP POLICY IF EXISTS "production_bibles_delete_creator" ON public.production_bibles;

CREATE POLICY "production_bibles_select_creator" ON public.production_bibles FOR SELECT TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "production_bibles_insert_creator" ON public.production_bibles FOR INSERT TO authenticated
WITH CHECK (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "production_bibles_update_creator" ON public.production_bibles FOR UPDATE TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
)
WITH CHECK (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "production_bibles_delete_creator" ON public.production_bibles FOR DELETE TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 20. EPISODE BLUEPRINTS (Granular Op-by-Op)
DROP POLICY IF EXISTS "episode_blueprints_select_creator" ON public.episode_blueprints;
DROP POLICY IF EXISTS "episode_blueprints_insert_creator" ON public.episode_blueprints;
DROP POLICY IF EXISTS "episode_blueprints_update_creator" ON public.episode_blueprints;
DROP POLICY IF EXISTS "episode_blueprints_delete_creator" ON public.episode_blueprints;

CREATE POLICY "episode_blueprints_select_creator" ON public.episode_blueprints FOR SELECT TO authenticated
USING (
    series_id IN (
        SELECT s.id::text FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR episode_id IN (
        SELECT e.id::text FROM public.episodes e
        JOIN public.series s ON e.series_id = s.id
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_blueprints_insert_creator" ON public.episode_blueprints FOR INSERT TO authenticated
WITH CHECK (
    series_id IN (
        SELECT s.id::text FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR episode_id IN (
        SELECT e.id::text FROM public.episodes e
        JOIN public.series s ON e.series_id = s.id
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_blueprints_update_creator" ON public.episode_blueprints FOR UPDATE TO authenticated
USING (
    series_id IN (
        SELECT s.id::text FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR episode_id IN (
        SELECT e.id::text FROM public.episodes e
        JOIN public.series s ON e.series_id = s.id
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
)
WITH CHECK (
    series_id IN (
        SELECT s.id::text FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR episode_id IN (
        SELECT e.id::text FROM public.episodes e
        JOIN public.series s ON e.series_id = s.id
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_blueprints_delete_creator" ON public.episode_blueprints FOR DELETE TO authenticated
USING (
    series_id IN (
        SELECT s.id::text FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR episode_id IN (
        SELECT e.id::text FROM public.episodes e
        JOIN public.series s ON e.series_id = s.id
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 21. EPISODE PRODUCTION PACKS (Granular Op-by-Op)
DROP POLICY IF EXISTS "episode_packs_select_creator" ON public.episode_production_packs;
DROP POLICY IF EXISTS "episode_packs_insert_creator" ON public.episode_production_packs;
DROP POLICY IF EXISTS "episode_packs_update_creator" ON public.episode_production_packs;
DROP POLICY IF EXISTS "episode_packs_delete_creator" ON public.episode_production_packs;

CREATE POLICY "episode_packs_select_creator" ON public.episode_production_packs FOR SELECT TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_packs_insert_creator" ON public.episode_production_packs FOR INSERT TO authenticated
WITH CHECK (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_packs_update_creator" ON public.episode_production_packs FOR UPDATE TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
)
WITH CHECK (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "episode_packs_delete_creator" ON public.episode_production_packs FOR DELETE TO authenticated
USING (
    ip_id IN (
        SELECT id::text FROM public.digital_ips WHERE master_owner_id = auth.uid()
        UNION
        SELECT franchise_code FROM public.digital_ips WHERE master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 22. CONTENT INTELLIGENCE RECORDS
DROP POLICY IF EXISTS "ci_records_select_admin" ON public.content_intelligence_records;
DROP POLICY IF EXISTS "ci_records_insert_admin" ON public.content_intelligence_records;
DROP POLICY IF EXISTS "ci_records_update_admin" ON public.content_intelligence_records;
DROP POLICY IF EXISTS "ci_records_delete_admin" ON public.content_intelligence_records;

CREATE POLICY "ci_records_select_admin" ON public.content_intelligence_records FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('admin', 'auditor') OR (auth.jwt() ->> 'role') IN ('admin', 'auditor'));

CREATE POLICY "ci_records_insert_admin" ON public.content_intelligence_records FOR INSERT TO authenticated
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "ci_records_update_admin" ON public.content_intelligence_records FOR UPDATE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "ci_records_delete_admin" ON public.content_intelligence_records FOR DELETE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 23. CONTENT DECISIONS
DROP POLICY IF EXISTS "content_decisions_select_admin" ON public.content_decisions;
DROP POLICY IF EXISTS "content_decisions_insert_admin" ON public.content_decisions;
DROP POLICY IF EXISTS "content_decisions_update_admin" ON public.content_decisions;
DROP POLICY IF EXISTS "content_decisions_delete_admin" ON public.content_decisions;

CREATE POLICY "content_decisions_select_admin" ON public.content_decisions FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('admin', 'auditor') OR (auth.jwt() ->> 'role') IN ('admin', 'auditor'));

CREATE POLICY "content_decisions_insert_admin" ON public.content_decisions FOR INSERT TO authenticated
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "content_decisions_update_admin" ON public.content_decisions FOR UPDATE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "content_decisions_delete_admin" ON public.content_decisions FOR DELETE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- 24. CONTENT INTELLIGENCE EVIDENCE PACKAGES
DROP POLICY IF EXISTS "ci_evidence_select_admin" ON public.content_intelligence_evidence_packages;
DROP POLICY IF EXISTS "ci_evidence_insert_admin" ON public.content_intelligence_evidence_packages;
DROP POLICY IF EXISTS "ci_evidence_update_admin" ON public.content_intelligence_evidence_packages;
DROP POLICY IF EXISTS "ci_evidence_delete_admin" ON public.content_intelligence_evidence_packages;

CREATE POLICY "ci_evidence_select_admin" ON public.content_intelligence_evidence_packages FOR SELECT TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') IN ('admin', 'auditor') OR (auth.jwt() ->> 'role') IN ('admin', 'auditor'));

CREATE POLICY "ci_evidence_insert_admin" ON public.content_intelligence_evidence_packages FOR INSERT TO authenticated
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "ci_evidence_update_admin" ON public.content_intelligence_evidence_packages FOR UPDATE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin')
WITH CHECK ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

CREATE POLICY "ci_evidence_delete_admin" ON public.content_intelligence_evidence_packages FOR DELETE TO authenticated
USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin' OR (auth.jwt() ->> 'role') = 'admin');

-- ----------------------------------------------------------------------------
-- STEP 7: SUPABASE CUSTOM ACCESS TOKEN HOOK FOR RBAC ENRICHMENT
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event JSONB)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    claims JSONB;
    user_role VARCHAR(32);
    user_creator_id VARCHAR(64);
BEGIN
    claims := event->'claims';
    
    SELECT role INTO user_role 
    FROM public.users 
    WHERE id = (event->>'user_id')::uuid;

    SELECT id::text INTO user_creator_id
    FROM public.creators
    WHERE user_id = (event->>'user_id')::uuid;

    claims := jsonb_set(claims, '{app_metadata, role}', to_jsonb(COALESCE(user_role, 'viewer')));
    IF user_creator_id IS NOT NULL THEN
        claims := jsonb_set(claims, '{app_metadata, creator_id}', to_jsonb(user_creator_id));
    END IF;

    event := jsonb_set(event, '{claims}', claims);
    RETURN event;
END;
$$;

GRANT EXECUTE ON FUNCTION public.custom_access_token_hook TO supabase_auth_admin;
REVOKE EXECUTE ON FUNCTION public.custom_access_token_hook FROM PUBLIC;

COMMIT;
