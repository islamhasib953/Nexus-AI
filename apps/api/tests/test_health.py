from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_liveness_returns_service_metadata() -> None:
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "nexus-ai-api"


def test_readiness_is_explicit_about_unconfigured_dependencies() -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["external_dependencies"] == "not_configured"


def test_correlation_id_is_returned_and_safe() -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "phase2-test-01"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "phase2-test-01"


def test_invalid_correlation_id_is_replaced() -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "bad value with spaces"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad value with spaces"


def test_unknown_route_uses_standard_error_envelope() -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_unhandled_error_uses_retryable_error_envelope() -> None:
    from app.main import create_app

    test_app = create_app()

    @test_app.get("/test-boom")
    async def boom() -> None:
        raise RuntimeError("test failure")

    response = TestClient(test_app, raise_server_exceptions=False).get("/test-boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["retryable"] is True


def test_settings_validates_unsupported_model_provider() -> None:
    import pytest
    from app.core.config import Settings

    with pytest.raises(ValueError, match="Unsupported model provider"):
        Settings(model_provider="unsupported_vendor")


def test_settings_requires_groq_api_key_when_groq_selected() -> None:
    import pytest
    from app.core.config import Settings

    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        Settings(model_provider="groq", groq_api_key="")


def test_settings_accepts_valid_groq_configuration() -> None:
    from app.core.config import Settings
    from app.llm.registry import ModelRegistry

    settings = Settings(
        model_provider="groq",
        groq_api_key="gsk_valid_mock_key",
        llm_primary_model_id="groq-gpt-oss-20b",
    )
    assert settings.model_provider == "groq"
    assert settings.groq_api_key == "gsk_valid_mock_key"

    registry = ModelRegistry()
    oss20b = registry.get("groq-gpt-oss-20b")
    assert oss20b.provider == "groq"
    assert oss20b.provider_model == "openai/gpt-oss-20b"

    oss120b = registry.get("groq-gpt-oss-120b")
    assert oss120b.provider == "groq"
    assert oss120b.provider_model == "openai/gpt-oss-120b"
