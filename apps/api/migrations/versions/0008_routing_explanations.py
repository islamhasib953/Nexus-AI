"""phase 2 routing confidence and explanations"""

import sqlalchemy as sa
from alembic import op

revision = "0008_routing_explanations"
down_revision = "0007_agent_execution_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("routing_decision_logs") as batch:
        batch.add_column(sa.Column("confidence", sa.Float(), nullable=False, server_default="0"))
        batch.add_column(
            sa.Column("explanation", sa.String(length=240), nullable=False, server_default="")
        )


def downgrade() -> None:
    with op.batch_alter_table("routing_decision_logs") as batch:
        batch.drop_column("explanation")
        batch.drop_column("confidence")
