-- ============================================================================
-- WELELE MEDIA™ — CANONICAL DATABASE SECURITY, GRANTS & GRANULAR RLS POLICIES (v3.0)
-- Architecture: Single Identity Primitive (Supabase Auth JWT)
-- Enforces: Principle of Least Privilege (Explicit REVOKE/GRANT + Op-by-Op RLS)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- STEP 1: REVOKE DEFAULT PUBLIC PRIVILEGES
-- ----------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

-- ----------------------------------------------------------------------------
-- STEP 2: ENABLE RLS ACROSS EVERY SINGLE TABLE
-- ----------------------------------------------------------------------------
DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'users', 'creators', 'digital_ips', 'story_worlds', 'character_bibles',
        'rights_ledger', 'story_forge_packages', 'series', 'episodes',
        'media_assets', 'wallets', 'coin_ledger', 'unlocked_episodes',
        'payment_transactions', 'telemetry_events', 'bullet_comments',
        'experience_layouts', 'security_audit_ledger'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = tbl) THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl);
        END IF;
    END LOOP;
END $$;

-- ----------------------------------------------------------------------------
-- STEP 3: EXPLICIT ROLE GRANTS (anon vs authenticated vs service_role)
-- ----------------------------------------------------------------------------

-- A. Anonymous Role (Strictly public catalog and published CMS)
GRANT SELECT ON public.digital_ips TO anon;
GRANT SELECT ON public.series TO anon;
GRANT SELECT ON public.episodes TO anon;
GRANT SELECT ON public.experience_layouts TO anon;
GRANT SELECT ON public.bullet_comments TO anon;

-- B. Authenticated Role (Viewers, Creators, Admins)
GRANT SELECT, UPDATE ON public.users TO authenticated;
GRANT SELECT ON public.creators TO authenticated;
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

-- Creator & Admin specific table privileges
GRANT ALL ON public.digital_ips TO authenticated;
GRANT ALL ON public.story_worlds TO authenticated;
GRANT ALL ON public.character_bibles TO authenticated;
GRANT ALL ON public.story_forge_packages TO authenticated;
GRANT ALL ON public.series TO authenticated;
GRANT ALL ON public.episodes TO authenticated;
GRANT ALL ON public.media_assets TO authenticated;
GRANT SELECT ON public.rights_ledger TO authenticated;

-- C. Service Role (Full system privileges for background workers)
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ----------------------------------------------------------------------------
-- STEP 4: GRANULAR ROW-LEVEL SECURITY POLICIES (Operation by Operation)
-- ----------------------------------------------------------------------------

-- 1. USERS TABLE
DROP POLICY IF EXISTS "users_select_policy" ON public.users;
DROP POLICY IF EXISTS "users_update_policy" ON public.users;

