"""Add ai_agent_events table for tracking autonomous AI agent actions across systems.

Revision ID: 041_add_ai_agent_events
Revises: 040_add_data_flows
Create Date: 2026-03-21 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '041_add_ai_agent_events'
down_revision = '040_add_data_flows'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_agent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),

        # Which agent fired this
        sa.Column('agent_name', sa.String(200), nullable=False),   # e.g. "GPT-4o", "Claude 3.5 Sonnet", "custom-crm-agent"
        sa.Column('agent_type', sa.String(50), nullable=False),    # "openai" | "anthropic" | "gemini" | "custom"

        # What it did
        sa.Column('action_type', sa.String(50), nullable=False),   # "api_call" | "tool_use" | "data_read" | "data_write" | "function_call"
        sa.Column('target_tool', sa.String(200), nullable=False),  # "salesforce" | "stripe" | "external_api" | etc.
        sa.Column('target_url', sa.String(500), nullable=True),    # actual endpoint if known

        # What data moved
        sa.Column('data_categories', postgresql.JSONB(), nullable=False, server_default='[]'),   # ["pii", "financial", "health"]
        sa.Column('input_summary', sa.Text(), nullable=True),      # sanitized description of what was sent
        sa.Column('output_summary', sa.Text(), nullable=True),     # sanitized description of what came back

        # Chain tracking — groups related calls in one "run"
        sa.Column('session_id', sa.String(100), nullable=True),    # groups a chain of calls
        sa.Column('chain_depth', sa.Integer(), nullable=False, server_default='0'),  # 0 = direct, 1+ = triggered by another agent call
        sa.Column('parent_event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ai_agent_events.id', ondelete='SET NULL'), nullable=True),

        # Risk assessment
        sa.Column('risk_level', sa.String(20), nullable=False, server_default='medium'),   # "low"|"medium"|"high"|"critical"
        sa.Column('risk_flags', postgresql.JSONB(), nullable=False, server_default='[]'),  # ["pii_exfiltration", "cross_border", "unauthenticated_endpoint", "chain_escalation"]

        # Outcome
        sa.Column('status', sa.String(20), nullable=False, server_default='completed'),  # "completed"|"failed"|"blocked"
        sa.Column('duration_ms', sa.Integer(), nullable=True),

        # Review workflow
        sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reviewed_by', sa.String(200), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_ai_agent_events_company_id', 'ai_agent_events', ['company_id'])
    op.create_index('ix_ai_agent_events_session_id', 'ai_agent_events', ['session_id'])
    op.create_index('ix_ai_agent_events_risk_level', 'ai_agent_events', ['risk_level'])
    op.create_index('ix_ai_agent_events_agent_type', 'ai_agent_events', ['agent_type'])
    op.create_index('ix_ai_agent_events_is_flagged', 'ai_agent_events', ['is_flagged'])
    op.create_index('ix_ai_agent_events_created_at', 'ai_agent_events', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_agent_events_created_at', table_name='ai_agent_events')
    op.drop_index('ix_ai_agent_events_is_flagged', table_name='ai_agent_events')
    op.drop_index('ix_ai_agent_events_agent_type', table_name='ai_agent_events')
    op.drop_index('ix_ai_agent_events_risk_level', table_name='ai_agent_events')
    op.drop_index('ix_ai_agent_events_session_id', table_name='ai_agent_events')
    op.drop_index('ix_ai_agent_events_company_id', table_name='ai_agent_events')
    op.drop_table('ai_agent_events')
