# Phase 8 — RAG and knowledge security

Nexus-AI stores document metadata and chunk evidence in PostgreSQL-compatible persistence. Each chunk is tagged with organization and workspace boundaries. Retrieval applies those predicates before scoring, and deleted documents are soft-deleted plus have their chunks removed from the local index.

The default embedding model is `hash-embedding-v1`, a free deterministic baseline with no external data transfer. It is deliberately replaceable behind `HashEmbeddingModel`. `QdrantVectorStore` mirrors points only when `QDRANT_URL` is configured; local database retrieval remains the safe development fallback.

Retrieved text is treated as untrusted evidence. Instruction-like markers are flagged in chunk metadata and never become system/developer instructions. Knowledge answers include document and chunk citations. If no authorized chunk clears the score threshold, the result reports `insufficient_authorized_evidence` and the agent is instructed not to invent company-specific facts.

Endpoints:

- `POST /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/documents`
- `POST /api/v1/knowledge/search`
- `DELETE /api/v1/knowledge/documents/{document_id}`
