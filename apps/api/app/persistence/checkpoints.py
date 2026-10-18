import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import AgentCheckpoint


class PostgresCheckpointStore:
    """Small LangGraph-compatible persistence seam backed by the application database.

    The runtime can use this store as its durable checkpointer without coupling the
    API layer to a particular graph implementation. PostgreSQL provides the same
    transactional semantics in production; SQLite remains useful for local tests.
    """

    def save(
        self,
        session: Session,
        *,
        run_id: str,
        organization_id: str,
        thread_id: str,
        namespace: str,
        checkpoint_key: str,
        state: dict[str, object],
    ) -> AgentCheckpoint:
        checkpoint = session.scalar(
            select(AgentCheckpoint).where(
                AgentCheckpoint.thread_id == thread_id,
                AgentCheckpoint.namespace == namespace,
                AgentCheckpoint.checkpoint_key == checkpoint_key,
            )
        )
        if checkpoint is None:
            checkpoint = AgentCheckpoint(
                run_id=run_id,
                organization_id=organization_id,
                thread_id=thread_id,
                namespace=namespace,
                checkpoint_key=checkpoint_key,
                state_json=json.dumps(state),
            )
            session.add(checkpoint)
        else:
            checkpoint.state_json = json.dumps(state)
            checkpoint.run_id = run_id
        session.flush()
        return checkpoint

    def load(
        self, session: Session, *, thread_id: str, namespace: str, checkpoint_key: str
    ) -> dict[str, object] | None:
        checkpoint = session.scalar(
            select(AgentCheckpoint).where(
                AgentCheckpoint.thread_id == thread_id,
                AgentCheckpoint.namespace == namespace,
                AgentCheckpoint.checkpoint_key == checkpoint_key,
            )
        )
        return json.loads(checkpoint.state_json) if checkpoint else None
