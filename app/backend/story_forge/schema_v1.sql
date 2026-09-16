-- ============================================================================
-- WELELE STORY FORGE™ — PERSISTENT NARRATIVE ENGINE SCHEMA v1.0
-- Database: PostgreSQL 15+ (Existing Supabase Instance)
-- Architecture: Decoupled Narrative Reasoning Engine linked to Canonical IP Spine
-- ============================================================================

-- Ensure crypto and UUID extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ----------------------------------------------------------------------------
-- 1. FORGE STORIES (Development Work in Progress)
-- NOTE: Represents an active narrative development work, NOT a duplicate IP entity.
-- Links directly to canonical `digital_ips.id` when registered.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digital_ip_id UUID REFERENCES public.digital_ips(id) ON DELETE SET NULL,
    owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    title VARCHAR(255) NOT NULL,
    logline TEXT,
    primary_language VARCHAR(32) NOT NULL DEFAULT 'isiZulu',
    status VARCHAR(32) NOT NULL DEFAULT 'IN_DEVELOPMENT' CHECK (status IN ('IN_DEVELOPMENT', 'FORGE_COMPLETE', 'PROMOTED_TO_IP', 'ARCHIVED')),
    current_state_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forge_stories_ip ON public.forge_stories(digital_ip_id);
CREATE INDEX IF NOT EXISTS idx_forge_stories_owner ON public.forge_stories(owner_id);

-- ----------------------------------------------------------------------------
-- 2. FORGE SESSIONS & AUDIT TRACES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    session_status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE' CHECK (session_status IN ('ACTIVE', 'PAUSED', 'COMPLETED', 'ABANDONED')),
    active_trace_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forge_sessions_story ON public.forge_sessions(story_id);
CREATE INDEX IF NOT EXISTS idx_forge_sessions_creator ON public.forge_sessions(creator_id);

CREATE TABLE IF NOT EXISTS public.forge_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES public.forge_sessions(id) ON DELETE CASCADE,
    total_transitions INT NOT NULL DEFAULT 0,
    trace_status VARCHAR(32) NOT NULL DEFAULT 'RECORDING' CHECK (trace_status IN ('RECORDING', 'SEALED', 'FAILED')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sealed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_forge_traces_story ON public.forge_traces(story_id);
CREATE INDEX IF NOT EXISTS idx_forge_traces_session ON public.forge_traces(session_id);

-- ----------------------------------------------------------------------------
-- 3. FORGE STORY STATES (Immutable Versioned State Snapshots)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_story_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    state_version INT NOT NULL,
    previous_state_version INT,
    source_transition_id UUID,
    premise TEXT,
    theme TEXT,
    tone VARCHAR(64),
    world_setting JSONB NOT NULL DEFAULT '{}'::jsonb,
    rules_and_lore JSONB NOT NULL DEFAULT '[]'::jsonb,
    unresolved_count INT NOT NULL DEFAULT 0,
    created_by UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_story_state_version UNIQUE (story_id, state_version)
);

CREATE INDEX IF NOT EXISTS idx_forge_story_states_story_ver ON public.forge_story_states(story_id, state_version);

-- ----------------------------------------------------------------------------
-- 4. FORGE CHARACTERS (Queryable Relational Narrative State)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    state_version INT NOT NULL,
    name VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'UNRESOLVED' CHECK (role IN ('PROTAGONIST', 'ANTAGONIST', 'CONFIDANT', 'CATALYST', 'SUPPORTING', 'UNRESOLVED')),
    archetype VARCHAR(64),
    core_motivation TEXT,
    secret_desire TEXT,
    fatal_flaw TEXT,
    current_status VARCHAR(32) NOT NULL DEFAULT 'FACT' CHECK (current_status IN ('FACT', 'UNKNOWN', 'UNRESOLVED')),
    relationships JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_forge_char_version UNIQUE (story_id, state_version, name)
);

CREATE INDEX IF NOT EXISTS idx_forge_char_story_ver ON public.forge_characters(story_id, state_version);

-- ----------------------------------------------------------------------------
-- 5. FORGE CHRONOLOGY EVENTS (Unified Narrative & Temporal Event Spine)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_chronology_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    state_version INT NOT NULL,
    event_sequence INT NOT NULL,
    story_time VARCHAR(128),
    headline VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(128),
    participants TEXT[] NOT NULL DEFAULT '{}',
    causal_antecedents UUID[] NOT NULL DEFAULT '{}',
    consequences TEXT[] NOT NULL DEFAULT '{}',
    event_status VARCHAR(32) NOT NULL DEFAULT 'FACT' CHECK (event_status IN ('FACT', 'UNKNOWN', 'UNRESOLVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_forge_event_sequence UNIQUE (story_id, state_version, event_sequence)
);

CREATE INDEX IF NOT EXISTS idx_forge_events_story_ver ON public.forge_chronology_events(story_id, state_version);

-- ----------------------------------------------------------------------------
-- 6. FORGE KNOWLEDGE STATES (Subjective Character Knowledge & Beliefs)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_knowledge_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    state_version INT NOT NULL,
    character_name VARCHAR(128) NOT NULL,
    fact_key VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('KNOWS', 'BELIEVES', 'DOES_NOT_KNOW', 'SUSPECTS')),
    source_event_id UUID,
    confidence NUMERIC(3, 2) NOT NULL DEFAULT 1.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_char_knowledge UNIQUE (story_id, state_version, character_name, fact_key)
);

CREATE INDEX IF NOT EXISTS idx_forge_knowledge_story_ver ON public.forge_knowledge_states(story_id, state_version);

