/**
 * Welele Media™ — Story Forge Resilient Edge Staging Fallback
 * 
 * Architectural Contract:
 * - Preserves existing StoryState and buffered creator inputs when backend is temporarily offline.
 * - ZERO specimen-specific narrative ontology or hardcoded story names.
 * - ZERO independent narrative reasoning, question invention, dependency classification, or canon mutation.
 * - All narrative reasoning remains strictly owned by the backend Story Forge Kernel + Engine + Judge.
 * - Buffers creator inputs and provides replay capability upon backend reconnection.
 */

import {
  StoryState,
  StorySummary,
  CurrentAction,
  ForgeCycleResult,
  Dependency,
  ForgeTransition,
  ForgeCompletionAssessment,
  IntelligenceProjection,
} from '../types/storyForge';

import {
  CreateStoryPayload,
  StartSessionPayload,
  SubmitInputPayload
} from './storyForgeApi';

const STORAGE_KEYS = {
  STORIES: 'welele_forge_stories_v1',
  STATE_PREFIX: 'welele_forge_state_',
  SESSION_PREFIX: 'welele_forge_session_',
  TRACE_PREFIX: 'welele_forge_trace_',
  DEPS_PREFIX: 'welele_forge_deps_',
  PENDING_INPUTS_PREFIX: 'welele_forge_pending_inputs_',
};

// In-memory fallback if localStorage is disabled
const memoryStore: Record<string, any> = {};

function safeGetItem(key: string): any {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const val = localStorage.getItem(key);
      return val ? JSON.parse(val) : null;
    }
  } catch (e) {
    console.warn('[StoryForgeFallback] localStorage read failed:', e);
  }
  return memoryStore[key] || null;
}

function safeSetItem(key: string, val: any): void {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem(key, JSON.stringify(val));
    }
  } catch (e) {
    console.warn('[StoryForgeFallback] localStorage write failed:', e);
  }
  memoryStore[key] = val;
}

