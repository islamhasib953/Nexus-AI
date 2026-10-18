from pathlib import Path

from app.agents.orchestrator import Orchestrator
from app.core.config import Settings
from app.main import create_app


def test_release_agent_routing_cases(tmp_path: Path) -> None:
    orchestrator: Orchestrator = create_app(
        Settings(database_url=f"sqlite:///{tmp_path / 'quality.db'}")
    ).state.orchestrator
    cases = {
        "calculate 2 + 2": "analytics",
        "design a data pipeline": "data-engineering",
        "help with CRM account": "crm",
        "support login issue": "customer-support",
        "customer onboarding": "customer-success",
        "finance budget": "finance",
        "product feature guide": "customer-product",
        "research the policy document": "knowledge-research",
    }
    assert {prompt: orchestrator.choose_agent(prompt) for prompt in cases} == cases


def test_release_agent_capabilities_are_explicit(tmp_path: Path) -> None:
    registry = create_app(
        Settings(database_url=f"sqlite:///{tmp_path / 'caps.db'}")
    ).state.orchestrator.registry
    for capability in registry.all():
        assert capability.supported_tasks
        assert capability.exclusions
