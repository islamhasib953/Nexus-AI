import asyncio
import json
from time import perf_counter
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.contracts import AgentExecutionError, AgentRequest
from app.agents.orchestrator import Orchestrator
from app.core.auth import DEV_PROFILES, Principal, issue_token, require_principal
from app.core.config import Settings
from app.llm.models import BudgetExceededError, ProviderUnavailableError
from app.llm.router import ModelRouter
from app.persistence.checkpoints import PostgresCheckpointStore
from app.persistence.database import Database
from app.persistence.models import AgentExecutionMetric, Conversation, Message, Run, RunEvent
from app.persistence.runs import transition_run

router = APIRouter(prefix="/api/v1", tags=["workspace"])
checkpoint_store = PostgresCheckpointStore()


class DevSessionRequest(BaseModel):
    profile: Literal["internal", "customer", "other"]


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=200)
    workspace: Literal["internal", "customer"] | None = None


class CreateRunRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


def get_db(request: Request):
    database: Database = request.app.state.database
    yield from database.sessions()


def get_model_router(request: Request) -> ModelRouter:
    return request.app.state.model_router


def require_owned_conversation(
    conversation_id: str, principal: Principal, db: Session
) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if (
        conversation is None
        or conversation.owner_id != principal.user_id
        or conversation.organization_id != principal.organization_id
    ):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


def require_owned_run(run_id: str, principal: Principal, db: Session) -> Run:
    run = db.get(Run, run_id)
    if (
        run is None
        or run.requester_id != principal.user_id
        or run.organization_id != principal.organization_id
    ):
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


def conversation_payload(conversation: Conversation) -> dict[str, object]:
    return {
        "id": conversation.id,
        "title": conversation.title,
        "workspace": conversation.workspace,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }


def run_payload(run: Run) -> dict[str, object]:
    return {
        "id": run.id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "attempt": run.attempt,
        "error_code": run.error_code,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
        "events_url": f"/api/v1/runs/{run.id}/events",
    }


def add_event(db: Session, run: Run, event_type: str, payload: dict[str, object]) -> RunEvent:
    latest = db.scalar(
        select(RunEvent.sequence)
        .where(RunEvent.run_id == run.id)
        .order_by(RunEvent.sequence.desc())
    )
    event = RunEvent(
        run_id=run.id,
        sequence=(latest or 0) + 1,
        event_type=event_type,
        payload=json.dumps(payload),
    )
    db.add(event)
    db.flush()
    return event


def encode_event(event: RunEvent) -> str:
    return f"id: {event.sequence}\nevent: {event.event_type}\ndata: {event.payload}\n\n"


@router.post("/auth/dev/session")
def create_development_session(body: DevSessionRequest, request: Request) -> dict[str, object]:
    settings: Settings = request.app.state.settings
    principal = DEV_PROFILES[body.profile]
    token = issue_token(principal, settings)
    return {"access_token": token, "token_type": "bearer", "principal": principal.__dict__}


@router.get("/me")
def current_user(principal: Principal = Depends(require_principal)) -> dict[str, object]:
    return {
        "user_id": principal.user_id,
        "organization_id": principal.organization_id,
        "role": principal.role,
        "workspace": principal.workspace,
    }


@router.get("/agents")
def list_agents(
    request: Request, principal: Principal = Depends(require_principal)
) -> dict[str, object]:
    orchestrator: Orchestrator = request.app.state.orchestrator
    return {
        "items": [
            {
                "id": capability.agent_id,
                "description": capability.description,
                "allowed_workspaces": sorted(capability.allowed_workspaces),
                "allowed_sources": sorted(capability.allowed_sources),
                "allowed_tools": sorted(capability.allowed_tools),
                "max_iterations": capability.max_iterations,
                "supported_tasks": list(capability.supported_tasks),
                "exclusions": list(capability.exclusions),
                "implementation_status": capability.implementation_status,
                "required_integrations": list(capability.required_integrations),
            }
            for capability in orchestrator.registry.all()
        ]
    }


