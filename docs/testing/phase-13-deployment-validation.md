# Phase 13 deployment validation

- Production API Dockerfile: added non-root user, frozen dependencies, read-only-compatible runtime, and healthcheck.
- Production web Dockerfile: added immutable static build and nginx healthcheck.
- Production compose: added restart policy, localhost-only bindings, health dependencies, and runtime environment injection.
- CI/CD: added manual, OIDC-based ECR build/push and SSM deployment workflow.
- IAM: added pull-only ECR and scoped Secrets Manager policy template.
- Migrations: deployment runs `alembic upgrade head` before restarting services.
- Rollback: immutable previous image tags and explicit rollback script/documentation.
- Smoke checks: liveness/readiness script added.

Production verification status: **blocked pending AWS environment**. AWS credentials, ECR, EC2, RDS, TLS, Secrets Manager, and deployed-network SSE verification were not available in this workspace and are not claimed as passed.
