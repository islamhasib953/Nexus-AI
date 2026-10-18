# Phase 0 project charter and product requirements document

## 1. Purpose

Nexus-AI is a secure, multi-tenant enterprise AI platform. It gives internal employees and authenticated external customers a unified conversational interface for approved knowledge, data, and business workflows. The platform selects the least costly safe execution path—conversation context, cache, direct model inference, retrieval, data query, tool, or specialized agent—rather than treating every message as an agentic workflow.

This charter defines the R1 Foundation scope. It translates the master prompt into testable requirements; it does not claim that any product capability is implemented.

## 2. Business objectives and measurable outcomes

| Objective | R1 outcome | Measurement at release-readiness |
| --- | --- | --- |
| Safe enterprise access | Employees and customers access only their authorized workspace, data, and actions | Tenant-isolation and authorization test suites pass for every R1 route and retrieval path |
| Useful knowledge assistance | Users receive grounded answers from approved content | Citation validity and answer-quality evaluation baselines are measured and published before release |
| Cost-aware execution | Simple requests do not incur unnecessary retrieval, tools, or multi-agent work | Router decision telemetry shows the selected path, latency, tokens, and cost for every test scenario |
| Auditable operations | Material execution is inspectable | Run, tool, approval, and security audit events are persisted and queryable by authorized operators |
| Extensible delivery | New agents and tools can be introduced without breaking security boundaries | A documented registry interface and one representative integration pass automated integration tests |

Numeric SLOs, per-task cost ceilings, concurrency, retention period, and quality thresholds are intentionally **TBD**. They must be benchmarked and approved in later phases; inventing them now would create false commitments.

## 3. Product scope

### R1 Foundation: in scope

- Two separately authorized experiences: Internal Workspace and Customer Workspace.
- Authentication integration abstraction, organization/tenant membership, roles, server-side authorization, and audit identity context.
- Persistent conversations, messages, runs, status events, cancellation, and resumable run state.
- A Smart Request Router with deterministic handling for greetings/context-only requests, cache eligibility, direct LLM, retrieval, and approved read-only tools.
- Agent framework with a restricted Orchestrator, Knowledge and Research Agent, Customer-Facing Product Agent, and Analytics Agent in read-only mode.
- Internal knowledge RAG and separately indexed customer-approved knowledge RAG, both carrying tenant, source, version, and access metadata with verifiable citations.
- Model-provider abstraction, task/model registry, usage accounting, bounded retry/timeout behavior, and explicit fallback policy.
- Tool registry and one **read-only** representative integration adapter, initially using a sandbox or mock until an owner provides credentials and approval.
- Streamed run status and response output without exposing secrets, internal reasoning, or unauthorized data.
- Automated unit, API/integration, authorization, tenant-isolation, and basic evaluation tests; documentation and local development setup.

### Explicitly out of R1 scope

- Live production writes to CRM, ticketing, finance, email, Slack, SMS, WhatsApp, deployment platforms, or databases.
- Finance, Data Engineering, CRM, Customer Support, and Customer Success agents beyond framework stubs or later prioritized increments.
- Autonomous irreversible actions, unapproved external actions, and paid-provider usage without explicit configuration and budget authorization.
- Multi-region/high-availability operation, independently deployed A2A services, and production AWS deployment. Architecture must leave a path for them, but no claim of deployment is permitted.
- Customer access to internal documentation, internal agents, internal analytics, or administrative operations.

## 4. Users, journeys, and tenant boundaries

| Persona | Primary journey | Boundary |
| --- | --- | --- |
| Internal member | Sign in, open/resume a conversation, ask a knowledge or approved analytics question, inspect citations and run status | May access only tenant-authorized internal data and agents permitted by role |
| Internal administrator | Manage organization membership, roles, agent/tool enablement, approved sources, and audit access | Administrative privilege is tenant-scoped and never inferred from the client |
| External customer | Sign in, use the Customer-Facing Product Agent for approved product documentation and, if enabled, their own account context | Can never access internal workspace, non-public documents, another customer account, admin tools, or internal prompts |
| Platform operator | Operate configured environments, investigate health and audit data | No automatic access to tenant content; operational access must be separately authorized and audited |

Tenant context is derived on the server from the authenticated identity and membership. A client-provided tenant, role, conversation, run, customer-account, cache key, document filter, or tool identifier is input to validate—not authorization evidence.

## 5. Initial roles and permissions

The authoritative initial matrix is [phase-0-permission-matrix.md](../security/phase-0-permission-matrix.md). The minimum roles are: `platform_operator`, `org_admin`, `internal_member`, and `external_customer`. R1 uses deny-by-default capability policies; an agent receives only an explicit list of permitted retrieval sources and tools.

## 6. Functional requirements

