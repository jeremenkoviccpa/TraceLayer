"""Add expires_at and expiry_notified_at to policies table.

Revision ID: 055_add_policy_expiry
Revises: 054_company_primary_frameworks
Create Date: 2026-03-30
"""
import sqlalchemy as sa
from alembic import op

revision = "055_add_policy_expiry"
down_revision = "054_company_primary_frameworks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "policies",
        sa.Column("expiry_notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("policies", "expiry_notified_at")
    op.drop_column("policies", "expires_at")
