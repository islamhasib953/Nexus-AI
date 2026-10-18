# Phase 0 user stories and acceptance criteria

The following stories are the R1 Foundation backlog. Owners identify the accountable implementation domain, not an individual person.

| ID | User story | Owner | Acceptance criteria |
| --- | --- | --- | --- |
| US-01 | As an authenticated user, I want my organization and workspace resolved securely so I only see resources I am entitled to use. | Identity and Authorization | Server derives identity/tenant/membership; tampered tenant or role input is rejected; cross-tenant API tests fail closed. |
| US-02 | As an internal member, I want to create and resume conversations so I can continue work across sessions. | Conversation Runtime | Authorized user can create/list/read own permitted conversations; message/run state persists; another tenant cannot enumerate or read them. |
| US-03 | As an external customer, I want product help from approved sources so I can solve onboarding and troubleshooting needs safely. | Customer Product Agent | Customer agent sees only allowlisted customer corpus/account services; output includes source citations when retrieval is used; tests demonstrate no internal-data path. |
| US-04 | As an internal member, I want answers grounded in approved company knowledge so I can verify claims. | Knowledge and Research Agent | Ingestion records source/version/access metadata; retrieval filters authorization before model context; every grounded claim displays an actual retrieved citation or states insufficient evidence. |
| US-05 | As a user, I want simple requests handled efficiently so I do not wait or pay for unnecessary processing. | Smart Router | Deterministic greeting/context tests do not invoke retrieval/tools; route decision and reason are recorded; direct/model/retrieval/tool branches have test coverage. |
| US-06 | As an analyst with permission, I want approved read-only data answers so I can inspect current business information without risking data changes. | Analytics Agent | Only approved datasets/views and read-only credentials work; query validation, tenant/data policy, timeout, and resource limits are enforced; calculations/source are shown. |
| US-07 | As an administrator, I want explicit capability policies so I can limit every agent to approved sources and tools. | Policy and Authorization | Deny-by-default registry; unpermitted agent/tool/source call is refused even when requested by UI or model output; decision is audited. |
| US-08 | As an authorized user, I want visible run progress so I know whether a response is generating, retrieving, waiting, completed, or failed. | UX and Runtime | Stable run-status events are streamed; UI/API distinguishes status states; stream payloads contain no secret, internal reasoning, or unauthorized data. |
| US-09 | As a security reviewer, I want activity traceability so I can investigate data access and attempted actions. | Security and Observability | Authorized audit view records actor, tenant, resource, route, agent/tool, outcome, timestamp, and correlation/run ID; sensitive values are redacted. |
| US-10 | As an operator, I want provider failures contained so a transient model failure does not produce silent, unsafe, or duplicate work. | Model Gateway | Provider timeout, bounded retry, fallback eligibility, and clear unavailable response are tested; paid fallback never occurs implicitly. |
| US-11 | As a requester of a future business action, I want proposed actions separated from execution so I retain control over changes. | Policy Engine | R1 has no live mutations; action contract records risk/approval needs and tests reject execution without required policy/approval. |
| US-12 | As an engineer, I want measurable verification so changes do not silently weaken isolation, quality, or cost controls. | Quality Engineering | Unit, integration, authorization, retrieval/citation, route, and provider-failure checks run in CI before a capability is marked complete. |

## Definition of acceptance evidence

An acceptance criterion is satisfied only by a recorded automated test, a reproducible manual verification procedure where automation is impractical, and a link to its implementation/evaluation result. A mock or sandbox is clearly labeled and never accepted as proof that a live integration works.
