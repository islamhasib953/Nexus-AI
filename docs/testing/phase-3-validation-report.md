# Phase 3 validation report

## Executed checks

| Check | Result |
| --- | --- |
| `uv run pytest` in `apps/api` | PASS — 14 tests, 94.04% coverage |
| `uv run ruff check .` in `apps/api` | PASS |
| `uv run ruff format --check .` in `apps/api` | PASS |
| `npm run typecheck` in `apps/web` | PASS |
| `npm run lint` in `apps/web` | PASS |
| `npm run test -- --run` in `apps/web` | PASS — 2 tests |
| `npm run build` in `apps/web` | PASS |
| `git diff --check` | PASS |
| Live Uvicorn smoke test | PASS — session, conversation, run, SSE completion, and cross-user denial (`404`) |

## Phase 3 coverage

- Development-only signed bearer sessions with server-side verification and expiration.
- SQLite persistence through SQLAlchemy for conversations, messages, runs, and run events.
- Server-authorized conversation and run access; cross-user access returns not found.
- Internal/customer workspace boundary check.
- Conversation creation, retrieval, message history, run creation, status retrieval, and safe cancellation.
- SSE event stream with lifecycle events and streamed assistant deltas.
- Responsive workspace UI with sign-in, conversation navigation, new conversation, message submission, stream display, cancel, error, and sign-out states.
- API client bearer-token handling and frontend tests.

## Scope limitation

The authentication implementation is intentionally development-only. It is a signed local token adapter, not production SSO/OIDC. SQLite is the local persistence profile; PostgreSQL/Alembic, durable workers, and resumable multi-step execution belong to later phases. The streamed response is a deterministic foundation response and does not invoke an LLM yet.
