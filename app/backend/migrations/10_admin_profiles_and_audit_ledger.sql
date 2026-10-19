-- Migration 10_admin_profiles_and_audit_ledger.sql
-- Welele Media™ — Phase 6O-6: Admin Profiles & Maker-Checker Separation of Duties
-- Preserves accepted 6I payment run schema 100% untouched per Correction 2.

CREATE TABLE IF NOT EXISTS public.admin_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.platform_users(id),
    staff_email VARCHAR(255) NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    department VARCHAR(50) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS Hardening for admin_profiles
ALTER TABLE public.admin_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admin_profiles_select_admin" ON public.admin_profiles
    FOR SELECT
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');

CREATE POLICY "admin_profiles_modify_admin" ON public.admin_profiles
    FOR ALL
    USING ((auth.jwt() -> 'app_metadata' ->> 'role') = 'admin');
