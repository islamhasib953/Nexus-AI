"""phase 10 policy approvals and audit"""

import sqlalchemy as sa
from alembic import op

revision = "0006_policy_approvals_audit"
down_revision = "0005_tool_executions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("approvals") as batch:
        batch.alter_column("run_id", existing_type=sa.String(36), nullable=True)
        batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_approvals_expires_at", "approvals", ["expires_at"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.String(80), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(120)),
        sa.Column("outcome", sa.String(30), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("organization_id", "actor_id", "action", "outcome", "created_at"):
        op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_approvals_expires_at", table_name="approvals")
    with op.batch_alter_table("approvals") as batch:
        batch.drop_column("cancelled_at")
        batch.drop_column("expires_at")
        batch.alter_column("run_id", existing_type=sa.String(36), nullable=False)