-- ----------------------------------------------------------------------------
-- 7. FORGE NARRATIVE PLANTS (Setup and Payoff Ledger)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_narrative_plants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    state_version INT NOT NULL,
    element_code VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    introduced_event_id UUID,
    intended_payoff TEXT NOT NULL,
    payoff_status VARCHAR(32) NOT NULL DEFAULT 'PLANTED' CHECK (payoff_status IN ('PLANTED', 'PAID_OFF', 'ABANDONED', 'SUBVERTED')),
    payoff_event_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_narrative_plant UNIQUE (story_id, state_version, element_code)
);

CREATE INDEX IF NOT EXISTS idx_forge_plants_story_ver ON public.forge_narrative_plants(story_id, state_version);

-- ----------------------------------------------------------------------------
-- 8. FORGE DEPENDENCIES (Central Control Objects)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    dependency_key VARCHAR(128) NOT NULL,
    dependency_type VARCHAR(32) NOT NULL CHECK (dependency_type IN ('NARRATIVE', 'CHARACTER', 'CAUSAL', 'TEMPORAL', 'KNOWLEDGE', 'PRODUCTION', 'CANON')),
    status VARCHAR(32) NOT NULL DEFAULT 'DETECTED' CHECK (status IN ('DETECTED', 'ASSESSED', 'PRIORITISED', 'ACTIVE', 'RESOLVED', 'DELIBERATELY_UNKNOWN', 'DEFERRED')),
    target_entity VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    impact INT NOT NULL DEFAULT 5,
    urgency INT NOT NULL DEFAULT 5,
    risk INT NOT NULL DEFAULT 5,
    leverage INT NOT NULL DEFAULT 5,
    cost INT NOT NULL DEFAULT 2,
    priority_score NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    priority_rationale TEXT,
    suggested_skill VARCHAR(64) NOT NULL DEFAULT 'EXCAVATOR',
    resolved_by_transition_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_story_dep_key UNIQUE (story_id, dependency_key)
);

CREATE INDEX IF NOT EXISTS idx_forge_deps_story_status ON public.forge_dependencies(story_id, status);
CREATE INDEX IF NOT EXISTS idx_forge_deps_priority ON public.forge_dependencies(priority_score DESC);

-- ----------------------------------------------------------------------------
-- 9. FORGE TRANSITIONS (Immutable Narrative Audit Trail)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    trace_id UUID NOT NULL REFERENCES public.forge_traces(id) ON DELETE CASCADE,
    sequence INT NOT NULL,
    creator_input TEXT,
    interpretation TEXT NOT NULL,
    skill VARCHAR(64) NOT NULL,
    active_dependency_id UUID REFERENCES public.forge_dependencies(id) ON DELETE SET NULL,
    priority_score NUMERIC(6, 2),
    authority_mode VARCHAR(32) NOT NULL CHECK (authority_mode IN ('ASK', 'INFER', 'PROPOSE', 'RECORD_PRODUCTION_DECISION', 'STOP')),
    question_asked TEXT,
    creator_response TEXT,
    mutations_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    consequences_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_trace_sequence UNIQUE (trace_id, sequence)
);

CREATE INDEX IF NOT EXISTS idx_forge_transitions_trace ON public.forge_transitions(trace_id, sequence);
CREATE INDEX IF NOT EXISTS idx_forge_transitions_story ON public.forge_transitions(story_id);

-- ----------------------------------------------------------------------------
-- 10. FORGE STATE MUTATIONS (Fine-Grained Mutation Audit Log)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_state_mutations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transition_id UUID NOT NULL REFERENCES public.forge_transitions(id) ON DELETE CASCADE,
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    target_path VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB NOT NULL,
    mutation_type VARCHAR(32) NOT NULL CHECK (mutation_type IN ('CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE')),
    rationale TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forge_mutations_trans ON public.forge_state_mutations(transition_id);

-- ----------------------------------------------------------------------------
-- 11. FORGE PRODUCTION DECISIONS (Deferred Physical Staging Choices)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_production_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    decision_key VARCHAR(128) NOT NULL,
    narrative_resolution TEXT NOT NULL,
    production_aspect VARCHAR(64) NOT NULL CHECK (production_aspect IN ('LOCATION', 'STUNT', 'CASTING', 'CHOREOGRAPHY', 'VFX', 'BUDGET_TIER', 'SOUND')),
    deferred_details TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'RECORDED' CHECK (status IN ('RECORDED', 'COMMITTED', 'RESOLVED_IN_PREPROD')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_story_prod_decision UNIQUE (story_id, decision_key)
);

CREATE INDEX IF NOT EXISTS idx_forge_prod_story ON public.forge_production_decisions(story_id);

-- ----------------------------------------------------------------------------
-- 12. FORGE COMPLETIONS (Readiness & Completion Assessment)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.forge_completions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID NOT NULL REFERENCES public.forge_stories(id) ON DELETE CASCADE,
    assessed_state_version INT NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('NOT_READY', 'FORGE_COMPLETE')),
    unresolved_narrative_count INT NOT NULL DEFAULT 0,
    unresolved_causal_count INT NOT NULL DEFAULT 0,
    unresolved_temporal_count INT NOT NULL DEFAULT 0,
    production_decisions_count INT NOT NULL DEFAULT 0,
    assessment_notes TEXT,
    assessed_by VARCHAR(64) NOT NULL DEFAULT 'FORGE_JUDGE',
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forge_completions_story ON public.forge_completions(story_id);
