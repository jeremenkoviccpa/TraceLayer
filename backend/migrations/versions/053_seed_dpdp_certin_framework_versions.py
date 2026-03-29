"""Register DPDP Act 2023 and CERT-In Directions 2022 in framework versioning tables.

Adds rows to:
  - framework_versions           — current version metadata
  - framework_source_manifests   — source URL watched by the framework monitor

The monitor job (schedule_framework_monitor) iterates ALL manifest rows, so
both frameworks will be checked for updates automatically on the next run.
The extraction service now supports PDF URLs via pypdf, so the official
government PDFs can be fetched, hashed, and sent to Claude for structured
control diffs when a change is detected.

Revision ID: 053_seed_dpdp_certin_framework_versions
Revises: 052_seed_dpdp_certin_controls
Create Date: 2026-03-29
"""
from alembic import op

revision = "053_seed_dpdp_certin_framework_versions"
down_revision = "052_seed_dpdp_certin_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Only insert if not already present (idempotent)
    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, is_current, published_at)
        SELECT gen_random_uuid(), 'dpdp', '2023', 'DPDP Act 2023', TRUE, '2023-08-11'
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_versions WHERE framework_key = 'dpdp'
        )
    """)

    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, is_current, published_at)
        SELECT gen_random_uuid(), 'cert_in', '2022', 'CERT-In Directions 2022', TRUE, '2022-04-28'
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_versions WHERE framework_key = 'cert_in'
        )
    """)

    # Source manifests — official government source documents.
    # The monitor hashes these URLs; a changed hash triggers a FrameworkUpdateRequest
    # and Slack alert so the team can review and apply any new requirements.
    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        SELECT gen_random_uuid(),
               'dpdp',
               'https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf',
               '2023'
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_source_manifests WHERE framework_key = 'dpdp'
        )
    """)

    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        SELECT gen_random_uuid(),
               'cert_in',
               'https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf',
               '2022'
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_source_manifests WHERE framework_key = 'cert_in'
        )
    """)


def downgrade() -> None:
    op.execute("DELETE FROM framework_source_manifests WHERE framework_key IN ('dpdp', 'cert_in')")
    op.execute("DELETE FROM framework_versions WHERE framework_key IN ('dpdp', 'cert_in')")
