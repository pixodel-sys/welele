"""
Welele Story Forge™ — Headless Test Harness Scenario Schema v0.1
Defines structured test scenarios, creator modes, and raw starting point invariants.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator
import yaml
import json
import os


class CreatorMode(str, Enum):
    INTERACTIVE = "interactive"  # Human answers questions in terminal
    SCRIPTED = "scripted"        # Predefined creator responses for regression replay
    BENCHMARK = "benchmark"      # Complete evaluation/reporting against recorded fixtures


class InitialCharacterDefinition(BaseModel):
    name: str
    role: str = "UNRESOLVED"
    core_motivation: Optional[str] = None
    status: str = "FACT"


class InitialStateDefinition(BaseModel):
    title: Optional[str] = None
    logline: Optional[str] = None
    characters: List[InitialCharacterDefinition] = Field(default_factory=list)


class ScenarioDefinition(BaseModel):
    test_id: str
    story_id: Optional[str] = None
    premise: str
    creative_objective: str
    production_objective: Optional[str] = None
    creator_mode: CreatorMode = CreatorMode.SCRIPTED
    adapter: str = "MockReasoningAdapter"
    initial_state: Optional[InitialStateDefinition] = None
    scripted_responses: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, file_path: str) -> "ScenarioDefinition":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Scenario file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return cls(**data)

    def verify_no_hidden_assistance(self) -> None:
        """
        'No Hidden Assistance' Invariant Test:
        Ensures a blind test definition does NOT contain pre-baked dependencies,
        predefined questions, story outlines, causal maps, or reasoning hints.
        """
        forbidden_keys = [
            "dependencies",
            "predefined_questions",
            "expected_questions",
            "causal_map",
            "story_outline",
            "reasoning_path"
        ]
        for key in forbidden_keys:
            if key in self.metadata:
                raise ValueError(
                    f"Hidden assistance violation: Scenario contains forbidden key '{key}' in metadata."
                )


class HarnessExecutionSummary(BaseModel):
    """
    Preserves the raw starting point and records final test results.
    """
    test_id: str
    story_id: str
    session_id: str
    creator_mode: CreatorMode
    raw_premise: str
    creative_objective: str
    production_objective: Optional[str] = None
    transitions_count: int
    dependencies_count: int
    resolved_dependencies_count: int
    final_state_version: int
    validation_errors_count: int = 0
    invalid_mutations_count: int = 0
    judge_status: str
    trace_integrity_pass: bool = True
    total_execution_time_ms: float = 0.0
