# Nexus-AI remediation tracker

This tracker is the source of truth for the remediation program. `IMPLEMENTED` means code exists; `VERIFIED` requires relevant tests and inspection; `PRODUCTION_READY` additionally requires the real external environment where applicable.

| ID | Priority | Workstream | Finding/task | Status | Blocker |
| --- | --- | --- | --- | --- | --- |
| A-001 | P2 | CI/validation | Remove undeclared `rg` dependency from PowerShell validation or fail clearly with prerequisite guidance | VERIFIED | none |
| A-002 | P2 | CI/validation | Format migration 0007 and verify import/apply/rollback | VERIFIED | none |
| A-003 | P1 | CI/validation | Add Phase 14 validation, security/dependency checks, and actionable reports to CI | IMPLEMENTED | GitHub service execution still needs a run |
| A-004 | P1 | deployment | Configure AWS credentials in the deploy job and verify workflow structure | IMPLEMENTED | AWS role/account for live run |
| B-001 | P1 | model gateway | Audit and test provider adapters, normalization, timeout, retry, budget, and availability behavior | IN_PROGRESS | live credentials/runtimes |
| B-002 | P2 | model gateway | Make model registry capability and policy metadata authoritative | VERIFIED | live provider capability verification remains external |
| B-003 | P1 | routing | Add structured confidence/ambiguity and capability-aware adaptive routing | IMPLEMENTED | model-assisted classification and quality benchmark remain |
| B-004 | P2 | routing | Evaluate optional tenant-safe semantic caching against exact-cache baseline | NOT_STARTED | embedding choice/evaluation data |
| C-001 | P1 | agents | Replace or accurately bound domain-agent wrappers with real authorized workflows | IMPLEMENTED | approved business data/integrations |
| C-002 | P1 | analytics | Add safe dataset discovery/query/aggregation workflow with limits | BLOCKED | approved tenant-scoped data source and schema |
| C-003 | P1 | orchestration | Verify typed state, handoffs, cancellation, recovery, and duplicate protection | IMPLEMENTED | production worker topology |
| D-001 | P1 | MCP/tools | Implement supported remote MCP transport and real compatible integration tests | IMPLEMENTED | approved server/credentials for production verification |
| D-002 | P1 | MCP/tools | Harden output redaction, cancellation, retry and execution budgets | IMPLEMENTED | none |
| E-001 | P1 | RAG | Add configurable real embedding provider and compatibility metadata | IMPLEMENTED | approved free/local embedding runtime for production verification |
| E-002 | P1 | RAG | Improve ingestion, retrieval quality, deletion consistency, and evaluation | NOT_STARTED | embedding/vector runtime |
| F-001 | P1 | security | Replace development auth with a production identity boundary and verify tenant enforcement | IMPLEMENTED | live issuer/JWKS availability and tenant-claim verification remain external |
| G-001 | P1 | lifecycle | Complete reconnect, duplicate event, cancellation, and recovery verification | VERIFIED | none for local verification |
| H-001 | P2 | frontend | Add end-to-end tests against a running API and remove any fake success states | NOT_STARTED | browser/e2e runtime |
| I-001 | P1 | observability | Add shared telemetry export, alert delivery, and external provider health probes | BLOCKED | AWS/CloudWatch or approved service |
| J-001 | P1 | deployment | Build and verify containers, migrations, rollback, backup/restore in authorized environment | BLOCKED | Docker/AWS/RDS access |
| K-001 | P1 | final verification | Run comprehensive regression/security/performance review and publish readiness report | VERIFIED | production external gates remain blocked |
| P1-001 | P1 | routing/security | Fix cross-tenant cache key leak by passing organization_id directly to make_key() | VERIFIED | none |
| P1-002 | P1 | CI/validation | Fix Ruff F401 unused sqlalchemy import in migration 0009 unblocking backend CI | VERIFIED | none |
| P1-003 | P2 | configuration | Remove duplicate QDRANT_URL and stabilize DEV_AUTH_SECRET in .env.example | VERIFIED | none |
| P3-001 | P1 | authorization/policy | Enforce role-based tool authorization in PolicyEngine (denies admin tools to unauthorized roles) | VERIFIED | none |
| P3-002 | P1 | audit/security | Expand audit logging to tool executions, document lifecycle, conversations, and run creation | VERIFIED | none |
| P3-003 | P1 | testing/security | Implement comprehensive negative security tests for tokens, cross-tenant isolation, role policies, and audit logging | VERIFIED | none |
| P3-004 | P2 | RAG/reliability | Fix ready_local_index fallback in Document search and listing when vector store is unconfigured | VERIFIED | none |
| P4-001 | P1 | model gateway | Add typed provider exception contract (ProviderAuthenticationError, ProviderRateLimitError, ProviderTimeoutError) | VERIFIED | none |
| P4-002 | P1 | routing | Implement capability-aware routing with Arabic/reasoning/tools signal detection and model selection | VERIFIED | none |
| P4-003 | P1 | model gateway | Formalize zero-budget semantics: 0.0 = unlimited; enforce strictly only when budget > 0.0 | VERIFIED | none |
| P4-004 | P1 | model gateway | Abort retries immediately on ProviderAuthenticationError (HTTP 401/403); never retry auth failures | VERIFIED | none |
| P4-005 | P2 | observability | Track end-to-end provider latency (ms) on all adapters (Groq/HF/Ollama/Mock) via perf_counter | VERIFIED | none |
| P4-006 | P2 | routing/cache | Add invalidate_tenant() API to purge all cached entries for a given organization | VERIFIED | none |
| P4-007 | P1 | model gateway | Verify live Groq provider: gpt-oss-20b (chat) and allam-2-7b (Arabic) respond correctly end-to-end | VERIFIED | none |
