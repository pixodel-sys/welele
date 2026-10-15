-- ============================================================================
-- WELELE MEDIA™ — STAGING CANONICAL CATALOG SEED SCRIPT (v1.0)
-- Target Platform: PostgreSQL 15+ (Supabase Staging Project Ref: dbsnaidhznofvyffdfni)
-- Scope:
--   1. Seed Authoritative Studio & Creator Persona Records
--   2. Seed 11 Canonical Digital IPs with Deterministic UUIDs
--   3. Seed 11 Published Series with Landscape Banners & 9:16 Vertical Posters
--   4. Seed Canonical Episodes with Free/Coin Cliffhanger Gates
--   5. Seed Decoupled Media Assets referencing verified static MP4 video assets
--   6. Seed Home Experience Layout Manifest (Hero Carousel, Trending, Spotlight)
-- Pre-conditions: 00_staging_consolidated_migration_v2.sql applied
-- Idempotency: All statements use ON CONFLICT DO UPDATE/NOTHING.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- STEP 1: STUDIO OWNER & CREATOR PERSONAS
-- ----------------------------------------------------------------------------

-- 1. Studio Administrator & Creator User
INSERT INTO public.users (
    id, display_name, email, phone_number, region_code, preferred_language, role, is_verified, created_at, updated_at
) VALUES (
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    'Zola Dlamini',
    'zola.dlamini@welele.media',
    '+27828912345',
    'ZA',
    'isiZulu',
    'creator',
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    role = EXCLUDED.role;

INSERT INTO public.users (
    id, display_name, email, phone_number, region_code, preferred_language, role, is_verified, created_at, updated_at
) VALUES (
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_amaka'),
    'Amaka Okafor',
    'amaka.okafor@welele.media',
    '+2348031234567',
    'NG',
    'Yoruba',
    'creator',
    TRUE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    role = EXCLUDED.role;

-- 2. Creator Studio Profiles
INSERT INTO public.creators (
    id, user_id, stage_name, bio, country, is_verified, total_views, lifetime_earnings_zar, created_at
) VALUES (
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.creator_zola'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    'Zola Dlamini',
    'Multi-award winning Johannesburg director and creator of Blood Ties and Queen of Jozi.',
    'ZA',
    TRUE,
    4850000,
    145000.00,
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    stage_name = EXCLUDED.stage_name,
    bio = EXCLUDED.bio;

INSERT INTO public.creators (
    id, user_id, stage_name, bio, country, is_verified, total_views, lifetime_earnings_zar, created_at
) VALUES (
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.creator_amaka'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_amaka'),
    'Amaka Okafor',
    'Lagos-based romance novelist and screenwriter behind The CEO''s Secret Wife.',
    'NG',
    TRUE,
    3210000,
    98000.00,
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    stage_name = EXCLUDED.stage_name,
    bio = EXCLUDED.bio;

-- ----------------------------------------------------------------------------
-- STEP 2: CANONICAL DIGITAL IP ASSET ROOTS
-- ----------------------------------------------------------------------------

INSERT INTO public.digital_ips (
    id, title, franchise_code, logline, synopsis, genre, primary_language, master_owner_id, global_valuation_usd, status
) VALUES 
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_blood_ties'),
    'Blood Ties',
    'FRAN_BLOOD_TIES',
    'Two powerful families tied by blood, torn apart by greed.',
    'When the matriarch of the mighty Khumalo dynasty collapses at the annual Sandton gala, a hidden will surfaces that names a secret daughter as the sole heir. Betrayal, boardroom warfare, and family secrets collide in Johannesburg''s most dramatic showdown.',
    'Drama • Family • Betrayal',
    'isiZulu',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    250000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_queen_of_jozi'),
    'Queen of Jozi',
    'FRAN_QUEEN_OF_JOZI',
    'One woman''s ruthless rise to the top of Johannesburg''s underworld.',
    'When her husband''s gold syndication empire falls into rival hands, Nina Khumalo steps from the shadows to reclaim the throne in Sandton. Boardroom power plays meet street warfare in South Africa''s most anticipated micro-drama.',
    'Crime • Empire • Dynasty',
    'isiZulu',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    180000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_ceo_wife'),
    'The CEO''s Secret Wife',
    'FRAN_CEO_SECRET_WIFE',
    'A fake marriage. A hidden identity. A love that could ruin everything.',
    'To save her family''s heritage estate from foreclosure, Zandile agrees to a 1-year secret contract marriage with Sandile Ndlovu, Johannesburg''s most feared billionaire CEO. But behind closed doors in his Clifton penthouse, cold business turns into undeniable, forbidden passion.',
    'Romance • Contract Marriage',
    'English',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_amaka'),
    150000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_umembeso'),
    'Umembeso: Royal Secrets',
    'FRAN_UMEMBESO',
    'A traditional royal wedding where every gift carries a deadly secret.',
    'During the opulent royal dowry ceremony in KwaZulu-Natal, an ancient family talisman is stolen, threatening to expose a thirty-year bloodline deception before the vows are sealed.',
    'Romance • Royal • Mystery',
    'isiZulu',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    120000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_lagos_confidential'),
    'Lagos Confidential',
    'FRAN_LAGOS_CONFIDENTIAL',
    'High-tech corporate espionage across Victoria Island.',
    'A brilliant forensic hacker uncovers a multi-billion naira offshore conduit on the eve of West Africa''s biggest telecom merger. With assassins on his trail, 60 seconds is all he has to leak the truth.',
    'Action • Tech • Thriller',
    'English',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_amaka'),
    160000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_zulu_love'),
    'Zulu Love Story',
    'FRAN_ZULU_LOVE_STORY',
    'Two worlds. One unforgettable royal heartbeat.',
    'Prince Sipho of the KwaZulu royal line meets Nandi, an edgy streetwear designer from Braamfontein. When ancestral duty calls him home to an arranged marriage, will he choose the crown or true love?',
    'Romance • Mzansi Originals',
    'isiZulu',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    110000.00,
    'active'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_broken_vows'),
    'Broken Vows',
    'FRAN_BROKEN_VOWS',
    'Every secret comes with a price in high society.',
    'During an ultra-glamorous 10th-anniversary ball in Sandton, an anonymous caller plays a secret recording that exposes betrayal, money laundering, and an unspoken pact from 2014.',
    'Drama • Mystery • Thriller',
    'isiZulu',
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.user_zola'),
    95000.00,
    'active'
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    synopsis = EXCLUDED.synopsis;

-- ----------------------------------------------------------------------------
-- STEP 3: CANONICAL SERIES & SEASONS (WITH VERIFIED POSTER & BANNER ASSETS)
-- ----------------------------------------------------------------------------

INSERT INTO public.series (
    id, ip_id, season_number, title, tagline, synopsis, cover_image, vertical_poster,
    genre, rating, total_episodes, free_episodes, coin_price_per_episode, is_published, available_languages, tags
) VALUES
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_blood_ties'),
    1,
    'Blood Ties',
    'Two powerful families tied by blood, torn apart by greed.',
    'When the matriarch of the mighty Khumalo dynasty collapses at the annual Sandton gala, a hidden will surfaces that names a secret daughter as the sole heir. Betrayal, boardroom warfare, and family secrets collide in Johannesburg''s most dramatic showdown.',
    '/banners/blood_ties_banner.jpg',
    '/posters/blood_ties.jpg',
    'Drama • Family • Betrayal',
    4.98,
    3,
    2,
    5,
    TRUE,
    ARRAY['isiZulu', 'isiXhosa', 'English', 'Afrikaans', 'Sesotho'],
    ARRAY['#BloodTies', '#MzansiDrama', '#BillionaireDynasty', '#Cliffhanger', '#WeleleOriginal']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_queen_of_jozi'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_queen_of_jozi'),
    1,
    'Queen of Jozi',
    'One woman''s ruthless rise to the top of Johannesburg''s underworld.',
    'When her husband''s gold syndication empire falls into rival hands, Nina Khumalo steps from the shadows to reclaim the throne in Sandton. Boardroom power plays meet street warfare in South Africa''s most anticipated micro-drama.',
    '/banners/queen_of_jozi_banner.jpg',
    '/posters/queen_of_jozi.jpg',
    'Crime • Empire • Dynasty',
    4.99,
    2,
    1,
    5,
    TRUE,
    ARRAY['isiZulu', 'isiXhosa', 'English', 'Afrikaans', 'Sesotho'],
    ARRAY['#QueenOfJozi', '#SandtonDynasty', '#MzansiCrime', '#WeleleSpotlight', '#Original']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_ceo_wife'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_ceo_wife'),
    1,
    'The CEO''s Secret Wife',
    'A fake marriage. A hidden identity. A love that could ruin everything.',
    'To save her family''s heritage estate from foreclosure, Zandile agrees to a 1-year secret contract marriage with Sandile Ndlovu, Johannesburg''s most feared billionaire CEO. But behind closed doors in his Clifton penthouse, cold business turns into undeniable, forbidden passion.',
    '/banners/ceo_secret_wife_banner.jpg',
    '/posters/ceo_secret_wife.jpg',
    'Romance • Contract Marriage',
    4.96,
    2,
    1,
    5,
    TRUE,
    ARRAY['English', 'isiZulu', 'Swahili', 'French', 'Pidgin'],
    ARRAY['#SecretWife', '#BillionaireRomance', '#ContractMarriage', '#SandtonLove', '#Trending']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_umembeso'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_umembeso'),
    1,
    'Umembeso: Royal Secrets',
    'A traditional royal wedding where every gift carries a deadly secret.',
    'During the opulent royal dowry ceremony in KwaZulu-Natal, an ancient family talisman is stolen, threatening to expose a thirty-year bloodline deception before the vows are sealed.',
    '/banners/umembeso_banner.jpg',
    '/posters/umembeso.jpg',
    'Romance • Royal • Mystery',
    4.94,
    1,
    1,
    5,
    TRUE,
    ARRAY['isiZulu', 'isiXhosa', 'English', 'Afrikaans'],
    ARRAY['#Umembeso', '#RoyalSecrets', '#ZuluTradition', '#MzansiRomance']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_lagos_confidential'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_lagos_confidential'),
    1,
    'Lagos Confidential',
    'High-tech corporate espionage across Victoria Island.',
    'A brilliant forensic hacker uncovers a multi-billion naira offshore conduit on the eve of West Africa''s biggest telecom merger. With assassins on his trail, 60 seconds is all he has to leak the truth.',
    '/banners/lagos_confidential_banner.jpg',
    '/posters/lagos_confidential.jpg',
    'Action • Tech • Thriller',
    4.96,
    1,
    1,
    5,
    TRUE,
    ARRAY['English', 'Pidgin', 'Yoruba', 'French'],
    ARRAY['#LagosConfidential', '#NaijaTech', '#VictoriaIsland', '#CyberThriller']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_zulu_love'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_zulu_love'),
    1,
    'Zulu Love Story',
    'Two worlds. One unforgettable royal heartbeat.',
    'Prince Sipho of the KwaZulu royal line meets Nandi, an edgy streetwear designer from Braamfontein. When ancestral duty calls him home to an arranged marriage, will he choose the crown or true love?',
    '/posters/zulu_love_story.jpg',
    '/posters/zulu_love_story.jpg',
    'Romance • Mzansi Originals',
    4.97,
    1,
    1,
    5,
    TRUE,
    ARRAY['isiZulu', 'isiXhosa', 'English', 'Afrikaans'],
    ARRAY['#ZuluLove', '#RoyalRomance', '#DurbanToJozi', '#MzansiMagic']
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_broken_vows'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ip_broken_vows'),
    1,
    'Broken Vows',
    'Every secret comes with a price in high society.',
    'During an ultra-glamorous 10th-anniversary ball in Sandton, an anonymous caller plays a secret recording that exposes betrayal, money laundering, and an unspoken pact from 2014.',
    '/posters/broken_vows.jpg',
    '/posters/broken_vows.jpg',
    'Drama • Mystery • Thriller',
    4.92,
    1,
    1,
    5,
    TRUE,
    ARRAY['isiZulu', 'isiXhosa', 'English', 'Afrikaans'],
    ARRAY['#BrokenVows', '#SandtonScandal', '#HighSociety', '#Betrayal']
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    cover_image = EXCLUDED.cover_image,
    vertical_poster = EXCLUDED.vertical_poster,
    total_episodes = EXCLUDED.total_episodes;

