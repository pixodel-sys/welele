"""
Welele Story Forge™ — Collaborative Forge Loop (Gate 2.1)
The Collaborative Loop orchestrating the Story Reasoning LLM (Conversational Director)
and the Forge Kernel (Truth, Invariants, and Canon Engine).
"""

from typing import Tuple, Optional, List, Dict, Any
from uuid import uuid4
import time

from ..models import (
    StoryState,
    ForgeTransition,
    SkillEnum,
    AuthorityMode,
    Provenance,
    StateStatus
)
from ..repository import StoryForgeRepository, InMemoryStoryForgeRepository
from ..engine import StateEngine, DependencyEngine, ConsequencePropagator
from ..validation import StoryValidator
from .models import (
    FactStatus,
    ExtractedFact,
    RevisionRecord,
    CollaborativeReasoningOutput,
    ForgeReconciliationResult,
    MicroscopeDiagnosticTrace
)
from .director import CollaborativeStoryDirector


class CollaborativeForgeLoop:
    """
    Orchestrates the collaborative storytelling conversation:
    - LLM drives conversation and extracts facts holistically.
    - Forge enforces structural invariants, reconciles dependencies, and commits canonical truth.
    - Emits the 8-Stage Microscope Diagnostic Trace.
    """
    def __init__(
        self,
        repository: Optional[StoryForgeRepository] = None,
        director: Optional[CollaborativeStoryDirector] = None,
        state_engine: Optional[StateEngine] = None,
        dependency_engine: Optional[DependencyEngine] = None,
        propagator: Optional[ConsequencePropagator] = None,
        validator: Optional[StoryValidator] = None
    ):
        self.repository = repository or InMemoryStoryForgeRepository()
        self.validator = validator or StoryValidator()
        self.state_engine = state_engine or StateEngine(validator=self.validator)
        self.dependency_engine = dependency_engine or DependencyEngine()
        self.propagator = propagator or ConsequencePropagator()
        self.director = director or CollaborativeStoryDirector()

    def process_cycle(
        self,
        story_id: str,
        creator_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        story_synopsis: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Tuple[ForgeTransition, StoryState, MicroscopeDiagnosticTrace, str]:
        """
        Executes one complete collaborative reasoning cycle.
        """
        session_id = session_id or f"sess_{uuid4().hex[:8]}"
        trace_id = trace_id or f"trace_{uuid4().hex[:8]}"
        transition_id = str(uuid4())

        # 1. Load Current Canonical State
        current_state = self.repository.get_current_state(story_id)
        if not current_state:
            raise ValueError(f"No active StoryState found for story_id: {story_id}")

        existing_transitions = self.repository.get_transitions(story_id, trace_id=trace_id)
        cycle_index = len(existing_transitions) + 1

        # 2. LLM Evaluates Input Holistically (Conversational Director)
        start_time = time.perf_counter()
        reasoning_output: CollaborativeReasoningOutput = self.director.evaluate(
            story_state=current_state,
            creator_input=creator_input,
            conversation_history=conversation_history,
            story_synopsis=story_synopsis
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 3. Forge Kernel Reconciliation & Invariant Validation
        applied_mutations = []
        rejected_mutations = []
        conflicts_flagged = []
        new_state = current_state

        if reasoning_output.proposed_mutations:
            try:
                new_state, val_result = self.state_engine.apply_mutations(
                    current_state=current_state,
                    mutations=reasoning_output.proposed_mutations,
                    transition_id=transition_id
                )
                applied_mutations.extend(reasoning_output.proposed_mutations)
            except Exception as me:
                conflicts_flagged.append(str(me))
                rejected_mutations.extend(reasoning_output.proposed_mutations)
                new_state = current_state

        # Apply revision records if detected
        for rev in reasoning_output.revisions_detected:
            rev_label = getattr(rev, "revision_type", "REVISION")
            conflicts_flagged.append(f"REVISION [{rev_label} | {rev.entity_or_topic}]: '{rev.previous_fact}' -> '{rev.revised_fact}'")
            for mc in getattr(rev, "material_consequences", []):
                conflicts_flagged.append(f"  -> Consequence: {mc}")

        # Consequence propagation
        propagated_consequences = []
        if applied_mutations:
            propagated_consequences = self.propagator.propagate(
                state=new_state,
                mutations=applied_mutations,
                events=new_state.chronology
            )

        # Determine authority mode from semantic conversational action:
        conv_action = getattr(reasoning_output, "conversational_action", "ASK_QUESTION")
        is_concluded = getattr(reasoning_output, "is_story_concluded", False) or (conv_action == "CONCLUDE_STORY")
        next_q = reasoning_output.next_conversational_move

        if is_concluded or conv_action == "CONCLUDE_STORY":
            auth_mode = AuthorityMode.STOP
            next_q = None
            new_state.explicit_ending_declared = True
        elif conv_action == "SYNTHESIZE_AND_CONTINUE":
            auth_mode = AuthorityMode.ASK if next_q else AuthorityMode.PROPOSE
        elif next_q:
            auth_mode = AuthorityMode.ASK
        else:
            auth_mode = AuthorityMode.PROPOSE

        # Save committed state
        if applied_mutations or reasoning_output.revisions_detected or new_state.explicit_ending_declared:
            self.repository.save_state(new_state)

        # Reconcile satisfied dependencies in the dependency graph
        all_deps = self.repository.get_dependencies(story_id)
        newly_resolved = self.dependency_engine.reconcile_satisfied_dependencies(
            state=new_state,
            events=new_state.chronology,
            existing_dependencies=all_deps
        )
        for dep in newly_resolved:
            dep.resolved_by_transition_id = transition_id
            self.repository.save_dependency(dep)

        # Format summary for trace
        canonical_summary = {
            "characters": {
                name: {
                    "role": c.role.value if hasattr(c.role, "value") else str(c.role),
                    "gender": c.gender,
                    "pronouns": c.pronouns,
                    "motivation": c.core_motivation,
                    "flaw": c.fatal_flaw,
                    "relationships": [f"{r.target_character} ({r.relation_type})" for r in c.relationships]
                }
                for name, c in new_state.characters.items()
            },
            "knowledge_states": [
                f"{k.character_name} knows {k.fact_key}" for k in new_state.knowledge_states
            ],
            "plants": [p.element_code for p in new_state.plants],
            "constraints": [
                f"[{c.category}] {c.description} ({c.status.value})" for c in getattr(new_state, "constraints", [])
            ],
            "resolved_dependencies": [d.dependency_key for d in newly_resolved]
        }

        reconciliation_result = ForgeReconciliationResult(
            mutations_applied=applied_mutations,
            mutations_rejected=rejected_mutations,
            reconciled_dependencies=[d.dependency_key for d in newly_resolved],
            conflicts_flagged=conflicts_flagged,
            state_version_before=current_state.state_version,
            state_version_after=new_state.state_version
        )

        # 4. Construct Microscope Diagnostic Trace
        trace = MicroscopeDiagnosticTrace(
            trace_id=trace_id,
            cycle_index=cycle_index,
            creator_input=creator_input,
            llm_understanding=reasoning_output.llm_understanding,
            facts_extracted=reasoning_output.extracted_facts,
            facts_proposed=reasoning_output.proposed_mutations,
            forge_reconciliation=reconciliation_result,
            canonical_state_summary=canonical_summary,
            what_remains_unclear=reasoning_output.what_remains_unclear,
            why_it_matters_to_the_story=reasoning_output.why_it_matters_to_the_story,
            next_conversational_move=next_q
        )

        # 5. Commit Forge Transition
        transition = ForgeTransition(
            transition_id=transition_id,
            story_id=story_id,
            trace_id=trace_id,
            sequence=cycle_index,
            creator_input=creator_input,
            interpretation=reasoning_output.llm_understanding,
            skill=SkillEnum.EXCAVATOR,
            authority_mode=auth_mode,
            question_asked=next_q,
            creator_response=creator_input,
            state_changes=applied_mutations,
            rejected_mutations=rejected_mutations,
            consequences=propagated_consequences,
            provenance=Provenance(
                session_id=session_id,
                adapter_name="CollaborativeStoryDirector",
                confidence=1.0,
                evidence=[f.statement for f in reasoning_output.extracted_facts],
                latency_ms=latency_ms,
                state_version_before=current_state.state_version,
                state_version_after=new_state.state_version
            )
        )
        self.repository.save_transition(transition)

        return transition, new_state, trace, next_q
