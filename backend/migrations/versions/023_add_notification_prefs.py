"""Add notification_prefs and slack_webhook_url to companies.

Revision ID: 023
Revises: 022
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("notification_prefs", JSONB, nullable=False, server_default="'{}'"))
    op.add_column("companies", sa.Column("slack_webhook_url", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "slack_webhook_url")
    op.drop_column("companies", "notification_prefs")
