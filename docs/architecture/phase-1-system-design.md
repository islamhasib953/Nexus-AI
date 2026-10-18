# Phase 1 system architecture and technical design

## Decision summary

R1 is a **modular monolith** deployed as a web/API application and a separate worker role from the same codebase/image. React/TypeScript is the browser workspace; FastAPI is the API and streaming boundary; LangGraph runs stateful agent workflows; PostgreSQL is durable system-of-record storage; Qdrant is the retrieval index; Redis is optional ephemeral cache/rate-limit coordination. The application owns authorization, policy, routing, and provider abstraction. These are logical modules, not independently deployed microservices.

The architecture preserves future split points without paying microservice overhead before real load, ownership, or isolation needs exist.

## Module boundaries

| Module | Owns | May depend on | Must not do |
| --- | --- | --- | --- |
| Web workspace | Role-aware UI, HTTP requests, SSE rendering | Public API contracts only | Enforce authorization or construct trusted tenant context |
| API and request context | Token validation, tenant/membership resolution, input validation, API errors | Identity adapter, policy, application services | Trust client resource/role/tenant claims |
| Conversation and run service | Conversations, messages, run lifecycle, event persistence, cancellation | PostgreSQL, event publisher | Call providers/tools directly |
| Smart router | Minimal execution-path decision and route telemetry | Context service, cache policy, model classifier, policy | Authorize requests or bypass policy |
| Policy engine | Resource/capability/action decisions; approval rules | Request context, registries | Execute tools or infer authority from LLM output |
| Agent runtime | Typed LangGraph state/checkpoints, delegated restricted agent steps | Router, policy, retrieval/tool/provider interfaces | Access an unregistered tool/source |
| Retrieval service | Ingestion/query abstraction, citations, document lifecycle | PostgreSQL, Qdrant, provider embedding interface | Return chunks before authorization filter |
| Tool service | Tool registry, schema checks, scoped execution, result validation | Policy, integration adapters | Execute unapproved/mutating R1 actions |
| Model provider gateway | Provider capabilities, task model selection, limits, usage, health, fallback | Provider adapters, configuration | Hide paid fallback or make policy decisions |
| Job service/worker | Durable ingestion and retriable background jobs | PostgreSQL, retrieval/integration interfaces | Blindly retry non-idempotent actions |
| Observability | Structured metrics/traces/audit correlation | Every module via neutral interface | Store secrets or unrestricted sensitive content by default |

## Request and state lifecycle

1. The browser sends a message only with its session credential and untrusted request parameters.
2. FastAPI validates the request, authenticates it, and constructs `RequestContext` from server-side identity/membership records.
3. The conversation service confirms access to the requested conversation, creates a durable `Run` and initial `RunEvent`, then streams status through SSE.
4. The router selects the minimum eligible route. It may return a cache result, direct model response, authorized RAG response, or a policy-checked restricted agent/tool workflow.
5. Every model, retrieval, tool, and agent step emits a sanitized event. Long-lived state is checkpointed; business records stay in PostgreSQL.
6. The result is validated, citations and usage are persisted, a terminal run event is published, and the browser receives the final SSE event.

Cancellation is cooperative: a cancellation flag is durable, streaming stops promptly, workers check the flag between steps, and no new tool/action starts after cancellation. A completed external action is never represented as cancelled.

## Sync and async split

| Work | Execution | Reason |
| --- | --- | --- |
| Authentication, authorization, creating a run, route decision, short answer streaming | API request process | User needs immediate response and SSE updates |
| Direct model/RAG answer | Request process with bounded timeout; resumable state | Keeps interaction responsive while allowing transparent failure |
| Document extraction, chunking, embedding, reindexing | Durable job and worker | Potentially long/retriable work must survive request disconnects |
| Large analytics/report generation | Durable job when it exceeds interactive limit | Prevents request exhaustion; exposes run progress |
| Future mutating integration action | Durable stateful workflow after approval | Requires exact approval, idempotency, outcome verification, and audit |

R1 queue design is a PostgreSQL `jobs` table with leases, attempt counters, scheduled retry time, and `FOR UPDATE SKIP LOCKED` claiming. It reuses the required database and avoids introducing a queue broker prematurely. Redis, Celery, SQS, or another queue is a future replacement only after measured throughput/delivery requirements justify it.

## Model strategy

The gateway exposes typed operations such as `classify`, `chat`, `structured_output`, `embed`, and `rerank`. Provider adapters expose capabilities, model identifiers, context limits, rate-limit/health status, and usage. Configuration chooses a free-tier or local/open-weight candidate first; Groq and Hugging Face are candidates, not a production guarantee. The gateway must never select a paid fallback unless an explicit configuration and budget approval enable it.

## Future scaling path

1. Scale API replicas behind a load balancer while retaining PostgreSQL/Qdrant/Redis as shared services and using SSE-compatible ingress.
2. Scale worker replicas independently based on durable job queue depth and ingestion demand.
3. Move retrieval, tool adapters, or provider gateway behind internal APIs only when their independent throughput, ownership, fault isolation, or credentials boundary warrants it.
4. Introduce a managed queue only when PostgreSQL job-claiming cannot meet measured delivery/throughput requirements.
5. Introduce A2A network services only for independently deployed agents; R1 agents stay modules with versioned internal contracts.

No scaling step removes server-side authorization or changes tenant isolation responsibilities.
