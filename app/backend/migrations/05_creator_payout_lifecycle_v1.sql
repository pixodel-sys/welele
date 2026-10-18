-- ==============================================================================
-- WELELE MEDIA™ — WORKSTREAM 6I-G.2 CREATOR PAYOUT LIFECYCLE & STATE MACHINE
-- Migration: 05_creator_payout_lifecycle_v1.sql
-- Environment: STAGING ONLY (Target: dbsnaidhznofvyffdfni)
-- Production: FROZEN / STRICTLY FORBIDDEN TO RUN ON PRODUCTION
-- ==============================================================================
-- Purpose:
-- 1. Updates check constraint on public.creator_payouts.status to support the
--    authoritative 6I-G.2 Payout State Machine:
--    'PENDING', 'PROCESSING', 'PAID', 'FAILED', 'REVERSED', 'HELD'
--    (Retaining 'SETTLED', 'REJECTED', 'CANCELLED' for backward audit compatibility).
-- 2. Adds performance and audit traversal indexes on public.creator_payout_allocations.
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. EXPAND PAYOUT STATUS CONSTRAINT TO INCLUDE 6I-G.2 LIFECYCLE STATES
-- ------------------------------------------------------------------------------
ALTER TABLE public.creator_payouts
    DROP CONSTRAINT IF EXISTS creator_payouts_status_check;

ALTER TABLE public.creator_payouts
    ADD CONSTRAINT creator_payouts_status_check
    CHECK (status IN (
        'PENDING',
        'PROCESSING',
        'PAID',
        'FAILED',
        'REVERSED',
        'HELD'
    ));

-- ------------------------------------------------------------------------------
-- 2. ADD INDEXES ON CREATOR PAYOUT ALLOCATIONS
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_creator_payout_allocations_payout
    ON public.creator_payout_allocations(payout_id);

CREATE INDEX IF NOT EXISTS idx_creator_payout_allocations_ledger
    ON public.creator_payout_allocations(ledger_entry_id);

COMMIT;

-- ------------------------------------------------------------------------------
-- REVERSIBILITY / DOWN MIGRATION (REFERENCE ONLY):
-- ------------------------------------------------------------------------------
-- BEGIN;
-- ALTER TABLE public.creator_payouts DROP CONSTRAINT IF EXISTS creator_payouts_status_check;
-- ALTER TABLE public.creator_payouts ADD CONSTRAINT creator_payouts_status_check
--     CHECK (status IN ('PENDING', 'PROCESSING', 'SETTLED', 'REJECTED', 'CANCELLED'));
-- DROP INDEX IF EXISTS public.idx_creator_payout_allocations_payout;
-- DROP INDEX IF EXISTS public.idx_creator_payout_allocations_ledger;
-- COMMIT;
