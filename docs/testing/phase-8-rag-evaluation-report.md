# Phase 8 RAG evaluation report

## Automated validation

- Backend: 40 tests passed.
- Coverage: 92.48% (project gate: 90%).
- Ruff lint and format: passed.
- Alembic: downgrade to base and upgrade to `0004_rag_documents`: passed.
- Frontend: typecheck, lint, 2 tests, and production build: passed.

## Covered behavior

- Document ingestion, metadata, deterministic free embeddings, chunking, and indexing.
- Version replacement: only the current `ready` version is searchable.
- Soft deletion removes local chunks and prevents stale retrieval.
- Organization and workspace predicates prevent cross-tenant/cross-workspace retrieval.
- Citations contain document ID, title, chunk ID/index, score, and excerpt.
- Insufficient evidence is explicit and does not become a supported answer.
- Instruction-like retrieved content is flagged as untrusted data.
- Qdrant is optional and failures fall back to the local persisted index.

## Known boundary

The default embedding is a deterministic, free baseline for development and reproducible tests. A production embedding benchmark and live Qdrant deployment require an approved runtime, capacity, and data-classification decision.
