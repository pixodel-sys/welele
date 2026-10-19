-- =============================================================================
-- Welele Media™ — Migration 09: Relational Ownership Normalization (6O-3)
-- Strictly Non-Destructive & Additive: Preserves All Accepted 6I Schemas Intact.
-- =============================================================================

-- 1. Exception Table for Auditing Unresolved Catalog Items
CREATE TABLE IF NOT EXISTS public.migration_unresolved_series_exceptions (
    series_id UUID PRIMARY KEY,
    title TEXT,
    ip_id UUID,
    detected_master_owner_id UUID,
    reason TEXT NOT NULL,
    flagged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolved_by UUID
);

-- 2. Add creator_id foreign keys to series and episodes (initially nullable for safe backfill)
ALTER TABLE public.series 
    ADD COLUMN IF NOT EXISTS creator_id TEXT REFERENCES public.creator_profiles(id);

ALTER TABLE public.episodes 
    ADD COLUMN IF NOT EXISTS creator_id TEXT REFERENCES public.creator_profiles(id);

-- 3. Deterministic Relational Backfill: Map series.creator_id via verified digital_ips owner
UPDATE public.series s
SET creator_id = cp.id
FROM public.digital_ips ip
JOIN public.creator_profiles cp ON cp.owner_user_id = ip.master_owner_id
WHERE s.ip_id = ip.id AND s.creator_id IS NULL;

-- 4. Audit & Flag Any Unresolved Series (Fail-Closed: Do NOT Blanket-Assign to Zola)
INSERT INTO public.migration_unresolved_series_exceptions (series_id, title, ip_id, detected_master_owner_id, reason)
SELECT s.id, s.title, s.ip_id, ip.master_owner_id, 'No matching creator_profile found for master_owner_id'
FROM public.series s
LEFT JOIN public.digital_ips ip ON s.ip_id = ip.id
WHERE s.creator_id IS NULL
ON CONFLICT (series_id) DO NOTHING;

-- 5. Cascade series.creator_id to child episodes
UPDATE public.episodes e
SET creator_id = s.creator_id
FROM public.series s
WHERE e.series_id = s.id AND s.creator_id IS NOT NULL AND e.creator_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_series_creator_id ON public.series(creator_id);
CREATE INDEX IF NOT EXISTS idx_episodes_creator_id ON public.episodes(creator_id);

-- 6. Enforce Series-Episode Creator Consistency via Trigger
CREATE OR REPLACE FUNCTION public.check_episode_series_creator_consistency()
RETURNS TRIGGER AS $$
DECLARE
    parent_creator_id TEXT;
BEGIN
    SELECT creator_id INTO parent_creator_id FROM public.series WHERE id = NEW.series_id;
    IF parent_creator_id IS NOT NULL AND NEW.creator_id IS NOT NULL AND NEW.creator_id <> parent_creator_id THEN
        RAISE EXCEPTION 'Relational Ownership Violation: Episode creator_id (%) does not match parent series creator_id (%)', 
            NEW.creator_id, parent_creator_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_episode_creator_consistency ON public.episodes;
CREATE TRIGGER trg_episode_creator_consistency
BEFORE INSERT OR UPDATE ON public.episodes
FOR EACH ROW EXECUTE FUNCTION public.check_episode_series_creator_consistency();
