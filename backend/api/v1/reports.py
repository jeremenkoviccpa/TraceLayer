import logging
import math
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user, get_current_admin
from core.plan_gate import require_growth
from models.company import Company
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


async def _run_audit_package_generation(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    framework: str,
) -> None:
    from core.database import AsyncSessionLocal
    from services.audit_package_service import generate_audit_package
    try:
        async with AsyncSessionLocal() as db:
            await generate_audit_package(report_id, company_id, framework, db)
    except Exception:
        logger.exception("Audit package generation failed: report_id=%s", report_id)


class AuditPackageRequest(BaseModel):
    framework: str = "soc2"


@router.post("/generate", response_model=ReportResponse, status_code=202)
async def generate(
    body: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Gate PDF/CSV formats to Growth plan
    if body.format in ("pdf", "csv"):
        from core.config import settings
        if current_user.email not in settings.internal_admins_list:
            result_company = await db.execute(select(Company).where(Company.id == current_user.company_id))
            company_obj = result_company.scalar_one_or_none()
            if not company_obj or company_obj.plan != "growth":
                raise HTTPException(
                    status_code=402,
                    detail="PDF and CSV reports require the Growth plan. JSON reports are available on the free plan.",
                )

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


@router.post("/audit-package", response_model=ReportResponse, status_code=202)
async def generate_audit_package_endpoint(
    body: AuditPackageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_growth),
):
    """Generate an AI-powered audit package PDF with full compliance data and AI narrative."""
    report = await create_report(
        company_id=current_user.company_id,
        framework=body.framework,
        report_type="audit_package",
        fmt="pdf",
        db=db,
    )
    background_tasks.add_task(
        _run_audit_package_generation,
        report.id,
        current_user.company_id,
        body.framework,
    )
    await log_action(
        db, current_user.company_id, "report.audit_package_generated",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="report", resource_id=str(report.id),
        metadata={"framework": body.framework},
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


@router.post("/weekly-preview", status_code=202)
async def weekly_report_preview(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a weekly compliance report email for the requesting admin.
    Useful for previewing / testing the weekly digest without waiting for Monday 09:00 UTC.
    """
    from datetime import datetime, timezone, timedelta
    from services.compliance_service import get_compliance_score
    from services.email_service import send_weekly_compliance_report
    from core.config import settings

    FRAMEWORKS = [
        {"value": "soc2",     "label": "SOC 2"},
        {"value": "iso27001", "label": "ISO 27001"},
        {"value": "hipaa",    "label": "HIPAA"},
    ]

    # Build week label identical to the scheduled job
    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    week_label = "{} – {}, {}".format(
        monday.strftime("%b %-d"),
        sunday.strftime("%b %-d"),
        sunday.year,
    )

    framework_scores = []
    for fw in FRAMEWORKS:
        try:
            score_data = await get_compliance_score(current_user.company_id, fw["value"], db)
            framework_scores.append({
                "framework": fw["value"],
                "label": fw["label"],
                "score": score_data["overall_score"],
                "controls": score_data["controls"],
            })
        except Exception as exc:
            logger.warning("Could not compute %s score for preview: %s", fw["value"], exc)

    from models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    _company = company_result.scalar_one_or_none()
    company_name = _company.name if _company else "Your Company"

    try:
        send_weekly_compliance_report(
            to=current_user.email,
            company_name=company_name,
            framework_scores=framework_scores,
            week_label=week_label,
            frontend_url=settings.app_frontend_url,
        )
    except Exception as exc:
        logger.error("weekly-preview email failed for user %s: %s", current_user.email, exc)
        raise HTTPException(status_code=500, detail="Failed to send preview email.")

    await log_action(
        db, current_user.company_id, "report.weekly_preview_sent",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="report", resource_id=None,
        metadata={"week_label": week_label},
    )

    return {"detail": f"Weekly compliance report preview sent to {current_user.email}."}
