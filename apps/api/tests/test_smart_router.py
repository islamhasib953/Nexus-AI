from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.config import Settings
from app.main import create_app
from app.persistence.models import ResponseCache, RoutingDecisionLog
from app.routing.cache import ExactResponseCache
from app.routing.classifier import RequestClassifier
from app.routing.context import ContextSelectionService
from fastapi.testclient import TestClient
from sqlalchemy import select


def auth(client: TestClient, profile: str = "internal") -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_classifier_routes_simple_current_retrieval_and_action_requests() -> None:
    classifier = RequestClassifier()
    assert classifier.classify("What is 2 + 2?").kind == "direct_model"
    assert classifier.classify("What is the latest status today?").cacheable is False
    assert classifier.classify("Find the internal policy document").kind == "retrieval"
    assert classifier.classify("Send an email to the client").requires_tools is True


def test_exact_cache_key_is_owner_and_tenant_aware(tmp_path: Path) -> None:
    cache = ExactResponseCache()
    first = cache.make_key(
        organization_id="org-a",
        owner_id="user-a",
        workspace="internal",
        model_id="mock-chat",
        route_kind="direct_model",
        prompt="same",
    )
    other_user = cache.make_key(
        organization_id="org-a",
        owner_id="user-b",
        workspace="internal",
        model_id="mock-chat",
        route_kind="direct_model",
        prompt="same",
    )
    other_org = cache.make_key(
        organization_id="org-b",
        owner_id="user-a",
        workspace="internal",
        model_id="mock-chat",
        route_kind="direct_model",
        prompt="same",
    )
    assert len({first, other_user, other_org}) == 3


def test_expired_cache_entries_are_bypassed_and_removed(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'cache.db'}")
    app = create_app(settings)
    with TestClient(app) as client:
        db = client.app.state.database
        with db.session_factory.begin() as session:
            entry = ResponseCache(
                organization_id="org-a",
                owner_id="user-a",
                workspace="internal",
                cache_key="expired",
                content="stale",
                model_id="mock-chat",
                route_kind="direct_model",
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
            session.add(entry)
            session.flush()
            assert app.state.smart_router.cache.get(session, "expired") is None
            assert (
                session.scalar(select(ResponseCache).where(ResponseCache.cache_key == "expired"))
                is None
            )


def test_current_data_bypasses_cache_and_logs_routing_decision(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'router.db'}")
    with TestClient(create_app(settings)) as client:
        headers = auth(client)
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "What is the latest status today?"},
        ).json()
        response = client.get(run["events_url"], headers=headers)
        assert response.status_code == 200
        with client.app.state.database.session_factory() as session:
            log = session.scalar(
                select(RoutingDecisionLog).where(RoutingDecisionLog.run_id == run["id"])
            )
            assert log is not None
            assert log.route_kind == "current_data"
            assert log.cache_status == "miss_bypass"


def test_repeated_simple_request_hits_exact_cache(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'hit.db'}")
    with TestClient(create_app(settings)) as client:
        headers = auth(client)
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        content = {"content": "Explain caching simply"}
        first = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs", headers=headers, json=content
        ).json()
        assert client.get(first["events_url"], headers=headers).status_code == 200
        second = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs", headers=headers, json=content
        ).json()
        second_stream = client.get(second["events_url"], headers=headers)
        assert second_stream.status_code == 200
        with client.app.state.database.session_factory() as session:
            logs = session.scalars(
                select(RoutingDecisionLog).where(RoutingDecisionLog.organization_id == "dev-org")
            ).all()
            assert {log.cache_status for log in logs} >= {"miss", "hit"}


def test_long_context_is_summarized_within_bound(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'context.db'}")
    service = ContextSelectionService(max_chars=1000)
    app = create_app(settings)
    with TestClient(app) as client:
        headers = auth(client)
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        for index in range(12):
            client.post(
                f"/api/v1/conversations/{conversation['id']}/runs",
                headers=headers,
                json={"content": f"message {index} " + "x" * 200},
            )
        with client.app.state.database.session_factory() as session:
            selected = service.select(session, conversation["id"], "final", True)
        assert selected.mode == "summarized"
        assert len(selected.prompt) <= 1040
