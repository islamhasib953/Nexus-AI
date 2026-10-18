# Phase 13 — AWS deployment and operations

## Release flow

1. GitHub Actions runs backend/frontend/repository gates.
2. A manually approved workflow assumes an AWS OIDC role.
3. API and web images are built with an immutable git-SHA tag and pushed to ECR.
4. SSM runs the deployment on the EC2 instance: pull images, run `alembic upgrade head`, start compose, and verify readiness.
5. The smoke script verifies liveness/readiness and the deployed SSE route is verified separately through the public HTTPS endpoint.

No AWS keys are stored in the repository. Runtime settings come from Secrets Manager/SSM or the host's protected `.env.production`; secrets are not copied into image layers.

## Network and data

Use private subnets for EC2 and RDS, an HTTPS ALB or hardened reverse proxy, and security groups with least-privilege ingress. Enable RDS encryption, automated backups, and a tested restore procedure. CloudWatch collects container logs and host metrics; add distributed tracing when the external runtime is selected.

## Rollback and recovery

Keep the previous immutable image tags. `scripts/rollback-production.sh` restores them and verifies readiness. Never downgrade a database migration automatically; restore from a tested backup or ship a forward migration. If a migration fails, stop rollout, preserve logs, and follow the manual recovery runbook.

## Current release gate

The deployment artifacts are ready and locally lintable, but a production deployment is blocked until an AWS account, OIDC role, ECR repositories, secret ARN, VPC/subnets, RDS endpoint, TLS certificate, and EC2 instance are provisioned and smoke-tested.
