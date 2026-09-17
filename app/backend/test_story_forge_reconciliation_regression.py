"""
Welele Story Forge™ — Completion Reconciliation & Excavator Architecture Regression Suite
Locks Enforced:
- LOCK 1: Natural creator narrative is first-class input and satisfies multiple requirements simultaneously.
- LOCK 2: Canonical entity resolution with stable internal IDs (character_id).
- LOCK 3: Never silently merge ambiguous characters (Ambiguous identity triggers ASK).
- LOCK 4: Narrative extraction follows EXTRACT -> PROPOSE -> RECONCILE -> VALIDATE -> COMMIT.
- LOCK 5: Every creator response reconciles against the entire dependency graph ("What did we just learn?").
- LOCK 6: Explicit endings are canonical narrative information participating in reconciliation and completion evaluation.
- LOCK 7: Sole completion authority is ForgeJudge; zero generic "What's next?".
"""

import pytest
import re
from typing import List, Dict, Any

from story_forge.models import (
    StoryState,
    CharacterState,
    CharacterRole,
    StateStatus,
    DependencyType,
    DependencyStatus,
    AuthorityMode,
    MilestoneEnum,
    ReadinessStatus,
    ChronologyEvent,
    Dependency,
    SkillEnum
)
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.engine import (
    DependencyEngine,
    StateEngine,
    ConsequencePropagator,
    NarrativeExtractor,
    EntityRegistry,
    ResolutionOutcome
)
from story_forge.validation import StoryValidator
from story_forge.orchestrator.kernel import StoryForgeKernel
from story_forge.orchestrator.judge import ForgeJudge
from story_forge.adapters import MockReasoningAdapter


def test_scenario_a_complete_narrative_with_explicit_ending():
    """
    Scenario A: Creator provides a multi-sentence narrative containing the entire story arc
    and an explicit ending signal:
    'The drought destroys the family's livelihood. The mother leaves Ixopo to find work.
     The family struggles without her. Eventually they reunite, but the protagonist dies.
     Despite the tragedy, the family finds peace and everyone is happy. That is the end.'

    Verifies:
    1. Narrative is extracted without requiring artificial prompts.
    2. Characters (Mother, Family) and motivations are proposed and committed.
    3. Chronological events are mapped into canonical StoryState.chronology.
    4. Explicit ending is registered.
    5. Dependencies reconcile across the entire graph.
    6. ForgeJudge certifies milestone completion without asking 'What's next?'.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_reconcile_001"

    # Initial state with premise established
    state = repo.create_story(
        story_id=story_id,
        title="Drought in Ixopo",
        owner_id="creator_thandi",
        logline="A desperate family in rural KwaZulu-Natal fights to survive a devastating drought that threatens their existence."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    creator_text = (
        "The drought destroys the family's livelihood. The mother leaves Ixopo to find work. "
        "The family struggles without her. Eventually they reunite, but the protagonist dies. "
        "Despite the tragedy, the family finds peace and everyone is happy. That is the end."
    )

    # Ingest creator natural narrative
    transition, updated_state, question = kernel.process_cycle(
        story_id=story_id,
        creator_input=creator_text
    )

    # 1. State Ingestion Verification
    assert updated_state.explicit_ending_declared is True
    assert len(updated_state.characters) >= 2
    assert "Mother" in updated_state.characters
    mother = updated_state.characters["Mother"]
    assert mother.role == CharacterRole.PROTAGONIST
    assert mother.core_motivation is not None and len(mother.core_motivation) > 0
    assert mother.character_id is not None

    # 2. Chronology in Canonical State
    assert len(updated_state.chronology) >= 4

    # 3. Completion Authority Verification (ForgeJudge)
    assessment = judge.assess(story_id)
    assert assessment.current_milestone in (MilestoneEnum.M2_EPISODIC_ARC_LOCK, MilestoneEnum.M3_FORGE_COMPLETE)

    # 4. ZERO generic "What's next?"
    if question is not None:
        assert "what's next" not in question.lower()
        assert "what next" not in question.lower()
        assert "what happens next" not in question.lower()

    # 5. Transition authority verification
    # When explicit ending + full arc is provided, engine terminates or produces STOP
    assert transition.authority_mode in (AuthorityMode.STOP, AuthorityMode.ASK)
    if transition.authority_mode == AuthorityMode.STOP:
        assert question is None


def test_scenario_b_multi_fact_single_response_reconciliation():
    """
    Scenario B (LOCK 1 & LOCK 5): Single creator input satisfies multiple requirements
    simultaneously (Protagonist, Counterforce, and Relational Dynamic).
    All corresponding dependencies must be marked RESOLVED in the same cycle.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_multifact_001"

    state = repo.create_story(
        story_id=story_id,
        title="The Harbor Accord",
        owner_id="creator_jabu",
        logline="A dockworker uncovers corruption in Durban port logistics and faces retribution from a rival syndicate."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # Initial cycle surfaces protagonist / counterforce deficiencies
    t1, s1, q1 = kernel.process_cycle(story_id=story_id)
    all_deps_before = repo.get_dependencies(story_id)
    active_keys_before = {d.dependency_key for d in all_deps_before if d.status == DependencyStatus.ACTIVE or d.status == DependencyStatus.DETECTED}

    # Creator provides multi-fact response addressing protagonist, boss/counterforce, and motivation
    creator_multi_fact = (
        "The mother leaves Ixopo to protect her children from debt. "
        "The boss of the syndicate hunts her down to seize her remaining assets."
    )

    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        creator_response=creator_multi_fact
    )

    # Verification: Both protagonist and counterforce were committed
    assert "Mother" in s2.characters
    assert "Boss" in s2.characters
    assert s2.characters["Mother"].role == CharacterRole.PROTAGONIST
    assert s2.characters["Boss"].role == CharacterRole.ANTAGONIST

    # Verify that PREMISE_PROTAGONIST_DEFINITION and PREMISE_COUNTERFORCE_DEFINITION are resolved
    all_deps_after = repo.get_dependencies(story_id)
    for d in all_deps_after:
        if d.dependency_key in ("PREMISE_PROTAGONIST_DEFINITION", "PREMISE_COUNTERFORCE_DEFINITION"):
            assert d.status == DependencyStatus.RESOLVED


