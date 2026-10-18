from pathlib import Path

from app.core.auth import Principal, issue_token
from app.core.config import Settings
from app.main import create_app
from app.persistence.models import ModelUsage, RoutingDecisionLog
from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path / 'operations.db'}")))


def auth(client: TestClient, profile: str) -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_operations_overview_records_agent_and_model_metrics(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "Hello"},
        ).json()
        assert client.get(run["events_url"], headers=headers).status_code == 200

        overview = client.get("/api/v1/operations/overview", headers=headers)
        assert overview.status_code == 200
        payload = overview.json()
        assert payload["summary"]["runs_total"] == 1
        assert payload["cost"]["by_provider"]["mock"] == "0.00000000"
        assert payload["agents"][0]["agent_id"] == "general"
        assert payload["organization_id"] == "dev-org"


def test_operations_metrics_are_internal_only_and_tenant_scoped(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        internal = auth(client, "internal")
        customer = auth(client, "customer")
        assert client.get("/api/v1/operations/overview", headers=customer).status_code == 403

        settings = client.app.state.settings
        other_tenant = issue_token(
            Principal("ops-user", "other-org", "internal_member", "internal"), settings
        )
        with client.app.state.database.session_factory.begin() as session:
            session.add(
                ModelUsage(
                    organization_id="other-org",
                    run_id="classified-run",
                    provider="secret-provider",
                    model_id="secret-model",
                    input_tokens=1,
                    output_tokens=1,
                    estimated_cost_usd="9.99",
                )
            )
            session.add(
                RoutingDecisionLog(
                    organization_id="other-org",
                    owner_id="ops-user",
                    run_id="classified-run",
                    route_kind="retrieval",
                    cache_status="miss_bypass",
                    context_mode="history",
                    latency_ms=4,
                )
            )
        own = client.get("/api/v1/operations/overview", headers=internal).json()
        other = client.get(
            "/api/v1/operations/overview",
            headers={"Authorization": f"Bearer {other_tenant}"},
        ).json()
        assert "secret-model" not in own["cost"]["by_model"]
        assert other["cost"]["by_model"]["secret-model"] == "9.99000000"
        assert other["cost"]["by_task"]["retrieval"] == "9.99000000"


def test_provider_circuit_and_queue_threshold_generate_alerts(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        client.app.state.model_router.health.failure("mock")
        response = client.get("/api/v1/operations/alerts", headers=headers)
        assert response.status_code == 200
        rule_ids = {item["rule_id"] for item in response.json()["items"]}
        assert "provider:mock" in rule_ids


def test_operations_can_be_disabled_by_environment(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'operations-disabled.db'}", observability_enabled=False
    )
    with TestClient(create_app(settings)) as client:
        assert (
            client.get("/api/v1/operations/overview", headers=auth(client, "internal")).status_code
            == 404
        )
