-- =============================================================================
-- Welele Media™ — Migration 08: Creator Tenancy and Workspace Membership (6O-2)
-- Strictly Non-Destructive & Additive: Preserves All Accepted 6I Schemas Intact.
-- =============================================================================

-- 1. Canonical Creator Profiles Table
-- Links to platform_users (owner_user_id) while preserving text slugs for 6I
CREATE TABLE IF NOT EXISTS public.creator_profiles (
    id TEXT PRIMARY KEY, -- e.g. 'creator_zola', 'creator_amaka' (Preserves 6I Compatibility)
    owner_user_id UUID, -- References platform_users(id) once Phase 6O-1 table is applied
    business_type VARCHAR(20) NOT NULL DEFAULT 'individual' CHECK (business_type IN ('individual', 'registered_entity')),
    legal_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    handle VARCHAR(100),
    country VARCHAR(10) NOT NULL DEFAULT 'ZA',
    legacy_passkey_enabled BOOLEAN NOT NULL DEFAULT true, -- Explicit allowlist during migration window
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'kyc_pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Workspace Members Table
-- Supports multi-user collaboration within creator studios (Owner, Admin, Editor, Finance)
CREATE TABLE IF NOT EXISTS public.workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- References platform_users(id)
    creator_id TEXT NOT NULL REFERENCES public.creator_profiles(id) ON DELETE CASCADE,
    role VARCHAR(30) NOT NULL CHECK (role IN ('owner', 'admin', 'editor', 'finance')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, creator_id)
);

CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON public.workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_creator ON public.workspace_members(creator_id);

-- 3. Idempotent Baseline Seeding for Canonical Creators
INSERT INTO public.creator_profiles (id, legal_name, display_name, handle, country, legacy_passkey_enabled, status)
VALUES 
    ('creator_zola', 'Zola Dlamini', 'Zola Dlamini', '@zola_cinemas', 'ZA', true, 'active'),
    ('creator_amaka', 'Amaka Okafor', 'Amaka Okafor', '@amaka_films', 'NG', true, 'active'),
    ('creator_kofi', 'Kofi Mensah', 'Kofi Mensah & Studio Accra', '@kofi_accra', 'GH', true, 'active'),
    ('creator_wanjiku', 'Wanjiku Mwangi', 'Wanjiku Mwangi', '@wanjiku_tales', 'KE', true, 'active')
ON CONFLICT (id) DO UPDATE SET
    legal_name = EXCLUDED.legal_name,
    display_name = EXCLUDED.display_name,
    handle = EXCLUDED.handle,
    country = EXCLUDED.country,
    legacy_passkey_enabled = EXCLUDED.legacy_passkey_enabled,
    updated_at = NOW();
