# Phase 14 operations API contract

All endpoints are versioned under `/api/v1`, return the common error envelope, and require a signed session with `workspace=internal` and role `internal_member` or `admin`. The server scopes every result to the caller's `organization_id`; query parameters cannot override it.

| Endpoint | Purpose | Sensitive fields excluded |
| --- | --- | --- |
| `GET /operations/overview` | Rolling service, routing, tool, document-index, agent, cost, and provider-circuit snapshot | prompts, response content, authorization tokens, tool request/result payloads, secrets |
| `GET /operations/alerts` | Threshold/SLO alert state derived from the same snapshot | all tenant data other than the caller's own aggregate |

`overview.cost` is an estimated cost calculated from the configured model registry. It is broken down by provider, model, agent, routing-task class, and the authenticated tenant. `by_agent` and `by_task` are present only for usage that can be joined to a recorded agent invocation/routing decision. A provider's `available` value means its local routing circuit is closed; it is not an active Internet reachability or billing-account probe.

The stable metric names are `runs_total`, `runs_failed`, `run_error_rate`, `queue_depth`, `queue_oldest_seconds`, `run_duration_avg_ms`, `tool_calls_total`, `tool_failure_rate`, `cache_hit_rate`, `routing_latency_avg_ms`, and `documents_indexed_chunks`.
