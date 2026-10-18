import json
from pathlib import Path
from time import sleep

import httpx
import pytest
from app.core.auth import Principal
from app.core.config import Settings
from app.main import create_app
from app.tools.contracts import ToolCall
from app.tools.mcp import RemoteMCPClient, RemoteMCPError
from app.tools.registry import ToolDefinition, ToolRegistry
from app.tools.service import ToolExecutionService
from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path / 'tools.db'}")))


def auth(client: TestClient, profile: str) -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def call(key: str, mode: str = "execute") -> dict[str, object]:
    return {
        "tool_id": "support.create_ticket",
        "idempotency_key": key,
        "mode": mode,
        "arguments": {"title": "Login issue", "description": "User cannot sign in."},
    }


def test_authorized_tool_draft_execute_and_idempotent_replay(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        listed = client.get("/api/v1/tools", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["items"][0]["name"] == "support.create_ticket"
        draft = client.post(
            "/api/v1/tools/execute", headers=headers, json=call("draft-123", "draft")
        )
        assert draft.json()["status"] == "draft"
        executed = client.post("/api/v1/tools/execute", headers=headers, json=call("exec-123"))
        assert executed.json()["status"] == "completed"
        assert executed.json()["verified"] is True
        replay = client.post("/api/v1/tools/execute", headers=headers, json=call("exec-123"))
        assert replay.json()["status"] == "replayed"
        assert replay.json()["result"]["ticket_id"] == executed.json()["result"]["ticket_id"]


def test_customer_cannot_invoke_internal_mutating_tool(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/v1/tools/execute", headers=auth(client, "customer"), json=call("customer-123")
        )
        assert response.status_code == 403
        assert client.get("/api/v1/tools", headers=auth(client, "customer")).json()["items"] == []


def test_tool_schema_and_provider_failures_are_explicit(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        headers = auth(client, "internal")
        invalid = client.post(
            "/api/v1/tools/execute",
            headers=headers,
            json={**call("invalid-123"), "arguments": {"title": "Missing description"}},
        )
        assert invalid.status_code == 422
        unknown = client.post(
            "/api/v1/tools/execute",
            headers=headers,
            json={
                "tool_id": "model.invented_tool",
                "idempotency_key": "unknown-123",
                "mode": "execute",
            },
        )
        assert unknown.status_code == 403


def test_tool_timeout_is_bounded(tmp_path: Path) -> None:
    class SlowAdapter:
        def draft(self, arguments):
            sleep(0.05)
            return arguments

        execute = draft

        def verify(self, result):
            return True

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "slow.read",
            "slow test tool",
            {"required": []},
            frozenset({"internal"}),
            frozenset({"internal_member"}),
            False,
            SlowAdapter(),
            max_retries=0,
        )
    )
    service = ToolExecutionService(registry)
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'timeout.db'}"))
    app.state.database.create_schema()
    with app.state.database.session_factory() as db:
        result = service.execute(
            db,
            Principal("u", "o", "internal_member", "internal"),
            ToolCall(tool_id="slow.read", idempotency_key="timeout-123", timeout_seconds=0.001),
        )
        assert result.status == "failed"
        assert result.error_code == "tool_timeout"


def test_remote_mcp_json_rpc_transport_validates_envelope_and_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        assert body["method"] == "tools/call"
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": "remote-123",
                "result": {"structuredContent": {"ticket_id": "T-1"}},
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as client:
        result = RemoteMCPClient("https://mcp.test", client=client).call(
            ToolCall(
                tool_id="support.create_ticket",
                arguments={"title": "Login", "description": "Blocked"},
                idempotency_key="remote-123",
            )
        )
    assert result.status == "completed"
    assert result.result == {"content": {"ticket_id": "T-1"}}
    assert result.verified is False


def test_remote_mcp_transport_fails_closed_when_unconfigured_or_malformed() -> None:
    call = ToolCall(tool_id="support.create_ticket", idempotency_key="remote-456")
    with pytest.raises(RemoteMCPError, match="not configured"):
        RemoteMCPClient().call(call)

    def malformed(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": "other"})

    with httpx.Client(transport=httpx.MockTransport(malformed)) as client:
        with pytest.raises(RemoteMCPError, match="invalid JSON-RPC envelope"):
            RemoteMCPClient("https://mcp.test", client=client).call(call)


def test_tool_results_are_redacted_and_idempotency_is_tenant_scoped(tmp_path: Path) -> None:
    class SensitiveAdapter:
        def draft(self, arguments):
            return {"ticket_id": "T-2", "api_token": "do-not-store"}

        execute = draft

        def verify(self, result):
            return True

    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "safe.test",
            "test tool",
            {"required": []},
            frozenset({"internal"}),
            frozenset({"internal_member"}),
            False,
            SensitiveAdapter(),
        )
    )
    service = ToolExecutionService(registry)
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'redaction.db'}"))
    app.state.database.create_schema()
    call_value = ToolCall(tool_id="safe.test", idempotency_key="tenant-key-123", mode="execute")
    with app.state.database.session_factory() as db:
        first = service.execute(
            db, Principal("u1", "org-1", "internal_member", "internal"), call_value
        )
        db.commit()
        assert first.result["api_token"] == "[REDACTED]"
        other_tenant = service.execute(
            db, Principal("u2", "org-2", "internal_member", "internal"), call_value
        )
        assert other_tenant.status == "completed"
