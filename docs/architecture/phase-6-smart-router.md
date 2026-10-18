# Phase 6 — Smart routing, context selection, and caching

## Deterministic route classes

`RequestClassifier` uses explicit rules before any model call:

- `direct_model`: short/simple requests; no history, retrieval, or tools.
- `retrieval`: document/policy/knowledge requests; cacheable while the source revision is stable.
- `current_data`: requests containing current/time-sensitive intent; cache bypassed.
- `action`: mutation/tool intent; cache bypassed and marked for the tool layer.

The classifier is intentionally lightweight and deterministic. It does not spend a model call to decide whether another model call is necessary.

## Cache policy

Exact cache keys include organization, owner, workspace, model, route, selected-context fingerprint, and prompt. This prevents cross-tenant and cross-user leakage. Entries have a configurable TTL (`ROUTER_CACHE_TTL_SECONDS`, default 15 minutes), and source revisions can invalidate groups of entries.

Semantic caching is not enabled in Phase 6. It remains an interface/extension point until an evaluation set demonstrates acceptable false-positive and privacy behavior.

## Context policy

Direct requests use no conversation history. Retrieval/action requests select conversation history. When the selected context exceeds `ROUTER_CONTEXT_MAX_CHARS`, the deterministic selector keeps the bounded tail and labels the result as summarized. A model-generated summary can replace this strategy after quality evaluation.

## Instrumentation

`routing_decision_logs` stores route class, cache status, context mode, bypass reason, latency, and token counts. `response_cache` stores exact responses and expiry/source revision metadata. These records provide cache hit rate, bypass rate, latency, and token-use baselines without exposing prompt text in the routing log.
