# Nexus-AI — Implementation Gaps

**Date:** 2026-10-19  
**Scope:** All gaps identified through direct source code inspection and test execution  

---

## 1. Critical Bugs (Must Fix Immediately)

### GAP-001: Cross-Tenant Cache Key Leak

**File**: `apps/api/app/routing/smart_router.py:67`  
**Severity**: CRITICAL  
**Status**: VERIFIED BUG  

**Description**:  
The cache key is computed in `prepare()` with `organization_id="pending"` then `complete()` attempts
to substitute the real org ID via `str.replace("pending", organization_id, 1)`. However, `make_key()`
returns a 64-character SHA-256 hex digest containing only `[0-9a-f]`. The string `"pending"` can
never appear in a valid hex digest. The replace call is therefore always a no-op.

**Impact**: Every tenant's cache key is permanently hashed with `org_id="pending"`. Two organizations
with matching `owner_id`, `workspace`, and `prompt` share the same cache key and can receive
each other's cached responses. This is a data isolation breach.

**Fix**:
```python
# In complete(), remove the two-step prepare/replace pattern.
# Pass organization_id directly:
key = self.cache.make_key(
    organization_id=organization_id,  # ← pass real org_id here
    owner_id=owner_id,
    workspace=workspace,
    model_id=self.model_router.settings.llm_primary_model_id,
    route_kind=decision.kind,
    prompt=prompt,
    context_fingerprint=hashlib.sha256(selected.prompt.encode("utf-8")).hexdigest(),
)
```

---

### GAP-002: Ruff F401 Lint Failure Blocks Backend CI

**File**: `apps/api/migrations/versions/0009_tenant_scoped_tool_idempotency.py:3`  
**Severity**: CRITICAL  
**Status**: VERIFIED BUG  

**Description**: `import sqlalchemy as sa` is present but `sa` is never referenced in the file.
Ruff correctly flags this as F401. The CI backend job fails at the lint step, preventing
both `pytest` and `pip-audit` from running.

**Fix**:
```python
# Delete line 3:
import sqlalchemy as sa  # ← remove this line
```

---

## 2. Security Gaps

### GAP-003: `role` Parameter Ignored in PolicyEngine

**File**: `apps/api/app/security/policy.py`  
**Severity**: HIGH  

```python
def evaluate(self, *, tool_id: str, role: str, workspace: str, mode: str) -> PolicyDecision:
    # role is NEVER referenced anywhere in this method body
    if workspace == "customer" and (tool_id.startswith("support.") or ".delete" in tool_id):
        ...
```

**Impact**: Admin and anonymous users receive identical risk decisions. Role-based
execution policy is not enforced at the engine level.

**Fix**: Add role-based checks, e.g.:
```python
if role not in {"internal_member", "admin"} and tool_id.startswith("admin."):
    return PolicyDecision(False, RiskCategory.critical, False, "insufficient_role")
```

---

### GAP-004: Audit Log Coverage — Only Approvals Logged

**File**: `apps/api/app/security/audit.py`  
**Severity**: HIGH  

`record_audit()` is called only from approval-related code paths:
- `approval.requested`
- `approval.approved`
- `approval.cancelled`

**Missing coverage**:
- Agent execution start/complete/fail
- LLM model calls
- Document access (search results)
- Tool execution (non-approval path)
- Conversation/run creation
- Authentication events

---

### GAP-005: Dev Auth Ships as Default

**File**: `apps/api/app/core/config.py`  
**Severity**: HIGH  

Default values: `dev_auth_enabled=True`, `identity_provider="development"`,
`dev_auth_secret="development-only-not-for-production"`.

Any deployment without an explicit `.env` override ships with predictable HMAC keys.
The production validator catches this at startup — but only if `APP_ENV=production` is set.

---

## 3. Agent & Routing Gaps

### GAP-006: All 6 Domain Agents Are Facades

**File**: `apps/api/app/agents/specialized.py:132-183`  
**Severity**: HIGH  

All domain agents (`DataEngineeringAgent`, `CRMAgent`, `CustomerSupportAgent`,
`CustomerSuccessAgent`, `FinanceAgent`, `CustomerProductAgent`) extend `DomainAgent`,
which extends `KnowledgeResearchAgent`. Their `execute()` method calls `super().execute()`
and appends a static disclaimer string. They share identical behavior.

**Declared capabilities they do not fulfill**:
- `CRMAgent`: declares `allowed_tools: {"support.create_ticket"}` — never invokes any tool
- All domain agents: declare `allowed_data_sources: {"approved_documents", "approved_metrics"}` — `approved_metrics` never accessed

---

### GAP-007: AnalyticsAgent Is a 2-Operand Calculator

**File**: `apps/api/app/agents/specialized.py:78-129`  
**Severity**: HIGH  

The `AnalyticsAgent.execute()` method:
1. Searches for exactly ONE regex match of `a OP b` (where OP is `+`, `-`, `*`, `/`)
2. Evaluates the arithmetic in Python
3. Returns the numeric result as a string

It cannot:
- Query any database or dataset
- Perform multi-step calculations
- Handle statistical aggregations
- Access any business metrics

**Routing defect**: The `Orchestrator.analytics_pattern` regex matches `calculate`, `sum`, `average`,
`compute`, `تحليل`, `احسب`, `متوسط`. Any of these words — even in a sentence with no arithmetic
expression — routes to `AnalyticsAgent`, which then raises `ValueError`.

---

### GAP-008: Context Summarization Is Character Truncation

**File**: `apps/api/app/routing/context.py`  
**Severity**: MEDIUM  

