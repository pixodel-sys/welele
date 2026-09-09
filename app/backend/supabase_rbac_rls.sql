-- ============================================================================
-- Welele Media™ — Security & Trust Foundation Database Schema & RLS Policies
-- Institutional Trust Infrastructure: Append-Only Audit Ledger & Strict Data Isolation
-- ============================================================================

-- 1. APPEND-ONLY SECURITY AUDIT LEDGER
CREATE TABLE IF NOT EXISTS security_audit_ledger (
    sequence_id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    domain VARCHAR(32) NOT NULL, -- 'AUTH', 'IP', 'CONTENT', 'COMMERCE', 'EXPERIENCE', 'SECURITY'
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

-- Indexes for lightning-fast audit queries
CREATE INDEX IF NOT EXISTS idx_audit_domain ON security_audit_ledger(domain);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON security_audit_ledger(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_actor_id ON security_audit_ledger(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_target_id ON security_audit_ledger(target_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON security_audit_ledger(created_at DESC);

-- REVOKE UPDATE AND DELETE TO GUARANTEE APPEND-ONLY IMMUTABILITY
REVOKE UPDATE, DELETE, TRUNCATE ON security_audit_ledger FROM PUBLIC, authenticated, anon;

-- ============================================================================
-- 2. ROW-LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS across all canonical operational tables
ALTER TABLE digital_ips ENABLE ROW LEVEL SECURITY;
ALTER TABLE story_worlds ENABLE ROW LEVEL SECURITY;
ALTER TABLE character_bibles ENABLE ROW LEVEL SECURITY;
ALTER TABLE rights_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE story_forge_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE coin_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_audit_ledger ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- A. DIGITAL IP & STORY FORGE POLICIES
-- ----------------------------------------------------------------------------
-- Public: Read active IPs
CREATE POLICY "digital_ips_read_public" ON digital_ips
FOR SELECT USING (status = 'active' OR auth.jwt() ->> 'role' IN ('creator', 'admin'));

-- Creator: Manage owned IP
CREATE POLICY "digital_ips_creator_manage" ON digital_ips
FOR ALL USING (
    master_owner_id = auth.jwt() ->> 'creator_id'
    OR master_owner_id = auth.uid()::text
    OR auth.jwt() ->> 'role' = 'admin'
);

-- Story Packages: Creator view owned packages, admin view all
CREATE POLICY "story_forge_packages_tenant_isolation" ON story_forge_packages
FOR ALL USING (
    creator_id = auth.jwt() ->> 'creator_id'
    OR creator_id = auth.uid()::text
    OR auth.jwt() ->> 'role' = 'admin'
);

-- ----------------------------------------------------------------------------
-- B. SERIES & EPISODES CATALOG POLICIES
-- ----------------------------------------------------------------------------
-- Public: Read published series
CREATE POLICY "series_public_read" ON series
FOR SELECT USING (is_published = TRUE OR creator_id = auth.jwt() ->> 'creator_id' OR auth.jwt() ->> 'role' = 'admin');

-- Creator: Manage owned series
CREATE POLICY "series_creator_manage" ON series
FOR ALL USING (
    creator_id = auth.jwt() ->> 'creator_id'
    OR creator_id = auth.uid()::text
    OR auth.jwt() ->> 'role' = 'admin'
);

-- Episodes: Public view published; Creators view owned series episodes
CREATE POLICY "episodes_tenant_policy" ON episodes
FOR ALL USING (
    status = 'published'
    OR series_id IN (
        SELECT id FROM series 
        WHERE creator_id = auth.jwt() ->> 'creator_id' 
        OR creator_id = auth.uid()::text
    )
    OR auth.jwt() ->> 'role' = 'admin'
);

-- ----------------------------------------------------------------------------
-- C. COMMERCE & WALLET POLICIES
-- ----------------------------------------------------------------------------
-- Wallets: Users can ONLY read and operate their own wallet balance
CREATE POLICY "wallet_owner_isolation" ON wallets
FOR ALL USING (
    user_id = auth.uid()::text
    OR user_id = auth.jwt() ->> 'sub'
    OR auth.jwt() ->> 'role' = 'admin'
);

-- Coin Ledger: Immutable ledger transactions readable only by owner or admin
CREATE POLICY "coin_ledger_owner_isolation" ON coin_ledger
FOR SELECT USING (
    wallet_id IN (
        SELECT id FROM wallets 
        WHERE user_id = auth.uid()::text 
        OR user_id = auth.jwt() ->> 'sub'
    )
    OR auth.jwt() ->> 'role' = 'admin'
);

-- ----------------------------------------------------------------------------
-- D. SECURITY AUDIT LEDGER POLICIES
-- ----------------------------------------------------------------------------
-- Admins can read all audit records; Creators can view audit records where they are the target or actor
CREATE POLICY "audit_ledger_read_policy" ON security_audit_ledger
FOR SELECT USING (
    auth.jwt() ->> 'role' = 'admin'
    OR actor_id = auth.jwt() ->> 'sub'
    OR target_id = auth.jwt() ->> 'creator_id'
);

-- Append capability for authenticated backend service
CREATE POLICY "audit_ledger_append_policy" ON security_audit_ledger
FOR INSERT WITH CHECK (TRUE);
