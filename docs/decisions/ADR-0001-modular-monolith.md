# ADR-0001: Start as a modular monolith

- Status: Accepted
- Date: 2026-10-18

## Context

R1 needs secure tenant isolation, routing, retrieval, agents, tools, streaming, and background ingestion, but has no measured independent scaling or team-ownership requirement for separate services.

## Decision

Build one FastAPI codebase with explicit modules and run API and worker as separate roles from the same versioned image. External boundaries use interfaces/contracts rather than network calls inside the application.

## Alternatives considered

- Deploy every logical component as a microservice: rejected for R1 due to operational cost, latency, distributed authorization/tracing complexity, and no evidence of need.
- Single unstructured application: rejected because it prevents safe capability boundaries and future extraction.

## Consequences

Module ownership and contracts are required. A module may become a separate service only when measured scale, reliability, credential boundary, or ownership needs justify it.
