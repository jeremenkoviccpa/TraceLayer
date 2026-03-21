from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataFlowCreate(BaseModel):
    data_type: str
    data_category: str
    tool: str
    tool_label: str
    region: str = "unknown"
    risk_level: str = "medium"
    regulations: list[str] = []
    purpose: Optional[str] = None
    legal_basis: Optional[str] = None
    is_cross_border: bool = False
    notes: Optional[str] = None


class DataFlowUpdate(BaseModel):
    data_type: Optional[str] = None
    data_category: Optional[str] = None
    tool: Optional[str] = None
    tool_label: Optional[str] = None
    region: Optional[str] = None
    risk_level: Optional[str] = None
    regulations: Optional[list[str]] = None
    purpose: Optional[str] = None
    legal_basis: Optional[str] = None
    is_cross_border: Optional[bool] = None
    notes: Optional[str] = None


class DataFlowResponse(BaseModel):
    id: str
    company_id: str
    data_type: str
    data_category: str
    tool: str
    tool_label: str
    region: str
    risk_level: str
    regulations: list[str]
    purpose: Optional[str]
    legal_basis: Optional[str]
    is_auto_detected: bool
    is_cross_border: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
