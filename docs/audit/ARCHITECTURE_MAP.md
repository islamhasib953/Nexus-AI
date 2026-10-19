# Nexus-AI — Architecture Map

**Generated:** 2026-10-19  
**Commit:** b2fb7d720ea5cd9f7143252c3b2c77c0f9a26915  

---

## 1. Repository Layout

```text
Nexus-AI/
├── apps/
│   ├── api/                          # FastAPI backend (Python 3.12, uv)
│   │   ├── app/
│   │   │   ├── main.py               # App factory, lifespan, middleware, route mounts
│   │   │   ├── core/
│   │   │   │   ├── config.py         # Settings (pydantic-settings, 53 env vars, .env)
│   │   │   │   ├── auth.py           # OIDCAuthenticator + dev auth + require_principal
│   │   │   │   ├── logging.py        # JsonFormatter, structured JSON logs
│   │   │   │   └── middleware.py     # CorrelationIdMiddleware, request_id context
│   │   │   ├── api/
│   │   │   │   ├── schemas.py        # ErrorDetail, ErrorEnvelope
│   │   │   │   └── routes/
│   │   │   │       ├── health.py     # GET /health/live, /health/ready
│   │   │   │       ├── contract.py   # GET /contract
│   │   │   │       ├── workspace.py  # Auth, conversations, runs, SSE events, agents, models
│   │   │   │       ├── knowledge.py  # Document ingest, list, search, delete
│   │   │   │       ├── tools.py      # Tool list + execute
│   │   │   │       ├── approvals.py  # Approval CRUD + approve/cancel
│   │   │   │       └── operations.py # Overview + alerts (internal only)
│   │   │   ├── agents/
│   │   │   │   ├── base.py           # BaseAgent abstract class
│   │   │   │   ├── contracts.py      # AgentRequest, AgentResponse, AgentProgress, AgentFailure
│   │   │   │   ├── registry.py       # AgentCapability + AgentRegistry (workspace auth)
│   │   │   │   ├── orchestrator.py   # Orchestrator: regex routing + agent dispatch
│   │   │   │   └── specialized.py    # KnowledgeResearchAgent, AnalyticsAgent, DomainAgent + 6 subclasses
│   │   │   ├── llm/
│   │   │   │   ├── models.py         # CompletionRequest, CompletionResult, ProviderUnavailableError
│   │   │   │   ├── providers.py      # MockProvider, OpenAICompatibleProvider, OllamaProvider
│   │   │   │   ├── registry.py       # ModelRegistry (4 models: mock, groq, hf, ollama)
│   │   │   │   └── router.py         # ModelRouter: circuit breaker, fallback, budget, usage recording
│   │   │   ├── routing/
│   │   │   │   ├── classifier.py     # RequestClassifier: regex → action/current_data/retrieval/direct_model
│   │   │   │   ├── context.py        # ContextSelectionService: history assembly (truncation, not summarization)
│   │   │   │   ├── cache.py          # ExactResponseCache: SHA-256 keyed DB cache
│   │   │   │   └── smart_router.py   # SmartRequestRouter: classify → cache → model → log
│   │   │   ├── persistence/
│   │   │   │   ├── models.py         # 14 SQLAlchemy 2.0 mapped models
│   │   │   │   ├── database.py       # Database class: engine, session factory, schema create, run recovery
│   │   │   │   ├── runs.py           # Run state machine: RUN_TRANSITIONS, transition_run, append_run_event
│   │   │   │   ├── checkpoints.py    # PostgresCheckpointStore (generic save/load seam)
│   │   │   │   └── langgraph_store.py # postgres_checkpointer context manager
│   │   │   ├── rag/
│   │   │   │   ├── chunking.py       # chunk_text(): whitespace-aware chunking with overlap
│   │   │   │   ├── embeddings.py     # HashEmbeddingModel, OpenAICompatibleEmbeddingModel
│   │   │   │   ├── models.py         # Citation, RetrievalResult
│   │   │   │   ├── vector_store.py   # QdrantVectorStore: upsert + delete (NO search method)
│   │   │   │   └── service.py        # DocumentService: ingest, search (in-memory SQL), delete
│   │   │   ├── tools/
│   │   │   │   ├── contracts.py      # ToolDefinition, ToolCall, ToolResult
│   │   │   │   ├── registry.py       # ToolRegistry: workspace + role authorization
│   │   │   │   ├── defaults.py       # build_tool_registry(): registers support.create_ticket
│   │   │   │   ├── integrations.py   # SupportTicketAdapter (deterministic mock ID generator)
│   │   │   │   ├── mcp.py            # LocalMCPServer, RemoteMCPClient (NOT wired to service)
│   │   │   │   └── service.py        # ToolExecutionService: idempotency, approval, rate limit, timeout
│   │   │   ├── security/
│   │   │   │   ├── policy.py         # PolicyEngine: risk evaluation (role param IGNORED)
│   │   │   │   └── audit.py          # record_audit(): synchronous DB write (approvals only)
│   │   │   └── operations/
│   │   │       └── service.py        # OperationsService: metrics, cost, SLO alerts (pull-based)
│   │   ├── migrations/
│   │   │   └── versions/             # 10 Alembic migrations (0000–0009)
│   │   ├── tests/                    # 68 pytest tests, 91.31% coverage
│   │   ├── pyproject.toml            # Python 3.12+, 12 runtime deps, 5 dev deps
│   │   └── alembic.ini
│   └── web/                          # React 19 + TypeScript 6 + Vite 8 frontend
│       └── src/
│           ├── App.tsx               # Login view, Chat workspace, Operations dashboard
│           ├── styles.css            # Design system (dark/light tokens)
│           └── api/
│               ├── client.ts         # HTTP client, Bearer auth, custom SSE reader
│               └── types.ts          # HealthResponse, ContractSummary types
├── contracts/
│   └── README.md                     # Notes client SDK generation is deferred
├── docs/
│   ├── audit/                        # THIS DIRECTORY (Phase 0 audit output)
│   ├── api/openapi-v1.yaml           # Phase 1 OpenAPI spec (12 endpoints missing)
│   ├── architecture/                 # 12 Mermaid diagrams + ADRs + design docs
│   ├── decisions/                    # 8 Architecture Decision Records
│   ├── operations/                   # Deployment, scaling, runbooks
│   ├── product/                      # Charter, user stories, wireframes
│   ├── releases/                     # Release plan
│   ├── remediation/                  # tracker.md + phase evidence + final report
│   ├── security/                     # Permission matrix, risk register
│   ├── testing/                      # 16 validation reports
│   └── PROJECT_STATUS.md             # Phase ledger and verified checks
├── infra/aws/                        # deploy-commands.sh, IAM template
├── scripts/                          # validate-phase2.ps1, validate-phase14.ps1
├── .github/workflows/
│   ├── ci.yml                        # 3 parallel jobs: backend + frontend + repository
│   └── deploy.yml                    # Sequential: ci → ECR build → SSM deploy
├── docker-compose.yml                # Dev: api + web + postgres + redis
├── docker-compose.production.yml     # Prod: api + web only (RDS/ElastiCache external)
├── .env.example                      # 52 variables (1 duplicate QDRANT_URL)
└── .env.local                        # Local overrides (2122 bytes, NOT auto-loaded)
```

