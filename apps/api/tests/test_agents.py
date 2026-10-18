from pathlib import Path

import pytest
from app.agents.contracts import AgentRequest
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.specialized import AnalyticsAgent
from app.core.config import Settings
from app.main import create_app
from app.persistence.models import RunEvent
from fastapi.testclient import TestClient
from sqlalchemy import select


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path / 'agents.db'}")))


def auth(client: TestClient, profile: str) -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_registry_exposes_capabilities_and_workspace_permissions(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/v1/agents", headers=auth(client, "internal"))
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()["items"]}
        assert {"orchestrator", "knowledge-research", "analytics", "general"} <= ids
        crm = next(item for item in response.json()["items"] if item["id"] == "crm")
        assert crm["implementation_status"] == "bounded"
        assert crm["required_integrations"] == ["crm"]
        registry = AgentRegistry()
        registry.authorize("analytics", "internal")
        try:
            registry.authorize("analytics", "customer")
        except PermissionError:
            pass
        else:
            raise AssertionError("customer workspace must not access analytics")


def test_analytics_request_is_delegated_and_emits_progress(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "calculate 6 * 7"},
        ).json()
        stream = client.get(run["events_url"], headers=headers)
        assert "Analytics result: 42" in stream.text
        assert "event: agent_started" in stream.text
        assert "event: agent_completed" in stream.text
        assert "event: run_completed" in stream.text


def test_customer_analytics_request_fails_instead_of_succeeding(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "customer")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "calculate 6 * 7"},
        ).json()
        stream = client.get(run["events_url"], headers=headers)
        assert "event: run_failed" in stream.text
        assert "event: run_completed" not in stream.text


def test_invalid_analytics_expression_is_a_failed_run(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "calculate the monthly trend"},
        ).json()
        stream = client.get(run["events_url"], headers=headers)
        assert "event: run_failed" in stream.text
        with client.app.state.database.session_factory() as session:
            events = session.scalars(select(RunEvent).where(RunEvent.run_id == run["id"])).all()
            assert any(event.event_type == "run_failed" for event in events)


def test_orchestrator_routes_representative_requests(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'orchestrator.db'}")
    app = create_app(settings)
    orchestrator: Orchestrator = app.state.orchestrator
    assert orchestrator.choose_agent("calculate 1 + 1") == "analytics"
    assert orchestrator.choose_agent("research the policy document") == "knowledge-research"
    assert orchestrator.choose_agent("hello there") == "general"
    request = AgentRequest(
        prompt="hello",
        organization_id="org",
        user_id="user",
        workspace="internal",
        conversation_id="conversation",
        run_id="run",
    )
    assert request.prompt == "hello"


def test_phase11_domain_portfolio_has_boundaries_and_deterministic_routing(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'portfolio.db'}")
    app = create_app(settings)
    orchestrator: Orchestrator = app.state.orchestrator
    assert orchestrator.choose_agent("design a data pipeline") == "data-engineering"
    assert orchestrator.choose_agent("help with CRM account") == "crm"
    assert orchestrator.choose_agent("support ticket for login issue") == "customer-support"
    assert orchestrator.choose_agent("customer onboarding plan") == "customer-success"
    assert orchestrator.choose_agent("finance budget policy") == "finance"
    assert orchestrator.choose_agent("how do I use this product feature") == "customer-product"
    assert orchestrator.registry.authorize(
        "customer-support", "customer"
    ).allowed_tools == frozenset({"support.create_ticket"})
    try:
        orchestrator.registry.authorize("finance", "customer")
    except PermissionError:
        pass
    else:
        raise AssertionError("finance must remain internal-only")


def test_customer_support_agent_is_failure_safe_without_evidence(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "customer")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "support login issue"},
        ).json()
        stream = client.get(run["events_url"], headers=headers)
        assert "customer-support" in stream.text
        assert "No authorized source" in stream.text
        assert "no approved external system integration" in stream.text


def test_analytics_rejects_multiple_or_unbounded_expressions() -> None:
    agent = AnalyticsAgent()
    request = AgentRequest(
        prompt="calculate 1 + 2 and 3 + 4",
        organization_id="org-internal",
        user_id="user-internal",
        workspace="internal",
        conversation_id="conversation",
        run_id="run",
    )
    with pytest.raises(ValueError, match="one bounded"):
        agent.execute(None, request, None)

    request.prompt = "calculate 1000000000001 + 1"
    with pytest.raises(ValueError, match="bounded calculation limit"):
        agent.execute(None, request, None)


def test_completed_run_replays_without_duplicate_execution_and_supports_sse_resume(
    tmp_path: Path,
) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "calculate 2 + 2"},
        ).json()
        first = client.get(run["events_url"], headers=headers)
        assert first.status_code == 200
        event_ids = [
            int(line.removeprefix("id: "))
            for line in first.text.splitlines()
            if line.startswith("id: ")
        ]
        assert event_ids
        replay = client.get(
            run["events_url"],
            headers={**headers, "Last-Event-ID": str(event_ids[-1] - 1)},
        )
        assert replay.status_code == 200
        assert "event: run_completed" in replay.text
        assert client.get(run["events_url"], headers=headers).status_code == 200
        assert client.get(f"/api/v1/runs/{run['id']}", headers=headers).json()["attempt"] == 1
