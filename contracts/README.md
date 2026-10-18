# Shared contracts

The initial API contract is maintained in [`docs/api/openapi-v1.yaml`](../docs/api/openapi-v1.yaml). The FastAPI application exposes it at `/openapi.json` and exposes a small stable summary at `/api/v1/contract` for the frontend foundation.

Generated clients are intentionally deferred until the resource schemas stabilize. Frontend types in `apps/web/src/api/types.ts` are limited to the Phase 2 health and contract responses.
