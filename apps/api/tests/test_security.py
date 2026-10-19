from pathlib import Path
from time import time

import httpx
import jwt
import pytest
from app.core.auth import AuthenticationError, OIDCAuthenticator
from app.core.config import Settings
from app.main import create_app
from app.security.policy import PolicyEngine, RiskCategory
from cryptography.hazmat.primitives.asymmetric import rsa
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


def test_oidc_authenticator_validates_jwks_claims_and_unknown_keys() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key())
    jwk = {**__import__("json").loads(public_jwk), "kid": "key-1", "use": "sig", "alg": "RS256"}

    def jwks(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"keys": [jwk]})

    claims = {
        "sub": "user-1",
        "org": "org-1",
        "role": "internal_member",
        "workspace": "internal",
        "iss": "https://issuer.test",
        "aud": "nexus",
        "iat": int(time()),
        "exp": int(time()) + 300,
    }
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "key-1"})
    with httpx.Client(transport=httpx.MockTransport(jwks)) as client:
        authenticator = OIDCAuthenticator(
            "https://issuer.test",
            "nexus",
            "https://issuer.test/.well-known/jwks.json",
            client=client,
        )
        principal = authenticator.verify(token)
        assert principal.organization_id == "org-1"
        assert principal.workspace == "internal"

        wrong_audience = jwt.encode(
            {**claims, "aud": "other"}, private_key, algorithm="RS256", headers={"kid": "key-1"}
        )
        with pytest.raises(AuthenticationError, match="Invalid identity token"):
            authenticator.verify(wrong_audience)

        unknown_key = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "unknown"})
        with pytest.raises(AuthenticationError, match="unknown"):
            authenticator.verify(unknown_key)

        # Missing tenant claim
        missing_org = jwt.encode(
            {k: v for k, v in claims.items() if k != "org"},
            private_key,
            algorithm="RS256",
            headers={"kid": "key-1"},
        )
        with pytest.raises(AuthenticationError, match="missing required tenant claims"):
            authenticator.verify(missing_org)


def test_missing_and_tampered_bearer_token_denied(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        # Missing token
        no_auth = client.get("/api/v1/me")
        assert no_auth.status_code == 401
        assert "Authentication is required" in no_auth.json()["error"]["message"]

        # Tampered / invalid token
        bad_token = client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-valid-token"})
        assert bad_token.status_code == 401
        assert "Invalid or expired" in bad_token.json()["error"]["message"]


def test_tenant_isolation_cross_tenant_access_denied(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        from app.core.auth import Principal, issue_token

        settings = client.app.state.settings
        token_tenant_a = issue_token(
            Principal("user-a", "org-alpha", "internal_member", "internal"), settings
        )
        token_tenant_b = issue_token(
            Principal("user-b", "org-beta", "internal_member", "internal"), settings
        )
        headers_a = {"Authorization": f"Bearer {token_tenant_a}"}
        headers_b = {"Authorization": f"Bearer {token_tenant_b}"}

        # Tenant A creates a conversation
        conv_a = client.post(
            "/api/v1/conversations", headers=headers_a, json={"title": "Secret Org A"}
        ).json()
        conv_id = conv_a["id"]

        # Tenant B attempts to read Tenant A's conversation -> 404 (Not Found in tenant scope)
        read_attempt = client.get(f"/api/v1/conversations/{conv_id}", headers=headers_b)
        assert read_attempt.status_code == 404

        # Tenant A ingests a knowledge document
        doc_a = client.post(
            "/api/v1/knowledge/documents",
            headers=headers_a,
            json={"title": "Alpha Confidential", "content": "Restricted knowledge"},
        ).json()
        doc_id = doc_a["id"]

        # Tenant B attempts to delete Tenant A's document -> 404
        delete_attempt = client.delete(f"/api/v1/knowledge/documents/{doc_id}", headers=headers_b)
        assert delete_attempt.status_code == 404

        # Tenant B searches knowledge -> must NOT see Tenant A's document
        search_b = client.post(
            "/api/v1/knowledge/search",
            headers=headers_b,
            json={"query": "Confidential", "limit": 5},
        ).json()
        assert len(search_b["citations"]) == 0


def test_operations_dashboard_denied_to_non_internal(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        customer_headers = auth(client, "customer")
        internal_headers = auth(client, "internal")

        # Customer role/workspace is forbidden from operations dashboard
        forbidden = client.get("/api/v1/operations/overview", headers=customer_headers)
        assert forbidden.status_code == 403

        # Internal member has access
        allowed = client.get("/api/v1/operations/overview", headers=internal_headers)
        assert allowed.status_code == 200


def test_policy_engine_denies_admin_tool_to_unauthorized_role() -> None:
    policy = PolicyEngine()
    # external_customer role denied from admin.*
    decision = policy.evaluate(
        tool_id="admin.shutdown_cluster",
        role="external_customer",
        workspace="internal",
        mode="execute",
    )
    assert decision.allowed is False
    assert decision.reason == "insufficient_role"

    # internal_member allowed (requires approval)
    internal_decision = policy.evaluate(
        tool_id="admin.shutdown_cluster",
        role="internal_member",
        workspace="internal",
        mode="execute",
    )
    assert internal_decision.allowed is True
    assert internal_decision.requires_approval is True


def test_audit_records_tool_and_document_events(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        from app.persistence.models import AuditLog
        from sqlalchemy import select

        internal = auth(client, "internal")

        # Ingest document
        client.post(
            "/api/v1/knowledge/documents",
            headers=internal,
            json={"title": "Audit Test Doc", "content": "Audited text"},
        )

        # Execute tool
        res = client.post(
            "/api/v1/tools/execute",
            headers=internal,
            json={
                "tool_id": "support.create_ticket",
                "arguments": {"title": "Need help", "description": "Details here"},
                "idempotency_key": "audit-test-key-001",
                "mode": "draft",
            },
        )
        assert res.status_code == 200

        with client.app.state.database.session_factory() as session:
            logs = session.scalars(select(AuditLog)).all()
            actions = {log.action for log in logs}
            assert "document.ingest" in actions
            assert "tool.execute" in actions
