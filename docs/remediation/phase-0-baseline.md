# Nexus-AI remediation — Phase 0 baseline

Date: 2026-10-18

## Scope

This baseline is an evidence-based reassessment of the existing repository against the Master Remediation, Engineering Completion & Production Readiness prompt. It preserves the existing implementation and treats every claimed capability as a hypothesis until its source code, tests, and runtime boundary support it.

## Repository map

| Area | Current implementation | Baseline status |
| --- | --- | --- |
| Web workspace | React/TypeScript/Vite in `apps/web` | IMPLEMENTED / locally verified |
| API | FastAPI modular monolith in `apps/api` | IMPLEMENTED / locally verified |
| Persistence | SQLAlchemy models, SQLite local mode, PostgreSQL driver, Alembic revisions 0000–0007 | IMPLEMENTED / migration path locally verified |
| Runs/streaming | Run state machine, SSE events, checkpoints, recovery seam | IMPLEMENTED / local tests exist; production worker topology not verified |
| Model gateway | Mock, OpenAI-compatible Groq/Hugging Face adapters, Ollama adapter | IMPLEMENTED locally; live providers unverified |
| Routing/cache | Deterministic classifier and exact tenant-aware cache | IMPLEMENTED; adaptive/semantic routing not complete |
| Agents | Registry, orchestrator, analytics arithmetic, knowledge/domain wrappers | PARTIAL; several advertised agents are bounded knowledge workflows |
| RAG | SQL-backed retrieval, optional Qdrant adapter, deterministic hash embeddings | PARTIAL; production embedding/retrieval quality unverified |
| Tools/MCP | Local MCP-shaped registry, support-ticket adapter, policy/approval/audit path | PARTIAL; remote MCP transport is explicitly unavailable |
| Authentication | Signed development profiles | NOT production-ready; external identity provider is not configured |
| Operations | Tenant-scoped local operations dashboard/API, SLO docs, runbooks | IMPLEMENTED locally; external telemetry/paging unverified |
| Deployment | Docker/AWS/GitHub Actions artifacts | IMPLEMENTED as artifacts; no live deployment verification |

## Confirmed findings

| ID | Priority | Finding | Evidence | Status |
| --- | --- | --- | --- | --- |
| A-001 | P2 | Phase 2 PowerShell validator invokes external `rg` without declaring or checking it | `scripts/validate-phase2.ps1` | CONFIRMED / remediation queued |
| A-002 | P2 | Phase 14 migration has a line exceeding the configured Ruff limit in the inspected source | `apps/api/migrations/versions/0007_agent_execution_metrics.py` | CONFIRMED / remediation queued |
| A-003 | P1 | CI runs the Phase 2 validator but not the Phase 14 validator and has no dedicated security/dependency scan gate | `.github/workflows/ci.yml` | CONFIRMED / remediation queued |
| A-004 | P1 | Deploy job uses AWS SSM without its own AWS credentials configuration | `.github/workflows/deploy.yml` | CONFIRMED / remediation queued |
| B-001 | P1 | Live Groq/Hugging Face/Ollama behavior, quotas, rate limits, and streaming are not verified in this environment | provider adapters and missing credentials/runtimes | BLOCKED external dependency |
| B-002 | P2 | Registry metadata is minimal and does not yet represent all capability/policy dimensions required by the remediation prompt | `app/llm/registry.py`, `app/llm/models.py` | CONFIRMED |
| B-003 | P1 | Request classification is primarily regex/rule based; confidence and model-assisted ambiguity handling are absent | `app/routing/classifier.py` | CONFIRMED |
| B-004 | P2 | Only exact caching is implemented; semantic caching is not implemented/evaluated | `app/routing/cache.py`, routing tests | CONFIRMED |
| C-001 | P1 | Domain agents share a knowledge-research wrapper and do not yet provide real domain data workflows | `app/agents/specialized.py` | CONFIRMED |
| C-002 | P1 | Analytics is limited to one bounded arithmetic expression and has no authorized dataset/query workflow | `app/agents/specialized.py` | CONFIRMED |
| D-001 | P1 | Remote MCP transport is an explicit unconfigured seam | `app/tools/mcp.py` | CONFIRMED / external integration required |
| E-001 | P1 | Hash embeddings are deterministic test/local embeddings, not production semantic embeddings | `app/rag/embeddings.py`, `app/rag/service.py` | CONFIRMED |
| E-002 | P2 | Qdrant is optional and the default retrieval path is SQL-backed in-process scoring | `app/rag/vector_store.py`, `app/rag/service.py` | CONFIRMED |
| I-001 | P0 | Production identity, real AWS services, live integrations, and backup restoration are not available for verification | deployment docs and environment inventory | BLOCKED external dependency |
| I-002 | P2 | Project status contains stale contradictions about implemented capabilities and next phase | `docs/PROJECT_STATUS.md` | CONFIRMED / fixed in Phase 0 |

## Baseline quality evidence

The repository has an existing local verification record for the current implementation: 55 backend tests, frontend typecheck/lint/tests/build, Ruff, migration round-trip, Phase 1/2/3/14 validators, and a local load smoke. The remediation work will rerun affected checks after every change and will not treat those local results as production evidence.

The current environment has no Docker executable, no configured production provider credentials, and no AWS/RDS/Redis/Qdrant/CloudWatch deployment. Those are explicit external blockers, not silently skipped success criteria.

## Phase 0 acceptance

- [x] Repository structure and implementation boundaries inspected.
- [x] Existing documentation claims compared with source boundaries.
- [x] Confirmed findings separated from external blockers.
- [x] Prioritized remediation tracker established.
- [x] Baseline and status contradictions documented.
- [ ] All remediation findings fixed; this belongs to subsequent phases.
