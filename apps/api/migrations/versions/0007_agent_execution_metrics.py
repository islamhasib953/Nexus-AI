"""phase 14 agent execution operational metrics"""

import sqlalchemy as sa
from alembic import op

revision = "0007_agent_execution_metrics"
down_revision = "0006_policy_approvals_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_execution_metrics",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("agent_id", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_agent_execution_metrics_organization_id", "agent_execution_metrics", ["organization_id"]
    )
    op.create_index("ix_agent_execution_metrics_run_id", "agent_execution_metrics", ["run_id"])
    op.create_index("ix_agent_execution_metrics_agent_id", "agent_execution_metrics", ["agent_id"])
    op.create_index("ix_agent_execution_metrics_status", "agent_execution_metrics", ["status"])
    op.create_index(
        "ix_agent_execution_metrics_org_created",
        "agent_execution_metrics",
        ["organization_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("agent_execution_metrics")
