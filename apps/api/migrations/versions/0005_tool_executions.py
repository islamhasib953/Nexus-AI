"""phase 9 tool execution records"""

import sqlalchemy as sa
from alembic import op

revision = "0005_tool_executions"
down_revision = "0004_rag_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("requester_id", sa.String(80), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("tool_id", sa.String(120), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="started"),
        sa.Column("request_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("provider_reference", sa.String(160)),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_code", sa.String(80)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("idempotency_key", name="ux_tool_executions_idempotency_key"),
    )
    for column in (
        "organization_id",
        "requester_id",
        "run_id",
        "tool_id",
        "idempotency_key",
        "status",
    ):
        op.create_index(f"ix_tool_executions_{column}", "tool_executions", [column])


def downgrade() -> None:
    op.drop_table("tool_executions")
