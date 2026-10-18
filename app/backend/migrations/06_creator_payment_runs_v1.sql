-- ==============================================================================
-- WELELE MEDIA™ — 06_creator_payment_runs_v1.sql
-- Workstream 6I-G.4.2: Human-in-the-Loop Creator Payment Run Architecture
-- Target: Staging PostgreSQL (Supabase Project Ref: dbsnaidhznofvyffdfni)
-- Production: 100% FROZEN (STRICTLY FORBIDDEN ON PRODUCTION)
-- ==============================================================================
-- Invariants:
-- 1. Payment runs group creator-requested payouts only (Zero automatic balance sweep)
-- 2. Once APPROVED, run membership and beneficiary snapshot are 100% immutable (DB-enforced)
-- 3. ON DELETE RESTRICT on run items (No cascading deletion of financial history)
-- 4. Dual-control enforcement (Creator/preparer cannot approve their own run)
-- 5. Payouts move to PROCESSING upon export; PAID requires authentic external settlement
-- 6. Strict service-role isolation via Row Level Security (RLS)
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. CREATOR PAYMENT RUNS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_payment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_reference VARCHAR(64) UNIQUE NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    payout_count INT NOT NULL DEFAULT 0 CHECK (payout_count >= 0),
    total_amount NUMERIC(12, 4) NOT NULL DEFAULT 0.0000 CHECK (total_amount >= 0.0000),
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT' CHECK (status IN (
        'DRAFT',
        'UNDER_REVIEW',
        'APPROVED',
        'EXPORTED',
        'AWAITING_EXTERNAL_RESULT',
        'RESULTS_RECORDED',
        'RECONCILED',
        'CANCELLED'
    )),
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_by VARCHAR(64),
    approved_at TIMESTAMPTZ,
    exported_at TIMESTAMPTZ,
    export_file_hash_sha256 VARCHAR(64),
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_payment_run_dates CHECK (period_end >= period_start),
    CONSTRAINT chk_payment_run_approval CHECK (
        (status IN ('DRAFT', 'UNDER_REVIEW', 'CANCELLED') AND approved_by IS NULL AND approved_at IS NULL)
        OR
        (status IN ('APPROVED', 'EXPORTED', 'AWAITING_EXTERNAL_RESULT', 'RESULTS_RECORDED', 'RECONCILED') AND approved_by IS NOT NULL AND approved_at IS NOT NULL)
    ),
    CONSTRAINT chk_payment_run_separation_of_duties CHECK (
        approved_by IS NULL OR approved_by <> created_by
    )
);

-- ------------------------------------------------------------------------------
-- 2. CREATOR PAYMENT RUN ITEMS (IMMUTABLE SNAPSHOT MEMBERSHIP)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.creator_payment_run_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_run_id UUID NOT NULL REFERENCES public.creator_payment_runs(id) ON DELETE RESTRICT,
    payout_id UUID NOT NULL REFERENCES public.creator_payouts(id) ON DELETE RESTRICT,
    creator_id VARCHAR(64) NOT NULL,
    statement_id UUID REFERENCES public.creator_statements(id) ON DELETE SET NULL,
    amount NUMERIC(12, 4) NOT NULL CHECK (amount > 0.0000),
    currency VARCHAR(8) NOT NULL DEFAULT 'ZAR',
    status VARCHAR(32) NOT NULL DEFAULT 'INCLUDED' CHECK (status IN (
        'INCLUDED',
        'HELD',
        'EXCLUDED',
        'PAID',
        'FAILED'
    )),
    beneficiary_name_snapshot VARCHAR(255) NOT NULL,
    bank_name_snapshot VARCHAR(128) NOT NULL,
    account_number_snapshot VARCHAR(128) NOT NULL,
    branch_code_snapshot VARCHAR(32) NOT NULL,
    account_type_snapshot VARCHAR(64) NOT NULL DEFAULT 'Current',
    payment_reference_snapshot VARCHAR(128) NOT NULL,
    external_payment_reference VARCHAR(128),
    failure_reason VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------------------
-- 3. UNIQUE & AUDIT INDEXES
-- ------------------------------------------------------------------------------
-- Prevent a payout from appearing in more than one active payment run item concurrently
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_payout_run_item
    ON public.creator_payment_run_items(payout_id)
    WHERE status NOT IN ('EXCLUDED', 'FAILED');

CREATE INDEX IF NOT EXISTS idx_payment_runs_status
    ON public.creator_payment_runs(status);

CREATE INDEX IF NOT EXISTS idx_payment_runs_created_at
    ON public.creator_payment_runs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payment_run_items_run_id
    ON public.creator_payment_run_items(payment_run_id);

CREATE INDEX IF NOT EXISTS idx_payment_run_items_creator_id
    ON public.creator_payment_run_items(creator_id);

-- ------------------------------------------------------------------------------
-- 4. DB-LEVEL POST-APPROVAL IMMUTABILITY TRIGGERS
-- ------------------------------------------------------------------------------

