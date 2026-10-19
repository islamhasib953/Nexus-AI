# Nexus-AI — Phase Execution Plan

**Date:** 2026-10-19  
**Based on:** Phase 0 repository audit (REPOSITORY_AUDIT.md, IMPLEMENTATION_GAPS.md)  
**Principle:** Verify each execution path before expanding. Fix before building new.

---

## Phase 1 — Fix Critical Blockers and Establish Stable Local Baseline

**Goal**: The backend CI pipeline passes completely. Every existing test passes. The app starts.
**Duration estimate**: 1–2 sessions

### Tasks

| Task | File | Change | Closes Gap |
|---|---|---|---|
| P1-T1 | `migrations/versions/0009_tenant_scoped_tool_idempotency.py` | Remove `import sqlalchemy as sa` (line 3) | GAP-002 |
| P1-T2 | `routing/smart_router.py` | Fix cross-tenant cache key — pass real `organization_id` directly to `make_key()` | GAP-001 |
| P1-T3 | `.env.example` | Remove duplicate `QDRANT_URL` entry (line 40), remove orphan `REDIS_URL` | GAP-017, GAP-018 |
| P1-T4 | `.env.example` | Add `DEV_AUTH_SECRET=change-me-in-dev` with comment warning | GAP-005 |
| P1-T5 | `apps/api/.env` | Create local working `.env` with mock provider, SQLite, hash embeddings | — |
| P1-T6 | Run tests | `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest` | — |

### Acceptance Criteria

- [ ] `uv run ruff check .` exits 0
- [ ] `uv run pytest` exits 0 with ≥91% coverage
- [ ] `uvicorn` starts without errors using mock provider
- [ ] `GET /api/v1/health/live` returns `{"status": "ok"}`
- [ ] `POST /api/v1/auth/dev/session` returns a valid token
- [ ] Frontend loads at `http://localhost:5173`
- [ ] Cache key test: same prompt from different org IDs produces different cache keys

### External Requirements

_None — this phase requires no external accounts, APIs, or credentials._

---

## Phase 2 — Connect and Verify a Real LLM Provider

**Goal**: At least one real model provider works end-to-end through the existing routing layer.
**Prerequisite**: Phase 1 complete.
**Duration estimate**: 1 session

### Tasks

**Option A: Groq (recommended first — fastest setup)**
1. Create free account at https://console.groq.com
2. Generate API key (free, no credit card required)
3. Add to `apps/api/.env`: `GROQ_API_KEY=your_key_here`, `LLM_PRIMARY_MODEL_ID=groq-gpt-oss-20b`
4. Submit a request and verify the response comes from Groq
5. Check `ModelUsage` table for recorded token counts

**Option B: Ollama (local, no account required)**
1. Download and install from https://ollama.com/download/OllamaSetup.exe
2. Open PowerShell: `ollama pull qwen3:8b` (downloads ~5GB model)
3. Verify: `ollama list` shows `qwen3:8b`
4. Add to `apps/api/.env`: `LLM_PRIMARY_MODEL_ID=ollama-qwen3`
5. Submit a request and verify the response comes from Ollama

**Common tasks for both options**:
- Add/update tests for the real provider path (mock the HTTP call with recorded fixture)
- Verify circuit breaker: stop the provider, confirm fallback to mock
- Verify token usage is recorded in `ModelUsage`
- Verify budget enforcement: set `LLM_TENANT_DAILY_BUDGET_USD=0.00001`, confirm 429 on next call

### Acceptance Criteria

- [ ] Real LLM response received and displayed in frontend chat
- [ ] `ModelUsage` row created with non-zero `input_tokens` and `output_tokens`
- [ ] Provider circuit breaker trips correctly on simulated failure
- [ ] Budget enforcement rejects request when limit exceeded
- [ ] All 68 existing tests still pass

### External Requirements

- **Groq**: Free account at console.groq.com + API key
- **Ollama**: Windows installer + `qwen3:8b` model (~5GB disk)

---

