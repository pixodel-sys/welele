"""
Welele Story Forge™ — Narrative Reasoning Kernel
Stateful orchestration supervisor executing the canonical Forge cycle.
Enforces the boundary: 'The Adapter reasons. The Kernel governs.'
"""

from typing import Optional, List, Tuple, Dict, Any
from uuid import uuid4
import time
import re
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
from ..engine import (
    DependencyEngine,
    StateEngine,
    ConsequencePropagator,
    NarrativeExtractor,
    EntityRegistry,
    ResolutionOutcome,
    StateMutationError
)
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
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        creator_input: Optional[str] = None,
        creator_response: Optional[str] = None,
        new_events: Optional[List[ChronologyEvent]] = None
    ) -> Tuple[ForgeTransition, StoryState, Optional[str]]:
        """
        Executes a single discrete Forge Cycle.
        Follows EXTRACT -> PROPOSE -> RECONCILE -> VALIDATE -> COMMIT.
        Enforces:
        - LOCK 1: Natural creator narrative is first-class input.
        - LOCK 2: Stable character IDs and entity resolution.
        - LOCK 3: Never silently merge ambiguous characters (ASK on ambiguity).
        - LOCK 4: Narrative extraction does not equal canon.
        - LOCK 5: Every creator response reconciles against the entire dependency graph.
        - LOCK 6: Explicit endings participate in reconciliation and completion evaluation.
        - LOCK 7: Sole completion authority is ForgeJudge; zero generic "What's next?".
        """
        session_id = session_id or str(uuid4())
        trace_id = trace_id or str(uuid4())

        # 1. Load current canonical state
        state = self.repository.get_current_state(story_id)
        if not state:
            raise ValueError(f"No active StoryState found for story_id {story_id}")

        existing_transitions = self.repository.get_transitions(story_id, trace_id=trace_id)
        next_seq = len(existing_transitions) + 1
        transition_id = str(uuid4())

        applied_mutations: List[StateMutation] = []
        propagated_consequences = []
        new_state = state

        creator_narrative = (creator_response or creator_input or "").strip()

        # =====================================================================
        # 2. EXTRACT & RESOLVE ENTITIES (LOCK 1, LOCK 2, LOCK 3, LOCK 4)
        # =====================================================================
        if creator_narrative:
            extraction_result = NarrativeExtractor.extract(
                text=creator_narrative,
                current_state=state,
                existing_events_count=len(state.chronology or self.repository.get_events(story_id))
            )

            # LOCK 3: Never silently merge ambiguous characters. If ambiguous: ASK.
            # Amendment 2: Partial reconciliation — block affected ambiguous reference,
            # but do NOT discard unrelated valid information from the same creator response.
            if extraction_result.ambiguities:
                ambiguity_q = f"Clarification needed: {extraction_result.ambiguities[0]}. Could you clarify who this refers to?"

                # Identify ambiguous tokens to block only affected character mutations
                ambiguous_keys = set()
                for amb in extraction_result.ambiguities:
                    m = re.search(r"'([^']+)'", amb)
                    if m:
                        ambiguous_keys.add(m.group(1).lower())

                valid_mutations = [
                    m for m in extraction_result.proposed_mutations
                    if not any(k in m.target_path.lower() for k in ambiguous_keys)
                ]

                if valid_mutations:
                    new_state, _ = self.state_engine.apply_mutations(
                        current_state=state,
                        mutations=valid_mutations,
                        transition_id=transition_id
                    )
                    propagated_consequences = self.propagator.propagate(
                        state=new_state,
                        mutations=valid_mutations,
                        events=new_state.chronology or self.repository.get_events(story_id)
                    )
                    applied_mutations.extend(valid_mutations)

                # Ingest valid proposed chronology events into canonical StoryState
                if extraction_result.proposed_events:
                    for ev in extraction_result.proposed_events:
                        new_state.chronology.append(ev)
                        self.repository.save_event(ev)

                self.repository.save_state(new_state)

                # Reconcile dependencies satisfied by valid partial mutations
                all_deps = self.repository.get_dependencies(story_id)
                newly_resolved = self.dependency_engine.reconcile_satisfied_dependencies(
                    state=new_state,
                    events=new_state.chronology,
                    existing_dependencies=all_deps
                )
                for dep in newly_resolved:
                    dep.resolved_by_transition_id = transition_id
                    self.repository.save_dependency(dep)

                transition = ForgeTransition(
                    transition_id=transition_id,
                    story_id=story_id,
                    trace_id=trace_id,
                    sequence=next_seq,
                    creator_input=creator_input,
                    interpretation=f"Partial reconciliation committed {len(applied_mutations)} valid mutations. Ambiguous character reference blocked pending creator clarification.",
                    skill=SkillEnum.EXCAVATOR,
                    authority_mode=AuthorityMode.ASK,
                    question_asked=ambiguity_q,
                    creator_response=creator_response,
                    state_changes=applied_mutations,
                    consequences=propagated_consequences,
                    provenance=Provenance(
                        session_id=session_id,
                        adapter_name="EntityRegistry",
                        confidence=0.70,
                        evidence=extraction_result.ambiguities,
                        state_version_before=state.state_version,
                        state_version_after=new_state.state_version
                    )
                )
                self.repository.save_transition(transition)
                return transition, new_state, ambiguity_q

            # PROPOSE -> RECONCILE -> VALIDATE -> COMMIT
            if extraction_result.proposed_mutations:
                new_state, _ = self.state_engine.apply_mutations(
                    current_state=state,
                    mutations=extraction_result.proposed_mutations,
                    transition_id=transition_id
                )
                # Consequence propagation
                propagated_consequences = self.propagator.propagate(
                    state=new_state,
                    mutations=extraction_result.proposed_mutations,
                    events=new_state.chronology or self.repository.get_events(story_id)
                )
                applied_mutations.extend(extraction_result.proposed_mutations)

            # Chronology is part of canonical Story State (Repository is persistence)
            if extraction_result.proposed_events:
                for ev in extraction_result.proposed_events:
                    new_state.chronology.append(ev)
                    self.repository.save_event(ev)

            # Commit updated state
            self.repository.save_state(new_state)

        # Ingest caller-supplied new_events if provided
        if new_events:
            for ev in new_events:
                new_state.chronology.append(ev)
                self.repository.save_event(ev)
            self.repository.save_state(new_state)

        events = (new_state.chronology if (hasattr(new_state, 'chronology') and new_state.chronology) else self.repository.get_events(story_id))

        # =====================================================================
        # 3. RECONCILE SATISFIED DEPENDENCIES (LOCK 5)
        # "What did we just learn?" Reconcile against the entire dependency graph.
        # =====================================================================
        all_deps = self.repository.get_dependencies(story_id)
        newly_resolved = self.dependency_engine.reconcile_satisfied_dependencies(
            state=new_state,
            events=events,
            existing_dependencies=all_deps
        )
        for dep in newly_resolved:
            dep.resolved_by_transition_id = transition_id
            self.repository.save_dependency(dep)

        # =====================================================================
        # 4. DETECT & EVALUATE REQUIRED STATE DEFICIENCIES
        # =====================================================================
        all_deps = self.repository.get_dependencies(story_id)
        latest_transition = existing_transitions[-1] if existing_transitions else None
        detected_deps = self.dependency_engine.detect(
            state=new_state,
            interpretation=latest_transition.interpretation if latest_transition else creator_narrative,
            events=events
        )
        for dep in detected_deps:
            existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
            if not existing_dep:
                self.repository.save_dependency(dep)

        all_deps = self.repository.get_dependencies(story_id)
        deficient_deps = self.dependency_engine.evaluate_required_state_deficiencies(
            state=new_state,
            events=events,
            existing_dependencies=all_deps
        )
        for dep in deficient_deps:
            existing_dep = self.repository.get_dependency_by_key(story_id, dep.dependency_key)
            if not existing_dep:
                self.repository.save_dependency(dep)

        all_deps = self.repository.get_dependencies(story_id)

        # Reconcile again after detection/synthesis
        second_resolved = self.dependency_engine.reconcile_satisfied_dependencies(
            state=new_state,
            events=events,
            existing_dependencies=all_deps
        )
        for dep in second_resolved:
            dep.resolved_by_transition_id = transition_id
            self.repository.save_dependency(dep)

        all_deps = self.repository.get_dependencies(story_id)
        active_candidates = [
            d for d in all_deps
            if d.status in (DependencyStatus.DETECTED, DependencyStatus.ASSESSED, DependencyStatus.PRIORITISED, DependencyStatus.ACTIVE)
        ]

        # =====================================================================
        # 5. COMPLETION EVALUATION (ForgeJudge Sole Completion Authority)
        # =====================================================================
        assessment = self.judge.assess(story_id)

        if assessment.status == ReadinessStatus.FORGE_COMPLETE and len(active_candidates) == 0:
            # All milestones M0-M3 certified complete!
            transition = ForgeTransition(
                transition_id=transition_id,
                story_id=story_id,
                trace_id=trace_id,
                sequence=next_seq,
                creator_input=creator_input,
                interpretation="All story milestones (M0-M3) satisfied and certified by ForgeJudge. Forge Complete.",
                skill=SkillEnum.FORGE_JUDGE,
                authority_mode=AuthorityMode.STOP,
                question_asked=None,
                proposal="All canonical story milestones (M0-M3) certified complete.",
                creator_response=creator_response,
                state_changes=applied_mutations,
                consequences=propagated_consequences,
                provenance=Provenance(
                    session_id=session_id,
                    adapter_name="ForgeJudge",
                    confidence=1.0,
                    evidence=[f"Certified milestone: {assessment.current_milestone}"],
                    state_version_before=state.state_version,
                    state_version_after=new_state.state_version
                )
            )
            self.repository.save_transition(transition)
            return transition, new_state, None

        # =====================================================================
        # 6. REASONING & TARGETED DEFICIENCY FORMULATION (LOCK 7)
        # If deficiencies remain: produce a targeted deficiency question. Generic "What's next?" is prohibited.
        # =====================================================================
        active_dep = self.dependency_engine.prioritise(all_deps)

        # If creator provided substantive narrative that was reconciled, formulate targeted deficiency directly
        if creator_narrative and applied_mutations:
            skill = self.dependency_engine.select_skill(active_dep, new_state) if active_dep else SkillEnum.FORGE_JUDGE
            targeted_q = self.dependency_engine.format_targeted_deficiency_question(active_dep, new_state) if active_dep else None
            committed_action = AuthorityMode.ASK if active_dep else AuthorityMode.STOP

            transition = ForgeTransition(
                transition_id=transition_id,
                story_id=story_id,
                trace_id=trace_id,
                sequence=next_seq,
                creator_input=creator_input,
                interpretation=f"Reconciled creator narrative into canonical state. Deficiencies remaining: {len(active_candidates)}",
                skill=skill,
                active_dependency_id=active_dep.id if active_dep else None,
                priority_score=active_dep.priority_score if active_dep else 0.0,
                authority_mode=committed_action,
                question_asked=targeted_q,
                proposal=None,
                creator_response=creator_response,
                state_changes=applied_mutations,
                consequences=propagated_consequences,
                provenance=Provenance(
                    session_id=session_id,
                    adapter_name="NarrativeExtractor",
                    confidence=0.95,
                    evidence=[active_dep.dependency_key] if active_dep else [],
                    state_version_before=state.state_version,
                    state_version_after=new_state.state_version
                )
            )
            self.repository.save_transition(transition)
            return transition, new_state, targeted_q

        # Fallback / Model Reasoning invocation if no direct narrative was extracted or reasoning adapter is explicitly tasked
        if active_dep:
            self.repository.save_dependency(active_dep)
            skill = self.dependency_engine.select_skill(active_dep, new_state)
        else:
            skill = SkillEnum.FORGE_JUDGE

        reasoning_req = self._assemble_reasoning_request(
            state=new_state,
            active_dep=active_dep,
            events=events,
            creator_input=creator_input,
            creator_response=creator_response
        )

        start_time = time.perf_counter()
        decision = self.reasoning_adapter.reason(reasoning_req)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        self._validate_adapter_decision(decision, reasoning_req, new_state)

        # Handle adapter decision
        if decision.action in (AuthorityMode.INFER, AuthorityMode.PROPOSE) and decision.proposed_mutations:
            try:
                new_state, _ = self.state_engine.apply_mutations(
                    current_state=new_state,
                    mutations=decision.proposed_mutations,
                    transition_id=transition_id
                )
                propagated = self.propagator.propagate(
                    state=new_state,
                    mutations=decision.proposed_mutations,
                    events=events
                )
                propagated_consequences.extend(propagated)
                applied_mutations.extend(decision.proposed_mutations)
                self.repository.save_state(new_state)

                if active_dep:
                    active_dep.status = DependencyStatus.RESOLVED
                    active_dep.resolved_by_transition_id = transition_id
                    self.repository.save_dependency(active_dep)
            except StateMutationError as e:
                val_errors = [err.conflict for err in e.validation_result.errors] if e.validation_result else [str(e)]
                val_status = "CANON_CONFLICT" if any("CANON_CONFLICT" in err for err in val_errors) else "INVALID"
                conflict_question = f"Proposed change conflicted with canon: {val_errors[0]}. How would you like to resolve this?"
                transition = ForgeTransition(
                    transition_id=transition_id,
                    story_id=story_id,
                    trace_id=trace_id,
                    sequence=next_seq,
                    creator_input=creator_input,
                    interpretation=f"Rejected mutations due to {val_status}: {val_errors[0]}",
                    skill=decision.skill,
                    active_dependency_id=active_dep.id if active_dep else None,
                    priority_score=active_dep.priority_score if active_dep else 0.0,
                    authority_mode=AuthorityMode.ASK,
                    question_asked=conflict_question,
                    proposal=None,
                    creator_response=creator_response,
                    state_changes=[],
                    rejected_mutations=decision.proposed_mutations,
                    consequences=[],
                    validation_status=val_status,
                    validation_errors=val_errors,
                    provenance=Provenance(
                        session_id=session_id,
                        adapter_name=decision.adapter_name,
                        adapter_version=decision.adapter_version,
                        confidence=0.0,
                        evidence=val_errors,
                        latency_ms=latency_ms,
                        state_version_before=state.state_version,
                        state_version_after=state.state_version
                    )
                )
                self.repository.save_transition(transition)
                return transition, state, conflict_question

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

        # Enforce targeted question (LOCK 7): Generic "What's next?" is prohibited
        effective_question = decision.question
        if decision.action == AuthorityMode.ASK:
            is_generic = not effective_question or any(gen in effective_question.lower() for gen in ["what's next", "what next", "what happens next", "how should the story resolve:"])
            if is_generic and active_dep:
                effective_question = self.dependency_engine.format_targeted_deficiency_question(active_dep, new_state)

        committed_action = decision.action
        if decision.action == AuthorityMode.STOP:
            assessment = self.judge.assess(story_id)
            if assessment.status != ReadinessStatus.FORGE_COMPLETE:
                committed_action = AuthorityMode.PROPOSE

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
            question_asked=effective_question,
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

        return transition, new_state, effective_question


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
                # Canon conflicts are handled by the Kernel via StateMutationError and recorded as rejected mutations
                if any("CANON_CONFLICT" in e.conflict for e in val_result.errors):
                    continue
                errors = "; ".join([e.conflict for e in val_result.errors])
                raise DecisionValidationError(f"Proposed mutation violates domain invariants: {errors}")
