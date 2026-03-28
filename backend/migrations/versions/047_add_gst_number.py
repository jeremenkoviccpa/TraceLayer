"""Add gst_number to companies for GST-compliant invoices

Revision ID: 047_add_gst_number
Revises: 046_training_quiz
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "047_add_gst_number"
down_revision = "046_training_quiz"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("gst_number", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "gst_number")
