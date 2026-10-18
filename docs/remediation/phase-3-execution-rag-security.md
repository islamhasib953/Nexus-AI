# Remediation Phase 3 — execution, tools, RAG, and security boundaries

Date: 2026-10-18

## Changes

- Added SSE `Last-Event-ID` replay filtering.
- Prevented a completed or already-running run from executing the orchestrator again when a client reconnects.
- Persisted the running status event before yielding it to an SSE consumer.
- Added bounded Analytics parsing: exactly one expression, finite operands, a maximum operand/result magnitude, and explicit division-by-zero failures.
- Added a real opt-in JSON-RPC `tools/call` transport for remote MCP-compatible endpoints with envelope/result validation. It remains unconfigured by default.
- Added configurable OpenAI-compatible embeddings for local or hosted runtimes while retaining deterministic hash embeddings only for development and tests.
- Added production settings guards for development authentication and hash embeddings.
- Scoped tool idempotency to `organization_id` and added migration `0009_tenant_scoped_tool_idempotency`.
- Added sensitive-key redaction before tool results are persisted or returned.
- Made authentication dependencies read the app's injected settings instead of the process-global settings cache.

## Verification

- Ruff format/check passed.
- Backend regression suite passed after the changes.
- Agent, workspace, and durable recovery tests passed, including SSE replay and duplicate-execution protection.
- Tool tests passed, including remote MCP fixture transport, timeout, redaction, tenant-scoped idempotency, schema validation, and provider failure handling.
- RAG tests passed, including embedding-provider normalization, dimension validation, deletion invalidation, citations, and tenant/workspace isolation.
- Security tests passed, including production identity/embedding guards, approval policy, audit behavior, and development-auth isolation.
- Alembic `0009` upgrade → downgrade → upgrade passed on SQLite.

## Explicit limits

The remote MCP endpoint, OIDC/JWKS identity provider, Qdrant service, and real embedding runtime still require an approved external environment. The code fails closed or reports these dependencies as unconfigured; fixture tests are not production connectivity verification. Analytics remains intentionally bounded arithmetic until an authorized dataset/query contract is approved.
