/**
 * Welele Media™ — Experience Engine Frontend Types (WEE Layer 4: Contract)
 * Defines the strict TypeScript interfaces matching the Experience Manifest contract.
 */

import { Story } from './index';

export type SectionType =
  | 'HERO_CAROUSEL'
  | 'HORIZONTAL_ROW'
  | 'POSTER_GRID'
  | 'EDITORIAL_SPOTLIGHT'
  | 'EDITORIAL_BANNER'
  | 'GENRE_PILLS_ROW'
  | 'COMING_SOON_RADAR'
  | 'CONTINUE_WATCHING';

export type CtaAction =
  | 'STREAM_EPISODE'
  | 'OPEN_STORY_DETAIL'
  | 'OPEN_PAYMENT_MODAL'
  | 'OPEN_CREATOR_PROFILE'
  | 'FILTER_GENRE'
  | 'EXTERNAL_LINK';

export interface ArtworkOverrides {
  mobile_9_16?: string;
  desktop_16_9?: string;
  banner_wide?: string;
  trailer_video_url?: string;
}

export interface SlotItem {
  slot_id: string;
  content_type?: 'series' | 'episode' | 'creator' | 'promo' | 'genre';
  content_id?: string;
  badge?: string;
  headline_override?: string;
  subheadline_override?: string;
  cta_text?: string;
  cta_action?: CtaAction;
  cta_target?: string;
  artwork_overrides?: ArtworkOverrides;
  is_active?: boolean;
  start_at?: string;
  end_at?: string;
  story?: Story; // Hydrated catalog story attached by backend resolver
}

export interface SectionSource {
  mode?: 'manual' | 'algorithmic' | 'hybrid';
  algo_type?: 'velocity_24h' | 'completion_rate' | 'new_releases' | 'trending' | 'personalized';
  pinned_content_ids?: string[];
  genre_filter?: string;
  max_items?: number;
}

export interface SectionConfig {
  auto_play_seconds?: number;
  aspect_ratio?: string;
  card_size?: 'small' | 'medium' | 'large';
  show_rank_numbers?: boolean;
  banner_style?: 'glass_gradient' | 'solid' | 'neon_glow' | 'editorial_dark';
  background_color?: string;
  cta_primary_color?: string;
  columns?: number;
}

export interface ExperienceSection {
  section_id: string;
  type: SectionType;
  title?: string | null;
  subtitle?: string | null;
  is_visible: boolean;
  order: number;
  config: SectionConfig;
  source: SectionSource;
  items: SlotItem[];
  start_at?: string;
  end_at?: string;
}

export interface PageMeta {
  title: string;
  theme?: string;
  description?: string;
}

export interface BrandAsset {
  id: string;
  asset_type: 'sonic_visual_ident' | 'originals_ident' | 'welcome_ident' | 'campaign_ident';
  name: string;
  url: string;
  version: number;
  active: boolean;
  duration?: number;
}

export interface BrandIdentConfig {
  play_brand_ident: boolean;
  brand_ident_url: string;
  brand_ident_duration?: number;
  ident_frequency: number; // Launch default: 5 (First episode + every 5th subsequent episode)
  failsafe_buffer?: number; // Configurable buffer in seconds (default: 1.0)
  experience_rule?: 'standard' | 'first_visit' | 'originals' | 'special_event' | 'creator_premiere';
  asset?: BrandAsset;
}

export interface ExperienceManifest {
  page_id: string;
  version: string;
  status: 'draft' | 'published' | 'archived';
  published_at?: string;
  updated_at?: string;
  meta: PageMeta;
  brand_config?: BrandIdentConfig;
  sections: ExperienceSection[];
}
