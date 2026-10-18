-- ==============================================================================
-- WELELE MEDIA™ — 04_creator_commercial_accounting_v1.sql
-- Workstream 6I-E.3: Authoritative Creator Commercial Accounting Layer
-- Target: Staging PostgreSQL (Supabase Project Ref: dbsnaidhznofvyffdfni)
-- Execution Method: Supabase SQL Editor (Single Contiguous Transaction Block)
-- Invariants:
--   1. NO EXTERNAL CREATOR PAYOUTS ACTIVATED IN THIS MIGRATION
--   2. Production remains completely untouched (STAGING ONLY)
--   3. Zero assumed payment-processing deduction without explicit contractual schedule
--   4. Immutable append-only creator ledger enforced via PostgreSQL trigger
--   5. Database-enforced version exclusion constraint preventing overlapping effective dates
--   6. Strict backend-only RLS (service_role only; zero direct client exposure)
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- STEP 0: PREREQUISITES & EXTENSIONS
-- ------------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ------------------------------------------------------------------------------
-- 1. COMMERCIAL AGREEMENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.commercial_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    series_id UUID REFERENCES public.series(id) ON DELETE RESTRICT,
    creator_id VARCHAR(64) NOT NULL,
    agreement_reference VARCHAR(64) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    commercial_model VARCHAR(32) NOT NULL CHECK (commercial_model IN ('MODEL_A', 'MODEL_B', 'MODEL_C', 'CUSTOM')),
    governing_law VARCHAR(64) NOT NULL DEFAULT 'South Africa',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('DRAFT', 'ACTIVE', 'TERMINATED', 'EXPIRED')),
    agreement_signed_at TIMESTAMPTZ,
    licence_start_at TIMESTAMPTZ,
    commercial_release_at TIMESTAMPTZ,
    licence_end_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_commercial_agreements_licence_dates CHECK (licence_end_at IS NULL OR licence_end_at > licence_start_at)
);

-- ------------------------------------------------------------------------------
-- 2. COMMERCIAL AGREEMENT VERSIONS (With Database-Enforced Non-Overlapping Exclusion)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.commercial_agreement_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agreement_id UUID NOT NULL REFERENCES public.commercial_agreements(id) ON DELETE CASCADE,
    version_number INT NOT NULL CHECK (version_number > 0),
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    commercial_model VARCHAR(32) NOT NULL CHECK (commercial_model IN ('MODEL_A', 'MODEL_B', 'MODEL_C', 'CUSTOM')),
    creator_share_percentage NUMERIC(5, 4) NOT NULL CHECK (creator_share_percentage >= 0.0000 AND creator_share_percentage <= 1.0000),
    welele_share_percentage NUMERIC(5, 4) NOT NULL CHECK (welele_share_percentage >= 0.0000 AND welele_share_percentage <= 1.0000),
    deduction_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    terms_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_agreement_version UNIQUE(agreement_id, version_number),
    CONSTRAINT chk_agreement_version_dates CHECK (effective_to IS NULL OR effective_to > effective_from),
    CONSTRAINT chk_agreement_version_shares CHECK (creator_share_percentage + welele_share_percentage <= 1.0001)
);

