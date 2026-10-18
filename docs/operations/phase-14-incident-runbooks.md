# Phase 14 incident response runbooks

## Severity and ownership

| Severity | Definition | Response |
| --- | --- | --- |
| SEV-1 | tenant isolation/security breach, irreversible unauthorized action, or total outage | stop risky actions, assign incident lead, preserve evidence, notify owner immediately |
| SEV-2 | sustained high error rate, database outage, provider exhaustion without safe fallback | mitigate within the on-call window, communicate status, create post-incident review |
| SEV-3 | one degraded provider, elevated queue, non-critical dashboard/worker issue | investigate in business hours and track corrective work |

## Standard procedure

1. Open the Operations dashboard and correlate the alert with request IDs, deployment revision, and provider circuit state.
2. Establish scope: affected organization(s), request class, model/tool, and time range. Do not place customer content in tickets or chat.
3. Stabilize first: disable a feature flag/tool, stop rollout, apply configured model fallback, or use the tested rollback procedure.
4. Verify recovery through health checks, a synthetic authorized request, and the affected SLI.
5. Preserve relevant audit records/logs, document the timeline, root cause, customer impact, and follow-up owner.

## Specific playbooks

- **Provider circuit open:** confirm provider configuration and budget status; retain free/local fallback; do not enable a paid fallback unless its configured budget and approval policy allow it. If all candidates fail, return a safe failed run rather than fabricated output.
- **Queue/deferred execution delay:** inspect queued and interrupted runs, worker health, database connections, and deployment revision. Do not manually replay a tool action without checking its idempotency key and approval state.
- **Database or vector-store degradation:** stop ingestion/action workloads, validate backup age and connection errors, restore only by the backup runbook, then re-index affected documents and test tenant filters.
- **Suspected data exposure/prompt injection:** halt the affected integration, preserve audit logs, rotate exposed secrets, assess tenant scope, and treat as SEV-1 until proven otherwise.
- **Bad rollout:** stop the rollout and use the immutable-image rollback guide. Never automatically downgrade database migrations; use a forward fix or a tested restore.
