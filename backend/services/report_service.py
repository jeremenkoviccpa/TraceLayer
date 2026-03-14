import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.company import Company
from models.evidence import Evidence
from models.report import Report
from core.config import settings
from services.storage_service import create_signed_url, upload_bytes

SIGNED_URL_EXPIRES_IN = 3600


async def create_report(
    company_id: uuid.UUID,
    framework: str,
    report_type: str,
    fmt: str,
    db: AsyncSession,
) -> Report:
    report = Report(
        company_id=company_id,
        report_type=report_type,
        framework=framework,
        status="pending",
        fmt=fmt,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def _build_bundle(company_id: uuid.UUID, db: AsyncSession) -> tuple[dict, int]:
    """Collect all evidence for company and return (bundle_dict, total_count)."""
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.company_id == company_id)
    )
    records = list(evidence_result.scalars().all())

    by_control: dict[str, list] = {}
    for e in records:
        by_control.setdefault(e.control, []).append({
            "id": str(e.id),
            "integration": e.integration,
            "evidence_type": e.evidence_type,
            "source_id": e.source_id,
            "timestamp": e.timestamp.isoformat(),
            "data": e.data,
        })

    return by_control, len(records)


async def generate_report_bundle(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Generate JSON evidence bundle, upload to storage, and mark report complete."""
    report = await _get_report_or_raise(report_id, company_id, db)

    try:
        by_control, total = await _build_bundle(company_id, db)
        now = datetime.now(timezone.utc)

        bundle = {
            "report_id": str(report.id),
            "company_id": str(company_id),
            "framework": report.framework,
            "report_type": report.report_type,
            "generated_at": now.isoformat(),
            "total_evidence_records": total,
            "controls": by_control,
        }

        payload = json.dumps(bundle).encode("utf-8")
        bucket = report.storage_bucket or settings.storage_bucket or "reports"
        path = f"reports/{company_id}/{report.id}.json"
        upload_bytes(bucket, path, payload, "application/json")

        report.status = "complete"
        report.generated_at = now
        report.file_url = f"/v1/reports/{report.id}/download?format=json"
        report.storage_bucket = bucket
        report.storage_path = path
        report.file_name = f"{report.framework}_report.json"
        report.mime_type = "application/json"
        report.file_size = len(payload)
        await db.commit()
        return bundle

    except Exception:
        report.status = "error"
        await db.commit()
        raise


async def generate_pdf_report(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Generate PDF, upload to storage, mark report complete."""
    from reports.generator import render_pdf
    from services.compliance_service import get_compliance_score

    report = await _get_report_or_raise(report_id, company_id, db)

    try:
        by_control, total = await _build_bundle(company_id, db)

        # Get company name
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one()

        # Get compliance score for summary
        score_data = await get_compliance_score(company_id, report.framework, db)

        now = datetime.now(timezone.utc)
        context = {
            "report_id": str(report.id),
            "company_name": company.name,
            "framework": report.framework,
            "report_type": report.report_type,
            "generated_at": now.strftime("%B %d, %Y"),
            "generated_at_full": now.strftime("%Y-%m-%d %H:%M UTC"),
            "total_records": total,
            "overall_score": score_data["overall_score"],
            "control_scores": score_data["controls"],
            "controls": by_control,
        }

        pdf_bytes = render_pdf(context)
        bucket = report.storage_bucket or settings.storage_bucket or "reports"
        path = f"reports/{company_id}/{report.id}.pdf"
        upload_bytes(bucket, path, pdf_bytes, "application/pdf")

        report.status = "complete"
        report.generated_at = now
        report.file_url = f"/v1/reports/{report.id}/download?format=pdf"
        report.storage_bucket = bucket
        report.storage_path = path
        report.file_name = f"{report.framework}_report.pdf"
        report.mime_type = "application/pdf"
        report.file_size = len(pdf_bytes)
        await db.commit()

    except Exception:
        report.status = "error"
        await db.commit()
        raise


async def list_reports(
    company_id: uuid.UUID,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Report], int]:
    query = select(Report).where(Report.company_id == company_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = list(
        (
            await db.execute(
                query.order_by(Report.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
    )
    return items, total


async def get_report(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[Report]:
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.company_id == company_id)
    )
    return result.scalar_one_or_none()


async def get_signed_report_url(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
    expires_in: int = SIGNED_URL_EXPIRES_IN,
) -> str:
    report = await _get_report_or_raise(report_id, company_id, db)
    if not report.storage_bucket or not report.storage_path:
        raise ValueError("Report storage location not available")
    return create_signed_url(report.storage_bucket, report.storage_path, expires_in)


async def _get_report_or_raise(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> Report:
    report = await get_report(report_id, company_id, db)
    if not report:
        raise ValueError("Report not found")
    return report
