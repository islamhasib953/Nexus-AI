# Phase 0 integration inventory

No external integration is configured or verified at Phase 0. This inventory describes boundaries and prerequisites only.

| Integration class | R1 disposition | Data/access requirement | Security and acceptance gate |
| --- | --- | --- | --- |
| Identity provider | Required architecture decision; adapter required | OIDC/OAuth/SSO details, organization membership claims, test tenant | Server validates tokens and maps identity server-side; role/tenant spoof tests pass |
| PostgreSQL | Required persistence candidate | Migration owner, backup/recovery design, access roles | Tenant-scoped query policy and migrations tested; no production credentials in repo |
| Redis | Optional R1 cache/runtime candidate | Cache eligibility, TTL/invalidation policy, isolated namespace | Tenant/permission/version-aware keys; sensitive data rules and cache isolation tests |
| Qdrant | Required RAG candidate | Approved document sources, metadata schema, embedding choice | Authorization metadata filter before context assembly; deleted/versioned content test cases |
| LLM/embedding provider | Required abstraction, provider undecided | Account, terms, model capability, region, budget approval | Current pricing/rate limits/licensing/data handling verified before selection; timeout/fallback/usage tests |
| Analytics data source | One sandbox/mock adapter then owner-approved live source | Approved views, data owner, row/column policy, read-only credential | Validated read-only queries, limits/timeouts, no raw arbitrary database access |
| MCP server/client | Registry/interface only unless one approved sandbox is selected | Tool schemas, auth, risk level, required permissions | Input/output validation; tool not exposed without capability policy; e2e evidence for enabled tool |
| CRM, ticketing, email, chat, SMS/WhatsApp | Deferred | Named provider, owner, scopes, retention, consent, approval policy | No live mutation in R1; future action lifecycle requires policy, approval, idempotency, outcome verification, audit |
| AWS | Deployment candidate, not provisioned | Region, account owner, budget, IAM/networking requirements | No production deployment until infrastructure/security/recovery evidence exists |

## Tool registry minimum contract

Every future tool record must contain: stable name and owner; purpose; version; input/output schemas; read/write risk; idempotency; permissions; required approval; timeout/retry; tenant and data constraints; audit fields; provider health; and test evidence. Descriptions and responses from tools are untrusted input.
