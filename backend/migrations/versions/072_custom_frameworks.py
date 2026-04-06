"""Add custom_frameworks and custom_controls tables.

Revision ID: 072_custom_frameworks
Revises: 071_pen_tests_v2
Create Date: 2026-04-06
"""
from alembic import op

revision = "072_custom_frameworks"
down_revision = "071_pen_tests_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS custom_frameworks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            version VARCHAR(50) NOT NULL DEFAULT '1.0',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_custom_frameworks_company ON custom_frameworks(company_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS custom_controls (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            framework_id UUID NOT NULL REFERENCES custom_frameworks(id) ON DELETE CASCADE,
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL DEFAULT 'general',
            description TEXT,
            external_id VARCHAR(100),
            evidence_types JSONB NOT NULL DEFAULT '[]',
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_custom_controls_company ON custom_controls(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_custom_controls_framework ON custom_controls(framework_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS custom_controls")
    op.execute("DROP TABLE IF EXISTS custom_frameworks")
