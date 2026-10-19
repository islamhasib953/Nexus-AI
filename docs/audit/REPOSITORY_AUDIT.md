# Nexus-AI — Repository Audit Report

**Date:** 2026-10-19  
**Commit:** b2fb7d720ea5cd9f7143252c3b2c77c0f9a26915  
**Branch:** `main`  
**Verdict:** Local baseline PASS · Production BLOCKED  

---

## 1. Executive Summary

Nexus-AI has a well-structured, modular codebase with 14 complete development phases.
The foundation is solid: FastAPI backend with 14 SQLAlchemy models, 10 Alembic migrations,
68 automated tests at 91.31% coverage, a React/TypeScript frontend, structured CI/CD, and
detailed documentation (77 files across 10 subdirectories).

Critical gaps exist between intended capabilities and verified behavior. The highest-priority
findings that must be fixed before any further development:

| Severity | Finding | Location |
|---|---|---|
| 🔴 CRITICAL | Cross-tenant cache leak: cache key `replace("pending", org_id)` is always a no-op on SHA-256 hex | `routing/smart_router.py:67` |
| 🔴 CRITICAL | Ruff F401 lint failure blocks entire backend CI pipeline | `migrations/versions/0009_tenant_scoped_tool_idempotency.py:3` |
| 🟠 HIGH | `role` parameter accepted but completely ignored in `PolicyEngine.evaluate()` | `security/policy.py` |
| 🟠 HIGH | All 6 domain agents are identical facades — no real integrations | `agents/specialized.py` |
| 🟠 HIGH | `AnalyticsAgent` is a 2-operand regex calculator, not a data analyst | `agents/specialized.py:78` |
| 🟠 HIGH | `AnalyticsAgent` routing mismatch: words like "calculate" or "data" route to it, crashes on non-math | `agents/orchestrator.py:30` |
| 🟠 HIGH | Dev auth ships as default (`DEV_AUTH_ENABLED=true`, `IDENTITY_PROVIDER=development`) | `core/config.py` |
| 🟡 MEDIUM | Context "summarization" is character truncation — no LLM summarization | `routing/context.py` |
| 🟡 MEDIUM | Semantic cache is completely absent (NOT_STARTED) | — |
| 🟡 MEDIUM | Qdrant has NO search method — RAG search uses in-memory SQL scan | `rag/vector_store.py` |
| 🟡 MEDIUM | `user_id` accepted in RAG search but never used — no user-level ACL | `rag/service.py` |
| 🟡 MEDIUM | Remote MCP client exists but is NOT wired into `ToolExecutionService` | `tools/mcp.py` |
| 🟡 MEDIUM | Tool rate limiter is in-memory only — not distributed, resets on restart | `tools/service.py` |
| 🟡 MEDIUM | Audit log only covers approvals — runs, LLM calls, agent delegation not logged | `security/audit.py` |
| 🟡 MEDIUM | `QDRANT_URL` appears twice in `.env.example` — second (empty) entry overrides first | `.env.example` |
| 🟡 MEDIUM | `openapi-v1.yaml` covers Phase 1 only — 12 live endpoints missing from spec | `docs/api/openapi-v1.yaml` |
| 🟡 MEDIUM | `REDIS_URL` in `.env.example` but Redis is not used anywhere in application code | `.env.example` |
| 🔵 INFO | SQLite default — PostgreSQL required for production | `core/config.py` |
| 🔵 INFO | Hash embeddings default — blocked from production by Pydantic validator | `core/config.py` |

---

## 2. Runtime Configuration

### 2.1 Environment File Loading

- **Library**: `pydantic-settings` `BaseSettings`
- **Target file**: `.env` (relative to `apps/api/` — the directory where uvicorn is launched)
- **`.env.local` is NOT loaded automatically** — the settings class only reads `.env`
- **Case sensitivity**: False — `APP_ENV` and `app_env` are equivalent

### 2.2 Known `.env.example` Defects

| Issue | Detail |
|---|---|
| Duplicate `QDRANT_URL` | Line 18: `=http://localhost:6333`, Line 40: `=` (empty). Second overrides first. |
| Empty `DEV_AUTH_SECRET` | With `DEV_AUTH_ENABLED=true`, an empty secret generates an ephemeral HMAC key — sessions invalidate on restart |
| `REDIS_URL` orphan | Redis is configured in `.env.example` but never read or used in any application code |

### 2.3 Production Validation (Pydantic `@model_validator`)

These rules abort startup when `APP_ENV=production`:

- `dev_auth_enabled` must be `False`
- `identity_provider` must not be `"development"`
- `identity_issuer_url`, `identity_audience`, `identity_jwks_url` must all be non-empty
- `embedding_provider` must not be `"hash"`

### 2.4 Complete Settings Reference (53 variables)

