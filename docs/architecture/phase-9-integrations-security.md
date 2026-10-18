# Phase 9 — MCP, A2A, integrations, and action execution

The application uses a local MCP-shaped server boundary for the first release. The server exposes only tools authorized for the principal's workspace and role, validates required fields against a registered schema, and executes adapters behind a service boundary. `RemoteMCPClient` is a transport seam for a future remote MCP server and remains disabled unless configured.

The representative integration is `support.create_ticket`, implemented by a deterministic local adapter that can later be replaced by Jira, Linear, or a CRM adapter without changing the API or agent contract. Mutating operations have explicit `draft` and `execute` modes. Execute results must pass provider verification before being reported as completed.

Tool execution records include tenant, requester, run, tool, idempotency key, status, attempts, request/result payloads, provider reference, and error code. Reusing an idempotency key returns the original result and prevents duplicate execution. Tool access is checked server-side, so model-generated or client-supplied tool IDs cannot bypass the registry.

`A2ATask` defines a bounded handoff contract with a maximum hop count. Approval workflows remain a Phase 10 concern; Phase 9 exposes explicit draft mode so no implicit final action is performed.
