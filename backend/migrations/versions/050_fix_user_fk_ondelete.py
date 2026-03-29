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


def _drop_fk(table: str, column: str) -> None:
    """Drop whatever FK constraint exists on (table, column) → users.id."""
    op.execute(f"""
        DO $$
        DECLARE
            _cname text;
        BEGIN
            SELECT tc.constraint_name INTO _cname
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name  = kcu.constraint_name
                AND tc.table_schema    = kcu.table_schema
            JOIN information_schema.referential_constraints rc
                ON tc.constraint_name  = rc.constraint_name
                AND tc.table_schema    = rc.constraint_schema
            JOIN information_schema.table_constraints tc2
                ON rc.unique_constraint_name   = tc2.constraint_name
                AND rc.unique_constraint_schema = tc2.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema    = 'public'
              AND tc.table_name      = '{table}'
              AND kcu.column_name    = '{column}'
              AND tc2.table_name     = 'users'
            LIMIT 1;

            IF _cname IS NOT NULL THEN
                EXECUTE format('ALTER TABLE {table} DROP CONSTRAINT %%I', _cname);
            END IF;
        END $$
    """)


def upgrade() -> None:
    # email_verification_tokens.user_id → CASCADE
    _drop_fk("email_verification_tokens", "user_id")
    op.execute("""
        ALTER TABLE email_verification_tokens
            ADD CONSTRAINT email_verification_tokens_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    """)

    # password_reset_tokens.user_id → CASCADE
    _drop_fk("password_reset_tokens", "user_id")
    op.execute("""
        ALTER TABLE password_reset_tokens
            ADD CONSTRAINT password_reset_tokens_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    """)

    # invitations.invited_by → SET NULL (make nullable first)
    _drop_fk("invitations", "invited_by")
    op.execute("ALTER TABLE invitations ALTER COLUMN invited_by DROP NOT NULL")
    op.execute("""
        ALTER TABLE invitations
            ADD CONSTRAINT invitations_invited_by_fkey
            FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL
    """)

    # audit_logs.user_id → SET NULL
    _drop_fk("audit_logs", "user_id")
    op.execute("""
        ALTER TABLE audit_logs
            ADD CONSTRAINT audit_logs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey")
    op.execute("ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)")

    op.execute("ALTER TABLE invitations DROP CONSTRAINT IF EXISTS invitations_invited_by_fkey")
    op.execute("ALTER TABLE invitations ALTER COLUMN invited_by SET NOT NULL")
    op.execute("ALTER TABLE invitations ADD CONSTRAINT invitations_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES users(id)")

    op.execute("ALTER TABLE password_reset_tokens DROP CONSTRAINT IF EXISTS password_reset_tokens_user_id_fkey")
    op.execute("ALTER TABLE password_reset_tokens ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)")

    op.execute("ALTER TABLE email_verification_tokens DROP CONSTRAINT IF EXISTS email_verification_tokens_user_id_fkey")
    op.execute("ALTER TABLE email_verification_tokens ADD CONSTRAINT email_verification_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)")
