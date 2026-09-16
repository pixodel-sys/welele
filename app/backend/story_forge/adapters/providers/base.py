"""
Welele Story Forge™ — LLM Provider Interface & Exceptions v0.1
Defines the thin provider abstraction isolating Story Forge from vendor-specific details.

Architectural Rule:
"The LLM is not Story Forge. The LLM is one replaceable reasoning component.
The durable asset is: Canonical Story State + Dependency Engine + Propagation +
Validation + Knowledge + Chronology + Trace + Completion Judge."
"""

from typing import Protocol, Dict, Any, Optional
from enum import Enum


class ProviderErrorType(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    INVALID_ACTION = "INVALID_ACTION"
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    GENERIC_FAILURE = "GENERIC_FAILURE"


class LLMProviderError(Exception):
    """Base exception for all LLM provider failures."""
    def __init__(
        self,
        message: str,
        error_type: ProviderErrorType = ProviderErrorType.GENERIC_FAILURE,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        retryable: bool = False,
        raw_response: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.provider = provider
        self.model = model
        self.retryable = retryable
        self.raw_response = raw_response


class LLMTimeoutError(LLMProviderError):
    """Raised when the LLM provider times out."""
    def __init__(self, message: str = "LLM request timed out", provider: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message, error_type=ProviderErrorType.TIMEOUT, provider=provider, model=model, retryable=True)


class LLMRateLimitError(LLMProviderError):
    """Raised when rate limits are exceeded."""
    def __init__(self, message: str = "LLM rate limit exceeded", provider: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message, error_type=ProviderErrorType.RATE_LIMIT, provider=provider, model=model, retryable=True)


class LLMUnavailableError(LLMProviderError):
    """Raised when provider service is unreachable or returns 5xx."""
    def __init__(self, message: str = "LLM provider unavailable", provider: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message, error_type=ProviderErrorType.UNAVAILABLE, provider=provider, model=model, retryable=True)


class LLMInvalidOutputError(LLMProviderError):
    """Raised when provider returns unparseable or non-conforming structured output."""
    def __init__(self, message: str, raw_response: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message, error_type=ProviderErrorType.INVALID_OUTPUT, provider=provider, model=model, retryable=False, raw_response=raw_response)


class LLMProvider(Protocol):
    """
    Protocol for structured LLM completion providers.
    Providers are solely responsible for raw model interaction and structured JSON output.
    They have zero knowledge of Story Forge business rules, state, or database.
    """
    provider_name: str
    model_name: str

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.2,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Execute structured completion and return parsed dictionary conforming to response_schema.
        Raises LLMProviderError or one of its subclasses on failure.
        """
        ...
