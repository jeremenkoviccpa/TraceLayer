"""add owner_user_id to manual_controls

Revision ID: 014
Revises: 013
Create Date: 2026-03-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'manual_controls',
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_manual_controls_owner_user_id',
        'manual_controls', 'users',
        ['owner_user_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_manual_controls_owner_user_id', 'manual_controls', type_='foreignkey')
    op.drop_column('manual_controls', 'owner_user_id')
