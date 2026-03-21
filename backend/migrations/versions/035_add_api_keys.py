"""Add api_keys table for CI/CD evidence ingestion

Revision ID: 035_add_api_keys
Revises: 034_auto_incidents
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '035_add_api_keys'
down_revision = '034_auto_incidents'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(16), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_index('ix_api_keys_company_id', 'api_keys', ['company_id'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_company_id', table_name='api_keys')
    op.drop_table('api_keys')
