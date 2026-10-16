"""
Welele Media™ — Series & Media Catalog Repository (GAP-001 & GAP-006)
Normalized relational data access for Series, Episodes, decoupled Media Assets, and Moderation Lifecycle.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from config import settings
from .base_repository import BaseRepository

logger = logging.getLogger("welele.series")

def to_uuid(name: str) -> str:
    """Deterministically maps any string identifier into a valid PostgreSQL UUID5."""
    try:
        uuid.UUID(str(name))
        return str(name)
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"welele.media.{name}"))


KNOWN_SERIES_SLUGS = [
    "story_blood_ties",
    "story_queen_of_jozi",
    "story_ceo_wife",
    "story_umembeso",
    "story_lagos_confidential",
    "story_zulu_love",
    "story_broken_vows",
    "story_the_hustlers",
    "story_campus_royals",
    "story_barrio_billionaire",
    "story_heist_game",
    "story_sandton_nights",
    "story_durban_heat",
    "story_the_spaza_king",
]
SERIES_UUID_TO_SLUG = {to_uuid(slug): slug for slug in KNOWN_SERIES_SLUGS}

KNOWN_EPISODE_SLUGS = [
    "ep_bt_1", "ep_bt_2", "ep_bt_3",
    "ep_qj_1", "ep_qj_2",
    "ep_ceo_1", "ep_ceo_2",
    "ep_um_1", "ep_lc_1", "ep_zl_1", "ep_bv_1", "ep_th_1",
    "ep_cr_1", "ep_bb_1", "ep_hg_1", "ep_sn_1", "ep_dh_1", "ep_sk_1"
]
EPISODE_UUID_TO_SLUG = {to_uuid(ep_slug): ep_slug for ep_slug in KNOWN_EPISODE_SLUGS}


class SeriesRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        if not self.local_get("series"):
            self.seed_if_missing()

    def seed_if_missing(self):
        # Canonical catalog with all 14 series synchronized across Creator, Admin, and Viewer
        canonical_series = [
            # 1. Blood Ties
            {
                "id": "story_blood_ties",
                "ip_id": "ip_blood_ties",
                "season_number": 1,
                "title": "Blood Ties",
                "tagline": "Two powerful families tied by blood, torn apart by greed.",
                "synopsis": "When the matriarch of the mighty Khumalo dynasty collapses at the annual Sandton gala, a hidden will surfaces that names a secret daughter as the sole heir. Betrayal, boardroom warfare, and family secrets collide in Johannesburg's most dramatic showdown.",
                "cover_image": "/banners/blood_ties_banner.jpg",
                "vertical_poster": "/posters/blood_ties.jpg",
                "genre": "Drama • Family • Betrayal",
                "rating": 4.98,
                "total_episodes": 3,
                "free_episodes": 2,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "isiXhosa", "English", "Afrikaans", "Sesotho"],
                "tags": ["#BloodTies", "#MzansiDrama", "#BillionaireDynasty", "#Cliffhanger", "#WeleleOriginal"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 2. Queen of Jozi
            {
                "id": "story_queen_of_jozi",
                "ip_id": "ip_queen_of_jozi",
                "season_number": 1,
                "title": "Queen of Jozi",
                "tagline": "One woman's ruthless rise to the top of Johannesburg's underworld.",
                "synopsis": "When her husband's gold syndication empire falls into rival hands, Nina Khumalo steps from the shadows to reclaim the throne in Sandton. Boardroom power plays meet street warfare in South Africa's most anticipated micro-drama.",
                "cover_image": "/banners/queen_of_jozi_banner.jpg",
                "vertical_poster": "/posters/queen_of_jozi.jpg",
                "genre": "Crime • Empire • Dynasty",
                "rating": 4.99,
                "total_episodes": 2,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "isiXhosa", "English", "Afrikaans", "Sesotho"],
                "tags": ["#QueenOfJozi", "#SandtonDynasty", "#MzansiCrime", "#WeleleSpotlight", "#Original"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 3. The CEO's Secret Wife
            {
                "id": "story_ceo_wife",
                "ip_id": "ip_ceo_wife",
                "season_number": 1,
                "title": "The CEO's Secret Wife",
                "tagline": "A fake marriage. A hidden identity. A love that could ruin everything.",
                "synopsis": "To save her family's heritage estate from foreclosure, Zandile agrees to a 1-year secret contract marriage with Sandile Ndlovu, Johannesburg's most feared billionaire CEO. But behind closed doors in his Clifton penthouse, cold business turns into undeniable, forbidden passion.",
                "cover_image": "/banners/ceo_secret_wife_banner.jpg",
                "vertical_poster": "/posters/ceo_secret_wife.jpg",
                "genre": "Romance • Contract Marriage",
                "rating": 4.96,
                "total_episodes": 2,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_amaka",
                "creator_name": "Amaka Okafor",
                "creator_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "isiZulu", "Swahili", "French", "Pidgin"],
                "tags": ["#SecretWife", "#BillionaireRomance", "#ContractMarriage", "#SandtonLove", "#Trending"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 4. Umembeso: Royal Secrets
            {
                "id": "story_umembeso",
                "ip_id": "ip_umembeso",
                "season_number": 1,
                "title": "Umembeso: Royal Secrets",
                "tagline": "A traditional royal wedding where every gift carries a deadly secret.",
                "synopsis": "During the opulent royal dowry ceremony in KwaZulu-Natal, an ancient family talisman is stolen, threatening to expose a thirty-year bloodline deception before the vows are sealed.",
                "cover_image": "/banners/umembeso_banner.jpg",
                "vertical_poster": "/posters/umembeso.jpg",
                "genre": "Romance • Royal • Mystery",
                "rating": 4.94,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "isiXhosa", "English", "Afrikaans"],
                "tags": ["#Umembeso", "#RoyalSecrets", "#ZuluTradition", "#MzansiRomance"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 5. Lagos Confidential
            {
                "id": "story_lagos_confidential",
                "ip_id": "ip_lagos_confidential",
                "season_number": 1,
                "title": "Lagos Confidential",
                "tagline": "High-tech corporate espionage across Victoria Island.",
                "synopsis": "A brilliant forensic hacker uncovers a multi-billion naira offshore conduit on the eve of West Africa's biggest telecom merger. With assassins on his trail, 60 seconds is all he has to leak the truth.",
                "cover_image": "/banners/lagos_confidential_banner.jpg",
                "vertical_poster": "/posters/lagos_confidential.jpg",
                "genre": "Action • Tech • Thriller",
                "rating": 4.96,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_amaka",
                "creator_name": "Amaka Okafor",
                "creator_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "Pidgin", "Yoruba", "French"],
                "tags": ["#LagosConfidential", "#NaijaTech", "#VictoriaIsland", "#CyberThriller"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 6. Zulu Love Story
            {
                "id": "story_zulu_love",
                "ip_id": "ip_zulu_love",
                "season_number": 1,
                "title": "Zulu Love Story",
                "tagline": "Two worlds. One unforgettable royal heartbeat.",
                "synopsis": "Prince Sipho of the KwaZulu royal line meets Nandi, an edgy streetwear designer from Braamfontein. When ancestral duty calls him home to an arranged marriage, will he choose the crown or true love?",
                "cover_image": "/posters/zulu_love_story.jpg",
                "vertical_poster": "/posters/zulu_love_story.jpg",
                "genre": "Romance • Mzansi Originals",
                "rating": 4.97,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "isiXhosa", "English", "Afrikaans"],
                "tags": ["#ZuluLove", "#RoyalRomance", "#DurbanToJozi", "#MzansiMagic"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 7. Broken Vows
            {
                "id": "story_broken_vows",
                "ip_id": "ip_broken_vows",
                "season_number": 1,
                "title": "Broken Vows",
                "tagline": "Every secret comes with a price in high society.",
                "synopsis": "During an ultra-glamorous 10th-anniversary ball in Sandton, an anonymous caller plays a secret recording that exposes betrayal, money laundering, and an unspoken pact from 2014.",
                "cover_image": "/posters/broken_vows.jpg",
                "vertical_poster": "/posters/broken_vows.jpg",
                "genre": "Drama • Mystery • Thriller",
                "rating": 4.92,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "isiXhosa", "isiZulu", "Afrikaans"],
                "tags": ["#BrokenVows", "#SandtonScandal", "#Betrayal", "#Cliffhanger"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 8. The Hustlers
            {
                "id": "story_the_hustlers",
                "ip_id": "ip_the_hustlers",
                "season_number": 1,
                "title": "The Hustlers",
                "tagline": "From Soweto streets to Sandton skyscrapers.",
                "synopsis": "Three ambitious street hustlers from Soweto execute a daring high-tech takeover of Johannesburg's biggest private gold bullion syndicate.",
                "cover_image": "/posters/the_hustlers.jpg",
                "vertical_poster": "/posters/the_hustlers.jpg",
                "genre": "Crime • Action • Thriller",
                "rating": 4.95,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_kofi",
                "creator_name": "Kofi Mensah",
                "creator_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "English", "Sesotho", "Afrikaans"],
                "tags": ["#TheHustlers", "#JoziUnderground", "#Action", "#SowetoToSandton"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 9. Campus Royals
            {
                "id": "story_campus_royals",
                "ip_id": "ip_campus_royals",
                "season_number": 1,
                "title": "Campus Royals",
                "tagline": "Privilege, power, and secret society scandals.",
                "synopsis": "At an elite Cape Town university, the secret student council decides who rises and who falls. A fearless scholarship student vows to tear down the dynasty from within.",
                "cover_image": "/posters/campus_royals.jpg",
                "vertical_poster": "/posters/campus_royals.jpg",
                "genre": "Drama • Youth • Ambition",
                "rating": 4.88,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_wanjiku",
                "creator_name": "Wanjiku Mwangi",
                "creator_avatar": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "isiXhosa", "Afrikaans"],
                "tags": ["#CampusRoyals", "#UCTDynasty", "#SecretSociety", "#Drama"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 10. Barrio Billionaire
            {
                "id": "story_barrio_billionaire",
                "ip_id": "ip_barrio_billionaire",
                "season_number": 1,
                "title": "Barrio Billionaire",
                "tagline": "Built from nothing. Feared by everyone.",
                "synopsis": "From a tiny spaza shop in Soweto to commanding Africa's most valuable fintech empire, Thabo faces old-money families trying to take his company down.",
                "cover_image": "/posters/barrio_billionaire.jpg",
                "vertical_poster": "/posters/barrio_billionaire.jpg",
                "genre": "Drama • Dynasty • Tech",
                "rating": 4.94,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "English", "Sesotho"],
                "tags": ["#BarrioBillionaire", "#FintechHustle", "#JoziPower", "#Dynasty"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 11. Heist Game
            {
                "id": "story_heist_game",
                "ip_id": "ip_heist_game",
                "season_number": 1,
                "title": "Heist Game",
                "tagline": "One night. Zero room for error.",
                "synopsis": "An elite crew of cybersecurity prodigies and street specialists plan an impossible raid on a subterranean Cape Town vault during the New Year's Eve gala.",
                "cover_image": "/posters/heist_game.jpg",
                "vertical_poster": "/posters/heist_game.jpg",
                "genre": "Crime • Action • Thriller",
                "rating": 4.91,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_kofi",
                "creator_name": "Kofi Mensah",
                "creator_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "Afrikaans", "isiXhosa"],
                "tags": ["#HeistGame", "#CapeTownAction", "#HighStakes", "#Thriller"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 12. Sandton Nights
            {
                "id": "story_sandton_nights",
                "ip_id": "ip_sandton_nights",
                "season_number": 1,
                "title": "Sandton Nights",
                "tagline": "High stakes, high society, and dangerous promises under the Jozi skyline.",
                "synopsis": "An undercover forensic investigator infiltrates an exclusive VIP poker circuit in Sandton to expose how offshore billions are moved behind crystal chandeliers.",
                "cover_image": "/banners/queen_of_jozi_banner.jpg",
                "vertical_poster": "/posters/queen_of_jozi.jpg",
                "genre": "Drama • Mystery • Glamour",
                "rating": 4.93,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_zola",
                "creator_name": "Zola Dlamini",
                "creator_avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["English", "isiZulu", "isiXhosa", "Afrikaans"],
                "tags": ["#SandtonNights", "#JoziGlamour", "#HighStakes", "#MzansiOriginal"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 13. Durban Heat
            {
                "id": "story_durban_heat",
                "ip_id": "ip_durban_heat",
                "season_number": 1,
                "title": "Durban Heat",
                "tagline": "Under the golden sun, the street race for justice begins.",
                "synopsis": "Two estranged brothers on opposite sides of the law collide when Durban's underground shipping lanes become the battleground for a missing shipment of uncut gemstones.",
                "cover_image": "/banners/lagos_confidential_banner.jpg",
                "vertical_poster": "/posters/the_hustlers.jpg",
                "genre": "Action • Crime • Fast Pace",
                "rating": 4.89,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_kofi",
                "creator_name": "Kofi Mensah",
                "creator_avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "English", "Afrikaans"],
                "tags": ["#DurbanHeat", "#ActionThriller", "#CoastalCrime", "#WeleleOriginal"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            # 14. The Spaza King
            {
                "id": "story_the_spaza_king",
                "ip_id": "ip_the_spaza_king",
                "season_number": 1,
                "title": "The Spaza King",
                "tagline": "From a corner container in Soweto to a township retail empire.",
                "synopsis": "Armed with grit, humor, and an unstoppable delivery drone experiment, Bongani revolutionizes township commerce while outsmarting loan sharks and corporate retail giants.",
                "cover_image": "/banners/umembeso_banner.jpg",
                "vertical_poster": "/posters/barrio_billionaire.jpg",
                "genre": "Comedy • Township • Hustle",
                "rating": 4.95,
                "total_episodes": 1,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": True,
                "creator_id": "creator_wanjiku",
                "creator_name": "Wanjiku Mwangi",
                "creator_avatar": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?auto=format&fit=crop&w=400&q=80",
                "available_languages": ["isiZulu", "English", "Sesotho", "isiXhosa"],
                "tags": ["#TheSpazaKing", "#TownshipHustle", "#MzansiComedy", "#Heartwarming"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # Seed canonical episodes
        episodes_data = [
            # 1. Blood Ties
            {
                "id": "ep_bt_1",
                "series_id": "story_blood_ties",
                "story_package_id": "sfp_bt_01",
                "episode_number": 1,
                "title": "The Golden Will",
                "synopsis": "The unsealed court document triggers panic in the boardroom.",
                "duration_seconds": 68,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 58,
                "cliffhanger_hook": "Who authorized her DNA test before the funeral?",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "ep_bt_2",
                "series_id": "story_blood_ties",
                "story_package_id": "sfp_bt_01",
                "episode_number": 2,
                "title": "Midnight at the Rank",
                "synopsis": "Sipho confronts the convoy blocking the workshop.",
                "duration_seconds": 74,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 64,
                "cliffhanger_hook": "Will Bra Oupa draw his weapon first?",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "ep_bt_3",
                "series_id": "story_blood_ties",
                "story_package_id": "sfp_bt_01",
                "episode_number": 3,
                "title": "The Cartel Route",
                "synopsis": "The hidden ledger exposes illicit transit lines across Gauteng.",
                "duration_seconds": 82,
                "is_free": False,
                "coin_price": 5,
                "cliffhanger_time_seconds": 72,
                "cliffhanger_hook": "The security camera reveals the traitor in the family.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 2. Queen of Jozi
            {
                "id": "ep_qj_1",
                "series_id": "story_queen_of_jozi",
                "story_package_id": "sfp_qj_01",
                "episode_number": 1,
                "title": "The Golden Takeover",
                "synopsis": "Nina walks into the Sandton boardroom as the rival syndicate votes to liquidate her family's mining assets.",
                "duration_seconds": 84,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 74,
                "cliffhanger_hook": "Who signed over 51% of the shares before sunrise?",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "ep_qj_2",
                "series_id": "story_queen_of_jozi",
                "story_package_id": "sfp_qj_01",
                "episode_number": 2,
                "title": "Midnight in Rosebank",
                "synopsis": "A tense standoff at the penthouse reveals an undercover mole inside the private security team.",
                "duration_seconds": 79,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 69,
                "cliffhanger_hook": "The security feed was hacked from inside the room.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 3. The CEO's Secret Wife
            {
                "id": "ep_ceo_1",
                "series_id": "story_ceo_wife",
                "story_package_id": "sfp_ceo_01",
                "episode_number": 1,
                "title": "The Proposal",
                "synopsis": "Sandile presents an offer Zandile cannot refuse: 50 million Rand and a ring, with strictly no feelings attached.",
                "duration_seconds": 62,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 54,
                "cliffhanger_hook": "Sign before the clock strikes midnight.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "ep_ceo_2",
                "series_id": "story_ceo_wife",
                "story_package_id": "sfp_ceo_01",
                "episode_number": 2,
                "title": "The Contract",
                "synopsis": "Clause 7: You must act as the devoted wife in front of the board and media at all costs.",
                "duration_seconds": 60,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 52,
                "cliffhanger_hook": "Who leaked our marriage certificate to the press?",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 4. Umembeso: Royal Secrets
            {
                "id": "ep_um_1",
                "series_id": "story_umembeso",
                "story_package_id": "sfp_um_01",
                "episode_number": 1,
                "title": "The Stolen Talisman",
                "synopsis": "The royal elders open the sacred chest to discover the ancestral spearhead has been replaced with a warning note.",
                "duration_seconds": 78,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 68,
                "cliffhanger_hook": "The note is written in the King's own handwriting.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 5. Lagos Confidential
            {
                "id": "ep_lc_1",
                "series_id": "story_lagos_confidential",
                "story_package_id": "sfp_lc_01",
                "episode_number": 1,
                "title": "The Decryption Key",
                "synopsis": "A rooftop server room in Ikoyi is breached 15 minutes before the boardroom press conference.",
                "duration_seconds": 82,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 72,
                "cliffhanger_hook": "The server just self-destructed and transmitted the coordinates.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 6. Zulu Love Story
            {
                "id": "ep_zl_1",
                "series_id": "story_zulu_love",
                "story_package_id": "sfp_zl_01",
                "episode_number": 1,
                "title": "Eyes in Braamfontein",
                "synopsis": "A pop-up fashion show in Johannesburg brings two completely different souls face to face.",
                "duration_seconds": 74,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 64,
                "cliffhanger_hook": "He didn't mention he was a prince.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 7. Broken Vows
            {
                "id": "ep_bv_1",
                "series_id": "story_broken_vows",
                "story_package_id": "sfp_bv_01",
                "episode_number": 1,
                "title": "The Anniversary Toast",
                "synopsis": "A crystal champagne glass shatters as the projector reveals evidence no one was meant to see.",
                "duration_seconds": 76,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 66,
                "cliffhanger_hook": "Who switched the USB drive at the podium?",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 8. The Hustlers
            {
                "id": "ep_th_1",
                "series_id": "story_the_hustlers",
                "story_package_id": "sfp_th_01",
                "episode_number": 1,
                "title": "The Gold Blueprint",
                "synopsis": "A secret meeting in Maboneng uncovers the security codes to the Carlton Centre underground vault.",
                "duration_seconds": 80,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 70,
                "cliffhanger_hook": "The alarm just triggered 3 minutes early.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 9. Campus Royals
            {
                "id": "ep_cr_1",
                "series_id": "story_campus_royals",
                "story_package_id": "sfp_cr_01",
                "episode_number": 1,
                "title": "The Induction",
                "synopsis": "The midnight bell rings at Jameson Hall as the masked council initiates the chosen few.",
                "duration_seconds": 75,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 65,
                "cliffhanger_hook": "She refused to take the loyalty oath.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 10. Barrio Billionaire
            {
                "id": "ep_bb_1",
                "series_id": "story_barrio_billionaire",
                "story_package_id": "sfp_bb_01",
                "episode_number": 1,
                "title": "The Hostile Takeover",
                "synopsis": "Sandton investment bankers laugh at Thabo's valuation—until his app clears 10 million transactions overnight.",
                "duration_seconds": 78,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 68,
                "cliffhanger_hook": "We own 51% of your bank as of 9 AM.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 11. Heist Game
            {
                "id": "ep_hg_1",
                "series_id": "story_heist_game",
                "story_package_id": "sfp_hg_01",
                "episode_number": 1,
                "title": "The Countdown Begins",
                "synopsis": "The laser grid trips in the penthouse, giving the crew exactly 60 seconds to bypass the biometric vault.",
                "duration_seconds": 80,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 70,
                "cliffhanger_hook": "The lasers didn't shut down.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 12. Sandton Nights
            {
                "id": "ep_sn_1",
                "series_id": "story_sandton_nights",
                "story_package_id": "sfp_sn_01",
                "episode_number": 1,
                "title": "The Platinum Chip",
                "synopsis": "A single hand of high-stakes poker reveals who is secretly controlling the mining concessions.",
                "duration_seconds": 76,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 67,
                "cliffhanger_hook": "Every chip at the table has an RFID tracer.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 13. Durban Heat
            {
                "id": "ep_dh_1",
                "series_id": "story_durban_heat",
                "story_package_id": "sfp_dh_01",
                "episode_number": 1,
                "title": "Harbor Gridlock",
                "synopsis": "A high-speed pursuit through the Durban harbor terminals traps the team in container sector 4.",
                "duration_seconds": 82,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 73,
                "cliffhanger_hook": "The crane controls were bypassed remotely.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            # 14. The Spaza King
            {
                "id": "ep_sk_1",
                "series_id": "story_the_spaza_king",
                "story_package_id": "sfp_sk_01",
                "episode_number": 1,
                "title": "The 3-Minute Delivery",
                "synopsis": "Bongani launches Soweto's fastest bunny chow delivery on an electric scooter, catching the eye of a Sandton venture capitalist.",
                "duration_seconds": 70,
                "is_free": True,
                "coin_price": 0,
                "cliffhanger_time_seconds": 60,
                "cliffhanger_hook": "The investor just offered 5 million on the spot.",
                "status": "published",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]

        # 1. Idempotent Series Insertion
        existing_series = self.local_get("series")
        existing_series_ids = {s.get("id") for s in existing_series if s.get("id")}
        for s in canonical_series:
            if s["id"] not in existing_series_ids:
                self.local_insert("series", s)

        # 2. Idempotent Episodes Insertion
        existing_episodes = self.local_get("episodes")
        existing_ep_ids = {e.get("id") for e in existing_episodes if e.get("id")}
        for ep in episodes_data:
            if ep["id"] not in existing_ep_ids:
                self.local_insert("episodes", ep)

        # 3. Idempotent Media Assets Insertion
        sample_videos = [
            "/videos/ocean_waves.mp4",
            "/videos/sample_drama.mp4",
            "/videos/flower_bloom.mp4",
            "/videos/jellyfish.mp4",
            "/videos/sintel.mp4",
            "/videos/big_buck.mp4",
        ]
        existing_media = self.local_get("media_assets")
        existing_media_ids = {m.get("id") for m in existing_media if m.get("id")}
        series_poster_map = {s["id"]: s.get("vertical_poster", "/posters/blood_ties.jpg") for s in canonical_series}
        for idx, ep in enumerate(episodes_data):
            m_id = f"media_{ep['id']}"
            if m_id not in existing_media_ids:
                s_poster = series_poster_map.get(ep["series_id"], "/posters/blood_ties.jpg")
                v_url = sample_videos[idx % len(sample_videos)]
                self.local_insert("media_assets", {
                    "id": m_id,
                    "episode_id": ep["id"],
                    "storage_key": f"masters/{ep['series_id']}/{ep['id']}.mp4",
                    "master_video_url": v_url,
                    "hls_master_manifest_url": f"https://cdn.welele.media/hls/{ep['series_id']}/{ep['id']}/master.m3u8",
                    "thumbnail_url": s_poster,
                    "duration_seconds": ep["duration_seconds"],
                    "transcoding_status": "READY",
                    "renditions_json": {
                        "1080p": f"https://cdn.welele.media/hls/{ep['series_id']}/{ep['id']}/1080p.m3u8",
                        "720p": f"https://cdn.welele.media/hls/{ep['series_id']}/{ep['id']}/720p.m3u8",
                        "480p": f"https://cdn.welele.media/hls/{ep['series_id']}/{ep['id']}/480p.m3u8"
                    },
                    "subtitles_vtt_json": {
                        "isiZulu": f"https://cdn.welele.media/subs/{ep['series_id']}/{ep['id']}_zu.vtt",
                        "English": f"https://cdn.welele.media/subs/{ep['series_id']}/{ep['id']}_en.vtt"
                    },
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })

        # 4. Internal Test Proving Dataset — JELLYFISH (Workstream 1 & 2)
        # CRITICAL CONTENT RULE: Used exclusively for machine proving; NEVER exposed in public viewer catalog
        internal_test_series_id = "series_internal_jellyfish_test"
        if internal_test_series_id not in existing_series_ids:
            self.local_insert("series", {
                "id": internal_test_series_id,
                "ip_id": "ip_internal_jellyfish_test",
                "season_number": 1,
                "title": "Internal Machine Proving (Jellyfish)",
                "tagline": "Internal test suite dataset. Not for public viewer distribution.",
                "synopsis": "Automated pipeline and machine proving fixture using vertical Jellyfish master assets.",
                "cover_image": "/posters/jellyfish_test.jpg",
                "vertical_poster": "/posters/jellyfish_test.jpg",
                "genre": "System Proving",
                "rating": 5.0,
                "total_episodes": 2,
                "free_episodes": 1,
                "coin_price_per_episode": 5,
                "is_published": False,
                "is_internal_test": True,
                "lifecycle_state": "INTERNAL_TEST",
                "creator_id": "system_tester",
                "creator_name": "Welele QA Engine",
                "creator_avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
                "available_languages": ["English"],
                "tags": ["#InternalTest", "#JellyfishProving"],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

        if "ep_jellyfish_1" not in existing_ep_ids:
            self.local_insert("episodes", {
                "id": "ep_jellyfish_1",
                "series_id": internal_test_series_id,
                "episode_number": 1,
                "title": "Jellyfish Proving Flight 1",
                "synopsis": "Free episode proving vertical playback, telemetry milestone guards, and progression.",
                "duration_seconds": 30,
                "is_free": True,
                "coin_price": 0,
                "unlock_price_coins": 0,
                "cliffhanger_time_seconds": 25,
                "cliffhanger_hook": "Testing automated milestone dispatch and progression hook.",
                "status": "published",
                "is_internal_test": True,
                "lifecycle_state": "INTERNAL_TEST",
                "readiness_state": "PRODUCTION_READY",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.local_insert("media_assets", {
                "id": "media_ep_jellyfish_1",
                "episode_id": "ep_jellyfish_1",
                "storage_key": "masters/internal_test/jellyfish.mp4",
                "master_video_url": "/videos/jellyfish.mp4",
                "hls_master_manifest_url": "https://cdn.welele.media/hls/internal_test/jellyfish/master.m3u8",
                "thumbnail_url": "/posters/jellyfish_test.jpg",
                "duration_seconds": 30,
                "transcoding_status": "READY",
                "is_internal_test": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

        if "ep_jellyfish_2" not in existing_ep_ids:
            self.local_insert("episodes", {
                "id": "ep_jellyfish_2",
                "series_id": internal_test_series_id,
                "episode_number": 2,
                "title": "Jellyfish Proving Flight 2 (Locked)",
                "synopsis": "Locked episode proving value proposition, payment rail, ledger entitlement, and unlock.",
                "duration_seconds": 30,
                "is_free": False,
                "coin_price": 5,
                "unlock_price_coins": 5,
                "cliffhanger_time_seconds": 25,
                "cliffhanger_hook": "Testing locked paywall state and entitlement unlock.",
                "status": "published",
                "is_internal_test": True,
                "lifecycle_state": "INTERNAL_TEST",
                "readiness_state": "PRODUCTION_READY",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.local_insert("media_assets", {
                "id": "media_ep_jellyfish_2",
                "episode_id": "ep_jellyfish_2",
                "storage_key": "masters/internal_test/jellyfish.mp4",
                "master_video_url": "/videos/jellyfish.mp4",
                "hls_master_manifest_url": "https://cdn.welele.media/hls/internal_test/jellyfish/master.m3u8",
                "thumbnail_url": "/posters/jellyfish_test.jpg",
                "duration_seconds": 30,
                "transcoding_status": "READY",
                "is_internal_test": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })


    @property
    def is_degraded(self) -> bool:
        return getattr(self, "_is_degraded", False)

    @property
    def degraded_reason(self) -> Optional[str]:
        return getattr(self, "_degraded_reason", None)

    @property
    def catalog_source(self) -> str:
        if self.is_degraded:
            return "local_fallback (DEGRADED)"
        if self.is_live:
            return "supabase_postgres"
        return "offline_fixtures"

    def _fetch_live_catalog(self) -> Optional[tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]]:
        """Safely queries authoritative PostgreSQL tables in Supabase staging/production."""
        if not self.is_live:
            return None
        try:
            s_res = self.get_table("series").select("*").execute()
            if not s_res or not s_res.data:
                if settings.IS_PRODUCTION_OR_STAGING:
                    logger.warning("[SeriesRepository:DEGRADED] Database connected but public.series table has 0 rows. Serving fallback.")
                    self._is_degraded = True
                    self._degraded_reason = "Empty database table: public.series has 0 rows"
                return None
            
            ep_res = self.get_table("episodes").select("*").execute()
            episodes = ep_res.data if ep_res and ep_res.data else []

            m_res = self.get_table("media_assets").select("*").execute()
            media = m_res.data if m_res and m_res.data else []

            self._is_degraded = False
            self._degraded_reason = None
            return (s_res.data, episodes, media)
        except Exception as e:
            logger.error(f"[SeriesRepository:DEGRADED] Remote Supabase catalogue query failed: {e}. Serving fallback.")
            if settings.IS_PRODUCTION_OR_STAGING:
                self._is_degraded = True
                self._degraded_reason = f"Database read exception: {str(e)}"
            return None

    def list_feed(self, genre: Optional[str] = None, language: Optional[str] = None) -> List[Dict[str, Any]]:
        live_data = self._fetch_live_catalog()
        if live_data:
            all_series, all_episodes, all_media = live_data
        else:
            all_series = self.local_get("series") or []
            all_episodes = self.local_get("episodes") or []
            all_media = self.local_get("media_assets") or []

        # Build media lookup by episode_id (support both string/UUID and slug)
        media_map = {}
        for m in all_media:
            ep_id = str(m.get("episode_id", ""))
            if ep_id:
                media_map[ep_id] = m
                slug = EPISODE_UUID_TO_SLUG.get(ep_id)
                if slug:
                    media_map[slug] = m

        result = []
        for s in all_series:
            # STRICT PUBLIC BOUNDARY: Exclude unpublished series and internal test datasets
            if not s.get("is_published", True) or s.get("is_internal_test", False) or s.get("lifecycle_state") == "INTERNAL_TEST":
                continue
            if genre and s.get("genre") != genre:
                continue

            s_copy = dict(s)
            s_id = str(s.get("id", ""))
            s_slug = s.get("slug") or SERIES_UUID_TO_SLUG.get(s_id)
            if s_slug:
                s_copy["slug"] = s_slug

            # Ensure creator metadata is populated for display
            if not s_copy.get("creator_name"):
                s_copy["creator_name"] = "Zola Dlamini" if ("blood" in str(s_copy.get("title", "")).lower() or "queen" in str(s_copy.get("title", "")).lower()) else "Amaka Okafor"
            if not s_copy.get("creator_id"):
                s_copy["creator_id"] = "creator_zola" if s_copy.get("creator_name") == "Zola Dlamini" else "creator_amaka"
            if not s_copy.get("creator_avatar"):
                s_copy["creator_avatar"] = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=400&q=80"
            if "is_original" not in s_copy:
                s_copy["is_original"] = True
            if "is_trending" not in s_copy:
                s_copy["is_trending"] = float(s_copy.get("rating", 0)) >= 4.95

            # Find episodes matching series_id (by UUID, string ID, or slug)
            valid_series_ids = {s_id}
            if s_slug:
                valid_series_ids.add(s_slug)
            valid_series_ids.add(to_uuid(s_id))
            if s_slug:
                valid_series_ids.add(to_uuid(s_slug))

            s_episodes = [
                e for e in all_episodes 
                if str(e.get("series_id", "")) in valid_series_ids 
                and e.get("status") == "published"
                and not e.get("is_internal_test", False)
                and e.get("lifecycle_state") != "INTERNAL_TEST"
            ]
            s_episodes.sort(key=lambda x: x.get("episode_number", 0))

            hydrated_eps = []
            for ep in s_episodes:
                ep_copy = dict(ep)
                ep_id_str = str(ep.get("id", ""))
                ep_slug = ep.get("slug") or EPISODE_UUID_TO_SLUG.get(ep_id_str)
                if ep_slug:
                    ep_copy["slug"] = ep_slug

                is_ep_free = ep_copy.get("is_free", False) or (ep_copy.get("episode_number", 1) <= s_copy.get("free_episodes", 2) if s_copy.get("free_episodes", 2) > 0 else False)
                ep_copy["is_free"] = is_ep_free

                media = media_map.get(ep_id_str) or (media_map.get(ep_slug) if ep_slug else None)
                if media:
                    ep_copy["thumbnail_url"] = media.get("thumbnail_url", s_copy.get("vertical_poster"))
                    ep_copy["media_asset_id"] = media.get("id")
                    if is_ep_free:
                        ep_copy["video_url"] = media.get("master_video_url", "/videos/welele_placeholder.mp4")
                        ep_copy["hls_url"] = media.get("hls_master_manifest_url")
                        ep_copy["renditions"] = media.get("renditions_json")
                        ep_copy["storage_key"] = media.get("storage_key")
                    else:
                        ep_copy["video_url"] = None
                        ep_copy["hls_url"] = None
                        ep_copy["renditions"] = None
                        ep_copy["storage_key"] = None
                else:
                    ep_copy["video_url"] = "/videos/welele_placeholder.mp4" if is_ep_free else None
                    ep_copy["hls_url"] = None
                    ep_copy["renditions"] = None
                    ep_copy["storage_key"] = None
                
                if "cliffhanger_time" not in ep_copy:
                    ep_copy["cliffhanger_time"] = ep_copy.get("cliffhanger_time_seconds", 65)
                hydrated_eps.append(ep_copy)

            s_copy["episodes"] = hydrated_eps
            s_copy["total_episodes"] = len(hydrated_eps)
            result.append(s_copy)

        return result

    def get_series_detail(self, series_id: str) -> Optional[Dict[str, Any]]:
        all_series = self.list_feed()
        target_uuid = to_uuid(series_id)
        for s in all_series:
            s_id = str(s.get("id", ""))
            s_slug = str(s.get("slug", ""))
            if s_id == series_id or s_slug == series_id or s_id == target_uuid or to_uuid(s_id) == target_uuid:
                return s
        
        # Check local store if not found in list_feed (e.g., drafts or offline)
        raw_series = self.local_get("series") or []
        for s in raw_series:
            s_id = str(s.get("id", ""))
            s_slug = str(s.get("slug", ""))
            if s_id == series_id or s_slug == series_id or s_id == target_uuid or to_uuid(s_id) == target_uuid:
                return s
        return None

    def get_series(self, series_id: str) -> Optional[Dict[str, Any]]:
        target_uuid = to_uuid(series_id)
        if self.is_live:
            try:
                res = self.get_table("series").select("*").or_(f"id.eq.{series_id},id.eq.{target_uuid}").execute()
                if res and res.data:
                    row = res.data[0]
                    row["slug"] = SERIES_UUID_TO_SLUG.get(str(row.get("id")))
                    return row
            except Exception as e:
                logger.warning(f"[SeriesRepository] get_series remote lookup failed: {e}")
        all_series = self.local_get("series") or []
        for s in all_series:
            s_id = str(s.get("id", ""))
            s_slug = str(s.get("slug", ""))
            if s_id == series_id or s_slug == series_id or s_id == target_uuid or to_uuid(s_id) == target_uuid:
                return s
        return None

    def get_episodes_for_series(self, series_id: str) -> List[Dict[str, Any]]:
        target_uuid = to_uuid(series_id)
        if self.is_live:
            try:
                res = self.get_table("episodes").select("*").or_(f"series_id.eq.{series_id},series_id.eq.{target_uuid}").order("episode_number").execute()
                if res and res.data:
                    for ep in res.data:
                        ep["slug"] = EPISODE_UUID_TO_SLUG.get(str(ep.get("id")))
                    return res.data
            except Exception as e:
                logger.warning(f"[SeriesRepository] get_episodes_for_series remote lookup failed: {e}")
        all_episodes = self.local_get("episodes") or []
        eps = [e for e in all_episodes if e.get("series_id") in [series_id, target_uuid] or to_uuid(str(e.get("series_id", ""))) == target_uuid]
        eps.sort(key=lambda x: x.get("episode_number", 0))
        return eps

    def get_media_asset_for_episode(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves authoritative media_asset record for an episode from Supabase PostgreSQL,
        falling back to local store if offline.
        """
        target_uuid = to_uuid(episode_id)
        if self.is_live:
            try:
                res = self.get_table("media_assets").select("*").eq(
                    "episode_id", target_uuid
                ).limit(1).execute()
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.warning(f"[SeriesRepository:DB] get_media_asset_for_episode remote lookup failed: {e}")
        all_media = self.local_get("media_assets") or []
        return next((m for m in all_media if str(m.get("episode_id")) in [episode_id, target_uuid]), None)

    def get_creator_series(self, creator_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Creator-facing Series roster returning ALL episodes across all lifecycle states
        (draft, under_review, changes_requested, approved, published) with full media hydration.
        """
        live_data = self._fetch_live_catalog()
        if live_data:
            all_series, all_episodes, all_media = live_data
        else:
            all_series = self.local_get("series") or []
            all_episodes = self.local_get("episodes") or []
            all_media = self.local_get("media_assets") or []

        media_map = {}
        for m in all_media:
            ep_id = str(m.get("episode_id", ""))
            if ep_id:
                media_map[ep_id] = m
                slug = EPISODE_UUID_TO_SLUG.get(ep_id)
                if slug:
                    media_map[slug] = m

        local_series = self.local_get("series") or []
        local_series_map = {str(s.get("id")): s for s in local_series}
        for s in local_series:
            s_slug = s.get("slug")
            if s_slug:
                local_series_map[s_slug] = s
            local_series_map[to_uuid(str(s.get("id")))] = s

        result = []
        for s in all_series:
            s_id = str(s.get("id", ""))
            s_slug = s.get("slug") or SERIES_UUID_TO_SLUG.get(s_id)
            c_id = s.get("creator_id")

            matched_local = local_series_map.get(s_id) or (local_series_map.get(s_slug) if s_slug else None) or local_series_map.get(to_uuid(s_id))
            if not c_id and matched_local:
                c_id = matched_local.get("creator_id")
            if not c_id:
                c_id = "creator_zola" if ("blood" in str(s.get("title", "")).lower() or "queen" in str(s.get("title", "")).lower()) else "creator_amaka"

            if creator_id and c_id and c_id != creator_id and to_uuid(c_id) != to_uuid(creator_id):
                continue

            s_copy = dict(s)
            s_copy["creator_id"] = c_id
            if matched_local:
                if not s_copy.get("creator_name"):
                    s_copy["creator_name"] = matched_local.get("creator_name")
                if not s_copy.get("creator_avatar"):
                    s_copy["creator_avatar"] = matched_local.get("creator_avatar")
            if s_slug:
                s_copy["slug"] = s_slug

            valid_series_ids = {s_id}
            if s_slug:
                valid_series_ids.add(s_slug)
            valid_series_ids.add(to_uuid(s_id))
            if s_slug:
                valid_series_ids.add(to_uuid(s_slug))

            s_episodes = [e for e in all_episodes if str(e.get("series_id", "")) in valid_series_ids]
            s_episodes.sort(key=lambda x: x.get("episode_number", 0))

            hydrated_eps = []
            for ep in s_episodes:
                ep_copy = dict(ep)
                ep_id_str = str(ep.get("id", ""))
                ep_slug = ep.get("slug") or EPISODE_UUID_TO_SLUG.get(ep_id_str)
                if ep_slug:
                    ep_copy["slug"] = ep_slug

                media = media_map.get(ep_id_str) or (media_map.get(ep_slug) if ep_slug else None)
                if media:
                    ep_copy["video_url"] = media.get("master_video_url", "/videos/welele_placeholder.mp4")
                    ep_copy["hls_url"] = media.get("hls_master_manifest_url")
                    ep_copy["thumbnail_url"] = media.get("thumbnail_url", s_copy.get("vertical_poster"))
                    ep_copy["renditions"] = media.get("renditions_json")
                    ep_copy["media_asset_id"] = media.get("id")
                    ep_copy["storage_key"] = media.get("storage_key")
                else:
                    ep_copy["video_url"] = ep_copy.get("video_url") or "/videos/welele_placeholder.mp4"
                hydrated_eps.append(ep_copy)

            published_cnt = len([e for e in hydrated_eps if e.get("status") == "published"])
            under_review_cnt = len([e for e in hydrated_eps if e.get("status") in ["under_review", "submitted", "pending_review"]])
            draft_cnt = len([e for e in hydrated_eps if e.get("status") == "draft"])
            archived_cnt = len([e for e in hydrated_eps if e.get("status") == "archived"])

            s_copy["episodes"] = hydrated_eps
            s_copy["total_episodes"] = len(hydrated_eps)
            s_copy["published_episodes_count"] = published_cnt
            s_copy["under_review_episodes_count"] = under_review_cnt
            s_copy["draft_episodes_count"] = draft_cnt
            s_copy["archived_episodes_count"] = archived_cnt
            result.append(s_copy)

        # Include any newly created local series not yet returned by remote catalog query
        existing_result_ids = {str(r.get("id")) for r in result}
        existing_result_ids.update({to_uuid(str(r.get("id"))) for r in result if r.get("id")})
        for ls in local_series:
            ls_id = str(ls.get("id", ""))
            if ls_id not in existing_result_ids and to_uuid(ls_id) not in existing_result_ids:
                ls_creator = ls.get("creator_id") or "creator_zola"
                if creator_id and ls_creator != creator_id and to_uuid(ls_creator) != to_uuid(creator_id):
                    continue
                ls_copy = dict(ls)
                ls_copy.setdefault("episodes", [])
                ls_copy.setdefault("total_episodes", len(ls_copy.get("episodes", [])))
                ls_copy.setdefault("published_episodes_count", 0)
                ls_copy.setdefault("under_review_episodes_count", 0)
                ls_copy.setdefault("draft_episodes_count", 0)
                ls_copy.setdefault("archived_episodes_count", 0)
                result.append(ls_copy)

        return result

    def get_creator_series_detail(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns a single series with all episodes across all lifecycle states.
        """
        all_series = self.get_creator_series()
        target_uuid = to_uuid(series_id)
        return next((s for s in all_series if s.get("id") == series_id or str(s.get("id")) == series_id or to_uuid(str(s.get("id", ""))) == target_uuid), None)

    def resolve_valid_ip_id(self, preferred_ip: Optional[str] = None) -> str:
        """
        Resolves or selects a valid UUID for digital_ips.id conforming to PostgreSQL schema.
        1. If preferred_ip is a valid UUID, returns it.
        2. Queries live Supabase public.digital_ips for an active IP UUID.
        3. Falls back to canonical staging seed UUID to_uuid('ip_blood_ties').
        """
        if preferred_ip:
            try:
                uuid.UUID(str(preferred_ip))
                return str(preferred_ip)
            except Exception:
                pass

        if self.is_live:
            try:
                res = self.get_table("digital_ips").select("id").limit(1).execute()
                if res.data and len(res.data) > 0 and res.data[0].get("id"):
                    return str(res.data[0]["id"])
            except Exception as e:
                logger.warning(f"[SeriesRepository] Could not fetch digital_ips from database: {e}")

        local_ips = self.local_get("digital_ips") or []
        for ip in local_ips:
            raw_id = ip.get("id")
            if raw_id:
                return to_uuid(str(raw_id))

        return to_uuid("ip_blood_ties")

    def resolve_next_season_number(self, ip_id: str) -> int:
        """
        Determines the next available season_number for the given digital_ip UUID
        to prevent duplicate key violations on CONSTRAINT unique_ip_season (ip_id, season_number).
        """
        existing_seasons = []
        if self.is_live:
            try:
                res = self.get_table("series").select("season_number").eq("ip_id", ip_id).execute()
                if res.data:
                    for row in res.data:
                        sn = row.get("season_number")
                        if sn is not None:
                            try:
                                existing_seasons.append(int(sn))
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                logger.warning(f"[SeriesRepository] Could not fetch season_numbers for ip {ip_id}: {e}")

        for s in (self.local_get("series") or []):
            s_ip = s.get("ip_id")
            if s_ip and (str(s_ip) == ip_id or to_uuid(str(s_ip)) == ip_id):
                sn = s.get("season_number")
                if sn is not None:
                    try:
                        existing_seasons.append(int(sn))
                    except (ValueError, TypeError):
                        pass

        if existing_seasons:
            return max(existing_seasons) + 1
        return 1

    def create_series(self, series_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authoritatively creates a new Series across local store and PostgreSQL.
        Enforces fail-closed semantics in staging/production when live database is active.
        """
        raw_id = series_data.get("id")
        if raw_id:
            try:
                uuid.UUID(str(raw_id))
                series_id = str(raw_id)
            except Exception:
                series_id = to_uuid(str(raw_id))
        else:
            series_id = str(uuid.uuid4())

        now_ts = datetime.now(timezone.utc).isoformat()

        raw_ip = series_data.get("ip_id")
        if not raw_ip or raw_ip == "ip_blood_ties":
            ip_id = self.resolve_valid_ip_id()
        else:
            ip_id = self.resolve_valid_ip_id(preferred_ip=str(raw_ip))

        season_number = series_data.get("season_number")
        if not season_number:
            season_number = self.resolve_next_season_number(ip_id)
        else:
            try:
                season_number = int(season_number)
            except (ValueError, TypeError):
                season_number = self.resolve_next_season_number(ip_id)

        series_record = {
            "id": series_id,
            "ip_id": ip_id,
            "season_number": season_number,
            "title": series_data["title"],
            "tagline": series_data.get("tagline", ""),
            "synopsis": series_data.get("synopsis", ""),
            "cover_image": series_data.get("cover_image", ""),
            "vertical_poster": series_data.get("vertical_poster", ""),
            "genre": series_data.get("genre", "Drama"),
            "rating": series_data.get("rating", 5.0),
            "total_episodes": series_data.get("total_episodes", 0),
            "free_episodes": series_data.get("free_episodes", 2),
            "coin_price_per_episode": series_data.get("coin_price_per_episode", 5),
            "is_published": series_data.get("is_published", True),
            "creator_id": series_data.get("creator_id", "creator_zola"),
            "creator_name": series_data.get("creator_name", "Zola Dlamini"),
            "creator_avatar": series_data.get("creator_avatar", ""),
            "available_languages": series_data.get("available_languages", ["isiZulu", "English"]),
            "tags": series_data.get("tags", []),
            "created_at": series_data.get("created_at", now_ts),
            "updated_at": series_data.get("updated_at", now_ts)
        }
        self.local_insert("series", series_record)
        
        if self.is_live:
            try:
                db_record = {
                    "id": to_uuid(series_id),
                    "ip_id": to_uuid(series_record["ip_id"]),
                    "season_number": series_record["season_number"],
                    "title": series_record["title"],
                    "tagline": series_record["tagline"],
                    "synopsis": series_record["synopsis"],
                    "cover_image": series_record["cover_image"],
                    "vertical_poster": series_record["vertical_poster"],
                    "genre": series_record["genre"],
                    "rating": series_record["rating"],
                    "total_episodes": series_record["total_episodes"],
                    "free_episodes": series_record["free_episodes"],
                    "coin_price_per_episode": series_record["coin_price_per_episode"],
                    "is_published": series_record["is_published"],
                    "available_languages": series_record["available_languages"],
                    "tags": series_record["tags"],
                    "created_at": series_record["created_at"],
                    "updated_at": series_record["updated_at"]
                }
                self.get_table("series").upsert(db_record).execute()
            except Exception as e:
                logger.error(f"[SeriesRepository:DB] Series remote persistence error: {e}")
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database write failure: Unable to persist series '{series_id}' to authoritative database: {e}")
        return series_record

    def create_episode_draft(
        self,
        series_id: str,
        story_package_id: Optional[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Creates an auditable Episode Draft linked to parent Series and Story Package.
        """
        ep_id = payload.get("id") or f"ep_{uuid.uuid4().hex[:8]}"
        now_ts = datetime.now(timezone.utc).isoformat()

        ep_record = {
            "id": ep_id,
            "series_id": series_id,
            "story_package_id": story_package_id,
            "episode_number": payload.get("episode_number", 1),
            "title": payload.get("title", f"Episode {payload.get('episode_number', 1)}"),
            "synopsis": payload.get("synopsis", ""),
            "duration_seconds": payload.get("duration_seconds", 80),
            "is_free": payload.get("is_free", False),
            "coin_price": payload.get("coin_price", 5) if not payload.get("is_free") else 0,
            "cliffhanger_time_seconds": payload.get("cliffhanger_time", payload.get("cliffhanger_time_seconds", 65)),
            "cliffhanger_time": payload.get("cliffhanger_time", payload.get("cliffhanger_time_seconds", 65)),
            "cliffhanger_hook": payload.get("cliffhanger_hook", "What happens next?"),
            "status": payload.get("status", "draft"),
            "preflight_health": payload.get("preflight_health"),
            "created_at": now_ts,
            "updated_at": now_ts
        }
        self.local_insert("episodes", ep_record)
        if self.is_live:
            try:
                db_record = {
                    "id": to_uuid(ep_id),
                    "series_id": to_uuid(series_id),
                    "episode_number": ep_record["episode_number"],
                    "title": ep_record["title"],
                    "synopsis": ep_record["synopsis"],
                    "duration_seconds": ep_record["duration_seconds"],
                    "is_free": ep_record["is_free"],
                    "coin_price": ep_record["coin_price"],
                    "cliffhanger_time_seconds": ep_record["cliffhanger_time_seconds"],
                    "cliffhanger_hook": ep_record["cliffhanger_hook"],
                    "status": ep_record["status"],
                    "created_at": ep_record["created_at"],
                    "updated_at": ep_record["updated_at"]
                }
                self.get_table("episodes").upsert(db_record).execute()
            except Exception as e:
                logger.error(f"[SeriesRepository:DB] Episode draft remote persistence error: {e}")
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database write failure: Unable to persist episode draft '{ep_id}' to authoritative database: {e}")
        return ep_record

    def attach_media_asset(
        self,
        episode_id: str,
        storage_key: str,
        master_url: str,
        thumbnail_url: Optional[str] = None,
        duration_seconds: float = 80.0
    ) -> Dict[str, Any]:
        """
        Attaches a decoupled media asset to an episode.
        """
        media_id = f"media_{episode_id}"
        now_ts = datetime.now(timezone.utc).isoformat()

        media_record = {
            "id": media_id,
            "episode_id": episode_id,
            "storage_key": storage_key,
            "master_video_url": master_url,
            "hls_master_manifest_url": f"https://cdn.welele.media/hls/{storage_key}/master.m3u8",
            "thumbnail_url": thumbnail_url,
            "duration_seconds": duration_seconds,
            "transcoding_status": "READY",
            "renditions_json": {
                "1080p": f"https://cdn.welele.media/hls/{storage_key}/1080p.m3u8",
                "720p": f"https://cdn.welele.media/hls/{storage_key}/720p.m3u8",
                "480p": f"https://cdn.welele.media/hls/{storage_key}/480p.m3u8"
            },
            "created_at": now_ts,
            "updated_at": now_ts
        }
        self.local_insert("media_assets", media_record)
        if self.is_live:
            try:
                db_media = {
                    "id": to_uuid(media_id),
                    "episode_id": to_uuid(episode_id),
                    "storage_key": storage_key,
                    "master_video_url": master_url,
                    "thumbnail_url": thumbnail_url,
                    "duration_seconds": duration_seconds,
                    "transcoding_status": "READY",
                    "created_at": now_ts,
                    "updated_at": now_ts
                }
                self.get_table("media_assets").upsert(db_media).execute()
            except Exception as e:
                logger.error(f"[SeriesRepository:DB] Media asset remote persistence error: {e}")
                if settings.IS_PRODUCTION_OR_STAGING:
                    raise RuntimeError(f"Database write failure: Unable to persist media asset '{media_id}' to authoritative database: {e}")
        return media_record

    def register_media_asset(
        self,
        episode_id: str,
        master_video_url: str,
        thumbnail_url: Optional[str] = None,
        storage_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.attach_media_asset(
            episode_id=episode_id,
            storage_key=storage_key or f"masters/{episode_id}.mp4",
            master_url=master_video_url,
            thumbnail_url=thumbnail_url
        )

    def submit_for_moderation(self, episode_id: str) -> Optional[Dict[str, Any]]:
        """
        Transitions episode status to 'under_review' for administrative review.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        updated = self.local_update("episodes", "id", episode_id, {
            "status": "under_review",
            "submitted_at": now_ts,
            "updated_at": now_ts
        })
        if self.is_live:
            try:
                self.get_table("episodes").update({
                    "status": "under_review",
                    "updated_at": now_ts
                }).or_(f"id.eq.{episode_id},id.eq.{to_uuid(episode_id)}").execute()
            except Exception as e:
                logger.warning(f"[SeriesRepository:DB] submit_for_moderation remote persistence error: {e}")
        return updated

    def review_episode(
        self,
        episode_id: str,
        decision: str, # 'approved' | 'changes_requested' | 'rejected'
        feedback: Optional[str] = None,
        reviewer_id: str = "admin_supervisor"
    ) -> Optional[Dict[str, Any]]:
        """
        Applies an auditable moderation decision. If approved, promotes status to 'published'.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        target_status = "published" if decision == "approved" else decision

        update_payload = {
            "status": target_status,
            "moderation_decision": decision,
            "moderation_feedback": feedback,
            "reviewed_by": reviewer_id,
            "reviewed_at": now_ts,
            "updated_at": now_ts
        }
        # CMS PUBLISH PROMOTION (Workstream 3): Approved content promoted to PRODUCTION_READY
        if decision == "approved":
            update_payload["lifecycle_state"] = "PUBLISHED"
            update_payload["readiness_state"] = "PRODUCTION_READY"

            update_payload["is_empty_draft"] = False

        updated = self.local_update("episodes", "id", episode_id, update_payload)
        if self.is_live:
            try:
                self.get_table("episodes").update({
                    "status": target_status,
                    "updated_at": now_ts
                }).or_(f"id.eq.{episode_id},id.eq.{to_uuid(episode_id)}").execute()
            except Exception as e:
                logger.warning(f"[SeriesRepository:DB] review_episode remote persistence error: {e}")
        return updated


    def archive_episode(
        self,
        episode_id: str,
        actor_id: str = "creator_zola",
        actor_role: str = "creator"
    ) -> Optional[Dict[str, Any]]:
        """
        Atomic Non-Destructive Operational Retirement:
        Transitions episode status to 'archived' while preserving all telemetry,
        ledger, audit, entitlements, and storage lineage.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        episodes = self.local_get("episodes")
        target_ep = next((e for e in episodes if e.get("id") == episode_id), None)
        if not target_ep:
            return None

        updated = self.local_update("episodes", "id", episode_id, {
            "status": "archived",
            "archived_by": actor_id,
            "archived_at": now_ts,
            "updated_at": now_ts
        })
        return updated

    def get_moderation_queue(self) -> List[Dict[str, Any]]:
        """
        Returns normalized queue of episodes currently under review with attached series and media data.
        """
        episodes = self.local_get("episodes")
        series_list = self.local_get("series")
        media_list = self.local_get("media_assets")

        series_map = {s["id"]: s for s in series_list}
        media_map = {m["episode_id"]: m for m in media_list}

        queue = []
        for ep in episodes:
            if ep.get("status") in ["under_review", "pending_review", "submitted"]:
                s = series_map.get(ep.get("series_id"), {})
                m = media_map.get(ep.get("id"), {})
                queue.append({
                    "id": f"mod_{ep['id']}",
                    "episode_id": ep["id"],
                    "series_id": ep.get("series_id"),
                    "series_title": s.get("title", "Untitled Series"),
                    "episode_number": ep.get("episode_number", 1),
                    "episode_title": ep.get("title", ""),
                    "creator_name": s.get("creator_name", "Showrunner"),
                    "creator_id": s.get("creator_id", "creator_zola"),
                    "submitted_at": ep.get("submitted_at", ep.get("created_at")),
                    "aspect_ratio": "9:16 (1080x1920)",
                    "duration": f"{ep.get('duration_seconds', 80)}s",
                    "duration_seconds": ep.get("duration_seconds", 80),
                    "video_url": m.get("master_video_url", "/videos/welele_placeholder.mp4"),
                    "thumbnail_url": m.get("thumbnail_url", s.get("vertical_poster")),
                    "cliffhanger_time": ep.get("cliffhanger_time_seconds", 65),
                    "cliffhanger_hook": ep.get("cliffhanger_hook", ""),
                    "ai_safety_score": 98.5,
                    "status": "pending_review",
                    "preflight_health": ep.get("preflight_health", {
                        "aspect_ratio_ok": True,
                        "duration_ok": True,
                        "audio_detected": True,
                        "thumbnail_present": True,
                        "cliffhanger_marker_ok": True,
                        "captions_present": True
                    })
                })
        return queue

    # --- Media Jobs & Rendition Operations (Amendment 1) ---

    def create_media_job(
        self,
        media_asset_id: str,
        provider: str = "CloudflareStream",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if idempotency_key:
            jobs = self.local_get("media_jobs")
            existing = next((j for j in jobs if j.get("idempotency_key") == idempotency_key), None)
            if existing:
                return existing

        now_ts = datetime.now(timezone.utc).isoformat()
        job = {
            "id": f"job_{uuid.uuid4().hex[:10]}",
            "media_asset_id": media_asset_id,
            "provider": provider,
            "status": "queued",
            "attempt": 1,
            "started_at": now_ts,
            "completed_at": None,
            "error": None,
            "idempotency_key": idempotency_key or f"job_idemp_{uuid.uuid4().hex[:8]}",
            "created_at": now_ts
        }
        self.local_insert("media_jobs", job)
        return job

    def update_media_job(
        self,
        job_id: str,
        status: str,
        attempt: Optional[int] = None,
        error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        now_ts = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {
            "status": status,
            "updated_at": now_ts
        }
        if status in ["completed", "ready"]:
            updates["completed_at"] = now_ts
        if attempt is not None:
            updates["attempt"] = attempt
        if error is not None:
            updates["error"] = error

        return self.local_update("media_jobs", "id", job_id, updates)

    def get_media_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        jobs = self.local_get("media_jobs")
        return next((j for j in jobs if j.get("id") == job_id), None)

    def add_rendition(
        self,
        media_asset_id: str,
        profile: str,
        width: int,
        height: int,
        bitrate: int,
        playlist_url: str
    ) -> Dict[str, Any]:
        rendition = {
            "id": f"rend_{uuid.uuid4().hex[:8]}",
            "media_asset_id": media_asset_id,
            "profile": profile,
            "width": width,
            "height": height,
            "bitrate": bitrate,
            "playlist_url": playlist_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.local_insert("media_renditions", rendition)
        return rendition

    def get_renditions_for_asset(self, media_asset_id: str) -> List[Dict[str, Any]]:
        renditions = self.local_get("media_renditions")
        return [r for r in renditions if r.get("media_asset_id") == media_asset_id]

    def update_media_asset_status(
        self,
        media_asset_id: str,
        status: str,
        hls_manifest_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        now_ts = datetime.now(timezone.utc).isoformat()
        updates: Dict[str, Any] = {
            "status": status,
            "updated_at": now_ts
        }
        if hls_manifest_url:
            updates["hls_master_manifest"] = hls_manifest_url
        return self.local_update("media_assets", "id", media_asset_id, updates)

series_repository = SeriesRepository()
