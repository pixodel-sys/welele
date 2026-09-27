"""
Welele Media™ — AI Production Adapter & Plan Compiler
Phase 3 Downstream Production Execution Layer

Governing Laws:
1. Welele Production Document (Bible + Episode Pack) = Authoritative Source of Truth.
2. AI Production Adapter = Translation / Runtime Layer.
3. Strict Question Classification:
   - Category A: Missing Canonical Information (Story Forge truth: premise, characters, lore, world rules)
   - Category B: Missing Production Information (Physical execution decisions: set design, practical props, stunts)
   - Category C: AI-Runtime / Adapter Requirement (reference_entity_ids, LoRA weights, seed, CFG scale, sampler, audio TTS voice IDs)
   Only A/B may bubble upstream to creators. Category C MUST be synthesized deterministically by this adapter.
4. Zero Provenance Escalation: AI-runtime IDs, generation parameters, and seed states NEVER become canonical facts.
"""

from enum import Enum
import hashlib
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from schemas.production_schemas import (
    ProductionBibleModel,
    EpisodeProductionPackModel,
    ProvenanceType
)


class FeedbackCategory(str, Enum):
    A_MISSING_CANONICAL = "CATEGORY_A_MISSING_CANONICAL"
    B_MISSING_PRODUCTION = "CATEGORY_B_MISSING_PRODUCTION"
    C_AI_RUNTIME_ADAPTER = "CATEGORY_C_AI_RUNTIME_ADAPTER"


class AIEntityBinding(BaseModel):
    """Binds canonical character to an AI-runtime generation entity."""
    canonical_character_name: str
    canonical_role: str
    reference_entity_id: str
    visual_embedding_tag: str
    lora_asset_id: str
    lora_trigger_token: str
    voice_profile_id: str
    voice_timbre: str
    speech_rate_wpm: int
    dialect_phonetics: str
    runtime_notes: str


class AIShotPlan(BaseModel):
    """A discrete, executable AI generation unit mapped to vertical mobile framing."""
    shot_id: str
    scene_ref: str
    beat_ref: str
    timing_start_seconds: int
    timing_end_seconds: int
    duration_seconds: int
    
    # Track 1 Visual Prompt Synthesis
    ai_video_prompt: str
    ai_negative_prompt: str
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"
    camera_movement: str
    lens_specification: str
    lighting_setup: str
    color_lut_id: str
    diffusion_cfg_scale: float = 7.5
    diffusion_steps: int = 30
    motion_bucket_id: int = 127
    
    # Track 2 Spoken Dialogue / TTS
    speaking_entity_id: Optional[str] = None
    spoken_dialogue_isizulu: Optional[str] = None
    dialogue_subtext: Optional[str] = None
    voice_profile_id: Optional[str] = None
    emotion_guidance: Optional[str] = None
    
    # Track 3 Voiceover
    narration_text: Optional[str] = None
    narrator_voice_id: Optional[str] = None
    
    # Track 4 Foley & SFX
    foley_cue: Optional[str] = None
    sfx_intensity_db: float = -12.0
    
    # Track 5 Score
    score_cue_id: str
    score_bpm: int
    score_stems: List[str]


class AIExecutableProductionPlan(BaseModel):
    """
    Executable AI-Production Plan compiled directly from the canonical Production Document.
    Ready for immediate execution by multi-modal diffusion and neural audio synthesis engines.
    """
    plan_id: str
    episode_id: str
    title: str
    source_production_bible_id: str
    source_pack_id: str
    source_lineage_hash: str
    plan_hash: str
    
    # Runtime Asset Bindings (Category C)
    character_entity_bindings: List[AIEntityBinding]
    environment_asset_bindings: Dict[str, str]
    
    # Executable Shot Storyboard
    executable_shots: List[AIShotPlan]
    
    # Quality & Compilation Audit
    total_shots: int
    total_duration_seconds: int
    paywall_lock_timestamp_seconds: int
    unresolved_questions: List[Dict[str, Any]] = Field(default_factory=list)
    compilation_status: str = "READY_FOR_EXECUTION"


