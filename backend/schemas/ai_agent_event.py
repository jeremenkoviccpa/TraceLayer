from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel


class AiAgentEventCreate(BaseModel):
    agent_name: str
    agent_type: str = "custom"           # "openai"|"anthropic"|"gemini"|"custom"
    action_type: str                      # "api_call"|"tool_use"|"data_read"|"data_write"|"function_call"
    target_tool: str
    target_url: Optional[str] = None
    data_categories: list[str] = []
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    session_id: Optional[str] = None
    chain_depth: int = 0
    parent_event_id: Optional[uuid.UUID] = None
    risk_flags: list[str] = []           # caller can provide; service will auto-infer additional ones
    status: str = "completed"
    duration_ms: Optional[int] = None
    notes: Optional[str] = None


class AiAgentEventUpdate(BaseModel):
    is_flagged: Optional[bool] = None
    notes: Optional[str] = None
    reviewed_by: Optional[str] = None


class AiAgentEventResponse(BaseModel):
    id: str
    company_id: str
    agent_name: str
    agent_type: str
    action_type: str
    target_tool: str
    target_url: Optional[str]
    data_categories: list[str]
    input_summary: Optional[str]
    output_summary: Optional[str]
    session_id: Optional[str]
    chain_depth: int
    parent_event_id: Optional[str]
    risk_level: str
    risk_flags: list[str]
    status: str
    duration_ms: Optional[int]
    is_flagged: bool
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AiAgentSessionResponse(BaseModel):
    """Groups events by session_id for chain visualization."""
    session_id: str
    events: list[AiAgentEventResponse]
    max_chain_depth: int
    max_risk_level: str
    total_events: int
