"""Add documents table for general file attachments.

Revision ID: 022
Revises: 021
Create Date: 2026-03-15 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploader_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("file_size", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(255), nullable=False, server_default="application/octet-stream"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_documents_company_id", "documents", ["company_id"])
    op.create_index("ix_documents_resource", "documents", ["resource_type", "resource_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_resource", table_name="documents")
    op.drop_index("ix_documents_company_id", table_name="documents")
    op.drop_table("documents")