-- Range exclusion constraint preventing overlapping effective periods for the same agreement
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_no_overlapping_agreement_versions'
    ) THEN
        ALTER TABLE public.commercial_agreement_versions
        ADD CONSTRAINT uq_no_overlapping_agreement_versions
        EXCLUDE USING gist (
            agreement_id WITH =,
            tstzrange(effective_from, COALESCE(effective_to, 'infinity'::timestamptz), '[)') WITH &&
        );
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 3. REVENUE EVENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.revenue_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    series_id UUID REFERENCES public.series(id) ON DELETE RESTRICT,
    episode_id UUID REFERENCES public.episodes(id) ON DELETE RESTRICT,
    source VARCHAR(64) NOT NULL CHECK (source IN ('EPISODE_UNLOCK', 'AIRTIME_UNLOCK', 'GIFT', 'SUBSCRIPTION_PASS', 'DIRECT_PURCHASE')),
    source_transaction_id VARCHAR(128) NOT NULL,
    provider_transaction_id VARCHAR(128),
    event_type VARCHAR(64) NOT NULL CHECK (event_type IN ('COIN_UNLOCK', 'AIRTIME_CHARGE', 'GIFT_SENT', 'FIAT_CHARGE')),
    gross_amount NUMERIC(12, 4) NOT NULL CHECK (gross_amount >= 0.0000),
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    settled_at TIMESTAMPTZ,
    settlement_status VARCHAR(32) NOT NULL DEFAULT 'SETTLED' CHECK (settlement_status IN ('SETTLED', 'PENDING', 'DISPUTED', 'REFUNDED')),
    commercial_agreement_version_id UUID REFERENCES public.commercial_agreement_versions(id) ON DELETE RESTRICT,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 4. REVENUE DEDUCTIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.revenue_deductions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revenue_event_id UUID NOT NULL REFERENCES public.revenue_events(id) ON DELETE CASCADE,
    deduction_type VARCHAR(64) NOT NULL CHECK (deduction_type IN ('PAYMENT_PROCESSING_FEE', 'PLATFORM_FEE', 'STATUTORY_TAX', 'REFUND', 'CHARGEBACK', 'CONTRACTUAL_LEVY')),
    amount NUMERIC(12, 4) NOT NULL CHECK (amount >= 0.0000),
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    contractual_basis VARCHAR(255) NOT NULL,
    source_reference VARCHAR(128),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 5. CREATOR LEDGER (IMMUTABLE, APPEND-ONLY)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id VARCHAR(64) NOT NULL,
    project_id UUID,
    series_id UUID REFERENCES public.series(id) ON DELETE RESTRICT,
    revenue_event_id UUID REFERENCES public.revenue_events(id) ON DELETE RESTRICT,
    commercial_agreement_version_id UUID REFERENCES public.commercial_agreement_versions(id) ON DELETE RESTRICT,
    entry_type VARCHAR(32) NOT NULL CHECK (entry_type IN ('EARNING', 'ADJUSTMENT', 'REVERSAL', 'REFUND', 'CHARGEBACK', 'PAYOUT_HOLD', 'PAYOUT_RELEASE')),
    gross_revenue NUMERIC(12, 4) NOT NULL DEFAULT 0.0000 CHECK (gross_revenue >= 0.0000),
    deductions NUMERIC(12, 4) NOT NULL DEFAULT 0.0000 CHECK (deductions >= 0.0000),
    net_revenue NUMERIC(12, 4) NOT NULL DEFAULT 0.0000 CHECK (net_revenue >= 0.0000),
    allocation_percentage NUMERIC(5, 4) NOT NULL DEFAULT 0.0000 CHECK (allocation_percentage >= 0.0000 AND allocation_percentage <= 1.0000),
    creator_amount NUMERIC(12, 4) NOT NULL, -- positive for earnings, negative for reversals / adjustments
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    accounting_period VARCHAR(16) NOT NULL, -- e.g. '2026-10'
    status VARCHAR(32) NOT NULL DEFAULT 'SETTLED' CHECK (status IN ('EARNED', 'SETTLED', 'AVAILABLE', 'PAID', 'HELD', 'DISPUTED', 'REVERSED')),
    reversal_of_ledger_id UUID REFERENCES public.creator_ledger(id) ON DELETE RESTRICT,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 6. CREATOR STATEMENTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id VARCHAR(64) NOT NULL,
    accounting_period VARCHAR(16) NOT NULL, -- e.g. '2026-10'
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    opening_balance NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    gross_revenue NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    total_deductions NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    net_revenue NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    total_earnings NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    total_adjustments NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    total_payouts NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    closing_balance NUMERIC(12, 4) NOT NULL DEFAULT 0.0000,
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'FINALIZED', 'AUDITED')),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_creator_statement_period UNIQUE(creator_id, accounting_period, currency)
);

