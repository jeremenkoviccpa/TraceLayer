"""
Email delivery via Resend.

Set RESEND_API_KEY in environment to enable.
If the key is absent, emails are logged to stdout instead (dev/test mode).
"""
import logging

from core.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> None:
    if not settings.resend_api_key:
        logger.info("EMAIL (no RESEND_API_KEY) to=%s subject=%s", to, subject)
        return

    import resend
    resend.api_key = settings.resend_api_key
    resend.Emails.send({
        "from": settings.email_from,
        "to": [to],
        "subject": subject,
        "html": html,
    })


def send_invite_email(to: str, invite_url: str, company_name: str, invited_by: str) -> None:
    subject = f"You've been invited to join {company_name} on TraceLayer"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px">You're invited to TraceLayer</h2>
      <p style="color:#555;margin:0 0 24px">
        <strong>{invited_by}</strong> has invited you to join
        <strong>{company_name}</strong> on TraceLayer — a continuous compliance
        evidence platform.
      </p>
      <a href="{invite_url}"
         style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;
                padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px">
        Accept invitation
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        This link expires in 7 days. If you weren't expecting this, you can ignore it.
      </p>
    </div>
    """
    _send(to, subject, html)


def send_password_changed_email(to: str) -> None:
    subject = "Your TraceLayer password was changed"
    html = """
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px">Password changed</h2>
      <p style="color:#555">
        Your TraceLayer account password was just changed. If you did this, no action
        is needed. If you didn't, please contact your admin immediately.
      </p>
    </div>
    """
    _send(to, subject, html)
