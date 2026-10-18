# Phase 0 initial scope and release plan

## Prioritization method

Priority is driven by security foundation, customer isolation, and proving the router/RAG architecture with the smallest useful product slice. A capability marked later is not rejected; it is intentionally deferred until its dependencies and business owner are known.

| Priority | Release slice | Included capabilities | Excluded capabilities | Exit evidence |
| --- | --- | --- | --- | --- |
| P0 | R1 Foundation | Identity/tenant boundary, conversation runtime, restricted agent framework, smart routing, internal/customer-separated RAG, model gateway, tool registry, one read-only sandbox integration, observability, tests/docs | Live writes, finance/CRM/support/success/data-engineering agents, live external messaging, production deployment | All R1 user-story acceptance criteria and security tests pass |
| P1 | R1.1 Validated business read access | Owner-approved analytics source and/or first real read-only business integration | Mutations and broad agent portfolio | Data owner approval, integration e2e test, data isolation and cost evidence |
| P2 | R2 Controlled actions | Selected CRM/support workflow with policy engine, approval UI, execution verification, idempotency, audit | Autonomous high-risk actions | Action lifecycle, abuse tests, approver policy, live sandbox verification |
| P3 | R3 Scale and portfolio | Prioritized remaining agents, more tools/providers, A2A only when warranted, resilience/scaling improvements | Unjustified microservices or agents | Measured demand, SLO/capacity evidence, each agent's scoped test suite |

## R1 release plan by implementation phase

| Phase | R1 outcome |
| --- | --- |
| 0 | Charter, scope, acceptance criteria, risks, decisions, traceability |
| 1 | Architecture proposal, ADRs, monorepo/module layout, local technical foundation |
| 2 | Tenant-aware persistence, authentication boundary, RBAC, conversation/run model |
| 3 | Workspace UX/API, streaming contract, run lifecycle |
| 4 | Model gateway, registry, cost/usage telemetry, provider evaluation harness |
| 5 | Smart router and cache policy with route/cost tests |
| 6 | RAG ingestion/retrieval, citations, document lifecycle and authorization tests |
| 7 | Initial restricted agents and capability policies |
| 8–10 | Tool registry/read-only integration, policy/approval foundations, security hardening |
| 12 | End-to-end verification, evaluation, load/security testing, release readiness |

AWS deployment and ongoing operations remain later master-prompt phases and are not R1 Foundation commitments until infrastructure requirements, budget, and security gates are approved.
