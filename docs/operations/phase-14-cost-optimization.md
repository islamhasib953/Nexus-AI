# Phase 14 cost optimization report

## Implemented measurement

The authenticated operations snapshot reports estimated model spend for the configured time window by tenant, provider, model, agent, and routing-task class. It also reports input/output tokens per agent attempt, cache hit rate, routing latency, tool failures, and queue pressure. Model budget enforcement remains upstream in the model router: configured tenant and global daily USD ceilings are checked before provider invocation, and paid fallback is disabled unless explicitly enabled.

## Initial cost controls

1. Free/local/mock-capable model registry is the default selection policy.
2. Exact tenant/owner/workspace-aware cache avoids repeat simple requests without sharing results across authorization boundaries.
3. Deterministic routing avoids RAG, tools, and delegation when the request does not require them.
4. Agent iteration, token, and time limits bound runaway execution.
5. Provider circuit state and bounded retries avoid repeatedly spending calls against a known failing provider.

## Next measured optimization cycle

Capture production baselines by request class, then compare any proposed model/routing/cache change on answer quality, citation validity, authorization behavior, latency, tokens, and cost per completed task. Do not select a paid fallback or reduce retrieval/agent quality solely from a raw cost chart. Actual cloud-provider invoices and negotiated/free-tier limits remain required to reconcile estimated cost with billed cost.
