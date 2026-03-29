"""Add due_date to manual_controls table for SLA tracking.

Revision ID: 056_add_control_due_date
Revises: 055_add_policy_expiry
Create Date: 2026-03-30
"""
import sqlalchemy as sa
from alembic import op

revision = "056_add_control_due_date"
down_revision = "055_add_policy_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "manual_controls",
        sa.Column("due_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("manual_controls", "due_date")
