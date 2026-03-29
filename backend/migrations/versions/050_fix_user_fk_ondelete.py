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


def upgrade() -> None:
    # email_verification_tokens.user_id → CASCADE
    op.drop_constraint(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # password_reset_tokens.user_id → CASCADE
    op.drop_constraint(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # invitations.invited_by → SET NULL (column must also become nullable)
    op.drop_constraint(
        "invitations_invited_by_fkey",
        "invitations",
        type_="foreignkey",
    )
    op.alter_column("invitations", "invited_by", nullable=True)
    op.create_foreign_key(
        "invitations_invited_by_fkey",
        "invitations",
        "users",
        ["invited_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # audit_logs.user_id → SET NULL
    op.drop_constraint(
        "audit_logs_user_id_fkey",
        "audit_logs",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "audit_logs_user_id_fkey",
        "audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("audit_logs_user_id_fkey", "audit_logs", type_="foreignkey")
    op.create_foreign_key(
        "audit_logs_user_id_fkey", "audit_logs", "users", ["user_id"], ["id"]
    )

    op.drop_constraint("invitations_invited_by_fkey", "invitations", type_="foreignkey")
    op.alter_column("invitations", "invited_by", nullable=False)
    op.create_foreign_key(
        "invitations_invited_by_fkey", "invitations", "users", ["invited_by"], ["id"]
    )

    op.drop_constraint(
        "password_reset_tokens_user_id_fkey", "password_reset_tokens", type_="foreignkey"
    )
    op.create_foreign_key(
        "password_reset_tokens_user_id_fkey",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_constraint(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "email_verification_tokens_user_id_fkey",
        "email_verification_tokens",
        "users",
        ["user_id"],
        ["id"],
    )
