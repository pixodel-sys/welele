import axios from 'axios';
import {
  StoryDraft,
  StoryReviewDiagnostic,
  PitchSubmitPayload,
  CreatorSubmission
} from '../types/storyReview';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || '/api';

const reviewClient = axios.create({
  baseURL: `${API_BASE}/v1/review`,
  timeout: 35000,
  headers: {
    'Content-Type': 'application/json',
  },
});

reviewClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('welele_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const storyReviewApi = {
  // Persistent Drafts
  getDrafts: async (creatorId: string = 'creator_zola'): Promise<StoryDraft[]> => {
    const res = await reviewClient.get('/drafts', { params: { creator_id: creatorId } });
    return res.data;
  },

  getDraft: async (draftId: string): Promise<StoryDraft> => {
    const res = await reviewClient.get(`/drafts/${draftId}`);
    return res.data;
  },

  saveDraft: async (draft: StoryDraft): Promise<{ success: boolean; draft: StoryDraft }> => {
    const res = await reviewClient.post('/drafts', draft);
    return res.data;
  },

  // Creator Diagnostic Review
  diagnoseStory: async (draft: StoryDraft): Promise<StoryReviewDiagnostic> => {
    const res = await reviewClient.post('/diagnose', draft);
    return res.data;
  },

  // IP Pipeline Submission
  submitPitch: async (payload: PitchSubmitPayload): Promise<CreatorSubmission> => {
    const res = await reviewClient.post('/submit-pitch', payload);
    return res.data;
  },

  getSubmissions: async (creatorId?: string): Promise<CreatorSubmission[]> => {
    const res = await reviewClient.get('/submissions', { params: { creator_id: creatorId } });
    return res.data;
  },

  getSubmission: async (submissionId: string): Promise<CreatorSubmission> => {
    const res = await reviewClient.get(`/submissions/${submissionId}`);
    return res.data;
  }
};
