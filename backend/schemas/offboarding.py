from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ChecklistItem(BaseModel):
    item: str
    done: bool = False


class OffboardingCreate(BaseModel):
    employee_name: str
    employee_email: Optional[str] = None
    last_day: Optional[datetime] = None
    department: Optional[str] = None
    status: str = "pending"
    checklist: list[dict[str, Any]] = []
    notes: Optional[str] = None


class OffboardingUpdate(BaseModel):
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    last_day: Optional[datetime] = None
    department: Optional[str] = None
    status: Optional[str] = None
    checklist: Optional[list[dict[str, Any]]] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class OffboardingResponse(BaseModel):
    id: str
    company_id: str
    employee_name: str
    employee_email: Optional[str]
    last_day: Optional[datetime]
    department: Optional[str]
    status: str
    checklist: list[dict[str, Any]]
    completed_by_user_id: Optional[str]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
