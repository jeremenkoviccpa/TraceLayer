"""
Specialized compliance report service.

Queries the DB, builds context dicts, calls PDF generators,
uploads to storage, and updates the Report record.
"""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.access_review import AccessReview
from models.company import Company
from models.data_breach import DataBreach
from models.incident import Incident
from models.management_review import ManagementReview
from models.report import Report
from models.subject_request import SubjectRequest
from models.training import TrainingRecord
from models.vendor import Vendor

logger = logging.getLogger(__name__)

REPORT_META = {
    "breach_notification": {"label": "Data Breach Notification Report", "framework": "gdpr"},
    "certin_incident":     {"label": "CERT-In Incident Report",          "framework": "cert_in"},
    "nis2_incident":       {"label": "NIS2 CSIRT Incident Report",       "framework": "nis2"},
    "dsar_log":            {"label": "DSAR Response Log",                "framework": "gdpr"},
    "management_review":   {"label": "Management Review Summary",        "framework": "soc2"},
    "vendor_risk":         {"label": "Vendor Risk Report",               "framework": "soc2"},
    "training_completion": {"label": "Training Completion Report",       "framework": "soc2"},
    "access_review":       {"label": "Access Review Report",             "framework": "soc2"},
}


async def _get_company_name(company_id: uuid.UUID, db: AsyncSession) -> str:
    res = await db.execute(select(Company).where(Company.id == company_id))
    c = res.scalar_one_or_none()
    return c.name if c else "Your Company"


def _hours_between(start, end) -> str | None:
    if start is None or end is None:
        return None
    delta = end - start
    h = delta.total_seconds() / 3600
    return f"{h:.1f}h"


def _days_between(start, end) -> str | None:
    if start is None or end is None:
        return None
    delta = end - start
    return str(delta.days)


async def _breach_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(DataBreach).where(DataBreach.company_id == company_id).order_by(DataBreach.discovered_at.desc().nullslast()))
    breaches = res.scalars().all()
    items = []
    for b in breaches:
        within_72h = False
        if b.discovered_at:
            for notif in [b.dpa_notified_at, b.poverenik_notified_at, b.dpbi_notified_at]:
                if notif:
                    h = (notif - b.discovered_at).total_seconds() / 3600
                    if h <= 72:
                        within_72h = True
        items.append({
            "title": b.title,
            "occurred_at": b.occurred_at,
            "discovered_at": b.discovered_at,
            "breach_type": b.breach_type,
            "severity": b.severity,
            "status": b.status,
            "affected_records": b.affected_records,
            "notification_required": b.notification_required,
            "dpa_notified_at": b.dpa_notified_at,
            "individuals_notified_at": b.individuals_notified_at,
            "dpbi_notified_at": b.dpbi_notified_at,
            "dpbi_ref_number": b.dpbi_ref_number,
            "poverenik_notified_at": b.poverenik_notified_at,
            "poverenik_ref_number": b.poverenik_ref_number,
            "within_72h": within_72h,
        })
    return {"breaches": items}


async def _certin_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(Incident).where(Incident.company_id == company_id).order_by(Incident.detected_at.desc().nullslast()))
    incidents = res.scalars().all()
    items = []
    for i in incidents:
        within_6h = False
        hours_str = None
        if i.detected_at and i.certin_reported_at:
            h = (i.certin_reported_at - i.detected_at).total_seconds() / 3600
            within_6h = h <= 6
            hours_str = f"{h:.1f}h"
        items.append({
            "title": i.title,
            "detected_at": i.detected_at,
            "severity": i.severity,
            "status": i.status,
            "affected_systems": i.affected_systems,
            "certin_reported_at": i.certin_reported_at,
            "certin_ref_number": i.certin_ref_number,
            "within_6h": within_6h,
            "hours_to_report": hours_str,
        })
    return {"incidents": items}


async def _nis2_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(Incident).where(Incident.company_id == company_id).order_by(Incident.detected_at.desc().nullslast()))
    incidents = res.scalars().all()
    items = []
    for i in incidents:
        items.append({
            "title": i.title,
            "detected_at": i.detected_at,
            "severity": i.severity,
            "status": i.status,
            "nis2_early_warning_at": i.nis2_early_warning_at,
            "nis2_notified_at": i.nis2_notified_at,
            "nis2_final_report_at": i.nis2_final_report_at,
            "nis2_ref_number": i.nis2_ref_number,
        })
    return {"incidents": items}


async def _dsar_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(SubjectRequest).where(SubjectRequest.company_id == company_id).order_by(SubjectRequest.received_at.desc()))
    requests = res.scalars().all()
    items = []
    for r in requests:
        on_time = False
        days_taken = None
        if r.completed_at and r.received_at:
            delta = r.completed_at - r.received_at
            days_taken = str(delta.days)
            sla = {"gdpr": 30, "ccpa": 45, "lpdp": 30, "dpdp": 30}.get(r.regulation, 30)
            on_time = delta.days <= sla
        items.append({
            "requester_name": r.requester_name,
            "requester_email": r.requester_email,
            "request_type": r.request_type,
            "regulation": r.regulation,
            "received_at": r.received_at,
            "due_at": r.due_at,
            "status": r.status,
            "completed_at": r.completed_at,
            "on_time": on_time,
            "days_taken": days_taken,
        })
    return {"requests": items}


