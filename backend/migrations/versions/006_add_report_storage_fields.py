"""Add storage metadata fields to reports.

Revision ID: 006_add_report_storage_fields
Revises: 005_seed_iso27001_hipaa_controls
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("storage_bucket", sa.String(length=128), nullable=True))
    op.add_column("reports", sa.Column("storage_path", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("file_name", sa.String(length=256), nullable=True))
    op.add_column("reports", sa.Column("mime_type", sa.String(length=128), nullable=True))
    op.add_column("reports", sa.Column("file_size", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "file_size")
    op.drop_column("reports", "mime_type")
    op.drop_column("reports", "file_name")
    op.drop_column("reports", "storage_path")
    op.drop_column("reports", "storage_bucket")
