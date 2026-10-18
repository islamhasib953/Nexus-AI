from pathlib import Path

from app.core.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'workspace.db'}")
    return TestClient(create_app(settings))


def token(client: TestClient, profile: str) -> str:
    response = client.post("/api/v1/auth/dev/session", json={"profile": profile})
    assert response.status_code == 200
    return response.json()["access_token"]


def headers(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def test_authorized_user_can_create_stream_and_retrieve_conversation(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        owner = headers(token(client, "internal"))
        created = client.post("/api/v1/conversations", json={"title": "Phase 3"}, headers=owner)
        assert created.status_code == 201
        conversation_id = created.json()["id"]

        run = client.post(
            f"/api/v1/conversations/{conversation_id}/runs",
            json={"content": "Hello"},
            headers=owner,
        )
        assert run.status_code == 202
        stream = client.get(run.json()["events_url"], headers=owner)
        assert stream.status_code == 200
        assert "event: message_delta" in stream.text
        assert "event: run_completed" in stream.text

        detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=owner)
        assert detail.status_code == 200
        assert [message["role"] for message in detail.json()["messages"]] == ["user", "assistant"]


def test_other_user_cannot_access_conversation_or_run(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        owner = headers(token(client, "internal"))
        other = headers(token(client, "other"))
        conversation = client.post(
            "/api/v1/conversations", json={"title": "Private"}, headers=owner
        ).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            json={"content": "Secret"},
            headers=owner,
        ).json()
        assert (
            client.get(f"/api/v1/conversations/{conversation['id']}", headers=other).status_code
            == 404
        )
        assert client.get(f"/api/v1/runs/{run['id']}", headers=other).status_code == 404


def test_customer_cannot_create_internal_workspace(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        customer = headers(token(client, "customer"))
        response = client.post(
            "/api/v1/conversations",
            json={"title": "Customer", "workspace": "internal"},
            headers=customer,
        )
        assert response.status_code == 403