| Variable | Default | Constraint | Notes |
|---|---|---|---|
| `APP_ENV` | `development` | — | Use `production` to activate all guards |
| `APP_NAME` | `nexus-ai-api` | — | |
| `APP_VERSION` | `0.1.0` | — | |
| `IDENTITY_PROVIDER` | `development` | Cannot be `development` in prod | |
| `IDENTITY_ISSUER_URL` | `` | Required in prod | |
| `IDENTITY_AUDIENCE` | `` | Required in prod | |
| `IDENTITY_JWKS_URL` | `` | Required in prod | |
| `IDENTITY_ALGORITHMS` | `RS256` | — | Comma-separated |
| `LOG_LEVEL` | `INFO` | — | |
| `API_HOST` | `0.0.0.0` | — | |
| `API_PORT` | `8000` | 1–65535 | |
| `WEB_ORIGIN` | `http://localhost:5173` | Valid URL | CORS origin |
| `MODEL_PROVIDER` | `mock` | — | |
| `MODEL_NAME` | `mock-chat` | — | |
| `LLM_PRIMARY_MODEL_ID` | `mock-chat` | — | |
| `LLM_FALLBACK_MODEL_IDS` | `` | — | Comma-separated |
| `LLM_TIMEOUT_SECONDS` | `20.0` | 0 < x ≤ 120 | |
| `LLM_MAX_RETRIES` | `1` | 0–3 | |
| `LLM_TENANT_DAILY_BUDGET_USD` | `0.0` | ≥ 0 | 0 = disabled |
| `LLM_GLOBAL_DAILY_BUDGET_USD` | `0.0` | ≥ 0 | 0 = disabled |
| `LLM_ALLOW_PAID_FALLBACK` | `False` | — | |
| `ROUTER_CACHE_TTL_SECONDS` | `900` | 0–86400 | |
| `ROUTER_CONTEXT_MAX_CHARS` | `12000` | 1000–100000 | |
| `ROUTER_CACHE_ENABLED` | `True` | — | |
| `AGENT_MAX_ITERATIONS` | `3` | 1–10 | |
| `AGENT_MAX_TOKENS` | `2048` | 128–16000 | |
| `AGENT_TIMEOUT_SECONDS` | `30.0` | 0 < x ≤ 300 | |
| `GROQ_API_KEY` | `` | — | Required for Groq |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | — | |
| `HUGGINGFACE_API_KEY` | `` | — | Required for HuggingFace |
| `HUGGINGFACE_BASE_URL` | `https://router.huggingface.co/v1` | — | |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | — | |
| `QDRANT_URL` | `` | — | Empty = Qdrant disabled |
| `QDRANT_COLLECTION` | `nexus_chunks` | — | |
| `MCP_REMOTE_URL` | `` | — | Empty = remote MCP disabled |
| `TOOL_RATE_LIMIT_PER_MINUTE` | `30` | 1–1000 | |
| `RAG_CHUNK_SIZE` | `900` | 200–4000 | |
| `RAG_DEFAULT_TOP_K` | `5` | 1–20 | |
| `RAG_MIN_SCORE` | `0.12` | -1–1 | |
| `EMBEDDING_PROVIDER` | `hash` | Cannot be `hash` in prod | |
| `EMBEDDING_MODEL_ID` | `hash-embedding-v1` | — | |
| `EMBEDDING_BASE_URL` | `` | Required if provider ≠ hash | |
| `EMBEDDING_API_KEY` | `` | — | |
| `EMBEDDING_DIMENSIONS` | `128` | 8–4096 | |
| `OBSERVABILITY_ENABLED` | `True` | — | |
| `METRICS_WINDOW_HOURS` | `24` | 1–720 | |
| `OPS_QUEUE_WARNING_THRESHOLD` | `10` | 1–10000 | |
| `OPS_ERROR_RATE_CRITICAL_THRESHOLD` | `0.05` | 0–1 | |
| `OPS_TOOL_FAILURE_CRITICAL_THRESHOLD` | `0.05` | 0–1 | |
| `METRICS_RETENTION_DAYS` | `30` | 1–3650 | |
| `DATABASE_URL` | `sqlite:///./data/nexus.db` | — | |
| `DEV_AUTH_ENABLED` | `True` | Must be False in prod | |
| `DEV_AUTH_SECRET` | `development-only-not-for-production` | — | Change in dev |

---

## 3. Authentication & Identity

### 3.1 Development Auth (Current Default)

- `IDENTITY_PROVIDER=development`, `DEV_AUTH_ENABLED=true`
- Token format: `base64url(json_payload).base64url(hmac_sha256_signature)`, 8-hour lifetime
- 3 profiles: `internal` (internal_member), `customer` (external_customer), `other`
- Endpoint: `POST /api/v1/auth/dev/session`
- Production guard: Returns HTTP 404 if `app_env=production` or `dev_auth_enabled=False`

### 3.2 OIDC Authentication (Fully Implemented, Not Activated)

`OIDCAuthenticator` is complete with:
- JWKS fetching with 300s TTL cache
- Key rotation (forced reload on unknown `kid`)
- PyJWT decoding requiring `exp`, `iat`, `sub`
- Tenant claims: `sub`, `org`/`organization_id`, `role`, `workspace`
- Returns HTTP 503 if `IDENTITY_PROVIDER=oidc` but no authenticator initialized

