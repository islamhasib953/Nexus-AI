"""phase 8 RAG document lifecycle"""

import sqlalchemy as sa
from alembic import op

revision = "0004_rag_documents"
down_revision = "0003_routing_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("owner_id", sa.String(80), nullable=False),
        sa.Column("workspace", sa.String(20), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("source_uri", sa.String(500)),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="upload"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="ready"),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    for column in (
        "organization_id",
        "owner_id",
        "workspace",
        "content_hash",
        "status",
        "deleted_at",
    ):
        op.create_index(f"ix_documents_{column}", "documents", [column])
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("workspace", sa.String(20), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="ux_document_chunks_document_index"),
    )
    for column in ("document_id", "organization_id", "workspace"):
        op.create_index(f"ix_document_chunks_{column}", "document_chunks", [column])


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_table("documents")
