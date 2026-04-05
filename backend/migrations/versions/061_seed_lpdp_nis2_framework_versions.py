"""Seed framework_versions and framework_source_manifests for Serbian LPDP and NIS2.

Revision ID: 061_seed_lpdp_nis2_framework_versions
Revises: 060_seed_lpdp_nis2_controls
Create Date: 2026-04-05
"""
from alembic import op

revision = "061_lpdp_nis2_fw_versions"
down_revision = "060_seed_lpdp_nis2_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Serbian LPDP — framework version
    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, is_current, published_at)
        SELECT gen_random_uuid(), 'lpdp', '2018', 'Serbian LPDP 2018', TRUE, '2018-11-09'::date
        WHERE NOT EXISTS (SELECT 1 FROM framework_versions WHERE framework_key = 'lpdp')
    """)

    # NIS2 — framework version
    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, is_current, published_at)
        SELECT gen_random_uuid(), 'nis2', '2022', 'NIS2 Directive 2022', TRUE, '2022-12-27'::date
        WHERE NOT EXISTS (SELECT 1 FROM framework_versions WHERE framework_key = 'nis2')
    """)

    # Serbian LPDP — source manifest
    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        SELECT gen_random_uuid(),
               'lpdp',
               'https://www.poverenik.rs/images/stories/dokumentacija-nova/zakoni/ZZPLeng.pdf',
               '2018'
        WHERE NOT EXISTS (SELECT 1 FROM framework_source_manifests WHERE framework_key = 'lpdp')
    """)

    # NIS2 — source manifest (ELI canonical URL avoids '?' parameter-placeholder ambiguity)
    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        SELECT gen_random_uuid(),
               'nis2',
               'https://eur-lex.europa.eu/eli/dir/2022/2555/oj',
               '2022'
        WHERE NOT EXISTS (SELECT 1 FROM framework_source_manifests WHERE framework_key = 'nis2')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM framework_versions WHERE framework_key IN ('lpdp', 'nis2')")
    op.execute("DELETE FROM framework_source_manifests WHERE framework_key IN ('lpdp', 'nis2')")