-- Guard on creator_payment_runs: protect approved run header from deletion and parameter mutation
CREATE OR REPLACE FUNCTION public.fn_guard_payment_run_post_approval_immutability()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Block deletion of approved runs
    IF TG_OP = 'DELETE' THEN
        IF OLD.status IN ('APPROVED', 'EXPORTED', 'AWAITING_EXTERNAL_RESULT', 'RESULTS_RECORDED', 'RECONCILED') THEN
            RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Cannot delete payment run % in % state.', OLD.id, OLD.status;
        END IF;
        RETURN OLD;
    END IF;

    -- Block alterations to core parameters post-approval
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status IN ('APPROVED', 'EXPORTED', 'AWAITING_EXTERNAL_RESULT', 'RESULTS_RECORDED', 'RECONCILED') THEN
            IF NEW.run_reference <> OLD.run_reference THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: run_reference is immutable post-approval.';
            END IF;
            IF NEW.period_start <> OLD.period_start OR NEW.period_end <> OLD.period_end THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: period dates are immutable post-approval.';
            END IF;
            IF NEW.currency <> OLD.currency THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: currency is immutable post-approval.';
            END IF;
            IF NEW.payout_count <> OLD.payout_count THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: payout_count is immutable post-approval.';
            END IF;
            IF NEW.total_amount <> OLD.total_amount THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: total_amount is immutable post-approval.';
            END IF;
            IF NEW.created_by <> OLD.created_by THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: created_by is immutable post-approval.';
            END IF;
            IF OLD.approved_by IS NOT NULL AND NEW.approved_by <> OLD.approved_by THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: approved_by is immutable post-approval.';
            END IF;
            IF OLD.approved_at IS NOT NULL AND NEW.approved_at <> OLD.approved_at THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: approved_at is immutable post-approval.';
            END IF;
            IF NEW.idempotency_key <> OLD.idempotency_key THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: idempotency_key is immutable post-approval.';
            END IF;
        END IF;
        RETURN NEW;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_payment_run_immutability ON public.creator_payment_runs;
CREATE TRIGGER trg_guard_payment_run_immutability
BEFORE UPDATE OR DELETE ON public.creator_payment_runs
FOR EACH ROW EXECUTE FUNCTION public.fn_guard_payment_run_post_approval_immutability();


-- Guard on creator_payment_run_items: prevent add/remove/tampering once parent run is approved
CREATE OR REPLACE FUNCTION public.fn_guard_payment_run_items_immutability()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    parent_status VARCHAR(32);
    target_run_id UUID;
BEGIN
    target_run_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.payment_run_id ELSE NEW.payment_run_id END;

    SELECT status INTO parent_status
    FROM public.creator_payment_runs
    WHERE id = target_run_id;

    IF parent_status IN ('APPROVED', 'EXPORTED', 'AWAITING_EXTERNAL_RESULT', 'RESULTS_RECORDED', 'RECONCILED') THEN
        IF TG_OP = 'INSERT' THEN
            RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Cannot add items to payment run in % state.', parent_status;
        ELSIF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Cannot remove items from payment run in % state.', parent_status;
        ELSIF TG_OP = 'UPDATE' THEN
            -- Financial & snapshot fields immutable
            IF NEW.amount <> OLD.amount OR NEW.currency <> OLD.currency THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Item amount and currency are immutable post-approval.';
            END IF;
            IF NEW.payout_id <> OLD.payout_id OR NEW.creator_id <> OLD.creator_id THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Item payout and creator bindings are immutable post-approval.';
            END IF;
            IF NEW.beneficiary_name_snapshot <> OLD.beneficiary_name_snapshot OR
               NEW.bank_name_snapshot <> OLD.bank_name_snapshot OR
               NEW.account_number_snapshot <> OLD.account_number_snapshot OR
               NEW.branch_code_snapshot <> OLD.branch_code_snapshot OR
               NEW.account_type_snapshot <> OLD.account_type_snapshot OR
               NEW.payment_reference_snapshot <> OLD.payment_reference_snapshot THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Item beneficiary snapshot is immutable post-approval.';
            END IF;
            IF NEW.payment_run_id <> OLD.payment_run_id THEN
                RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: Cannot reassign item to another payment run.';
            END IF;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;

DROP TRIGGER IF EXISTS trg_guard_payment_run_items_immutability ON public.creator_payment_run_items;
CREATE TRIGGER trg_guard_payment_run_items_immutability
BEFORE INSERT OR UPDATE OR DELETE ON public.creator_payment_run_items
FOR EACH ROW EXECUTE FUNCTION public.fn_guard_payment_run_items_immutability();

-- ------------------------------------------------------------------------------
-- 5. ROW LEVEL SECURITY (RLS) FOR SERVICE ROLE RESTRICTION
-- ------------------------------------------------------------------------------
ALTER TABLE public.creator_payment_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.creator_payment_run_items ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_creator_payment_runs" ON public.creator_payment_runs;
CREATE POLICY "service_role_all_creator_payment_runs"
    ON public.creator_payment_runs FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_creator_payment_run_items" ON public.creator_payment_run_items;
CREATE POLICY "service_role_all_creator_payment_run_items"
    ON public.creator_payment_run_items FOR ALL TO service_role USING (true) WITH CHECK (true);

COMMIT;