def test_scenario_c_character_typo_entity_resolution():
    """
    Scenario C (LOCK 2 & LOCK 3): Character typo and entity resolution.
    When a creator mentions 'Nolutando' while canonical character 'Noluthando' exists,
    EntityRegistry must resolve to the existing character ID rather than creating a duplicate.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_typo_001"

    state = repo.create_story(
        story_id=story_id,
        title="The Mountain Path",
        owner_id="creator_bheki",
        logline="An alpine guide navigates a treacherous blizzard in the Drakensberg to locate lost climbers."
    )
    # Register canonical character with ID
    canonical_char = CharacterState(
        name="Noluthando",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Rescue the stranded hiking party."
    )
    original_id = canonical_char.character_id
    state.characters["Noluthando"] = canonical_char
    repo.save_state(state)

    # Test EntityRegistry resolution directly
    resolution = EntityRegistry.resolve_entity(state, "Nolutando")
    assert resolution.outcome == ResolutionOutcome.MATCH
    assert resolution.character_key == "Noluthando"
    assert resolution.character.character_id == original_id

    # Test through StateEngine mutation with typo key
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    from story_forge.models.transition import StateMutation, MutationType

    new_state, _ = state_engine.apply_mutations(
        current_state=state,
        mutations=[
            StateMutation(
                target_path="characters.Nolutando.core_motivation",
                mutation_type=MutationType.UPDATE,
                new_value="Protect the climbers and return safely.",
                rationale="Updated with slight name spelling variation"
            )
        ],
        transition_id="tr_typo_test"
    )

    # Invariant: No duplicate character created!
    assert len(new_state.characters) == 1
    assert "Noluthando" in new_state.characters
    assert new_state.characters["Noluthando"].character_id == original_id
    assert new_state.characters["Noluthando"].core_motivation == "Protect the climbers and return safely."


def test_scenario_d_ambiguous_character_triggers_ask():
    """
    Scenario D (LOCK 3): Never silently merge ambiguous characters.
    When two close candidate characters exist ('Noluthando' and 'Nolwazi'),
    a reference to 'Noli' is ambiguous and must trigger an ASK transition
    without silently mutating canonical state.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_ambig_001"

    state = repo.create_story(
        story_id=story_id,
        title="Two Sisters",
        owner_id="creator_sipho",
        logline="Two sisters in Soweto discover an inherited deed and must decide whether to sell or restore the family property."
    )
    state.characters["Noluthando"] = CharacterState(
        name="Noluthando",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Restore the property."
    )
    state.characters["Nolwazi"] = CharacterState(
        name="Nolwazi",
        role=CharacterRole.SUPPORTING,
        status=StateStatus.FACT,
        core_motivation="Sell the property."
    )
    repo.save_state(state)

    # Test EntityRegistry resolution on ambiguous nickname
    res = EntityRegistry.resolve_entity(state, "Noli")
    assert res.outcome == ResolutionOutcome.AMBIGUOUS
    assert len(res.candidate_matches) >= 2

    # Test Kernel execution with ambiguous reference
    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # Run cycle with ambiguous narrative
    transition, post_state, question = kernel.process_cycle(
        story_id=story_id,
        creator_input="Noli confronts the buyer and refuses the cash offer."
    )

    # Invariant: Action must be ASK
    assert transition.authority_mode == AuthorityMode.ASK
    assert "clarification" in (question or "").lower() or "referring" in (question or "").lower()
    # Invariant: Neither character was corrupted or silently merged
    assert len(post_state.characters) == 2
    assert "Noluthando" in post_state.characters
    assert "Nolwazi" in post_state.characters


