# Phase 0 risk register

| ID | Risk | Likelihood | Impact | Mitigation / control | Owner domain | Release gate |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | Cross-tenant or internal-to-customer data exposure | Medium | Critical | Server-derived identity, deny-by-default policies, metadata filtering, isolated cache keys, negative tests | Security | Blocks any external-customer release |
| R-02 | Prompt injection in documents, tool output, or user messages causes data/tool misuse | High | Critical | Treat content as untrusted, constrain agents/tools, validate schemas, policy checks, adversarial tests | AI Security | Blocks enabled tool/retrieval release if critical bypass remains |
| R-03 | Model provider cost/rate limit/availability assumptions are wrong | High | High | Provider abstraction, budget caps, measured evaluation, explicit fallback/queue behavior, no silent paid fallback | Model Platform | Blocks provider default selection |
| R-04 | RAG gives stale, ungrounded, or unauthorized answers | Medium | High | Source/version/access metadata, deletion/reindex lifecycle, citation validation, evaluation set | Retrieval | Blocks knowledge claim of production readiness |
| R-05 | Unbounded analytics query causes data leakage or resource exhaustion | Medium | High | Approved views, read-only credentials, policy validation, row/column constraints, query time/resource limits | Data Platform | Blocks analytics enablement |
| R-06 | Ambiguous customer-data and privacy obligations | Medium | Critical | Obtain data classification, retention/deletion/residency/legal requirements before production data | Product/Security owner | Blocks production data ingestion |
| R-07 | Autonomous or duplicate external action | Medium | Critical | R1 read-only; later proposal→policy→approval→execute→verify→audit lifecycle and idempotency | Governance | Blocks all mutations |
| R-08 | Single-instance deployment causes outage/data loss | Medium | High | Document limitation; backups, restore verification, monitoring, and scaling roadmap before production | Operations | Blocks availability claims |
| R-09 | Scope expands to every agent/integration before foundation is secure | High | High | R1 scope boundary, phase gates, feature flags, prioritized backlog | Product/Engineering | Reviewed every phase |
| R-10 | Secrets or sensitive content enter source, logs, prompts, or streams | Medium | Critical | Secret management, redaction, scanning, least privilege, stream contract review | Security/Operations | Blocks release on confirmed exposure |

Risk ratings are preliminary. Phase 1 threat modeling must refine likelihood, controls, evidence, and residual risk.
