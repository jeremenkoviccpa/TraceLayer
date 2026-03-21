"""Add auto_detected and detection_key to incidents table

Revision ID: 034_auto_incidents
Revises: 033_auto_training_bgcheck
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '034_auto_incidents'
down_revision = '033_auto_training_bgcheck'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('incidents', sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('incidents', sa.Column('detection_key', sa.String(255), nullable=True))
    op.create_index('ix_incidents_detection_key', 'incidents', ['company_id', 'detection_key'])


def downgrade() -> None:
    op.drop_index('ix_incidents_detection_key', table_name='incidents')
    op.drop_column('incidents', 'detection_key')
    op.drop_column('incidents', 'auto_detected')
