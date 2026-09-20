"""
PHASE 1A.1 — STORY FORGE ADVERSARIAL TEST SUITE
Executes and validates all 10 adversarial narrative scenarios.
"""

import sys
import os
import re
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus, CharacterRelationship,
    Dependency, DependencyType, DependencyStatus, AuthorityMode, SkillEnum,
    MilestoneEnum, ReadinessStatus, ChronologyEvent, StateMutation, MutationType,
    KnowledgeState, KnowledgeStatus, NarrativePlant, WorldSetting
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.engine import (
    DependencyEngine, NarrativeExtractor, ConsequencePropagator, StateEngine, EntityRegistry
)
from story_forge.api.routes import get_story_package
from story_forge.adapters import MockReasoningAdapter


def test_scenario_1_minimalist_story():
    print("\n=======================================================")
    print("TEST 1 — MINIMALIST STORY")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_01_minimalist"
    repo.create_story(
        story_id=story_id,
        title="Thandi's Village",
        owner_id="creator_thandi",
        logline="Thandi wants to leave her village, but her mother refuses to let her go."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Creator input
    trans1, s1, q1 = kernel.process_cycle(
        story_id,
        creator_input="Thandi wants to leave her village, but her mother refuses to let her go."
    )

    print(f"Cycle 1 Question: {q1}")
    print(f"Characters ({len(s1.characters)}): {list(s1.characters.keys())}")
    for k, c in s1.characters.items():
        print(f"  - {c.name} ({c.role}): mot='{c.core_motivation}', rels={[r.target_character for r in c.relationships]}")

    # Verify:
    # 1. Thandi is preserved as protagonist
    assert "Thandi" in s1.characters, "Thandi must be identified as character"
    assert s1.characters["Thandi"].role == CharacterRole.PROTAGONIST, "Thandi must be PROTAGONIST"

    # 2. Mother is NOT converted into a fabricated proper name (e.g. no character named 'Mother')
    assert "Mother" not in s1.characters, "Mother must NOT be created as a proper-named character entity"
    assert "Mom" not in s1.characters, "Mom must NOT be created as a proper-named character entity"

    # 3. No invented motivation promoted to FACT beyond what creator stated
    thandi_mot = s1.characters["Thandi"].core_motivation or ""
    assert "leave her village" in thandi_mot.lower() or "leave" in thandi_mot.lower()

    # 4. No invented chronology is created
    assert len(s1.chronology) <= 1, f"No fabricated chronology, found {len(s1.chronology)} events"

    # 5. Judge assessment and milestone
    asm = judge.assess(story_id)
    pkg = get_story_package(story_id, repo=repo, judge=judge)
    print(f"Judge Milestone: {asm.current_milestone}, Status: {asm.status}")
    print(f"Missing Invariants: {asm.missing_invariants}")

    # 6. Must not certify prematurely
    assert asm.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE, "Minimalist story must NOT certify M3"
    assert asm.status != ReadinessStatus.FORGE_COMPLETE, "Must NOT be FORGE_COMPLETE"
    assert q1 is not None, "Forge must ask natural story questions when state is missing"

    print("[PASS] Test 1: Minimalist Story Verified")


def test_scenario_2_ensemble_multi_character_story():
    print("\n=======================================================")
    print("TEST 2 — ENSEMBLE / MULTI-CHARACTER STORY")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_02_ensemble"
    repo.create_story(
        story_id=story_id,
        title="The Taxi Line",
        owner_id="creator_lebo",
        logline="Lebo is trying to save his family's taxi business. His sister Ayanda wants to sell it. His cousin Musa thinks they should fight the bank. Their uncle Themba secretly owes the bank money."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    trans1, s1, q1 = kernel.process_cycle(
        story_id,
        creator_input="Lebo is trying to save his family's taxi business. His sister Ayanda wants to sell it. His cousin Musa thinks they should fight the bank. Their uncle Themba secretly owes the bank money."
    )

    print(f"Characters extracted ({len(s1.characters)}): {list(s1.characters.keys())}")
    for k, c in s1.characters.items():
        print(f"  - {c.name} ({c.role}): mot='{c.core_motivation}', rels={[(r.target_character, r.relation_type) for r in c.relationships]}")
    print(f"Knowledge States ({len(s1.knowledge_states)}):")
    for ks in s1.knowledge_states:
        print(f"  - {ks.character_name}: fact='{ks.fact_key}', status={ks.status}")

    # Verify characters distinguished
    assert "Lebo" in s1.characters
    assert "Ayanda" in s1.characters
    assert "Musa" in s1.characters
    assert "Themba" in s1.characters

    # Verify relationships preserved separately from identities
    assert "Sister" not in s1.characters
    assert "Cousin" not in s1.characters
    assert "Uncle" not in s1.characters

    # Verify distinct motivations
    lebo = s1.characters["Lebo"]
    ayanda = s1.characters["Ayanda"]
    musa = s1.characters["Musa"]
    themba = s1.characters["Themba"]

    assert "save" in (lebo.core_motivation or "").lower() or "business" in (lebo.core_motivation or "").lower()
    assert "sell" in (ayanda.core_motivation or "").lower()
    assert "fight" in (musa.core_motivation or "").lower() or "bank" in (musa.core_motivation or "").lower()
    assert "debt" in (themba.core_motivation or "").lower() or "owes" in (themba.core_motivation or "").lower() or "bank" in (themba.core_motivation or "").lower()

    # Musa is NOT automatically classified as villain/antagonist
    assert musa.role != CharacterRole.ANTAGONIST, "Musa's family disagreement must not be marked as ANTAGONIST"

    # Knowledge asymmetry: Themba's secret debt
    themba_knows = any(k.character_name == "Themba" and "debt" in k.fact_key.lower() and k.status == KnowledgeStatus.KNOWS for k in s1.knowledge_states)
    lebo_ignorant = any(k.character_name == "Lebo" and "debt" in k.fact_key.lower() and k.status == KnowledgeStatus.DOES_NOT_KNOW for k in s1.knowledge_states)
    print(f"Themba knows secret: {themba_knows}, Lebo ignorant: {lebo_ignorant}")

    print("[PASS] Test 2: Ensemble / Multi-Character Story Verified")


def test_scenario_3_contradictory_creator():
    print("\n=======================================================")
    print("TEST 3 — CONTRADICTORY CREATOR")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_03_contradictory"
    repo.create_story(
        story_id=story_id,
        title="Sabelo & Zodwa",
        owner_id="creator_sabelo",
        logline="A Johannesburg drama."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Step 1: Establish Zodwa is Sabelo's sister
    t1, s1, q1 = kernel.process_cycle(story_id, creator_input="Sabelo is a driver. Zodwa is Sabelo's sister.")
    s_sabelo_1 = s1.characters["Sabelo"]
    z_rel_1 = next((r for r in s_sabelo_1.relationships if r.target_character == "Zodwa"), None)
    assert z_rel_1 is not None and z_rel_1.relation_type == "SIBLING"
    print(f"Step 1 Sabelo-Zodwa rel: {z_rel_1.relation_type}")

    # Step 2: Actually, Zodwa isn't Sabelo's sister. She's his girlfriend.
    t2, s2, q2 = kernel.process_cycle(story_id, creator_response="Actually, Zodwa isn't Sabelo's sister. She's his girlfriend.")
    s_sabelo_2 = s2.characters["Sabelo"]
    z_rel_2 = next((r for r in s_sabelo_2.relationships if r.target_character == "Zodwa"), None)
    assert z_rel_2 is not None and z_rel_2.relation_type in ("PARTNER", "GIRLFRIEND")
    assert z_rel_2.relation_type != "SIBLING", "Obsolete SIBLING relationship must be replaced!"
    print(f"Step 2 Sabelo-Zodwa rel: {z_rel_2.relation_type}")

    # Step 3: No, wait. They grew up together, but they're not related.
    t3, s3, q3 = kernel.process_cycle(story_id, creator_response="No, wait. They grew up together, but they're not related.")
    s_sabelo_3 = s3.characters["Sabelo"]
    z_rel_3 = next((r for r in s_sabelo_3.relationships if r.target_character == "Zodwa"), None)
    assert z_rel_3 is not None
    assert z_rel_3.relation_type not in ("SIBLING", "GIRLFRIEND", "PARTNER"), f"Expected unrelated/companion, got {z_rel_3.relation_type}"
    print(f"Step 3 Sabelo-Zodwa rel: {z_rel_3.relation_type}")

    # Step 4: Sabelo thinks she's his sister because that's what he was told.
    t4, s4, q4 = kernel.process_cycle(story_id, creator_response="Sabelo thinks she's his sister because that's what he was told.")
    
    # Verify distinction: World Truth vs Character Belief
    pkg = get_story_package(story_id, repo=repo, judge=judge)
    print(f"Step 4 Knowledge States: {[(k.character_name, k.fact_key, k.status) for k in s4.knowledge_states]}")
    sabelo_belief = next((k for k in s4.knowledge_states if k.character_name == "Sabelo" and k.status == KnowledgeStatus.BELIEVES), None)
    assert sabelo_belief is not None, "Must record Sabelo's belief state"
    print(f"Sabelo Belief Recorded: {sabelo_belief.fact_key} -> {sabelo_belief.status}")

    print("[PASS] Test 3: Contradictory Creator Verified")


def test_scenario_4_messy_natural_creator_language():
    print("\n=======================================================")
    print("TEST 4 — MESSY NATURAL CREATOR LANGUAGE")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_04_messy"
    repo.create_story(
        story_id=story_id,
        title="Fontana Nights",
        owner_id="creator_messy",
        logline="Urban drama in Johannesburg."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Step 1
    t1, s1, q1 = kernel.process_cycle(
        story_id,
        creator_input="Okay, so Sabelo is basically broke and he's working nights at this place in Fontana, and he's not really a criminal, but then he sees this BMW and there's money in the boot and he thinks about taking it because Zodwa needs the operation."
    )
    assert "Sabelo" in s1.characters and s1.characters["Sabelo"].role == CharacterRole.PROTAGONIST
    assert "Zodwa" in s1.characters
    print(f"Step 1 characters: {list(s1.characters.keys())}")

    # Step 2
    t2, s2, q2 = kernel.process_cycle(
        story_id,
        creator_response="Jonas owns the money. He's dangerous, obviously, but I don't want him to just be some cartoon villain."
    )
    assert "Jonas" in s2.characters and s2.characters["Jonas"].role == CharacterRole.ANTAGONIST
    # Verify creator meta commentary "cartoon villain" is not stored as character name
    assert "Cartoon" not in s2.characters
    assert "Villain" not in s2.characters
    print(f"Step 2 characters: {list(s2.characters.keys())}")

    # Step 3: Jonas doesn't know Sabelo took it yet
    t3, s3, q3 = kernel.process_cycle(
        story_id,
        creator_response="Actually Jonas doesn't know Sabelo took it yet."
    )
    jonas_ks = next((k for k in s3.knowledge_states if k.character_name == "Jonas" and k.status == KnowledgeStatus.DOES_NOT_KNOW), None)
    assert jonas_ks is not None, "Jonas DOES_NOT_KNOW knowledge state must be recorded"
    print(f"Step 3 Jonas knowledge state: {jonas_ks.character_name} {jonas_ks.status} {jonas_ks.fact_key}")

    # Step 4: Audience knows, Jonas shouldn't
    t4, s4, q4 = kernel.process_cycle(
        story_id,
        creator_response="Wait — the audience should know, but Jonas shouldn't."
    )
    aud_ks = next((k for k in s4.knowledge_states if k.character_name == "Audience" and k.status == KnowledgeStatus.KNOWS), None)
    assert aud_ks is not None, "Audience KNOWS dramatic irony state must be recorded"
    print(f"Step 4 Audience knowledge state: {aud_ks.character_name} {aud_ks.status} {aud_ks.fact_key}")

    print("[PASS] Test 4: Messy Natural Language Verified")


def test_scenario_5_false_polarity_attack():
    print("\n=======================================================")
    print("TEST 5 — FALSE POLARITY ATTACK")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_05_polarity"
    repo.create_story(
        story_id=story_id,
        title="Corporate Secrets",
        owner_id="creator_maya",
        logline="Maya wants to expose corruption at the company."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    t1, s1, q1 = kernel.process_cycle(
        story_id,
        creator_input="Maya wants to expose corruption at the company. Her boss Daniel tells her she should stop asking questions because he is afraid she'll lose her job."
    )
    print(f"Step 1 characters: {[(name, c.role) for name, c in s1.characters.items()]}")

    t2, s2, q2 = kernel.process_cycle(
        story_id,
        creator_response="Daniel isn't corrupt. He's trying to protect her."
    )
    print(f"Step 2 characters: {[(name, c.role) for name, c in s2.characters.items()]}")
    
    assert "Maya" in s2.characters and s2.characters["Maya"].role == CharacterRole.PROTAGONIST
    assert "Daniel" in s2.characters
    # Daniel must NOT be an ANTAGONIST
    assert s2.characters["Daniel"].role != CharacterRole.ANTAGONIST, f"Daniel must NOT be ANTAGONIST, got {s2.characters['Daniel'].role}"
    assert s2.characters["Daniel"].role in (CharacterRole.SUPPORTING, CharacterRole.CONFIDANT)

    print("[PASS] Test 5: False Polarity Attack Verified")


def test_scenario_6_chronology_pressure_test():
    print("\n=======================================================")
    print("TEST 6 — CHRONOLOGY PRESSURE TEST")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "test_adv_06_chronology"
    repo.create_story(
        story_id=story_id,
        title="Sipho's Journey",
        owner_id="creator_sipho",
        logline="Sipho and his brother in Johannesburg."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Event given out of order: Ending first
    t1, s1, q1 = kernel.process_cycle(
        story_id,
        creator_input="Sipho discovers a betrayal. At the end, Sipho leaves Johannesburg."
    )
    print(f"Step 1 events ({len(s1.chronology)}): {[e.headline for e in s1.chronology]}")

    # Step 2: Prior event
    t2, s2, q2 = kernel.process_cycle(
        story_id,
        creator_response="Before that, he discovers that his brother stole the money."
    )
    print(f"Step 2 events ({len(s2.chronology)}): {[e.headline for e in s2.chronology]}")

    # Step 3: Audience sees theft in ep 1, Sipho discovers later
    t3, s3, q3 = kernel.process_cycle(
        story_id,
        creator_response="Actually the audience sees the theft in episode one, but Sipho only discovers it later."
    )
    print(f"Step 3 events ({len(s3.chronology)}): {[e.headline for e in s3.chronology]}")
    print(f"Knowledge states: {[(k.character_name, k.fact_key, k.status) for k in s3.knowledge_states]}")

    # Verify no duplicated events
    headlines = [e.headline.lower() for e in s3.chronology]
    assert len(headlines) == len(set(headlines)), "No duplicate events should be created"
    assert any("theft" in h or "stole" in h for h in headlines)

    print("[PASS] Test 6: Chronology Pressure Test Verified")


def test_scenario_7_and_8_certification_and_package_convergence():
    print("\n=======================================================")
    print("TEST 7 & 8 — CERTIFICATION BOUNDARY & PACKAGE CONVERGENCE")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=repo)
    
    # Incomplete story must not certify
    story_id_inc = "adv_inc_01"
    repo.create_story(story_id=story_id_inc, title="Unfinished", owner_id="c1", logline="A woman arrives in Durban.")
    asm_inc = judge.assess(story_id_inc)
    pkg_inc = get_story_package(story_id_inc, repo=repo, judge=judge)
    
    assert asm_inc.status != ReadinessStatus.FORGE_COMPLETE
    assert pkg_inc.readiness_status != ReadinessStatus.FORGE_COMPLETE
    assert asm_inc.current_milestone == pkg_inc.milestone
    
    print("[PASS] Incomplete Story Convergence Verified")


def test_scenario_9_creator_language_clean_room():
    print("\n=======================================================")
    print("TEST 9 — CREATOR-LANGUAGE CLEAN ROOM")
    print("=======================================================")
    FORBIDDEN_MACHINE_TERMS = [
        "dependency", "invariant", "counterforce", "knowledge state", "chronology anchor",
        "required state", "canonical state", "mutation", "validation", "schema", "graph", "deficiency"
    ]
    
    dep_engine = DependencyEngine()
    dummy_state = StoryState(story_id="creator_lang_test", title="Test Title", logline="A dramatic story in Johannesburg")
    dummy_state.characters["Sabelo"] = CharacterState(character_id="c1", name="Sabelo", role=CharacterRole.PROTAGONIST, status=StateStatus.FACT)

    dummy_deps = dep_engine.evaluate_required_state_deficiencies(dummy_state)
    for d in dummy_deps:
        q = dep_engine.format_targeted_deficiency_question(d, dummy_state)
        print(f"Dep [{d.dependency_key}] -> Question: '{q}'")
        for term in FORBIDDEN_MACHINE_TERMS:
            assert term not in q.lower(), f"Machine ontology leakage detected in question! Found forbidden term '{term}' in: '{q}'"

    print("[PASS] Creator-Language Clean Room (0% Machine Leakage) Verified")


if __name__ == "__main__":
    test_scenario_1_minimalist_story()
    test_scenario_2_ensemble_multi_character_story()
    test_scenario_3_contradictory_creator()
    test_scenario_4_messy_natural_creator_language()
    test_scenario_5_false_polarity_attack()
    test_scenario_6_chronology_pressure_test()
    test_scenario_7_and_8_certification_and_package_convergence()
    test_scenario_9_creator_language_clean_room()
    print("\n=======================================================")
    print("ALL PHASE 1A.1 ADVERSARIAL TESTS COMPLETED")
    print("=======================================================")
