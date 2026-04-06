"""Add pen_tests_v2 and pen_test_findings tables.

Revision ID: 071_pen_tests_v2
Revises: 070_devices_v2
Create Date: 2026-04-06
"""
from alembic import op

revision = "071_pen_tests_v2"
down_revision = "070_devices_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS pen_tests_v2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            vendor_name VARCHAR(255),
            test_type VARCHAR(100) NOT NULL DEFAULT 'external',
            status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
            scope TEXT,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            report_url VARCHAR(1000),
            executive_summary TEXT,
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pen_tests_v2_company ON pen_tests_v2(company_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS pen_test_findings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pen_test_id UUID NOT NULL REFERENCES pen_tests_v2(id) ON DELETE CASCADE,
            company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            severity VARCHAR(50) NOT NULL DEFAULT 'medium',
            status VARCHAR(50) NOT NULL DEFAULT 'open',
            description TEXT,
            recommendation TEXT,
            cvss_score FLOAT,
            cve_id VARCHAR(50),
            remediation_notes TEXT,
            remediated_at TIMESTAMP WITH TIME ZONE,
            ticket_url VARCHAR(1000),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_pen_test_findings_company ON pen_test_findings(company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_pen_test_findings_test ON pen_test_findings(pen_test_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pen_test_findings")
    op.execute("DROP TABLE IF EXISTS pen_tests_v2")
