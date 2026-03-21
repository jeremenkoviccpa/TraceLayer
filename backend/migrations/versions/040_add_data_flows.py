"""Add data_flows table for automated data flow mapping and visualization.

Revision ID: 040_add_data_flows
Revises: 039_control_drift_events
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '040_add_data_flows'
down_revision = '039_control_drift_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'data_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('data_category', sa.String(50), nullable=False),
        sa.Column('tool', sa.String(100), nullable=False),
        sa.Column('tool_label', sa.String(255), nullable=False),
        sa.Column('region', sa.String(100), nullable=False, server_default='unknown'),
        sa.Column('risk_level', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('regulations', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('purpose', sa.String(255), nullable=True),
        sa.Column('legal_basis', sa.String(100), nullable=True),
        sa.Column('is_auto_detected', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_cross_border', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_data_flows_company_id', 'data_flows', ['company_id'])
    op.create_index('ix_data_flows_risk_level', 'data_flows', ['risk_level'])
    op.create_index('ix_data_flows_tool', 'data_flows', ['tool'])


def downgrade() -> None:
    op.drop_index('ix_data_flows_tool', table_name='data_flows')
    op.drop_index('ix_data_flows_risk_level', table_name='data_flows')
    op.drop_index('ix_data_flows_company_id', table_name='data_flows')
    op.drop_table('data_flows')
