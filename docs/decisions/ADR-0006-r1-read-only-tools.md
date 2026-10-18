# ADR-0006: Restrict R1 integrations to read-only operations

- Status: Accepted
- Date: 2026-10-18

## Decision

R1 may implement a sandbox or approved read-only integration through the tool registry. It will not perform live mutations. The data model/API retains the proposal, approval, reauthorization, idempotency, verification, and audit design for a later release.

## Alternatives considered

- Allow model-directed writes with a confirmation dialog: rejected because confirmation alone does not provide policy/revalidation/idempotency guarantees.
- Omit action architecture: rejected because future mutation needs a controlled foundation.

## Consequences

Any enabled tool is schema-validated, capability-scoped, timed out, and audited. Production write capability requires a new ADR and Phase 9–10 evidence.
