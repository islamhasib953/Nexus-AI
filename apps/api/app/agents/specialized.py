import re

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.contracts import AgentProgress, AgentRequest, AgentResponse
from app.agents.registry import AgentCapability
from app.routing.smart_router import SmartRequestRouter


class KnowledgeResearchAgent(BaseAgent):
    agent_id = "knowledge-research"

    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        self.router = router
        self.documents = documents

    def execute(
        self, db: Session, request: AgentRequest, capability: AgentCapability
    ) -> AgentResponse:
        citations = ()
        evidence_context = ""
        if self.documents is not None:
            retrieval = self.documents.search(
                db,
                organization_id=request.organization_id,
                user_id=request.user_id,
                workspace=request.workspace,
                query=request.prompt,
            )
            citations = retrieval.evidence
            if retrieval.supported:
                evidence_context = f"\nAuthorized evidence:\n{retrieval.prompt_context()}"
        result, _, _, _ = self.router.complete(
            db,
            organization_id=request.organization_id,
            owner_id=request.user_id,
            workspace=request.workspace,
            conversation_id=request.conversation_id,
            run_id=request.run_id,
            prompt=request.prompt + evidence_context,
        )
        if citations:
            source_lines = "\n".join(
                f"- [{index}] {citation.title} "
                f"(document {citation.document_id}, chunk {citation.chunk_index})"
                for index, citation in enumerate(citations, 1)
            )
            content = f"{result.content}\n\nSources:\n{source_lines}"
        else:
            content = (
                f"{result.content}\n\nNo authorized source supports a company-specific answer."
            )
        return AgentResponse(
            agent_id=self.agent_id,
            content=content,
            summary="Knowledge research response prepared with authorized citations."
            if citations
            else "Knowledge research found insufficient authorized evidence.",
            iterations=1,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            progress=[
                AgentProgress(
                    event_type="agent_progress",
                    message="Research response prepared.",
                    agent_id=self.agent_id,
                )
            ],
        )


class GeneralAgent(KnowledgeResearchAgent):
    agent_id = "general"


class AnalyticsAgent(BaseAgent):
    agent_id = "analytics"
    expression = re.compile(r"(?P<a>-?\d+(?:\.\d+)?)\s*(?P<op>[+\-*/])\s*(?P<b>-?\d+(?:\.\d+)?)")

    def execute(
        self, db: Session, request: AgentRequest, capability: AgentCapability
    ) -> AgentResponse:
        match = self.expression.search(request.prompt)
        if not match:
            raise ValueError("Analytics request must contain one bounded arithmetic expression.")
        left = float(match.group("a"))
        right = float(match.group("b"))
        operation = match.group("op")
        if operation == "+":
            answer = left + right
        elif operation == "-":
            answer = left - right
        elif operation == "*":
            answer = left * right
        elif right != 0:
            answer = left / right
        else:
            raise ValueError("Division by zero is not allowed.")
        rendered = str(int(answer)) if answer.is_integer() else str(answer)
        return AgentResponse(
            agent_id=self.agent_id,
            content=f"Analytics result: {rendered}",
            summary="Bounded arithmetic calculation completed.",
            iterations=1,
            input_tokens=0,
            output_tokens=0,
            progress=[
                AgentProgress(
                    event_type="agent_progress",
                    message="Calculation validated.",
                    agent_id=self.agent_id,
                )
            ],
        )


class DomainAgent(KnowledgeResearchAgent):
    """Shared bounded implementation for domain agents until real integrations are approved."""

    def __init__(self, agent_id: str, router: SmartRequestRouter, documents=None) -> None:
        super().__init__(router, documents)
        self.agent_id = agent_id

    def execute(
        self, db: Session, request: AgentRequest, capability: AgentCapability
    ) -> AgentResponse:
        response = super().execute(db, request, capability)
        response.agent_id = self.agent_id
        response.summary = f"{self.agent_id} completed a bounded knowledge workflow."
        for progress in response.progress:
            progress.agent_id = self.agent_id
        return response


class DataEngineeringAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("data-engineering", router, documents)


class CRMAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("crm", router, documents)


class CustomerSupportAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("customer-support", router, documents)


class CustomerSuccessAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("customer-success", router, documents)


class FinanceAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("finance", router, documents)


class CustomerProductAgent(DomainAgent):
    def __init__(self, router: SmartRequestRouter, documents=None) -> None:
        super().__init__("customer-product", router, documents)
