"""Seed framework_versions and framework_source_manifests with data for all 7 frameworks.

Revision ID: 038_seed_framework_versions
Revises: 037_framework_versioning_schema
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op

revision = '038_seed_framework_versions'
down_revision = '037_framework_versioning_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── framework_versions ────────────────────────────────────────────────────
    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, is_current, published_at)
        VALUES
            (gen_random_uuid(), 'soc2',     '2022', 'SOC 2 TSC 2022',          TRUE, '2022-10-15'),
            (gen_random_uuid(), 'iso27001',  '2022', 'ISO 27001:2022',           TRUE, '2022-10-25'),
            (gen_random_uuid(), 'hipaa',     '2024', 'HIPAA Security Rule 2024', TRUE, '2024-03-27'),
            (gen_random_uuid(), 'gdpr',      '2018', 'GDPR 2018',               TRUE, '2018-05-25'),
            (gen_random_uuid(), 'pci_dss',   '4.0',  'PCI DSS v4.0',            TRUE, '2022-03-31'),
            (gen_random_uuid(), 'ccpa',      '2023', 'CCPA/CPRA 2023',          TRUE, '2023-01-01'),
            (gen_random_uuid(), 'nist_csf',  '2.0',  'NIST CSF 2.0',            TRUE, '2024-02-26')
    """)

    # ── framework_source_manifests ────────────────────────────────────────────
    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        VALUES
            (gen_random_uuid(), 'soc2',    'https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria',          '2022'),
            (gen_random_uuid(), 'iso27001', 'https://www.iso.org/standard/27001',                                                  '2022'),
            (gen_random_uuid(), 'hipaa',   'https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html',    '2024'),
            (gen_random_uuid(), 'gdpr',    'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679',              '2018'),
            (gen_random_uuid(), 'pci_dss', 'https://www.pcisecuritystandards.org/document_library/',                              '4.0'),
            (gen_random_uuid(), 'ccpa',    'https://cppa.ca.gov/regulations/',                                                     '2023'),
            (gen_random_uuid(), 'nist_csf','https://www.nist.gov/cyberframework',                                                  '2.0')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM framework_source_manifests WHERE framework_key IN ('soc2', 'iso27001', 'hipaa', 'gdpr', 'pci_dss', 'ccpa', 'nist_csf')")
    op.execute("DELETE FROM framework_versions WHERE framework_key IN ('soc2', 'iso27001', 'hipaa', 'gdpr', 'pci_dss', 'ccpa', 'nist_csf')")
