# Nexus-AI API

FastAPI modular-monolith API. Phase 4 includes relational persistence, Alembic migrations, durable run checkpoints, recovery, and tenant-aware conversation access.

## Commands

```powershell
uv sync
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run alembic upgrade head
```

Set `DATABASE_URL` to a PostgreSQL URL for deployment, for example
`postgresql+psycopg://nexus:nexus@localhost:5432/nexus`. SQLite remains the local-test default.
