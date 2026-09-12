export type AppMode = 'viewer' | 'creator' | 'admin';

export type MarketRegion = 'ZA' | 'NG' | 'KE' | 'GHS' | 'GLOBAL';

export type EpisodeStatus =
  | 'draft'
  | 'pre_flight'
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'scheduled'
  | 'published'
  | 'changes_requested'
  | 'rejected';

export interface PreflightHealth {
  aspect_ratio_ok: boolean;
  aspect_ratio_label: string; // e.g., "1080 × 1920 (9:16)"
  duration_ok: boolean;
  duration_seconds: number;
  audio_detected: boolean;
  thumbnail_present: boolean;
  cliffhanger_marker_ok: boolean;
  cliffhanger_time_seconds: number;
  cliffhanger_hook_copy?: string;
  captions_present: boolean;
}

export interface Episode {
  id: string;
  series_id: string;
  episode_number: number;
  title: string;
  synopsis: string;
  duration_seconds: number;
  video_url: string;
  thumbnail_url: string;
  is_free: boolean;
  coin_price: number;
  cliffhanger_time: number;
  cliffhanger_hook?: string;
  status?: EpisodeStatus;
  scheduled_at?: string;
  preflight_health?: PreflightHealth;
  moderation_feedback?: string;
  likes_count: number;
  views_count: number;
  comments_count: number;
  published_at: string;
  media_asset_id?: string;
  storage_key?: string;
  hls_url?: string;
  subtitles?: Record<string, Array<{ start: string; end: string; text: string }>>;
}

export interface Story {
  id: string;
  title: string;
  tagline: string;
  synopsis: string;
  cover_image: string;
  vertical_poster: string;
  genre: string;
  language: string;
  available_languages: string[];
  tags: string[];
  creator_id: string;
  creator_name: string;
  creator_avatar: string;
  is_verified_creator: boolean;
  rating: number;
  total_episodes: number;
  free_episodes_count: number;
  coin_price_per_episode: number;
  total_views: number;
  total_likes: number;
  is_original: boolean;
  is_trending: boolean;
  status: string;
  ip_id?: string;
  franchise_code?: string;
  characters?: any[];
  under_review_episodes_count?: number;
  episodes: Episode[];
}

export interface Creator {
  id: string;
  name: string;
  handle: string;
  bio: string;
  avatar: string;
  country: string;
  verified: boolean;
  followers_count: number;
  total_views: number;
  coin_earnings: number;
  payout_balance: number;
}

export interface Comment {
  id: string;
  episode_id: string;
  user_name: string;
  avatar: string;
  text: string;
  likes: number;
  time_ago: string;
}

export interface Reaction {
  id: string;
  episode_id: string;
  emoji: string;
  timestamp_seconds: number;
}

export interface CoinPack {
  id: string;
  coins: number;
  bonus: number;
  price_usd: number;
  price_local: number;
  currency: string;
  popular: boolean;
  label: string;
  description?: string;
}

export interface VirtualGift {
  id: string;
  name: string;
  icon: string;
  cost: number;
  description: string;
}

export interface SACarrier {
  id: string;
  name: string;
  brand_color: string;
  icon: string;
  country: string;
  speed: string;
  ussd_code: string;
  prefixes: string[];
  support_note: string;
}

export interface AirtimePass {
  id: string;
  name: string;
  price_zar: number;
  duration: string;
  benefits: string;
  badge: string;
  popular: boolean;
  coins_grant: number;
}

export interface AirtimeTransaction {
  transaction_id: string;
  status: string;
  charge_type: string;
  target_id: string;
  carrier_id: string;
  carrier_name: string;
  phone_number: string;
  amount_zar: number;
  coins_credited: number;
  reference: string;
  sms_notification: string;
  timestamp: string;
}

export interface USSDSession {
  session_id: string;
  carrier: string;
  phone: string;
  ussd_code: string;
  menu_text: string;
  options: Array<{ choice: string; label: string; amount: number; coins: number }>;
}

export type CreatorNavTab =
  | 'overview'
  | 'series'
  | 'story_forge'
  | 'episodes'
  | 'analytics'
  | 'earnings'
  | 'profile';

export type SeriesCommandTab =
  | 'overview'
  | 'episodes'
  | 'story'
  | 'assets'
  | 'analytics';

export interface ModerationItem {
  id: string;
  series_id?: string;
  series_title: string;
  episode_id?: string;
  episode_number?: number;
  episode_title?: string;
  creator_name: string;
  creator_id?: string;
  submitted_at: string;
  aspect_ratio: string;
  duration: string;
  duration_seconds?: number;
  video_url?: string;
  thumbnail_url?: string;
  cliffhanger_time?: number;
  cliffhanger_hook?: string;
  ai_safety_score: number;
  status: 'pending_review' | 'under_review' | 'approved' | 'rejected' | 'changes_requested';
  flag: string;
  preflight_health?: PreflightHealth;
  feedback?: string;
}


// --- Story Forge & Writer Hub ---
export interface StoryBeat {
  timestamp_seconds: number;
  label: string;
  intensity: number; // 1-10
  action_description: string;
  cliffhanger_trigger?: boolean;
}

export interface DialogueLine {
  speaker: string;
  original_text: string;
  dialect_code: 'zu' | 'yo' | 'sw' | 'pcm' | 'en' | 'xh';
  dialect_label: string;
  phonetic_note?: string;
}

export interface CharacterBibleItem {
  id: string;
  name: string;
  role: 'protagonist' | 'antagonist' | 'confidant' | 'catalyst';
  archetype: string;
  secret_motivation: string;
  fatal_flaw: string;
  signature_quote: string;
  avatar_seed?: string;
}

export interface StoryForgeScript {
  id: string;
  series_title: string;
  genre: string;
  target_duration_seconds: number;
  logline: string;
  beats: StoryBeat[];
  dialogue: DialogueLine[];
  characters: CharacterBibleItem[];
  cliffhanger_prompt: string;
  created_at: string;
}

// --- Creator Analytics & Retention Telemetry ---
export interface DropoffDataPoint {
  second: number;
  retention_pct: number;
  viewer_count: number;
  is_cliffhanger?: boolean;
}

export interface RetentionTelemetry {
  series_id: string;
  episode_id: string;
  episode_number: number;
  total_starts: number;
  completion_rate_pct: number;
  cliffhanger_conversion_pct: number;
  avg_watch_time_seconds: number;
  dropoff_curve: DropoffDataPoint[];
  geo_distribution: Array<{ country: string; flag: string; share_pct: number; views: number }>;
  telco_payment_mix: Array<{ provider: string; color: string; share_pct: number }>;
}

// --- MoMo Payouts & Invoicing ---
export type PayoutRail = 'momo' | 'mpesa' | 'chipper' | 'bank' | 'airtime';

export interface MoMoPayoutTransaction {
  id: string;
  transaction_ref: string;
  invoice_number: string;
  creator_id: string;
  creator_name: string;
  rail: PayoutRail;
  provider_name: string;
  account_identifier: string;
  coins_redeemed: number;
  gross_amount_zar: number;
  platform_fee_zar: number;
  tax_withholding_zar: number;
  net_payout_zar: number;
  currency: string;
  status: 'completed' | 'processing' | 'pending' | 'failed';
  created_at: string;
  settled_at?: string;
}


export interface AIStatus {
  mode: 'live' | 'fallback';
  provider: string;
  model: string;
  is_connected: boolean;
  has_api_key: boolean;
  quota_depleted?: boolean;
  masked_key?: string;
  latency_ms: number;
  supported_dialects: string[];
}
