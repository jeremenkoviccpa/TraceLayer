import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.company import Company
from models.evidence import Evidence
from models.training import TrainingRecord
from models.user import User
from schemas.training import TrainingCreate, TrainingResponse, TrainingUpdate

router = APIRouter(prefix="/training", tags=["training"])

PASS_THRESHOLD = 80  # % required to pass


# ── Quiz content ──────────────────────────────────────────────────────────────
# Each entry: {"q": str, "opts": [str, str, str, str], "ans": int (0-indexed)}

_Q: dict[str, list[dict]] = {
    "security awareness": [
        {"q": "What should you do if you receive an email asking for your password?", "opts": ["Provide it as requested — it's probably IT", "Report it to IT security and delete the email", "Forward it to colleagues to verify", "Reply asking for their employee ID first"], "ans": 1},
        {"q": "What is phishing?", "opts": ["A legitimate IT password-reset technique", "A fraudulent attempt to steal credentials via fake emails or websites", "A type of firewall configuration", "A network monitoring protocol"], "ans": 1},
        {"q": "What is the purpose of multi-factor authentication (MFA)?", "opts": ["To allow faster password recovery", "To speed up the login process", "To add a second verification step beyond just a password", "To automatically sync security settings across devices"], "ans": 2},
        {"q": "What should you do if you accidentally click a suspicious link?", "opts": ["Ignore it and continue working", "Disconnect from the network immediately and report to IT", "Clear your browser cache and carry on", "Change only your email password"], "ans": 1},
        {"q": "Which of the following is an example of a strong password?", "opts": ["password123", "YourName2024", "Tr@c3L@y3r!9#Xz", "QWERTY"], "ans": 2},
        {"q": "What is social engineering?", "opts": ["Building company social media profiles", "Manipulating people into revealing confidential information", "Setting up employee social channels", "A type of network architecture"], "ans": 1},
        {"q": "What does 'need-to-know' mean in information security?", "opts": ["All employees should know all company information", "Access to information should be limited to those who need it for their role", "Managers must be informed of all employee activities", "All company data must be publicly documented"], "ans": 1},
        {"q": "Which of the following is the safest way to handle a USB drive found in a public place?", "opts": ["Plug it in to see who it belongs to", "Hand it to IT security without plugging it in", "Keep it — finders keepers", "Plug it into an offline computer only"], "ans": 1},
    ],
    "hipaa": [
        {"q": "What does PHI stand for under HIPAA?", "opts": ["Personal Handling Information", "Protected Health Information", "Private Healthcare Identity", "Processed Health Index"], "ans": 1},
        {"q": "When may PHI be shared without a patient's written authorization?", "opts": ["Whenever a colleague asks", "For treatment, payment, or healthcare operations", "For marketing purposes only", "Only when the patient is deceased"], "ans": 1},
        {"q": "What is the HIPAA Minimum Necessary Standard?", "opts": ["Only the minimum number of staff should be hired", "Only access or disclose the minimum amount of PHI needed for the task", "Retain records for the minimum time required", "Encrypt the minimum required number of devices"], "ans": 1},
        {"q": "How quickly must a HIPAA breach affecting 500+ individuals be reported to HHS?", "opts": ["Within 24 hours", "Within 30 days", "Within 60 days of discovery", "Within 7 days"], "ans": 2},
        {"q": "Which of the following is NOT an example of PHI?", "opts": ["A patient's name and diagnosis", "A patient's medical record number", "General population health statistics with no identifiers", "A patient's email address linked to their care"], "ans": 2},
        {"q": "What is the HIPAA Security Rule primarily concerned with?", "opts": ["Physical security of hospital buildings", "Protecting electronic PHI (ePHI) through administrative, physical, and technical safeguards", "Patient billing procedures", "Employee health benefits"], "ans": 1},
        {"q": "What should you do if you discover a potential HIPAA breach?", "opts": ["Wait to see if anyone notices", "Immediately report it to your Privacy Officer", "Investigate fully on your own before reporting", "Only report if patient data was definitely accessed"], "ans": 1},
        {"q": "Which of the following is a HIPAA-compliant way to communicate PHI?", "opts": ["Standard unencrypted email", "Encrypted email or secure messaging platforms", "Text messages on personal phones", "Public cloud storage links"], "ans": 1},
    ],
    "phishing": [
        {"q": "Which of the following is a common sign of a phishing email?", "opts": ["It comes from your CEO's exact email address", "Urgent language demanding immediate action, with a suspicious link", "It is addressed to your full name", "It asks you to attend a scheduled meeting"], "ans": 1},
        {"q": "A legitimate organisation will NEVER ask you to do which of the following via email?", "opts": ["Confirm a scheduled meeting time", "Provide your password or full account credentials", "Reset your password via their official website", "Verify a recent purchase you made"], "ans": 1},
        {"q": "What is spear phishing?", "opts": ["A phishing attack targeting fishing industry companies", "A highly targeted phishing attack personalised for a specific individual or organisation", "A phishing attack using phone calls", "A technique to test employee security awareness at random"], "ans": 1},
        {"q": "How can you verify if an email link is safe before clicking?", "opts": ["Click it quickly and see what loads", "Hover over the link to preview the actual URL destination", "Check whether the email font looks professional", "Forward it to a colleague to click first"], "ans": 1},
        {"q": "What is a vishing attack?", "opts": ["A phishing attack via video call", "Voice phishing — fraudulent phone calls to extract sensitive information", "A visual phishing attack using fake logos", "A virus disguised as a phishing email"], "ans": 1},
        {"q": "Which URL is most likely to be a phishing attempt for a bank?", "opts": ["https://www.barclays.co.uk/login", "https://barclays-secure-login.com/account", "https://online.barclays.co.uk/portal", "https://auth.barclays.co.uk/signin"], "ans": 1},
        {"q": "What should you do with a suspected phishing email?", "opts": ["Delete it immediately without telling anyone", "Report it to IT security using the phishing report button, then delete it", "Reply to ask if it is legitimate", "Forward it to colleagues to warn them"], "ans": 1},
        {"q": "What is smishing?", "opts": ["Phishing via SMTP email servers", "Phishing via SMS text messages", "A social media phishing technique", "Phishing using malicious QR codes"], "ans": 1},
    ],
    "password": [
        {"q": "What is the minimum recommended length for a secure password?", "opts": ["6 characters", "8 characters", "12 characters or more", "4 characters with a special symbol"], "ans": 2},
        {"q": "What is a password manager?", "opts": ["A person in IT who resets passwords", "Software that securely stores and generates unique passwords for each account", "A browser feature that stores passwords in plain text", "A policy document listing all company passwords"], "ans": 1},
        {"q": "What is the principle of least privilege?", "opts": ["Staff should have the least enjoyable tasks first", "Users should only have access to the resources they need to perform their job", "Passwords should be as short as possible", "Junior employees get fewer software licences"], "ans": 1},
        {"q": "When should you share your login credentials with a colleague?", "opts": ["When they need temporary access to your account", "When IT helpdesk asks via email", "Never — credentials are personal and must not be shared", "Only when your line manager approves in writing"], "ans": 2},
        {"q": "What should you do when you leave your workstation temporarily?", "opts": ["Leave it as it is — you will be back shortly", "Lock your screen (Win+L or Cmd+Ctrl+Q)", "Log out completely every time", "Put a sticky note warning others not to use it"], "ans": 1},
        {"q": "How often should you change passwords for critical systems?", "opts": ["Never, if they are strong enough", "Every day", "Only when a breach is suspected or after a set policy period", "Annually on your birthday"], "ans": 2},
        {"q": "What is single sign-on (SSO)?", "opts": ["A policy requiring one unique password per account", "A system allowing users to log in once to access multiple applications", "A type of two-factor authentication", "A hardware security key"], "ans": 1},
        {"q": "Which of the following is NOT a recommended password practice?", "opts": ["Using a unique password for every account", "Enabling MFA wherever possible", "Using the same password everywhere for convenience", "Using a passphrase of several random words"], "ans": 2},
    ],
    "data handling": [
        {"q": "What does data classification mean?", "opts": ["Organising files into folders", "Categorising data by its sensitivity level to apply appropriate protections", "Compressing data to save storage", "Classifying data by file format"], "ans": 1},
        {"q": "Which type of data typically requires the highest level of protection?", "opts": ["Publicly available marketing materials", "Internal staff memos", "Personally identifiable information (PII) and financial records", "Employee lunch preference surveys"], "ans": 2},
        {"q": "How should confidential paper documents be disposed of?", "opts": ["Placed in a standard recycling bin", "Cross-shredded or placed in a secure destruction bin", "Torn in half and binned", "Left for the office cleaner to handle"], "ans": 1},
        {"q": "What is data minimisation?", "opts": ["Using the smallest possible file sizes", "Only collecting and retaining personal data that is necessary for the stated purpose", "Deleting all data after one year", "Minimising the number of databases used"], "ans": 1},
        {"q": "When sending sensitive data by email, what should you do?", "opts": ["Send it as a plain text attachment", "Encrypt the attachment and share the key via a separate channel", "Use your personal email for extra security", "CC your manager as a record"], "ans": 1},
        {"q": "What does encryption protect against?", "opts": ["Hardware failure", "Unauthorised parties reading data even if they obtain it", "Accidental file deletion", "Slow network speeds"], "ans": 1},
        {"q": "What is a data retention policy?", "opts": ["A rule about how fast data must be processed", "Rules defining how long data is kept and when it must be securely deleted", "A policy about how much data can be stored", "A guideline for organising shared drives"], "ans": 1},
        {"q": "What should you do before transferring data to a personal device?", "opts": ["Check if the file is small enough", "Obtain explicit authorisation and ensure the device meets security requirements", "Copy only after business hours", "It is always fine for work-from-home use"], "ans": 1},
    ],
    "incident response": [
        {"q": "What is a security incident?", "opts": ["Any scheduled system maintenance window", "An event that threatens the confidentiality, integrity, or availability of information", "A routine software update that fails", "A planned penetration test"], "ans": 1},
        {"q": "Who should you notify first when you discover a security incident?", "opts": ["Your personal lawyer", "Your direct line manager via personal SMS", "Your organisation's IT security team or incident response contact", "The press"], "ans": 2},
        {"q": "What should you NOT do when responding to a suspected security breach?", "opts": ["Preserve evidence by not altering affected systems", "Document what you observed with timestamps", "Attempt to clean up the breach yourself without informing security", "Report it immediately to the IR team"], "ans": 2},
        {"q": "What is the first step in the incident response lifecycle?", "opts": ["Eradication", "Preparation", "Recovery", "Lessons learned"], "ans": 1},
        {"q": "Which of the following is a sign that your workstation may be infected with malware?", "opts": ["Your computer runs faster than usual", "Unexpected pop-ups, slow performance, or programmes launching on their own", "You receive an email from IT asking you to update software", "Your screen brightness changes automatically"], "ans": 1},
        {"q": "What is a tabletop exercise in incident response?", "opts": ["A physical security drill performed in a server room", "A discussion-based simulation where teams walk through a hypothetical incident scenario", "A test of backup restoration procedures", "An automated vulnerability scan"], "ans": 1},
        {"q": "What does RTO stand for in business continuity?", "opts": ["Required Training Objective", "Recovery Time Objective — the maximum acceptable downtime after an incident", "Regulatory Testing Order", "Risk Threshold Override"], "ans": 1},
        {"q": "What is containment in incident response?", "opts": ["Deleting all infected files immediately", "Isolating affected systems to prevent the incident from spreading further", "Notifying all employees company-wide", "Restoring from backup immediately"], "ans": 1},
    ],
    "soc 2": [
        {"q": "What does SOC 2 stand for?", "opts": ["Security Operations Centre 2", "System and Organisation Controls 2", "Software Operations Compliance 2", "Secure Online Commerce 2"], "ans": 1},
        {"q": "Which of the following is NOT one of the five SOC 2 Trust Service Criteria?", "opts": ["Security", "Availability", "Profitability", "Confidentiality"], "ans": 2},
        {"q": "What is the difference between SOC 2 Type I and Type II?", "opts": ["Type I is for small companies; Type II is for enterprises", "Type I evaluates design at a point in time; Type II evaluates operating effectiveness over a period", "Type I covers all five criteria; Type II covers only Security", "Type I is cheaper; Type II requires a third party"], "ans": 1},
        {"q": "Who is qualified to conduct an official SOC 2 audit?", "opts": ["Any certified ISO 27001 consultant", "A licensed CPA firm specialising in SOC audits", "Your internal IT security team", "Any independent security consultant"], "ans": 1},
        {"q": "What is the typical observation period for a SOC 2 Type II audit?", "opts": ["1 week", "1 month", "6 to 12 months", "2 years"], "ans": 2},
        {"q": "What does the Availability criterion in SOC 2 focus on?", "opts": ["Whether staff are available to respond to audit requests", "Whether systems are available for operation and use as agreed with customers", "Availability of audit reports to the public", "The availability of encryption keys"], "ans": 1},
        {"q": "What is a control in the context of SOC 2?", "opts": ["A management reporting dashboard", "A policy, procedure, or mechanism that mitigates a specific risk", "A user permission setting", "A type of firewall rule"], "ans": 1},
        {"q": "Why do customers request SOC 2 reports from vendors?", "opts": ["To get discounts on software licences", "To assess whether the vendor's security controls are effective before sharing data", "To verify the vendor is a registered business", "For tax compliance purposes"], "ans": 1},
    ],
    "code of conduct": [
        {"q": "What is an Acceptable Use Policy (AUP)?", "opts": ["A policy about acceptable office behaviour at lunch", "Rules governing how employees may use company systems, devices, and data", "A guideline for acceptable salary negotiations", "A policy for use of the company gym"], "ans": 1},
        {"q": "Which of the following is generally NOT permitted on company devices?", "opts": ["Accessing work email", "Installing unauthorised personal software or games", "Using approved cloud collaboration tools", "Attending video calls from home"], "ans": 1},
        {"q": "What should you do if you discover a colleague violating the code of conduct?", "opts": ["Ignore it — it is not your concern", "Report it through the appropriate channel such as HR or an ethics hotline", "Confront them publicly", "Post about it on social media"], "ans": 1},
        {"q": "Can you use company-licensed software for personal projects?", "opts": ["Yes, always — you paid for it with your salary", "Only if no one finds out", "No — company licences are for business use only unless explicitly permitted", "Yes, but only outside business hours"], "ans": 2},
        {"q": "What is an insider threat?", "opts": ["A customer who complains loudly", "A risk posed by current or former employees, contractors, or partners misusing their access", "A competitor who infiltrates company events", "An external hacker who obtains employee login credentials"], "ans": 1},
        {"q": "When is it appropriate to post confidential company information on social media?", "opts": ["When it would generate positive PR", "When your manager verbally approves it", "Never — confidential information must not be shared on personal or public channels", "Only if you make the post private"], "ans": 2},
        {"q": "What is the purpose of a conflict of interest policy?", "opts": ["To prevent employees from working overtime", "To ensure personal interests do not improperly influence business decisions", "To resolve salary disputes between colleagues", "To stop employees from having side projects"], "ans": 1},
        {"q": "Which of the following is an appropriate use of company email?", "opts": ["Signing up for personal newsletters", "Communicating with customers and colleagues on business matters", "Registering for personal online shopping accounts", "Mass-forwarding chain emails"], "ans": 1},
    ],
}

