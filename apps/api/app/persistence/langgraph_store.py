from collections.abc import Iterator
from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver


@contextmanager
def postgres_checkpointer(database_url: str) -> Iterator[PostgresSaver]:
    """Yield the production LangGraph PostgreSQL checkpointer.

    Schema setup is explicit so deployment jobs, rather than every API request,
    control database DDL. The application uses the SQLAlchemy checkpoint seam for
    SQLite tests and can inject this checkpointer when a graph worker is enabled.
    """
    if not database_url.startswith("postgresql"):
        raise ValueError("LangGraph PostgreSQL checkpointer requires a PostgreSQL database URL.")
    with PostgresSaver.from_conn_string(database_url) as checkpointer:
        yield checkpointer