CREATE POLICY "users_select_policy" ON public.users
FOR SELECT TO authenticated
USING (
    id = auth.uid() 
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "users_update_policy" ON public.users
FOR UPDATE TO authenticated
USING (id = auth.uid())
WITH CHECK (
    id = auth.uid() 
    AND role IS NOT DISTINCT FROM (SELECT role FROM public.users WHERE id = auth.uid()) -- Prevent self-privilege escalation
);

-- 2. EPISODES TABLE (Fix Critical Deletion / Public Mutation Bug)
DROP POLICY IF EXISTS "episodes_tenant_policy" ON public.episodes;
DROP POLICY IF EXISTS "episodes_select_public" ON public.episodes;
DROP POLICY IF EXISTS "episodes_insert_creator" ON public.episodes;
DROP POLICY IF EXISTS "episodes_update_creator" ON public.episodes;
DROP POLICY IF EXISTS "episodes_delete_creator" ON public.episodes;

-- SELECT: Public and Viewers can only view published episodes; Creators see their own series; Admin sees all
CREATE POLICY "episodes_select_public" ON public.episodes
FOR SELECT TO anon, authenticated
USING (
    status = 'published'
    OR series_id IN (
        SELECT s.id FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- INSERT: Creators can only insert episodes into series they own; Admin can insert
CREATE POLICY "episodes_insert_creator" ON public.episodes
FOR INSERT TO authenticated
WITH CHECK (
    series_id IN (
        SELECT s.id FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- UPDATE: Creators can update episodes in series they own; Admin can update
CREATE POLICY "episodes_update_creator" ON public.episodes
FOR UPDATE TO authenticated
USING (
    series_id IN (
        SELECT s.id FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
)
WITH CHECK (
    series_id IN (
        SELECT s.id FROM public.series s
        JOIN public.digital_ips ip ON s.ip_id = ip.id
        WHERE ip.master_owner_id = auth.uid()
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- DELETE: Creators can only delete draft/review episodes in series they own; Admin can delete; Never public
CREATE POLICY "episodes_delete_creator" ON public.episodes
FOR DELETE TO authenticated
USING (
    (
        series_id IN (
            SELECT s.id FROM public.series s
            JOIN public.digital_ips ip ON s.ip_id = ip.id
            WHERE ip.master_owner_id = auth.uid()
        )
        AND status IN ('draft', 'under_review', 'rejected')
    )
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 3. WALLETS & DOUBLE-ENTRY COIN LEDGER
DROP POLICY IF EXISTS "wallets_select_owner" ON public.wallets;
DROP POLICY IF EXISTS "coin_ledger_select_owner" ON public.coin_ledger;

CREATE POLICY "wallets_select_owner" ON public.wallets
FOR SELECT TO authenticated
USING (
    user_id = auth.uid()
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "coin_ledger_select_owner" ON public.coin_ledger
FOR SELECT TO authenticated
USING (
    user_id = auth.uid()
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 4. UNLOCKED EPISODES (Paywall Gates)
DROP POLICY IF EXISTS "unlocked_episodes_select_owner" ON public.unlocked_episodes;

CREATE POLICY "unlocked_episodes_select_owner" ON public.unlocked_episodes
FOR SELECT TO authenticated
USING (
    user_id = auth.uid()
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 5. PAYMENT TRANSACTIONS
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'payment_transactions') THEN
        DROP POLICY IF EXISTS "payment_transactions_select_owner" ON public.payment_transactions;
        EXECUTE 'CREATE POLICY "payment_transactions_select_owner" ON public.payment_transactions
                 FOR SELECT TO authenticated
                 USING (
                     user_id = auth.uid()
                     OR (auth.jwt() -> ''app_metadata'' ->> ''role'') = ''admin''
                     OR (auth.jwt() ->> ''role'') = ''admin''
                 );';
    END IF;
END $$;

-- 6. SECURITY AUDIT LEDGER (Append-Only Immobility)
DROP POLICY IF EXISTS "audit_ledger_select_admin" ON public.security_audit_ledger;
DROP POLICY IF EXISTS "audit_ledger_insert_system" ON public.security_audit_ledger;
DROP POLICY IF EXISTS "audit_ledger_append_policy" ON public.security_audit_ledger;

CREATE POLICY "audit_ledger_select_admin" ON public.security_audit_ledger
FOR SELECT TO authenticated
USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "audit_ledger_insert_system" ON public.security_audit_ledger
FOR INSERT TO service_role
WITH CHECK (TRUE);

REVOKE UPDATE, DELETE, TRUNCATE ON public.security_audit_ledger FROM PUBLIC, anon, authenticated;

-- 7. EXPERIENCE LAYOUTS (CMS UI)
DROP POLICY IF EXISTS "layouts_select_public" ON public.experience_layouts;
DROP POLICY IF EXISTS "layouts_insert_admin" ON public.experience_layouts;
DROP POLICY IF EXISTS "layouts_update_admin" ON public.experience_layouts;
DROP POLICY IF EXISTS "layouts_delete_admin" ON public.experience_layouts;

CREATE POLICY "layouts_select_public" ON public.experience_layouts
FOR SELECT TO anon, authenticated
USING (
    status = 'published' 
    OR (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "layouts_insert_admin" ON public.experience_layouts
FOR INSERT TO authenticated
WITH CHECK (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "layouts_update_admin" ON public.experience_layouts
FOR UPDATE TO authenticated
USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
)
WITH CHECK (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

CREATE POLICY "layouts_delete_admin" ON public.experience_layouts
FOR DELETE TO authenticated
USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- 8. TELEMETRY EVENTS
DROP POLICY IF EXISTS "telemetry_insert_owner" ON public.telemetry_events;
DROP POLICY IF EXISTS "telemetry_select_admin" ON public.telemetry_events;

CREATE POLICY "telemetry_insert_owner" ON public.telemetry_events
FOR INSERT TO authenticated
WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "telemetry_select_admin" ON public.telemetry_events
FOR SELECT TO authenticated
USING (
    (auth.jwt() -> 'app_metadata' ->> 'role') = 'admin'
    OR (auth.jwt() ->> 'role') = 'admin'
);

-- ----------------------------------------------------------------------------
-- STEP 5: SUPABASE CUSTOM ACCESS TOKEN HOOK FOR RBAC
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
    
    -- Lookup user role from public.users table
    SELECT role INTO user_role 
    FROM public.users 
    WHERE id = (event->>'user_id')::uuid;

    -- Lookup creator identity if role is creator
    SELECT id::text INTO user_creator_id
    FROM public.creators
    WHERE user_id = (event->>'user_id')::uuid;

    -- Enrich app_metadata in JWT claims
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
