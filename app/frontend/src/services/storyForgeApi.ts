import axios from 'axios';
import {
  StoryState,
  StorySummary,
  CurrentAction,
  ForgeCycleResult,
  Dependency,
  ForgeTransition,
  ForgeCompletionAssessment,
  IntelligenceProjection
} from '../types/storyForge';
import { storyForgeFallback } from './storyForgeFallback';

const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) || ((globalThis as any).process?.env?.VITE_API_BASE_URL) || '/api';

const forgeClient = axios.create({
  baseURL: `${API_BASE}/v1/forge`,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

forgeClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('welele_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface CreateStoryPayload {
  story_id?: string;
  title: string;
  owner_id: string;
  digital_ip_id?: string;
  logline?: string;
  primary_language?: string;
}

export interface StartSessionPayload {
  creator_id: string;
  session_id?: string;
  initial_premise?: string;
  story_document_context?: string;
  creative_objective?: string;
  production_objective?: string;
}

export interface SubmitInputPayload {
  creator_input?: string;
  creator_response?: string;
  proposal_action?: 'ACCEPT' | 'REJECT' | 'MODIFY';
  event_headline?: string;
  event_description?: string;
  participants?: string[];
}

export const storyForgeApi = {
  // Story Lifecycle
  createStory: async (payload: CreateStoryPayload): Promise<StoryState> => {
    try {
      const res = await forgeClient.post('/stories', payload);
      if (res.data) {
        storyForgeFallback.cacheStoryState(res.data);
      }
      return res.data;
    } catch (err) {
      console.warn('[storyForgeApi] Backend unavailable, engaging resilient edge staging kernel for story creation:', err);
      return storyForgeFallback.createStory(payload);
    }
  },

  listStories: async (): Promise<StorySummary[]> => {
    try {
      const res = await forgeClient.get('/stories');
      if (Array.isArray(res.data)) {
        storyForgeFallback.syncBackendStories(res.data);
        return res.data;
      }
    } catch (err) {
      console.warn('[storyForgeApi] listStories falling back to edge store:', err);
    }
    const fallbackList = storyForgeFallback.listStories();
    // Return meaningful stories first; filter out empty untitled duplicates if any titled story exists
    const hasNamed = fallbackList.some(s => s.title && s.title !== 'Untitled Story' && s.title !== 'Story');
    if (hasNamed) {
      return fallbackList.filter(s => (s.title && s.title !== 'Untitled Story' && s.title !== 'Story') || !!s.logline);
    }
    return fallbackList;
  },

  deleteStory: async (storyId: string): Promise<boolean> => {
    try {
      await forgeClient.delete(`/stories/${storyId}`);
    } catch (e) {
      console.warn('[storyForgeApi] Backend delete failed or unavailable:', e);
    }
    return storyForgeFallback.deleteStory(storyId);
  },

  clearUntitledDrafts: async (): Promise<number> => {
    try {
      await forgeClient.delete('/stories/cleanup/untitled');
    } catch {
      // ignore
    }
    return storyForgeFallback.clearUntitledDrafts();
  },

  getStorySummary: async (storyId: string): Promise<StorySummary> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}`);
      return res.data;
    } catch {
      return storyForgeFallback.getStorySummary(storyId);
    }
  },

  getStoryState: async (storyId: string): Promise<StoryState> => {
    if (!storyId || !storyId.trim()) {
      return storyForgeFallback.getStoryState(storyId || '');
    }
    try {
      const res = await forgeClient.get(`/stories/${storyId}/state`);
      if (res.data) {
        storyForgeFallback.cacheStoryState(res.data);
      }
      return res.data;
    } catch {
      return storyForgeFallback.getStoryState(storyId);
    }
  },

  getDependencies: async (storyId: string): Promise<Dependency[]> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}/dependencies`);
      return res.data;
    } catch {
      return storyForgeFallback.getDependencies(storyId);
    }
  },

  getTrace: async (storyId: string): Promise<ForgeTransition[]> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}/trace`);
      return res.data;
    } catch {
      return storyForgeFallback.getTrace(storyId);
    }
  },

  getCompletion: async (storyId: string): Promise<ForgeCompletionAssessment> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}/completion`);
      return res.data;
    } catch {
      return storyForgeFallback.getCompletion(storyId);
    }
  },

  assessCompletion: async (storyId: string): Promise<ForgeCompletionAssessment> => {
    try {
      const res = await forgeClient.post(`/stories/${storyId}/completion-assessment`);
      return res.data;
    } catch {
      return storyForgeFallback.assessCompletion(storyId);
    }
  },

  getIntelligence: async (storyId: string): Promise<IntelligenceProjection> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}/intelligence`);
      return res.data;
    } catch {
      return storyForgeFallback.getIntelligence(storyId);
    }
  },

  getPackage: async (storyId: string): Promise<any> => {
    try {
      const res = await forgeClient.get(`/stories/${storyId}/package`);
      return res.data;
    } catch (err) {
      console.warn('[storyForgeApi] getPackage error:', err);
      throw err;
    }
  },

  // Session & Input Lifecycle
  startSession: async (storyId: string, payload: StartSessionPayload): Promise<any> => {
    const clientStartTime = performance.now();
    try {
      const res = await forgeClient.post(`/stories/${storyId}/sessions`, payload);
      const clientEndTime = performance.now();
      const roundTripMs = Math.round(clientEndTime - clientStartTime);

      const ingestionMs = parseFloat(res.headers?.['x-forge-ingestion-ms'] || '0') || 0;
      const llmMs = parseFloat(res.headers?.['x-forge-llm-ms'] || '0') || 0;
      const reconciliationMs = parseFloat(res.headers?.['x-forge-reconciliation-ms'] || '0') || 0;
      const backendTotalMs = parseFloat(res.headers?.['x-forge-backend-total-ms'] || '0') || (ingestionMs + llmMs + reconciliationMs);
      const networkTransportMs = Math.max(0, Math.round(roundTripMs - backendTotalMs));

      if (res.data && typeof res.data === 'object') {
        res.data._timingBreakdown = {
          ingestionMs,
          llmMs,
          reconciliationMs,
          backendTotalMs,
          networkTransportMs,
          roundTripMs,
        };
      }
      return res.data;
    } catch (err) {
      console.warn('[storyForgeApi] startSession falling back to edge store:', err);
      return storyForgeFallback.startSession(storyId, payload);
    }
  },

  getSessionStatus: async (sessionId: string): Promise<any> => {
    try {
      const res = await forgeClient.get(`/sessions/${sessionId}`);
      return res.data;
    } catch {
      return storyForgeFallback.getSessionStatus(sessionId);
    }
  },

  getCurrentAction: async (sessionId: string): Promise<CurrentAction> => {
    if (!sessionId || !sessionId.trim()) {
      return storyForgeFallback.getCurrentAction(sessionId || '');
    }
    try {
      const res = await forgeClient.get(`/sessions/${sessionId}/current`);
      return res.data;
    } catch {
      return storyForgeFallback.getCurrentAction(sessionId);
    }
  },

  submitInput: async (sessionId: string, payload: SubmitInputPayload): Promise<ForgeCycleResult> => {
    try {
      // If there are buffered offline inputs from degraded mode, replay them first in order
      const pending = storyForgeFallback.getPendingInputs(sessionId);
      if (pending.length > 0) {
        console.log(`[storyForgeApi] Replaying ${pending.length} buffered offline inputs to backend Forge...`);
        for (const item of pending) {
          await forgeClient.post(`/sessions/${sessionId}/input`, item.payload);
        }
        storyForgeFallback.clearPendingInputs(sessionId);
      }

      const res = await forgeClient.post(`/sessions/${sessionId}/input`, payload);
      return res.data;
    } catch (err) {
      console.warn('[storyForgeApi] submitInput falling back to edge store:', err);
      return storyForgeFallback.submitInput(sessionId, payload);
    }
  },

  replayPendingInputs: async (sessionId: string): Promise<ForgeCycleResult | null> => {
    const pending = storyForgeFallback.getPendingInputs(sessionId);
    if (pending.length === 0) return null;

    let lastResult: ForgeCycleResult | null = null;
    for (const item of pending) {
      const res = await forgeClient.post(`/sessions/${sessionId}/input`, item.payload);
      lastResult = res.data;
    }
    storyForgeFallback.clearPendingInputs(sessionId);
    return lastResult;
  },
};
