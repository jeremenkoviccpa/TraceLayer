"""Outbound vendor security questionnaire management (TPRM)."""
import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.company import Company
from models.user import User
from models.vendor import Vendor
from models.vendor_questionnaire import VendorQuestionnaire
from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendor-questionnaires", tags=["vendor_questionnaires"])

# IT-focused security questionnaire template (12 questions)
DEFAULT_QUESTIONS = [
    {"id": "q1",  "text": "Do you hold a SOC 2 Type II, ISO 27001, or equivalent security certification? If yes, please describe which certification(s) and when they were last audited.", "required": True},
    {"id": "q2",  "text": "Is all customer data encrypted at rest (AES-256 or equivalent) and in transit (TLS 1.2+)?", "required": True},
    {"id": "q3",  "text": "Do you have a formal Incident Response Plan? What is your contractual SLA for notifying customers of a security incident or data breach?", "required": True},
    {"id": "q4",  "text": "Do you conduct annual penetration testing by an independent third party? When was the most recent test and what was the overall outcome?", "required": True},
    {"id": "q5",  "text": "Is multi-factor authentication (MFA) enforced for all employee accounts that access production systems and customer data?", "required": True},
    {"id": "q6",  "text": "Do you have a formal vulnerability management programme including scheduled scanning, patch management SLAs, and CVE tracking?", "required": True},
    {"id": "q7",  "text": "Are background checks conducted on employees and contractors with access to customer data prior to onboarding?", "required": True},
    {"id": "q8",  "text": "Do you maintain a Business Continuity and Disaster Recovery plan? What are your documented RTO and RPO targets?", "required": True},
    {"id": "q9",  "text": "What is your data retention policy? How is customer data securely deleted upon contract termination and within what timeframe?", "required": True},
    {"id": "q10", "text": "Do you use sub-processors or third-party vendors that access, process, or store our data? If yes, please provide a list of key sub-processors.", "required": True},
    {"id": "q11", "text": "Are all employees with access to customer data required to complete annual security awareness training? How is completion tracked?", "required": True},
    {"id": "q12", "text": "Are you willing to sign a Data Processing Agreement (DPA)? Do you currently have standard DPA terms available?", "required": True},
]


class SendQuestionnaireRequest(BaseModel):
    vendor_id: Optional[uuid.UUID] = None
    vendor_name: str
    sent_to_email: str
    due_days: int = 14


class SubmitResponseRequest(BaseModel):
    responses: dict  # {question_id: answer_text}
    vendor_contact_name: Optional[str] = None


def _to_response(q: VendorQuestionnaire) -> dict:
    now = datetime.now(timezone.utc)
    is_overdue = (
        q.status == "sent" and q.due_date is not None and q.due_date < now
    )
    return {
        "id": str(q.id),
        "vendor_id": str(q.vendor_id) if q.vendor_id else None,
        "vendor_name": q.vendor_name,
        "sent_to_email": q.sent_to_email,
        "token": q.token,
        "status": "overdue" if is_overdue else q.status,
        "questions": q.questions,
        "responses": q.responses,
        "sent_at": q.sent_at,
        "due_date": q.due_date,
        "completed_at": q.completed_at,
        "created_at": q.created_at,
        "response_url": f"{settings.app_frontend_url}/vendor-questionnaire/{q.token}",
    }


@router.get("")
async def list_questionnaires(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VendorQuestionnaire)
        .where(VendorQuestionnaire.company_id == current_user.company_id)
        .order_by(VendorQuestionnaire.sent_at.desc())
    )
    return [_to_response(q) for q in result.scalars().all()]


@router.get("/by-vendor/{vendor_id}")
async def list_vendor_questionnaires(
    vendor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VendorQuestionnaire)
        .where(
            VendorQuestionnaire.company_id == current_user.company_id,
            VendorQuestionnaire.vendor_id == vendor_id,
        )
        .order_by(VendorQuestionnaire.sent_at.desc())
    )
    return [_to_response(q) for q in result.scalars().all()]


@router.post("", status_code=201)
async def send_questionnaire(
    body: SendQuestionnaireRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = (await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )).scalar_one_or_none()
    company_name = company.name if company else "Our Company"

    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    due_date = now + timedelta(days=body.due_days)

    q = VendorQuestionnaire(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        vendor_id=body.vendor_id,
        vendor_name=body.vendor_name,
        sent_to_email=body.sent_to_email,
        token=token,
        questions=DEFAULT_QUESTIONS,
        sent_at=now,
        due_date=due_date,
        created_by_id=current_user.id,
        created_at=now,
    )
    db.add(q)
    await db.flush()

    # Send email to vendor
    try:
        from services.email_service import send_vendor_questionnaire
        response_url = f"{settings.app_frontend_url}/vendor-questionnaire/{token}"
        send_vendor_questionnaire(
            to=body.sent_to_email,
            vendor_name=body.vendor_name,
            company_name=company_name,
            sender_name=current_user.full_name or current_user.email,
            response_url=response_url,
            due_date=due_date,
            question_count=len(DEFAULT_QUESTIONS),
        )
    except Exception as exc:
        logger.warning("Failed to send vendor questionnaire email: %s", exc)

    await db.commit()
    await db.refresh(q)
    await log_action(db, current_user.company_id, "vendor_questionnaire.sent",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="vendor_questionnaire", resource_id=str(q.id),
                     metadata={"vendor_name": body.vendor_name, "sent_to": body.sent_to_email})
    return _to_response(q)


# ── Public endpoint (no auth) — vendor fills out the form ────────────────────

@router.get("/public/{token}")
async def get_public_questionnaire(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for vendor to retrieve questionnaire. No auth required."""
    q = (await db.execute(
        select(VendorQuestionnaire).where(VendorQuestionnaire.token == token)
    )).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found or link has expired")

    company = (await db.execute(
        select(Company).where(Company.id == q.company_id)
    )).scalar_one_or_none()

    return {
        "vendor_name": q.vendor_name,
        "company_name": company.name if company else "Our Company",
        "questions": q.questions,
        "status": q.status,
        "due_date": q.due_date,
        "already_completed": q.status == "completed",
        "existing_responses": q.responses if q.status == "completed" else {},
    }


@router.post("/public/{token}/respond")
async def submit_questionnaire_response(
    token: str,
    body: SubmitResponseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint for vendor to submit their responses. No auth required."""
    q = (await db.execute(
        select(VendorQuestionnaire).where(VendorQuestionnaire.token == token)
    )).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    if q.status == "completed":
        raise HTTPException(status_code=409, detail="This questionnaire has already been completed")

    now = datetime.now(timezone.utc)
    q.responses = body.responses
    if body.vendor_contact_name:
        q.responses["_contact_name"] = body.vendor_contact_name
    q.status = "completed"
    q.completed_at = now
    await db.commit()

    return {"detail": "Thank you. Your security questionnaire has been submitted successfully."}