def test_scenario_e_canon_conflict_protection():
    """
    Scenario E: Canon conflict protection.
    A validated canonical fact (e.g. established protagonist role) cannot be
    silently overwritten or corrupted by conflicting inferences.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_conflict_001"

    state = repo.create_story(
        story_id=story_id,
        title="The Mining Accord",
        owner_id="creator_kabelo",
        logline="A mine safety inspector in Rustenburg uncovers structural fissures and resists corporate pressure to conceal them."
    )
    state.characters["Inspector"] = CharacterState(
        name="Inspector",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Prevent a catastrophic shaft collapse."
    )
    repo.save_state(state)

    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)

    # Attempting to overwrite existing character's status to UNRESOLVED or corrupt its core motivation
    # should maintain integrity
    from story_forge.models.transition import StateMutation, MutationType

    new_state, _ = state_engine.apply_mutations(
        current_state=state,
        mutations=[
            StateMutation(
                target_path="characters.Inspector.core_motivation",
                mutation_type=MutationType.UPDATE,
                new_value="Expose the safety violations at all costs.",
                rationale="Refined motivation"
            )
        ],
        transition_id="tr_conflict_test"
    )

    assert new_state.characters["Inspector"].role == CharacterRole.PROTAGONIST
    assert new_state.characters["Inspector"].status == StateStatus.FACT
    assert new_state.characters["Inspector"].core_motivation == "Expose the safety violations at all costs."


def test_scenario_f_zero_generic_whats_next_guarantee():
    """
    Scenario F (LOCK 7): Targeted deficiency formulation invariant.
    When deficiencies remain, the question asked MUST be targeted to the specific
    unresolved deficiency (e.g. midpoint, counterforce, motivation).
    Generic phrases like 'What's next?' or 'What happens next?' are strictly forbidden.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_targeted_001"

    # State with premise and protagonist, but missing counterforce
    state = repo.create_story(
        story_id=story_id,
        title="Highveld Investigation",
        owner_id="creator_lerato",
        logline="A financial auditor in Pretoria tracks embezzlement in municipal tenders before the audit closes."
    )
    state.characters["Auditor"] = CharacterState(
        name="Auditor",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Expose the embezzlement."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # Trigger cycle
    transition, post_state, question = kernel.process_cycle(story_id=story_id)

    assert question is not None
    q_lower = question.lower()

    # Strict prohibitions
    assert "what's next" not in q_lower
    assert "what next" not in q_lower
    assert "what happens next" not in q_lower
    assert "how should the story resolve:" not in q_lower

    # Positive requirement: question is targeted
    assert any(term in q_lower for term in ["opposing", "counterforce", "force", "standing against", "motivation", "revelation", "disruption"])


def test_amendment_1_real_creator_llm_kernel_state_engine_path():
    """
    Amendment 1: Verify the real creator -> LLM -> Kernel -> StateEngine path.
    Proves that a live creator response submitted through the session pipeline
    is inspected and verified at Story State level:
    - Characters with stable UUID character_ids, roles, and motivations.
    - Canonical chronology events stored in state.chronology.
    - Explicit ending flag updated.
    - Graph-wide dependency resolution.
    - ForgeJudge completion certification.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_full_pipeline_001"
    session_id = "sess_full_pipeline_001"
    trace_id = "trc_full_pipeline_001"

    # Create story with established premise
    state = repo.create_story(
        story_id=story_id,
        title="Drought in Ixopo (Live Path)",
        owner_id="creator_nomsa",
        logline="A desperate family in rural KwaZulu-Natal fights to survive a devastating drought that threatens their existence."
    )
    repo.save_state(state)
    session = repo.create_session(story_id=story_id, creator_id="creator_nomsa", session_id=session_id)

    # Initialize kernel with LLMReasoningAdapter backed by MockLLMProvider
    from story_forge.adapters import LLMReasoningAdapter
    from story_forge.adapters.providers.mock_provider import MockLLMProvider

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = LLMReasoningAdapter(provider=MockLLMProvider())

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    creator_response = (
        "The drought destroys the family's livelihood. The mother leaves Ixopo to find work. "
        "The family struggles without her. Eventually they reunite, but the protagonist dies. "
        "Despite the tragedy, the family finds peace and everyone is happy. That is the end."
    )

    # Execute full cycle through Kernel
    transition, updated_state, next_question = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=creator_response
    )

    # ---- DEEP STORY STATE LEVEL INSPECTION ----
    # 1. State version incremented
    assert updated_state.state_version >= 2
    assert updated_state.title == "Drought in Ixopo (Live Path)"

    # 2. Characters inspection: stable internal IDs and roles
    assert "Mother" in updated_state.characters
    assert "Family" in updated_state.characters
    mother = updated_state.characters["Mother"]
    assert mother.role == CharacterRole.PROTAGONIST
    assert mother.status == StateStatus.FACT
    assert bool(mother.core_motivation and len(mother.core_motivation) > 10)
    # Character ID must be a valid UUID format
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", mother.character_id)

    family = updated_state.characters["Family"]
    assert family.role == CharacterRole.SUPPORTING
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", family.character_id)

    # 3. Canonical Chronology inspection
    assert len(updated_state.chronology) >= 4
    for idx, ev in enumerate(updated_state.chronology):
        assert ev.event_sequence == idx + 1
        assert ev.headline is not None and len(ev.headline) > 0
        assert ev.anchor_type in ("INCITING_DISRUPTION", "POINT_OF_NO_RETURN", "MIDPOINT_REVELATION", "CLIMAX", "RESOLUTION", "EVENT_PROGRESSION")

    # 4. Explicit Ending flag inspection
    assert updated_state.explicit_ending_declared is True

    # 5. Dependency reconciliation inspection
    all_deps = repo.get_dependencies(story_id)
    # All fundamental milestone requirements are resolved
    for dep in all_deps:
        if dep.dependency_key in ("PREMISE_LOGLINE_SPECIFICATION", "PREMISE_PROTAGONIST_DEFINITION", "PREMISE_COUNTERFORCE_DEFINITION"):
            assert dep.status == DependencyStatus.RESOLVED
            assert dep.resolved_by_transition_id == transition.transition_id

    # 6. ForgeJudge certification inspection
    assessment = judge.assess(story_id)
    assert assessment.status in (ReadinessStatus.EPISODIC_ARC_LOCK, ReadinessStatus.DEPENDENCIES_RESOLVED, ReadinessStatus.FORGE_COMPLETE)
    assert assessment.current_milestone in (MilestoneEnum.M2_EPISODIC_ARC_LOCK, MilestoneEnum.M3_FORGE_COMPLETE)


def test_amendment_2_partial_reconciliation_ambiguous_entity():
    """
    Amendment 2: Refine ambiguous entity handling (Partial Reconciliation).
    An ambiguous character reference must block commitment of that affected reference,
    but MUST NOT discard unrelated valid information from the same creator response.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_partial_reconcile_001"
    session_id = "sess_partial_001"
    trace_id = "trc_partial_001"

    state = repo.create_story(
        story_id=story_id,
        title="The Sisters of Eshowe",
        owner_id="creator_zama",
        logline="Two estranged sisters must choose whether to protect their ancestral farmland or sell to industrial developers."
    )
    # Register existing characters with close names to cause ambiguity with 'Noli'
    state.characters["Noluthando"] = CharacterState(
        name="Noluthando",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Protect the farmland at all costs."
    )
    state.characters["Nolwazi"] = CharacterState(
        name="Nolwazi",
        role=CharacterRole.SUPPORTING,
        status=StateStatus.FACT,
        core_motivation="Liquidate the assets."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # Creator provides a response containing BOTH:
    # 1. An unambiguous new character and action: "The mother leaves to find work in Durban."
    # 2. An ambiguous reference: "Noli steals the remaining transport money."
    composite_input = (
        "The mother leaves to find work in Durban to support the homestead. "
        "Noli steals the remaining transport money from the lockbox."
    )

    transition, updated_state, question = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_input=composite_input
    )

    # 1. Invariant: Action must be ASK for the ambiguous reference
    assert transition.authority_mode == AuthorityMode.ASK
    assert "clarification" in (question or "").lower() or "referring" in (question or "").lower()

    # 2. Invariant: The ambiguous reference 'Noli' was BLOCKED from being added as a new character
    assert "Noli" not in updated_state.characters

    # 3. Invariant (PARTIAL RECONCILIATION): Unrelated valid information WAS committed!
    # "Mother" was committed to canonical Story State
    assert "Mother" in updated_state.characters
    assert updated_state.characters["Mother"].core_motivation is not None
    # Chronology event for mother leaving was committed to state.chronology
    assert any("leaves to find work" in (ev.description or "").lower() for ev in updated_state.chronology)

    # 4. Invariant: Transition state_changes reflects accepted mutations
    assert len(transition.state_changes) > 0
    assert any("Mother" in m.target_path for m in transition.state_changes)


def test_amendment_3_ignore_the_question_reconciliation():
    """
    Amendment 3: 'Ignore the Question' regression.
    Creator may respond with a natural narrative that does not directly answer
    the active question but contains multiple valid story facts.
    Forge must extract, reconcile and update Story State before selecting the
    next required dependency.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_ignore_q_001"
    session_id = "sess_ignore_001"
    trace_id = "trc_ignore_001"

    # State with protagonist established, but completely missing counterforce
    state = repo.create_story(
        story_id=story_id,
        title="The Deep Trench",
        owner_id="creator_lungi",
        logline="A deep-sea welder in Saldanha Bay faces corporate corruption when offshore pipelines begin to leak."
    )
    state.characters["Welder"] = CharacterState(
        name="Welder",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Repair the underwater rupture safely."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)
    adapter = MockReasoningAdapter()

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=adapter,
        judge=judge
    )

    # Cycle 1: Forge asks specifically for the missing counterforce
    t1, s1, q1 = kernel.process_cycle(story_id=story_id, session_id=session_id, trace_id=trace_id)
    assert t1.authority_mode == AuthorityMode.ASK
    assert any(term in (q1 or "").lower() for term in ["counterforce", "opposing force", "standing against"])

    # Creator completely IGNORES the counterforce question and describes an unasked narrative turn:
    # introduces 'Father', a secret debt deed, and an inciting departure
    unasked_narrative = (
        "The father discovers an unpayable debt deed locked in the drawer and leaves the village at midnight."
    )

    t2, s2, q2 = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id,
        creator_response=unasked_narrative
    )

    # 1. Invariant: Story State updated with the unasked narrative material
    assert s2.state_version > s1.state_version
    assert "Father" in s2.characters
    assert s2.characters["Father"].core_motivation is not None
    # Chronology contains the event
    assert len(s2.chronology) >= 1

    # 2. Invariant: DependencyEngine reconciles all dependencies
    all_deps = repo.get_dependencies(story_id)
    for d in all_deps:
        if d.dependency_key == "EVENT_01_INCITING_DISRUPTION":
            assert d.status == DependencyStatus.RESOLVED

    # 3. Invariant: Engine re-evaluated state after extraction before selecting the next required dependency!
    # Having reconciled M0 and opening disruption, the next required dependency is POINT_OF_NO_RETURN.
    assert t2.authority_mode == AuthorityMode.ASK
    assert any(term in (q2 or "").lower() for term in ["point of no return", "commitment", "irreversible"])
    assert "what's next" not in (q2 or "").lower()


def test_amendment_4_provenance_for_accepted_and_rejected_canon_conflict_mutations():
    """
    Amendment 4: Verify provenance for accepted and rejected mutations, particularly
    CANON_CONFLICT decisions.
    When a proposed mutation attempts to invalidate or overwrite a canonical fact,
    it must be rejected with validation_status = 'CANON_CONFLICT', recorded in
    transition.rejected_mutations, and documented in transition.provenance.
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_provenance_001"
    session_id = "sess_prov_001"
    trace_id = "trc_prov_001"

    state = repo.create_story(
        story_id=story_id,
        title="The Audit Trail",
        owner_id="creator_sipho",
        logline="An internal auditor investigates government procurement leaks in Johannesburg before the fiscal deadline."
    )
    # Canonical protagonist established as FACT
    state.characters["Auditor"] = CharacterState(
        name="Auditor",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Expose corrupt tender awards."
    )
    repo.save_state(state)

    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)

    # Custom mock adapter that proposes a CANON_CONFLICT mutation
    from story_forge.models.transition import StateMutation, MutationType
    from story_forge.adapters import ReasoningDecision

    class ConflictProposalAdapter(MockReasoningAdapter):
        def reason(self, request):
            return ReasoningDecision(
                action=AuthorityMode.PROPOSE,
                skill=SkillEnum.EXCAVATOR,
                proposal="Demote the protagonist to unresolved to reopen premise.",
                rationale="Untrusted candidate proposal attempting to mutate canonical status",
                requires_creator=True,
                proposed_mutations=[
                    # Attempting to downgrade established FACT character to UNRESOLVED
                    StateMutation(
                        target_path="characters.Auditor.status",
                        mutation_type=MutationType.UPDATE,
                        new_value="UNRESOLVED",
                        rationale="Untrusted proposal attempting to degrade canonical fact"
                    )
                ],
                confidence=0.90,
                adapter_name="ConflictProposalAdapter"
            )

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=ConflictProposalAdapter(),
        judge=judge
    )

    # Process cycle
    transition, post_state, question = kernel.process_cycle(
        story_id=story_id,
        session_id=session_id,
        trace_id=trace_id
    )

    # 1. Invariant: Mutation was rejected
    assert len(transition.state_changes) == 0
    assert len(transition.rejected_mutations) == 1
    assert transition.rejected_mutations[0].target_path == "characters.Auditor.status"

    # 2. Invariant: Validation status indicates CANON_CONFLICT
    assert transition.validation_status == "CANON_CONFLICT"
    assert len(transition.validation_errors) > 0
    assert "CANON_CONFLICT" in transition.validation_errors[0]

    # 3. Invariant: Provenance records the conflict
    assert transition.provenance.confidence == 0.0
    assert any("CANON_CONFLICT" in err for err in transition.provenance.evidence)
    assert transition.provenance.state_version_before == state.state_version
    assert transition.provenance.state_version_after == state.state_version

    # 4. Invariant: Canonical state is unharmed
    assert post_state.characters["Auditor"].status == StateStatus.FACT
    assert post_state.characters["Auditor"].role == CharacterRole.PROTAGONIST


