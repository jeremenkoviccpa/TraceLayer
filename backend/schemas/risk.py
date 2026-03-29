from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class RiskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "General"
    likelihood: int = 3
    impact: int = 3
    status: str = "open"
    owner_user_id: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("likelihood", "impact")
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Must be between 1 and 5")
        return v


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    likelihood: Optional[int] = None
    impact: Optional[int] = None
    status: Optional[str] = None
    owner_user_id: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("likelihood", "impact", mode="before")
    @classmethod
    def validate_score(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Must be between 1 and 5")
        return v


class RiskResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: Optional[str]
    category: str
    likelihood: int
    impact: int
    status: str
    owner_user_id: Optional[str]
    owner_name: Optional[str] = None
    notes: Optional[str]
    due_date: Optional[datetime] = None
    auto_detected: bool = False
    detection_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    risk_level: str = ""

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_risk_level(self) -> "RiskResponse":
        score = self.likelihood * self.impact
        if score >= 16:
            self.risk_level = "critical"
        elif score >= 9:
            self.risk_level = "high"
        elif score >= 4:
            self.risk_level = "medium"
        else:
            self.risk_level = "low"
        return self