-- ----------------------------------------------------------------------------
-- STEP 4: CANONICAL EPISODES & CLIFFHANGER GATES
-- ----------------------------------------------------------------------------

INSERT INTO public.episodes (
    id, series_id, episode_number, title, synopsis, duration_seconds, is_free, coin_price, cliffhanger_time_seconds, cliffhanger_hook, status
) VALUES
-- Blood Ties Episodes
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties'),
    1,
    'The Golden Will',
    'The unsealed court document triggers panic in the boardroom.',
    68,
    TRUE,
    0,
    58,
    'Who authorized her DNA test before the funeral?',
    'published'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties'),
    2,
    'Midnight at the Rank',
    'Sipho confronts the convoy blocking the workshop.',
    74,
    TRUE,
    0,
    64,
    'Will Bra Oupa draw his weapon first?',
    'published'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_3'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties'),
    3,
    'The Cartel Route',
    'The hidden ledger exposes illicit transit lines across Gauteng.',
    82,
    FALSE,
    5,
    72,
    'The security camera reveals the traitor in the family.',
    'published'
),
-- Queen of Jozi Episodes
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_qj_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_queen_of_jozi'),
    1,
    'The Golden Vault',
    'Nina Khumalo breaks into her late husband''s private Sandton vault.',
    75,
    TRUE,
    0,
    65,
    'The vault door opens to reveal an empty safe and a ticking timer.',
    'published'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_qj_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_queen_of_jozi'),
    2,
    'Red Velvet Syndicate',
    'A standoff at the Rosebank nightclub changes the underworld balance.',
    80,
    FALSE,
    5,
    70,
    'Whose finger is on the detonator?',
    'published'
),
-- The CEO's Secret Wife Episodes
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_ceo_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_ceo_wife'),
    1,
    'The Contract Signed',
    'Zandile signs the one-year non-disclosure contract in Sandile''s penthouse.',
    70,
    TRUE,
    0,
    60,
    'He hands her the keys, but whispers a chilling rule.',
    'published'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_ceo_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_ceo_wife'),
    2,
    'Clifton Sunset',
    'An unexpected reporter appears outside the penthouse.',
    78,
    FALSE,
    5,
    68,
    'Will Sandile kiss her for the camera or break the deal?',
    'published'
),
-- Umembeso Episode 1
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_um_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_umembeso'),
    1,
    'The Stolen Talisman',
    'The royal heirloom disappears minutes before the ceremonial procession.',
    84,
    TRUE,
    0,
    74,
    'The elder points to the bride''s mother.',
    'published'
),
-- Lagos Confidential Episode 1
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_lc_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_lagos_confidential'),
    1,
    'The 60-Second Leak',
    'Tunde bypasses the firewall as security breaches the server room door.',
    88,
    TRUE,
    0,
    78,
    'The upload progress bar hits 99% as the power cuts.',
    'published'
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    duration_seconds = EXCLUDED.duration_seconds,
    status = EXCLUDED.status;