## Phase 3 — Fix Policy Engine Role Enforcement and Expand Audit Logging

**Goal**: The policy engine uses the `role` parameter. Critical actions are audited.
**Prerequisite**: Phase 1 complete.
**Duration estimate**: 1 session

### Tasks

| Task | File | Change |
|---|---|---|
| P3-T1 | `security/policy.py` | Add role-based checks: only `internal_member`/`admin` can execute `admin.*` or `*.delete` tools |
| P3-T2 | `security/audit.py` | Add audit records for: run created, run completed, run failed, agent delegation, LLM call, document search |
| P3-T3 | `api/routes/workspace.py` | Call `record_audit()` at run creation and completion |
| P3-T4 | Tests | Add: role enforcement test (anonymous user denied admin tool), audit record tests for new events |

### Acceptance Criteria

- [ ] `external_customer` role cannot execute `admin.*` tools regardless of workspace
- [ ] Every run completion creates an `AuditLog` row
- [ ] Every document search creates an `AuditLog` row
- [ ] All existing tests pass

### External Requirements

_None._

---

## Phase 4 — Real Embeddings and Qdrant Vector Search

**Goal**: RAG uses a real embedding model. Qdrant search works end-to-end.
**Prerequisite**: Phase 2 complete (Ollama or embedding provider available).
**Duration estimate**: 1–2 sessions

### Tasks

| Task | File | Change |
|---|---|---|
| P4-T1 | `rag/vector_store.py` | Add `search(query_vector, limit, filters)` method that calls Qdrant `/collections/{col}/points/search` |
| P4-T2 | `rag/service.py` | Update `search()` to use `qdrant.search()` when Qdrant is enabled, fall back to SQL scan |
| P4-T3 | `rag/service.py` | Fix silent Qdrant deletion failure — log the error, do not silently pass |
| P4-T4 | `rag/service.py` | Fix `ready_local_index` — include these documents in search or re-index them |
| P4-T5 | Config | Set `EMBEDDING_PROVIDER=openai-compatible`, `EMBEDDING_BASE_URL=http://localhost:11434/v1`, `EMBEDDING_MODEL_ID=nomic-embed-text` (via Ollama) |
| P4-T6 | Config | Set `QDRANT_URL=http://localhost:6333` and start Qdrant via Docker |
| P4-T7 | Tests | Add Qdrant integration tests (with mocked HTTP), test search path, test fallback on Qdrant error |

**Qdrant setup** (local Docker):
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

**Ollama embedding model**:
```powershell
ollama pull nomic-embed-text
```

### Acceptance Criteria

- [ ] Document ingested → Qdrant receives upsert request with real embedding vector
- [ ] Search query → Qdrant search is called → semantically relevant chunks returned
- [ ] `EMBEDDING_PROVIDER=hash` correctly blocked by production validator
- [ ] Qdrant deletion failure is logged (not silently swallowed)
- [ ] `ready_local_index` documents are queryable or re-indexed
- [ ] All existing tests pass

### External Requirements

- **Docker Desktop** (for local Qdrant)
- **Ollama** with `nomic-embed-text` model (~270MB), OR an OpenAI-compatible embedding API

---

## Phase 5 — Fix AnalyticsAgent and Improve Orchestration Routing

**Goal**: Analytics routing no longer crashes. Routing is more robust.
**Prerequisite**: Phase 2 complete.
**Duration estimate**: 1 session

### Tasks

| Task | File | Change |
|---|---|---|
| P5-T1 | `agents/orchestrator.py` | Fix `analytics_pattern`: remove duplicate `calculate`, add intent disambiguation — only route to AnalyticsAgent if prompt contains a numeric expression |
| P5-T2 | `agents/specialized.py` | Improve `AnalyticsAgent`: handle case where no arithmetic expression found — fall back to `GeneralAgent` behavior instead of raising `ValueError` |
| P5-T3 | `agents/orchestrator.py` | Add routing confidence threshold: if no pattern matches well, route to `general` |
| P5-T4 | Tests | Add routing tests: "what is the average salary" → general (not analytics), "calculate 5 + 3" → analytics |

