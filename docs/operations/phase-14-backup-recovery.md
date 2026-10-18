# Phase 14 backup, restore, and retention procedure

## Backup scope

Production must back up PostgreSQL (conversations, runs, approvals, audit records, usage/agent metrics, and document metadata), vector index snapshots or rebuild inputs, and protected configuration. Secrets are managed in AWS Secrets Manager/SSM and are not copied to application backups.

## Restore drill

1. Record the incident, target recovery point/time, and the source backup identifier.
2. Restore into an isolated PostgreSQL instance; never overwrite the only production database during a drill.
3. Run migrations only forward to the deployed application revision.
4. Validate row counts, an authorized conversation lookup, a run checkpoint, an approval/audit lookup, and tenant-denied retrieval from a second organization.
5. Restore or rebuild Qdrant from the authoritative document records, then validate deletion and authorization filters.
6. Record achieved RPO/RTO and update this runbook. Do not declare the backup strategy proven until this drill has passed in AWS.

## Retention and deletion

The default metrics retention setting is 30 days, subject to the Phase 0 privacy/data-classification decision. A scheduled production cleanup job must delete/aggregate expired operational records in small batches and emit an audit/metric record. Tenant deletion must delete both relational document records and vector entries, invalidate caches, and produce evidence; a legal hold overrides routine deletion. No production deletion job is enabled in the local repository yet.
