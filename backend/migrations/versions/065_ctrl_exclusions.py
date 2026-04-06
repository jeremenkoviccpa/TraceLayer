"""Add control_exclusions table for marking controls as not applicable / out of scope.

Revision ID: 065_ctrl_exclusions
Revises: 064_risk_exceptions
Create Date: 2026-04-06
"""
from alembic import op

revision = "065_ctrl_exclusions"
down_revision = "064_risk_exceptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS control_exclusions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            framework VARCHAR(50) NOT NULL,
            control_category VARCHAR(100) NOT NULL,
            control_name VARCHAR(255) NOT NULL,
            justification TEXT NOT NULL,
            exclusion_type VARCHAR(50) NOT NULL DEFAULT 'not_applicable',
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            UNIQUE (company_id, framework, control_category)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ctrl_exclusions_company ON control_exclusions(company_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS control_exclusions")