-- ----------------------------------------------------------------------------
-- STEP 5: DECOUPLED MEDIA ASSETS (REFERENCING LOCAL VERIFIED STATIC ASSETS)
-- ----------------------------------------------------------------------------

INSERT INTO public.media_assets (
    id, episode_id, storage_key, master_video_url, thumbnail_url, duration_seconds, transcoding_status
) VALUES
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_bt_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_1'),
    'videos/ocean_waves.mp4',
    '/videos/ocean_waves.mp4',
    '/posters/blood_ties.jpg',
    68.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_bt_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_2'),
    'videos/sample_drama.mp4',
    '/videos/sample_drama.mp4',
    '/posters/blood_ties.jpg',
    74.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_bt_3'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_3'),
    'videos/flower_bloom.mp4',
    '/videos/flower_bloom.mp4',
    '/posters/blood_ties.jpg',
    82.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_qj_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_qj_1'),
    'videos/ocean_waves.mp4',
    '/videos/ocean_waves.mp4',
    '/posters/queen_of_jozi.jpg',
    75.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_qj_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_qj_2'),
    'videos/sample_drama.mp4',
    '/videos/sample_drama.mp4',
    '/posters/queen_of_jozi.jpg',
    80.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_ceo_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_ceo_1'),
    'videos/welele_placeholder.mp4',
    '/videos/welele_placeholder.mp4',
    '/posters/ceo_secret_wife.jpg',
    70.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_ceo_2'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_ceo_2'),
    'videos/sample_drama.mp4',
    '/videos/sample_drama.mp4',
    '/posters/ceo_secret_wife.jpg',
    78.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_um_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_um_1'),
    'videos/Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4',
    '/videos/Isibusiso_Ep01_The_Midnight_Sovereign_v1.mp4',
    '/posters/umembeso.jpg',
    84.0,
    'READY'
),
(
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.asset_lc_1'),
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_lc_1'),
    'videos/sample_drama.mp4',
    '/videos/sample_drama.mp4',
    '/posters/lagos_confidential.jpg',
    88.0,
    'READY'
)
ON CONFLICT (id) DO UPDATE SET
    master_video_url = EXCLUDED.master_video_url,
    thumbnail_url = EXCLUDED.thumbnail_url;

