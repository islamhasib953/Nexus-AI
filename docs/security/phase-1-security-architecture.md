# Phase 1 security architecture

## Trust boundaries and enforcement

1. **Browser to API:** TLS, secure session/token validation, CSRF strategy appropriate to selected session mode, input size/schema limits, rate limit, and no client-owned authorization facts.
2. **Identity to request context:** FastAPI validates identity claims and resolves active organization/membership/customer account from server records; it does not accept a requested role or tenant as proof.
3. **Application to data stores:** all relational, vector, cache, job, and checkpoint access receives the authorized organization/workspace context. Vector and cache access are subject to the same policy scope as API requests.
4. **Application to models/tools:** only the policy-approved agent capability set is exposed; retrieved/tool content is untrusted data, not instructions or authorization.
5. **Application to operations:** least-privilege credentials, secrets references only, redacted structured telemetry, and audited administrator/operator access.

## Security controls by architecture component

| Component | Required controls |
| --- | --- |
| API | Pydantic validation, authentication, server-side resource authorization, rate limits, safe errors, correlation IDs |
| PostgreSQL | Separate application roles, parameterized queries/ORM, tenant-scoped query methods, migrations, backups, encryption/service controls |
| Qdrant | Server-computed metadata filters, tenant/audience/version fields, deletion propagation, no direct browser access |
| Redis | Scoped opaque keys, TTL, no sensitive content by default, access-limited network placement |
| RAG | Source approval/classification, file validation, prompt-injection-aware handling, authorization before context assembly, citations based on retrieved chunks |
| Model gateway | Data-minimizing prompts, provider allowlist, configured no-paid-default policy, timeout/usage limits, no secrets in prompts/logs |
| Tool registry | Schema validation, allowlisted tool and agent pairing, scoped credentials, timeout, audited outcome, no live R1 mutation |
| Streaming | Run authorization on connect/reconnect, sanitized payloads, no raw tool credentials or private reasoning |
| Jobs | Leases, idempotency key for future writes, cancellation/approval state recheck, dead-letter review after retry ceiling |

## Critical security boundary resolution

R1 has a defined internal/customer isolation rule: customer workspace requests can enter only the Customer-Facing Product Agent capability policy and customer-approved knowledge sources; they have no path to internal agents, internal corpus, analytics, admin APIs, or another customer account. This is tested at API, retrieval metadata, cache-key, agent-capability, and event layers.

Privacy retention, jurisdiction, and legal classification are not guessed. They are open deployment gates documented in Phase 0; therefore real production data ingestion remains blocked until an owner supplies those policies. This is a controlled unresolved product decision, not an unresolved architecture boundary.
