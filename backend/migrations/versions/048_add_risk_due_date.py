"""Add due_date to risks

Revision ID: 048_add_risk_due_date
Revises: 047_add_gst_number
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "048_add_risk_due_date"
down_revision = "047_add_gst_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("risks", sa.Column("due_date", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("risks", "due_date")
