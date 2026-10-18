# Nexus-AI remediation readiness report

Date: 2026-10-18

## Local result

The repository was re-audited and remediated phase by phase. The local foundation is internally consistent and regression-tested:

- Backend: 66 collected tests, full run passed, coverage reported at 92% against the 90% gate.
- Frontend: TypeScript typecheck passed, ESLint passed, 2 Vitest tests passed, and Vite production build passed.
- Repository validation: Phase 2 validator passed 55 checks; Phase 14 validator passed 48 checks.
- Database: Alembic head is `0009_tenant_scoped_tool_idempotency`; the new migration passed upgrade → downgrade → upgrade.
- Security/lifecycle: tenant ownership, production-auth guard, approval policy, tool redaction, tenant-scoped idempotency, SSE replay, interrupted-run recovery, and duplicate-execution protection are covered locally.

## Implemented in this remediation

- CI dependency/security gates and corrected AWS credential configuration.
- Authoritative model capability metadata, context/structured-output routing checks, and route confidence explanations.
- Explicit bounded-agent status and limitation disclosure.
- SSE replay using `Last-Event-ID` and no duplicate execution on reconnect.
- Opt-in remote MCP JSON-RPC transport with fail-closed validation.
- Configurable OpenAI-compatible embeddings with dimension validation; hash embeddings are development-only.
- Sensitive tool-result redaction and organization-scoped idempotency.
- Application-scoped settings for authentication dependencies; development authentication is unavailable outside development.

## Release decision

**Local release candidate: PASS. Production release: BLOCKED.**

Production cannot be marked ready until all of the following are executed in the authorized target environment:

1. Configure and verify an OIDC/JWKS identity provider and real tenant claims.
2. Run with PostgreSQL, Qdrant, Redis, and the approved embedding runtime.
3. Verify at least one real model provider and one real MCP/business integration, including timeout, retry, approval, and rollback behavior.
4. Build and scan the production containers, run migrations, deploy to AWS, verify network-path SSE, and perform backup/restore.
5. Verify CloudWatch/alert delivery, provider health probes, and load/cost targets against the release gates.

These are external verification gates, not silently skipped tests. Docker and the AWS/provider services are not available in this workspace, so their status remains `UNVERIFIED` or `BLOCKED` in the remediation tracker.
