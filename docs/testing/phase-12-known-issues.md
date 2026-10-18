# Phase 12 known issues

- Domain agents use bounded framework behavior and free/local defaults; they are not production-ready integrations.
- Remote MCP, real CRM/finance/support providers, PostgreSQL/Redis/Qdrant, and cloud identity are not configured in this workspace.
- The included load script is an in-process smoke benchmark, not a distributed stress test.
- Backup restore and external model cost benchmarks require deployment-like services and credentials.
