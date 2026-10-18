from pathlib import Path

from app.core.config import Settings
from app.main import create_app
from app.persistence.models import Run
from fastapi.testclient import TestClient
from sqlalchemy import select


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path / 'phase4.db'}")))


def auth(client: TestClient, profile: str = "internal") -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_checkpoint_and_run_metadata_survive_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "restart.db"
    settings = Settings(database_url=f"sqlite:///{database_path}")
    first = create_app(settings)
    with TestClient(first) as client:
        headers = auth(client)
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "durable"},
        ).json()
        events = client.get(run["events_url"], headers=headers)
        assert events.status_code == 200

    second = create_app(settings)
    with TestClient(second) as client:
        headers = auth(client)
        detail = client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["messages"][-1]["role"] == "assistant"
        stored = client.app.state.database.session_factory()
        try:
            persisted = stored.scalar(select(Run).where(Run.id == run["id"]))
            assert persisted is not None
            assert persisted.status == "completed"
            assert persisted.attempt == 1
        finally:
            stored.close()


def test_running_run_is_marked_interrupted_and_can_resume(tmp_path: Path) -> None:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'recovery.db'}")
    app = create_app(settings)
    with TestClient(app) as client:
        headers = auth(client)
        conversation = client.post("/api/v1/conversations", headers=headers, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=headers,
            json={"content": "recover"},
        ).json()
        database = client.app.state.database
        with database.session_factory.begin() as session:
            item = session.get(Run, run["id"])
            item.status = "running"

    recovered_app = create_app(settings)
    with TestClient(recovered_app) as client:
        headers = auth(client)
        recovered = client.get(f"/api/v1/runs/{run['id']}", headers=headers).json()
        assert recovered["status"] == "interrupted"
        resumed = client.post(f"/api/v1/runs/{run['id']}/resume", headers=headers)
        assert resumed.status_code == 202
        assert resumed.json()["status"] == "queued"


def test_recovery_respects_tenant_and_owner_boundary(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        owner = auth(client)
        other = auth(client, "other")
        conversation = client.post("/api/v1/conversations", headers=owner, json={}).json()
        run = client.post(
            f"/api/v1/conversations/{conversation['id']}/runs",
            headers=owner,
            json={"content": "private"},
        ).json()
        assert client.post(f"/api/v1/runs/{run['id']}/resume", headers=other).status_code == 404
