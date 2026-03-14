import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GenerateReportRequest(BaseModel):
    framework: str = "soc2"
    report_type: str = "full"


class ReportResponse(BaseModel):
    id: uuid.UUID
    framework: str
    report_type: str
    status: str
    file_url: Optional[str]
    generated_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
