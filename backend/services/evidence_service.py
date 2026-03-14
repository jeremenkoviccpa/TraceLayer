import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.evidence import Evidence


async def list_evidence(
    company_id: uuid.UUID,
    db: AsyncSession,
    control: Optional[str] = None,
    integration: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Evidence], int]:
    query = select(Evidence).where(Evidence.company_id == company_id)

    if control:
        query = query.where(Evidence.control == control)
    if integration:
        query = query.where(Evidence.integration == integration)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    items_result = await db.execute(
        query.order_by(Evidence.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(items_result.scalars().all())

    return items, total


async def get_evidence_by_id(
    evidence_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[Evidence]:
    result = await db.execute(
        select(Evidence).where(
            Evidence.id == evidence_id,
            Evidence.company_id == company_id,
        )
    )
    return result.scalar_one_or_none()
