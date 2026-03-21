"""Add teams_webhook_url to companies

Revision ID: 036_add_teams_webhook
Revises: 035_add_api_keys
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '036_add_teams_webhook'
down_revision = '035_add_api_keys'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('teams_webhook_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'teams_webhook_url')
