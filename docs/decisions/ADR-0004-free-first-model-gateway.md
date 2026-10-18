# ADR-0004: Use an internal free-first provider gateway

- Status: Accepted
- Date: 2026-10-18

## Decision

Create a lightweight internal provider gateway with task-specific model registry, capability metadata, timeout/retry, health, usage, and explicit fallback rules. Free-tier and local/open-weight candidates are evaluated first; Groq and Hugging Face are candidates. Paid fallback is disabled by default and needs owner approval.

## Alternatives considered

- Direct provider calls from agents: rejected because provider behavior, cost, and fallback would leak across modules.
- Adopt a managed gateway immediately: deferred pending comparison of cost, security, and operational value.
- Pick one free provider permanently: rejected because free availability, limits, capability, licensing, and quality vary.

## Consequences

Phase 4 must benchmark actual candidate models and record their terms/limits before selecting defaults. No documentation may describe a provider as free/unlimited without current verification.
