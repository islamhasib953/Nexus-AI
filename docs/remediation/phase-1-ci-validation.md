# Remediation Phase 1 — CI/CD and repository validation

Date: 2026-10-18

## Changes

- Formatted `apps/api/migrations/versions/0007_agent_execution_metrics.py` to the configured Ruff line length without changing its schema behavior.
- Replaced the undeclared `rg` calls in `scripts/validate-phase2.ps1` with native PowerShell scanning, while excluding dependency/build/cache directories so validation remains bounded.
- Added the Phase 14 repository validator to CI.
- Added high-severity frontend dependency audit and pinned `pip-audit` execution to the backend CI job.
- Added AWS OIDC credential configuration to the deploy job before its SSM call.

## Verification

- `uv run ruff check .`: passed.
- `uv run ruff format --check .`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/validate-phase2.ps1`: passed 55 checks.
- `powershell -ExecutionPolicy Bypass -File scripts/validate-phase14.ps1`: passed 48 checks.
- Alembic downgrade from 0007 to 0006 and upgrade back to 0007: passed.
- `npm audit --audit-level=high`: 0 vulnerabilities reported.
- Workflow changes were inspected statically. A GitHub-hosted CI/deploy run and AWS execution are still external verification steps.

## Remaining limitation

The local runner intermittently leaves Node/uv worker processes when multiple commands are launched concurrently; that is an execution-environment issue and is handled by running checks serially. The repository changes themselves are validated independently. The pinned `pip-audit` command timed out while downloading its tool in the local runner, so its CI execution remains `IMPLEMENTED`, not `VERIFIED`.
