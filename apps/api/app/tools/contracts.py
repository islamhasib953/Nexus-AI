from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_id: str = Field(min_length=1, max_length=120)
    arguments: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=8, max_length=160)
    mode: Literal["draft", "execute"] = "draft"
    timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    approval_id: str | None = Field(default=None, max_length=36)


class ToolResult(BaseModel):
    tool_id: str
    status: Literal["draft", "pending_approval", "completed", "failed", "replayed"]
    result: dict[str, Any] = Field(default_factory=dict)
    provider_reference: str | None = None
    approval_id: str | None = None
    error_code: str | None = None
    verified: bool = False


class A2ATask(BaseModel):
    task_id: str
    source_agent: str
    target_agent: str
    intent: str
    input: dict[str, Any] = Field(default_factory=dict)
    max_hops: int = Field(default=1, ge=0, le=3)
