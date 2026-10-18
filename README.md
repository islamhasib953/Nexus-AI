# Nexus-AI

Enterprise multi-agent AI platform foundation. The repository follows the project master prompt and is being delivered phase by phase.

## Current status

- Phase 0: discovery and project charter — complete.
- Phase 1: system architecture and technical design — complete.
- Phase 2: repository, development environment, and engineering foundations — complete.
- Phase 3: frontend workspace and core backend APIs — complete.
- Phase 4: durable execution and persistence for multi-turn agent workflows — complete.
- Phase 5: LLM gateway, model registry, and routing safeguards — complete.
- Phase 6: smart request router, context selection, and caching — complete.
- Phase 7: agent framework and initial specialized agents — complete.
- Phase 8: RAG, document ingestion, and knowledge security — complete.
- Phase 9: MCP-shaped tool integration and controlled action execution — complete.
- Phase 10: policy, approvals, audit, and security hardening — complete.
- Phase 11: bounded domain-agent portfolio — complete.
- Phase 12: local quality/release-readiness verification — complete; production blocked.
- Phase 13: AWS deployment artifacts and CI/CD — complete locally; AWS deployment blocked.
- Phase 14: internal observability, operational runbooks, and scaling roadmap — complete locally; shared production telemetry is blocked on AWS provisioning.

External providers, production data, live business mutations, and AWS resources are not configured in this workspace.

## Repository layout

```text
apps/
├── api/       # FastAPI modular-monolith backend and worker boundary
└── web/       # React + TypeScript workspace
contracts/     # Shared API contracts
docs/          # Product, architecture, security, testing, and operations records
scripts/       # Repeatable validation and developer tooling
infra/         # Development and future deployment configuration
```

## Local setup

Prerequisites: Node.js 22+, npm 11+, and uv. Docker Desktop is optional for the Phase 2 skeleton but required to start the Compose PostgreSQL/Redis services. Python is installed and managed by uv for the API environment.

1. Copy `.env.example` to `.env` and keep credentials empty unless you explicitly configure a provider.
2. Install and lock backend dependencies with `uv sync --directory apps/api`.
3. Install frontend dependencies with `npm ci --prefix apps/web`.
4. Start the API with `uv run --directory apps/api uvicorn app.main:app --reload`.
5. Start the web workspace with `npm run dev --prefix apps/web`.
6. Open `http://localhost:5173`; the workspace calls the API health endpoint and displays its status.

Alternatively, after installing Docker Desktop, run `docker compose up --build` from the repository root.

## Validation commands

```powershell
uv run --directory apps/api pytest
uv run --directory apps/api ruff check .
uv run --directory apps/api ruff format --check .
npm run typecheck --prefix apps/web
npm run lint --prefix apps/web
npm run test --prefix apps/web -- --run
npm run build --prefix apps/web
powershell -ExecutionPolicy Bypass -File scripts/validate-phase2.ps1
```

The backend and frontend communicate through the versioned contract in `docs/api/openapi-v1.yaml`; the running skeleton exposes `/api/v1/health/live`, `/api/v1/health/ready`, and `/api/v1/contract`.

## Safety defaults

The Phase 2 application has no live external tools, no production database credentials, no mutating actions, and a `mock` model-provider setting. Paid providers are never selected implicitly.