@router.get("/models")
def list_models(
    principal: Principal = Depends(require_principal),
    model_router: ModelRouter = Depends(get_model_router),
) -> dict[str, object]:
    return {
        "items": [
            {
                "id": model.id,
                "provider": model.provider,
                "context_window": model.context_window,
                "supports_structured_output": model.supports_structured_output,
                "supports_streaming": model.supports_streaming,
                "supports_tools": model.supports_tools,
                "supports_multimodal": model.supports_multimodal,
                "requires_api_key": model.requires_api_key,
                "capabilities": list(model.capabilities),
            }
            for model in model_router.registry.all()
        ]
    }


@router.get("/conversations")
def list_conversations(
    principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    items = db.scalars(
        select(Conversation)
        .where(Conversation.owner_id == principal.user_id)
        .order_by(Conversation.updated_at.desc())
    ).all()
    return {"items": [conversation_payload(item) for item in items]}


@router.post("/conversations", status_code=201)
def create_conversation(
    body: CreateConversationRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    workspace = body.workspace or principal.workspace
    if workspace != principal.workspace:
        raise HTTPException(status_code=403, detail="Workspace is not authorized for this user.")
    conversation = Conversation(
        organization_id=principal.organization_id,
        owner_id=principal.user_id,
        workspace=workspace,
        title=body.title,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation_payload(conversation)


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    conversation = require_owned_conversation(conversation_id, principal, db)
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    ).all()
    return {
        **conversation_payload(conversation),
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ],
    }


@router.post("/conversations/{conversation_id}/runs", status_code=202)
def create_run(
    conversation_id: str,
    body: CreateRunRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    conversation = require_owned_conversation(conversation_id, principal, db)
    run = Run(
        conversation_id=conversation.id,
        organization_id=principal.organization_id,
        requester_id=principal.user_id,
    )
    db.add(run)
    db.flush()
    db.add(
        Message(conversation_id=conversation.id, run_id=run.id, role="user", content=body.content)
    )
    add_event(db, run, "run_started", {"status": "queued"})
    db.commit()
    db.refresh(run)
    return run_payload(run)


@router.get("/runs/{run_id}")
def get_run(
    run_id: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    return run_payload(require_owned_run(run_id, principal, db))


@router.post("/runs/{run_id}/cancel", status_code=202)
def cancel_run(
    run_id: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    run = require_owned_run(run_id, principal, db)
    if run.status in {"completed", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Run is already terminal.")
    transition_run(db, run, "cancelled")
    add_event(db, run, "run_cancelled", {"status": "cancelled"})
    db.commit()
    return run_payload(run)


@router.post("/runs/{run_id}/resume", status_code=202)
def resume_run(
    run_id: str, principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
) -> dict[str, object]:
    run = require_owned_run(run_id, principal, db)
    transition_run(db, run, "queued")
    add_event(db, run, "run_resumed", {"status": "queued", "attempt": run.attempt})
    db.commit()
    db.refresh(run)
    return run_payload(run)


@router.get("/runs/{run_id}/events")
async def stream_run(
    run_id: str,
    request: Request,
    last_event_id: int | None = Header(default=None, alias="Last-Event-ID"),
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    run = require_owned_run(run_id, principal, db)

    async def events():
        emitted = 0
        stored = db.scalars(
            select(RunEvent).where(RunEvent.run_id == run.id).order_by(RunEvent.sequence)
        ).all()
        for event in stored:
            emitted = event.sequence
            if last_event_id is None or event.sequence > last_event_id:
                yield encode_event(event)
        db.expire_all()
        current = db.get(Run, run.id)
        if current is None or current.status in {"completed", "failed", "cancelled"}:
            return
        if current.status != "queued":
            # A second consumer must not execute an already-running run again. The
            # worker/request that owns the run will append the remaining events.
            return
        transition_run(db, current, "running")
        status_event = add_event(db, current, "status_changed", {"status": "running"})
        db.commit()
        if last_event_id is None or status_event.sequence > last_event_id:
            yield encode_event(status_event)
        prompt = db.scalar(
            select(Message.content)
            .where(Message.run_id == run.id, Message.role == "user")
            .order_by(Message.created_at.desc())
        )
        orchestrator: Orchestrator = request.app.state.orchestrator
        agent_started = perf_counter()
        try:
            agent_response = orchestrator.execute(
                db,
                AgentRequest(
                    prompt=prompt or "",
                    organization_id=principal.organization_id,
                    user_id=principal.user_id,
                    workspace=principal.workspace,
                    conversation_id=run.conversation_id,
                    run_id=run.id,
                ),
            )
        except (BudgetExceededError, ProviderUnavailableError, AgentExecutionError) as error:
            current = db.get(Run, run.id)
            if current is not None and current.status == "running":
                error_code = getattr(getattr(error, "failure", None), "code", "model_unavailable")
                transition_run(db, current, "failed", error_code=error_code)
                db.add(
                    AgentExecutionMetric(
                        organization_id=current.organization_id,
                        run_id=current.id,
                        agent_id=getattr(getattr(error, "failure", None), "agent_id", "unknown"),
                        status="failed",
                        duration_ms=int((perf_counter() - agent_started) * 1000),
                    )
                )
                event = add_event(db, current, "run_failed", {"reason": str(error)})
                db.commit()
                if last_event_id is None or event.sequence > last_event_id:
                    yield encode_event(event)
            return
        for progress in agent_response.progress:
            progress_event = add_event(
                db,
                run,
                progress.event_type,
                {"agent_id": progress.agent_id, "message": progress.message},
            )
            db.commit()
            emitted = progress_event.sequence
            if last_event_id is None or progress_event.sequence > last_event_id:
                yield encode_event(progress_event)
        db.add(
            AgentExecutionMetric(
                organization_id=run.organization_id,
                run_id=run.id,
                agent_id=agent_response.agent_id,
                status=agent_response.status.value,
                duration_ms=int((perf_counter() - agent_started) * 1000),
                input_tokens=agent_response.input_tokens,
                output_tokens=agent_response.output_tokens,
            )
        )
        db.commit()
        chunks = [agent_response.content]
        for chunk in chunks:
            db.expire_all()
            current = db.get(Run, run.id)
            if current is None or current.status == "cancelled":
                break
            event = add_event(db, current, "message_delta", {"delta": chunk})
            checkpoint_store.save(
                db,
                run_id=current.id,
                organization_id=current.organization_id,
                thread_id=current.conversation_id,
                namespace=current.checkpoint_namespace,
                checkpoint_key="latest",
                state={"last_delta": chunk, "event_sequence": event.sequence},
            )
            db.commit()
            emitted = event.sequence
            if last_event_id is None or event.sequence > last_event_id:
                yield encode_event(event)
            await asyncio.sleep(0.08)
            if await request.is_disconnected():
                return
        db.expire_all()
        current = db.get(Run, run.id)
        if current is not None and current.status == "running":
            content = "".join(chunks)
            db.add(
                Message(
                    conversation_id=current.conversation_id,
                    run_id=current.id,
                    role="assistant",
                    content=content,
                )
            )
            transition_run(db, current, "completed")
            event = add_event(db, current, "run_completed", {"status": "completed"})
            db.commit()
            if last_event_id is None or event.sequence > last_event_id:
                yield encode_event(event)
        elif current is not None and current.status == "cancelled":
            events_after_cancel = db.scalars(
                select(RunEvent)
                .where(RunEvent.run_id == current.id, RunEvent.sequence > emitted)
                .order_by(RunEvent.sequence)
            ).all()
            for event in events_after_cancel:
                yield encode_event(event)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
