"""Add partner onboarding nudge sent flags to users table.

Revision ID: 028
Revises: 027
"""
import sqlalchemy as sa
from alembic import op

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("partner_nudge_day1_sent", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("partner_nudge_day3_sent", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("partner_nudge_day7_sent", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("users", "partner_nudge_day7_sent")
    op.drop_column("users", "partner_nudge_day3_sent")
    op.drop_column("users", "partner_nudge_day1_sent")
