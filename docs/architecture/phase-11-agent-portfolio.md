# Phase 11 — agent portfolio and workflow boundaries

Phase 11 adds six bounded domain agents to the shared framework:

| Agent | Allowed workspace | Supported scope | Explicit exclusion |
| --- | --- | --- | --- |
| Data Engineering | internal | pipeline, schema, data-quality reasoning | production data mutation or unapproved queries |
| CRM | internal | CRM guidance and account workflow explanation | cross-tenant customer data |
| Customer Support | internal, customer | troubleshooting and escalation guidance | refunds or policy bypass |
| Customer Success | internal, customer | onboarding and adoption guidance | account permission changes |
| Finance | internal | approved finance policies and metric explanations | payments or external financial disclosure |
| Customer Product | internal, customer | product feature and safe usage guidance | product configuration changes |

Each agent is registered with allowed sources and tools. The orchestrator performs deterministic keyword routing, then the registry authorizes the chosen agent against the caller workspace. Domain agents reuse the authorized RAG boundary and include the same insufficient-evidence behavior as Knowledge/Research. Tool execution remains behind Phase 9 and Phase 10 policy/approval controls; agents do not bypass it.

The implementations are bounded framework agents using the configured model/RAG path. They are not production-ready integrations until real CRM, finance, data platform, and support providers are approved and benchmarked.
