"""
Welele Story Forge™ — HTTP / OpenAI Structured Completion Provider v0.1
Thin client interface for real structured LLM generation via OpenAI-compatible endpoints.
"""

from typing import Dict, Any, Optional
import json
import os
import httpx
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .base import (
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMUnavailableError,
    LLMInvalidOutputError,
    ProviderErrorType
)


class HttpLLMProvider(LLMProvider):
    """
    HTTP Provider connecting to OpenAI / LiteLLM / Generic OpenAI-compatible endpoints.
    Enforces strict structured JSON output and converts HTTP/JSON failures into controlled exceptions.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        provider_name: Optional[str] = None
    ):
        self.api_key = (
            api_key
            or os.getenv("STORY_FORGE_LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or "mock-key"
        )
        # Auto-detect default base_url and model if using Gemini
        default_base_url = "https://api.openai.com/v1"
        default_model = "gpt-4o-mini"
        default_provider = "openai"

        if os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("STORY_FORGE_LLM_BASE_URL"):
            default_base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            default_model = "gemini-3.5-flash"
            default_provider = "gemini"

        self.base_url = (base_url or os.getenv("STORY_FORGE_LLM_BASE_URL", default_base_url)).rstrip("/")
        self.model_name = model_name or os.getenv("STORY_FORGE_LLM_MODEL", default_model)
        self.provider_name = provider_name or os.getenv("STORY_FORGE_LLM_PROVIDER", default_provider)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.2,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Request structured JSON format
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "reasoning_decision",
                    "strict": True,
                    "schema": response_schema
                }
            }
        }

        import time
        max_retries = 8
        backoff_seconds = 3.0

        data = None
        for attempt in range(1, max_retries + 1):
            try:
                with httpx.Client(timeout=timeout_seconds) as client:
                    response = client.post(url, headers=headers, json=payload)
                    
                    # Check HTTP status codes
                    if response.status_code == 429:
                        if attempt < max_retries:
                            retry_wait = backoff_seconds * attempt * 3
                            try:
                                err_data = response.json()
                                for detail in err_data.get("error", {}).get("details", []):
                                    if "retryDelay" in detail:
                                        delay_str = str(detail["retryDelay"]).rstrip("s")
                                        retry_wait = max(retry_wait, float(delay_str) + 2.0)
                            except Exception:
                                pass
                            time.sleep(min(retry_wait, 60.0))
                            continue
                        raise LLMRateLimitError(
                            message=f"Rate limit exceeded (429): {response.text}",
                            provider=self.provider_name,
                            model=self.model_name
                        )
                    elif response.status_code in (500, 502, 503, 504):
                        if attempt < max_retries:
                            time.sleep(backoff_seconds * attempt)
                            continue
                        raise LLMUnavailableError(
                            message=f"LLM service unavailable ({response.status_code}): {response.text}",
                            provider=self.provider_name,
                            model=self.model_name
                        )
                    elif response.status_code >= 400:
                        raise LLMProviderError(
                            message=f"LLM provider error ({response.status_code}): {response.text}",
                            error_type=ProviderErrorType.GENERIC_FAILURE,
                            provider=self.provider_name,
                            model=self.model_name
                        )

                    data = response.json()
                    break
            except (httpx.TimeoutException, httpx.RequestError) as net_err:
                if attempt < max_retries:
                    time.sleep(backoff_seconds * attempt)
                    continue
                if isinstance(net_err, httpx.TimeoutException):
                    raise LLMTimeoutError(
                        message=f"HTTP request timed out after {timeout_seconds}s: {str(net_err)}",
                        provider=self.provider_name,
                        model=self.model_name
                    )
                else:
                    raise LLMUnavailableError(
                        message=f"HTTP connection failed: {str(net_err)}",
                        provider=self.provider_name,
                        model=self.model_name
                    )

        if not data:
            raise LLMUnavailableError(
                message="Failed to retrieve response from LLM endpoint after retries",
                provider=self.provider_name,
                model=self.model_name
            )

        choices = data.get("choices", [])
        if not choices:
            raise LLMInvalidOutputError(
                message="Provider returned empty choices array",
                raw_response=response.text,
                provider=self.provider_name,
                model=self.model_name
            )

        content = choices[0].get("message", {}).get("content")
        if not content:
            raise LLMInvalidOutputError(
                message="Provider message content was null or empty",
                raw_response=response.text,
                provider=self.provider_name,
                model=self.model_name
            )

        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as jde:
            raise LLMInvalidOutputError(
                message=f"Provider content was not valid JSON: {str(jde)}",
                raw_response=content,
                provider=self.provider_name,
                model=self.model_name
            )

        if not isinstance(parsed_json, dict):
            raise LLMInvalidOutputError(
                message=f"Expected JSON object, got {type(parsed_json).__name__}",
                raw_response=content,
                provider=self.provider_name,
                model=self.model_name
            )

        return parsed_json
