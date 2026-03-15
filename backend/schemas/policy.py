from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PolicyResponse(BaseModel):
    slug: str
    title: str
    category: str
    content: str
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PolicySaveRequest(BaseModel):
    content: str
