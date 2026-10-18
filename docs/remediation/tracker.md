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
| C-002 | P1 | analytics | Add safe dataset discovery/query/aggregation workflow with limits | NOT_STARTED | approved data source |
| C-003 | P1 | orchestration | Verify typed state, handoffs, cancellation, recovery, and duplicate protection | IMPLEMENTED | production worker topology |
| D-001 | P1 | MCP/tools | Implement supported remote MCP transport and real compatible integration tests | IMPLEMENTED | approved server/credentials for production verification |
| D-002 | P1 | MCP/tools | Harden output redaction, cancellation, retry and execution budgets | IMPLEMENTED | none |
| E-001 | P1 | RAG | Add configurable real embedding provider and compatibility metadata | IMPLEMENTED | approved free/local embedding runtime for production verification |
| E-002 | P1 | RAG | Improve ingestion, retrieval quality, deletion consistency, and evaluation | NOT_STARTED | embedding/vector runtime |
| F-001 | P1 | security | Replace development auth with a production identity boundary and verify tenant enforcement | IN_PROGRESS | selected OIDC/JWKS identity provider |
| G-001 | P1 | lifecycle | Complete reconnect, duplicate event, cancellation, and recovery verification | VERIFIED | none for local verification |
| H-001 | P2 | frontend | Add end-to-end tests against a running API and remove any fake success states | NOT_STARTED | browser/e2e runtime |
| I-001 | P1 | observability | Add shared telemetry export, alert delivery, and external provider health probes | BLOCKED | AWS/CloudWatch or approved service |
| J-001 | P1 | deployment | Build and verify containers, migrations, rollback, backup/restore in authorized environment | BLOCKED | Docker/AWS/RDS access |
| K-001 | P1 | final verification | Run comprehensive regression/security/performance review and publish readiness report | VERIFIED | production external gates remain blocked |
