"""scope tool idempotency keys to the owning organization"""

from alembic import op

revision = "0009_tenant_scoped_tool_idempotency"
down_revision = "0008_routing_explanations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tool_executions") as batch:
        batch.drop_constraint("ux_tool_executions_idempotency_key", type_="unique")
        batch.create_unique_constraint(
            "ux_tool_executions_org_idempotency", ["organization_id", "idempotency_key"]
        )


def downgrade() -> None:
    with op.batch_alter_table("tool_executions") as batch:
        batch.drop_constraint("ux_tool_executions_org_idempotency", type_="unique")
        batch.create_unique_constraint("ux_tool_executions_idempotency_key", ["idempotency_key"])
