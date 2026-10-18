import json
from collections.abc import Mapping
from typing import Protocol

import httpx

from app.core.config import Settings
from app.llm.models import CompletionRequest, CompletionResult, ProviderUnavailableError
from app.llm.registry import ModelRegistry


class ProviderAdapter(Protocol):
    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult: ...


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


class MockProvider:
    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        content = f"Mock response: {request.prompt}"
        structured = {"answer": content} if request.structured_schema else None
        if structured:
            content = json.dumps(structured)
        return CompletionResult(
            content=content,
            input_tokens=_estimate_tokens(request.prompt),
            output_tokens=_estimate_tokens(content),
            model_id=model_id,
            provider="mock",
            structured=structured,
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
        }
        if request.structured_schema:
            body["response_format"] = {"type": "json_object"}
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProviderUnavailableError(f"{self.name} request failed safely.") from error
        usage: Mapping[str, int] = payload.get("usage", {})
        return CompletionResult(
            content=str(content),
            input_tokens=int(usage.get("prompt_tokens", _estimate_tokens(request.prompt))),
            output_tokens=int(usage.get("completion_tokens", _estimate_tokens(str(content)))),
            model_id=model_id,
            provider=self.name,
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
        try:
            response = httpx.post(f"{self.base_url}/api/chat", json=body, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            content = payload["message"]["content"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
            raise ProviderUnavailableError("ollama request failed safely.") from error
        return CompletionResult(
            content=str(content),
            input_tokens=_estimate_tokens(request.prompt),
            output_tokens=_estimate_tokens(str(content)),
            model_id=model_id,
            provider="ollama",
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
