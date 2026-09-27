"""
Welele Media™ — Baseline End-to-End Production Proof Fixture
Canonical Reference: Isibusiso Episode 1 (The Midnight Sovereign)

Frozen Baseline Invariants:
1. Canonical Story -> Episodic State -> Production Document -> AI Adapter -> Rendered Episode -> Continuity Audit
2. The 10 Inviolable Dimensions:
   - character_identity (biometric similarity >= 0.95)
   - wardrobe (green midwife tunic with wax distress, charcoal suit)
   - spatial_continuity (Mofolo South Clinic Interior Ward -> Exterior Gate)
   - lighting_grammar (2700K candle key vs 5600K vehicle headlights)
   - prop_persistence (Royal ink-mark on infant left scapula & 1912 customary ledger)
   - voice_identity (formal ancestral isiZulu @ 120 WPM vs boardroom @ 135 WPM)
   - dialogue_fidelity (verbatim canonical match: 'A child is not platinum ore...')
   - audio_music (locked 68 BPM Zulu drum heartbeat pulse)
   - timing (88-90s vertical microdrama: 15s hook, 50s reversal, 88s climax)
   - paywall_cliffhanger (hard blackout freeze at 88.0s)
   - canon_immutability (zero synthetic lore leakage back upstream)
"""

import json
from typing import Dict, Any

FROZEN_BASELINE_EPISODE_1: Dict[str, Any] = {
    "fixture_version": "1.0.0-FROZEN",
    "fixture_date": "2026-09-27T15:27:00Z",
    "ip_id": "ip_isibusiso_dynasty",
    "franchise_code": "IP-ISIBUSISO",
    "series_id": "series_isibusiso_s1",
    "episode_number": 1,
    "episode_title": "Episode 1: The Midnight Sovereign",
    "duration_seconds": 88.0,
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "fps": 24,
    "format": "Vertical Microdrama",
    "paywall_cut_second": 88.0,
    "cliffhanger_prompt": "Will Thandiwe sign the Khumalo settlement or trigger a township uprising to protect the royal infant?",
    "invariants": {
        "character_identity": {
            "thandiwe_entity_id": "ent_thandiwe_sithole",
            "thandiwe_lora_token": "welele_thandiwe_face",
            "bhekisisa_entity_id": "ent_bhekisisa_khumalo",
            "bhekisisa_lora_token": "welele_bhekisisa_face",
            "min_face_similarity_threshold": 0.95
        },
        "wardrobe": {
            "thandiwe": "Weathered green clinical midwife tunic with candle wax distress",
            "bhekisisa": "Immaculate charcoal bespoke Sandton suit with gold signet ring",
            "lerato": "Oversized dark thrifted coat with postpartum exhaustion and hospital wristband"
        },
        "spatial_continuity": {
            "scene_1": "Mofolo South Clinic Delivery Ward (15m2 practical interior)",
            "scene_2": "Clinic Exterior Gate & Gravel Perimeter",
            "scene_3": "Clinic Threshold (Interior/Exterior confrontation line)"
        },
        "lighting_grammar": {
            "scene_1_interior": 2700,
            "scene_2_exterior": 5600,
            "scene_3_threshold": 5000,
            "lut": "Welele_Mzansi_Chiaroscuro_v1"
        },
        "prop_persistence": [
            {
                "prop_name": "Royal Ink-Mark",
                "location": "Infant left shoulder blade / scapula",
                "first_appearance_second": 4,
                "status": "PERSISTENT"
            },
            {
                "prop_name": "Customary Birth Register Ledger",
                "carrier": "Thandiwe Sithole",
                "climax_appearance_second": 86,
                "status": "PERSISTENT"
            }
        ],
        "voice_identity": {
            "thandiwe_voice_profile": "voice_isizulu_matriarch_v1",
            "thandiwe_wpm": 120,
            "thandiwe_dialect": "Formal ancestral isiZulu",
            "bhekisisa_voice_profile": "voice_isizulu_tycoon_v1",
            "bhekisisa_wpm": 135,
            "bhekisisa_dialect": "Corporate Sandton isiZulu"
        },
        "dialogue_fidelity": [
            {
                "speaker": "Thandiwe",
                "verbatim_line": "A child is not platinum ore to be dug up and traded in Sandton, Bhekisisa.",
                "delivery": "Steely maternal authority"
            },
            {
                "speaker": "Bhekisisa",
                "verbatim_line": "That child carries the only bloodline that keeps my mining shafts open. Hand him over.",
                "delivery": "Cold corporate threat"
            }
        ],
        "audio_music": {
            "score_theme": "The Ancestral Heartbeat",
            "tempo_bpm": 68,
            "stems": ["Low Zulu acoustic bass drum", "Solo cello staccato", "High-tension string tremolo", "Brass crescendo"],
            "paywall_silence_second": 88.0
        },
        "timing_and_beats": {
            "beat_1_hook_window": [0, 15],
            "beat_2_reversal_window": [15, 50],
            "beat_3_climax_window": [50, 88],
            "total_shots": 3
        },
        "paywall_and_canon": {
            "hard_freeze_at_second": 88.0,
            "canon_mutation_permitted": False,
            "runtime_tokens_leak_upstream": False
        }
    }
}
