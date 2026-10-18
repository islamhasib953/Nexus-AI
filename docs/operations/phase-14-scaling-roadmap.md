# Phase 14 scaling and capacity roadmap

## Current constraint

The approved initial EC2 deployment is a modular monolith with a single instance. It is economical but is a single point of failure and cannot provide a shared in-memory provider circuit, cache, rate limit, or alert evaluator across multiple instances.

## Measured decision path

| Trigger | Change | Safety requirement |
| --- | --- | --- |
| Queue depth/latency grows beyond baseline | move deferred runs and ingestion to a durable worker queue | idempotency keys, bounded retries, dead-letter handling, per-tenant fairness |
| CPU/memory or connection saturation | add stateless API replicas behind an ALB | externalize session/cache/rate state; shared observability |
| SQLite/local state no longer viable | RDS PostgreSQL + managed backup/monitoring | migration/recovery drill and tenant isolation tests |
| retrieval volume/latency rises | managed or clustered Qdrant and asynchronous indexing | preserve metadata filters, version/deletion propagation |
| cost per task rises | adjust registry/routing/cache policy | quality/security evaluation before rollout |

Capacity planning uses the Operations time window: requests/runs, execution duration, queue age, cache hit rate, tokens, costs, tool failures, document chunks, and provider circuit events. Collect a production baseline before committing concurrency, RTO/RPO, or spend commitments. Forecast monthly model cost from tenant/task usage rather than raw request count alone.

Rollouts are incremental: deploy immutable image to a staging/canary target, run migrations forward, run smoke/SSE/authorization checks, observe SLOs, then increase traffic. Roll back application images on regression; use forward migrations or isolated backup recovery for database failures.
