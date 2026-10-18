import re
from time import perf_counter

from sqlalchemy.orm import Session

from app.agents.contracts import (
    AgentExecutionError,
    AgentFailure,
    AgentProgress,
    AgentRequest,
    AgentResponse,
)
from app.agents.registry import AgentRegistry
from app.agents.specialized import (
    AnalyticsAgent,
    CRMAgent,
    CustomerProductAgent,
    CustomerSuccessAgent,
    CustomerSupportAgent,
    DataEngineeringAgent,
    FinanceAgent,
    GeneralAgent,
    KnowledgeResearchAgent,
)
from app.core.config import Settings
from app.routing.smart_router import SmartRequestRouter


class Orchestrator:
    analytics_pattern = re.compile(
        r"\b(calculate|compute|sum|average|calculate|تحليل|احسب|متوسط)\b", re.I
    )
    knowledge_pattern = re.compile(
        r"\b(research|document|policy|knowledge|مستند|سياسة|بحث)\b", re.I
    )
    domain_patterns = {
        "data-engineering": re.compile(
            r"\b(data|pipeline|schema|etl|quality|بيانات|خط أنابيب)\b", re.I
        ),
        "crm": re.compile(r"\b(crm|account|customer record|عميل|حساب)\b", re.I),
        "customer-support": re.compile(r"\b(support|issue|troubleshoot|ticket|دعم|مشكلة)\b", re.I),
        "customer-success": re.compile(
            r"\b(onboard\w*|adoption|success|اعتماد|تفعيل|نجاح العميل)\b", re.I
        ),
        "finance": re.compile(r"\b(finance|budget|invoice|financial|ميزانية|فاتورة|مالي)\b", re.I),
        "customer-product": re.compile(r"\b(product|feature|how to use|منتج|ميزة|استخدم)\b", re.I),
    }

    def __init__(
        self, settings: Settings, smart_router: SmartRequestRouter, documents=None
    ) -> None:
        self.settings = settings
        self.registry = AgentRegistry()
        self.agents = {
            "knowledge-research": KnowledgeResearchAgent(smart_router, documents),
            "analytics": AnalyticsAgent(),
            "general": GeneralAgent(smart_router),
            "data-engineering": DataEngineeringAgent(smart_router, documents),
            "crm": CRMAgent(smart_router, documents),
            "customer-support": CustomerSupportAgent(smart_router, documents),
            "customer-success": CustomerSuccessAgent(smart_router, documents),
            "finance": FinanceAgent(smart_router, documents),
            "customer-product": CustomerProductAgent(smart_router, documents),
        }

    def choose_agent(self, prompt: str) -> str:
        if self.analytics_pattern.search(prompt):
            return "analytics"
        for agent_id, pattern in self.domain_patterns.items():
            if pattern.search(prompt):
                return agent_id
        if self.knowledge_pattern.search(prompt):
            return "knowledge-research"
        return "general"

    def execute(self, db: Session, request: AgentRequest) -> AgentResponse:
        started = perf_counter()
        agent_id = self.choose_agent(request.prompt)
        try:
            capability = self.registry.authorize(agent_id, request.workspace)
            if capability.max_iterations > self.settings.agent_max_iterations:
                raise AgentExecutionError(
                    AgentFailure(
                        agent_id=agent_id,
                        code="iteration_budget",
                        message="Agent iteration budget is too low.",
                    )
                )
            agent = self.agents[agent_id]
            response = agent.execute(db, request, capability)
            if response.iterations > self.settings.agent_max_iterations:
                raise AgentExecutionError(
                    AgentFailure(
                        agent_id=agent_id,
                        code="iteration_budget",
                        message="Agent exceeded the iteration budget.",
                    )
                )
            response.progress.insert(
                0,
                AgentProgress(
                    event_type="agent_started",
                    message=f"Delegated to {agent_id}.",
                    agent_id=agent_id,
                ),
            )
            response.progress.append(
                AgentProgress(
                    event_type="agent_completed",
                    message=f"{response.summary} ({int((perf_counter() - started) * 1000)}ms).",
                    agent_id=agent_id,
                )
            )
            return response
        except AgentExecutionError:
            raise
        except Exception as error:
            raise AgentExecutionError(
                AgentFailure(
                    agent_id=agent_id,
                    code="agent_failed",
                    message=str(error),
                    retryable=False,
                )
            ) from error
