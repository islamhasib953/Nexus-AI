"""phase 4 durable state

Revision ID: 0001_phase4_durable_state
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_phase4_durable_state"
down_revision = "0000_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "runs",
        sa.Column(
            "checkpoint_namespace", sa.String(length=120), nullable=False, server_default="default"
        ),
    )
    op.add_column("runs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("runs", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("runs", sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("runs", sa.Column("error_code", sa.String(length=80), nullable=True))
    op.create_index("ux_run_events_run_sequence", "run_events", ["run_id", "sequence"], unique=True)
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("requested_by", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("decided_by", sa.String(length=80), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "agent_checkpoints",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("thread_id", sa.String(length=120), nullable=False),
        sa.Column("namespace", sa.String(length=120), nullable=False, server_default="default"),
        sa.Column("checkpoint_key", sa.String(length=120), nullable=False),
        sa.Column("state_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "thread_id", "namespace", "checkpoint_key", name="ux_checkpoint_thread_namespace_key"
        ),
    )
    for table, column in [
        ("approvals", "run_id"),
        ("approvals", "organization_id"),
        ("approvals", "requested_by"),
        ("approvals", "status"),
        ("agent_checkpoints", "run_id"),
        ("agent_checkpoints", "organization_id"),
        ("agent_checkpoints", "thread_id"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    op.drop_table("agent_checkpoints")
    op.drop_table("approvals")
    op.drop_index("ux_run_events_run_sequence", table_name="run_events")
    for column in [
        "error_code",
        "lease_until",
        "completed_at",
        "started_at",
        "checkpoint_namespace",
        "attempt",
    ]:
        op.drop_column("runs", column)
