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

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || '/api';

const forgeClient = axios.create({
  baseURL: `${API_BASE}/v1/forge`,
  timeout: 60000, // 60s for LLM reasoning cycles
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
    const res = await forgeClient.post('/stories', payload);
    return res.data;
  },

  listStories: async (): Promise<StorySummary[]> => {
    const res = await forgeClient.get('/stories');
    return res.data;
  },

  getStorySummary: async (storyId: string): Promise<StorySummary> => {
    const res = await forgeClient.get(`/stories/${storyId}`);
    return res.data;
  },

  getStoryState: async (storyId: string): Promise<StoryState> => {
    const res = await forgeClient.get(`/stories/${storyId}/state`);
    return res.data;
  },

  getDependencies: async (storyId: string): Promise<Dependency[]> => {
    const res = await forgeClient.get(`/stories/${storyId}/dependencies`);
    return res.data;
  },

  getTrace: async (storyId: string): Promise<ForgeTransition[]> => {
    const res = await forgeClient.get(`/stories/${storyId}/trace`);
    return res.data;
  },

  getCompletion: async (storyId: string): Promise<ForgeCompletionAssessment> => {
    const res = await forgeClient.get(`/stories/${storyId}/completion`);
    return res.data;
  },

  assessCompletion: async (storyId: string): Promise<ForgeCompletionAssessment> => {
    const res = await forgeClient.post(`/stories/${storyId}/completion-assessment`);
    return res.data;
  },

  getIntelligence: async (storyId: string): Promise<IntelligenceProjection> => {
    const res = await forgeClient.get(`/stories/${storyId}/intelligence`);
    return res.data;
  },

  // Session & Input Lifecycle
  startSession: async (storyId: string, payload: StartSessionPayload): Promise<any> => {
    const res = await forgeClient.post(`/stories/${storyId}/sessions`, payload);
    return res.data;
  },

  getSessionStatus: async (sessionId: string): Promise<any> => {
    const res = await forgeClient.get(`/sessions/${sessionId}`);
    return res.data;
  },

  getCurrentAction: async (sessionId: string): Promise<CurrentAction> => {
    const res = await forgeClient.get(`/sessions/${sessionId}/current`);
    return res.data;
  },

  submitInput: async (sessionId: string, payload: SubmitInputPayload): Promise<ForgeCycleResult> => {
    const res = await forgeClient.post(`/sessions/${sessionId}/input`, payload);
    return res.data;
  },
};
