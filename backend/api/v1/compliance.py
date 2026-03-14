from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.compliance import ComplianceScoreResponse
from services.compliance_service import get_compliance_score

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/score", response_model=ComplianceScoreResponse)
async def compliance_score(
    framework: str = Query("soc2", description="Compliance framework"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_compliance_score(current_user.company_id, framework, db)
    return result
