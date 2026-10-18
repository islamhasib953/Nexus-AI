# Phase 12 release-readiness checklist

## Gates

- [x] Backend unit/API/integration suite passes with coverage above 90%.
- [x] Frontend typecheck, lint, tests, and production build pass.
- [x] Migration downgrade/upgrade passes through the current head.
- [x] Agent routing evaluation cases pass.
- [x] Tenant isolation, authorization bypass, prompt-injection, and approval tests pass.
- [x] Tool timeout handling is bounded and tested.
- [x] Interrupted-run recovery tests from Phase 4 remain green.
- [x] Local load smoke baseline is reproducible.
- [x] Rollback criteria and known limitations are documented.
- [ ] Production PostgreSQL/Redis/Qdrant load test.
- [ ] Backup restoration test against production-like PostgreSQL.
- [ ] External provider latency/cost benchmark with approved credentials.
- [ ] CI secret scanning and dependency vulnerability scan configured.

## Release decision

The local release gates pass. Production release is **blocked** until the unchecked infrastructure and security gates are completed; they are not silently treated as passing.

Rollback if migration fails, p95 latency breaches the agreed SLO for two consecutive runs, tenant isolation fails, an approval can be reused after payload modification, or any critical dependency/security scan issue is found.
