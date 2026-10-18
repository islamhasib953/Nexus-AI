from dataclasses import dataclass


@dataclass(frozen=True)
class AgentCapability:
    agent_id: str
    description: str
    allowed_workspaces: frozenset[str]
    allowed_sources: frozenset[str]
    allowed_tools: frozenset[str]
    max_iterations: int
    supported_tasks: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()


class AgentRegistry:
    def __init__(self, capabilities: tuple[AgentCapability, ...] | None = None) -> None:
        self._capabilities = {
            item.agent_id: item for item in capabilities or default_capabilities()
        }

    def get(self, agent_id: str) -> AgentCapability:
        return self._capabilities[agent_id]

    def all(self) -> tuple[AgentCapability, ...]:
        return tuple(self._capabilities.values())

    def authorize(self, agent_id: str, workspace: str) -> AgentCapability:
        capability = self.get(agent_id)
        if workspace not in capability.allowed_workspaces:
            raise PermissionError(f"Agent {agent_id} is not allowed in workspace {workspace}.")
        return capability


def default_capabilities() -> tuple[AgentCapability, ...]:
    return (
        AgentCapability(
            "orchestrator",
            "Routes a request to one specialized agent.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation"}),
            frozenset(),
            1,
            ("route requests",),
            ("execute business actions",),
        ),
        AgentCapability(
            "knowledge-research",
            "Answers research and document-oriented questions.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation", "approved_documents"}),
            frozenset(),
            2,
            ("research approved documents", "answer grounded questions"),
            ("invent unsupported company facts",),
        ),
        AgentCapability(
            "analytics",
            "Performs bounded calculations and analytical summaries.",
            frozenset({"internal"}),
            frozenset({"conversation", "approved_metrics"}),
            frozenset(),
            2,
            ("bounded arithmetic", "approved metric summaries"),
            ("write to business systems",),
        ),
        AgentCapability(
            "general",
            "Handles direct conversational requests.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation"}),
            frozenset(),
            1,
            ("general conversation",),
            ("access protected business data",),
        ),
        AgentCapability(
            "data-engineering",
            "Explains data quality, pipelines, schemas, and bounded transformation tasks.",
            frozenset({"internal"}),
            frozenset({"conversation", "approved_documents", "approved_metrics"}),
            frozenset(),
            2,
            ("data quality", "pipeline design", "schema reasoning"),
            ("mutate production data", "run unapproved queries"),
        ),
        AgentCapability(
            "crm",
            "Assists internal users with authorized CRM knowledge and workflow guidance.",
            frozenset({"internal"}),
            frozenset({"conversation", "approved_documents"}),
            frozenset({"support.create_ticket"}),
            2,
            ("CRM guidance", "account workflow explanation"),
            ("expose another tenant's customer data",),
        ),
        AgentCapability(
            "customer-support",
            "Provides customer-facing support grounded in authorized knowledge.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation", "approved_documents"}),
            frozenset({"support.create_ticket"}),
            2,
            ("support answers", "troubleshooting", "escalation guidance"),
            ("promise refunds", "bypass approval policy"),
        ),
        AgentCapability(
            "customer-success",
            "Provides onboarding and adoption guidance from authorized customer knowledge.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation", "approved_documents"}),
            frozenset(),
            2,
            ("onboarding", "adoption guidance", "success planning"),
            ("change account permissions",),
        ),
        AgentCapability(
            "finance",
            "Provides internal finance explanations from approved policies and metrics.",
            frozenset({"internal"}),
            frozenset({"conversation", "approved_documents", "approved_metrics"}),
            frozenset(),
            2,
            ("finance policy", "budget explanation", "approved metric summaries"),
            ("execute payments", "expose financial data externally"),
        ),
        AgentCapability(
            "customer-product",
            "Explains product capabilities and safe customer-facing usage.",
            frozenset({"internal", "customer"}),
            frozenset({"conversation", "approved_documents"}),
            frozenset(),
            2,
            ("product how-to", "feature explanation", "safe usage guidance"),
            ("change product configuration",),
        ),
    )
