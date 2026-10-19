import json
from collections.abc import Mapping
from time import perf_counter
from typing import Protocol

import httpx

from app.core.config import Settings
from app.llm.models import (
    CompletionRequest,
    CompletionResult,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.llm.registry import ModelRegistry


class ProviderAdapter(Protocol):
    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult: ...


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class MockProvider:
    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        started = perf_counter()
        content = f"Mock response: {request.prompt}"
        structured = {"answer": content} if request.structured_schema else None
        if structured:
            content = json.dumps(structured)
        latency_ms = max(1, int((perf_counter() - started) * 1000))
        input_tokens = _estimate_tokens(request.prompt)
        output_tokens = _estimate_tokens(content)
        return CompletionResult(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_id=model_id,
            provider="mock",
            structured=structured,
            latency_ms=latency_ms,
            raw_usage={"prompt_tokens": input_tokens, "completion_tokens": output_tokens},
        )


class OpenAICompatibleProvider:
    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        registry: ModelRegistry,
        timeout: float,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.registry = registry
        self.timeout = timeout

    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        if not self.api_key:
            raise ProviderUnavailableError(f"{self.name} is not configured.")
        model = self.registry.get(model_id)
        body: dict[str, object] = {
            "model": model.provider_model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_output_tokens,
            "temperature": request.temperature,
        }
        if request.stop:
            body["stop"] = list(request.stop)
        if request.structured_schema:
            body["response_format"] = {"type": "json_object"}

        timeout = request.timeout_seconds if request.timeout_seconds is not None else self.timeout
        started = perf_counter()
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except httpx.TimeoutException as error:
            msg = f"{self.name} request timed out after {timeout}s."
            raise ProviderTimeoutError(msg) from error
        except httpx.HTTPStatusError as error:
            status = error.response.status_code
            if status in {401, 403}:
                raise ProviderAuthenticationError(
                    f"{self.name} authentication failed (HTTP {status})."
                ) from error
            if status == 429:
                raise ProviderRateLimitError(
                    f"{self.name} rate limit or quota exceeded (HTTP 429)."
                ) from error
            if status in {408, 504}:
                raise ProviderTimeoutError(
                    f"{self.name} gateway timeout (HTTP {status})."
                ) from error
            raise ProviderUnavailableError(f"{self.name} request failed safely.") from error
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProviderUnavailableError(f"{self.name} request failed safely.") from error

        latency_ms = max(1, int((perf_counter() - started) * 1000))
        usage: Mapping[str, int] = payload.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", _estimate_tokens(request.prompt)))
        completion_tokens = int(usage.get("completion_tokens", _estimate_tokens(str(content))))
        return CompletionResult(
            content=str(content),
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model_id=model_id,
            provider=self.name,
            latency_ms=latency_ms,
            raw_usage=dict(usage) if usage else None,
        )


class OllamaProvider:
    def __init__(self, base_url: str, registry: ModelRegistry, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.registry = registry
        self.timeout = timeout

    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        model = self.registry.get(model_id)
        body: dict[str, object] = {
            "model": model.provider_model,
            "messages": [{"role": "user", "content": request.prompt}],
            "stream": False,
        }
        if request.structured_schema:
            body["format"] = request.structured_schema

        timeout = request.timeout_seconds if request.timeout_seconds is not None else self.timeout
        started = perf_counter()
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=body, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            content = payload["message"]["content"]
        except httpx.TimeoutException as error:
            raise ProviderTimeoutError(f"ollama request timed out after {timeout}s.") from error
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProviderUnavailableError("ollama request failed safely.") from error

        latency_ms = max(1, int((perf_counter() - started) * 1000))
        prompt_tokens = _estimate_tokens(request.prompt)
        completion_tokens = _estimate_tokens(str(content))
        return CompletionResult(
            content=str(content),
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model_id=model_id,
            provider="ollama",
            latency_ms=latency_ms,
        )


def build_providers(settings: Settings, registry: ModelRegistry) -> dict[str, ProviderAdapter]:
    return {
        "mock": MockProvider(),
        "groq": OpenAICompatibleProvider(
            "groq",
            settings.groq_base_url,
            settings.groq_api_key,
            registry,
            settings.llm_timeout_seconds,
        ),
        "huggingface": OpenAICompatibleProvider(
            "huggingface",
            settings.huggingface_base_url,
            settings.huggingface_api_key,
            registry,
            settings.llm_timeout_seconds,
        ),
        "ollama": OllamaProvider(
            settings.ollama_base_url,
            registry,
            settings.llm_timeout_seconds,
        ),
    }
