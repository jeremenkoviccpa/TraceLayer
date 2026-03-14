import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    user_email: Optional[str]
    action: str
    action_label: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    metadata_: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
