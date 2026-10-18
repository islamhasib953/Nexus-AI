# Phase 1 architecture diagrams

The files in this directory are editable Mermaid sources. They are the architecture source of truth; rendering is intentionally deferred until a Mermaid renderer is introduced in the repository, so no generated PNG or SVG can become stale.

| File | Purpose |
| --- | --- |
| `01-system-context.mmd` | Users and external systems |
| `02-container-component-architecture.mmd` | Initial modular-monolith boundaries |
| `03-request-routing-flow.mmd` | Minimum-path request decision process |
| `04-conversation-run-lifecycle.mmd` | Run states and recovery transitions |
| `05-agent-orchestration-a2a.mmd` | Restricted agents and deferred A2A boundary |
| `06-mcp-tool-execution.mmd` | Policy-controlled MCP/tool execution |
| `07-rag-ingestion-retrieval-pipeline.mmd` | Secure RAG ingestion and answering |
| `08-approval-action-sequence.mmd` | Future mutating-action lifecycle |
| `09-deployment-architecture.mmd` | Initial deployment topology |
| `10-failure-recovery-fallback-flow.mmd` | Safe failure and recovery paths |
| `11-data-model-erd.mmd` | Initial relational entity relationships |
| `12-observability-operations.mmd` | Tenant-scoped telemetry, alert, and production export boundary |

## Product wireframes

The editable Mermaid wireframes in `docs/product/wireframes/` describe the implemented workspace, conversation/tool states, approval dialog, and internal operations dashboard. They complement the React interface; they are not a substitute for it.

Render only from these sources. A rendered artifact must record the Mermaid CLI/tool version and be regenerated whenever its source changes.
