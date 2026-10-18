# Phase 0 requirements traceability matrix

| Master-prompt concern | R1 requirement / artifact | Verification evidence required later | Target phase |
| --- | --- | --- | --- |
| Separate internal and customer workspaces | FR-01, FR-03; permission matrix | Authentication, authorization, cross-workspace isolation tests | 2–3 |
| Multi-tenant server-side isolation | NFR-01, NFR-02; permission matrix | API/database/vector/cache/job negative tests | 2, 6, 10, 12 |
| Persistent conversations and resumable runs | FR-02, FR-03; US-02/US-08 | Migration, API, run recovery, streaming tests | 2–3 |
| Smart minimal-cost routing | FR-04/FR-05; US-05 | Route decision matrix, latency/token/cost telemetry and tests | 5, 12 |
| Low-cost model strategy and fallback | FR-07; integration inventory | Current provider evaluation and fallback/limit tests | 4, 12 |
| Grounded RAG with citations | FR-06; US-04 | Ingestion/retrieval/citation/version/deletion evaluation | 6, 12 |
| Agent framework with limited capabilities | FR-08/FR-10; agent matrix | Capability policy and unauthorized delegation tests | 7, 10 |
| Read-only validated analytics | FR-09; US-06 | Dataset/query-policy/timeout/resource-limit tests | 7–8 |
| MCP/A2A/tool integration | FR-08; integration inventory | Schema, auth, timeout, tool success/failure tests | 8 |
| Approval and safe external action | FR-11; US-11 | Policy, approval, idempotency, verification, audit tests | 9–10 / R2 for live writes |
| Security, privacy, and reliability | NFR-01–07; risk register | Threat model, scanning, adversarial, recovery evidence | Every phase; 10, 12 |
| Observability, cost, and operations | FR-12; project status | Metrics/traces/dashboards and measured baseline | 4–5, 12–14 |
| Reproducible deployment and documentation | release plan; docs index | CI, infrastructure, deployment/rollback verification | 13–14 |

## Traceability rule

When implementation begins, each requirement above must gain links to its source module, test/evaluation identifier, status, and verification result. A requirement with no evidence remains open.
