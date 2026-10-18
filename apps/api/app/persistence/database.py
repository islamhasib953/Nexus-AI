from collections.abc import Generator

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, database_url: str) -> None:
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(database_url, connect_args=connect_args)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    def create_schema(self) -> None:
        from app.persistence import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def recover_interrupted_runs(self) -> int:
        """Mark leased work as interrupted so a worker can resume it safely."""
        from datetime import UTC, datetime

        from app.persistence.models import Run, RunEvent

        with self.session_factory.begin() as session:
            runs = session.scalars(select(Run).where(Run.status == "running")).all()
            for run in runs:
                run.status = "interrupted"
                run.updated_at = datetime.now(UTC)
                run.error_code = "worker_interrupted"
                latest = session.scalar(
                    select(RunEvent.sequence)
                    .where(RunEvent.run_id == run.id)
                    .order_by(RunEvent.sequence.desc())
                )
                session.add(
                    RunEvent(
                        run_id=run.id,
                        sequence=(latest or 0) + 1,
                        event_type="run_interrupted",
                        payload='{"status":"interrupted","reason":"worker_restart"}',
                    )
                )
        return len(runs)

    def sessions(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
