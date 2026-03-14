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


class ScoreHistoryPoint(BaseModel):
    score: int
    ts: str


class EvidenceActivityPoint(BaseModel):
    day: str
    count: int


class ManualControlItem(BaseModel):
    control_id: str
    name: str
    description: str
    status: str  # "pending" | "compliant" | "not_applicable"
    notes: Optional[str]
    updated_at: Optional[str]
    owner_user_id: Optional[str] = None
    owner_name: Optional[str] = None


class UpdateManualControlRequest(BaseModel):
    status: str  # "pending" | "compliant" | "not_applicable"
    notes: Optional[str] = None


class AssignManualControlRequest(BaseModel):
    owner_user_id: Optional[str] = None  # UUID string or null to unassign


class AISummaryResponse(BaseModel):
    summary: str
    framework: str
    overall_score: int
    generated_at: str