-- ------------------------------------------------------------------------------
-- 7. CREATOR STATEMENT LINES
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_statement_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID NOT NULL REFERENCES public.creator_statements(id) ON DELETE CASCADE,
    ledger_entry_id UUID REFERENCES public.creator_ledger(id) ON DELETE RESTRICT,
    line_type VARCHAR(32) NOT NULL CHECK (line_type IN ('EARNING', 'DEDUCTION', 'ADJUSTMENT', 'PAYOUT')),
    project_id UUID,
    series_id UUID,
    description VARCHAR(255),
    amount NUMERIC(12, 4) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 8. CREATOR PAYOUTS (ACCOUNTING OBJECT ONLY — NO EXTERNAL SETTLEMENT)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id VARCHAR(64) NOT NULL,
    requested_amount NUMERIC(12, 4) NOT NULL CHECK (requested_amount > 0.0000),
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    payout_method VARCHAR(64) NOT NULL,
    account_details VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'SETTLED', 'REJECTED', 'CANCELLED')),
    settlement_status VARCHAR(64) NOT NULL DEFAULT 'Settlement Pending (External Rails Unproven)',
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    settled_at TIMESTAMPTZ,
    rejection_reason VARCHAR(255),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 9. CREATOR PAYOUT ALLOCATIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_payout_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payout_id UUID NOT NULL REFERENCES public.creator_payouts(id) ON DELETE CASCADE,
    ledger_entry_id UUID NOT NULL REFERENCES public.creator_ledger(id) ON DELETE RESTRICT,
    amount_allocated NUMERIC(12, 4) NOT NULL CHECK (amount_allocated > 0.0000),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 10. INDEXES FOR PERFORMANCE & AUDIT TRAVERSAL
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_commercial_agreements_series ON public.commercial_agreements(series_id);
CREATE INDEX IF NOT EXISTS idx_commercial_agreements_creator ON public.commercial_agreements(creator_id);
CREATE INDEX IF NOT EXISTS idx_commercial_versions_agreement ON public.commercial_agreement_versions(agreement_id, effective_from);
CREATE INDEX IF NOT EXISTS idx_revenue_events_series ON public.revenue_events(series_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_revenue_events_idemp ON public.revenue_events(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_ledger_creator_period ON public.creator_ledger(creator_id, accounting_period);
CREATE INDEX IF NOT EXISTS idx_creator_ledger_idemp ON public.creator_ledger(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_creator_ledger_revenue_event ON public.creator_ledger(revenue_event_id);
CREATE INDEX IF NOT EXISTS idx_creator_payouts_creator ON public.creator_payouts(creator_id, status);

-- ------------------------------------------------------------------------------
-- 11. APPEND-ONLY PROTECTION TRIGGER ON CREATOR_LEDGER
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.fn_enforce_creator_ledger_append_only()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'CRITICAL ACCOUNTING INVARIANT: creator_ledger is append-only. % is prohibited; post a compensating reversal or adjustment row instead.',
        TG_OP;
END $$;

DROP TRIGGER IF EXISTS trg_guard_creator_ledger_append_only ON public.creator_ledger;
CREATE TRIGGER trg_guard_creator_ledger_append_only
BEFORE UPDATE OR DELETE ON public.creator_ledger
FOR EACH ROW EXECUTE FUNCTION public.fn_enforce_creator_ledger_append_only();

-- ------------------------------------------------------------------------------
-- 12. ROW LEVEL SECURITY (RLS) & STRICT BACKEND SERVICE ROLE ISOLATION
-- (Zero direct client exposure: authenticated and anon roles have NO direct access.
-- All access is mediated by the backend service layer via service_role.)
-- ------------------------------------------------------------------------------
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'commercial_agreements',
        'commercial_agreement_versions',
        'revenue_events',
        'revenue_deductions',
        'creator_ledger',
        'creator_statements',
        'creator_statement_lines',
        'creator_payouts',
        'creator_payout_allocations'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        -- Enable RLS
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl);
        -- Revoke all direct privileges from public, anon, and authenticated
        EXECUTE format('REVOKE ALL ON public.%I FROM PUBLIC, anon, authenticated;', tbl);
        -- Grant full access strictly to service_role (backend API persistence)
        EXECUTE format('GRANT ALL ON public.%I TO service_role;', tbl);
    END LOOP;
END $$;

-- Service Role full access policies
DROP POLICY IF EXISTS "service_role_all_commercial_agreements" ON public.commercial_agreements;
CREATE POLICY "service_role_all_commercial_agreements" ON public.commercial_agreements FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_commercial_versions" ON public.commercial_agreement_versions;
CREATE POLICY "service_role_all_commercial_versions" ON public.commercial_agreement_versions FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_revenue_events" ON public.revenue_events;
CREATE POLICY "service_role_all_revenue_events" ON public.revenue_events FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_revenue_deductions" ON public.revenue_deductions;
CREATE POLICY "service_role_all_revenue_deductions" ON public.revenue_deductions FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_ledger" ON public.creator_ledger;
CREATE POLICY "service_role_all_creator_ledger" ON public.creator_ledger FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_statements" ON public.creator_statements;
CREATE POLICY "service_role_all_creator_statements" ON public.creator_statements FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_statement_lines" ON public.creator_statement_lines;
CREATE POLICY "service_role_all_creator_statement_lines" ON public.creator_statement_lines FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_payouts" ON public.creator_payouts;
CREATE POLICY "service_role_all_creator_payouts" ON public.creator_payouts FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_payout_allocations" ON public.creator_payout_allocations;
CREATE POLICY "service_role_all_creator_payout_allocations" ON public.creator_payout_allocations FOR ALL TO service_role USING (true) WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 13. CANONICAL STAGING SEED DATA (Verified Existing Staging References)
-- ------------------------------------------------------------------------------

-- Scenario 1: Blood Ties (Model B, 40% creator share, 60% Welele share)
-- Verified Staging Series ID: c3e9302a-9809-51c2-b219-4e2a3079787f
-- Verified Staging Creator ID: 71de72b7-d88d-55fc-b5e8-bc3260ad8569 (Zola Dlamini)
INSERT INTO public.commercial_agreements (
    id,
    project_id,
    series_id,
    creator_id,
    agreement_reference,
    title,
    commercial_model,
    governing_law,
    status,
    agreement_signed_at,
    licence_start_at,
    commercial_release_at,
    licence_end_at,
    metadata
) VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'c3e9302a-9809-51c2-b219-4e2a3079787f'::uuid,
    'c3e9302a-9809-51c2-b219-4e2a3079787f'::uuid,
    '71de72b7-d88d-55fc-b5e8-bc3260ad8569',
    'AGR-BT-2026-001',
    'Blood Ties Commercial Distribution Agreement',
    'MODEL_B',
    'South Africa',
    'ACTIVE',
    '2026-01-01T00:00:00Z',
    '2026-01-15T00:00:00Z',
    '2026-02-01T00:00:00Z',
    '2028-02-01T00:00:00Z',
    '{"notes": "Canonical Model B reference agreement (Blood Ties 40% creator / 60% Welele)"}'::jsonb
) ON CONFLICT (agreement_reference) DO NOTHING;

INSERT INTO public.commercial_agreement_versions (
    id,
    agreement_id,
    version_number,
    effective_from,
    effective_to,
    commercial_model,
    creator_share_percentage,
    welele_share_percentage,
    deduction_rules,
    terms_metadata
) VALUES (
    'b0000000-0000-0000-0000-000000000001'::uuid,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    1,
    '2026-01-01T00:00:00Z',
    NULL,
    'MODEL_B',
    0.4000,
    0.6000,
    '[]'::jsonb,
    '{"schedule": "Schedule B-1: 40% Net Revenue"}'::jsonb
) ON CONFLICT (agreement_id, version_number) DO NOTHING;

-- Scenario 2: Queen of Jozi (Model A, Default 0% creator share during exclusive period)
-- Verified Staging Series ID: df8e81cd-6da8-512e-aaf6-8625549079b0
-- Verified Staging Creator ID: 71de72b7-d88d-55fc-b5e8-bc3260ad8569 (Zola Dlamini)
INSERT INTO public.commercial_agreements (
    id,
    project_id,
    series_id,
    creator_id,
    agreement_reference,
    title,
    commercial_model,
    governing_law,
    status,
    agreement_signed_at,
    licence_start_at,
    commercial_release_at,
    licence_end_at,
    metadata
) VALUES (
    'a0000000-0000-0000-0000-000000000002'::uuid,
    'df8e81cd-6da8-512e-aaf6-8625549079b0'::uuid,
    'df8e81cd-6da8-512e-aaf6-8625549079b0'::uuid,
    '71de72b7-d88d-55fc-b5e8-bc3260ad8569',
    'AGR-QJ-2026-001',
    'Queen of Jozi Production Partnership Agreement',
    'MODEL_A',
    'South Africa',
    'ACTIVE',
    '2026-01-01T00:00:00Z',
    '2026-01-10T00:00:00Z',
    '2026-01-20T00:00:00Z',
    '2027-01-20T00:00:00Z',
    '{"notes": "Canonical Model A reference agreement (Queen of Jozi 0% creator / 100% Welele)"}'::jsonb
) ON CONFLICT (agreement_reference) DO NOTHING;

INSERT INTO public.commercial_agreement_versions (
    id,
    agreement_id,
    version_number,
    effective_from,
    effective_to,
    commercial_model,
    creator_share_percentage,
    welele_share_percentage,
    deduction_rules,
    terms_metadata
) VALUES (
    'b0000000-0000-0000-0000-000000000002'::uuid,
    'a0000000-0000-0000-0000-000000000002'::uuid,
    1,
    '2026-01-01T00:00:00Z',
    NULL,
    'MODEL_A',
    0.0000,
    1.0000,
    '[]'::jsonb,
    '{"schedule": "Schedule A: 0% creator revenue share during exclusive period"}'::jsonb
) ON CONFLICT (agreement_id, version_number) DO NOTHING;

COMMIT;
