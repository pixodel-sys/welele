"""
Welele Story Forge™ — Narrative Reasoning Kernel
Stateful orchestration supervisor executing the canonical Forge cycle.
Enforces the boundary: 'The Adapter reasons. The Kernel governs.'
"""

from typing import Optional, List, Tuple, Dict, Any
from uuid import uuid4
import time
from ..models import (
    StoryState,
    ForgeTransition,
    Dependency,
    DependencyType,
    DependencyStatus,
    ChronologyEvent,
    SkillEnum,
    AuthorityMode,
    Provenance,
    ProductionDecision,
    StateMutation,
    PriorityComponents,
    ReadinessStatus
)
from ..repository import StoryForgeRepository
from ..engine import DependencyEngine, StateEngine, ConsequencePropagator
from ..validation import StoryValidator, ValidationResult
from .judge import ForgeJudge
from ..adapters import (
    ReasoningAdapter,
    MockReasoningAdapter,
    ReasoningRequest,
    ReasoningDecision,
    StoryContext,
    DependencyContext,
    EntityContext,
    EventContext,
    KnowledgeContext,
    PlantContext,
    ForgeObjective
)


class DecisionValidationError(Exception):
    """Raised when an untrusted reasoning adapter decision violates kernel governance."""
    pass


class StoryForgeKernel:
    def __init__(
        self,
        repository: StoryForgeRepository,
        dependency_engine: Optional[DependencyEngine] = None,
        state_engine: Optional[StateEngine] = None,
        propagator: Optional[ConsequencePropagator] = None,
        validator: Optional[StoryValidator] = None,
        reasoning_adapter: Optional[ReasoningAdapter] = None,
        judge: Optional[ForgeJudge] = None
    ):
        self.repository = repository
        self.validator = validator or StoryValidator()
        self.dependency_engine = dependency_engine or DependencyEngine()
        self.state_engine = state_engine or StateEngine(validator=self.validator)
        self.propagator = propagator or ConsequencePropagator()
        self.reasoning_adapter = reasoning_adapter or MockReasoningAdapter()
        self.judge = judge or ForgeJudge(repository=self.repository)

    def process_cycle(
        self,
        story_id: str,
        session_id: str,
        trace_id: str,
        creator_input: Optional[str] = None,
        creator_response: Optional[str] = None,
        new_events: Optional[List[ChronologyEvent]] = None
    ) -> Tuple[ForgeTransition, StoryState, Optional[str]]:
        """
        Executes a single discrete Forge Cycle.
        Returns: (Transition, NewStoryState, NextQuestionOrAction)
        """
        # 1. Load current canonical state
        state = self.repository.get_current_state(story_id)
        if not state:
            raise ValueError(f"No active StoryState found for story_id {story_id}")

        existing_transitions = self.repository.get_transitions(story_id, trace_id=trace_id)
        next_seq = len(existing_transitions) + 1

        # 2. Ingest chronology events if provided
        if new_events:
            for ev in new_events:
                self.repository.save_event(ev)

        # 3. Detect dependencies and evaluate required state deficiencies
        events = self.repository.get_events(story_id)
        latest_transition = existing_transitions[-1] if existing_transitions else None
        detected_deps = self.dependency_engine.detect(
            state=state,
            interpretation=latest_transition.interpretation if latest_transition else (creator_input or creator_response or ""),
            events=events
        )
        for dep in detected_deps:
            existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
            if not existing_dep:
                self.repository.save_dependency(dep)

        # 3b. If no active candidate dependencies remain, evaluate required state deficiencies for milestone progression
        all_deps = self.repository.get_dependencies(story_id)
        active_candidates = [
            d for d in all_deps
            if d.status in (DependencyStatus.DETECTED, DependencyStatus.ASSESSED, DependencyStatus.PRIORITISED, DependencyStatus.ACTIVE)
        ]
        if not active_candidates:
            deficient_deps = self.dependency_engine.evaluate_required_state_deficiencies(
                state=state,
                events=events,
                existing_dependencies=all_deps
            )
            for dep in deficient_deps:
                existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
                if not existing_dep:
                    self.repository.save_dependency(dep)
            all_deps = self.repository.get_dependencies(story_id)

        # 4. Select top active dependency
        active_dep = self.dependency_engine.prioritise(all_deps)

        if active_dep:
            self.repository.save_dependency(active_dep)
            skill = self.dependency_engine.select_skill(active_dep, state)
        else:
            skill = SkillEnum.FORGE_JUDGE

        # 5. Context Assembly (Kernel retrieves relevant truth rather than dumping database)
        reasoning_req = self._assemble_reasoning_request(
            state=state,
            active_dep=active_dep,
            events=events,
            creator_input=creator_input,
            creator_response=creator_response
        )

        # 6. Invoke Reasoning Adapter (Untrusted proposal generation)
        start_time = time.perf_counter()
        decision = self.reasoning_adapter.reason(reasoning_req)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 7. Decision Governance & Validation
        self._validate_adapter_decision(decision, reasoning_req, state)

        transition_id = str(uuid4())
        applied_mutations: List[StateMutation] = []
        propagated_consequences = []
        new_state = state

        # 8. State Mutation Flow: Validated Proposals -> State Engine -> Validator -> Commit
        if decision.action in (AuthorityMode.INFER, AuthorityMode.PROPOSE) and decision.proposed_mutations:
            new_state, val_result = self.state_engine.apply_mutations(
                current_state=state,
                mutations=decision.proposed_mutations,
                transition_id=transition_id
            )
            # Consequence propagation ("What else must now be true?")
            propagated_consequences = self.propagator.propagate(
                state=new_state,
                mutations=decision.proposed_mutations,
                events=events
            )
            applied_mutations = decision.proposed_mutations

            # Commit new versioned state
            self.repository.save_state(new_state)

            if active_dep:
                active_dep.status = DependencyStatus.RESOLVED
                active_dep.resolved_by_transition_id = transition_id
                self.repository.save_dependency(active_dep)

        elif decision.action == AuthorityMode.RECORD_PRODUCTION_DECISION and decision.production_decision:
            self.repository.save_production_decision(decision.production_decision)
            if active_dep:
                active_dep.status = DependencyStatus.DEFERRED
                active_dep.resolved_by_transition_id = transition_id
                self.repository.save_dependency(active_dep)

        elif decision.action == AuthorityMode.ASK:
            if active_dep:
                active_dep.status = DependencyStatus.ACTIVE
                self.repository.save_dependency(active_dep)

        # 8b. STOP Governance: Validate untrusted model STOP proposal against DependencyEngine and ForgeJudge
        committed_action = decision.action
        if decision.action == AuthorityMode.STOP:
            # Detect any remaining dependencies across the entire graph
            newly_detected = self.dependency_engine.detect(
                state=new_state,
                interpretation=decision.rationale or "",
                events=events
            )
            for dep in newly_detected:
                existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
                if not existing_dep:
                    self.repository.save_dependency(dep)

            # Synthesize any missing required-state milestone deficiencies
            current_all_deps = self.repository.get_dependencies(story_id)
            deficient_deps = self.dependency_engine.evaluate_required_state_deficiencies(
                state=new_state,
                events=events,
                existing_dependencies=current_all_deps
            )
            for dep in deficient_deps:
                existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
                if not existing_dep:
                    self.repository.save_dependency(dep)

            # Independent evaluation by ForgeJudge
            assessment = self.judge.assess(story_id)
            if assessment.status != ReadinessStatus.FORGE_COMPLETE:
                # LLM proposed STOP, but Kernel/Judge independently verifies completion criteria are NOT met.
                # STOP proposal is overridden to PROPOSE (candidate proposal); story cannot terminate prematurely.
                committed_action = AuthorityMode.PROPOSE

        # 9. Record Immutable ForgeTransition with Provenance Observability
        transition = ForgeTransition(
            transition_id=transition_id,
            story_id=story_id,
            trace_id=trace_id,
            sequence=next_seq,
            creator_input=creator_input,
            interpretation=decision.rationale,
            skill=decision.skill,
            active_dependency_id=active_dep.id if active_dep else None,
            priority_score=active_dep.priority_score if active_dep else 0.0,
            authority_mode=committed_action,
            question_asked=decision.question,
            proposal=decision.proposal,
            creator_response=creator_response,
            state_changes=applied_mutations,
            consequences=propagated_consequences,
            provenance=Provenance(
                session_id=session_id,
                adapter_name=decision.adapter_name,
                adapter_version=decision.adapter_version,
                confidence=decision.confidence,
                assumptions=decision.assumptions,
                evidence=decision.evidence,
                latency_ms=latency_ms,
                state_version_before=state.state_version,
                state_version_after=new_state.state_version
            )
        )
        self.repository.save_transition(transition)

        return transition, new_state, decision.question

    def _assemble_reasoning_request(
        self,
        state: StoryState,
        active_dep: Optional[Dependency],
        events: List[ChronologyEvent],
        creator_input: Optional[str],
        creator_response: Optional[str]
    ) -> ReasoningRequest:
        """
        Assembles deliberate context slices for the reasoning adapter.
        """
        # Story context
        story_ctx = StoryContext(
            story_id=state.story_id,
            title=state.title,
            logline=state.logline,
            theme=state.theme,
            tone=state.tone
        )

        # Dependency context
        dep_ctx = None
        if active_dep:
            dep_ctx = DependencyContext(
                id=active_dep.id,
                dependency_key=active_dep.dependency_key,
                dependency_type=active_dep.dependency_type.value,
                target_entity=active_dep.target_entity,
                description=active_dep.description,
                status=active_dep.status.value,
                priority_score=active_dep.priority_score,
                suggested_skill=active_dep.suggested_skill
            )

        # Relevant entities (target entity or characters in state)
        relevant_entities = []
        for name, char in state.characters.items():
            relevant_entities.append(
                EntityContext(
                    name=name,
                    role=char.role.value if hasattr(char.role, "value") else str(char.role),
                    status=char.status.value if hasattr(char.status, "value") else str(char.status),
                    core_motivation=char.core_motivation,
                    secret_desire=char.secret_desire,
                    fatal_flaw=char.fatal_flaw,
                    relationships=[r.model_dump() for r in char.relationships]
                )
            )

        # Relevant events
        relevant_events = [
            EventContext(
                event_sequence=ev.event_sequence,
                story_time=ev.story_time,
                headline=ev.headline,
                description=ev.description,
                participants=ev.participants,
                location=ev.location
            )
            for ev in events
        ]

        # Relevant knowledge
        relevant_knowledge = [
            KnowledgeContext(
                character_name=k.character_name,
                fact_key=k.fact_key,
                status=k.status.value,
                confidence=k.confidence
            )
            for k in state.knowledge_states
        ]

        # Relevant plants
        relevant_plants = [
            PlantContext(
                element_code=p.element_code,
                description=p.description,
                intended_payoff=p.intended_payoff,
                payoff_status=p.payoff_status
            )
            for p in state.plants
        ]

        return ReasoningRequest(
            story_id=state.story_id,
            state_version=state.state_version,
            story_context=story_ctx,
            active_dependency=dep_ctx,
            relevant_entities=relevant_entities,
            relevant_events=relevant_events,
            relevant_knowledge=relevant_knowledge,
            relevant_plants=relevant_plants,
            available_skills=list(SkillEnum),
            allowed_authority_modes=list(AuthorityMode),
            objective=ForgeObjective.RESOLVE_DEPENDENCY if active_dep else ForgeObjective.ASSESS_COMPLETION,
            creator_input=creator_input,
            creator_response=creator_response
        )

    def _validate_adapter_decision(
        self,
        decision: ReasoningDecision,
        request: ReasoningRequest,
        state: StoryState
    ) -> None:
        """
        Validates untrusted reasoning adapter output.
        Enforces authority mode permissions, single question rule, and canon protection.
        """
        if decision.action not in request.allowed_authority_modes:
            raise DecisionValidationError(
                f"Reasoning decision action '{decision.action}' is not in allowed modes: {request.allowed_authority_modes}"
            )

        if decision.action == AuthorityMode.ASK:
            if not decision.question or not decision.question.strip():
                raise DecisionValidationError("Action ASK requires a non-empty primary question.")

        # Validate proposed mutations against existing canon
        for mut in decision.proposed_mutations:
            val_result = self.validator.validate_mutation(state, mut)
            if not val_result.is_valid:
                errors = "; ".join([e.conflict for e in val_result.errors])
                raise DecisionValidationError(f"Proposed mutation violates domain invariants: {errors}")