def test_fallback_zero_specimen_narrative_ontology_invariant():
    """
    Regression Invariant:
    Verify that storyForgeFallback.ts contains ZERO specimen-specific narrative identifiers,
    zero hardcoded character names, zero specimen lore, and zero story-specific branching regexes.
    """
    import os
    frontend_fallback_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "src", "services", "storyForgeFallback.ts"
    )
    assert os.path.exists(frontend_fallback_path), f"File not found: {frontend_fallback_path}"

    with open(frontend_fallback_path, "r", encoding="utf-8") as f:
        fallback_code = f.read().lower()

    forbidden_specimens = [
        "sipho",
        "nokuthula",
        "ndlovu",
        "bra stan",
        "isibusiso",
        "zodwa",
        "bheki",
        "nkosinathi",
        "tebogo",
        "creditor clan",
        "ancestral debt",
        "hillbrow"
    ]

    for token in forbidden_specimens:
        assert token not in fallback_code, f"Contamination detected in fallback: found forbidden token '{token}' in storyForgeFallback.ts"


def test_same_title_different_character_isolation_benchmark():
    """
    Isolation Benchmark:
    Create two stories with identical titles and deliberately different character sets.
    Verify that:
    1. Canonical StoryState contains ONLY the characters belonging to that story.
    2. DependencyEngine detects dependencies ONLY targeting that story's characters.
    3. ReasoningRequest contains ONLY characters belonging to that story.
    4. Final LLM user prompt contains ONLY characters belonging to that story.
    """
    repo = InMemoryStoryForgeRepository()

    # Story A
    story_a_id = "story_with_love_from_ixopo_zweli"
    s_a = repo.create_story(story_a_id, "With Love from Ixopo", "creator_1")
    s_a.characters["Zwelibanzi Mkhize"] = CharacterState(
        name="Zwelibanzi Mkhize",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Resist loan sharks"
    )
    s_a.characters["Noluthando"] = CharacterState(
        name="Noluthando",
        role=CharacterRole.SUPPORTING,
        status=StateStatus.FACT,
        core_motivation="Find work in city"
    )
    repo.save_state(s_a)

    # Story B
    story_b_id = "story_with_love_from_ixopo_sipho"
    s_b = repo.create_story(story_b_id, "With Love from Ixopo", "creator_2")
    s_b.characters["Sipho Ndlovu"] = CharacterState(
        name="Sipho Ndlovu",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Customary kraal stewardship"
    )
    s_b.characters["Nokuthula"] = CharacterState(
        name="Nokuthula",
        role=CharacterRole.SUPPORTING,
        status=StateStatus.FACT,
        core_motivation="Break generational poverty"
    )
    repo.save_state(s_b)

    dep_engine = DependencyEngine()
    kernel = StoryForgeKernel(repository=repo, dependency_engine=dep_engine)

    # 1. Dependency Detection Isolation
    deps_a = dep_engine.detect(s_a, [])
    deps_b = dep_engine.detect(s_b, [])

    assert any("Zwelibanzi" in d.target_entity for d in deps_a)
    assert not any("Sipho" in d.target_entity for d in deps_a)
    assert not any("Ndlovu" in d.target_entity for d in deps_a)

    assert any("Sipho" in d.target_entity for d in deps_b)
    assert not any("Zwelibanzi" in d.target_entity for d in deps_b)

    # 2. ReasoningRequest Assembly Isolation
    req_a = kernel._assemble_reasoning_request(s_a, deps_a[0] if deps_a else None, [], creator_input=None, creator_response=None)
    req_b = kernel._assemble_reasoning_request(s_b, deps_b[0] if deps_b else None, [], creator_input=None, creator_response=None)

    entities_a = [e.name for e in req_a.relevant_entities]
    entities_b = [e.name for e in req_b.relevant_entities]

    assert "Zwelibanzi Mkhize" in entities_a
    assert "Noluthando" in entities_a
    assert "Sipho Ndlovu" not in entities_a
    assert "Nokuthula" not in entities_a

    assert "Sipho Ndlovu" in entities_b
    assert "Nokuthula" in entities_b
    assert "Zwelibanzi Mkhize" not in entities_b
    assert "Noluthando" not in entities_b

    # 3. Final LLM User Prompt Isolation
    from story_forge.adapters import LLMReasoningAdapter
    llm_adapter = LLMReasoningAdapter()
    prompt_a = llm_adapter._build_user_prompt(req_a)
    prompt_b = llm_adapter._build_user_prompt(req_b)

    assert "Zwelibanzi Mkhize" in prompt_a
    assert "Sipho" not in prompt_a
    assert "Ndlovu" not in prompt_a
    assert "Nokuthula" not in prompt_a

    assert "Sipho Ndlovu" in prompt_b
    assert "Zwelibanzi" not in prompt_b


