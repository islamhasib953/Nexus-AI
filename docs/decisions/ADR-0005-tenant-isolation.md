# ADR-0005: Enforce tenant isolation in every data path

- Status: Accepted
- Date: 2026-10-18

## Decision

Derive tenant/workspace/customer-account context from authenticated server records and enforce it at API, relational query, vector filter, cache key, checkpoint, job, tool, streaming, and audit boundaries. Use deny-by-default agent/tool/source capability policy.

## Alternatives considered

- Trust client-supplied tenant or role identifiers: rejected as unsafe.
- Isolate only at API route level: rejected because retrieval, cache, workers, and tools would remain exposure paths.
- One database per tenant immediately: deferred; it creates operational overhead without current contractual isolation demand.

## Consequences

Cross-tenant negative tests are required from Phase 2 onward. Customer workspace has a distinct capability policy and cannot inherit internal permissions.
