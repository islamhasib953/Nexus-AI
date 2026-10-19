import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.llm.models import (
    BudgetExceededError,
    CompletionRequest,
    CompletionResult,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.llm.providers import ProviderAdapter, build_providers
from app.llm.registry import ModelRegistry
from app.persistence.models import ModelUsage


class ProviderHealth:
    def __init__(self) -> None:
        self.failures: dict[str, int] = {}
        self.unhealthy_until: dict[str, datetime] = {}

    def available(self, provider: str) -> bool:
        unavailable_since = self.unhealthy_until.get(provider, datetime.min.replace(tzinfo=UTC))
        return unavailable_since <= datetime.now(UTC)

    def success(self, provider: str) -> None:
        self.failures[provider] = 0
        self.unhealthy_until.pop(provider, None)

    def failure(self, provider: str) -> None:
        count = self.failures.get(provider, 0) + 1
        self.failures[provider] = count
        self.unhealthy_until[provider] = datetime.now(UTC) + timedelta(seconds=min(60, 2**count))

    def snapshot(self, providers: set[str]) -> list[dict[str, object]]:
        now = datetime.now(UTC)
        return [
            {
                "provider": provider,
                "available": self.available(provider),
                "consecutive_failures": self.failures.get(provider, 0),
                "unhealthy_until": (
                    self.unhealthy_until[provider].isoformat()
                    if provider in self.unhealthy_until and self.unhealthy_until[provider] > now
                    else None
                ),
            }
            for provider in sorted(providers)
        ]


class ModelRouter:
    def __init__(
        self,
        settings: Settings,
        registry: ModelRegistry | None = None,
        providers: dict[str, ProviderAdapter] | None = None,
        health: ProviderHealth | None = None,
    ) -> None:
        self.settings = settings
        self.registry = registry or ModelRegistry()
        self.providers = providers or build_providers(settings, self.registry)
        self.health = health or ProviderHealth()

    def complete(
        self,
        db: Session,
        organization_id: str,
        request: CompletionRequest,
        run_id: str | None = None,
        preferred_model_id: str | None = None,
    ) -> CompletionResult:
        failures: list[str] = []
        structured_error: StructuredOutputError | None = None
        for model_id in self._candidates(preferred_model_id):
            try:
                model = self.registry.get(model_id)
            except ValueError as error:
                failures.append(str(error))
                continue
            if model.paid and not self.settings.llm_allow_paid_fallback:
                failures.append(f"{model_id}: paid fallback is disabled")
                continue
            if not self.health.available(model.provider):
                failures.append(f"{model_id}: provider circuit is open")
                continue
            capability_error = self._validate_request(model_id, model, request)
            if capability_error:
                failures.append(f"{model_id}: {capability_error}")
                continue
            estimated = self._estimate_cost(model_id, request.prompt, request.max_output_tokens)
            self._enforce_budget(db, organization_id, estimated)
            adapter = self.providers[model.provider]
            for _ in range(self.settings.llm_max_retries + 1):
                try:
                    result = adapter.complete(model_id, request)
                    result = self._validate_structured(request, result)
                    self._record_usage(db, organization_id, run_id, result)
                    self.health.success(model.provider)
                    return result
                except ProviderAuthenticationError as error:
                    self.health.failure(model.provider)
                    failures.append(str(error))
                    break
                except (
                    ProviderRateLimitError,
                    ProviderTimeoutError,
                    ProviderUnavailableError,
                ) as error:
                    self.health.failure(model.provider)
                    failures.append(str(error))
                    if not self.health.available(model.provider):
                        break
                except StructuredOutputError as error:
                    failures.append(str(error))
                    structured_error = error
                    break
        if structured_error:
            raise structured_error
        raise ProviderUnavailableError(
            "No configured model provider is available: " + "; ".join(failures)
        )

    @staticmethod
    def _validate_request(model_id, model, request: CompletionRequest) -> str | None:
        estimated_input = max(1, (len(request.prompt) + 3) // 4)
        if estimated_input + request.max_output_tokens > model.context_window:
            return "request exceeds model context window"
        if request.structured_schema and not model.supports_structured_output:
            return "structured output is not supported"
        if request.max_output_tokens <= 0:
            return "max output tokens must be positive"
        return None

    def _candidates(self, preferred_model_id: str | None = None) -> tuple[str, ...]:
        fallbacks = tuple(
            item.strip() for item in self.settings.llm_fallback_model_ids.split(",") if item.strip()
        )
        base = (self.settings.llm_primary_model_id, *fallbacks)
        if preferred_model_id:
            ordered = [preferred_model_id] + [m for m in base if m != preferred_model_id]
            return tuple(ordered)
        return base

    def _enforce_budget(self, db: Session, organization_id: str, estimated: float) -> None:
        # Zero budget semantics: 0.0 disables the budget guard (unlimited usage).
        # Any positive value (> 0.0) strictly enforces the daily budget ceiling.
        if (
            self.settings.llm_tenant_daily_budget_usd <= 0.0
            and self.settings.llm_global_daily_budget_usd <= 0.0
        ):
            return

        since = datetime.now(UTC) - timedelta(days=1)
        if self.settings.llm_tenant_daily_budget_usd > 0.0:
            tenant_total = float(
                db.scalar(
                    select(func.coalesce(func.sum(ModelUsage.estimated_cost_usd), "0")).where(
                        ModelUsage.organization_id == organization_id,
                        ModelUsage.created_at >= since,
                    )
                )
                or 0
            )
            if tenant_total + estimated > self.settings.llm_tenant_daily_budget_usd:
                raise BudgetExceededError("Tenant daily model budget has been reached.")

        if self.settings.llm_global_daily_budget_usd > 0.0:
            global_total = float(
                db.scalar(
                    select(func.coalesce(func.sum(ModelUsage.estimated_cost_usd), "0")).where(
                        ModelUsage.created_at >= since
                    )
                )
                or 0
            )
            if global_total + estimated > self.settings.llm_global_daily_budget_usd:
                raise BudgetExceededError("Global daily model budget has been reached.")

    def _estimate_cost(self, model_id: str, prompt: str, max_output_tokens: int) -> float:
        model = self.registry.get(model_id)
        input_tokens = max(1, (len(prompt) + 3) // 4)
        return (
            input_tokens * model.input_cost_per_million_usd
            + max_output_tokens * model.output_cost_per_million_usd
        ) / 1_000_000

    def _record_usage(
        self,
        db: Session,
        organization_id: str,
        run_id: str | None,
        result: CompletionResult,
    ) -> None:
        model = self.registry.get(result.model_id)
        cost = (
            result.input_tokens * model.input_cost_per_million_usd
            + result.output_tokens * model.output_cost_per_million_usd
        ) / 1_000_000
        db.add(
            ModelUsage(
                organization_id=organization_id,
                run_id=run_id,
                provider=result.provider,
                model_id=result.model_id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                estimated_cost_usd=f"{cost:.8f}",
            )
        )

    def _validate_structured(
        self, request: CompletionRequest, result: CompletionResult
    ) -> CompletionResult:
        if not request.structured_schema:
            return result
        try:
            parsed = json.loads(result.content)
        except json.JSONDecodeError as error:
            raise StructuredOutputError(
                "Provider returned invalid JSON for a structured request."
            ) from error
        required = request.structured_schema.get("required", [])
        if not isinstance(parsed, dict) or any(key not in parsed for key in required):
            raise StructuredOutputError(
                "Provider output did not satisfy required structured fields."
            )
        return CompletionResult(
            result.content,
            result.input_tokens,
            result.output_tokens,
            result.model_id,
            result.provider,
            parsed,
        )
