from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
import uuid


class ManagementReviewCreate(BaseModel):
    review_date: datetime
    attendees: Optional[str] = None
    inputs_summary: Optional[str] = None
    decisions: Optional[str] = None
    action_items: List[Any] = []
    next_review_date: Optional[datetime] = None
    outcome: str = "satisfactory"
    notes: Optional[str] = None


class ManagementReviewUpdate(ManagementReviewCreate):
    review_date: Optional[datetime] = None


class ManagementReviewResponse(ManagementReviewCreate):
    id: uuid.UUID
    review_date: datetime

    model_config = {"from_attributes": True}
