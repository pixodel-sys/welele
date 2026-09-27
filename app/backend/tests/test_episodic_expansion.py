"""
Test Suite: Canonical Forge -> Episodic Expansion & Living State Machine
Validates:
1. Continuity Chain (E1 -> E5): E2 starts from E1's exact cliffhanger and consequences.
2. Character Knowledge States: Characters cannot act on secrets before they learn them.
3. Provenance Protection: Episodic facts never overwrite or escalate to Forge Canon.
4. Variable Episode Count: Runs with configurable target count (not hardcoded to 30).
5. Safe Regeneration of Episode 4:
   - Does NOT mutate Forge Canon or Episodes 1-3.
   - Downstream states (Episode 4 and Episode 5) successfully re-propagate.
6. AI Production Readiness:
   - Evaluates that production packs contain structured prompts (framing, visual action,
     lighting, isiZulu dialogue, subtext, SFX, BPM music) ready for AI generation compilers.
"""

import pytest
from services.episodic_expansion_service import episodic_expansion_engine
from schemas.episodic_expansion_schemas import EpisodicProvenance


@pytest.fixture
def mock_umkhehlo_forge_canon():
    """Authoritative Story Forge state for Umkhehlo series."""
    return {
        "story_id": "umkhehlo_series",
        "title": "Umkhehlo: The Stained Veil",
        "logline": "A humble seamstress is humiliated at a billionaire wedding, only for an ancient royal heirloom to halt the altar ceremony and expose a stolen dynastic throne.",
        "theme": "Royal Lineage, Customary Succession & Sacred Bloodline",
        "characters": {
            "Nandi": {
                "name": "Nandi",
                "role": "PROTAGONIST",
                "core_motivation": "Protect her late mother's honor and survive the sudden royal scrutiny.",
                "secret_desire": "To know the true identity of her father and her mother's hidden royal lineage.",
                "fatal_flaw": "Naivety regarding high-stakes corporate sabotage."
            },
            "Bhekisisa": {
                "name": "Bhekisisa",
                "role": "ANTAGONIST",
                "core_motivation": "Preserve the Khumalo dynasty's commercial mining rights and succession.",
                "secret_desire": "To atone for his late father's ruthless usurpation of the throne.",
                "fatal_flaw": "Pride and blind dedication to institutional survival."
            },
            "Minenhle": {
                "name": "Minenhle",
                "role": "ANTAGONIST",
                "core_motivation": "Secure billionaire status through marriage into the Khumalo family.",
                "secret_desire": "Eliminate any threat to her impending coronation.",
                "fatal_flaw": "Desperate ruthlessness that leaves forensic paper trails."
            }
        },
        "world": {
            "arena": "Umhlanga Coastline Estates & Umlazi Seamstress Shops, KwaZulu-Natal",
            "rules_and_lore": [
                "Customary royal succession covenants supersede civil commercial contracts.",
                "The royal heirloom wrist cuff authenticates bloodline succession."
            ]
        },
        "plants": [
            {"plant_name": "Royal Heirloom Wrist Cuff", "element_code": "PLANT-01", "payoff_status": "LOCKED"},
            {"plant_name": "Bridal Veil with Customary Embroidery", "element_code": "PLANT-02", "payoff_status": "LOCKED"}
        ]
    }


def test_living_state_continuity_chain(mock_umkhehlo_forge_canon):
    """
    Test 1: Verify E1 -> E5 continuity chain.
    Episode 2 must start from Episode 1's consequences.
    """
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5
    )

    assert len(contracts) == 5
    assert len(states) == 6  # Baseline State[0] + 5 episodes
    assert len(packs) == 5

    # Check E1 -> E2 bridge
    e1_contract = contracts[0]
    e2_contract = contracts[1]
    e2_state = states[2]  # State at end of Ep 2

    # Episode 2 opening hook must acknowledge Episode 1's altar halt
    assert "altar" in e1_contract.closing_cliffhanger.lower() or "wrist" in e1_contract.closing_cliffhanger.lower()
    assert "Nandi" in e2_contract.opening_hook
    assert "Bhekisisa" in e2_contract.opening_hook

    # Check Episode 3 flight to Umlazi originates from Episode 2 security escalation
    e3_contract = contracts[2]
    assert "escape" in e3_contract.opening_hook.lower() or "screech" in e3_contract.opening_hook.lower()


