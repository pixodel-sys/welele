"""
Story Forge Unit Tests: Headless Test Harness Verification
Tests generic runner, YAML scenario loading, no-hidden-assistance validation, and execution summaries.
"""

import os
import io
import pytest
from story_forge.harness import (
    ScenarioDefinition,
    CreatorMode,
    HeadlessForgeRunner,
    HarnessExecutionSummary
)


def test_scenario_loading_and_no_hidden_assistance_validation():
    scenario_path = os.path.join(
        os.path.dirname(__file__), "..", "harness", "scenarios", "blind_001.yaml"
    )
    scenario = ScenarioDefinition.from_file(scenario_path)
    assert scenario.test_id == "blind_001"
    assert "debt owed to a rival clan" in scenario.premise
    assert scenario.creative_objective is not None

    # Invariant: No hidden assistance
    scenario.verify_no_hidden_assistance()

    # Verify that adding a forbidden key fails validation
    scenario.metadata["dependencies"] = ["FAKED_DEPENDENCY"]
    with pytest.raises(ValueError) as exc_info:
        scenario.verify_no_hidden_assistance()
    assert "Hidden assistance violation" in str(exc_info.value)


def test_headless_runner_scripted_inhliziyo_benchmark():
    scenario_path = os.path.join(
        os.path.dirname(__file__), "..", "harness", "scenarios", "inhliziyo_ayiphakelwa.yaml"
    )
    scenario = ScenarioDefinition.from_file(scenario_path)

    runner = HeadlessForgeRunner()
    summary = runner.execute_scenario(scenario)

    assert isinstance(summary, HarnessExecutionSummary)
    assert summary.test_id == "inhliziyo_ayiphakelwa"
    assert summary.transitions_count >= 5
    assert summary.final_state_version >= 5
    assert summary.judge_status in ("DRAMATIC_ENGINE_LOCK", "FORGE_COMPLETE")
    assert summary.validation_errors_count == 0
    assert summary.invalid_mutations_count == 0
    assert summary.trace_integrity_pass is True


def test_headless_runner_blind_001_run():
    scenario_path = os.path.join(
        os.path.dirname(__file__), "..", "harness", "scenarios", "blind_001.yaml"
    )
    scenario = ScenarioDefinition.from_file(scenario_path)

    runner = HeadlessForgeRunner()
    summary = runner.execute_scenario(scenario)

    assert summary.test_id == "blind_001"
    assert summary.transitions_count >= 1
    assert summary.final_state_version >= 1
    assert summary.validation_errors_count == 0


def test_headless_runner_interactive_stream_simulation():
    from story_forge.harness.schema import InitialStateDefinition, InitialCharacterDefinition
    scenario = ScenarioDefinition(
        test_id="interactive_sim_001",
        premise="A young detective discovers an unmarked vault beneath the Johannesburg stock exchange.",
        creative_objective="Develop into a financial crime thriller.",
        creator_mode=CreatorMode.INTERACTIVE,
        initial_state=InitialStateDefinition(
            title="Vault 7",
            characters=[
                InitialCharacterDefinition(name="Detective Sithole", role="UNRESOLVED")
            ]
        )
    )

    fake_input = io.StringIO("He decides to photograph the ledger secretly before alerting his commander.\n")
    fake_output = io.StringIO()

    runner = HeadlessForgeRunner()
    summary = runner.execute_scenario(
        scenario=scenario,
        interactive_stream_in=fake_input,
        interactive_stream_out=fake_output
    )

    out_text = fake_output.getvalue()
    assert "WELELE STORY FORGE — HEADLESS RUNNER" in out_text
    assert "Forge asks:" in out_text
    assert summary.transitions_count >= 1
