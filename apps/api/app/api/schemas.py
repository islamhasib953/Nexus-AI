from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str
    retryable: bool = False
    details: list[Any] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
