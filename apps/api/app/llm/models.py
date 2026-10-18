from dataclasses import dataclass
from typing import Any


class ModelGatewayError(Exception):
    """A safe, provider-neutral inference failure."""


class ProviderUnavailableError(ModelGatewayError):
    pass


class BudgetExceededError(ModelGatewayError):
    pass


class StructuredOutputError(ModelGatewayError):
    pass


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


@dataclass(frozen=True)
class CompletionRequest:
    prompt: str
    max_output_tokens: int = 512
    structured_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class CompletionResult:
    content: str
    input_tokens: int
    output_tokens: int
    model_id: str
    provider: str
    structured: dict[str, Any] | None = None