### Acceptance Criteria

- [ ] Prompt "what is the average performance?" does NOT crash with ValueError
- [ ] Prompt "calculate 10 * 3" → AnalyticsAgent → returns `30`
- [ ] All 68 existing tests pass

### External Requirements

_None._

---

## Phase 6 — Real Domain Agent (Choose One)

**Goal**: One domain agent performs a real, useful, non-facade workflow.
**Prerequisite**: Phases 2 and 4 complete.
**Duration estimate**: 2–3 sessions

**Recommended starting agent**: `CustomerSupportAgent`

### Tasks

1. Define the CustomerSupportAgent contract:
   - Input: user support question
   - Data sources: uploaded support documentation + conversation history
   - Output: answer with citations + optional ticket draft
   - Tools: `support.create_ticket` (replace mock adapter with real or configurable one)
2. Implement real tool invocation from within the agent
3. Replace `SupportTicketAdapter` with a real HTTP integration (or a configurable webhook)
4. Add agent-specific tests

### Acceptance Criteria

- [ ] CustomerSupportAgent returns a cited answer from ingested support docs
- [ ] CustomerSupportAgent can draft a support ticket (tool call)
- [ ] Approval flow triggers for ticket creation (requires approval)
- [ ] Internal vs customer workspace correctly limits access

### External Requirements

- A real or mock support system webhook URL (or Zapier/n8n integration)

---

## Phase 7 — Production Authentication (OIDC)

**Goal**: Production-grade identity replaces dev auth.
**Prerequisite**: Phase 1 complete.
**Duration estimate**: 1–2 sessions

### Steps

1. Choose an OIDC provider (recommended free options: **Auth0**, **Clerk**, **Keycloak self-hosted**)
2. Create application, configure:
   - `IDENTITY_PROVIDER=oidc`
   - `IDENTITY_ISSUER_URL=https://your-domain.auth0.com/`
   - `IDENTITY_AUDIENCE=https://nexus-ai-api`
   - `IDENTITY_JWKS_URL=https://your-domain.auth0.com/.well-known/jwks.json`
3. Configure JWT custom claims for `org`, `role`, `workspace`
4. Update frontend to use OIDC login flow instead of dev profile picker
5. Run tenant isolation tests:
   - Token from Org A cannot access Org B's conversations
   - Token from Org A cannot access Org B's documents

### Acceptance Criteria

- [ ] `DEV_AUTH_ENABLED=false` — dev auth completely disabled
- [ ] Valid OIDC token → successful request
- [ ] Expired token → 401
- [ ] Missing `org` claim → 401
- [ ] Cross-tenant ID manipulation → 403 or 404

### External Requirements

- **Free OIDC provider**: Auth0 (free tier), Clerk (free tier), or self-hosted Keycloak
- Will need to share provider URLs and test user credentials — NO real keys in code

---

## Phase 8 — Production Database (PostgreSQL)

**Goal**: SQLite replaced by PostgreSQL. All migrations run successfully.
**Prerequisite**: Phase 7 complete.
**Duration estimate**: 1 session

### Steps

1. Start PostgreSQL (local Docker or managed service):
   ```powershell
   docker run -p 5432:5432 -e POSTGRES_PASSWORD=nexus -e POSTGRES_DB=nexus postgres:17-alpine
   ```
2. Set `DATABASE_URL=postgresql+psycopg://postgres:nexus@localhost:5432/nexus`
3. Run: `uv run --directory apps/api alembic upgrade head`
4. Verify all 10 migrations apply cleanly
5. Run full test suite against PostgreSQL
6. Verify run recovery works: kill the server mid-run, restart, check interrupted run detection

### Acceptance Criteria

- [ ] All 10 migrations apply without errors on PostgreSQL
- [ ] All 68 tests pass against PostgreSQL
- [ ] Run recovery correctly transitions `running` → `interrupted` on restart
- [ ] `alembic downgrade -1` works for the latest migration

