from enum import StrEnum

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class AgentRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=10000)
    organization_id: str
    user_id: str
    workspace: str
    conversation_id: str
    run_id: str


class AgentProgress(BaseModel):
    event_type: str
    message: str
    agent_id: str


class AgentResponse(BaseModel):
    agent_id: str
    content: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    status: AgentStatus = AgentStatus.completed
    iterations: int = Field(ge=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    progress: list[AgentProgress] = Field(default_factory=list)


class AgentFailure(BaseModel):
    agent_id: str
    code: str
    message: str
    retryable: bool = False


class AgentExecutionError(Exception):
    def __init__(self, failure: AgentFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure
