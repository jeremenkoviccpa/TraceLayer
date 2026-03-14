import logging
import math
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.reports import GenerateReportRequest, ReportResponse
from services.report_service import (
    SIGNED_URL_EXPIRES_IN,
    create_report,
    generate_pdf_report,
    generate_report_bundle,
    get_report,
    get_signed_report_url,
    list_reports,
)
from utils.pagination import Page

from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


async def _run_json_generation(report_id: uuid.UUID, company_id: uuid.UUID) -> None:
    from core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await generate_report_bundle(report_id, company_id, db)
    except Exception:
        logger.exception("JSON report generation failed: report_id=%s", report_id)


async def _run_pdf_generation(report_id: uuid.UUID, company_id: uuid.UUID) -> None:
    from core.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            await generate_pdf_report(report_id, company_id, db)
    except Exception:
        logger.exception("PDF report generation failed: report_id=%s", report_id)


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
        fmt=body.format,
        db=db,
    )

    if body.format == "pdf":
        background_tasks.add_task(_run_pdf_generation, report.id, current_user.company_id)
    else:
        background_tasks.add_task(_run_json_generation, report.id, current_user.company_id)

    await log_action(
        db, current_user.company_id, "report.generated",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="report", resource_id=str(report.id),
        metadata={"framework": body.framework, "format": body.format},
    )
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
    format: str = Query("json", enum=["json", "pdf"]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await get_report(report_id, current_user.company_id, db)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "complete":
        raise HTTPException(status_code=409, detail=f"Report not ready (status: {report.status})")

    if report.fmt != format:
        raise HTTPException(
            status_code=409,
            detail=f"Report format mismatch (stored: {report.fmt}, requested: {format})",
        )

    try:
        signed_url = await get_signed_report_url(report_id, current_user.company_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await log_action(
        db, current_user.company_id, "report.downloaded",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="report", resource_id=str(report_id),
        metadata={"framework": report.framework, "format": format},
    )
    return JSONResponse(
        content={
            "url": signed_url,
            "expires_in": SIGNED_URL_EXPIRES_IN,
            "file_name": report.file_name,
            "mime_type": report.mime_type,
            "file_size": report.file_size,
        }
    )
