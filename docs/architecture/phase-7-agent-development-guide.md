# Phase 7 — Agent development guide

## Shared contract

Every agent receives `AgentRequest` and returns a validated `AgentResponse`. Responses include an agent id, user-facing content, summary, iteration count, token counts, and progress events. Failures use `AgentFailure` and become durable `run_failed` events; they are never silently returned as successful answers.

## Registry and permissions

`AgentRegistry` is the capability boundary. Each agent declares allowed workspaces, data sources, tools, and maximum iterations. The Orchestrator authorizes the selected agent before execution. Analytics is internal-only in this phase; Knowledge/Research and General are available to both workspaces.

## Current agents

- `general`: direct conversational requests through the Phase 6 smart router.
- `knowledge-research`: document/research-shaped requests through the smart router. Approved document retrieval is classified but connected in Phase 8.
- `analytics`: bounded arithmetic expressions with deterministic validation and no external tool access.
- `orchestrator`: chooses one specialist using deterministic rules and prevents uncontrolled delegation.

## Guardrails

The orchestrator enforces maximum iterations from `AGENT_MAX_ITERATIONS`. The registry prevents unauthorized workspace use. The current implementation delegates at most once per request; future multi-agent plans must add explicit graph edges, deadlines, and budgets before enabling loops.