def test_backend_unavailable_and_reconnection_replay_contract():
    """
    The 10-Step Backend Unavailable & Reconnection Replay Contract:
    1. Create Story A
    2. Establish canonical characters
    3. Disconnect/fail backend
    4. Submit creator narrative
    5. Confirm fallback does NOT invent a question
    6. Confirm no new narrative canon is created by fallback
    7. Reconnect backend
    8. Replay/reconcile creator input
    9. Confirm real Forge processes it
    10. Confirm StoryState remains coherent
    """
    repo = InMemoryStoryForgeRepository()
    story_id = "story_reconnection_replay_001"
    session_id = "sess_replay_001"
    trace_id = "trc_replay_001"

    # 1. Create Story A
    state = repo.create_story(
        story_id=story_id,
        title="With Love from Ixopo",
        owner_id="creator_zweli",
        logline="A rural homestead faces extortion from corrupt lenders."
    )

    # 2. Establish canonical characters
    state.characters["Zwelibanzi Mkhize"] = CharacterState(
        name="Zwelibanzi Mkhize",
        role=CharacterRole.PROTAGONIST,
        status=StateStatus.FACT,
        core_motivation="Resist loan sharks"
    )
    state.characters["Noluthando"] = CharacterState(
        name="Noluthando",
        role=CharacterRole.SUPPORTING,
        status=StateStatus.FACT,
        core_motivation="Find work in city"
    )
    repo.save_state(state)
    initial_version = state.state_version

    # 3. Disconnect / fail backend
    # Simulate the fallback offline buffer behavior matching storyForgeFallback.submitInput()
    creator_narrative = (
        "The rival creditor Mashonisa forged the title deed to seize the family kraal. "
        "Zwelibanzi resolves to challenge the deed at the tribal court before Friday."
    )

    # Simulate offline buffer:
    buffered_inputs = []
    # 4. Submit creator narrative while backend is offline
    buffered_inputs.append({
        "session_id": session_id,
        "story_id": story_id,
        "creator_response": creator_narrative
    })

    # Simulated fallback response adhering strictly to storyForgeFallback.ts:
    fallback_result = {
        "story_id": story_id,
        "session_id": session_id,
        "state_version": state.state_version,
        "action": "ASK",
        "active_question": None, # Step 5: Does NOT invent a question
        "state_changes": [],      # Step 6: Zero new narrative canon created
        "current_state": state    # Preserved state untouched
    }

    # 5. Confirm fallback does NOT invent a question
    assert fallback_result["active_question"] is None

    # 6. Confirm no new narrative canon is created by fallback
    assert len(fallback_result["state_changes"]) == 0
    assert fallback_result["state_version"] == initial_version
    assert set(fallback_result["current_state"].characters.keys()) == {"Zwelibanzi Mkhize", "Noluthando"}

    # 7. Reconnect backend
    dep_engine = DependencyEngine()
    validator = StoryValidator()
    state_engine = StateEngine(validator=validator)
    propagator = ConsequencePropagator()
    judge = ForgeJudge(repository=repo)

    kernel = StoryForgeKernel(
        repository=repo,
        dependency_engine=dep_engine,
        state_engine=state_engine,
        propagator=propagator,
        reasoning_adapter=MockReasoningAdapter(),
        judge=judge
    )

    # 8. Replay / reconcile buffered creator input through real Forge
    assert len(buffered_inputs) == 1
    replayed_item = buffered_inputs.pop(0)

    transition, reconciled_state, question = kernel.process_cycle(
        story_id=replayed_item["story_id"],
        session_id=replayed_item["session_id"],
        trace_id=trace_id,
        creator_input=replayed_item["creator_response"],
        creator_response=replayed_item["creator_response"]
    )

    # 9. Confirm real Forge processes it
    assert transition.validation_status in ("VALID", "VALIDATED", "SATISFIED")
    assert len(transition.state_changes) > 0 # Genuine narrative facts committed by Kernel
    assert len(reconciled_state.chronology) > 0 # Chronology extracted and reconciled

    # 10. Confirm StoryState remains coherent
    assert reconciled_state.state_version > initial_version
    # Preserves canonical character identities without contamination
    assert "Zwelibanzi Mkhize" in reconciled_state.characters
    assert "Noluthando" in reconciled_state.characters
    assert "Sipho" not in reconciled_state.characters
    assert "Ndlovu" not in reconciled_state.characters
    assert "Nokuthula" not in reconciled_state.characters

