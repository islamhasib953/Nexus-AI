# Phase 0 user and permission matrix

## Core resource rules

| Resource or operation | Platform operator | Org admin | Internal member | External customer |
| --- | --- | --- | --- | --- |
| Own authorized profile/session | Yes | Yes | Yes | Yes |
| Internal workspace | Separate operational access only | Tenant-scoped | Tenant-scoped | No |
| Customer workspace | Separate operational access only | Tenant policy only | No by default | Own customer account only |
| Internal conversations | No implicit access | Tenant policy/audited admin access | Own/shared if explicitly granted | No |
| External conversations | No implicit access | Tenant policy/audited admin access | No by default | Own customer account only |
| Internal knowledge corpus | Only if separately granted | Manage tenant source policy | Allowed sources only | Never |
| Customer-approved corpus | Only if separately granted | Manage tenant source policy | Only if explicitly allowed | Allowlisted sources only |
| Customer account context | No implicit access | Tenant policy/audited access | Only explicitly permitted business role | Own account only |
| Analytics data | No implicit access | Configure approved datasets | Approved data policy only | Never |
| Agent configuration | Platform configuration only | Tenant capability policy | No | No |
| Tool configuration | Platform configuration only | Tenant capability policy | No | No |
| Read-only tool execution | Only if separately granted | According to policy | Explicit agent/user permission | Explicitly allowlisted only |
| Mutating tool execution | Not in R1 | Not in R1 | Not in R1 | Not in R1 |
| Audit events | Operational events only unless separately granted | Tenant audit view | Own events where policy permits | Own events where policy permits |

## Agent capability boundary

| Agent | R1 status | Allowed data/tools | Explicit exclusions |
| --- | --- | --- | --- |
| Orchestrator | Implement | Routing metadata and delegated, allowlisted capability references | Direct unrestricted access to every tool, source, or dataset |
| Knowledge and Research | Implement | Authorized internal corpus, read-only retrieval | Customer account data, mutations, unapproved web/data sources |
| Customer-Facing Product | Implement | Customer-approved corpus; authenticated own-account context only if explicitly connected | Internal corpus, analytics, admin tools, other customers |
| Analytics | Implement, read-only | Approved tenant datasets/views via validated read-only adapter | Writes, arbitrary SQL/data-source access, customer use by default |
| CRM / Support / Success / Finance / Data Engineering | Deferred | No live capability in R1 | All live execution until separately scoped and approved |

## Enforcement points

Authorization must be enforced, with tenant context included where relevant, at API handlers, database query builders/row-level policies, vector metadata filters, cache key creation/lookup, conversation and run access, background work, model context assembly, agent capability lookup, tool registration/execution, file ingestion, streaming event emission, and audit access. Client claims and LLM tool proposals never bypass these checks.