-- ----------------------------------------------------------------------------
-- STEP 6: SEED CANONICAL EXPERIENCE LAYOUT MANIFEST (HOME)
-- ----------------------------------------------------------------------------

INSERT INTO public.experience_layouts (
    id, page_id, version, status, manifest_json, published_at, updated_at
) VALUES (
    uuid_generate_v5(uuid_ns_dns(), 'welele.media.layout_home'),
    'home',
    '1.0.0',
    'published',
    jsonb_build_object(
        'page_id', 'home',
        'version', '1.0.0',
        'status', 'published',
        'published_at', '2026-08-01T00:00:00Z',
        'updated_at', NOW(),
        'meta', jsonb_build_object(
            'title', 'Welele™ | Short African Dramas',
            'theme', 'dark_gold_glow',
            'description', 'Stream high-octane vertical micro-dramas produced across South Africa, Nigeria, and Ghana.'
        ),
        'brand_config', jsonb_build_object(
            'play_brand_ident', true,
            'brand_ident_url', '/api/storage/stream/videos/welele_ident_v2.mp4',
            'brand_ident_duration', 5.2,
            'ident_frequency', 5,
            'failsafe_buffer', 1.0,
            'experience_rule', 'standard',
            'asset', jsonb_build_object(
                'id', 'welele-brand-ident-v2',
                'asset_type', 'sonic_visual_ident',
                'name', 'Welele Sonic Visual Ident v2',
                'url', '/api/storage/stream/videos/welele_ident_v2.mp4',
                'version', 2,
                'active', true,
                'duration', 5.2
            )
        ),
        'sections', jsonb_build_array(
            jsonb_build_object(
                'section_id', 'sec_hero_home',
                'type', 'HERO_CAROUSEL',
                'is_visible', true,
                'order', 0,
                'config', jsonb_build_object(
                    'auto_play_seconds', 8,
                    'aspect_ratio', '9:16',
                    'card_size', 'large',
                    'show_rank_numbers', false
                ),
                'items', jsonb_build_array(
                    jsonb_build_object(
                        'slot_id', 'slot_hero_1',
                        'content_type', 'series',
                        'content_id', uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties')::text,
                        'badge', 'SPOTLIGHT ORIGINAL',
                        'cta_text', 'Watch Now',
                        'cta_action', 'STREAM_EPISODE',
                        'cta_target', uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_1')::text,
                        'artwork_overrides', jsonb_build_object(
                            'mobile_9_16', '/posters/blood_ties.jpg',
                            'desktop_16_9', '/banners/blood_ties_banner.jpg',
                            'trailer_video_url', '/videos/welele_placeholder.mp4'
                        ),
                        'is_active', true
                    ),
                    jsonb_build_object(
                        'slot_id', 'slot_hero_2',
                        'content_type', 'series',
                        'content_id', uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_queen_of_jozi')::text,
                        'badge', 'TOP RATED #1',
                        'cta_text', 'Watch Now',
                        'cta_action', 'STREAM_EPISODE',
                        'cta_target', uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_qj_1')::text,
                        'artwork_overrides', jsonb_build_object(
                            'mobile_9_16', '/posters/queen_of_jozi.jpg',
                            'desktop_16_9', '/banners/queen_of_jozi_banner.jpg',
                            'trailer_video_url', '/videos/ocean_waves.mp4'
                        ),
                        'is_active', true
                    ),
                    jsonb_build_object(
                        'slot_id', 'slot_hero_3',
                        'content_type', 'series',
                        'content_id', uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_ceo_wife')::text,
                        'badge', 'ROMANCE HIT',
                        'cta_text', 'Watch Now',
                        'cta_action', 'STREAM_EPISODE',
                        'cta_target', uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_ceo_1')::text,
                        'artwork_overrides', jsonb_build_object(
                            'mobile_9_16', '/posters/ceo_secret_wife.jpg',
                            'desktop_16_9', '/banners/ceo_secret_wife_banner.jpg',
                            'trailer_video_url', '/videos/welele_placeholder.mp4'
                        ),
                        'is_active', true
                    )
                )
            ),
            jsonb_build_object(
                'section_id', 'sec_spotlight_editorial',
                'type', 'EDITORIAL_SPOTLIGHT',
                'title', 'Editor''s Pick of the Week ⭐',
                'subtitle', 'Curated by Welele Editorial Desk',
                'is_visible', true,
                'order', 1,
                'config', jsonb_build_object('aspect_ratio', '16:9'),
                'items', jsonb_build_array(
                    jsonb_build_object(
                        'slot_id', 'slot_spotlight_1',
                        'content_type', 'series',
                        'content_id', uuid_generate_v5(uuid_ns_dns(), 'welele.media.story_blood_ties')::text,
                        'badge', 'WELELE ORIGINAL',
                        'headline_override', 'Blood Ties: The Dynasty That Redefined Jozi Drama',
                        'subheadline_override', 'Director Zola Dlamini delivers a masterclass in 90-second cliffhanger storytelling.',
                        'cta_text', 'Watch From Episode 1',
                        'cta_action', 'STREAM_EPISODE',
                        'cta_target', uuid_generate_v5(uuid_ns_dns(), 'welele.media.ep_bt_1')::text,
                        'is_active', true
                    )
                )
            )
        )
    ),
    NOW(),
    NOW()
) ON CONFLICT (page_id, status) DO UPDATE SET
    manifest_json = EXCLUDED.manifest_json,
    updated_at = NOW();

COMMIT;
