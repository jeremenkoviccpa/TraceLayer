import uuid
from datetime import datetime

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    integration: str
    control: str
    evidence_type: str
    source_id: str
    timestamp: datetime
    data: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
