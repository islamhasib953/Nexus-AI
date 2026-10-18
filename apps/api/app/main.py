import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.agents.orchestrator import Orchestrator
from app.api.routes.approvals import router as approvals_router
from app.api.routes.contract import router as contract_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.operations import router as operations_router
from app.api.routes.tools import router as tools_router
from app.api.routes.workspace import router as workspace_router
from app.api.schemas import ErrorDetail, ErrorEnvelope
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.middleware import (
    CorrelationIdMiddleware,
    attach_request_state,
    request_id_from_request,
)
from app.llm.router import ModelRouter
from app.persistence.database import Database
from app.rag.service import DocumentService
from app.rag.vector_store import QdrantVectorStore
from app.routing.smart_router import SmartRequestRouter
from app.tools.defaults import build_tool_registry
from app.tools.service import ToolExecutionService


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[object] | None = None,
    retryable: bool = False,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(
            code=code,
            message=message,
            request_id=request_id_from_request(request),
            retryable=retryable,
            details=details or [],
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = application.state.settings
    configure_logging(settings.log_level)
    application.state.database.create_schema()
    recovered = application.state.database.recover_interrupted_runs()
    if recovered:
        logging.getLogger("nexus_ai").warning("runs_recovered", extra={"count": recovered})
    logging.getLogger("nexus_ai").info("application_started")
    try:
        yield
    finally:
        application.state.database.engine.dispose()
        logging.getLogger("nexus_ai").info("application_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    application = FastAPI(title="Nexus-AI API", version=settings.app_version, lifespan=lifespan)
    application.state.settings = settings
    application.state.database = Database(settings.database_url)
    application.state.model_router = ModelRouter(settings)
    application.state.smart_router = SmartRequestRouter(settings, application.state.model_router)
    application.state.documents = DocumentService(
        QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection)
    )
    application.state.orchestrator = Orchestrator(
        settings, application.state.smart_router, application.state.documents
    )
    application.state.tools = ToolExecutionService(build_tool_registry())
    application.add_middleware(CorrelationIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.web_origin).rstrip("/")],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID", "X-Request-ID"],
    )
    application.middleware("http")(attach_request_state)
    application.include_router(health_router)
    application.include_router(contract_router)
    application.include_router(workspace_router)
    application.include_router(knowledge_router)
    application.include_router(tools_router)
    application.include_router(approvals_router)
    application.include_router(operations_router)

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return _error_response(request, exc.status_code, code, str(exc.detail))

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request, 422, "validation_failed", "Request validation failed.", exc.errors()
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
        logging.getLogger("nexus_ai").exception("unhandled_exception")
        return _error_response(
            request, 500, "internal_error", "An unexpected error occurred.", retryable=True
        )

    return application


app = create_app()