**To activate**: `IDENTITY_PROVIDER=oidc` + supply `IDENTITY_ISSUER_URL`, `IDENTITY_AUDIENCE`, `IDENTITY_JWKS_URL`

---

## 4. Test Results (Executed 2026-10-19)

```
Total tests: 68
Passed: 68
Failed: 0
Coverage: 91.31% (gate: 90%)
Ruff check: FAILED (F401 in migration 0009)
Ruff format: PASSED
```

**Ruff failure**: `F401 sqlalchemy imported but unused` in `migrations/versions/0009_tenant_scoped_tool_idempotency.py:3`
This causes the entire backend CI job to fail before tests run.

### Coverage Gaps (modules below 85%)

| Module | Coverage | Missing Lines |
|---|---|---|
| `tools/service.py` | 74% | Approval flow, retry logic, tool execution paths |
| `persistence/runs.py` | 79% | State transition error paths |
| `persistence/langgraph_store.py` | 78% | LangGraph integration |
| `rag/chunking.py` | 77% | Chunk boundary edge cases |
| `rag/vector_store.py` | 71% | Qdrant upsert/delete (untested) |

---

## 5. Security Assessment

### 5.1 Critical Security Issues

#### Cache Key Cross-Tenant Leak

File: `apps/api/app/routing/smart_router.py:67`

```python
# BROKEN — pending_key is a 64-char hex SHA-256 digest
# The string "pending" NEVER appears in a valid hex digest
# This replace() call is always a no-op
key = pending_key.replace("pending", organization_id, 1)
```

**Consequence**: All cache entries are keyed with `organization_id="pending"`. Any two tenants
sharing workspace + owner_id + prompt receive identical cache keys. Tenant A's response is
served to Tenant B.

**Fix** (safe, minimal): Remove the two-step prepare/replace pattern. Pass `organization_id`
directly to `make_key()` in `complete()`.

#### Ruff F401 CI Blocker

File: `apps/api/migrations/versions/0009_tenant_scoped_tool_idempotency.py:3`

```python
import sqlalchemy as sa  # unused — sa is never referenced in this file
```

**Fix**: Delete line 3.

### 5.2 High Security Issues

| Issue | File | Risk |
|---|---|---|
| `role` ignored in PolicyEngine | `security/policy.py:evaluate()` | Admin and anonymous get identical risk decisions |
| Dev auth default enabled | `core/config.py` | Default config has `DEV_AUTH_ENABLED=True` |
| Audit log coverage gap | `security/audit.py` | Only approvals logged; LLM, agent, RAG access unlogged |
| Domain agents declare tools they never invoke | `agents/specialized.py` | Declared `allowed_tools` capabilities are dead metadata |

### 5.3 Medium Security Issues

| Issue | File | Risk |
|---|---|---|
| In-memory rate limiter | `tools/service.py` | Not distributed — resets on restart |
| Qdrant delete fire-and-forget | `rag/service.py` | `except Exception: pass` swallows failures |
| Context truncation labelled "summarized" | `routing/context.py` | Misleading — can slice mid-word |
| User ACL unused in RAG search | `rag/service.py` | All org members see all workspace documents |
| Remote MCP not wired | `tools/mcp.py` | `RemoteMCPClient` unreachable from tool execution |
| Prompt injection detection is regex only | `rag/service.py` | LLM-level adversarial injection not covered |

---

## 6. External Dependencies

| Dependency | Required For | Current Status |
|---|---|---|
| OIDC/JWKS Provider (Auth0, Keycloak, etc.) | Production auth | NOT configured |
| PostgreSQL | Production database | NOT configured (SQLite default) |
| Qdrant (vector store) | Semantic RAG | NOT configured (empty `QDRANT_URL`) |
| Redis | Caching/queuing | Config exists — **NOT USED in code** |
| Groq API key | Cloud LLM | Empty |
| HuggingFace API key | Cloud LLM | Empty |
| Ollama runtime + model | Local LLM | Not installed |
| Embedding provider | Production RAG | NOT configured (hash default) |
| AWS (ECR, EC2, SSM, RDS) | Production deployment | NOT provisioned |
| CloudWatch | Telemetry/alerting | NOT provisioned |

---

## 7. Accounts and Credentials Required

The following external accounts/credentials must be obtained before specific phases can proceed:

| Credential | Provider | Phase Required | Notes |
|---|---|---|---|
| Free API key | Groq (console.groq.com) | Phase 1 (real LLM) | Free tier sufficient |
| Free API key | HuggingFace (huggingface.co) | Phase 1 (real LLM) | Free tier sufficient |
| Ollama installation | ollama.com/download | Phase 1 (local LLM) | Windows installer |
| OIDC issuer | Auth0/Keycloak/Clerk/etc. | Phase 3 (production auth) | Free tier available |
| Qdrant Cloud or local | qdrant.tech | Phase 4 (real RAG) | Free cluster available |
| Embedding model | Ollama or OpenAI-compatible | Phase 4 (real RAG) | nomic-embed-text via Ollama is free |
| AWS account | AWS | Phase 7 (production deploy) | Requires explicit provisioning |
