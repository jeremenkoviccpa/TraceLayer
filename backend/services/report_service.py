import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.evidence import Evidence
from models.report import Report


async def create_report(
    company_id: uuid.UUID,
    framework: str,
    report_type: str,
    db: AsyncSession,
) -> Report:
    report = Report(
        company_id=company_id,
        report_type=report_type,
        framework=framework,
        status="pending",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def generate_report_bundle(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Generate the JSON evidence bundle for a report.
    Called in the background after create_report().
    """
    report_result = await db.execute(
        select(Report).where(Report.id == report_id, Report.company_id == company_id)
    )
    report = report_result.scalar_one_or_none()
    if not report:
        raise ValueError("Report not found")

    try:
        evidence_result = await db.execute(
            select(Evidence).where(Evidence.company_id == company_id)
        )
        records = list(evidence_result.scalars().all())

        # Group evidence by control
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

        bundle = {
            "report_id": str(report.id),
            "company_id": str(company_id),
            "framework": report.framework,
            "report_type": report.report_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_evidence_records": len(records),
            "controls": by_control,
        }

        now = datetime.now(timezone.utc)
        report.status = "complete"
        report.generated_at = now
        # file_url points to the download endpoint — no external storage needed for MVP
        report.file_url = f"/v1/reports/{report.id}/download"
        await db.commit()

        return bundle

    except Exception as e:
        report.status = "error"
        await db.commit()
        raise


async def list_reports(
    company_id: uuid.UUID,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Report], int]:
    from sqlalchemy import func
    query = select(Report).where(Report.company_id == company_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    items = list(
        (await db.execute(
            query.order_by(Report.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
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
