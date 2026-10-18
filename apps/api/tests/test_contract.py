from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_contract_summary_matches_phase_2_boundary() -> None:
    response = client.get("/api/v1/contract")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["phase"] == 2
    assert body["streaming"] == "SSE"
    assert body["model_provider"] == "mock"


def test_openapi_contains_foundation_routes() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/health/live" in paths
    assert "/api/v1/health/ready" in paths
    assert "/api/v1/contract" in paths
