import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    framework: str = "soc2"
    report_type: str = "full"
    format: str = "json"  # "json" | "pdf"


class ReportResponse(BaseModel):
    id: uuid.UUID
    framework: str
    report_type: str
    fmt: str
    status: str
    file_url: Optional[str]
    storage_bucket: Optional[str]
    storage_path: Optional[str]
    file_name: Optional[str]
    mime_type: Optional[str]
    file_size: Optional[int]
    generated_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
