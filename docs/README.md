# Project documentation

This directory is the durable engineering record for Nexus-AI. The project is governed by the Enterprise Multi-Agent AI Platform master prompt supplied by the project owner.

## Current status

- Active phase: **Phase 7 — Agent Framework and Initial Specialized Agents**
- Release under definition: **R1 Foundation**
- Production integrations: **none verified or configured**
- Next gate: approve the Phase 0 open decisions, then produce the Phase 1 architecture proposal.

## Phase 0 artifacts

- [Project charter and PRD](product/phase-0-project-charter.md)
- [User stories and acceptance criteria](product/phase-0-user-stories.md)
- [Permission matrix](security/phase-0-permission-matrix.md)
- [Integration inventory](architecture/phase-0-integration-inventory.md)
- [Risk register](security/phase-0-risk-register.md)
- [Release plan and prioritization](releases/phase-0-release-plan.md)
- [Requirements traceability matrix](product/phase-0-traceability.md)
- [Project status](PROJECT_STATUS.md)

## Phase 1 architecture artifacts

- [System design](architecture/phase-1-system-design.md)
- [Editable Mermaid diagrams](architecture/README.md)
- [Initial database schema](architecture/phase-1-data-model.md)
- [API and event contract](api/phase-1-api-contract.md)
- [Security architecture](security/phase-1-security-architecture.md)
- [Deployment and scaling plan](operations/phase-1-deployment-and-scaling.md)
- [Architecture decisions](decisions/)
- [Phase 1 validation report](testing/phase-1-validation-report.md)
- [Phase 2 validation report](testing/phase-2-validation-report.md)
- [Phase 3 validation report](testing/phase-3-validation-report.md)
- [Phase 4 retention and recovery policy](operations/phase-4-retention-and-recovery.md)
- [Phase 4 validation report](testing/phase-4-validation-report.md)
- [Phase 5 model gateway design](architecture/phase-5-model-gateway.md)
- [Phase 5 model evaluation report](testing/phase-5-model-evaluation-report.md)
- [Phase 6 smart router design](architecture/phase-6-smart-router.md)
- [Phase 6 routing evaluation report](testing/phase-6-routing-evaluation-report.md)
- [Regression report for Phases 1–7](testing/regression-phases-1-to-6.md)
- [Phase 7 agent development guide](architecture/phase-7-agent-development-guide.md)
- [Phase 7 agent evaluation report](testing/phase-7-agent-evaluation-report.md)

Phase 1 can be checked locally with `powershell -ExecutionPolicy Bypass -File scripts/validate-phase1.ps1`. The validator has no third-party dependency; a real Mermaid renderer and generated image artifacts remain optional tooling.

All implementation phases must update the status file, preserve these security boundaries, and link verification evidence before a capability is called complete.