| ID | Requirement |
| --- | --- |
| FR-01 | Authenticate users and resolve tenant, membership, role, workspace, and customer-account context server-side. |
| FR-02 | Persist and authorize conversations, messages, runs, run events, citations, tool executions, approvals, and audit events. |
| FR-03 | Provide a workspace UI/API to create, resume, list, and cancel authorized conversations/runs and display streamed status. |
| FR-04 | Route requests through the minimum justified path, recording the selected path and reason category. |
| FR-05 | Support exact-cache eligibility and safe conversation-context reuse with authorization-aware keys; semantic cache is deferred until its equivalence and security policy are validated. |
| FR-06 | Retrieve only authorized, current, versioned documents and return citations linked to actual retrieved sources. |
| FR-07 | Use model and provider abstractions with task routing, timeout, bounded retry, health state, usage, and explicit fallback. |
| FR-08 | Register tools with schemas, owning integration, permissions, risk, timeout, retry, idempotency, and audit policy; reject unauthorized calls. |
| FR-09 | Provide read-only Analytics queries only through approved datasets, query validation, limits, timeouts, and read-only credentials. |
| FR-10 | Treat tool output, retrieved content, document content, and model output as untrusted until validated by the receiving boundary. |
| FR-11 | Enforce policy checks and an auditable proposal/approval lifecycle before any later mutating action. R1 exposes no live mutation. |
| FR-12 | Emit structured observability data for request/routing, model usage, retrieval, tools, errors, and security-sensitive events. |

## 7. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-01 | Tenant isolation is enforced in database, vector retrieval, caches, conversation state, jobs, tools, logs, and APIs. |
| NFR-02 | Authorization is rechecked server-side when a run, retrieval, tool call, or future approved action executes. |
| NFR-03 | Secrets are injected through typed environment configuration/secret management and never committed, displayed, or logged. |
| NFR-04 | All external calls use bounded timeout/retry behavior; mutating work in later releases must be idempotent or duplicate-safe. |
| NFR-05 | Data-retention, deletion, residency, and privacy requirements remain deployment-blocking decisions until an owner supplies them. |
| NFR-06 | The system is modular but starts as a deployable modular monolith unless Phase 1 evidence justifies separate services. |
| NFR-07 | Every release capability has automated acceptance evidence; absent evidence is an incomplete capability, not a pass. |

## 8. Initial data sources, permissions, and deployment assumptions

### Data sources

R1 data is limited to an owner-approved internal knowledge corpus and a separately approved customer-facing product corpus. Live analytic datasets may be connected only after their owner defines the approved views, row/column policy, freshness expectation, and read-only credential. No source is operational merely because an adapter exists.

### Deployment and budget assumptions

- Development starts locally using containers and non-production data.
- The intended first deployment path is a Dockerized modular monolith on one AWS EC2 instance with managed PostgreSQL considered separately, consistent with the master prompt. This is an architectural assumption, not a deployment commitment.
- Budget is a hard external constraint: use free-tier or locally runnable/open-weight model candidates first, including providers such as Groq or Hugging Face when they satisfy the task and current service limits. Use usage caps and explicit fallbacks. No paid model/provider may be activated silently or without owner approval.
- A single instance is not high availability. Availability/recovery targets, region, managed-service selection, and monthly budget ceiling are unresolved release gates.

## 9. Assumptions and owner decisions

| ID | Assumption or decision needed | Impact | Owner input required before |
| --- | --- | --- | --- |
| OD-01 | Initial organization/tenant and pilot users | Identity, authorization, test fixtures | Phase 1 implementation |
| OD-02 | Authentication provider and SSO requirement | Identity architecture and data model | Phase 1 implementation |
| OD-03 | Initial internal/customer document sources, owners, classification, and retention | RAG ingestion and external isolation | Phase 3/RAG implementation |
| OD-04 | Initial approved analytics dataset and data owner | Analytics integration | Analytics implementation |
| OD-05 | First real integration to prioritize after sandbox validation | Tool adapter and acceptance tests | Integration implementation |
| OD-06 | Deployment region, monthly budget ceiling, and paid-service approval process. Owner preference is free-first; paid services are fallback-only and require approval. | Provider/infrastructure selection | Any paid or production commitment |
| OD-07 | Privacy, regulatory, residency, retention, and deletion obligations | Security architecture and release eligibility | Before storing production data |
| OD-08 | Languages required for UI, knowledge base, and agents (Arabic/English assumed as a possible need, not committed) | Model/embedding evaluation | Model/RAG selection |

## 10. Phase 0 acceptance decision

Phase 0 is complete when the linked deliverables exist, every R1 capability has a defined scope and measurable acceptance criterion, external-customer isolation and data ownership are explicit, and unresolved material decisions are visible. It does **not** authorize provider spending, production deployment, live integrations, or application construction until the relevant subsequent phase contract is approved.
