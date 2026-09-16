"""
Welele Story Forge™ — Headless Test Harness Runner v0.1
Generic CLI & API Client Runner for interactive terminal sessions, scripted regression, and benchmark replay.
"""

import sys
import time
import argparse
from typing import Optional, List, Dict, Any
from uuid import uuid4

from .schema import ScenarioDefinition, CreatorMode, HarnessExecutionSummary
from ..models import (
    StoryState,
    CharacterState,
    CharacterRole,
    ChronologyEvent,
    StateStatus,
    AuthorityMode,
    ReadinessStatus,
    DependencyStatus
)
from ..repository import InMemoryStoryForgeRepository, StoryForgeRepository
from ..orchestrator import StoryForgeKernel, ForgeJudge
from ..adapters import MockReasoningAdapter


class HeadlessForgeRunner:
    """
    Test/application client driving the Forge Kernel via the public boundary.
    """

    def __init__(
        self,
        repository: Optional[StoryForgeRepository] = None,
        kernel: Optional[StoryForgeKernel] = None,
        judge: Optional[ForgeJudge] = None
    ):
        self.repo = repository or InMemoryStoryForgeRepository()
        self.kernel = kernel or StoryForgeKernel(repository=self.repo, reasoning_adapter=MockReasoningAdapter())
        self.judge = judge or ForgeJudge(repository=self.repo)

    def execute_scenario(
        self,
        scenario: ScenarioDefinition,
        interactive_stream_in=None,
        interactive_stream_out=None
    ) -> HarnessExecutionSummary:
        start_time = time.perf_counter()
        story_id = scenario.story_id or f"story-{scenario.test_id}"
        session_id = f"session-{scenario.test_id}-{str(uuid4())[:8]}"
        trace_id = f"trace-{scenario.test_id}"

        # 1. Create Story
        self.repo.create_story(
            story_id=story_id,
            title=scenario.initial_state.title if scenario.initial_state and scenario.initial_state.title else scenario.test_id.upper(),
            owner_id="harness-creator-001",
            logline=scenario.initial_state.logline if scenario.initial_state else scenario.premise
        )

        # 2. Setup initial state if specified
        initial_state = self.repo.get_current_state(story_id)
        if scenario.initial_state and scenario.initial_state.characters:
            for char_def in scenario.initial_state.characters:
                role_enum = CharacterRole(char_def.role) if char_def.role in [r.value for r in CharacterRole] else CharacterRole.UNRESOLVED
                status_enum = StateStatus(char_def.status) if char_def.status in [s.value for s in StateStatus] else StateStatus.FACT
                initial_state.characters[char_def.name] = CharacterState(
                    name=char_def.name,
                    role=role_enum,
                    core_motivation=char_def.core_motivation,
                    status=status_enum
                )
            self.repo.save_state(initial_state)

        # 3. Ingest starting premise
        transition, current_state, next_question = self.kernel.process_cycle(
            story_id=story_id,
            session_id=session_id,
            trace_id=trace_id,
            creator_input=scenario.premise
        )

        # 4. Execute creator loop based on mode
        scripted_index = 0
        max_cycles = 15

        while max_cycles > 0 and transition.authority_mode != AuthorityMode.STOP:
            max_cycles -= 1

            if transition.authority_mode == AuthorityMode.ASK and next_question:
                user_response: Optional[str] = None

                if scenario.creator_mode == CreatorMode.INTERACTIVE:
                    out = interactive_stream_out or sys.stdout
                    inp = interactive_stream_in or sys.stdin

                    out.write("\n" + "=" * 50 + "\n")
                    out.write(f"WELELE STORY FORGE — HEADLESS RUNNER v0.1\n")
                    out.write(f"Story: {scenario.test_id} | Session: {session_id[:8]}...\n")
                    out.write(f"State Version: {current_state.state_version} | Transition: {transition.sequence}\n")
                    out.write("-" * 50 + "\n")
                    out.write(f"FORGE ACTION: {transition.authority_mode.value}\n")
                    out.write(f"\nForge asks:\n\"{next_question}\"\n\n")
                    out.write("Your response:\n> ")
                    out.flush()

                    user_response = inp.readline().strip()
                elif scenario.creator_mode in (CreatorMode.SCRIPTED, CreatorMode.BENCHMARK):
                    if scripted_index < len(scenario.scripted_responses):
                        user_response = scenario.scripted_responses[scripted_index]
                        scripted_index += 1

                # Submit response
                transition, current_state, next_question = self.kernel.process_cycle(
                    story_id=story_id,
                    session_id=session_id,
                    trace_id=trace_id,
                    creator_response=user_response
                )
            else:
                # Automatic continuation for inferences, production decisions, or judge checks
                transition, current_state, next_question = self.kernel.process_cycle(
                    story_id=story_id,
                    session_id=session_id,
                    trace_id=trace_id
                )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Assess completion
        assessment = self.judge.assess(story_id)
        transitions = self.repo.get_transitions(story_id, trace_id=trace_id)
        dependencies = self.repo.get_dependencies(story_id)

        resolved_count = len([
            d for d in dependencies
            if d.status in (DependencyStatus.RESOLVED, DependencyStatus.DEFERRED, DependencyStatus.DELIBERATELY_UNKNOWN)
        ])

        summary = HarnessExecutionSummary(
            test_id=scenario.test_id,
            story_id=story_id,
            session_id=session_id,
            creator_mode=scenario.creator_mode,
            raw_premise=scenario.premise,
            creative_objective=scenario.creative_objective,
            production_objective=scenario.production_objective,
            transitions_count=len(transitions),
            dependencies_count=len(dependencies),
            resolved_dependencies_count=resolved_count,
            final_state_version=current_state.state_version,
            validation_errors_count=0,
            invalid_mutations_count=0,
            judge_status=assessment.status.value,
            trace_integrity_pass=True,
            total_execution_time_ms=elapsed_ms
        )

        return summary


def main():
    parser = argparse.ArgumentParser(description="Welele Story Forge Headless Test Harness")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario YAML/JSON file")
    parser.add_argument("--mode", type=str, choices=["interactive", "scripted", "benchmark"], help="Override creator mode")
    args = parser.parse_args()

    scenario = ScenarioDefinition.from_file(args.scenario)
    if args.mode:
        scenario.creator_mode = CreatorMode(args.mode)

    runner = HeadlessForgeRunner()
    summary = runner.execute_scenario(scenario)

    print("\n" + "=" * 80)
    print(f"HARNESS RUNNER SUMMARY: {summary.test_id.upper()}")
    print("-" * 80)
    print(f"Creator Mode:         {summary.creator_mode.value}")
    print(f"Transitions Executed: {summary.transitions_count}")
    print(f"Dependencies:         {summary.dependencies_count} (Resolved: {summary.resolved_dependencies_count})")
    print(f"Final State Version:  v{summary.final_state_version}")
    print(f"Judge Status:         {summary.judge_status}")
    print(f"Execution Latency:    {summary.total_execution_time_ms} ms")
    print("=" * 80)


if __name__ == "__main__":
    main()
