"""smart router cache and decision logs

Revision ID: 0003_routing_cache
Revises: 0002_model_usage
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_routing_cache"
down_revision = "0002_model_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "response_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("owner_id", sa.String(80), nullable=False),
        sa.Column("workspace", sa.String(20), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(160), nullable=False),
        sa.Column("route_kind", sa.String(40), nullable=False),
        sa.Column("source_revision", sa.String(120), nullable=False, server_default="static"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "routing_decision_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("owner_id", sa.String(80), nullable=False),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("route_kind", sa.String(40), nullable=False),
        sa.Column("cache_status", sa.String(20), nullable=False),
        sa.Column("context_mode", sa.String(30), nullable=False),
        sa.Column("bypass_reason", sa.String(120), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for table, column in [
        ("response_cache", "organization_id"),
        ("response_cache", "owner_id"),
        ("response_cache", "workspace"),
        ("response_cache", "cache_key"),
        ("response_cache", "expires_at"),
        ("routing_decision_logs", "organization_id"),
        ("routing_decision_logs", "owner_id"),
        ("routing_decision_logs", "run_id"),
        ("routing_decision_logs", "route_kind"),
        ("routing_decision_logs", "cache_status"),
    ]:
        op.create_index(f"ix_{table}_{column}", table, [column])


def downgrade() -> None:
    op.drop_table("routing_decision_logs")
    op.drop_table("response_cache")
