import { ExperienceManifest, ExperienceSection, SlotItem, BrandIdentConfig } from '../types/experience';
import { Story } from '../types';
import { DEFAULT_STORIES } from '../services/mockData';

export const DEFAULT_BRAND_IDENT_CONFIG: BrandIdentConfig = {
  play_brand_ident: true,
  brand_ident_url: '/videos/welele_ident_v2.mp4',
  brand_ident_duration: 5.2,
  ident_frequency: 5, // Launch default: 5 (First episode of session + every 5th subsequent)
  failsafe_buffer: 1.0, // Configurable failsafe watchdog margin
  experience_rule: 'standard',
  asset: {
    id: 'welele-brand-ident-v2',
    asset_type: 'sonic_visual_ident',
    name: 'Welele Sonic Visual Ident v2',
    url: '/videos/welele_ident_v2.mp4',
    version: 2,
    active: true,
    duration: 5.2,
  },
};

/**
 * Hydrates an ExperienceManifest by attaching full Story objects to slot items
 * and populating empty sections from pinned content IDs or catalog.
 */
export function hydrateManifest(
  rawManifest: ExperienceManifest,
  storiesCatalog: Story[] = DEFAULT_STORIES
): ExperienceManifest {
  const catalog = storiesCatalog && storiesCatalog.length > 0 ? storiesCatalog : DEFAULT_STORIES;
  const storyMap = new Map<string, Story>();
  catalog.forEach((s) => storyMap.set(s.id, s));
  DEFAULT_STORIES.forEach((s) => {
    if (!storyMap.has(s.id)) storyMap.set(s.id, s);
  });

  const hydratedSections: ExperienceSection[] = rawManifest.sections.map((section) => {
    let items: SlotItem[] = [...(section.items || [])];

    // If items are empty but pinned_content_ids exist, populate items
    if (items.length === 0 && section.source?.pinned_content_ids && section.source.pinned_content_ids.length > 0) {
      items = section.source.pinned_content_ids.map((id, idx) => ({
        slot_id: `slot_${section.section_id}_${id}_${idx}`,
        content_type: 'series',
        content_id: id,
        badge: section.type === 'HERO_CAROUSEL' ? (idx === 0 ? 'SPOTLIGHT ORIGINAL' : 'TOP RATED #1') : undefined,
        cta_text: 'Watch Now',
        cta_action: 'STREAM_EPISODE',
        is_active: true,
      }));
    }

    // Hydrate each slotItem with story object
    const hydratedItems: SlotItem[] = items.map((item, idx) => {
      const story = item.story || (item.content_id ? storyMap.get(item.content_id) : undefined) || catalog[idx % catalog.length];
      return {
        ...item,
        story,
        artwork_overrides: {
          mobile_9_16: item.artwork_overrides?.mobile_9_16 || story?.vertical_poster || story?.cover_image || '/posters/blood_ties.jpg',
          desktop_16_9: item.artwork_overrides?.desktop_16_9 || story?.cover_image || story?.vertical_poster || '/banners/blood_ties_banner.jpg',
          trailer_video_url: item.artwork_overrides?.trailer_video_url || story?.episodes?.[0]?.video_url || '/videos/ocean_waves.mp4',
        },
      };
    });

    return {
      ...section,
      items: hydratedItems,
    };
  });

  return {
    ...rawManifest,
    sections: hydratedSections,
  };
}

/**
 * Returns the canonical default ExperienceManifest for a page (e.g. 'home', 'discover')
 * fully hydrated with active stories.
 */
