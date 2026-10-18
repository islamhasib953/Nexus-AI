from pathlib import Path

import pytest
from app.core.config import Settings
from app.main import create_app
from app.security.policy import PolicyEngine, RiskCategory
from fastapi.testclient import TestClient


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(Settings(database_url=f"sqlite:///{tmp_path / 'security.db'}")))


def auth(client: TestClient, profile: str) -> dict[str, str]:
    token = client.post("/api/v1/auth/dev/session", json={"profile": profile}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_high_risk_policy_requires_approval_and_prevents_material_change() -> None:
    policy = PolicyEngine()
    decision = policy.evaluate(
        tool_id="admin.delete_customer",
        role="internal_member",
        workspace="internal",
        mode="execute",
    )
    assert decision.risk == RiskCategory.critical
    assert decision.requires_approval is True
    assert (
        policy.approval_is_valid(
            "approved",
            __import__("datetime").datetime.now(__import__("datetime").UTC),
            __import__("datetime").datetime.now(__import__("datetime").UTC),
        )
        is False
    )


def test_approval_requires_internal_approver_and_is_audited(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        customer = auth(client, "customer")
        internal = auth(client, "internal")
        request = client.post(
            "/api/v1/approvals",
            headers=customer,
            json={"action_type": "admin.delete_customer", "payload": {"customer_id": "c-1"}},
        )
        assert request.status_code == 201
        approval_id = request.json()["id"]
        denied = client.post(f"/api/v1/approvals/{approval_id}/approve", headers=customer)
        assert denied.status_code == 403
        approved = client.post(f"/api/v1/approvals/{approval_id}/approve", headers=internal)
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        listed = client.get("/api/v1/approvals", headers=internal).json()["items"]
        assert listed[0]["status"] == "approved"


def test_customer_action_is_denied_and_approval_can_be_cancelled(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        customer = auth(client, "customer")
        denied = client.post(
            "/api/v1/approvals",
            headers=customer,
            json={"action_type": "support.create_ticket", "payload": {"title": "x"}},
        )
        assert denied.status_code == 201
        approval_id = denied.json()["id"]
        cancelled = client.post(f"/api/v1/approvals/{approval_id}/cancel", headers=customer)
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"


def test_development_auth_is_not_available_outside_development(tmp_path: Path) -> None:
    settings = Settings(
        app_env="staging",
        dev_auth_enabled=False,
        database_url=f"sqlite:///{tmp_path / 'staging.db'}",
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/me", headers={"Authorization": "Bearer anything"})
        assert response.status_code == 503


def test_production_settings_require_identity_provider_and_real_embeddings() -> None:
    with pytest.raises(ValueError, match="identity provider"):
        Settings(app_env="production", dev_auth_enabled=False, embedding_provider="openai")
