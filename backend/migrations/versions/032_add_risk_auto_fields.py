"""Add auto_detected and detection_key to risks table

Revision ID: 032_add_risk_auto_fields
Revises: 031_add_sso
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '032_add_risk_auto_fields'
down_revision = '031_add_sso'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('risks', sa.Column('auto_detected', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('risks', sa.Column('detection_key', sa.String(255), nullable=True))
    op.create_index('ix_risks_detection_key', 'risks', ['company_id', 'detection_key'])


def downgrade() -> None:
    op.drop_index('ix_risks_detection_key', table_name='risks')
    op.drop_column('risks', 'detection_key')
    op.drop_column('risks', 'auto_detected')
