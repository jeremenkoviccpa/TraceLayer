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


def send_welcome_email(to: str, company_name: str) -> None:
    subject = "Welcome to TraceLayer"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px">Welcome to TraceLayer</h2>
      <p style="color:#555;margin:0 0 16px">
        Your account for <strong>{company_name}</strong> is ready.
        Connect your first integration to start collecting compliance evidence automatically.
      </p>
      <a href="{settings.frontend_url}/onboarding"
         style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;
                padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px">
        Get started
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        TraceLayer — Continuous compliance evidence collection.
      </p>
    </div>
    """
    _send(to, subject, html)


def send_collection_failure_email(to: str, integration_type: str, error: str) -> None:
    subject = f"TraceLayer: {integration_type} collection failed"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px;color:#dc2626">Collection failed</h2>
      <p style="color:#555;margin:0 0 16px">
        The scheduled evidence collection for <strong>{integration_type}</strong> failed.
        Your compliance score may be out of date until this is resolved.
      </p>
      <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px;margin-bottom:24px">
        <code style="font-size:12px;color:#991b1b">{error[:300]}</code>
      </div>
      <a href="{settings.frontend_url}/integrations"
         style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;
                padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px">
        Check integrations
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        You can reconnect the integration or trigger a manual collection from the Integrations page.
      </p>
    </div>
    """
    _send(to, subject, html)


def send_password_reset_email(to: str, reset_url: str) -> None:
    subject = "Reset your TraceLayer password"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px">Reset your password</h2>
      <p style="color:#555;margin:0 0 24px">
        We received a request to reset the password for your TraceLayer account.
        Click the button below — this link expires in 1 hour.
      </p>
      <a href="{reset_url}"
         style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;
                padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px">
        Reset password
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        If you didn't request this, you can safely ignore this email.
        Your password will not change.
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