class AIProductionAdapterCompiler:
    """
    Transforms canonical Welele Production Documents into executable AI-specific plans.
    Classifies inquiries into Category A, B, and C, and self-resolves all Category C runtime needs.
    """

    def __init__(self):
        pass

    def _hash_data(self, data: Any) -> str:
        s = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

    def classify_inquiry(self, inquiry_text: str) -> Dict[str, Any]:
        """
        Classifies an AI or engine question into:
        - A: Missing Canonical Information (Story Forge level)
        - B: Missing Production Information (Human physical production level)
        - C: AI-Runtime / Adapter Requirement (Self-handled by this adapter)
        """
        inquiry_lower = inquiry_text.lower()
        
        # Category C check: Technical synthesis & generation runtime tokens
        c_keywords = [
            "reference_entity_id", "lora", "embedding", "seed", "cfg", "sampler",
            "fps", "resolution", "voice_id", "checkpoint", "motion bucket",
            "token", "tts engine", "lut_file", "codec", "prompt format", "wpm"
        ]
        if any(k in inquiry_lower for k in c_keywords):
            return {
                "category": FeedbackCategory.C_AI_RUNTIME_ADAPTER,
                "action": "AUTO_RESOLVE_BY_ADAPTER",
                "bubbles_upstream": False,
                "reason": "Technical execution parameter belongs to the runtime translation layer, not narrative canon."
            }

        # Category B check: Physical practical production execution
        b_keywords = [
            "permit", "practical set", "stunt double", "soundstage rental",
            "actor call time", "caterer", "props purchase", "camera equipment rental",
            "insurance", "fire marshal"
        ]
        if any(k in inquiry_lower for k in b_keywords):
            return {
                "category": FeedbackCategory.B_MISSING_PRODUCTION,
                "action": "DEFER_TO_PRODUCTION_OFFICE",
                "bubbles_upstream": True,
                "reason": "Physical production requirement missing from production logistics."
            }

        # Category A check: Story, characters, world rules, chronology
        return {
            "category": FeedbackCategory.A_MISSING_CANONICAL,
            "action": "FLAG_TO_STORY_FORGE",
            "bubbles_upstream": True,
            "reason": "Story truth or character motivation ambiguity requires Story Forge clarification."
        }

    def compile_production_pack_to_ai_plan(
        self,
        bible: Any,
        pack: Any
    ) -> AIExecutableProductionPlan:
        """
        Takes the exact canonical Production Document (Bible + Episode 1 Pack)
        and compiles it into a fully resolved AI-specific executable plan without asking
        the creator for information already present.
        """
        # Convert dicts to models if needed
        if isinstance(bible, dict):
            bible_model = ProductionBibleModel(**bible)
        else:
            bible_model = bible

        if isinstance(pack, dict):
            pack_model = EpisodeProductionPackModel(**pack)
        else:
            pack_model = pack

        plan_id = f"ai_plan_{pack_model.id}_{pack_model.episode_number}"

        # 1. Map Section 3 Characters -> AI Character Entity Bindings (Category C translation)
        entity_bindings: List[AIEntityBinding] = []
        for char in bible_model.section_3_character_bible:
            # Deterministic ID generation based on character name and role
            entity_id = f"ent_{char.name.lower().replace(' ', '_').replace('/', '_')}"
            lora_token = f"welele_{char.name.split()[0].lower()}_face"
            
            # Voice profiles mapped to Section 7 dialect & vernacular matrix
            voice_id = (
                "voice_isizulu_matriarch_v1" if "Thandiwe" in char.name
                else "voice_isizulu_tycoon_v1" if "Bhekisisa" in char.name
                else "voice_isizulu_young_urban_v1" if "Lerato" in char.name
                else "voice_xitsonga_youth_amu_v1" if "Amu" in char.name
                else "voice_xitsonga_teen_stofel_v1" if "Stofel" in char.name
                else "voice_portuguese_syndicate_tavares_v1" if "Tavares" in char.name
                else "voice_africanis_dog_bougie_v1" if "Bougie" in char.name
                else "voice_african_generic_v1"
            )

            binding = AIEntityBinding(
                canonical_character_name=char.name,
                canonical_role=char.role,
                reference_entity_id=entity_id,
                visual_embedding_tag=f"<lora:{entity_id}_v1:0.85>, {lora_token}",
                lora_asset_id=f"lora_{entity_id}_base_v1.safetensors",
                lora_trigger_token=lora_token,
                voice_profile_id=voice_id,
                voice_timbre="Resonant chest voice with steely ancestral cadence" if "Thandiwe" in char.name else "Cultivated Sandton corporate cadence",
                speech_rate_wpm=120 if "Thandiwe" in char.name else 135,
                dialect_phonetics=char.dialect_guidance or "Durban / Soweto isiZulu",
                runtime_notes="Zero narrative mutation. Character visual key anchored to canonical wardrobe."
            )
            entity_bindings.append(binding)

        # 2. Environment Asset Bindings (Section 4 -> AI Set Latents)
        env_bindings: Dict[str, str] = {}
        for loc in bible_model.section_4_location_bible:
            loc_key = loc.location_name.lower().replace(" ", "_")
            env_bindings[loc.location_name] = f"latent_set_{loc_key}_v1.safetensors"

        # 3. Compile Episode Beats & 5 Tracks into Executable AI Shots
        shots: List[AIShotPlan] = []
        
        # Sourced from Section 6 Visual Language
        vis_lang = bible_model.section_6_visual_language
        lut_id = vis_lang.lut_specifications or "Welele_Mzansi_Chiaroscuro_v1"
        lens_pkg = {l.get("use", ""): l.get("lens", "35mm f/1.4") for l in vis_lang.camera_and_lens_package}

        video_scenes = pack_model.five_tracks.video.scene_descriptions
        dialogue_items = pack_model.five_tracks.dialogue.dialogue_lines
        foley_events = pack_model.five_tracks.ambience.foley_events
        music_tracks = pack_model.five_tracks.music.stems_progression

        for idx, scene in enumerate(video_scenes, start=1):
            s_timing = scene.get("timing", "00:00 - 00:30")
            # Parse timing: e.g. "00:00 - 00:15"
            try:
                parts = s_timing.replace("00:", "").split("-")
                t_start = int(parts[0].strip())
                t_end = int(parts[1].strip())
            except Exception:
                t_start = (idx - 1) * 30
                t_end = idx * 30

            # Find matching dialogue in this timing window
            matched_diag = next(
                (d for d in dialogue_items if t_start <= d.get("timestamp_s", 0) <= t_end),
                None
            )
            
            # Find matching foley
            matched_foley = next(
                (f.get("foley") for f in foley_events if t_start <= f.get("timestamp_s", 0) <= t_end),
                None
            )

            # Sourced camera movement
            cam_dir = next(
                (c.get("technique") for c in pack_model.five_tracks.video.camera_direction if str(idx) in c.get("shot", "")),
                "Slow cinematic push-in on 9:16 vertical subject"
            )

            # Match character entity for dialogue
            speaker_entity = None
            voice_id = None
            if matched_diag:
                spk = matched_diag.get("speaker", "")
                binding = next((b for b in entity_bindings if spk.lower() in b.canonical_character_name.lower()), None)
                if binding:
                    speaker_entity = binding.reference_entity_id
                    voice_id = binding.voice_profile_id

            # Sourced score stems
            score_stems = [
                m.get("stem") for m in music_tracks
                if m.get("time") and parts[0].strip() in m.get("time")
            ] or ["Solo Zulu drum heartbeat at 68 BPM"]

            # Compose synthetic AI generation prompt adhering strictly to Section 10 Prompt Constitution
            vis_action = scene.get("visual_action", "")
            framing = scene.get("framing", "9:16 Vertical Close-Up")
            lighting = scene.get("lighting", "2700K Warm Candle Key")
            
            ai_prompt = (
                f"Cinematic 9:16 vertical video for South African microdrama. {framing}. {vis_action}. "
                f"Lighting: {lighting}. 4K UHD, photorealistic, natural skin texture, dramatic shadow falloff, "
                f"LUT {lut_id}. Camera motion: {cam_dir}."
            )
            
            ai_neg = (
                "horizontal aspect ratio, 16:9, widescreen, western suburban aesthetics, distorted anatomy, "
                "cartoon, oversaturated, generic stock video, warped fingers, flat lighting"
            )

            shot = AIShotPlan(
                shot_id=f"shot_{scene.get('scene_id', f'SC_0{idx}')}",
                scene_ref=scene.get("scene_id", f"SC_0{idx}"),
                beat_ref=f"beat_ep1_0{idx}",
                timing_start_seconds=t_start,
                timing_end_seconds=t_end,
                duration_seconds=t_end - t_start,
                ai_video_prompt=ai_prompt,
                ai_negative_prompt=ai_neg,
                aspect_ratio="9:16",
                resolution="1080x1920",
                camera_movement=cam_dir,
                lens_specification="35mm f/1.4 Prime" if idx == 1 else "24mm f/1.8 Wide" if idx == 2 else "50mm f/1.2 Macro",
                lighting_setup=lighting,
                color_lut_id=lut_id,
                diffusion_cfg_scale=7.5,
                diffusion_steps=30,
                motion_bucket_id=127,
                speaking_entity_id=speaker_entity,
                spoken_dialogue_isizulu=matched_diag.get("line") if matched_diag else None,
                dialogue_subtext=matched_diag.get("subtext") if matched_diag else None,
                voice_profile_id=voice_id,
                emotion_guidance=matched_diag.get("delivery_tone") if matched_diag else None,
                narration_text=pack_model.five_tracks.narration.opening_hook_vo if idx == 1 else None,
                narrator_voice_id="voice_ancestral_elder_narrator_v1" if idx == 1 else None,
                foley_cue=matched_foley,
                sfx_intensity_db=-14.0,
                score_cue_id=pack_model.five_tracks.music.score_theme or "Bougie_Motif",
                score_bpm=pack_model.five_tracks.music.tempo_bpm or 112,
                score_stems=score_stems
            )
            shots.append(shot)

        total_dur = sum(s.duration_seconds for s in shots)
        plan_hash = self._hash_data({
            "bible_id": bible_model.id,
            "pack_id": pack_model.id,
            "shots_count": len(shots),
            "total_dur": total_dur
        })

        return AIExecutableProductionPlan(
            plan_id=plan_id,
            episode_id=str(pack_model.episode_number),
            title=pack_model.title,
            source_production_bible_id=bible_model.id,
            source_pack_id=pack_model.id,
            source_lineage_hash=pack_model.lineage_hash,
            plan_hash=plan_hash,
            character_entity_bindings=entity_bindings,
            environment_asset_bindings=env_bindings,
            executable_shots=shots,
            total_shots=len(shots),
            total_duration_seconds=total_dur,
            paywall_lock_timestamp_seconds=88,
            unresolved_questions=[],
            compilation_status="READY_FOR_EXECUTION"
        )


ai_production_adapter_compiler = AIProductionAdapterCompiler()
