from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.agents.contracts import AgentRequest, AgentResponse
from app.agents.registry import AgentCapability


class BaseAgent(ABC):
    agent_id: str

    @abstractmethod
    def execute(
        self, db: Session, request: AgentRequest, capability: AgentCapability
    ) -> AgentResponse:
        raise NotImplementedError