---

## 2. Request Lifecycle (Verified Code Path)

```
[Browser]
  |
  | HTTP POST /api/v1/conversations/{id}/runs
  | Bearer token in Authorization header
  |
[FastAPI app/main.py]
  |
  |-- CorrelationIdMiddleware → X-Request-ID header attached
  |-- CORSMiddleware → origin validated against WEB_ORIGIN setting
  |
[workspace.py → create_run()]
  |
  |-- require_principal() → auth.py
  |     ├── OIDC mode: OIDCAuthenticator.verify(token) → JWKS → PyJWT decode → Principal
  |     └── Dev mode: verify_token(token, settings) → HMAC verify → Principal
  |
  |-- Tenant context resolved from Principal.organization_id + workspace
  |
  |-- Conversation ownership check: db.scalar(select(Conversation).where(id AND org_id AND owner_id))
  |
  |-- Run record created: Run(status="queued") → db.flush()
  |-- Message recorded: Message(role="user", content=prompt)
  |
  |-- Run transitioned: transition_run(db, run, "running")
  |-- RunEvent appended: append_run_event(db, run, "run_started", {})
  |
  |-- Orchestrator.execute(db, AgentRequest)
  |     |
  |     |-- choose_agent(prompt) → regex patterns → agent_id
  |     |-- AgentRegistry.authorize(agent_id, workspace) → workspace check
  |     |
  |     |-- agent.execute(db, request, capability)
  |     |     |
  |     |     |-- [KnowledgeResearchAgent / GeneralAgent / DomainAgent]
  |     |     |     |
  |     |     |     |-- DocumentService.search(db, org_id, user_id, workspace, query)
  |     |     |     |     |-- SQL query: DocumentChunk JOIN Document WHERE org+workspace+status='ready'
  |     |     |     |     |-- In-memory cosine similarity on embedding_json
  |     |     |     |     |-- Returns RetrievalResult(evidence, supported, reason)
  |     |     |     |
  |     |     |     |-- SmartRequestRouter.complete(db, org_id, owner_id, workspace, conv_id, run_id, prompt)
  |     |     |     |     |-- RequestClassifier.classify(prompt) → RouteDecision(kind, cacheable, ...)
  |     |     |     |     |-- ContextSelectionService.select(db, conv_id, prompt, include_history)
  |     |     |     |     |     └── Message history query → assemble or truncate to max_chars
  |     |     |     |     |
  |     |     |     |     |-- Cache check (if cacheable):
  |     |     |     |     |     └── ExactResponseCache.get(db, key) → ResponseCache row or None
  |     |     |     |     |     ⚠️  BUG: key uses org_id="pending" — cross-tenant leak
  |     |     |     |     |
  |     |     |     |     |-- ModelRouter.complete(db, org_id, CompletionRequest, run_id)
  |     |     |     |     |     |-- _enforce_budget() → ModelUsage 24h SUM check
  |     |     |     |     |     |-- Circuit breaker check per provider
  |     |     |     |     |     |-- Provider.complete(model_id, CompletionRequest)
  |     |     |     |     |     |     ├── MockProvider: deterministic string format
  |     |     |     |     |     |     ├── OpenAICompatibleProvider: httpx.post → Groq/HuggingFace
  |     |     |     |     |     |     └── OllamaProvider: httpx.post → localhost:11434
  |     |     |     |     |     |-- _record_usage() → ModelUsage INSERT
  |     |     |     |     |     └── Returns CompletionResult
  |     |     |     |     |
  |     |     |     |     |-- Cache store (if cacheable)
  |     |     |     |     |-- RoutingDecisionLog INSERT
  |     |     |     |     └── Returns (CompletionResult, RouteDecision, SelectedContext, key)
  |     |     |     |
  |     |     |     └── Returns AgentResponse(content, citations, progress)
  |     |     |
  |     |     └── [AnalyticsAgent]
  |     |           └── Regex parse single binary expression → float arithmetic → AgentResponse
  |     |
  |     |-- AgentExecutionMetric INSERT
  |     └── Returns AgentResponse
  |
  |-- Message recorded: Message(role="assistant", content=response.content)
  |-- RunEvent appended: run_completed / run_failed
  |-- Run transitioned: status → "completed" or "failed"
  |
  └── HTTP 202: {id, status, events_url}

[Browser — SSE]
  GET /api/v1/runs/{id}/events
  └── StreamingResponse: db.scalars(RunEvent WHERE run_id ORDER BY sequence)
      → data: {type, payload} events
```

