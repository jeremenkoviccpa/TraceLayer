"""Add policy_signatures and slack_configs tables.

Revision ID: 044_employee_portal_slack
Revises: 043_add_gap_features
Create Date: 2026-03-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '044_employee_portal_slack'
down_revision = '043_add_gap_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Policy Signatures ─────────────────────────────────────────────────────
    op.create_table(
        'policy_signatures',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('policy_id', 'user_id', name='uq_policy_signatures_policy_user'),
    )
    op.create_index('ix_policy_signatures_user_id', 'policy_signatures', ['user_id'])
    op.create_index('ix_policy_signatures_company_id', 'policy_signatures', ['company_id'])

    # ── Slack Configs ─────────────────────────────────────────────────────────
    op.create_table(
        'slack_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('webhook_url', sa.String(512), nullable=False),
        sa.Column('channel_name', sa.String(100), nullable=True),
        sa.Column('reminder_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('slack_configs')
    op.drop_index('ix_policy_signatures_company_id', table_name='policy_signatures')
    op.drop_index('ix_policy_signatures_user_id', table_name='policy_signatures')
    op.drop_table('policy_signatures')
