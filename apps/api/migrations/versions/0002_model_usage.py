"""model usage accounting

Revision ID: 0002_model_usage
Revises: 0001_phase4_durable_state
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_model_usage"
down_revision = "0001_phase4_durable_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_usage",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=80), nullable=False),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model_id", sa.String(length=160), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.String(length=32), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_usage_org_created", "model_usage", ["organization_id", "created_at"])
    op.create_index("ix_model_usage_run_id", "model_usage", ["run_id"])
    op.create_index("ix_model_usage_provider", "model_usage", ["provider"])
    op.create_index("ix_model_usage_model_id", "model_usage", ["model_id"])


def downgrade() -> None:
    op.drop_table("model_usage")
