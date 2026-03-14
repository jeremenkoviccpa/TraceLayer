"""
Audit logging service.

Call log_action() from any endpoint to record an auditable event.
Uses its own DB session so a failure never aborts the main request.
"""
import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Human-readable labels for the frontend
ACTION_LABELS = {
    "user.login": "Signed in",
    "user.logout": "Signed out",
    "user.password_changed": "Changed password",
    "user.email_verified": "Verified email",
    "integration.connected": "Connected integration",
    "integration.disconnected": "Disconnected integration",
    "integration.collect_triggered": "Triggered evidence collection",
    "report.generated": "Generated report",
    "report.downloaded": "Downloaded report",
    "member.invited": "Invited team member",
    "member.removed": "Removed team member",
    "invite.revoked": "Revoked invitation",
    "company.updated": "Updated company settings",
    "plan.upgraded": "Upgraded to Growth plan",
    "plan.downgraded": "Downgraded to Free plan",
}


async def log_action(
    db: AsyncSession,
    company_id: uuid.UUID,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Append an audit log entry. Swallows all exceptions to never break callers."""
    try:
        entry = AuditLog(
            company_id=company_id,
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata,
            ip_address=ip_address,
        )
        db.add(entry)
        await db.flush()
    except Exception:
        logger.warning("audit_service: failed to log action=%s", action, exc_info=True)
