# ADR-0008: tenant-scoped operational telemetry from durable records

- Status: accepted
- Date: 2026-10-18

## Decision

The initial release aggregates operational views from existing durable application records, augmented with one `agent_execution_metrics` record per agent attempt. The `/api/v1/operations/*` endpoints require an internal role and always filter by the requester's organization. Provider circuit state is reported as an in-process signal, not as a claim of an external provider health probe.

## Consequences

This provides a real in-product dashboard without introducing a paid telemetry platform or a cross-tenant data store. It is adequate for a single-instance release, but it is not sufficient for multi-instance alerting: Phase 14's production path exports logs/metrics to CloudWatch or an equivalent shared backend and moves alert evaluation out of process.

## Alternatives considered

Prometheus/Grafana or a managed APM service would improve time-series querying and alert delivery, but add infrastructure, retention, credential, and recurring-cost commitments before the AWS environment exists.
