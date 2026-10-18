# Phase 14 — Observability, SLIs, SLOs, and alert policy

## What is implemented locally

The internal workspace exposes an Operations view backed by authenticated APIs. It aggregates the last configurable window (default 24 hours) from durable runs, routing decisions, model usage, tool executions, document chunks, and agent attempts. JSON logs continue to carry a correlation/request ID. The editable [operations diagram](../architecture/12-observability-operations.mmd) and [dashboard wireframe](../product/wireframes/04-admin-observability-dashboard.mmd) describe the intended production topology and user experience.

Data stays organization-scoped at query time. Customer users cannot call the operations endpoints; an internal user cannot request another organization's aggregate. Dashboard/API output deliberately omits prompts, messages, tool payloads/results, provider keys, and private model reasoning.

## Initial SLIs and release objectives

These are operational objectives to measure against, not unverified production guarantees.

| SLI | Source | Initial objective | Alert/review policy |
| --- | --- | --- | --- |
| Run error rate | durable run status | <= 5% per rolling window | critical above configured threshold |
| Tool failure rate | tool execution status | <= 5% | critical above configured threshold |
| Queue depth | queued runs | below 10 for the single-instance baseline | warning at configured threshold |
| Provider circuit state | model router bounded-retry circuit | no sustained open circuit | warning for each open provider circuit |
| Cache hit rate | routing decision logs | measure before setting a target | weekly trend review |
| Routing latency | routing decision logs | measure by request class | weekly trend review |
| End-to-end run duration | run timestamps | measure by request class | investigate sustained regression |
| Cost per task | model usage joined to agent/run | measure before committing a budget | daily tenant/global budget guards remain enforced |
| Retrieval index volume | document chunks | capacity signal only | scale/re-index review before thresholds |

The alert API evaluates thresholds synchronously for the initial single-instance release. Production alert delivery, paging, and deduplication must be configured in CloudWatch (or an approved shared telemetry service) before claiming 24/7 coverage.

## Configuration and retention

`OBSERVABILITY_ENABLED`, `METRICS_WINDOW_HOURS`, `METRICS_RETENTION_DAYS`, `OPS_QUEUE_WARNING_THRESHOLD`, `OPS_ERROR_RATE_CRITICAL_THRESHOLD`, and `OPS_TOOL_FAILURE_CRITICAL_THRESHOLD` are typed settings and documented in `.env.example`. Setting `OBSERVABILITY_ENABLED=false` returns a safe 404 from these internal endpoints. Metrics are currently reconstructed from the durable business records rather than copied into a second raw-data store. The retention job design is documented below; it is intentionally not auto-scheduled until the production worker/scheduler is provisioned so data is not silently deleted.

## Production telemetry backlog

1. Export structured application logs, host/container metrics, and request traces to CloudWatch with a shared dashboard.
2. Configure database, Qdrant, Redis, ALB, and worker queue metrics with environment-specific alarms.
3. Add alert destinations, ownership, escalation rules, and tested paging.
4. Add an authenticated health probe for each configured external provider; never use the routing-circuit value as a substitute for an end-to-end probe.
5. Run the defined retention/archival task after legal retention and tenant deletion commitments are approved.
