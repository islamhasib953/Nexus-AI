# Phase 10 — policy, approval, and security hardening

`PolicyEngine` classifies actions as low, medium, high, or critical and decides whether an action is allowed and whether human approval is required. The tool service evaluates the policy again immediately before execution. An approval is bound to the exact action type and JSON payload, has an expiration time, and is single-state (`pending`, `approved`, `cancelled`); materially different arguments cannot reuse it.

Approval APIs are tenant-scoped and internal approvers are required for approval decisions. Every request, approval, cancellation, and execution is written to `audit_logs`. SQLite timezone values are normalized to UTC before expiration comparisons. The workspace exposes pending approvals for internal users with approve/cancel controls.

Security tests cover customer attempts to initiate restricted actions, non-internal approval attempts, prompt-injection evidence handling inherited from Phase 8, tool authorization inherited from Phase 9, and exact approval payload binding. Uploaded content remains bounded by the ingestion API and tool schemas validate required fields before adapters run.

Production release remains blocked until CI secret scanning, dependency vulnerability scanning, retention windows, and real identity/provider credentials are configured.
