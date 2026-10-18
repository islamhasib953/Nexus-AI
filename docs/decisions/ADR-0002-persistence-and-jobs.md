# ADR-0002: Use PostgreSQL as system of record and initial durable job queue

- Status: Accepted
- Date: 2026-10-18

## Decision

Use PostgreSQL for relational business state, audit history, run state references, and a durable `jobs` table. Use Qdrant solely for vector retrieval and Redis only for short-lived cache/rate-limit/coordination use cases. Workers claim PostgreSQL jobs through leases and row locking.

## Alternatives considered

- Redis-only queue: rejected because it adds delivery/recovery configuration and does not replace durable business state.
- Celery/SQS/Kafka from day one: deferred because required delivery semantics and throughput are not yet measured.
- Store all data in Qdrant or document store: rejected; relational authorization/lifecycle/audit relationships need transactional storage.

## Consequences

Job leasing, retry ceilings, dead-letter review, and idempotency metadata are mandatory. Queue extraction is an evidence-based later decision.
