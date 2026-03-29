"""Fix missing ondelete rules on FK references to users.id

Revision ID: 050_fix_user_fk_ondelete
Revises: 049_add_chat_conversations
Create Date: 2026-03-29
"""
from alembic import op

revision = "050_fix_user_fk_ondelete"
down_revision = "049_add_chat_conversations"
branch_labels = None
depends_on = None

# SQL helper: find and drop any FK on (table, column) pointing at users.id,
# then recreate it with the desired ondelete action.
_DROP_AND_RECREATE = """
DO $$
DECLARE
    _cname text;
BEGIN
    SELECT tc.constraint_name INTO _cname
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema    = kcu.table_schema
    JOIN information_schema.referential_constraints rc
        ON tc.constraint_name = rc.constraint_name
        AND tc.table_schema    = rc.constraint_schema
    JOIN information_schema.table_constraints tc2
        ON rc.unique_constraint_name  = tc2.constraint_name
        AND rc.unique_constraint_schema = tc2.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema    = 'public'
      AND tc.table_name      = {table!r}
      AND kcu.column_name    = {column!r}
      AND tc2.table_name     = 'users'
    LIMIT 1;

    IF _cname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %%I', _cname);
    END IF;
END $$;

ALTER TABLE {table}
    ADD CONSTRAINT {new_name} FOREIGN KEY ({column})
    REFERENCES users(id) ON DELETE {action};
"""


def _fix(table: str, column: str, action: str) -> None:
    new_name = f"{table}_{column}_fkey"
    op.execute(
        _DROP_AND_RECREATE.format(
            table=table, column=column, action=action, new_name=new_name
        )
    )


def upgrade() -> None:
    _fix("email_verification_tokens", "user_id", "CASCADE")
    _fix("password_reset_tokens", "user_id", "CASCADE")

    # invitations.invited_by must become nullable before SET NULL can work
    op.execute("""
DO $$
DECLARE
    _cname text;
BEGIN
    SELECT tc.constraint_name INTO _cname
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema    = kcu.table_schema
    JOIN information_schema.referential_constraints rc
        ON tc.constraint_name = rc.constraint_name
        AND tc.table_schema    = rc.constraint_schema
    JOIN information_schema.table_constraints tc2
        ON rc.unique_constraint_name  = tc2.constraint_name
        AND rc.unique_constraint_schema = tc2.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema    = 'public'
      AND tc.table_name      = 'invitations'
      AND kcu.column_name    = 'invited_by'
      AND tc2.table_name     = 'users'
    LIMIT 1;

    IF _cname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE invitations DROP CONSTRAINT %%I', _cname);
    END IF;
END $$;

ALTER TABLE invitations ALTER COLUMN invited_by DROP NOT NULL;

ALTER TABLE invitations
    ADD CONSTRAINT invitations_invited_by_fkey FOREIGN KEY (invited_by)
    REFERENCES users(id) ON DELETE SET NULL;
    """)

    _fix("audit_logs", "user_id", "SET NULL")


def downgrade() -> None:
    # Restore without ondelete (default RESTRICT)
    op.execute("""
        ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
        ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id);
    """)
    op.execute("""
        ALTER TABLE invitations DROP CONSTRAINT IF EXISTS invitations_invited_by_fkey;
        ALTER TABLE invitations ALTER COLUMN invited_by SET NOT NULL;
        ALTER TABLE invitations ADD CONSTRAINT invitations_invited_by_fkey
            FOREIGN KEY (invited_by) REFERENCES users(id);
    """)
    op.execute("""
        ALTER TABLE password_reset_tokens DROP CONSTRAINT IF EXISTS password_reset_tokens_user_id_fkey;
        ALTER TABLE password_reset_tokens ADD CONSTRAINT password_reset_tokens_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id);
    """)
    op.execute("""
        ALTER TABLE email_verification_tokens DROP CONSTRAINT IF EXISTS email_verification_tokens_user_id_fkey;
        ALTER TABLE email_verification_tokens ADD CONSTRAINT email_verification_tokens_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id);
    """)
