import math
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.reports import GenerateReportRequest, ReportResponse
from services.report_service import (
    create_report,
    generate_report_bundle,
    get_report,
    list_reports,
)
from utils.pagination import Page

router = APIRouter(prefix="/reports", tags=["reports"])


async def _run_generation(report_id: uuid.UUID, company_id: uuid.UUID) -> None:
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await generate_report_bundle(report_id, company_id, db)


@router.post("/generate", response_model=ReportResponse, status_code=202)
async def generate(
    body: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await create_report(
        company_id=current_user.company_id,
        framework=body.framework,
        report_type=body.report_type,
        db=db,
    )
    background_tasks.add_task(_run_generation, report.id, current_user.company_id)
    return report


@router.get("", response_model=Page[ReportResponse])
async def get_reports(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_reports(current_user.company_id, db, page, page_size)
    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await get_report(report_id, current_user.company_id, db)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await get_report(report_id, current_user.company_id, db)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "complete":
        raise HTTPException(status_code=409, detail=f"Report is not ready (status: {report.status})")

    bundle = await generate_report_bundle(report_id, current_user.company_id, db)
    return JSONResponse(content=bundle)
