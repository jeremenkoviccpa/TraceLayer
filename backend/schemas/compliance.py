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
    due_date: Optional[str] = None  # ISO date string YYYY-MM-DD


class UpdateManualControlRequest(BaseModel):
    status: str  # "pending" | "compliant" | "not_applicable"
    notes: Optional[str] = None


class AssignManualControlRequest(BaseModel):
    owner_user_id: Optional[str] = None  # UUID string or null to unassign


class SetDueDateRequest(BaseModel):
    due_date: Optional[str] = None  # ISO date "YYYY-MM-DD" or null to clear


class AISummaryResponse(BaseModel):
    summary: str
    framework: str
    overall_score: int
    generated_at: str


class RemediationStep(BaseModel):
    step: int
    action: str
    detail: str


class RemediationResponse(BaseModel):
    control_id: str
    control_name: str
    priority: str          # "critical" | "high" | "medium" | "low"
    suggested_sla_days: int
    steps: list[RemediationStep]
    helpful_integrations: list[str]   # integration types already connected that help
    missing_integrations: list[str]   # integration types that would help but aren't connected


class ActionPlanItem(BaseModel):
    rank: int
    category: str
    title: str
    description: str
    effort: str   # "quick" | "medium" | "involved"
    impact: str   # "high" | "medium" | "low"
    control_refs: list[str]
    suggested_action: str


class ActionPlanResponse(BaseModel):
    framework: str
    overall_score: int
    items: list[ActionPlanItem]
    generated_at: str
