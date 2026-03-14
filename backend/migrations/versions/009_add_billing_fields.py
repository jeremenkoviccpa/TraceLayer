"""Add billing fields to companies table.

Revision ID: 009
Revises: 008
Create Date: 2026-03-14
"""

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("plan", sa.String(20), nullable=False, server_default="free"))
    op.add_column("companies", sa.Column("subscription_status", sa.String(50), nullable=True))
    op.add_column("companies", sa.Column("ls_subscription_id", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("ls_customer_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "ls_customer_id")
    op.drop_column("companies", "ls_subscription_id")
    op.drop_column("companies", "subscription_status")
    op.drop_column("companies", "plan")
