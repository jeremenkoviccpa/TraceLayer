from typing import Optional
from pydantic import BaseModel


class ControlScore(BaseModel):
    category: str
    name: str
    score: int
    status: str  # "passing" | "warning" | "failing" | "no_evidence"
    evidence_count: int
    covered_types: list[str]
    missing_types: list[str]
    last_collected: Optional[str]


class ComplianceScoreResponse(BaseModel):
    framework: str
    overall_score: int
    evaluated_at: str
    controls: list[ControlScore]
