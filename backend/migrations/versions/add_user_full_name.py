"""add user full_name

Revision ID: a1b2c3d4e5f6
Revises: 012
Create Date: 2025-03-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'full_name')