async def _mgmt_review_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(ManagementReview).where(ManagementReview.company_id == company_id).order_by(ManagementReview.review_date.desc()))
    reviews = res.scalars().all()
    items = []
    for r in reviews:
        action_items = r.action_items or []
        open_actions = sum(1 for a in action_items if not a.get("done"))
        items.append({
            "review_date": r.review_date,
            "attendees": r.attendees,
            "inputs_summary": r.inputs_summary,
            "decisions": r.decisions,
            "outcome": r.outcome,
            "next_review_date": r.next_review_date,
            "notes": r.notes,
            "open_action_items": open_actions,
        })
    return {"reviews": items}


async def _vendor_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(Vendor).where(Vendor.company_id == company_id).order_by(Vendor.name))
    vendors = res.scalars().all()
    items = []
    for v in vendors:
        items.append({
            "name": v.name,
            "category": v.category,
            "risk_level": v.risk_level,
            "soc2_certified": v.soc2_certified,
            "iso27001_certified": v.iso27001_certified,
            "hipaa_certified": v.hipaa_certified,
            "review_date": v.review_date,
            "website": v.website,
        })
    return {"vendors": items}


async def _training_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(TrainingRecord).where(TrainingRecord.company_id == company_id).order_by(TrainingRecord.due_date.asc().nullslast()))
    records = res.scalars().all()
    items = []
    for r in records:
        items.append({
            "assignee_email": r.assignee_email,
            "assignee_name": r.assignee_name,
            "title": r.title,
            "status": r.status,
            "due_date": r.due_date,
            "completed_at": r.completed_at,
            "quiz_score": r.quiz_score,
            "quiz_passed": r.quiz_passed,
        })
    return {"records": items}


async def _access_review_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    res = await db.execute(select(AccessReview).where(AccessReview.company_id == company_id).order_by(AccessReview.due_date.desc().nullslast()))
    reviews = res.scalars().all()
    items = []
    for r in reviews:
        items.append({
            "title": r.title,
            "period": r.period,
            "status": r.status,
            "due_date": r.due_date,
            "completed_at": r.completed_at,
            "users_reviewed": r.users_reviewed,
            "access_changes": r.access_changes,
            "scope": r.scope,
            "findings": r.findings,
        })
    return {"reviews": items}


_CONTEXT_BUILDERS = {
    "breach_notification": _breach_context,
    "certin_incident":     _certin_context,
    "nis2_incident":       _nis2_context,
    "dsar_log":            _dsar_context,
    "management_review":   _mgmt_review_context,
    "vendor_risk":         _vendor_context,
    "training_completion": _training_context,
    "access_review":       _access_review_context,
}


def _render_pdf(report_type: str, ctx: dict) -> bytes:
    from reports.specialized_reports import (
        render_access_review_report,
        render_breach_report,
        render_certin_report,
        render_dsar_report,
        render_mgmt_review_report,
        render_nis2_report,
        render_training_report,
        render_vendor_report,
    )
    renderers = {
        "breach_notification": render_breach_report,
        "certin_incident":     render_certin_report,
        "nis2_incident":       render_nis2_report,
        "dsar_log":            render_dsar_report,
        "management_review":   render_mgmt_review_report,
        "vendor_risk":         render_vendor_report,
        "training_completion": render_training_report,
        "access_review":       render_access_review_report,
    }
    renderer = renderers.get(report_type)
    if not renderer:
        raise ValueError(f"Unknown report type: {report_type}")
    return renderer(ctx)


async def generate_specialized_report(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    report_type: str,
    db: AsyncSession,
) -> None:
    from services.storage_service import upload_bytes

    report = (
        await db.execute(select(Report).where(Report.id == report_id, Report.company_id == company_id))
    ).scalar_one_or_none()

    if not report:
        raise ValueError("Report not found")

    try:
        company_name = await _get_company_name(company_id, db)
        now = datetime.now(timezone.utc)

        builder = _CONTEXT_BUILDERS.get(report_type)
        if not builder:
            raise ValueError(f"Unsupported report type: {report_type}")

        data = await builder(company_id, db)
        data["company_name"] = company_name
        data["generated_at"] = now.strftime("%B %d, %Y %H:%M UTC")

        pdf_bytes = _render_pdf(report_type, data)

        bucket = settings.storage_bucket or "reports"
        path = f"specialized-reports/{company_id}/{report_type}/{report_id}.pdf"
        upload_bytes(bucket, path, pdf_bytes, "application/pdf")

        meta = REPORT_META[report_type]
        report.status = "complete"
        report.generated_at = now
        report.file_url = f"/v1/reports/{report_id}/download?format=pdf"
        report.storage_bucket = bucket
        report.storage_path = path
        report.file_name = f"{report_type}.pdf"
        report.mime_type = "application/pdf"
        report.file_size = len(pdf_bytes)
        await db.commit()

    except Exception:
        logger.exception("Specialized report generation failed: report_id=%s type=%s", report_id, report_type)
        report.status = "error"
        await db.commit()
        raise
