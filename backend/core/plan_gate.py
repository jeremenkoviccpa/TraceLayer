from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.company import Company
from models.user import User


async def require_growth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency: raises 402 if company is not on the Growth plan."""
    if current_user.email in settings.internal_admins:
        return current_user
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company or company.plan != "growth":
        raise HTTPException(
            status_code=402,
            detail="This feature requires the Growth plan. Upgrade at /settings.",
        )
    return current_user
