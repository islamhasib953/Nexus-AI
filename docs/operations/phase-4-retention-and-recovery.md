# Phase 4 — Retention, Checkpoints, and Recovery

## Durable state

Conversations, messages, runs, run events, approvals, and agent checkpoints are stored in the configured relational database. PostgreSQL is the deployment default; SQLite is supported for local development and automated tests.

Run state transitions are validated centrally. A worker lease is assigned when a run enters `running`. On application startup, any previously running run is changed to `interrupted` and receives a durable `run_interrupted` event. A future worker can resume it through the queued state without losing the conversation or checkpoint.

## Retention policy

- Conversation and message history: retained until an organization-level deletion or retention policy is applied.
- Run events: retain with the parent run; archive or delete with the run.
- Agent checkpoints: retain the latest checkpoint per thread and namespace during the active run; clean up checkpoints for terminal runs after 30 days.
- Approvals: retain the decision audit trail for 365 days, subject to the organization’s legal policy.
- Cleanup jobs must filter by `organization_id`, run in batches, and emit deletion metrics.

The cleanup worker is intentionally not enabled in Phase 4. Its SQL and schedule must be approved against customer-specific retention requirements before production activation.
