"""Add audit_engagements and partner_directory tables.

Revision ID: 042_add_partner_ecosystem
Revises: 041_add_ai_agent_events
Create Date: 2026-03-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '042_add_partner_ecosystem'
down_revision = '041_add_ai_agent_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Audit Engagements ─────────────────────────────────────────────────────
    op.create_table(
        'audit_engagements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('customer_company_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framework', sa.String(50), nullable=False),
        sa.Column('obs_start', sa.Date(), nullable=False),
        sa.Column('obs_end', sa.Date(), nullable=False),
        sa.Column('access_token', sa.String(100), unique=True, nullable=False),
        sa.Column('auditor_email', sa.String(255), nullable=False),
        sa.Column('auditor_name', sa.String(255), nullable=True),
        sa.Column('auditor_firm', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index('ix_audit_engagements_company_id', 'audit_engagements', ['customer_company_id'])
    op.create_index('ix_audit_engagements_token', 'audit_engagements', ['access_token'], unique=True)

    # ── Partner Directory ─────────────────────────────────────────────────────
    op.create_table(
        'partner_directory',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('partner_type', sa.String(20), nullable=False),  # "auditor" | "pen_test"
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('referral_url', sa.String(500), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('frameworks', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('specialties', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_partner_directory_type', 'partner_directory', ['partner_type'])

    # ── Seed: Pen Test Firms ──────────────────────────────────────────────────
    op.execute("""
        INSERT INTO partner_directory (id, partner_type, name, description, website, referral_url, specialties, is_featured, is_active)
        VALUES
        (gen_random_uuid(), 'pen_test', 'Cobalt',
         'Pentest as a Service with 400+ vetted security researchers. SOC 2 required pen tests completed in days, not months.',
         'https://cobalt.io', 'https://cobalt.io',
         ARRAY['SOC 2','ISO 27001','HIPAA','PCI DSS','Cloud Security'], true, true),

        (gen_random_uuid(), 'pen_test', 'NetSPI',
         'Enterprise-grade security testing with advanced methodology and detailed remediation guidance.',
         'https://netspi.com', 'https://netspi.com',
         ARRAY['SOC 2','ISO 27001','HIPAA','PCI DSS'], false, true),

        (gen_random_uuid(), 'pen_test', 'Synack',
         'Crowdsourced security testing powered by a managed red team of vetted researchers.',
         'https://synack.com', 'https://synack.com',
         ARRAY['SOC 2','HIPAA','Cloud Security'], false, true),

        (gen_random_uuid(), 'pen_test', 'Rapid7',
         'Full-service pen testing with expert consultants and integrated vulnerability management.',
         'https://rapid7.com', 'https://rapid7.com',
         ARRAY['SOC 2','ISO 27001','PCI DSS','HIPAA'], false, true)
    """)

    # ── Seed: Auditor Firms ───────────────────────────────────────────────────
    op.execute("""
        INSERT INTO partner_directory (id, partner_type, name, description, website, contact_email, frameworks, is_featured, is_active)
        VALUES
        (gen_random_uuid(), 'auditor', 'Prescient Assurance',
         'Startup-friendly SOC 2 and ISO 27001 audits. Fast timelines, transparent pricing, and deep experience with early-stage companies.',
         'https://prescientassurance.com', 'info@prescientassurance.com',
         ARRAY['SOC 2','ISO 27001','HIPAA'], true, true),

        (gen_random_uuid(), 'auditor', 'Johanson Group',
         'Leading audit firm in the SMB and startup space. Known for efficient SOC 2 audits with practical guidance.',
         'https://johansongroup.net', 'info@johansongroup.net',
         ARRAY['SOC 2','HIPAA','PCI DSS'], true, true),

        (gen_random_uuid(), 'auditor', 'A-LIGN',
         'Enterprise-grade compliance assessments. SOC 2, ISO 27001, FedRAMP, HIPAA, and PCI DSS certified auditors.',
         'https://a-lign.com', 'info@a-lign.com',
         ARRAY['SOC 2','ISO 27001','HIPAA','PCI DSS','FedRAMP'], false, true),

        (gen_random_uuid(), 'auditor', 'BARR Advisory',
         'Boutique CPA firm specializing in cybersecurity compliance. Strong reputation with technology vendor partners.',
         'https://barradvisory.com', 'info@barradvisory.com',
         ARRAY['SOC 2','ISO 27001','HIPAA'], false, true),

        (gen_random_uuid(), 'auditor', 'Schellman',
         'Premium compliance assessments for companies going upmarket. Specialists in SOC 2, ISO 27001, and FedRAMP.',
         'https://schellman.com', 'info@schellman.com',
         ARRAY['SOC 2','ISO 27001','HIPAA','FedRAMP','PCI DSS'], false, true)
    """)


def downgrade() -> None:
    op.drop_index('ix_partner_directory_type', table_name='partner_directory')
    op.drop_table('partner_directory')
    op.drop_index('ix_audit_engagements_token', table_name='audit_engagements')
    op.drop_index('ix_audit_engagements_company_id', table_name='audit_engagements')
    op.drop_table('audit_engagements')