### External Requirements

- **Docker Desktop** (for local PostgreSQL), OR managed PostgreSQL service

---

## Phase 9 — Distributed Rate Limiting and MCP Hardening

**Goal**: Rate limiting is persistent and distributed. Remote MCP is wired.
**Prerequisite**: Phase 4 complete (Qdrant/Redis context).
**Duration estimate**: 1–2 sessions

### Tasks

| Task | Change |
|---|---|
| Replace in-memory rate limiter | Use database-backed sliding window via `ToolExecution` table counts |
| Wire `RemoteMCPClient` | Connect `RemoteMCPClient` to `ToolExecutionService.execute()` when `MCP_REMOTE_URL` is set |
| Full JSON schema validation | Replace presence-only check with actual JSON Schema validation in `LocalMCPServer.validate_call()` |
| Test rate limiting | Add test that exceeds 30 calls in 60s window |

### Acceptance Criteria

- [ ] Rate limit enforced across simulated multi-worker scenario (DB-backed)
- [ ] Remote MCP tool appears in `/api/v1/tools` when `MCP_REMOTE_URL` is configured
- [ ] Invalid parameter type rejected by schema validator

### External Requirements

- Optional: A remote MCP-compatible server for live integration test

---

## Phase 10 — E2E Testing and Production Deployment

**Goal**: End-to-end browser tests. Production deploy succeeds.
**Prerequisite**: Phases 7 + 8 complete.
**Duration estimate**: 2–3 sessions

### Tasks

1. Add Playwright or Cypress E2E tests covering:
   - Login → create conversation → send message → receive response
   - Upload document → search knowledge → verify citation
   - Internal tool execution → approval flow → tool completes
2. Configure GitHub Actions for E2E tests
3. Provision AWS infrastructure (EC2, RDS, ECR) — requires explicit approval
4. Run full deploy pipeline: `deploy.yml` with `workflow_dispatch`
5. Production smoke tests: health, auth, LLM call, document ingest/search

### Acceptance Criteria

- [ ] E2E tests pass against running local stack
- [ ] Production containers build and push to ECR without errors
- [ ] Migration runs successfully on RDS PostgreSQL
- [ ] Production smoke test: all health checks green
- [ ] CloudWatch metrics visible for at least one real request

### External Requirements

- **AWS account** with EC2, RDS, ECR, SSM permissions
- **Domain + TLS certificate** (for CORS and OIDC callback)
- **GitHub secrets**: `AWS_DEPLOY_ROLE_ARN`, `vars.AWS_REGION`, `vars.EC2_INSTANCE_ID`, `vars.VITE_API_BASE_URL`

---

## Summary Table

| Phase | Goal | External Needs | Blocks |
|---|---|---|---|
| 1 | Fix CI + cache bug | None | Everything |
| 2 | Real LLM provider | Groq key OR Ollama | Phase 6 |
| 3 | Policy + audit | None | Phase 7 |
| 4 | Real RAG + Qdrant | Docker + Ollama embed | Phase 6 |
| 5 | Fix analytics routing | None | — |
| 6 | Real domain agent | Webhook/integration | Phase 10 |
| 7 | OIDC production auth | OIDC provider | Phase 10 |
| 8 | PostgreSQL | Docker | Phase 10 |
| 9 | Distributed rate limit + MCP | Optional MCP server | Phase 10 |
| 10 | E2E + production deploy | AWS account | — |

---

## Immediate Next Action

1. **Fix GAP-002** (Ruff F401): Delete line 3 of migration `0009`.
2. **Fix GAP-001** (Cache key bug): Refactor `smart_router.py` to pass `organization_id` directly.
3. Run `uv run ruff check .` → must exit 0.
4. Run `uv run pytest` → 68 tests must pass.
5. Git commit with message: `fix: resolve CI lint blocker and cross-tenant cache key bug`.
6. Push to `main` and verify CI pipeline passes all 3 jobs.
7. Proceed to Phase 2 (real LLM provider).