def test_character_knowledge_states(mock_umkhehlo_forge_canon):
    """
    Test 2: Characters retain established motivations and cannot know facts before learning them.
    In E1: Bheki does not know the full 1998 usurpation history until E4.
    In E3: Nandi discovers her mother's 1998 covenant.
    """
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5
    )

    state_before_e1 = states[0]
    bheki_e0 = state_before_e1.character_states["Bhekisisa"]
    # Before E1, Bhekisisa only knows his canonical setup
    assert not any("1998" in fact for fact in bheki_e0.known_facts)

    state_after_e4 = states[4]
    bheki_e4 = state_after_e4.character_states["Bhekisisa"]
    # After E4, Bhekisisa has learned of his father's usurpation
    assert any("1998" in fact for fact in bheki_e4.known_facts)

    # Nandi discovers her mother's covenant in Ep 3
    state_after_e3 = states[3]
    nandi_e3 = state_after_e3.character_states["Nandi"]
    assert any("1998" in fact for fact in nandi_e3.known_facts)


def test_provenance_immutability(mock_umkhehlo_forge_canon):
    """
    Test 3: Episodic facts never mutate or escalate to Macro Story Forge Canon.
    """
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5
    )

    baseline_hash = states[0].canon_lineage_hash
    for s in states:
        # Macro canon lineage hash remains identical across all state snapshots
        assert s.canon_lineage_hash == baseline_hash

    # Contracts audit verification
    for c in contracts:
        assert c.provenance_audit["core_canon"] == EpisodicProvenance.CANON
        assert c.state_delta.provenance == EpisodicProvenance.EPISODIC_FACT


def test_regeneration_of_episode_4_without_breaking_e1_to_e3(mock_umkhehlo_forge_canon):
    """
    Test 4: Regenerate Episode 4.
    Must NOT mutate Forge Canon or Episodes 1-3.
    Downstream Episode 5 state must re-propagate properly.
    """
    # 1. Initial Generation
    contracts_initial, states_initial, packs_initial = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5
    )

    e1_hash_initial = contracts_initial[0].resulting_state_hash
    e2_hash_initial = contracts_initial[1].resulting_state_hash
    e3_hash_initial = contracts_initial[2].resulting_state_hash
    e4_hash_initial = contracts_initial[3].resulting_state_hash

    # 2. Regenerate from Episode 4 forward
    contracts_regen, states_regen, packs_regen = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5,
        regenerate_from_episode=4,
        cached_states=states_initial,
        cached_contracts=contracts_initial
    )

    # Episodes 1-3 remain completely untouched and byte-identical
    assert contracts_regen[0].resulting_state_hash == e1_hash_initial
    assert contracts_regen[1].resulting_state_hash == e2_hash_initial
    assert contracts_regen[2].resulting_state_hash == e3_hash_initial

    # E1-3 titles and contents untouched
    assert contracts_regen[0].title == contracts_initial[0].title
    assert contracts_regen[1].title == contracts_initial[1].title
    assert contracts_regen[2].title == contracts_initial[2].title

    # Ep 4 and Ep 5 exist and are continuous
    assert len(contracts_regen) == 5
    assert contracts_regen[3].episode_number == 4
    assert contracts_regen[4].episode_number == 5