export const storyForgeFallback = {
  /**
   * Preserves a generic story shell in local cache.
   * Does NOT inject hardcoded specimen characters or world rules.
   */
  createStory: (payload: CreateStoryPayload): StoryState => {
    const storyId = payload.story_id || `story_local_${Date.now()}`;
    const title = payload.title.trim();
    const logline = payload.logline?.trim() || null;
    const primaryLanguage = payload.primary_language || 'isiZulu';

    // Truly generic story state: Zero invented characters or specimen lore
    const newState: StoryState = {
      story_id: storyId,
      state_version: 1,
      previous_state_version: null,
      title,
      logline,
      theme: null,
      tone: null,
      characters: {},
      world: {
        arena: '',
        rules_and_lore: []
      },
      plants: []
    };

    safeSetItem(STORAGE_KEYS.STATE_PREFIX + storyId, newState);

    const existingList: StorySummary[] = safeGetItem(STORAGE_KEYS.STORIES) || [];
    const summary: StorySummary = {
      id: storyId,
      title,
      owner_id: payload.owner_id || 'creator_current',
      digital_ip_id: payload.digital_ip_id || null,
      logline,
      primary_language: primaryLanguage,
      status: 'ACTIVE_DEVELOPMENT',
      current_state_version: 1
    };
    const filtered = existingList.filter(s => s.id !== storyId);
    safeSetItem(STORAGE_KEYS.STORIES, [summary, ...filtered]);

    return newState;
  },

  listStories: (): StorySummary[] => {
    return safeGetItem(STORAGE_KEYS.STORIES) || [];
  },

  getStorySummary: (storyId: string): StorySummary => {
    const list: StorySummary[] = safeGetItem(STORAGE_KEYS.STORIES) || [];
    const found = list.find(s => s.id === storyId);
    if (found) return found;
    return {
      id: storyId,
      title: 'Story',
      owner_id: 'creator_current',
      primary_language: 'isiZulu',
      status: 'ACTIVE_DEVELOPMENT',
      current_state_version: 1
    };
  },

  getStoryState: (storyId: string): StoryState => {
    const state = safeGetItem(STORAGE_KEYS.STATE_PREFIX + storyId);
    if (state) return state;

    return storyForgeFallback.createStory({
      story_id: storyId,
      title: 'Untitled Story',
      owner_id: 'creator_current'
    });
  },

  /**
   * Initializes a session shell awaiting live backend connection.
   * Does NOT invent story-specific dependencies or questions.
   */
  startSession: (storyId: string, payload: StartSessionPayload): any => {
    const sessionId = payload.session_id || `sess_${Date.now()}`;
    const state = storyForgeFallback.getStoryState(storyId);

    const currentAction: CurrentAction = {
      session_id: sessionId,
      story_id: storyId,
      state_version: state.state_version,
      action: 'ASK',
      skill: 'FORGE_JUDGE',
      question: null, // Fallback does not invent narrative questions
      active_dependency_key: null,
      active_dependency_description: null,
      unresolved_dependencies_count: 0,
      is_paused: false,
      requires_creator: true
    };

    const sessionData = {
      id: sessionId,
      story_id: storyId,
      creator_id: payload.creator_id,
      current_action: currentAction,
      created_at: new Date().toISOString(),
      is_degraded: true
    };

    safeSetItem(STORAGE_KEYS.SESSION_PREFIX + sessionId, sessionData);
    return { id: sessionId, story_id: storyId, status: 'ACTIVE', is_degraded: true };
  },

  getSessionStatus: (sessionId: string): any => {
    return safeGetItem(STORAGE_KEYS.SESSION_PREFIX + sessionId) || { id: sessionId, status: 'ACTIVE', is_degraded: true };
  },

  getCurrentAction: (sessionId: string): CurrentAction => {
    const session = safeGetItem(STORAGE_KEYS.SESSION_PREFIX + sessionId);
    if (session?.current_action) return session.current_action;

    return {
      session_id: sessionId,
      story_id: 'story_default',
      state_version: 1,
      action: 'ASK',
      skill: 'FORGE_JUDGE',
      question: null,
      unresolved_dependencies_count: 0,
      is_paused: false,
      requires_creator: true
    };
  },

  getDependencies: (storyId: string): Dependency[] => {
    return safeGetItem(STORAGE_KEYS.DEPS_PREFIX + storyId) || [];
  },

  getTrace: (storyId: string): ForgeTransition[] => {
    return safeGetItem(STORAGE_KEYS.TRACE_PREFIX + storyId) || [];
  },

  getCompletion: (storyId: string): ForgeCompletionAssessment => {
    const state: StoryState = storyForgeFallback.getStoryState(storyId);
    return {
      assessment_id: `asm_fallback_${Date.now()}`,
      story_id: storyId,
      assessed_state_version: state.state_version,
      status: 'NOT_READY',
      current_milestone: null,
      target_milestone: 'FORGE_COMPLETE',
      satisfied_milestones: [],
      missing_invariants: ['Narrative reasoning governed by live backend kernel.'],
      unresolved_narrative_count: 0,
      unresolved_causal_count: 0,
      unresolved_temporal_count: 0,
      production_decisions_count: 0,
      blocking_dependencies: [],
      assessment_notes: 'Fallback preservation mode: Narrative completion certified exclusively by live ForgeJudge.',
      assessed_by: 'ForgeJudge::PreservedStateShell',
      assessed_at: new Date().toISOString()
    };
  },

  assessCompletion: (storyId: string): ForgeCompletionAssessment => {
    return storyForgeFallback.getCompletion(storyId);
  },

  getIntelligence: (storyId: string): IntelligenceProjection => {
    const state: StoryState = storyForgeFallback.getStoryState(storyId);
    const charNames = Object.values(state.characters || {}).map(c => c.name);

    return {
      story_id: storyId,
      state_version: state.state_version,
      current_milestone: null,
      target_milestone: 'FORGE_COMPLETE',
      satisfied_milestones: [],
      readiness_status: 'NOT_READY',
      core_understanding: {
        title: state.title,
        logline: state.logline || null,
        protagonists: charNames.slice(0, 1),
        antagonists: [],
        supporting_characters: charNames.slice(1),
        chronology_anchors_count: 0,
        narrative_plants_count: state.plants?.length || 0,
        production_decisions_count: 0
      },
      strengths: [],
      unresolved_risks: [],
      missing_invariants: [],
      next_needed_decisions: [],
      total_dependencies: 0,
      resolved_dependencies_count: 0
    };
  },

  /**
   * Offline input handler:
   * 1. Preserves StoryState without mutating canon.
   * 2. Buffers creator input in pending queue for replay when backend reconnects.
   * 3. Does NOT invent narrative questions or transitions.
   */
  submitInput: (sessionId: string, payload: SubmitInputPayload): ForgeCycleResult => {
    const session = safeGetItem(STORAGE_KEYS.SESSION_PREFIX + sessionId);
    const storyId = session?.story_id || 'story_default';
    const currentState: StoryState = storyForgeFallback.getStoryState(storyId);
    const responseText = payload.creator_response || payload.creator_input || '';

    // Buffer pending input for replay upon backend reconnection
    const pendingKey = STORAGE_KEYS.PENDING_INPUTS_PREFIX + sessionId;
    const existingPending: Array<{ payload: SubmitInputPayload; timestamp: string }> = safeGetItem(pendingKey) || [];
    existingPending.push({ payload, timestamp: new Date().toISOString() });
    safeSetItem(pendingKey, existingPending);

    // Maintain current state version and action — zero canonical mutations invented
    const existingAction = session?.current_action;
    const preservedAction: CurrentAction = {
      session_id: sessionId,
      story_id: storyId,
      state_version: currentState.state_version,
      action: existingAction?.action || 'ASK',
      skill: existingAction?.skill || 'FORGE_JUDGE',
      question: null, // Fallback does NOT invent narrative questions
      active_dependency_key: existingAction?.active_dependency_key || null,
      active_dependency_description: existingAction?.active_dependency_description || null,
      unresolved_dependencies_count: existingAction?.unresolved_dependencies_count || 0,
      is_paused: false,
      requires_creator: true
    };

    safeSetItem(STORAGE_KEYS.SESSION_PREFIX + sessionId, {
      ...session,
      current_action: preservedAction,
      has_pending_inputs: true,
      is_degraded: true
    });

    const placeholderTransition: ForgeTransition = {
      transition_id: `trans_buffered_${Date.now()}`,
      story_id: storyId,
      trace_id: `trc_buffered_${Date.now()}`,
      sequence: currentState.state_version,
      creator_input: responseText,
      interpretation: 'Creator input buffered offline awaiting backend Forge reconciliation.',
      skill: 'FORGE_JUDGE',
      active_dependency_id: null,
      authority_mode: 'ASK',
      creator_response: responseText,
      state_changes: [], // Zero canonical mutations created by fallback
      consequences: [],
      validation_status: 'BUFFERED_OFFLINE',
      validation_errors: [],
      provenance: {
        creator_id: 'creator_current',
        session_id: sessionId,
        adapter_name: 'StoryForgeOfflineBuffer',
        adapter_version: '1.0.0-buffer',
        confidence: 1.0,
        assumptions: [],
        evidence: ['Input buffered offline for Forge reconciliation'],
        timestamp: new Date().toISOString(),
        state_version_before: currentState.state_version,
        state_version_after: currentState.state_version
      },
      created_at: new Date().toISOString()
    };

    return {
      story_id: storyId,
      session_id: sessionId,
      state_version: currentState.state_version,
      action: preservedAction.action,
      active_question: null, // Does NOT invent narrative question
      transition: placeholderTransition,
      current_state: currentState, // StoryState preserved without hallucinated canon
      unresolved_dependencies_count: preservedAction.unresolved_dependencies_count
    };
  },

  /**
   * Pending input buffer management for replay upon backend reconnection.
   */
  getPendingInputs: (sessionId: string): Array<{ payload: SubmitInputPayload; timestamp: string }> => {
    return safeGetItem(STORAGE_KEYS.PENDING_INPUTS_PREFIX + sessionId) || [];
  },

  clearPendingInputs: (sessionId: string): void => {
    safeSetItem(STORAGE_KEYS.PENDING_INPUTS_PREFIX + sessionId, []);
  }
};
