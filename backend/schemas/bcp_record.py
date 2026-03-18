from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BcpRecordCreate(BaseModel):
    title: str
    record_type: str = "both"
    status: str = "not_tested"
    last_tested_at: Optional[datetime] = None
    next_test_due: Optional[datetime] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    test_results: Optional[str] = None
    scope: Optional[str] = None
    notes: Optional[str] = None
    owner_user_id: Optional[str] = None
    file_url: Optional[str] = None


class BcpRecordUpdate(BaseModel):
    title: Optional[str] = None
    record_type: Optional[str] = None
    status: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    next_test_due: Optional[datetime] = None
    rto_minutes: Optional[int] = None
    rpo_minutes: Optional[int] = None
    test_results: Optional[str] = None
    scope: Optional[str] = None
    notes: Optional[str] = None
    owner_user_id: Optional[str] = None
    file_url: Optional[str] = None


class BcpRecordResponse(BaseModel):
    id: str
    company_id: str
    title: str
    record_type: str
    status: str
    last_tested_at: Optional[datetime]
    next_test_due: Optional[datetime]
    rto_minutes: Optional[int]
    rpo_minutes: Optional[int]
    test_results: Optional[str]
    scope: Optional[str]
    notes: Optional[str]
    owner_user_id: Optional[str]
    owner_name: Optional[str]
    file_url: Optional[str]
    created_at: datetime
    updated_at: datetime