---

## 3. Agent Class Hierarchy

```
BaseAgent (abstract)
├── KnowledgeResearchAgent          ← REAL: RAG search + LLM synthesis
│   ├── GeneralAgent                ← FACADE: clone of KnowledgeResearchAgent
│   └── DomainAgent                 ← FACADE: calls super() + appends disclaimer
│       ├── DataEngineeringAgent    ← FACADE
│       ├── CRMAgent                ← FACADE (declares support.create_ticket, never calls it)
│       ├── CustomerSupportAgent    ← FACADE
│       ├── CustomerSuccessAgent    ← FACADE
│       ├── FinanceAgent            ← FACADE
│       └── CustomerProductAgent    ← FACADE
└── AnalyticsAgent                  ← STUB: regex 2-operand arithmetic only
```

**Workspace permissions** (from AgentRegistry):
- Internal only: `analytics`, `data-engineering`, `crm`, `finance`
- Both: `orchestrator`, `knowledge-research`, `general`, `customer-support`, `customer-success`, `customer-product`

---

## 4. Data Model ERD (Abbreviated)

```
Conversation ──< Message
Conversation ──< Run ──< RunEvent
                Run ──< AgentCheckpoint
                Run ──< ModelUsage
                Run ──< RoutingDecisionLog
                Run ──< ToolExecution
                Run ──< AgentExecutionMetric
                Run ──┤ Approval (optional)
Document ──< DocumentChunk
AuditLog (standalone, org-scoped)
ResponseCache (standalone, org-scoped)
```

---

## 5. Provider Abstractions

| Provider | Class | Transport | Key Needed | Models |
|---|---|---|---|---|
| Mock | `MockProvider` | In-memory | No | `mock-chat` |
| Groq | `OpenAICompatibleProvider` | httpx POST | `GROQ_API_KEY` | `groq-gpt-oss-20b` |
| HuggingFace | `OpenAICompatibleProvider` | httpx POST | `HUGGINGFACE_API_KEY` | `hf-qwen3` |
| Ollama | `OllamaProvider` | httpx POST | No | `ollama-qwen3` (qwen3:8b) |

---

## 6. CI/CD Pipeline

```
ci.yml (triggers: push main, PR, workflow_call)
├── backend (parallel)
│   ├── uv sync --locked
│   ├── ruff check .       ← CURRENTLY FAILS (F401)
│   ├── ruff format --check .
│   ├── pytest             ← blocked by ruff failure in CI
│   └── pip-audit --strict
├── frontend (parallel)
│   ├── npm ci
│   ├── tsc --noEmit
│   ├── eslint .
│   ├── vitest --run
│   ├── vite build
│   └── npm audit --audit-level=high
└── repository (parallel)
    ├── validate-phase2.ps1  (55 checks)
    └── validate-phase14.ps1 (48 checks)

deploy.yml (trigger: workflow_dispatch)
├── verify → calls ci.yml (must all pass)
├── image  → ECR build + push (API + Web Docker images)
└── deploy → AWS SSM Run Command → deploy-commands.sh on EC2
   (Requires: AWS_DEPLOY_ROLE_ARN, AWS_REGION, EC2_INSTANCE_ID, VITE_API_BASE_URL)
```
