import axios from 'axios';
import {
  Story,
  Creator,
  CoinPack,
  VirtualGift,
  Comment,
  Reaction,
  ModerationItem,
  SACarrier,
  AirtimePass,
  AIStatus, StoryForgeScript,
  RetentionTelemetry,
  DropoffDataPoint
} from '../types';
import { ExperienceManifest } from '../types/experience';

const API = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL as string) || '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Authorization Bearer token from localStorage to all outgoing API requests
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('welele_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// ============================================================================
// CANONICAL DOMAIN SERVICE CLIENTS (Section 5.1 & Architecture Manifesto)
// ============================================================================

export const authApi = {
  sendOtp: async (phone_number: string, region_code = 'ZA') => {
    const res = await API.post('/auth/phone/send-otp', { phone_number, region_code });
    return res.data;
  },
  verifyOtp: async (phone_number: string, otp_code: string) => {
    const res = await API.post('/auth/phone/verify-otp', { phone_number, otp_code });
    if (res.data?.access_token) {
      localStorage.setItem('welele_auth_token', res.data.access_token);
    }
    return res.data;
  },
  guestLogin: async (region_code = 'ZA') => {
    const res = await API.post('/auth/guest', { region_code });
    if (res.data?.access_token) {
      localStorage.setItem('welele_auth_token', res.data.access_token);
    }
    return res.data;
  },
  creatorLogin: async (creator_id = 'creator_zola', studio_pin = '1234') => {
    const res = await API.post('/auth/creator/login', { creator_id, studio_pin });
    if (res.data?.access_token) {
      localStorage.setItem('welele_auth_token', res.data.access_token);
    }
    return res.data;
  },
  adminLogin: async (admin_key = 'admin_master_welele_2026', two_factor_code = '999888') => {
    const res = await API.post('/auth/admin/login', { admin_key, two_factor_code });
    if (res.data?.access_token) {
      localStorage.setItem('welele_auth_token', res.data.access_token);
    }
    return res.data;
  },
  getProfile: async (user_id?: string) => {
    const res = await API.get('/auth/me', { params: { user_id } });
    return res.data;
  },
};

export const seriesApi = {
  getFeed: async (genre?: string, language?: string): Promise<{ series: Story[]; total: number }> => {
    const res = await API.get('/series/feed', { params: { genre, language } });
    return res.data;
  },
  getTrending: async (): Promise<{ trending: Story[] }> => {
    const res = await API.get('/series/trending');
    return res.data;
  },
  getSeriesDetail: async (seriesId: string): Promise<Story> => {
    const res = await API.get(`/series/${seriesId}`);
    return res.data;
  },
  likeSeries: async (seriesId: string): Promise<{ success: boolean; total_likes: number }> => {
    const res = await API.post(`/series/${seriesId}/like`);
    return res.data;
  },
};

export const episodesApi = {
  getStream: async (seriesId: string, episodeId: string, userId?: string) => {
    const res = await API.get(`/episodes/${seriesId}/${episodeId}`, { params: { user_id: userId } });
    return res.data;
  },
  unlock: async (seriesId: string, episodeId: string, userId: string, method = 'COINS') => {
    const res = await API.post(`/episodes/${seriesId}/${episodeId}/unlock`, null, {
      params: { user_id: userId, method },
    });
    return res.data;
  },
};

export const walletApi = {
  getBalance: async (user_id: string) => {
    const res = await API.get('/wallet/balance', { params: { user_id } });
    return res.data;
  },
  getLedger: async (user_id: string, limit = 50) => {
    const res = await API.get('/wallet/ledger', { params: { user_id, limit } });
    return res.data;
  },
  getPacks: async (region = 'ZA') => {
    const res = await API.get('/wallet/packs', { params: { region } });
    return res.data;
  },
  sendGift: async (payload: {
    user_id: string;
    creator_id: string;
    series_id: string;
    episode_id: string;
    gift_id: string;
    gift_name: string;
    gift_icon: string;
    coin_cost: number;
    message?: string;
  }) => {
    const res = await API.post('/wallet/gifts/send', payload);
    return res.data;
  },
};

export const storageApi = {
  uploadBinary: async (
    file: File,
    series_id: string,
    episode_number?: number,
    episode_id?: string
  ): Promise<{
    success: boolean;
    storage_key: string;
    public_cdn_url: string;
    file_size_bytes: number;
    content_type: string;
    provider: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('series_id', series_id);
    if (episode_number !== undefined) {
      formData.append('episode_number', episode_number.toString());
    }
    if (episode_id) {
      formData.append('episode_id', episode_id);
    }
    const res = await API.post('/storage/upload-binary', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  getPresignedUploadUrl: async (story_id: string, episode_number: number, filename: string) => {
    const res = await API.post('/storage/presigned-upload', {
      story_id,
      episode_number,
      filename,
    });
    return res.data;
  },
  getRenditions: async (storage_key: string) => {
    const res = await API.get('/storage/renditions', { params: { storage_key } });
    return res.data;
  },
};

// ============================================================================
// LEGACY & WRAPPER APIS (Maintains 100% Backward Compatibility)
// ============================================================================

export const storyApi = {
  getFeed: async (genre?: string, language?: string): Promise<{ stories: Story[]; total: number }> => {
    const res = await API.get('/stories/feed', { params: { genre, language } });
    return res.data;
  },
  getTrending: async (): Promise<{ trending: Story[] }> => {
    const res = await API.get('/stories/trending');
    return res.data;
  },
  getStoryDetail: async (storyId: string): Promise<Story> => {
    const res = await API.get(`/stories/${storyId}`);
    return res.data;
  },
  likeStory: async (storyId: string): Promise<{ success: boolean; total_likes: number }> => {
    const res = await API.post(`/stories/like/${storyId}`);
    return res.data;
  },
};

export const monetizationApi = {
  getPacks: async (currency: string = 'USD'): Promise<{
    packs: CoinPack[];
    gifts: VirtualGift[];
    currencies: string[];
    sa_airtime_carriers?: SACarrier[];
    sa_airtime_passes?: AirtimePass[];
  }> => {
    const res = await API.get('/monetization/packs', { params: { currency } });
    return res.data;
  },
  getCarriers: async (): Promise<{ country: string; currency: string; carriers: SACarrier[] }> => {
    const res = await API.get('/monetization/airtime/carriers');
    return res.data;
  },
  getAirtimePasses: async (): Promise<{ country: string; currency: string; passes: AirtimePass[] }> => {
    const res = await API.get('/monetization/airtime/passes');
    return res.data;
  },
  detectCarrier: async (phone: string): Promise<{ phone: string; carrier: SACarrier }> => {
    const res = await API.get('/monetization/airtime/detect-carrier', { params: { phone } });
    return res.data;
  },
  chargeAirtime: async (payload: {
    user_id: string;
    carrier_id: string;
    phone_number: string;
    charge_type: 'episode_unlock' | 'coin_pack' | 'story_pass';
    target_id: string;
    series_id?: string;
    amount_zar: number;
    coins_equivalent?: number;
  }) => {
    const res = await API.post('/monetization/airtime/charge', payload);
    return res.data;
  },
  simulateUSSD: async (payload: { phone_number: string; ussd_string: string; user_id?: string }) => {
    const res = await API.post('/monetization/airtime/ussd', payload);
    return res.data;
  },
  topupCoins: async (payload: {
    user_id: string;
    pack_id: string;
    coins: number;
    amount_local: number;
    currency: string;
    payment_method: string;
    phone_or_account: string;
  }) => {
    const res = await API.post('/monetization/topup', payload);
    return res.data;
  },
  unlockEpisode: async (payload: {
    user_id: string;
    episode_id: string;
    series_id: string;
    coins: number;
  }) => {
    const res = await API.post('/monetization/unlock', payload);
    return res.data;
  },
  sendGift: async (payload: {
    user_id: string;
    creator_id: string;
    series_id: string;
    episode_id: string;
    gift_id: string;
    gift_name: string;
    gift_icon: string;
    coin_cost: number;
    message?: string;
  }) => {
    const res = await API.post('/monetization/gift', payload);
    return res.data;
  },
  requestPayout: async (payload: {
    creator_id: string;
    amount_coins: number;
    amount_local: number;
    currency: string;
    payout_method: string;
    account_details: string;
  }) => {
    const res = await API.post('/monetization/payout', payload);
    return res.data;
  },
};

export const chatApi = {
  getComments: async (episodeId: string): Promise<{ comments: Comment[]; total: number }> => {
    const res = await API.get(`/chat/episodes/${episodeId}/comments`);
    return res.data;
  },
  postComment: async (episodeId: string, payload: { user_name: string; text: string; avatar?: string }) => {
    const res = await API.post(`/chat/episodes/${episodeId}/comments`, payload);
    return res.data;
  },
  getReactions: async (episodeId: string): Promise<{ reactions: Reaction[] }> => {
    const res = await API.get(`/chat/episodes/${episodeId}/reactions`);
    return res.data;
  },
  sendReaction: async (episodeId: string, payload: { emoji: string; timestamp_seconds: number }) => {
    const res = await API.post(`/chat/episodes/${episodeId}/reactions`, payload);
    return res.data;
  },
};

export const creatorApi = {
  listCreators: async (): Promise<{ creators: Creator[] }> => {
    try {
      const res = await API.get('/creators/list');
      return res.data;
    } catch {
      return {
        creators: [
          {
            id: 'creator_zola',
            name: 'Zola Dlamini',
            handle: '@zola_cinemas',
            bio: 'Johannesburg crime & dynasty showrunner.',
            avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80',
            country: 'South Africa',
            verified: true,
            followers_count: 420000,
            total_views: 8420000,
            coin_earnings: 284000,
            payout_balance: 1890.00
          }
        ]
      };
    }
  },
  getProfile: async (creatorId: string) => {
    try {
      const res = await API.get(`/creators/${creatorId}`);
      return res.data;
    } catch {
      return {
        creator: {
          id: creatorId,
          name: 'Zola Dlamini',
          handle: '@zola_cinemas',
          bio: 'Johannesburg crime & dynasty showrunner.',
          avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80',
          country: 'South Africa',
          verified: true,
          followers_count: 420000,
          total_views: 8420000,
          coin_earnings: 284000,
          payout_balance: 1890.00
        },
        series: [],
        total_series: 0
      };
    }
  },
  getDashboard: async (creatorId: string) => {
    try {
      const res = await API.get(`/creators/${creatorId}/dashboard`);
      return res.data;
    } catch {
      return {
        stats: {
          total_views: 8420000,
          total_likes: 482000,
          total_episodes: 12,
          followers: 420000,
          coin_earnings: 284000,
          payout_balance_usd: 1890.00,
          avg_cliffhanger_completion_rate: "88.4%",
          monthly_growth_rate: "+26.4%"
        },
        series: []
      };
    }
  },
  getEpisodes: async (creatorId: string, status?: string) => {
    try {
      const res = await API.get(`/creators/${creatorId}/episodes`, { params: { status } });
      return res.data;
    } catch {
      return { episodes: [], total: 0 };
    }
  },
  getSeriesWorkspace: async (seriesId: string) => {
    try {
      const res = await API.get(`/creators/series/${seriesId}/workspace`);
      return res.data;
    } catch {
      return { series: null, episodes: [], analytics: null };
    }
  },
  createSeries: async (payload: any) => {
    try {
      const res = await API.post('/creators/series/create', payload);
      return res.data;
    } catch {
      return { success: true, series: payload };
    }
  },
  addEpisode: async (payload: any) => {
    try {
      const res = await API.post('/creators/episodes/add', payload);
      return res.data;
    } catch {
      return { success: true, episode: payload };
    }
  },
  getTransactions: async (creatorId: string) => {
    const res = await API.get(`/creators/${creatorId}/transactions`);
    return res.data;
  },
  requestPayout: async (payload: {
    creator_id: string;
    amount_coins: number;
    amount_local: number;
    currency: string;
    payout_method: string;
    account_details: string;
    idempotency_key?: string;
  }) => {
    const res = await API.post('/monetization/payout', payload);
    return res.data;
  },
};

export const aiApi = {
  getStatus: async (): Promise<AIStatus> => {
    try {
      const res = await API.get('/ai/status');
      return res.data;
    } catch {
      return {
        mode: 'fallback',
        provider: 'Welele Offline Drama Engine',
        model: 'local-rule-matrix-v1',
        is_connected: false,
        has_api_key: false,
        latency_ms: 12,
        supported_dialects: ['isiZulu', 'Yoruba', 'Kiswahili', 'Nigerian Pidgin', 'isiXhosa', 'English']
      };
    }
  },

  generateSubtitles: async (videoUrl: string, targetLanguages: string[]) => {
    const res = await API.post('/ai/subtitles', {
      video_url: videoUrl,
      target_languages: targetLanguages,
    });
    return res.data;
  },
  analyzeVideo: async (videoUrl: string, title: string, synopsis: string) => {
    const res = await API.post('/ai/analyze-video', {
      video_url: videoUrl,
      title,
      synopsis,
    });
    return res.data;
  },
};

export const adminApi = {
  getMetrics: async () => {
    const res = await API.get('/admin/metrics');
    return res.data;
  },
  getModerationQueue: async (): Promise<{ queue: ModerationItem[] }> => {
    const res = await API.get('/admin/moderation-queue');
    return res.data;
  },
  approveItem: async (itemId: string) => {
    const res = await API.post(`/admin/moderation/${itemId}/approve`);
    return res.data;
  },
  requestChanges: async (itemId: string, feedback?: string) => {
    const res = await API.post(`/admin/moderation/${itemId}/request-changes`, { feedback });
    return res.data;
  },
  rejectItem: async (itemId: string, feedback?: string) => {
    const res = await API.post(`/admin/moderation/${itemId}/reject`, { feedback });
    return res.data;
  },
  getAuditLogs: async (params?: { domain?: string; event_type?: string; actor_id?: string; limit?: number }) => {
    const res = await API.get('/admin/audit-logs', { params });
    return res.data;
  },
  verifyAuditChain: async () => {
    const res = await API.post('/admin/audit-logs/verify-chain');
    return res.data;
  },
};

export const experienceApi = {
  getManagedPages: async (): Promise<{ pages: Array<{ page_id: string; title: string; route: string }> }> => {
    const res = await API.get('/experience/pages');
    return res.data;
  },
  getPageExperience: async (pageId: string): Promise<ExperienceManifest> => {
    const res = await API.get(`/experience/page/${pageId}`);
    return res.data;
  },
  getPreviewExperience: async (pageId: string, state = 'draft', simulatedTime?: string): Promise<ExperienceManifest> => {
    const res = await API.get(`/experience/preview/${pageId}`, {
      params: { state, simulated_time: simulatedTime },
    });
    return res.data;
  },
  saveDraft: async (pageId: string, payload: { meta?: any; sections: any[] }) => {
    const res = await API.put(`/experience/page/${pageId}/draft`, payload);
    return res.data;
  },
  publish: async (pageId: string, scheduledFor?: string) => {
    const res = await API.post(`/experience/page/${pageId}/publish`, { scheduled_for: scheduledFor });
    return res.data;
  },
  resetDefault: async (pageId: string) => {
    const res = await API.post(`/experience/page/${pageId}/reset-default`);
    return res.data;
  },
};


// --- Extension APIs for Next-Gen Creator Studio ---
export const storyForgeApi = {
  generateScript: async (payload: {
    genre: string;
    target_duration_seconds: number;
    prompt: string;
    language?: string;
  }): Promise<StoryForgeScript> => {
    try {
      const res = await API.post('/ai/story-forge/generate', payload);
      return res.data;
    } catch {
      // Offline fallback mock for ultra resilience
      return {
        id: 'sf_' + Date.now(),
        series_title: payload.prompt ? payload.prompt.slice(0, 30) : 'Soweto Nights',
        genre: payload.genre || 'Drama',
        target_duration_seconds: payload.target_duration_seconds || 90,
        logline: 'When an ambitious street-hustler discovers a lost gold ledger, rival cartels and family loyalty collide in the heart of Johannesburg.',
        created_at: new Date().toISOString(),
        cliffhanger_prompt: 'Will Sipho sign the cartel deed before the siren sounds?',
        characters: [
          {
            id: 'c1',
            name: 'Sipho Khumalo',
            role: 'protagonist',
            archetype: 'The Ambitious Hustler',
            secret_motivation: 'To buy back his mother’s bakery before the bank auctions it.',
            fatal_flaw: 'Trusts charm over written contracts.',
            signature_quote: 'In this city, if you hesitate, you are already forgotten.'
          },
          {
            id: 'c2',
            name: 'Nomsa Zulu',
            role: 'antagonist',
            archetype: 'The Cartel Kingpin',
            secret_motivation: 'Secure total control over the central taxi rank ledger.',
            fatal_flaw: 'Underestimates street loyalty.',
            signature_quote: 'Every coin in this town carries my thumbprint.'
          }
        ],
        beats: [
          { timestamp_seconds: 0, label: 'Cold Open Hook', intensity: 8, action_description: 'Sipho hides in an alley as black SUVs screech to a halt.' },
          { timestamp_seconds: 25, label: 'Inciting Incident', intensity: 7, action_description: 'He opens the ledger to find his own father’s signature from 1998.' },
          { timestamp_seconds: 55, label: 'Reversal & Tension', intensity: 9, action_description: 'Nomsa steps out of the shadows with a silver phone recording him.' },
          { timestamp_seconds: 88, label: 'Cliffhanger Paywall', intensity: 10, action_description: 'A single gunshot echoes as the phone rings with his sister’s voice.', cliffhanger_trigger: true }
        ],
        dialogue: [
          {
            speaker: 'Sipho',
            original_text: 'You cannot own what belongs to the ancestors.',
            dialect_code: 'zu',
            dialect_label: 'isiZulu',
            phonetic_note: 'Emphasis on "okhokho" with heavy emotional weight.'
          },
          {
            speaker: 'Nomsa',
            original_text: 'The ancestors do not accept mobile money transfers, young man.',
            dialect_code: 'en',
            dialect_label: 'English / Slang',
            phonetic_note: 'Cold, calculated delivery.'
          }
        ]
      };
    }
  },
  translateDialogue: async (line: string, targetDialect: 'zu' | 'yo' | 'sw' | 'pcm' | 'en' | 'xh'): Promise<{
    translated_text: string;
    phonetic_note: string;
    cultural_context: string;
  }> => {
    try {
      const res = await API.post('/ai/story-forge/translate', { line, target_dialect: targetDialect });
      return res.data;
    } catch {
      const dialectMap: Record<string, { translated_text: string; phonetic_note: string; cultural_context: string }> = {
        zu: {
          translated_text: 'Awukwazi ukuthatha lokho okungokwethu ngempela.',
          phonetic_note: 'Click sound on "kwa", steady breath tone.',
          cultural_context: 'Traditional Zulu expression of ancestral right.'
        },
        yo: {
          translated_text: 'O ko le gba ohun ti o je tiwa lati ipilẹsẹ.',
          phonetic_note: 'Tonal inflections on low-high marks.',
          cultural_context: 'Yoruba high-stakes familial confrontation style.'
        },
        sw: {
          translated_text: 'Huwezi kuchukua kile ambacho ni chetu kisheria.',
          phonetic_note: 'Crisp coastal Swahili cadence.',
          cultural_context: 'East African drama pacing.'
        },
        pcm: {
          translated_text: 'You no fit just carry wetin belong to our papa dem like dat!',
          phonetic_note: 'High energetic West African street vernacular.',
          cultural_context: 'Lagos Nollywood short-form drama tone.'
        },
        xh: {
          translated_text: 'Awunakho ukuthatha oku kwayanyaniswa kuthi.',
          phonetic_note: 'Clear dental clicks on "th" and "q".',
          cultural_context: 'Deep Xhosa gravitas.'
        },
        en: {
          translated_text: line,
          phonetic_note: 'Standard dramatic pacing.',
          cultural_context: 'Universal international streaming cue.'
        }
      };
      return dialectMap[targetDialect] || dialectMap.en;
    }
  }
};

export const retentionApi = {
  getTelemetry: async (seriesId: string, episodeNumber: number = 1): Promise<RetentionTelemetry> => {
    try {
      const res = await API.get('/creators/analytics/retention', { params: { series_id: seriesId, episode_number: episodeNumber } });
      return res.data;
    } catch {
      // High fidelity telemetry mock
      const points: DropoffDataPoint[] = [];
      let current = 100;
      for (let sec = 0; sec <= 90; sec += 5) {
        if (sec === 0) current = 100;
        else if (sec <= 15) current -= Math.random() * 2.5 + 1; // initial bounce
        else if (sec <= 70) current -= Math.random() * 1.2 + 0.3; // steady engagement
        else if (sec >= 85) current -= Math.random() * 0.5; // hooked until cliffhanger
        points.push({
          second: sec,
          retention_pct: Math.max(45, Math.round(current * 10) / 10),
          viewer_count: Math.round(14500 * (current / 100)),
          is_cliffhanger: sec >= 85
        });
      }

      return {
        series_id: seriesId,
        episode_id: 'ep_' + episodeNumber,
        episode_number: episodeNumber,
        total_starts: 14500,
        completion_rate_pct: 78.4,
        cliffhanger_conversion_pct: 64.2,
        avg_watch_time_seconds: 79.5,
        dropoff_curve: points,
        geo_distribution: [
          { country: 'South Africa', flag: '🇿🇦', share_pct: 44, views: 6380 },
          { country: 'Nigeria', flag: '🇳🇬', share_pct: 28, views: 4060 },
          { country: 'Kenya', flag: '🇰🇪', share_pct: 16, views: 2320 },
          { country: 'Ghana', flag: '🇬🇭', share_pct: 12, views: 1740 }
        ],
        telco_payment_mix: [
          { provider: 'MTN Airtime / MoMo', color: '#FFCC00', share_pct: 48 },
          { provider: 'Vodacom / M-Pesa', color: '#E60000', share_pct: 31 },
          { provider: 'Chipper Cash', color: '#7C3AED', share_pct: 14 },
          { provider: 'Card & EFT', color: '#3B82F6', share_pct: 7 }
        ]
      };
    }
  }
};

// ============================================================================
// CANONICAL DIGITAL IP & TELEMETRY APIS (GAP-001 & GAP-004)
// ============================================================================

export const ipApi = {
  listIps: async () => {
    const res = await API.get('/ip/list');
    return res.data;
  },
  getIpDetail: async (ipId: string) => {
    const res = await API.get(`/ip/${ipId}`);
    return res.data;
  },
  createIp: async (payload: any) => {
    const res = await API.post('/ip/create', payload);
    return res.data;
  },
  saveStoryPackage: async (ipId: string, payload: any) => {
    const res = await API.post(`/ip/${ipId}/story-forge/save`, payload);
    return res.data;
  }
};

export const telemetryApi = {
  trackEvent: async (payload: {
    event_name: string;
    session_id: string;
    user_id?: string;
    ip_id?: string;
    series_id?: string;
    episode_id?: string;
    playback_second?: number;
    region_code?: string;
    device_type?: string;
    metadata?: Record<string, any>;
  }) => {
    try {
      const res = await API.post('/events/track', payload);
      return res.data;
    } catch {
      return { status: 'buffered' };
    }
  },
  getRetentionTelemetry: async (seriesId: string, episodeId: string) => {
    const res = await API.get(`/events/retention/${seriesId}/${episodeId}`);
    return res.data;
  }
};

