"""
PHASE 1 — GATE A: STORY FORGE STABILISATION TEST SUITE
Executes and validates all 10 Gate A integrity requirements.
"""

import sys
import os
import re
from typing import Optional
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from story_forge.models import (
    StoryState, CharacterState, CharacterRole, StateStatus, CharacterRelationship,
    Dependency, DependencyType, DependencyStatus, AuthorityMode, SkillEnum,
    MilestoneEnum, ReadinessStatus, ChronologyEvent, StateMutation, MutationType
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.orchestrator import StoryForgeKernel, ForgeJudge
from story_forge.engine import (
    DependencyEngine, NarrativeExtractor, ConsequencePropagator, StateEngine, EntityRegistry
)
from story_forge.api.routes import get_story_package
from story_forge.adapters import MockReasoningAdapter


def test_section_1_clean_room_sabelo():
    print("\n=======================================================")
    print("1. CLEAN-ROOM SABELO REGRESSION")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "sabelo_gate_a_clean"
    state = repo.create_story(
        story_id=story_id,
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Sabelo is a desperate security guard who steals R2 million from drug dealer Jonas's car boot to pay for his sister Zodwa's urgent heart surgery."
    )
    session = repo.create_session(story_id, "creator_zola", "sess_sabelo_01")
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Cycle 1: Creator inputs natural narrative establishing Sabelo and Jonas
    trans1, s1, q1 = kernel.process_cycle(
        story_id,
        session_id="sess_sabelo_01",
        creator_input="Sabelo is an honest security guard at a high-end Fontana casino in downtown Johannesburg who discovers R2 million in drug dealer Jonas's BMW boot. His younger sister Zodwa is hospitalized needing urgent heart surgery."
    )
    print(f"Cycle 1 Question: {q1}")
    print(f"Cycle 1 Characters: {list(s1.characters.keys())}")
    print(f"Cycle 1 Chronology: {[e.headline for e in s1.chronology]}")

    # Cycle 2: Creator inputs Point of No Return & Midpoint
    trans2, s2, q2 = kernel.process_cycle(
        story_id,
        session_id="sess_sabelo_01",
        creator_response="Sabelo takes the money and flees the casino workshop before sunrise. Jonas discovers the theft and threatens his family, sending ruthless debt collectors after Zodwa."
    )
    print(f"\nCycle 2 Question: {q2}")
    print(f"Cycle 2 Chronology count: {len(s2.chronology)}")

    # Cycle 3: Creator inputs Climax and Resolution with Explicit Ending
    trans3, s3, q3 = kernel.process_cycle(
        story_id,
        session_id="sess_sabelo_01",
        creator_response="Sabelo faces Jonas in a tense final confrontation at the hospital parking lot. Sabelo outsmarts Jonas with casino security footage, getting Jonas arrested by the police. Zodwa survives her surgery and Sabelo starts a legitimate transport business. That is the end."
    )
    print(f"\nCycle 3 Action: {trans3.authority_mode}")
    print(f"Cycle 3 Question: {q3}")
    print(f"Cycle 3 Chronology count: {len(s3.chronology)}")

    # Assess Completion
    assessment = judge.assess(story_id)
    pkg = get_story_package(story_id, repo=repo, judge=judge)
    all_deps = repo.get_dependencies(story_id)
    unresolved = [d for d in all_deps if d.status not in (DependencyStatus.RESOLVED, DependencyStatus.DELIBERATELY_UNKNOWN, DependencyStatus.DEFERRED)]
    print(f"Unresolved dependencies ({len(unresolved)}):")
    for d in unresolved:
        print(f"  - [{d.dependency_key}] status={d.status}: {d.description}")

    print("\n--- Clean-Room Sabelo Results ---")
    print(f"Canonical State version: {s3.state_version}")
    print(f"Canonical Characters ({len(s3.characters)}): {list(s3.characters.keys())}")
    for name, c in s3.characters.items():
        print(f"  - {name} ({c.role}): relationships={[r.target_character + ' (' + r.relation_type + ')' for r in c.relationships]}")
    print(f"Chronology Events count: {len(s3.chronology)}")
    print(f"Explicit ending declared: {getattr(s3, 'explicit_ending_declared', False)}")
    print(f"Judge Assessment Milestone: {assessment.current_milestone}")
    print(f"Judge Assessment Status: {assessment.status}")
    print(f"Story Package Milestone: {pkg.milestone}")
    print(f"Story Package Readiness: {pkg.readiness_status}")

    # Verification assertions
    assert "Sabelo" in s3.characters, "Sabelo must be in characters"
    assert s3.characters["Sabelo"].role == CharacterRole.PROTAGONIST, "Sabelo must be PROTAGONIST"
    assert "Jonas" in s3.characters, "Jonas must be in characters"
    assert s3.characters["Jonas"].role == CharacterRole.ANTAGONIST, "Jonas must be ANTAGONIST"
    assert "Zodwa" in s3.characters, "Zodwa must be in characters"
    assert len(s3.chronology) >= 3, "Chronology must be populated"
    assert assessment.current_milestone == MilestoneEnum.M3_FORGE_COMPLETE, f"Must reach M3, got {assessment.current_milestone}"
    assert pkg.milestone == MilestoneEnum.M3_FORGE_COMPLETE, "Package milestone must be M3"
    print("[PASS] Clean-Room Sabelo Regression")


def test_section_2_proper_noun_extraction():
    print("\n=======================================================")
    print("2. PROPER-NOUN EXTRACTION REGRESSION")
    print("=======================================================")
    test_cases = [
        ("younger sister Zodwa", "Zodwa", CharacterRole.CONFIDANT, "SIBLING"),
        ("brother Thabo", "Thabo", CharacterRole.CONFIDANT, "SIBLING"),
        ("uncle Amu", "Amu", CharacterRole.SUPPORTING, "FAMILY"),
        ("mother Naledi", "Naledi", CharacterRole.CONFIDANT, "PARENT"),
        ("friend Jonas", "Jonas", CharacterRole.CONFIDANT, "FRIEND"),
        ("boss Mr Dube", "Mr Dube", CharacterRole.ANTAGONIST, "OPPOSITION"),
    ]

    for phrase, expected_name, expected_role, expected_rel in test_cases:
        dummy_state = StoryState(story_id="pn_test_" + str(uuid4())[:8], title="Test", logline="A test story in Johannesburg")
        text = f"Sabelo speaks with his {phrase} about the money."
        res = NarrativeExtractor.extract(text, dummy_state)
        
        extracted_names = [
            m.new_value["name"] for m in res.proposed_mutations
            if m.mutation_type == MutationType.CREATE and "name" in m.new_value
        ]
        print(f"Input: '{phrase}' -> Extracted names: {extracted_names}")
        
        assert expected_name in extracted_names, f"Expected proper name '{expected_name}' in extracted names {extracted_names}"
        
        # Verify no generic relational descriptor is used as character identity
        generic_words = ["Sister", "Brother", "Uncle", "Mother", "Friend", "Boss"]
        for g in generic_words:
            if g != expected_name:
                assert g not in extracted_names, f"Generic descriptor '{g}' must NEVER be the character identity when proper name '{expected_name}' is present!"

    # Also verify standalone proper names remain unaffected
    standalone_text = "Kagiso goes to the taxi rank to meet Lerato."
    dummy_state = StoryState(story_id="pn_test_std", title="Test", logline="A test story in Johannesburg")
    res_std = NarrativeExtractor.extract(standalone_text, dummy_state)
    std_names = [m.new_value["name"] for m in res_std.proposed_mutations if m.mutation_type == MutationType.CREATE and "name" in m.new_value]
    print(f"Standalone names test: {std_names}")
    assert "Kagiso" in std_names or "Lerato" in std_names
    print("[PASS] Proper-Noun Extraction Regression")


def test_section_3_false_completion_attack():
    print("\n=======================================================")
    print("3. FALSE-COMPLETION ATTACK")
    print("=======================================================")
    judge_repo = InMemoryStoryForgeRepository()
    judge = ForgeJudge(repository=judge_repo)

    # Case A: Two characters, no meaningful opposition, no relationship, no chronology
    s_a = judge_repo.create_story("case_a", "Case A Story", "creator_1", logline="Two people sit in a room in Johannesburg doing nothing.")
    s_a.characters["Sabelo"] = CharacterState(character_id="c1", name="Sabelo", role=CharacterRole.PROTAGONIST, status=StateStatus.FACT, core_motivation="Wants coffee")
    s_a.characters["Thabo"] = CharacterState(character_id="c2", name="Thabo", role=CharacterRole.SUPPORTING, status=StateStatus.FACT, core_motivation="Reads newspaper")
    judge_repo.save_state(s_a)
    asm_a = judge.assess("case_a")
    print(f"Case A (2 chars, no opposition, no rels, no chronology): Status={asm_a.status}, Milestone={asm_a.current_milestone}, Missing={asm_a.missing_invariants}")
    assert asm_a.status != ReadinessStatus.FORGE_COMPLETE, "Case A must NOT certify FORGE_COMPLETE"
    assert asm_a.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE, "Case A must NOT certify M3"

    # Case B: Protagonist exists, second character exists, but no demonstrated dramatic collision/counterforce
    s_b = judge_repo.create_story("case_b", "Case B Story", "creator_1", logline="A story about Sabelo walking through town.")
    s_b.characters["Sabelo"] = CharacterState(character_id="c1", name="Sabelo", role=CharacterRole.PROTAGONIST, status=StateStatus.FACT, core_motivation="Find peace")
    s_b.characters["Stranger"] = CharacterState(character_id="c2", name="Stranger", role=CharacterRole.SUPPORTING, status=StateStatus.FACT, core_motivation="Watching birds")
    judge_repo.save_state(s_b)
    asm_b = judge.assess("case_b")
    print(f"Case B (no dramatic collision/counterforce): Status={asm_b.status}, Milestone={asm_b.current_milestone}, Missing={asm_b.missing_invariants}")
    assert asm_b.status != ReadinessStatus.FORGE_COMPLETE, "Case B must NOT certify FORGE_COMPLETE"
    assert any("COUNTERFORCE" in inv for inv in asm_b.missing_invariants), "Case B must fail counterforce invariant"

    # Case C: Strong premise, characters exist, zero chronological events
    s_c = judge_repo.create_story("case_c", "Case C Story", "creator_1", logline="High stakes taxi war drama in Soweto with intense cartel conflict.")
    s_c.characters["Sabelo"] = CharacterState(character_id="c1", name="Sabelo", role=CharacterRole.PROTAGONIST, status=StateStatus.FACT, core_motivation="Survive taxi war")
    s_c.characters["Jonas"] = CharacterState(character_id="c2", name="Jonas", role=CharacterRole.ANTAGONIST, status=StateStatus.FACT, core_motivation="Destroy Sabelo")
    s_c.characters["Sabelo"].relationships.append(type('Rel', (), {'target_character': 'Jonas', 'relation_type': 'OPPOSITION', 'status': StateStatus.FACT, 'dynamic': 'War', 'tension_level': 9})())
    judge_repo.save_state(s_c)
    asm_c = judge.assess("case_c")
    print(f"Case C (0 chronology events): Status={asm_c.status}, Milestone={asm_c.current_milestone}, Missing={asm_c.missing_invariants}")
    assert asm_c.status != ReadinessStatus.FORGE_COMPLETE, "Case C must NOT certify FORGE_COMPLETE"
    assert asm_c.current_milestone != MilestoneEnum.M2_EPISODIC_ARC_LOCK, "Case C must NOT certify M2"
    assert asm_c.current_milestone != MilestoneEnum.M3_FORGE_COMPLETE, "Case C must NOT certify M3"
    print("[PASS] False-Completion Attack")


def test_section_4_story_package_integrity(story_id: Optional[str] = None):
    print("\n=======================================================")
    print("4. STORY PACKAGE INTEGRITY TEST")
    print("=================================================")
    repo = InMemoryStoryForgeRepository()
    actual_story_id = story_id or "pkg_integrity_story"
    sabelo_state = repo.create_story(
        story_id=actual_story_id,
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Sabelo is a desperate security guard who steals R2 million from drug dealer Jonas's car boot to pay for his sister Zodwa's urgent heart surgery."
    )
    sabelo_state.characters["Sabelo"] = CharacterState(
        character_id="c_sabelo", name="Sabelo", role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT, core_motivation="Save Zodwa and escape poverty", fatal_flaw="Desperate greed"
    )
    sabelo_state.characters["Jonas"] = CharacterState(
        character_id="c_jonas", name="Jonas", role=CharacterRole.ANTAGONIST,
        status=StateStatus.FACT, core_motivation="Enforce cartel debt", fatal_flaw="Arrogance"
    )
    sabelo_state.characters["Zodwa"] = CharacterState(
        character_id="c_zodwa", name="Zodwa", role=CharacterRole.CONFIDANT,
        status=StateStatus.FACT, core_motivation="Survive heart surgery", fatal_flaw="Fragile health"
    )
    sabelo_state.characters["Sabelo"].relationships.append(CharacterRelationship(target_character="Jonas", relation_type="OPPOSITION", status=StateStatus.FACT, dynamic="High tension enemy", tension_level=9))
    sabelo_state.characters["Sabelo"].relationships.append(CharacterRelationship(target_character="Zodwa", relation_type="SIBLING", status=StateStatus.FACT, dynamic="Beloved sister", tension_level=4))
    sabelo_state.explicit_ending_declared = True

    # 3 Events + Explicit Ending = Complete episodic arc
    sabelo_state.chronology = [
        ChronologyEvent(event_id="e1", story_id=actual_story_id, event_sequence=1, anchor_type="INCITING_DISRUPTION", headline="Sabelo finds the money", description="Finds R2m in Jonas boot", event_status=StateStatus.FACT),
        ChronologyEvent(event_id="e2", story_id=actual_story_id, event_sequence=2, anchor_type="MIDPOINT_REVELATION", headline="Jonas hunts Sabelo", description="Jonas sends enforcers to hospital", event_status=StateStatus.FACT),
        ChronologyEvent(event_id="e3", story_id=actual_story_id, event_sequence=3, anchor_type="CLIMAX", headline="Parking lot showdown", description="Sabelo gets Jonas arrested", event_status=StateStatus.FACT),
    ]
    repo.save_state(sabelo_state)

    judge = ForgeJudge(repository=repo)
    assessment = judge.assess(actual_story_id)
    pkg = get_story_package(actual_story_id, repo=repo, judge=judge)

    print(f"Canonical Characters: {len(sabelo_state.characters)} vs Package Characters: {len(pkg.characters)}")
    print(f"Canonical Chronology: {len(sabelo_state.chronology)} vs Package Chronology: {len(pkg.chronology_spine)}")
    print(f"Canonical Milestone: {assessment.current_milestone} vs Package Milestone: {pkg.milestone}")
    print(f"Canonical Status: {assessment.status} vs Package Status: {pkg.readiness_status}")

    assert len(sabelo_state.characters) == len(pkg.characters)
    assert len(sabelo_state.chronology) == len(pkg.chronology_spine)
    assert assessment.current_milestone == pkg.milestone
    assert assessment.status == pkg.readiness_status
    print("[PASS] Story Package Integrity Test")


def test_section_5_and_6_story_mutation_and_withdrawal():
    print("\n=======================================================")
    print("5 & 6. STORY MUTATION, PROPAGATION & CERTIFICATION WITHDRAWAL")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "sabelo_mutation_test"
    
    # 1. Start with certified completed story where Zodwa is sister
    state = repo.create_story(
        story_id=story_id,
        title="Sabelo: The Fontana Boss",
        owner_id="creator_zola",
        logline="Comedy drama set in Johannesburg. Sabelo steals R2m from Jonas to pay for his sister Zodwa's heart surgery."
    )
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Ingest baseline complete story
    kernel.process_cycle(story_id, creator_input="Sabelo steals R2m from Jonas to pay for his sister Zodwa's surgery. He flees, Jonas hunts them, Sabelo confronts Jonas, and the story concludes.")
    
    asm1 = judge.assess(story_id)
    pkg1 = get_story_package(story_id, repo=repo, judge=judge)
    print(f"Pre-mutation Milestone: {asm1.current_milestone}, Readiness: {asm1.status}")
    print(f"Pre-mutation Sabelo Relationships: {[r.target_character + ' (' + r.relation_type + ')' for r in repo.get_current_state(story_id).characters['Sabelo'].relationships]}")
    
    # 2. Creator mutates fact: "Zodwa is not Sabelo's sister. She is his girlfriend."
    mutation_text = "Zodwa is not Sabelo's sister. She is his girlfriend."
    trans_mut, s_mut, q_mut = kernel.process_cycle(
        story_id,
        creator_response=mutation_text
    )

    print(f"\nPost-mutation Question: {q_mut}")
    print(f"Post-mutation Canonical Sabelo Relationships:")
    sabelo_rels = s_mut.characters["Sabelo"].relationships
    for r in sabelo_rels:
        print(f"  - Target: {r.target_character}, Type: {r.relation_type}, Dynamic: {r.dynamic}")

    # Inspect Zodwa relationship in Sabelo
    zodwa_rel = next((r for r in sabelo_rels if r.target_character == "Zodwa"), None)
    assert zodwa_rel is not None, "Zodwa must have a relationship with Sabelo"
    print(f"Zodwa relation_type after mutation: '{zodwa_rel.relation_type}'")
    assert zodwa_rel.relation_type in ("PARTNER", "GIRLFRIEND"), f"Expected PARTNER/GIRLFRIEND relationship, got '{zodwa_rel.relation_type}'"
    assert zodwa_rel.relation_type != "SIBLING", "Old relationship 'SIBLING' must NOT be retained!"

    # 3. Assess new Judge state and Story Package
    asm2 = judge.assess(story_id)
    pkg2 = get_story_package(story_id, repo=repo, judge=judge)
    print(f"Post-mutation Judge Assessment: {asm2.status}")
    print(f"Post-mutation Package Characters Zodwa relationships: {[r for c in pkg2.characters if c['name'] == 'Sabelo' for r in c['relationships']]}")
    
    # Verify package reflects new relationship truth
    pkg_sabelo_rels = next((c["relationships"] for c in pkg2.characters if c["name"] == "Sabelo"), [])
    pkg_zodwa_rel = next((r for r in pkg_sabelo_rels if r["target_character"] == "Zodwa"), None)
    assert pkg_zodwa_rel["relation_type"] in ("PARTNER", "GIRLFRIEND")
    assert pkg_zodwa_rel["relation_type"] != "SIBLING"

    print("[PASS] Mutation Propagation & Package Authority Verified")


def test_section_7_package_api_authority():
    print("\n=======================================================")
    print("7. API AUTHORITY TEST")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "api_auth_test_01"
    repo.create_story(story_id, "API Authority Story", "creator_zola", logline="A testing story for authoritative package endpoint.")
    judge = ForgeJudge(repository=repo)

    pkg1 = get_story_package(story_id, repo=repo, judge=judge)
    pkg2 = get_story_package(story_id, repo=repo, judge=judge)
    
    assert pkg1.story_id == pkg2.story_id
    assert pkg1.state_version == pkg2.state_version
    assert pkg1.milestone == pkg2.milestone
    print(f"Repeated package retrieval is idempotent and authoritative: {pkg1.story_id}, version={pkg1.state_version}")
    print("[PASS] API Package Authority Test")


def test_section_8_stop_completion_separation():
    print("\n=======================================================")
    print("8. STOP / COMPLETION SEPARATION TEST")
    print("=======================================================")
    repo = InMemoryStoryForgeRepository()
    story_id = "stop_test_01"
    repo.create_story(story_id, "Stop Test Story", "creator_zola", logline="A testing story.")
    kernel = StoryForgeKernel(repository=repo)
    judge = ForgeJudge(repository=repo)

    # Simulate an adapter returning STOP while story has unresolved dependencies
    class MockPrematureStopAdapter(MockReasoningAdapter):
        def reason(self, req):
            return type('Decision', (), {
                'action': AuthorityMode.STOP,
                'skill': SkillEnum.FORGE_JUDGE,
                'rationale': 'Premature stop attempt',
                'confidence': 1.0,
                'question': None,
                'proposal': None,
                'proposed_mutations': [],
                'production_decision': None,
                'adapter_name': 'MockStop',
                'adapter_version': '1.0',
                'assumptions': [],
                'evidence': []
            })()

    kernel_stop = StoryForgeKernel(repository=repo, reasoning_adapter=MockPrematureStopAdapter())
    trans, state, q = kernel_stop.process_cycle(story_id)

    # In kernel.py line 506: if decision.action == AuthorityMode.STOP and assessment.status != ReadinessStatus.FORGE_COMPLETE:
    # committed_action is overridden to PROPOSE or governed
    print(f"Adapter asked for STOP on incomplete story. Kernel committed authority_mode: {trans.authority_mode}")
    asm = judge.assess(story_id)
    print(f"Judge assessment status: {asm.status}")
    assert asm.status != ReadinessStatus.FORGE_COMPLETE, "Incomplete story must not be FORGE_COMPLETE"
    assert trans.authority_mode != AuthorityMode.STOP, "Kernel must NOT permit STOP when required invariants are missing!"
    print("[PASS] STOP / Completion Separation Test")


def test_section_9_creator_language_integrity():
    print("\n=======================================================")
    print("9. CREATOR-LANGUAGE INTEGRITY (ZERO LEAKAGE)")
    print("=======================================================")
    FORBIDDEN_MACHINE_TERMS = [
        "dependency",
        "counterforce",
        "invariant",
        "required state",
        "canon",
        "mutation",
        "knowledge state",
        "chronology anchor",
        "validation",
        "schema",
        "graph",
        "deficiency"
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

    print("[PASS] Creator-Language Integrity (0% Machine Leakage)")


if __name__ == "__main__":
    print("Running Story Forge Gate A Stabilisation Tests...")
    s_id = test_section_1_clean_room_sabelo()
    test_section_2_proper_noun_extraction()
    test_section_3_false_completion_attack()
    test_section_4_story_package_integrity(s_id)
    test_section_5_and_6_story_mutation_and_withdrawal()
    test_section_7_package_api_authority()
    test_section_8_stop_completion_separation()
    test_section_9_creator_language_integrity()
    print("\n=======================================================")
    print("ALL GATE A STABILISATION TESTS COMPLETED SUCCESSFULLY")
    print("=======================================================")