When context exceeds `max_chars` (default 12,000), the service returns mode `"summarized"`
but performs no summarization:

```python
prefix = "Conversation summary (older context compacted):\n"
tail = combined[-max(0, self.max_chars - len(prefix)):]
summary = f"{prefix}{tail}"  # ← raw character slice, may cut mid-word
```

---

### GAP-009: Semantic Cache Not Implemented

**Status**: NOT_STARTED (confirmed in `docs/remediation/tracker.md`)  
**Severity**: MEDIUM  

Only SHA-256 exact-match cache exists. No vector similarity, no threshold tuning,
no freshness rules, no semantic deduplication.

---

## 4. RAG Gaps

### GAP-010: Qdrant Vector Store Has No Search Method

**File**: `apps/api/app/rag/vector_store.py`  
**Severity**: HIGH  

`QdrantVectorStore` implements only `upsert()` and `delete_document()`. There is no
`search()` or `query()` method. `DocumentService.search()` does not call Qdrant at all —
it scans the SQL `document_chunks` table and computes cosine similarity in Python memory.

**Consequence**: Qdrant serves as a write-only backup store. Documents upserted to Qdrant
are never queried. The entire RAG retrieval path bypasses the vector index.

---

### GAP-011: Qdrant Failure Sets `ready_local_index` Status

**File**: `apps/api/app/rag/service.py`  
**Severity**: MEDIUM  

If `qdrant.upsert()` raises any exception, `document.status` is set to `"ready_local_index"`.
However, `DocumentService.search()` filters `Document.status == "ready"`. Documents
with `"ready_local_index"` status are permanently invisible to search.

---

### GAP-012: User-Level ACL Not Applied in RAG Search

**File**: `apps/api/app/rag/service.py:search()`  
**Severity**: MEDIUM  

`user_id` is accepted as a parameter but never referenced in the SQL query or
in-memory filters. All members of an organization in a workspace can access all
workspace documents regardless of document-level ownership.

---

### GAP-013: Qdrant Deletion Not Transactional

**File**: `apps/api/app/rag/service.py:delete()`  
**Severity**: MEDIUM  

```python
try:
    self.qdrant.delete_document(document.id)
except Exception:
    pass  # ← Qdrant failures silently ignored
```

If the database transaction rolls back, the Qdrant deletion cannot be undone.
If Qdrant fails, the document record is soft-deleted but vectors remain.

---

## 5. Tool & MCP Gaps

### GAP-014: Remote MCP Client Not Wired Into Tool Execution

**File**: `apps/api/app/tools/mcp.py` + `tools/service.py`  
**Severity**: MEDIUM  

`RemoteMCPClient` implements JSON-RPC 2.0 transport over HTTP but is never instantiated
or called from `ToolExecutionService.execute()`. Remote tool execution cannot be triggered
through any API path.

---

### GAP-015: Rate Limiter Is In-Memory and Not Distributed

**File**: `apps/api/app/tools/service.py`  
**Severity**: MEDIUM  

```python
self._calls: dict[tuple[str, str], list[float]] = {}
```

Rate limit state is per-process, per-worker. Multiple API workers or restarts
reset the counter. The configured `TOOL_RATE_LIMIT_PER_MINUTE` cannot be reliably enforced.

---

### GAP-016: Only 1 Tool Registered by Default

**File**: `apps/api/app/tools/defaults.py`  
**Severity**: MEDIUM  

Only `support.create_ticket` is registered. The `SupportTicketAdapter` generates
deterministic fake ticket IDs (`TCK-[A-F0-9]{10}`) — it is a mock, not a real integration.

---

## 6. Infrastructure & Config Gaps

### GAP-017: Duplicate `QDRANT_URL` in `.env.example`

**File**: `.env.example:18,40`  
**Severity**: MEDIUM  

- Line 18: `QDRANT_URL=http://localhost:6333` (intended default)
- Line 40: `QDRANT_URL=` (empty — overrides the default if file is parsed sequentially)

---

### GAP-018: `REDIS_URL` is an Orphan Variable

**File**: `.env.example:14`  
**Severity**: LOW  

`REDIS_URL=redis://localhost:6379/0` is in `.env.example` and `docker-compose.yml`
but is not read by any Python module, Settings class, or application code path.
Redis is not actually used.

---

### GAP-019: `.env.local` is Not Auto-Loaded

**File**: `apps/api/app/core/config.py:62-67`  
**Severity**: INFO  

The Settings class only reads `.env`. Creating `.env.local` at the repo root has no effect.
Developers must either:
1. Create `apps/api/.env` (where uvicorn runs from), or
2. Export environment variables directly in the shell

---

### GAP-020: `openapi-v1.yaml` Missing 12 Endpoints

**File**: `docs/api/openapi-v1.yaml`  
**Severity**: LOW  

The spec is a Phase 1 design document. It is missing all endpoints added in Phases 3–14:
`/auth/dev/session`, `/conversations/{id}`, `/approvals/*`, `/operations/*`, `/agents`,
`/models`, `/contract`, `/health/*`, `/tools`.

---

## 7. Testing Gaps

| Area | Gap |
|---|---|
| Qdrant integration | Zero tests for `upsert` or `delete_document` |
| `ready_local_index` fallback | Never tested |
| Tool rate limiting | No test exceeds 30/min threshold |
| Tool retry logic | Transient error retry loop untested |
| Tool verify failure | `verify() == False` path untested |
| Remote MCP → ToolService | Never exercised end-to-end |
| SLO threshold breaches | No test triggers queue/error/tool alerts |
| E2E browser tests | NOT_STARTED |
| Cross-tenant cache leak | Not caught by existing tests |