# Fallback to general security awareness
_Q["default"] = _Q["security awareness"]


def _get_questions(title: str) -> list[dict]:
    t = title.lower()
    for key, questions in _Q.items():
        if key == "default":
            continue
        if key in t or any(word in t for word in key.split()):
            return questions
    return _Q["default"]


# Evidence control mapping by title keyword
_EVIDENCE_CONTROLS = {
    "hipaa": ("hipaa_privacy", "HIPAA.164.308"),
    "soc 2": ("training", "CC1.4"),
    "phishing": ("training", "CC6.1"),
    "password": ("training", "CC6.1"),
    "incident": ("training", "CC7.3"),
    "default": ("training", "CC1.4"),
}


def _evidence_control(title: str) -> tuple[str, str]:
    t = title.lower()
    for key, val in _EVIDENCE_CONTROLS.items():
        if key == "default":
            continue
        if key in t:
            return val
    return _EVIDENCE_CONTROLS["default"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_response(t: TrainingRecord) -> TrainingResponse:
    return TrainingResponse(
        id=str(t.id),
        company_id=str(t.company_id),
        assignee_email=t.assignee_email,
        assignee_name=t.assignee_name,
        title=t.title,
        description=t.description,
        due_date=t.due_date,
        completed_at=t.completed_at,
        status=t.status,
        annual=t.annual,
        notes=t.notes,
        auto_detected=t.auto_detected,
        detection_key=t.detection_key,
        completion_token=t.completion_token,
        quiz_score=t.quiz_score,
        quiz_passed=t.quiz_passed,
        quiz_attempts=t.quiz_attempts,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _compute_status(record: TrainingRecord) -> str:
    if record.completed_at:
        return "completed"
    if record.due_date and record.due_date < datetime.now(timezone.utc):
        return "overdue"
    return "pending"


# ── Company auth endpoints ────────────────────────────────────────────────────

@router.get("", response_model=list[TrainingResponse])
async def list_training(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord)
        .where(TrainingRecord.company_id == current_user.company_id)
        .order_by(TrainingRecord.created_at.desc())
    )
    records = result.scalars().all()
    for r in records:
        computed = _compute_status(r)
        if r.status != computed and r.status != "completed":
            r.status = computed
    if any(r.status == "overdue" for r in records):
        await db.commit()
    return [_to_response(r) for r in records]


@router.post("", response_model=TrainingResponse, status_code=201)
async def create_training(
    body: TrainingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = TrainingRecord(
        company_id=current_user.company_id,
        assignee_email=body.assignee_email,
        assignee_name=body.assignee_name,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        annual=body.annual,
        notes=body.notes,
        status="pending",
        completion_token=secrets.token_urlsafe(32),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.patch("/{record_id}", response_model=TrainingResponse)
async def update_training(
    record_id: uuid.UUID,
    body: TrainingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.id == record_id,
            TrainingRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    if "status" not in body.model_dump(exclude_unset=True):
        record.status = _compute_status(record)

    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.delete("/{record_id}", status_code=204)
async def delete_training(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.id == record_id,
            TrainingRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    await db.delete(record)
    await db.commit()


@router.post("/detect", status_code=200)
async def trigger_training_detection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin access required")

    from services.auto_detector import run_training_detection_for_company
    created = await run_training_detection_for_company(db, current_user.company_id)
    return {"created": created}


# ── Public quiz endpoints (no auth — token in URL) ────────────────────────────

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: list[str]


class QuizPayload(BaseModel):
    training_id: str
    title: str
    assignee_name: Optional[str]
    assignee_email: str
    company_name: str
    already_passed: bool
    questions: list[QuizQuestion]


class QuizSubmit(BaseModel):
    answers: dict[str, int]  # {"0": 2, "1": 0, ...} — question index → chosen option index


class QuizResult(BaseModel):
    passed: bool
    score: int
    correct: int
    total: int
    completion_token: str


class CertificateData(BaseModel):
    title: str
    assignee_name: str
    assignee_email: str
    company_name: str
    completed_at: str
    score: int


@router.get("/take/{token}", response_model=QuizPayload)
async def get_quiz(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRecord).where(TrainingRecord.completion_token == token)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training link not found")

    company = await db.get(Company, record.company_id)
    company_name = company.name if company else "Your Company"

    questions = _get_questions(record.title)
    quiz_questions = [
        QuizQuestion(id=i, question=q["q"], options=q["opts"])
        for i, q in enumerate(questions)
    ]

    return QuizPayload(
        training_id=str(record.id),
        title=record.title,
        assignee_name=record.assignee_name,
        assignee_email=record.assignee_email,
        company_name=company_name,
        already_passed=record.quiz_passed,
        questions=quiz_questions,
    )


@router.post("/take/{token}/submit", response_model=QuizResult)
async def submit_quiz(token: str, body: QuizSubmit, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRecord).where(TrainingRecord.completion_token == token)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training link not found")

    questions = _get_questions(record.title)
    total = len(questions)
    correct = sum(
        1 for i, q in enumerate(questions)
        if body.answers.get(str(i)) == q["ans"]
    )
    score = round(correct / total * 100) if total else 0
    passed = score >= PASS_THRESHOLD

    record.quiz_attempts = (record.quiz_attempts or 0) + 1
    record.quiz_score = score

    if passed and not record.quiz_passed:
        record.quiz_passed = True
        record.completed_at = datetime.now(timezone.utc)
        record.status = "completed"

        # Auto-create evidence record
        integration, control = _evidence_control(record.title)
        try:
            evidence = Evidence(
                company_id=record.company_id,
                integration=integration,
                control=control,
                evidence_type="training_completion",
                source_id=str(record.id),
                timestamp=record.completed_at,
                data={
                    "title": record.title,
                    "assignee_email": record.assignee_email,
                    "assignee_name": record.assignee_name,
                    "score": score,
                    "attempts": record.quiz_attempts,
                    "completed_at": record.completed_at.isoformat(),
                },
            )
            db.add(evidence)
        except Exception:
            pass  # Don't fail quiz submission if evidence creation fails

    await db.commit()
    await db.refresh(record)

    return QuizResult(
        passed=passed,
        score=score,
        correct=correct,
        total=total,
        completion_token=token,
    )


@router.get("/certificate/{token}", response_model=CertificateData)
async def get_certificate(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRecord).where(TrainingRecord.completion_token == token)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Certificate not found")
    if not record.quiz_passed:
        raise HTTPException(status_code=403, detail="Training not yet completed")

    company = await db.get(Company, record.company_id)
    company_name = company.name if company else "Your Company"

    return CertificateData(
        title=record.title,
        assignee_name=record.assignee_name or record.assignee_email,
        assignee_email=record.assignee_email,
        company_name=company_name,
        completed_at=record.completed_at.isoformat() if record.completed_at else "",
        score=record.quiz_score or 0,
    )
