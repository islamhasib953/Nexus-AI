from datetime import UTC, datetime, timedelta
from typing import Final

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import Run, RunEvent

RUN_TRANSITIONS: Final[dict[str, frozenset[str]]] = {
    "queued": frozenset({"running", "cancelled"}),
    "running": frozenset({"completed", "failed", "cancelled", "interrupted"}),
    "interrupted": frozenset({"queued", "cancelled", "failed"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}
TERMINAL_STATUSES: Final[frozenset[str]] = frozenset({"completed", "failed", "cancelled"})


def transition_run(
    session: Session, run: Run, status: str, *, error_code: str | None = None
) -> Run:
    if status not in RUN_TRANSITIONS.get(run.status, frozenset()):
        raise HTTPException(
            status_code=409,
            detail=f"Invalid run transition: {run.status} -> {status}.",
        )
    now = datetime.now(UTC)
    run.status = status
    run.updated_at = now
    if status == "running":
        run.attempt += 1
        run.started_at = run.started_at or now
        run.lease_until = now + timedelta(minutes=5)
    if status in TERMINAL_STATUSES:
        run.completed_at = now
        run.lease_until = None
    run.error_code = error_code
    return run


def append_run_event(
    session: Session, run: Run, event_type: str, payload: dict[str, object]
) -> RunEvent:
    latest = session.scalar(
        select(RunEvent.sequence)
        .where(RunEvent.run_id == run.id)
        .order_by(RunEvent.sequence.desc())
    )
    event = RunEvent(
        run_id=run.id,
        sequence=(latest or 0) + 1,
        event_type=event_type,
        payload=__import__("json").dumps(payload),
    )
    session.add(event)
    session.flush()
    return event
