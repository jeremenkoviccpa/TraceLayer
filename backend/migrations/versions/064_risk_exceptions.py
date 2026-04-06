"""Add risk_exceptions table for formal risk acceptance workflow.

Revision ID: 064_risk_exceptions
Revises: 063_nis2_incident_fields
Create Date: 2026-04-06
"""
from alembic import op

revision = "064_risk_exceptions"
down_revision = "063_nis2_incident_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS risk_exceptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            framework VARCHAR(50) NOT NULL,
            control_category VARCHAR(100) NOT NULL,
            control_name VARCHAR(255) NOT NULL,
            justification TEXT NOT NULL,
            owner_name VARCHAR(255),
            owner_email VARCHAR(255),
            expires_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_risk_exceptions_company ON risk_exceptions(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_risk_exceptions_fw ON risk_exceptions(company_id, framework)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS risk_exceptions")
