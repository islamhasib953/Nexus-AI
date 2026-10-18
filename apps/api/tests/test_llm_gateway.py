from pathlib import Path

import pytest
from app.core.config import Settings
from app.llm.models import (
    BudgetExceededError,
    CompletionRequest,
    CompletionResult,
    ModelSpec,
    ProviderUnavailableError,
    StructuredOutputError,
)
from app.llm.providers import OllamaProvider, OpenAICompatibleProvider
from app.llm.registry import ModelRegistry
from app.llm.router import ModelRouter
from app.main import create_app
from app.persistence.langgraph_store import postgres_checkpointer
from app.persistence.models import ModelUsage
from fastapi.testclient import TestClient
from sqlalchemy import select


class UnavailableProvider:
    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        raise ProviderUnavailableError("provider unavailable")


class FixedProvider:
    def __init__(self, content: str = "fallback") -> None:
        self.content = content

    def complete(self, model_id: str, request: CompletionRequest) -> CompletionResult:
        return CompletionResult(self.content, 3, 2, model_id, "fixed")


class FakeHttpResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def make_app(tmp_path: Path, **values: object):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'llm.db'}", **values)
    return create_app(settings)


def token(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/dev/session", json={"profile": "internal"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_mock_inference_is_verified_end_to_end_and_records_usage(tmp_path: Path) -> None:
    with TestClient(make_app(tmp_path)) as client:
        headers = token(client)
        conversation = client.post("/api/v1/conversations", json={}, headers=headers).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            json={"content": "hello gateway"},
            headers=headers,
        ).json()
        stream = client.get(run["events_url"], headers=headers)
        assert "Mock response: hello gateway" in stream.text
        assert "event: run_completed" in stream.text
        with client.app.state.database.session_factory() as session:
            usage = session.scalars(select(ModelUsage).where(ModelUsage.run_id == run["id"])).all()
            assert len(usage) == 1
            assert usage[0].model_id == "mock-chat"


def test_unavailable_primary_falls_back_to_configured_model(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'fallback.db'}",
        llm_primary_model_id="primary",
        llm_fallback_model_ids="fallback",
        llm_max_retries=0,
    )
    registry = ModelRegistry(
        (
            ModelSpec("primary", "first", "first", 100, False),
            ModelSpec("fallback", "second", "second", 100, False),
        )
    )
    router = ModelRouter(
        settings,
        registry,
        {"first": UnavailableProvider(), "second": FixedProvider()},
    )
    app = create_app(settings)
    with TestClient(app) as client:
        with client.app.state.database.session_factory.begin() as session:
            result = router.complete(session, "tenant-a", CompletionRequest(prompt="retry"))
            assert result.model_id == "fallback"
            assert result.content == "fallback"


def test_budget_blocks_before_provider_can_be_called(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'budget.db'}",
        llm_primary_model_id="metered",
        llm_tenant_daily_budget_usd=0.000001,
    )
    registry = ModelRegistry((ModelSpec("metered", "fixed", "metered", 100, False, 1.0, 1.0),))
    router = ModelRouter(settings, registry, {"fixed": FixedProvider()})
    app = create_app(settings)
    with TestClient(app) as client:
        with client.app.state.database.session_factory.begin() as session:
            with pytest.raises(BudgetExceededError):
                router.complete(
                    session,
                    "tenant-a",
                    CompletionRequest(prompt="cost", max_output_tokens=10),
                )


def test_paid_model_is_skipped_when_paid_fallback_is_disabled(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'paid.db'}",
        llm_primary_model_id="paid",
        llm_fallback_model_ids="free",
        llm_allow_paid_fallback=False,
    )
    registry = ModelRegistry(
        (
            ModelSpec("paid", "paid", "paid", 100, False, paid=True),
            ModelSpec("free", "free", "free", 100, False),
        )
    )
    router = ModelRouter(
        settings,
        registry,
        {"paid": FixedProvider("paid"), "free": FixedProvider()},
    )
    app = create_app(settings)
    with TestClient(app) as client:
        with client.app.state.database.session_factory.begin() as session:
            result = router.complete(session, "tenant-a", CompletionRequest(prompt="safe"))
    assert result.model_id == "free"


def test_structured_response_must_include_required_fields(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'structured.db'}",
        llm_primary_model_id="fixed",
    )
    registry = ModelRegistry((ModelSpec("fixed", "fixed", "fixed", 100, True),))
    router = ModelRouter(settings, registry, {"fixed": FixedProvider("not json")})
    app = create_app(settings)
    with TestClient(app) as client:
        with client.app.state.database.session_factory.begin() as session:
            with pytest.raises(StructuredOutputError):
                router.complete(
                    session,
                    "tenant-a",
                    CompletionRequest(prompt="json", structured_schema={"required": ["answer"]}),
                )


def test_model_registry_is_available_to_an_authorized_user(tmp_path: Path) -> None:
    with TestClient(make_app(tmp_path)) as client:
        response = client.get("/api/v1/models", headers=token(client))
        assert response.status_code == 200
        assert any(item["id"] == "mock-chat" for item in response.json()["items"])


def test_openai_compatible_adapter_and_ollama_adapter_parse_provider_responses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = ModelRegistry(
        (
            ModelSpec("groq-test", "groq", "provider-model", 100, True),
            ModelSpec("ollama-test", "ollama", "local-model", 100, True),
        )
    )
    calls: list[dict[str, object]] = []

    def fake_post(*args: object, **kwargs: object) -> FakeHttpResponse:
        calls.append(kwargs)
        url = str(args[0])
        if url.endswith("/api/chat"):
            return FakeHttpResponse({"message": {"content": "local result"}})
        return FakeHttpResponse(
            {
                "choices": [{"message": {"content": "remote result"}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 2},
            }
        )

    monkeypatch.setattr("app.llm.providers.httpx.post", fake_post)
    remote = OpenAICompatibleProvider("groq", "https://example.test/v1", "key", registry, 1)
    local = OllamaProvider("http://localhost:11434", registry, 1)
    remote_result = remote.complete("groq-test", CompletionRequest(prompt="hello"))
    local_result = local.complete("ollama-test", CompletionRequest(prompt="hello"))
    assert remote_result.content == "remote result"
    assert local_result.content == "local result"
    assert len(calls) == 2


def test_unconfigured_provider_and_non_postgres_checkpointer_fail_safely() -> None:
    registry = ModelRegistry((ModelSpec("groq-test", "groq", "provider-model", 100, True),))
    provider = OpenAICompatibleProvider("groq", "https://example.test/v1", "", registry, 1)
    with pytest.raises(ProviderUnavailableError):
        provider.complete("groq-test", CompletionRequest(prompt="hello"))
    with pytest.raises(ValueError, match="PostgreSQL"):
        with postgres_checkpointer("sqlite:///local.db"):
            pass
