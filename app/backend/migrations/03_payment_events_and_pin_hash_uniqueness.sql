-- Welele Media™ — Migration 03: Payment Events & PIN Hash Uniqueness Hardening
-- CORRECTED REVIEW ARTIFACT. Do not execute without explicit owner authorization.
-- Staging target: dbsnaidhznofvyffdfni
-- Production target: mngyyxqdhjgteezwkxdn (FROZEN)
--
-- This script has not been executed. Confirm the target and schema immediately
-- before execution. Run the real-PostgreSQL tests after applying to staging.
--
-- Important accounting contract:
--   coin_ledger.amount = base coins + bonus coins credited by this transaction.
--   balance_before / balance_after = combined spendable base + bonus balance.
--   lifetime_coins_purchased increases only for purchase/top-up transaction types.
-- Confirm these semantics against the current schema/callers before execution.

BEGIN;

-- Fail early rather than silently attempting to repair pre-existing duplicate
-- financial identities. Do not delete or merge financial rows automatically.
DO $$
DECLARE
    v_duplicates BIGINT;
BEGIN
    IF to_regclass('public.payment_events') IS NULL
       OR to_regclass('public.wallets') IS NULL
       OR to_regclass('public.coin_ledger') IS NULL THEN
        RAISE EXCEPTION 'Migration 03 preflight failed: one or more required tables are missing';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'payment_events'
          AND column_name IN ('processing_status', 'provider', 'idempotency_key',
                              'amount_fiat', 'coins_grant', 'currency',
                              'provider_transaction_id')
        GROUP BY table_schema, table_name
        HAVING COUNT(DISTINCT column_name) = 7
    ) THEN
        RAISE EXCEPTION 'Migration 03 preflight failed: payment_events is missing required columns';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'wallets'
          AND column_name IN ('id', 'user_id', 'coin_balance', 'bonus_coins',
                              'lifetime_coins_purchased', 'lifetime_coins_spent',
                              'updated_at')
        GROUP BY table_schema, table_name
        HAVING COUNT(DISTINCT column_name) = 7
    ) THEN
        RAISE EXCEPTION 'Migration 03 preflight failed: wallets is missing required columns';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'coin_ledger'
          AND column_name IN ('id', 'wallet_id', 'user_id', 'amount',
                              'balance_before', 'balance_after', 'transaction_type',
                              'reference_id', 'idempotency_key', 'description',
                              'created_at')
        GROUP BY table_schema, table_name
        HAVING COUNT(DISTINCT column_name) = 11
    ) THEN
        RAISE EXCEPTION 'Migration 03 preflight failed: coin_ledger is missing required columns';
    END IF;

    SELECT COUNT(*) INTO v_duplicates
    FROM (
        SELECT user_id FROM public.wallets
        GROUP BY user_id HAVING COUNT(*) > 1
    ) d;
    IF v_duplicates > 0 THEN
        RAISE EXCEPTION 'Migration 03 stopped: % duplicate wallets.user_id groups exist; investigate manually', v_duplicates;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'coin_ledger'
          AND column_name = 'idempotency_key'
    ) THEN
        EXECUTE $q$
            SELECT COUNT(*) FROM (
                SELECT idempotency_key
                FROM public.coin_ledger
                WHERE idempotency_key IS NOT NULL
                GROUP BY idempotency_key
                HAVING COUNT(*) > 1
            ) d
        $q$ INTO v_duplicates;
        IF v_duplicates > 0 THEN
            RAISE EXCEPTION 'Migration 03 stopped: % duplicate coin_ledger.idempotency_key groups exist; investigate manually', v_duplicates;
        END IF;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'payment_events'
          AND column_name = 'pin_hash'
    ) THEN
        ALTER TABLE public.payment_events ADD COLUMN pin_hash CHAR(64);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_events_pin_hash_success
    ON public.payment_events (pin_hash)
    WHERE processing_status = 'SUCCESS' AND pin_hash IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_events_provider_idempotency
    ON public.payment_events (provider, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_wallets_user_id
    ON public.wallets (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_coin_ledger_idempotency_key
    ON public.coin_ledger (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_payment_events_provider_tx
    ON public.payment_events (provider, provider_transaction_id);

-- Replace only single-column CHECK constraints on transaction_type.
DO $$
DECLARE
    r RECORD;
    v_attnum SMALLINT;
BEGIN
    SELECT attnum INTO v_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.coin_ledger'::regclass
      AND attname = 'transaction_type' AND NOT attisdropped;

    IF v_attnum IS NULL THEN
        RAISE EXCEPTION 'Migration 03: coin_ledger.transaction_type does not exist';
    END IF;

    FOR r IN
        SELECT conname FROM pg_constraint
        WHERE conrelid = 'public.coin_ledger'::regclass
          AND contype = 'c'
          AND array_length(conkey, 1) = 1
          AND conkey[1] = v_attnum
    LOOP
        EXECUTE format('ALTER TABLE public.coin_ledger DROP CONSTRAINT %I', r.conname);
    END LOOP;

    ALTER TABLE public.coin_ledger
        ADD CONSTRAINT coin_ledger_transaction_type_check
        CHECK (transaction_type IN (
            'TOPUP_PURCHASE', 'TOPUP_1VOUCHER', 'TOPUP', 'AIRTIME_TOPUP',
            'TOPUP_VODACOM_DCB', 'TOPUP_PAYSTACK', 'TOPUP_OZOW',
            'AIRTIME_PASS', 'EPISODE_UNLOCK', 'GIFT_SENT', 'ROYALTY_CREDIT',
            'ONBOARDING_REWARD', 'DAILY_REWARD', 'REFUND', 'DISPUTE_REVERSAL',
            'ADJUSTMENT'
        ));
END $$;

-- Append-only coin ledger. Corrections must be compensating entries.
CREATE OR REPLACE FUNCTION public.fn_enforce_coin_ledger_append_only()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'CRITICAL ACCOUNTING INVARIANT: coin_ledger is append-only. % is prohibited; post a compensating journal row instead.',
        TG_OP;
END $$;

DROP TRIGGER IF EXISTS trg_guard_coin_ledger_append_only ON public.coin_ledger;
CREATE TRIGGER trg_guard_coin_ledger_append_only
BEFORE UPDATE OR DELETE ON public.coin_ledger
FOR EACH ROW EXECUTE FUNCTION public.fn_enforce_coin_ledger_append_only();

-- Protect settled receipts. Metadata may still be updated for reconciliation.
CREATE OR REPLACE FUNCTION public.fn_guard_payment_events_settlement()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'CRITICAL AUDIT INVARIANT: deletion from payment_events is prohibited.';
    END IF;

    IF TG_OP = 'UPDATE' THEN
        IF OLD.processing_status IN ('SUCCESS', 'SETTLED_DISPUTED') THEN
            IF NEW.amount_fiat IS DISTINCT FROM OLD.amount_fiat
               OR NEW.coins_grant IS DISTINCT FROM OLD.coins_grant
               OR NEW.currency IS DISTINCT FROM OLD.currency
               OR NEW.provider_transaction_id IS DISTINCT FROM OLD.provider_transaction_id
               OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key
               OR NEW.pin_hash IS DISTINCT FROM OLD.pin_hash THEN
                RAISE EXCEPTION
                    'CRITICAL FINTECH INVARIANT: financial fields on a settled payment event are immutable.';
            END IF;
        END IF;

        IF OLD.processing_status = 'SUCCESS'
           AND NEW.processing_status IS DISTINCT FROM 'SUCCESS'
           AND NEW.processing_status IS DISTINCT FROM 'SETTLED_DISPUTED' THEN
            RAISE EXCEPTION
                'CRITICAL FINTECH INVARIANT: SUCCESS may remain SUCCESS or transition to SETTLED_DISPUTED; received %.',
                NEW.processing_status;
        END IF;

        IF OLD.processing_status = 'SETTLED_DISPUTED'
           AND NEW.processing_status IS DISTINCT FROM 'SETTLED_DISPUTED' THEN
            RAISE EXCEPTION
                'CRITICAL FINTECH INVARIANT: SETTLED_DISPUTED cannot transition to another status; received %.',
                NEW.processing_status;
        END IF;
    END IF;

    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_guard_payment_events_settlement ON public.payment_events;
CREATE TRIGGER trg_guard_payment_events_settlement
BEFORE UPDATE OR DELETE ON public.payment_events
FOR EACH ROW EXECUTE FUNCTION public.fn_guard_payment_events_settlement();

-- Atomic wallet credit: ledger insert and wallet mutation share one transaction.
-- Advisory transaction lock serializes every invocation using the same non-null
-- idempotency key, including attempts made for different users. Hash collisions
-- only serialize unrelated keys; the unique index remains the final guard.
CREATE OR REPLACE FUNCTION public.fn_credit_coins_atomic(
    p_user_id UUID,
    p_base_coins INT,
    p_bonus_coins INT DEFAULT 0,
    p_transaction_type VARCHAR(32) DEFAULT 'TOPUP_1VOUCHER',
    p_reference_id VARCHAR(128) DEFAULT '',
    p_idempotency_key VARCHAR(128) DEFAULT NULL,
    p_description TEXT DEFAULT ''
)
RETURNS JSONB LANGUAGE plpgsql AS $$
DECLARE
    v_wallet_id UUID;
    v_current_balance BIGINT;
    v_current_bonus BIGINT;
    v_new_base BIGINT;
    v_new_bonus BIGINT;
    v_total_before BIGINT;
    v_total_after BIGINT;
    v_total_credit BIGINT;
    v_lifetime_purchased BIGINT;
    v_ledger_id UUID;
    v_existing_ledger RECORD;
    v_is_purchase BOOLEAN;
BEGIN
    -- Validate before lock acquisition, wallet creation, or other mutation.
    IF p_user_id IS NULL THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: user_id cannot be null';
    END IF;
    IF p_base_coins IS NULL OR p_bonus_coins IS NULL THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: base_coins and bonus_coins cannot be null';
    END IF;
    IF p_base_coins < 0 OR p_bonus_coins < 0 THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: coin amounts cannot be negative';
    END IF;

    v_total_credit := p_base_coins::BIGINT + p_bonus_coins::BIGINT;
    IF v_total_credit <= 0 OR v_total_credit > 2147483647 THEN
        RAISE EXCEPTION 'CRITICAL ACCOUNTING ERROR: combined credit must be between 1 and 2147483647';
    END IF;

    IF p_transaction_type IS NULL OR BTRIM(p_transaction_type) = '' THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: transaction_type cannot be null or empty';
    END IF;
    IF p_transaction_type NOT IN (
        'TOPUP_PURCHASE', 'TOPUP_1VOUCHER', 'TOPUP', 'AIRTIME_TOPUP',
        'TOPUP_VODACOM_DCB', 'TOPUP_PAYSTACK', 'TOPUP_OZOW',
        'AIRTIME_PASS', 'EPISODE_UNLOCK', 'GIFT_SENT', 'ROYALTY_CREDIT',
        'ONBOARDING_REWARD', 'DAILY_REWARD', 'REFUND', 'DISPUTE_REVERSAL',
        'ADJUSTMENT'
    ) THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: invalid transaction_type %', p_transaction_type;
    END IF;

    v_is_purchase := p_transaction_type IN (
        'TOPUP_PURCHASE', 'TOPUP_1VOUCHER', 'TOPUP', 'AIRTIME_TOPUP',
        'TOPUP_VODACOM_DCB', 'TOPUP_PAYSTACK', 'TOPUP_OZOW'
    );

    IF v_is_purchase AND (p_idempotency_key IS NULL OR BTRIM(p_idempotency_key) = '') THEN
        RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: purchase/top-up credits require a non-empty idempotency_key';
    END IF;

    -- Serialize all callers sharing this key before reading or inserting a row.
    -- No key means no replay protection; live payment settlement callers must
    -- always provide a durable, non-empty idempotency key.
    IF p_idempotency_key IS NOT NULL THEN
        IF BTRIM(p_idempotency_key) = '' THEN
            RAISE EXCEPTION 'CRITICAL INPUT VALIDATION ERROR: idempotency_key cannot be empty';
        END IF;
        PERFORM pg_advisory_xact_lock(
            hashtextextended('welele.coin-credit:' || p_idempotency_key, 0)
        );

        SELECT id, wallet_id, user_id, amount, balance_before, balance_after,
               transaction_type, reference_id
        INTO v_existing_ledger
        FROM public.coin_ledger
        WHERE idempotency_key = p_idempotency_key;

        IF FOUND THEN
            IF v_existing_ledger.user_id IS DISTINCT FROM p_user_id
               OR v_existing_ledger.amount::BIGINT IS DISTINCT FROM v_total_credit
               OR v_existing_ledger.transaction_type IS DISTINCT FROM p_transaction_type
               OR COALESCE(v_existing_ledger.reference_id, '') IS DISTINCT FROM COALESCE(p_reference_id, '') THEN
                RAISE EXCEPTION 'CRITICAL IDEMPOTENCY VIOLATION: key % was previously used for a different request', p_idempotency_key;
            END IF;
            RETURN jsonb_build_object(
                'success', TRUE, 'already_processed', TRUE,
                'message', 'Idempotent credit already processed',
                'ledger_id', v_existing_ledger.id, 'wallet_id', v_existing_ledger.wallet_id,
                'amount', v_existing_ledger.amount,
                'balance_before', v_existing_ledger.balance_before,
                'balance_after', v_existing_ledger.balance_after
            );
        END IF;
    END IF;

    INSERT INTO public.wallets (
        id, user_id, coin_balance, bonus_coins,
        lifetime_coins_purchased, lifetime_coins_spent, updated_at
    ) VALUES (
        gen_random_uuid(), p_user_id, 0, 0, 0, 0, NOW()
    ) ON CONFLICT (user_id) DO NOTHING;

    SELECT id, coin_balance, bonus_coins
    INTO v_wallet_id, v_current_balance, v_current_bonus
    FROM public.wallets WHERE user_id = p_user_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'CRITICAL ACCOUNTING ERROR: wallet could not be found or created for user %', p_user_id;
    END IF;

    -- Recheck after the wallet lock as a defensive invariant.
    IF p_idempotency_key IS NOT NULL THEN
        SELECT id, wallet_id, user_id, amount, balance_before, balance_after,
               transaction_type, reference_id
        INTO v_existing_ledger
        FROM public.coin_ledger
        WHERE idempotency_key = p_idempotency_key;

        IF FOUND THEN
            IF v_existing_ledger.user_id IS DISTINCT FROM p_user_id
               OR v_existing_ledger.amount::BIGINT IS DISTINCT FROM v_total_credit
               OR v_existing_ledger.transaction_type IS DISTINCT FROM p_transaction_type
               OR COALESCE(v_existing_ledger.reference_id, '') IS DISTINCT FROM COALESCE(p_reference_id, '') THEN
                RAISE EXCEPTION 'CRITICAL IDEMPOTENCY VIOLATION: key % was concurrently used for a different request', p_idempotency_key;
            END IF;
            RETURN jsonb_build_object(
                'success', TRUE, 'already_processed', TRUE,
                'message', 'Idempotent credit already processed (serialized)',
                'ledger_id', v_existing_ledger.id, 'wallet_id', v_existing_ledger.wallet_id,
                'amount', v_existing_ledger.amount,
                'balance_before', v_existing_ledger.balance_before,
                'balance_after', v_existing_ledger.balance_after
            );
        END IF;
    END IF;

    v_total_before := v_current_balance + v_current_bonus;
    v_new_base := v_current_balance + p_base_coins::BIGINT;
    v_new_bonus := v_current_bonus + p_bonus_coins::BIGINT;
    v_total_after := v_new_base + v_new_bonus;

    -- Current wallet/ledger schema uses integer-sized coin values in the
    -- existing contract. Reject overflow explicitly before inserting a journal
    -- entry or mutating the wallet; never rely on a later cast failure.
    IF v_new_base > 2147483647 OR v_new_bonus > 2147483647
       OR v_total_before > 2147483647 OR v_total_after > 2147483647 THEN
        RAISE EXCEPTION 'CRITICAL ACCOUNTING ERROR: wallet balance would exceed supported integer range';
    END IF;

    IF v_is_purchase THEN
        SELECT lifetime_coins_purchased::BIGINT + p_base_coins::BIGINT
        INTO v_lifetime_purchased
        FROM public.wallets WHERE id = v_wallet_id;
        IF v_lifetime_purchased > 2147483647 THEN
            RAISE EXCEPTION 'CRITICAL ACCOUNTING ERROR: lifetime purchased coins would exceed supported integer range';
        END IF;
    END IF;

    v_ledger_id := gen_random_uuid();

    -- Insert the journal row before changing wallet balances. A duplicate key
    -- is an invariant failure here, so it aborts the transaction; it is not
    -- converted into a possibly stale SELECT-based replay.
    INSERT INTO public.coin_ledger (
        id, wallet_id, user_id, amount, balance_before, balance_after,
        transaction_type, reference_id, idempotency_key, description, created_at
    ) VALUES (
        v_ledger_id, v_wallet_id, p_user_id, v_total_credit::INT,
        v_total_before::INT, v_total_after::INT, p_transaction_type,
        NULLIF(p_reference_id, ''), p_idempotency_key,
        COALESCE(NULLIF(p_description, ''), 'Credited ' || v_total_credit || ' coins via ' || p_transaction_type),
        NOW()
    );

    UPDATE public.wallets
    SET coin_balance = v_new_base,
        bonus_coins = v_new_bonus,
        lifetime_coins_purchased = lifetime_coins_purchased
            + CASE WHEN v_is_purchase THEN p_base_coins ELSE 0 END,
        updated_at = NOW()
    WHERE id = v_wallet_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'CRITICAL ACCOUNTING ERROR: wallet update failed for user %', p_user_id;
    END IF;

    RETURN jsonb_build_object(
        'success', TRUE, 'already_processed', FALSE,
        'message', 'Credit executed successfully',
        'ledger_id', v_ledger_id, 'wallet_id', v_wallet_id,
        'amount', v_total_credit,
        'balance_before', v_total_before,
        'balance_after', v_total_after
    );
END $$;

REVOKE ALL ON FUNCTION public.fn_credit_coins_atomic(UUID, INT, INT, VARCHAR, VARCHAR, VARCHAR, TEXT)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.fn_credit_coins_atomic(UUID, INT, INT, VARCHAR, VARCHAR, VARCHAR, TEXT)
    TO service_role;

COMMIT;
