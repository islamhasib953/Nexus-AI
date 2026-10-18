# ADR-0007: Use configuration-driven free-first model routing with pre-invocation budgets

- Status: Accepted
- Date: 2026-10-18

## Decision

Nexus-AI uses a common provider adapter interface and a task-specific model registry. The default is an in-process mock model for deterministic local development. Groq, Hugging Face, and Ollama are optional adapters selected by configuration.

Every attempted model is subject to tenant and global daily budget checks before it is invoked. Paid fallback is disabled unless explicitly enabled. A provider failure is bounded by the retry setting and opens a short circuit breaker before the router tries an explicitly configured fallback.

## Alternatives considered

- Allow every agent to select providers directly: rejected because it would duplicate budget, retry, and privacy policy.
- Enable semantic caching immediately: deferred until evaluation proves acceptable quality and isolation.
- Cache current-data and mutation requests: rejected because stale answers and repeated side effects are unsafe.

## Consequences

- Changing a model or fallback policy does not require agent code changes.
- A missing key, timeout, malformed response, or unavailable local runtime fails a run safely.
- Usage records retain token counts and an estimated cost for audit and future billing analysis.
- Actual cloud model quality/cost benchmarks require credentials and must be repeated when provider catalogues change.
