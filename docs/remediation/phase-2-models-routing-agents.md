# Remediation Phase 2 — models, routing, and agent boundaries

Date: 2026-10-18

## Changes

- Expanded `ModelSpec` with authoritative capability metadata: streaming, tools, multimodal support, API-key requirement, named capabilities, and validated context/cost invariants.
- Added duplicate-ID validation and provider lookup to `ModelRegistry`.
- Added pre-inference context-window and structured-output capability checks so an unsuitable model is skipped before provider invocation.
- Added confidence and human-readable explanation fields to route decisions and durable routing logs.
- Added explicit ambiguous-signal handling for action requests that also contain current-data or retrieval signals.
- Added model/route regression tests and migration `0008_routing_explanations` with a successful round trip.
- Exposed agent implementation status and required integrations through `/api/v1/agents`.
- Made domain-agent responses explicitly state that their current output is limited to authorized conversation/document knowledge when external integrations are absent.

## Verification

- Ruff format/check passed after the changes.
- LLM gateway tests: 10/10 passed, including context fallback, structured capability validation, duplicate registry protection, and provider parsing.
- Smart router tests: 7/7 passed, including confidence, ambiguity explanation, cache behavior, and durable decision logging.
- Agent tests: 7/7 passed, including bounded implementation metadata and limitation disclosure.
- Migration `0008` upgrade → downgrade → upgrade passed.

## Explicit limits

The providers still require their real credentials/runtimes for live verification. Adaptive classification currently uses explainable deterministic signals and confidence; a model-assisted classifier is not enabled by default and still requires an evaluation dataset before adding its latency/cost.
