"""Add SSO configuration tables

Revision ID: 031_add_sso
Revises: 030_compliance_docs
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '031_add_sso'
down_revision = '030_compliance_docs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sso_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('issuer', sa.String(500), nullable=False),
        sa.Column('client_id', sa.String(500), nullable=False),
        sa.Column('client_secret_enc', sa.Text(), nullable=False),
        sa.Column('scopes', sa.String(200), nullable=False, server_default='openid email profile'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id'),
        sa.UniqueConstraint('domain'),
    )
    op.create_index('ix_sso_configs_domain', 'sso_configs', ['domain'])

    op.create_table(
        'sso_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('sso_states')
    op.drop_index('ix_sso_configs_domain', table_name='sso_configs')
    op.drop_table('sso_configs')