def test_ai_production_readiness_pack(mock_umkhehlo_forge_canon):
    """
    Test 5: Verify Episode Production Pack contains sufficient structured data
    for direct AI compilation (Video visual prompts, locked isiZulu dialogue, subtext, SFX, BPM).
    """
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=5
    )

    ep1_pack = packs[0]
    assert ep1_pack.readiness_audit.is_sparse_draft is False
    assert ep1_pack.readiness_state.value == "READY_FOR_PRODUCTION"
    assert len(ep1_pack.production_units) >= 3

    for unit in ep1_pack.production_units:
        # Track 1: Video prompt completeness
        assert "9:16" in unit.video_track.framing
        assert len(unit.video_track.visual_action) > 10
        assert unit.video_track.visual_prompt is not None
        assert "Cinematic 9:16" in unit.video_track.visual_prompt

        # Track 2: Dialogue & Subtext
        assert unit.dialogue_track.speaker != "UNKNOWN"
        assert len(unit.dialogue_track.dialogue) > 5
        assert unit.dialogue_track.language == "isiZulu"
        assert len(unit.dialogue_track.delivery_intention) > 5

        # Track 4: Ambience & SFX
        assert len(unit.ambience_track.action_sfx) > 0

        # Track 5: Music BPM
        assert "BPM" in unit.music_track.style_instrumentation


def test_natural_story_resolution_discovery(mock_umkhehlo_forge_canon):
    """
    Test 6: Variable-length expansion without hardcoded 30 episodes.
    The machine must discover when the story reaches legitimate resolution
    and explain why it stopped.
    """
    # Run expansion without specifying target count (or with open ceiling 30)
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=None,
        stop_on_natural_resolution=True,
        max_safety_limit=30
    )

    # Umkhehlo naturally resolves at Episode 8
    assert len(contracts) == 8
    assert len(states) == 9  # baseline + 8
    assert len(packs) == 8

    # Final episode must be marked as resolution
    final_contract = contracts[-1]
    final_state = states[-1]

    assert final_contract.is_series_climax_or_resolution is True
    assert final_state.is_story_resolved is True

    # Machine must provide explicit rationale explaining why it stopped
    assert final_state.resolution_rationale is not None
    assert len(final_state.resolution_rationale) > 20
    assert "bloodline" in final_state.resolution_rationale.lower() or "covenant" in final_state.resolution_rationale.lower()

    # Preceding episodes must NOT be marked as resolution
    for c in contracts[:-1]:
        assert c.is_series_climax_or_resolution is False


def test_rich_dialogue_and_arc_specific_audio_motifs(mock_umkhehlo_forge_canon):
    """
    Test 7: Verify incorporation of the two quality observations:
    - Richer multi-speaker dialogue exchanges where dramatically appropriate
    - Arc-specific and episode-specific audio motifs (BPM, instruments, sound environments)
    """
    contracts, states, packs = episodic_expansion_engine.expand_canonical_story_into_episodes(
        story_state=mock_umkhehlo_forge_canon,
        target_episode_count=8
    )

    # Check Episode 6 (Council Inquest) has council judgment percussion motif
    ep6_pack = packs[5]
    ep6_music = ep6_pack.production_units[0].music_track.style_instrumentation
    assert "Council Judgment" in ep6_music or "Igubu" in ep6_music

    # Check Episode 7 (Ancestral Night) has mourning flute motif
    ep7_pack = packs[6]
    ep7_music = ep7_pack.production_units[0].music_track.style_instrumentation
    assert "Flute" in ep7_music or "Ancestral" in ep7_music

    # Check Episode 8 (Coronation) has triumphant coronation anthem
    ep8_pack = packs[7]
    ep8_music = ep8_pack.production_units[0].music_track.style_instrumentation
    assert "Coronation Anthem" in ep8_music

    # Check richer multi-speaker dialogue exchange in Unit 2 of Episode 6
    unit_2_dialogue = ep6_pack.production_units[1].dialogue_track.dialogue
    assert "[" in unit_2_dialogue and "]" in unit_2_dialogue  # Multi-speaker formatted exchange

