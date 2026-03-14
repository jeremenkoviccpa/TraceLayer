from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.compliance import ComplianceScoreResponse, EvidenceActivityPoint, ScoreHistoryPoint
from services.compliance_service import get_compliance_score, get_evidence_activity, get_score_history

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/score", response_model=ComplianceScoreResponse)
async def compliance_score(
    framework: str = Query("soc2", description="Compliance framework"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_compliance_score(current_user.company_id, framework, db)


@router.get("/score-history", response_model=list[ScoreHistoryPoint])
async def score_history(
    framework: str = Query("soc2"),
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_score_history(current_user.company_id, framework, days, db)


@router.get("/evidence-activity", response_model=list[EvidenceActivityPoint])
async def evidence_activity(
    days: int = Query(14, ge=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_evidence_activity(current_user.company_id, days, db)
