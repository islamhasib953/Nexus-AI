# Phase 5 model evaluation report

Date: 2026-10-18

Automated validation: 25 API tests passed with 91.78% coverage; frontend typecheck, lint, 2 tests, and production build passed; Ruff, Alembic downgrade/upgrade, repository validation, and `git diff --check` passed.

## Verified result

`mock-chat` is the verified end-to-end inference path: a conversation request reaches the gateway, returns a response through SSE, completes the run, persists the assistant message, and writes model usage. This is intentionally deterministic and has no cloud cost.

A live Uvicorn smoke test also passed: the API exposed 4 registry models, served a `mock-chat` completion, emitted `run_completed`, and shut down cleanly.

## Adapter verification

| Adapter | Result | Scope |
| --- | --- | --- |
| Mock | PASS | Full API/SSE/usage path |
| Groq | PASS | Adapter request/response parsing with mocked HTTP transport; no credential supplied |
| Hugging Face | PASS | OpenAI-compatible adapter contract shared with the Groq test; no credential supplied |
| Ollama | PASS | Local chat request/response parsing with mocked HTTP transport; no local daemon assumed |

## Safety evaluation

- Unconfigured cloud provider: PASS — safe `ProviderUnavailableError`.
- Configured fallback after provider failure: PASS.
- Tenant budget pre-invocation block: PASS.
- Required structured fields: PASS — malformed JSON fails safely.
- Paid fallback guard: implemented in router policy; no paid registry entry is enabled by default.

The dataset in `phase-5-model-evaluation-dataset.json` is the baseline for later live benchmarks. Real Groq, Hugging Face, and local-model scores are intentionally recorded as pending because the repository contains no credentials or running local model service.
