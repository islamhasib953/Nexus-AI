from dataclasses import dataclass
from typing import Any


class ModelGatewayError(Exception):
    """A safe, provider-neutral inference failure."""


class ProviderUnavailableError(ModelGatewayError):
    pass


class ProviderAuthenticationError(ModelGatewayError):
    """The provider rejected credentials (HTTP 401/403)."""


class ProviderRateLimitError(ModelGatewayError):
    """The provider rate limit or quota has been reached (HTTP 429)."""


class ProviderTimeoutError(ModelGatewayError):
    """The provider request timed out."""


class BudgetExceededError(ModelGatewayError):
    pass


class StructuredOutputError(ModelGatewayError):
    pass


class ModelCapabilityError(ModelGatewayError):
    """The selected model cannot safely satisfy the requested capability."""


@dataclass(frozen=True)
class ModelSpec:
    id: str
    provider: str
    provider_model: str
    context_window: int
    supports_structured_output: bool
    input_cost_per_million_usd: float = 0.0
    output_cost_per_million_usd: float = 0.0
    paid: bool = False
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_multimodal: bool = False
    requires_api_key: bool = False
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.context_window <= 0:
            raise ValueError("Model context window must be positive.")
        if self.input_cost_per_million_usd < 0 or self.output_cost_per_million_usd < 0:
            raise ValueError("Model costs cannot be negative.")


@dataclass(frozen=True)
class CompletionRequest:
    prompt: str
    max_output_tokens: int = 512
    structured_schema: dict[str, Any] | None = None
    temperature: float = 0.7
    stop: tuple[str, ...] = ()
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class CompletionResult:
    content: str
    input_tokens: int
    output_tokens: int
    model_id: str
    provider: str
    structured: dict[str, Any] | None = None
    latency_ms: int = 0
    raw_usage: dict[str, int] | None = None
