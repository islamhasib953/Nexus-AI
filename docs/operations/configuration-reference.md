# Nexus-AI — Configuration Reference

**Version:** 0.1.0  
**Last Updated:** 2026-10-19 (Phase 2)  
**Configuration Loader:** `pydantic-settings` via `app.core.config.Settings`  

---

## 1. Overview & Loading Order

The application loads configuration in the following order (later sources override earlier ones):

1. Default field values defined in `Settings`
2. `REPO_ROOT/.env`
3. `apps/api/.env`
4. `REPO_ROOT/.env.local` (Local developer overrides — Git-ignored)
5. `apps/api/.env.local` (Local developer overrides — Git-ignored)
6. System environment variables (highest priority)

Case sensitivity is disabled (`case_sensitive=False`), meaning `MODEL_PROVIDER` and `model_provider` are treated identically.

---

## 2. Complete Environment Variables Specification

| Variable | Type | Default | Required? | Secret? | Consumer Component | Validation & Notes |
|---|---|---|---|---|---|---|
| `APP_ENV` | `str` | `"development"` | No | No | Core, Auth | `"development"`, `"staging"`, or `"production"`. When set to `"production"`, activates strict security boundaries. |
| `APP_NAME` | `str` | `"nexus-ai-api"` | No | No | FastAPI, Logging | Application identifier for telemetry and headers. |
| `APP_VERSION` | `str` | `"0.1.0"` | No | No | Contract, Health | Semver string exposed in `/api/v1/health/live`. |
| `LOG_LEVEL` | `str` | `"INFO"` | No | No | Logging | `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`. |
| `API_HOST` | `str` | `"0.0.0.0"` | No | No | Server | Host binding address. |
| `API_PORT` | `int` | `8000` | No | No | Server | Port number (`1 <= api_port <= 65535`). |
| `WEB_ORIGIN` | `AnyHttpUrl` | `"http://localhost:5173"` | No | No | CORS Middleware | Allowed origin for frontend requests. |
| `IDENTITY_PROVIDER` | `str` | `"development"` | Conditional | No | Auth | `"development"` or `"oidc"`. Must not be `"development"` in production. |
| `IDENTITY_ISSUER_URL` | `str` | `""` | Conditional | No | OIDC Authenticator | Required if `IDENTITY_PROVIDER=oidc` or in production. |
| `IDENTITY_AUDIENCE` | `str` | `""` | Conditional | No | OIDC Authenticator | Required if `IDENTITY_PROVIDER=oidc` or in production. |
| `IDENTITY_JWKS_URL` | `str` | `""` | Conditional | No | OIDC Authenticator | Required if `IDENTITY_PROVIDER=oidc` or in production. |
| `IDENTITY_ALGORITHMS` | `str` | `"RS256"` | No | No | OIDC Authenticator | Comma-separated list of allowed JWT algorithms. |
| `DATABASE_URL` | `str` | `"sqlite:///./data/nexus.db"` | No | No | Persistence | SQLAlchemy connection URL (SQLite or PostgreSQL). |
| `REDIS_URL` | `str` | `"redis://localhost:6379/0"` | No | No | Future Queue/Cache | Optional; not actively bound to core execution in R1. |
| `MODEL_PROVIDER` | `str` | `"mock"` | No | No | LLM Gateway | Supported: `"mock"`, `"groq"`, `"huggingface"`, `"ollama"`. Validated at startup. |
| `MODEL_NAME` | `str` | `"mock-chat"` | No | No | LLM Gateway | General model descriptor. |
| `LLM_PRIMARY_MODEL_ID` | `str` | `"mock-chat"` | No | No | Model Router | Primary model ID. Options: `"mock-chat"`, `"groq-llama-3.3-70b"`, `"groq-llama-3.1-8b"`, `"hf-qwen3"`, `"ollama-qwen3"`. |
| `LLM_FALLBACK_MODEL_IDS` | `str` | `""` | No | No | Model Router | Comma-separated fallback model IDs. |
| `LLM_TIMEOUT_SECONDS` | `float` | `20.0` | No | No | Provider Adapters | Request timeout in seconds (`0 < x <= 120`). |
| `LLM_MAX_RETRIES` | `int` | `1` | No | No | Model Router | Maximum retries on provider failure (`0 <= x <= 3`). |
| `LLM_TENANT_DAILY_BUDGET_USD` | `float` | `0.0` | No | No | Budget Guard | Daily USD budget per tenant (`>= 0`). `0` disables budget enforcement. |
| `LLM_GLOBAL_DAILY_BUDGET_USD` | `float` | `0.0` | No | No | Budget Guard | Global daily USD budget (`>= 0`). `0` disables budget enforcement. |
| `LLM_ALLOW_PAID_FALLBACK` | `bool` | `False` | No | No | Model Router | Whether to allow automatic fallback to paid providers. |
| `ROUTER_CACHE_TTL_SECONDS` | `int` | `900` | No | No | Smart Router | Cache time-to-live in seconds (`0 <= x <= 86400`). |
| `ROUTER_CONTEXT_MAX_CHARS` | `int` | `12000` | No | No | Context Selector | Max character length for conversation history (`1000 <= x <= 100000`). |
| `ROUTER_CACHE_ENABLED` | `bool` | `True` | No | No | Smart Router | Enables/disables exact-match response cache. |
| `AGENT_MAX_ITERATIONS` | `int` | `3` | No | No | Orchestrator | Maximum iterations allowed per agent (`1 <= x <= 10`). |
| `AGENT_MAX_TOKENS` | `int` | `2048` | No | No | Agent Exec | Output token limit for agents (`128 <= x <= 16000`). |
| `AGENT_TIMEOUT_SECONDS` | `float` | `30.0` | No | No | Agent Exec | Timeout per agent execution (`0 < x <= 300`). |
| `GROQ_API_KEY` | `str` | `""` | Conditional | **YES** | Groq Provider | Required when `MODEL_PROVIDER="groq"`. Validated at startup. |
| `GROQ_BASE_URL` | `str` | `"https://api.groq.com/openai/v1"` | No | No | Groq Provider | Groq OpenAI-compatible API base URL. |
| `HUGGINGFACE_API_KEY` | `str` | `""` | Conditional | **YES** | HuggingFace Provider | Required when `MODEL_PROVIDER="huggingface"`. Validated at startup. |
| `HUGGINGFACE_BASE_URL` | `str` | `"https://router.huggingface.co/v1"` | No | No | HuggingFace Provider | HuggingFace router API base URL. |
| `OLLAMA_BASE_URL` | `str` | `"http://localhost:11434"` | No | No | Ollama Provider | Local Ollama instance URL. |
| `QDRANT_URL` | `str` | `""` | No | No | Vector Store | Qdrant endpoint. Empty string disables Qdrant integration. |
| `QDRANT_COLLECTION` | `str` | `"nexus_chunks"` | No | No | Vector Store | Qdrant collection name. |
| `MCP_REMOTE_URL` | `str` | `""` | No | No | MCP Client | Remote MCP server URL. Empty string disables remote MCP. |
| `TOOL_RATE_LIMIT_PER_MINUTE` | `int` | `30` | No | No | Tool Service | Rate limit per user per tool (`1 <= x <= 1000`). |
| `RAG_CHUNK_SIZE` | `int` | `900` | No | No | RAG Chunking | Character size per document chunk (`200 <= x <= 4000`). |
| `RAG_DEFAULT_TOP_K` | `int` | `5` | No | No | RAG Search | Default number of retrieval chunks (`1 <= x <= 20`). |
| `RAG_MIN_SCORE` | `float` | `0.12` | No | No | RAG Search | Minimum similarity threshold (`-1 <= x <= 1`). |
| `EMBEDDING_PROVIDER` | `str` | `"hash"` | Conditional | No | RAG Embeddings | `"hash"` or `"openai-compatible"`. Cannot be `"hash"` in production. |
| `EMBEDDING_MODEL_ID` | `str` | `"hash-embedding-v1"` | No | No | RAG Embeddings | Identifier of embedding model. |
| `EMBEDDING_BASE_URL` | `str` | `""` | Conditional | No | RAG Embeddings | Required when `EMBEDDING_PROVIDER != "hash"`. |
| `EMBEDDING_API_KEY` | `str` | `""` | No | **YES** | RAG Embeddings | API key for external embedding provider. |
| `EMBEDDING_DIMENSIONS` | `int` | `128` | No | No | RAG Embeddings | Vector dimensions (`8 <= x <= 4096`). |
| `OBSERVABILITY_ENABLED` | `bool` | `True` | No | No | Operations API | Enables `/api/v1/operations/*` endpoints. |
| `METRICS_WINDOW_HOURS` | `int` | `24` | No | No | Operations | Sliding window for operational metrics (`1 <= x <= 720`). |
| `OPS_QUEUE_WARNING_THRESHOLD` | `int` | `10` | No | No | Operations Alerts | Queue depth threshold for warning alert. |
| `OPS_ERROR_RATE_CRITICAL_THRESHOLD` | `float` | `0.05` | No | No | Operations Alerts | Run error rate (5%) for critical alert. |
| `OPS_TOOL_FAILURE_CRITICAL_THRESHOLD` | `float` | `0.05` | No | No | Operations Alerts | Tool failure rate (5%) for critical alert. |
| `METRICS_RETENTION_DAYS` | `int` | `30` | No | No | Operations | Days to retain operational metrics. |
| `DEV_AUTH_ENABLED` | `bool` | `True` | Conditional | No | Dev Auth | Must be `False` in production. |
| `DEV_AUTH_SECRET` | `str` | `"development-only-not-for-production"` | No | **YES** | Dev Auth | HMAC secret for dev tokens. Must be changed in shared environments. |

---

## 3. Production Boundaries Validation

The application enforces the following rules at startup via Pydantic model validation:

1. **Production Guardrails** (`APP_ENV=production`):
   - `DEV_AUTH_ENABLED` must be `False`.
   - `IDENTITY_PROVIDER` must not be `"development"`.
   - `IDENTITY_ISSUER_URL`, `IDENTITY_AUDIENCE`, and `IDENTITY_JWKS_URL` must all be non-empty.
   - `EMBEDDING_PROVIDER` must not be `"hash"`.
2. **Provider Credential Validation**:
   - If `MODEL_PROVIDER="groq"`, `GROQ_API_KEY` must be non-empty.
   - If `MODEL_PROVIDER="huggingface"`, `HUGGINGFACE_API_KEY` must be non-empty.
   - If `EMBEDDING_PROVIDER != "hash"`, `EMBEDDING_BASE_URL` must be non-empty.
3. **Supported Model Providers**:
   - Must be one of: `mock`, `groq`, `huggingface`, `ollama`.
