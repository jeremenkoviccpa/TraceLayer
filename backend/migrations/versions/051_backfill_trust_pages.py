"""Backfill trust_pages rows for companies that don't have one yet.

Revision ID: 051_backfill_trust_pages
Revises: 050_fix_user_fk_ondelete
Create Date: 2026-03-29
"""
from alembic import op

revision = "051_backfill_trust_pages"
down_revision = "050_fix_user_fk_ondelete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create trust_pages rows for any company that doesn't have one.
    # Uses the same slugify logic as the Python model: lowercase, strip non-word chars,
    # replace whitespace/underscores with hyphens.  Collision suffix added when needed.
    op.execute("""
        DO $$
        DECLARE
            rec RECORD;
            _base_slug TEXT;
            _slug TEXT;
            _suffix INT;
        BEGIN
            FOR rec IN
                SELECT c.id, c.name
                FROM companies c
                WHERE NOT EXISTS (
                    SELECT 1 FROM trust_pages tp WHERE tp.company_id = c.id
                )
            LOOP
                -- Replicate Python slugify():
                --   lower, strip leading/trailing whitespace,
                --   remove chars that are not \\w / space / hyphen,
                --   replace whitespace+underscores with hyphen,
                --   collapse multiple hyphens.
                _base_slug := lower(trim(rec.name));
                _base_slug := regexp_replace(_base_slug, '[^\w\s-]', '', 'g');
                _base_slug := regexp_replace(_base_slug, '[\s_]+', '-', 'g');
                _base_slug := regexp_replace(_base_slug, '-+', '-', 'g');
                _base_slug := trim(both '-' from substring(_base_slug, 1, 80));
                IF _base_slug = '' THEN
                    _base_slug := 'my-company';
                END IF;

                _slug := _base_slug;
                _suffix := 0;

                -- Find a unique slug
                WHILE EXISTS (SELECT 1 FROM trust_pages WHERE slug = _slug) LOOP
                    _suffix := _suffix + 1;
                    _slug := _base_slug || '-' || _suffix::TEXT;
                END LOOP;

                INSERT INTO trust_pages (
                    id, company_id, slug,
                    is_enabled, show_score, show_policies, show_integrations,
                    frameworks_json, domain_verified,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), rec.id, _slug,
                    true, true, true, false,
                    '["soc2","iso27001","hipaa","gdpr","pci_dss","ccpa","nist_csf","dpdp","cert_in"]', false,
                    now(), now()
                );
            END LOOP;
        END $$
    """)


def downgrade() -> None:
    pass