export function getDefaultExperienceManifest(
  pageId: string,
  storiesCatalog: Story[] = DEFAULT_STORIES
): ExperienceManifest {
  const catalog = storiesCatalog && storiesCatalog.length > 0 ? storiesCatalog : DEFAULT_STORIES;
  const storyMap = new Map<string, Story>();
  catalog.forEach((s) => storyMap.set(s.id, s));
  DEFAULT_STORIES.forEach((s) => {
    if (!storyMap.has(s.id)) storyMap.set(s.id, s);
  });

  const getStory = (id: string, fallbackIdx = 0): Story => {
    return storyMap.get(id) || catalog[fallbackIdx % catalog.length] || DEFAULT_STORIES[0];
  };

  if (pageId === 'discover') {
    const rawDiscover: ExperienceManifest = {
      page_id: 'discover',
      version: '1.0.0',
      status: 'published',
      published_at: '2026-08-01T00:00:00Z',
      updated_at: '2026-09-08T10:00:00Z',
      meta: {
        title: 'Discover | Welele™',
        theme: 'dark_gold_glow',
        description: 'Explore African short dramas by genre, country, and creator.',
      },
      brand_config: DEFAULT_BRAND_IDENT_CONFIG,
      sections: [
        {
          section_id: 'sec_discover_grid',
          type: 'POSTER_GRID',
          title: 'All Series Catalog',
          subtitle: 'Browse 9:16 micro-series with free introductory episodes',
          is_visible: true,
          order: 0,
          config: {
            columns: 2,
            card_size: 'medium',
          },
          source: {
            mode: 'algorithmic',
            max_items: 24,
          },
          items: catalog.map((s, idx) => ({
            slot_id: `slot_disc_${s.id}_${idx}`,
            content_type: 'series',
            content_id: s.id,
            story: s,
            badge: s.is_original ? 'ORIGINAL' : s.is_trending ? 'TRENDING' : undefined,
            headline_override: s.title,
            subheadline_override: s.synopsis,
            cta_text: 'Watch Now',
            cta_action: 'STREAM_EPISODE',
            is_active: true,
          })),
        },
      ],
    };
    return rawDiscover;
  }

  // Canonical Home Manifest
  const heroStoryIds = [
    'story_blood_ties',
    'story_queen_of_jozi',
    'story_ceo_wife',
    'story_umembeso',
    'story_lagos_confidential',
  ];

  const heroBadges = [
    'SPOTLIGHT ORIGINAL',
    'TOP RATED #1',
    'VIRAL HIT',
    'TRENDING DRAMA',
    'PAN-AFRICAN SHOWCASE',
  ];

  const heroItems: SlotItem[] = heroStoryIds.map((id, idx) => {
    const s = getStory(id, idx);
    return {
      slot_id: `slot_hero_${s.id}`,
      content_type: 'series',
      content_id: s.id,
      story: s,
      badge: heroBadges[idx] || (s.is_original ? 'SPOTLIGHT ORIGINAL' : 'TOP RATED #1'),
      headline_override: s.title,
      subheadline_override: s.synopsis || s.tagline,
      cta_text: 'Watch Now',
      cta_action: 'STREAM_EPISODE',
      cta_target: s.episodes?.[0]?.id || '',
      artwork_overrides: {
        mobile_9_16: s.vertical_poster || s.cover_image,
        desktop_16_9: s.cover_image || s.vertical_poster || '/banners/blood_ties_banner.jpg',
        trailer_video_url: s.episodes?.[0]?.video_url || '/videos/ocean_waves.mp4',
      },
      is_active: true,
    };
  });

  const trendingStoryIds = [
    'story_queen_of_jozi',
    'story_ceo_wife',
    'story_heist_game',
    'story_barrio_billionaire',
    'story_lagos_confidential',
  ];

  const trendingItems: SlotItem[] = trendingStoryIds.map((id, idx) => {
    const s = getStory(id, idx);
    return {
      slot_id: `slot_trending_${s.id}`,
      content_type: 'series',
      content_id: s.id,
      story: s,
      badge: `#${idx + 1} TODAY`,
      headline_override: s.title,
      subheadline_override: s.synopsis,
      cta_text: 'Watch Now',
      cta_action: 'STREAM_EPISODE',
      cta_target: s.episodes?.[0]?.id || '',
      artwork_overrides: {
        mobile_9_16: s.vertical_poster || s.cover_image,
        desktop_16_9: s.cover_image || s.vertical_poster,
      },
      is_active: true,
    };
  });

  const spotlightStory = getStory('story_blood_ties', 0);

  const originalsStoryIds = [
    'story_blood_ties',
    'story_umembeso',
    'story_durban_heat',
    'story_the_hustlers',
  ];

  const originalsItems: SlotItem[] = originalsStoryIds.map((id, idx) => {
    const s = getStory(id, idx);
    return {
      slot_id: `slot_orig_${s.id}`,
      content_type: 'series',
      content_id: s.id,
      story: s,
      badge: 'WELELE ORIGINAL',
      headline_override: s.title,
      subheadline_override: s.synopsis,
      cta_text: 'Watch Now',
      cta_action: 'STREAM_EPISODE',
      cta_target: s.episodes?.[0]?.id || '',
      artwork_overrides: {
        mobile_9_16: s.vertical_poster || s.cover_image,
        desktop_16_9: s.cover_image || s.vertical_poster,
      },
      is_active: true,
    };
  });

  const comingSoonStoryIds = ['story_accra_nights', 'story_nairobi_hustle'];
  const comingSoonItems: SlotItem[] = comingSoonStoryIds.map((id, idx) => {
    const s = getStory(id, idx);
    return {
      slot_id: `slot_cs_${s.id}`,
      content_type: 'series',
      content_id: s.id,
      story: s,
      badge: 'DROPPING NEXT WEEK',
      headline_override: s.title,
      subheadline_override: s.synopsis,
      cta_text: 'Remind Me',
      cta_action: 'OPEN_STORY_DETAIL',
      cta_target: s.id,
      artwork_overrides: {
        mobile_9_16: s.vertical_poster || s.cover_image,
        desktop_16_9: s.cover_image || s.vertical_poster,
      },
      is_active: true,
    };
  });

  const homeManifest: ExperienceManifest = {
    page_id: 'home',
    version: '1.0.0',
    status: 'published',
    published_at: '2026-08-01T00:00:00Z',
    updated_at: '2026-09-08T10:00:00Z',
    meta: {
      title: 'Welele™ | Short African Dramas',
      theme: 'dark_gold_glow',
      description: 'Stream high-octane 9:16 vertical micro-dramas produced across South Africa, Nigeria, and Ghana.',
    },
    brand_config: DEFAULT_BRAND_IDENT_CONFIG,
    sections: [
      {
        section_id: 'sec_hero_home',
        type: 'HERO_CAROUSEL',
        title: null,
        subtitle: null,
        is_visible: true,
        order: 0,
        config: {
          auto_play_seconds: 8,
          aspect_ratio: '9:16',
          card_size: 'large',
          show_rank_numbers: false,
        },
        source: {
          mode: 'manual',
          pinned_content_ids: heroStoryIds,
          max_items: 5,
        },
        items: heroItems,
      },
      {
        section_id: 'sec_trending_row',
        type: 'HORIZONTAL_ROW',
        title: 'Trending in South Africa 🔥',
        subtitle: 'Top daily bingeable vertical micro-episodes',
        is_visible: true,
        order: 1,
        config: {
          card_size: 'medium',
          show_rank_numbers: true,
          aspect_ratio: '9:16',
        },
        source: {
          mode: 'manual',
          pinned_content_ids: trendingStoryIds,
          max_items: 8,
        },
        items: trendingItems,
      },
      {
        section_id: 'sec_airtime_promo',
        type: 'EDITORIAL_BANNER',
        title: null,
        subtitle: null,
        is_visible: true,
        order: 2,
        config: {
          banner_style: 'editorial_dark',
        },
        source: {
          mode: 'manual',
        },
        items: [
          {
            slot_id: 'slot_airtime_promo_1',
            content_type: 'promo',
            badge: 'MZANSI FLASH DROP',
            headline_override: 'Unlock 50 Coins for R15 with Vodacom & MTN Airtime',
            subheadline_override: 'Instant one-tap checkout with Direct Carrier Billing. No credit card required.',
            cta_text: 'Claim Special Pack',
            cta_action: 'OPEN_PAYMENT_MODAL',
            is_active: true,
          },
        ],
      },
      {
        section_id: 'sec_spotlight_editorial',
        type: 'EDITORIAL_SPOTLIGHT',
        title: 'Spotlight Feature',
        subtitle: 'Curated by Welele Editorial Desk',
        is_visible: true,
        order: 3,
        config: {
          aspect_ratio: '16:9',
          banner_style: 'editorial_dark',
        },
        source: {
          mode: 'manual',
          pinned_content_ids: [spotlightStory.id],
        },
        items: [
          {
            slot_id: 'slot_spotlight_1',
            content_type: 'series',
            content_id: spotlightStory.id,
            story: spotlightStory,
            badge: 'WELELE ORIGINAL',
            headline_override: `${spotlightStory.title}: The Dynasty That Redefined Jozi Drama`,
            subheadline_override: 'Director Zola Dlamini delivers a masterclass in 90-second cliffhanger storytelling.',
            cta_text: 'Watch From Episode 1',
            cta_action: 'STREAM_EPISODE',
            cta_target: spotlightStory.episodes?.[0]?.id || '',
            artwork_overrides: {
              desktop_16_9: spotlightStory.cover_image || '/banners/blood_ties_banner.jpg',
              mobile_9_16: spotlightStory.vertical_poster,
            },
            is_active: true,
          },
        ],
      },
      {
        section_id: 'sec_originals_row',
        type: 'HORIZONTAL_ROW',
        title: 'Welele Originals 🎬',
        subtitle: 'Exclusive short-form productions made for vertical viewing',
        is_visible: true,
        order: 4,
        config: {
          card_size: 'medium',
          show_rank_numbers: false,
          aspect_ratio: '9:16',
        },
        source: {
          mode: 'manual',
          pinned_content_ids: originalsStoryIds,
          max_items: 8,
        },
        items: originalsItems,
      },
      {
        section_id: 'sec_coming_soon',
        type: 'COMING_SOON_RADAR',
        title: 'Coming Soon to Welele 🚀',
        subtitle: 'Dropping next week — Turn on episode reminders',
        is_visible: true,
        order: 5,
        config: {
          card_size: 'medium',
        },
        source: {
          mode: 'manual',
          pinned_content_ids: comingSoonStoryIds,
          max_items: 4,
        },
        items: comingSoonItems,
      },
    ],
  };

  return homeManifest;
}
