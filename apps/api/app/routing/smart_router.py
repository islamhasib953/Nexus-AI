import hashlib
from time import perf_counter

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.llm.models import CompletionRequest, CompletionResult
from app.llm.router import ModelRouter
from app.persistence.models import RoutingDecisionLog
from app.routing.cache import ExactResponseCache
from app.routing.classifier import RequestClassifier, RouteDecision
from app.routing.context import ContextSelectionService, SelectedContext


class SmartRequestRouter:
    def __init__(self, settings: Settings, model_router: ModelRouter) -> None:
        self.settings = settings
        self.model_router = model_router
        self.classifier = RequestClassifier()
        self.cache = ExactResponseCache()
        self.context = ContextSelectionService(settings.router_context_max_chars)

    def select_model(self, decision: RouteDecision, workspace: str) -> str:
        registry = self.model_router.registry
        primary_id = self.model_router.settings.llm_primary_model_id

        # 1. Local or privacy workspace constraint
        if workspace == "local":
            local_models = [
                m for m in registry.all() if "local" in m.capabilities or m.provider == "mock"
            ]
            if local_models:
                return local_models[0].id

        # 2. Match requested capabilities
        required = set(decision.required_capabilities)
        if "arabic" in required:
            arabic_models = [m for m in registry.all() if "arabic" in m.capabilities]
            if arabic_models:
                return arabic_models[0].id

        if "reasoning" in required:
            reasoning_models = [
                m
                for m in registry.all()
                if "reasoning" in m.capabilities or "complex" in m.capabilities
            ]
            if reasoning_models:
                return reasoning_models[0].id

        if "tools" in required:
            tool_models = [
                m for m in registry.all() if m.supports_tools or "tools" in m.capabilities
            ]
            if tool_models:
                try:
                    primary = registry.get(primary_id)
                    if primary.supports_tools or "tools" in primary.capabilities:
                        return primary_id
                except ValueError:
                    pass
                return tool_models[0].id

        return primary_id

    def prepare(
        self,
        db: Session,
        *,
        organization_id: str,
        prompt: str,
        conversation_id: str,
        owner_id: str,
        workspace: str,
    ):
        decision = self.classifier.classify(prompt)
        selected = self.context.select(
            db, conversation_id, prompt, decision.use_conversation_context
        )
        model_id = self.select_model(decision, workspace)
        key = self.cache.make_key(
            organization_id=organization_id,
            owner_id=owner_id,
            workspace=workspace,
            model_id=model_id,
            route_kind=decision.kind,
            prompt=prompt,
            context_fingerprint=hashlib.sha256(selected.prompt.encode("utf-8")).hexdigest(),
        )
        return decision, selected, key

    def complete(
        self,
        db: Session,
        *,
        organization_id: str,
        owner_id: str,
        workspace: str,
        conversation_id: str,
        run_id: str,
        prompt: str,
    ) -> tuple[CompletionResult, RouteDecision, SelectedContext, str]:
        started = perf_counter()
        decision, selected, key = self.prepare(
            db,
            organization_id=organization_id,
            prompt=prompt,
            conversation_id=conversation_id,
            owner_id=owner_id,
            workspace=workspace,
        )
        model_id = self.select_model(decision, workspace)
        if self.settings.router_cache_enabled and decision.cacheable:
            cached = self.cache.get(db, key)
            if cached:
                result = CompletionResult(cached.content, 0, 0, cached.model_id, "cache")
                self._log(
                    db,
                    organization_id,
                    owner_id,
                    run_id,
                    decision,
                    selected,
                    "hit",
                    started,
                    result,
                )
                return result, decision, selected, key
        result = self.model_router.complete(
            db,
            organization_id,
            CompletionRequest(prompt=selected.prompt),
            run_id,
            preferred_model_id=model_id,
        )
        if self.settings.router_cache_enabled and decision.cacheable:
            self.cache.put(
                db,
                organization_id=organization_id,
                owner_id=owner_id,
                workspace=workspace,
                cache_key=key,
                content=result.content,
                model_id=result.model_id,
                route_kind=decision.kind,
                ttl_seconds=self.settings.router_cache_ttl_seconds,
            )
        self._log(
            db,
            organization_id,
            owner_id,
            run_id,
            decision,
            selected,
            "miss_bypass" if not decision.cacheable else "miss",
            started,
            result,
        )
        return result, decision, selected, key

    @staticmethod
    def _log(
        db,
        organization_id,
        owner_id,
        run_id,
        decision,
        selected,
        cache_status,
        started,
        result,
    ):
        db.add(
            RoutingDecisionLog(
                organization_id=organization_id,
                owner_id=owner_id,
                run_id=run_id,
                route_kind=decision.kind,
                cache_status=cache_status,
                context_mode=selected.mode,
                bypass_reason=decision.bypass_reason,
                latency_ms=int((perf_counter() - started) * 1000),
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                confidence=decision.confidence,
                explanation=decision.explanation,
            )
        )
