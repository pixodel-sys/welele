"""
Welele Story Forge™ — Mock LLM Provider v0.1
Deterministic, scriptable mock provider for testing LLM Reasoning Adapter contracts offline.
"""

from typing import Dict, Any, Optional, Callable, List
import json
import time
from .base import (
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMInvalidOutputError,
    ProviderErrorType
)


class MockLLMProvider(LLMProvider):
    """
    Test double for LLMProvider.
    Allows complete offline control of responses, latencies, and failure injection.
    """
    def __init__(
        self,
        provider_name: str = "mock_provider",
        model_name: str = "mock-reasoner-v1",
        simulated_latency_ms: float = 10.0
    ):
        self.provider_name = provider_name
        self.model_name = model_name
        self.simulated_latency_ms = simulated_latency_ms

        # Handlers and queues
        self.canned_responses: List[Dict[str, Any]] = []
        self.keyed_responses: Dict[str, Dict[str, Any]] = {}
        self.generator_fn: Optional[Callable[[str, str, Dict[str, Any]], Dict[str, Any]]] = None

        # Fault injection switches
        self.force_timeout: bool = False
        self.force_rate_limit: bool = False
        self.force_unavailable: bool = False
        self.force_raw_malformed_json: Optional[str] = None
        self.force_generic_error: Optional[str] = None

        # Inspection audit log
        self.calls_history: List[Dict[str, Any]] = []

    def enqueue_response(self, response_payload: Dict[str, Any]):
        """Queue a structured response to be returned on next call."""
        self.canned_responses.append(response_payload)

    def register_keyed_response(self, match_key: str, response_payload: Dict[str, Any]):
        """Register a response to return whenever match_key is present in user_prompt."""
        self.keyed_responses[match_key] = response_payload

    def set_generator(self, fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]]):
        """Set a dynamic response generator callback."""
        self.generator_fn = fn

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.2,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        call_record = {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "response_schema": response_schema,
            "temperature": temperature,
            "timeout_seconds": timeout_seconds,
            "timestamp": time.time()
        }
        self.calls_history.append(call_record)

        # 1. Fault injection checks
        if self.force_timeout:
            raise LLMTimeoutError(
                message=f"Mock LLM timeout forced after {timeout_seconds}s",
                provider=self.provider_name,
                model=self.model_name
            )

        if self.force_rate_limit:
            raise LLMRateLimitError(
                message="Mock LLM rate limit 429 forced",
                provider=self.provider_name,
                model=self.model_name
            )

        if self.force_unavailable:
            raise LLMUnavailableError(
                message="Mock LLM service 503 unavailable forced",
                provider=self.provider_name,
                model=self.model_name
            )

        if self.force_raw_malformed_json is not None:
            raise LLMInvalidOutputError(
                message=f"Malformed JSON returned by provider: {self.force_raw_malformed_json}",
                raw_response=self.force_raw_malformed_json,
                provider=self.provider_name,
                model=self.model_name
            )

        if self.force_generic_error is not None:
            raise LLMProviderError(
                message=self.force_generic_error,
                error_type=ProviderErrorType.GENERIC_FAILURE,
                provider=self.provider_name,
                model=self.model_name
            )

        # 2. Generator function check (if set and returns a dict)
        if self.generator_fn is not None:
            gen_res = self.generator_fn(system_prompt, user_prompt, response_schema)
            if gen_res is not None:
                return gen_res

        # 3. Keyed match check (reverse insertion order so specific overrides match first)
        for key, resp in reversed(list(self.keyed_responses.items())):
            if key in user_prompt:
                return resp

        # 4. Queue pop check
        if self.canned_responses:
            return self.canned_responses.pop(0)

        # 5. Default STOP fallback
        return {
            "action": "STOP",
            "skill": "ORCHESTRATOR",
            "question": None,
            "proposal": None,
            "proposed_mutations": [],
            "production_decision": None,
            "rationale": "Default mock provider STOP fallback",
            "confidence": 1.0,
            "requires_creator": False,
            "assumptions": [],
            "evidence": []
        }
