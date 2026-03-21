"""
Email delivery via Resend.

Set RESEND_API_KEY in environment to enable.
If the key is absent, emails are logged to stdout instead (dev/test mode).
"""
import logging

from core.config import settings

logger = logging.getLogger(__name__)


# ── Brand constants ───────────────────────────────────────────────────────────
_BRAND       = "#0f766e"   # brand-600 teal — primary CTA
_BRAND_LIGHT = "#f0fdfa"   # brand-50
_BRAND_BORDER= "#ccfbf1"   # brand-100
_TEXT_HEAD   = "#1e293b"   # slate-800
_TEXT_BODY   = "#475569"   # slate-600
_TEXT_MUTED  = "#94a3b8"   # slate-400
_RED         = "#dc2626"   # danger / security alerts
_RED_BG      = "#fef2f2"
_RED_BORDER  = "#fecaca"


def _layout(body_html: str, footer_note: str = "") -> str:
    """Wrap content in the standard TraceLayer branded email shell."""
    footer = footer_note or (
        f'TraceLayer &nbsp;&middot;&nbsp; '
        f'<a href="mailto:support@tracelayer.it.com" '
        f'style="color:{_TEXT_MUTED};text-decoration:none;">support@tracelayer.it.com</a>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f1f5f9;">
    <tr><td align="center" style="padding:40px 16px 32px;">
      <table width="560" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;width:100%;">

        <!-- Wordmark -->
        <tr>
          <td style="padding:0 0 20px 4px;">
            <span style="font-size:21px;font-weight:800;color:{_BRAND};letter-spacing:-0.5px;">TraceLayer</span>
          </td>
        </tr>

        <!-- Card -->
        <tr>
          <td style="background:#ffffff;border-radius:16px;padding:36px 40px;border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
            {body_html}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td align="center" style="padding:24px 0 0;font-size:12px;color:{_TEXT_MUTED};line-height:1.7;">
            {footer}
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _btn(url: str, label: str, color: str = _BRAND) -> str:
    """Render a full-width-safe CTA button."""
    return (
        f'<a href="{url}" style="display:inline-block;background:{color};color:#ffffff;'
        f'text-decoration:none;padding:13px 28px;border-radius:8px;font-weight:700;'
        f'font-size:15px;letter-spacing:-0.1px;">{label}</a>'
    )


def _send(to: str, subject: str, html: str, text: str = "") -> None:
    if not settings.resend_api_key:
        logger.info("EMAIL (no RESEND_API_KEY) to=%s subject=%s", to, subject)
        return

    import resend

    resend.api_key = settings.resend_api_key
    payload: dict = {
        "from": settings.email_from,
        "reply_to": "support@tracelayer.it.com",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    try:
        result = resend.Emails.send(payload)
        logger.info("EMAIL sent: to=%s subject=%s id=%s", to, subject, result)
    except Exception:
        logger.exception("EMAIL failed: to=%s subject=%s from=%s", to, subject, settings.email_from)
        raise


def send_invite_email(to: str, invite_url: str, company_name: str, invited_by: str) -> None:
    subject = f"You've been invited to join {company_name} on TraceLayer"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">You've been invited</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;font-size:15px;line-height:1.6;">
        <strong>{invited_by}</strong> has invited you to join <strong>{company_name}</strong>
        on TraceLayer — automated compliance evidence collection for SOC 2, ISO 27001, GDPR and more.
      </p>
      {_btn(invite_url, "Accept invitation")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:24px 0 0;">
        This link expires in 7 days. If you weren't expecting this, you can safely ignore it.
      </p>
    """
    _send(to, subject, _layout(body))


def send_welcome_email(to: str, company_name: str) -> None:
    subject = "Welcome to TraceLayer"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Welcome to TraceLayer</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 20px;font-size:15px;line-height:1.6;">
        Your account for <strong>{company_name}</strong> is ready. Connect your first integration
        and TraceLayer will start collecting compliance evidence automatically — no manual work needed.
      </p>
      <div style="background:{_BRAND_LIGHT};border:1.5px solid {_BRAND_BORDER};border-radius:12px;padding:18px 22px;margin:0 0 28px;">
        <p style="margin:0 0 10px;font-weight:700;color:{_BRAND};font-size:13px;text-transform:uppercase;letter-spacing:0.06em;">What you can do right now</p>
        <table cellpadding="0" cellspacing="0" border="0" width="100%">
          <tr><td style="padding:4px 0;font-size:14px;color:#065f46;">✓ &nbsp;Connect GitHub, AWS, Slack and 20+ other tools</td></tr>
          <tr><td style="padding:4px 0;font-size:14px;color:#065f46;">✓ &nbsp;Watch your compliance score update automatically</td></tr>
          <tr><td style="padding:4px 0;font-size:14px;color:#065f46;">✓ &nbsp;Get audit-ready for SOC 2, ISO 27001, HIPAA, GDPR</td></tr>
        </table>
      </div>
      {_btn(f"{settings.app_frontend_url}/onboarding", "Get started →")}
    """
    _send(to, subject, _layout(body, f"TraceLayer &nbsp;&middot;&nbsp; Continuous compliance evidence collection."))


def send_partner_welcome_email(to: str, company_name: str) -> None:
    """Welcome email for new partner / agency accounts."""
    subject = "Welcome to the TraceLayer Partner Program"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Welcome, {company_name}!</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;font-size:15px;line-height:1.6;">
        You're now set up as a TraceLayer Partner. Here's everything you can do from your partner dashboard.
      </p>
      <div style="background:{_BRAND_LIGHT};border:1.5px solid {_BRAND_BORDER};border-radius:12px;padding:20px 24px;margin:0 0 24px;">
        <p style="margin:0 0 12px;font-weight:700;color:{_BRAND};font-size:13px;text-transform:uppercase;letter-spacing:0.06em;">Your partner dashboard</p>
        <table cellpadding="0" cellspacing="0" border="0" width="100%">
          <tr><td style="padding:5px 0;font-size:14px;color:#065f46;">✓ &nbsp;Add client workspaces ($99 each)</td></tr>
          <tr><td style="padding:5px 0;font-size:14px;color:#065f46;">✓ &nbsp;Switch into any client's dashboard instantly</td></tr>
          <tr><td style="padding:5px 0;font-size:14px;color:#065f46;">✓ &nbsp;Share a branded Trust Center link with each client</td></tr>
          <tr><td style="padding:5px 0;font-size:14px;color:#065f46;">✓ &nbsp;Manage SOC 2, ISO 27001, GDPR compliance for all clients</td></tr>
        </table>
      </div>
      <p style="color:{_TEXT_BODY};font-size:14px;margin:0 0 24px;line-height:1.6;">
        Head to your partner dashboard and add your first client. Each workspace is provisioned instantly.
      </p>
      {_btn(f"{settings.app_frontend_url}/partner/clients", "Open partner dashboard →")}
    """
    _send(to, subject, _layout(body, f"TraceLayer Partner Program &nbsp;&middot;&nbsp; <a href='mailto:support@tracelayer.it.com' style='color:{_TEXT_MUTED};text-decoration:none;'>support@tracelayer.it.com</a>"))


def send_partner_nudge_email(to: str, day: int, client_count: int = 0) -> None:
    """Day 1 / 3 / 7 activation nudge for partners who haven't added their first client."""
    nudge_content = {
        1: {
            "subject": "Ready to add your first client to TraceLayer?",
            "headline": "Your partner dashboard is waiting",
            "body": (
                "You signed up for the TraceLayer Partner Program yesterday — great first step. "
                "The next one is adding your first client workspace. It takes about 60 seconds: "
                "click 'Add client', enter their company name, and you're in."
            ),
            "tip": "💡 Tip: Once you add a client, you get a Trust Center link you can share with them immediately — no setup required on their end.",
            "cta": "Add your first client",
        },
        3: {
            "subject": "Your clients are waiting on their compliance program",
            "headline": "You haven't added a client yet",
            "body": (
                "It's been a few days since you joined the TraceLayer Partner Program. "
                "If you have a client who needs SOC 2 or ISO 27001, now is the time. "
                "Add their workspace, switch into their dashboard, and start collecting evidence today — "
                "all within minutes."
            ),
            "tip": "💡 Tip: Each client gets their own isolated workspace. You manage everything from your partner view — they don't need to do anything technical.",
            "cta": "Add a client workspace",
        },
        7: {
            "subject": "Partner tips: getting the most out of TraceLayer",
            "headline": "Make your compliance practice more efficient",
            "body": (
                "Here are the most useful TraceLayer partner features our top partners rely on every week:"
            ),
            "tip": None,
            "cta": "Open partner dashboard",
        },
    }
    content = nudge_content.get(day, nudge_content[1])

    tips_html = ""
    if day == 7:
        tips_html = """
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 24px">
          <tr><td style="padding:8px 0;border-bottom:1px solid #f1f5f9">
            <span style="font-weight:700;color:#1e293b;font-size:14px;">1. One-click context switch</span><br/>
            <span style="color:#64748b;font-size:13px;">Jump into any client dashboard instantly. Your partner token is preserved — just click Exit to return.</span>
          </td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #f1f5f9">
            <span style="font-weight:700;color:#1e293b;font-size:14px;">2. Trust Center links</span><br/>
            <span style="color:#64748b;font-size:13px;">Each client has a public Trust Center URL. Share it with their auditors or prospects — it updates in real-time.</span>
          </td></tr>
          <tr><td style="padding:8px 0;border-bottom:1px solid #f1f5f9">
            <span style="font-weight:700;color:#1e293b;font-size:14px;">3. AI Audit Package</span><br/>
            <span style="color:#64748b;font-size:13px;">Generate a polished 11-section PDF audit report for any client in seconds. Great for executive presentations.</span>
          </td></tr>
          <tr><td style="padding:8px 0">
            <span style="font-weight:700;color:#1e293b;font-size:14px;">4. Weekly compliance emails</span><br/>
            <span style="color:#64748b;font-size:13px;">Each client's admin automatically receives a weekly compliance briefing — one less report for you to write.</span>
          </td></tr>
        </table>
        """
    elif content["tip"]:
        tips_html = f"""
        <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:12px 16px;margin:0 0 24px;font-size:13px;color:#854d0e;line-height:1.6">
          {content['tip']}
        </div>
        """

    body = f"""
      <h2 style="margin:0 0 12px;color:{_TEXT_HEAD};font-size:20px;line-height:1.3;">{content['headline']}</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 20px;line-height:1.6;font-size:15px;">
        {content['body']}
      </p>
      {tips_html}
      {_btn(f"{settings.app_frontend_url}/partner/clients", f"{content['cta']} →")}
    """
    _send(to, subject, _layout(body, f"TraceLayer Partner Program &nbsp;&middot;&nbsp; <a href='mailto:support@tracelayer.it.com' style='color:{_TEXT_MUTED};text-decoration:none;'>support@tracelayer.it.com</a>"))


def send_activation_nudge_email(to: str, day: int) -> None:
    """Send a Day-N activation nudge to users who haven't connected an integration yet."""
    nudge_content = {
        1: {
            "subject": "Your TraceLayer dashboard is ready — connect your first tool",
            "headline": "One quick step to get started",
            "body": (
                "You signed up yesterday but haven't connected a tool yet. "
                "Connecting GitHub or AWS takes under 2 minutes and immediately starts "
                "collecting compliance evidence for you automatically."
            ),
            "cta": "Connect your first tool",
            "cta_url": f"{settings.app_frontend_url}/integrations",
        },
        3: {
            "subject": "Your compliance evidence isn't collecting yet",
            "headline": "You're 2 minutes away from automated compliance",
            "body": (
                "TraceLayer is ready — but your compliance score is sitting at zero because "
                "no tools are connected. Connect GitHub, AWS, or Slack and we'll start "
                "collecting evidence automatically, no manual work needed."
            ),
            "cta": "Connect an integration",
            "cta_url": f"{settings.app_frontend_url}/integrations",
        },
        7: {
            "subject": "One week in — your compliance program hasn't started yet",
            "headline": "Don't leave compliance evidence on the table",
            "body": (
                "It's been a week since you signed up for TraceLayer. Without an integration, "
                "your compliance score stays at zero and auditors will have nothing to review. "
                "Take 2 minutes now to connect your first tool — it's the single highest-leverage "
                "thing you can do for your security program today."
            ),
            "cta": "Set up your first integration",
            "cta_url": f"{settings.app_frontend_url}/integrations",
        },
    }
    content = nudge_content.get(day, nudge_content[1])
    subject = content["subject"]
    body = f"""
      <h2 style="margin:0 0 12px;color:{_TEXT_HEAD};font-size:20px;line-height:1.3;">{content['headline']}</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;line-height:1.6;font-size:15px;">
        {content['body']}
      </p>
      {_btn(content['cta_url'], f"{content['cta']} →")}
    """
    footer = (
        f'TraceLayer &nbsp;&middot;&nbsp; '
        f'<a href="{settings.app_frontend_url}/settings" style="color:{_TEXT_MUTED};text-decoration:none;">Manage email preferences</a>'
    )
    _send(to, subject, _layout(body, footer))


def send_collection_failure_email(to: str, integration_type: str, error: str) -> None:
    subject = f"TraceLayer: {integration_type} evidence collection failed"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:20px;">Evidence collection failed</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        The scheduled evidence collection for <strong>{integration_type}</strong> failed.
        Your compliance score may be out of date until this is resolved.
      </p>
      <div style="background:{_RED_BG};border:1px solid {_RED_BORDER};border-radius:10px;padding:14px 18px;margin:0 0 24px;">
        <p style="margin:0 0 6px;font-weight:700;font-size:12px;color:#991b1b;text-transform:uppercase;letter-spacing:0.05em;">Error details</p>
        <code style="font-size:12px;color:#991b1b;line-height:1.5;">{error[:300]}</code>
      </div>
      {_btn(f"{settings.app_frontend_url}/integrations", "Go to Integrations")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:20px 0 0;line-height:1.6;">
        You can reconnect the integration or trigger a manual sync from the Integrations page.
      </p>
    """
    _send(to, subject, _layout(body))


def send_verification_email(to: str, verify_url: str) -> None:
    subject = "Verify your TraceLayer email address"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Verify your email</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        Click the button below to verify your email address and activate your TraceLayer account.
        This link expires in 24 hours.
      </p>
      {_btn(verify_url, "Verify email address")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:24px 0 0;">
        If you didn't create a TraceLayer account, you can safely ignore this email.
      </p>
    """
    text = (
        f"Verify your TraceLayer email address\n\n"
        f"Click the link below to verify your email and activate your account.\n"
        f"This link expires in 24 hours.\n\n"
        f"{verify_url}\n\n"
        f"If you didn't create a TraceLayer account, you can safely ignore this email."
    )
    _send(to, subject, _layout(body), text)


def send_password_reset_email(to: str, reset_url: str) -> None:
    subject = "Reset your TraceLayer password"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Reset your password</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        We received a request to reset the password for your TraceLayer account.
        Click the button below — this link expires in 1 hour.
      </p>
      {_btn(reset_url, "Reset password")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:24px 0 0;">
        If you didn't request this, you can safely ignore this email. Your password will not change.
      </p>
    """
    text = (
        f"Reset your TraceLayer password\n\n"
        f"We received a request to reset your password. Click the link below — it expires in 1 hour.\n\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, you can safely ignore this email. Your password will not change."
    )
    _send(to, subject, _layout(body), text)


def send_password_changed_email(to: str) -> None:
    subject = "Your TraceLayer password was changed"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Password changed</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        Your TraceLayer account password was just updated. If you made this change, no action is needed.
      </p>
      <p style="color:{_TEXT_BODY};font-size:15px;line-height:1.6;">
        If you didn't do this, please contact us immediately at
        <a href="mailto:support@tracelayer.it.com" style="color:{_BRAND};">support@tracelayer.it.com</a>.
      </p>
    """
    _send(to, subject, _layout(body))


def send_account_deleted_email(to: str, company_name: str) -> None:
    subject = "Your TraceLayer account has been deleted"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Account deleted</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        Your TraceLayer account for <strong>{company_name}</strong> has been permanently deleted.
        All associated data has been removed from our systems.
      </p>
      <p style="color:{_TEXT_BODY};font-size:15px;line-height:1.6;">
        If you did not request this, please contact us immediately at
        <a href="mailto:support@tracelayer.it.com" style="color:{_BRAND};">support@tracelayer.it.com</a>.
      </p>
    """
    _send(to, subject, _layout(body))


def send_subscription_cancelled_email(to: str, company_name: str) -> None:
    subject = "Your TraceLayer subscription has been cancelled"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Subscription cancelled</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        Your Growth plan subscription for <strong>{company_name}</strong> has been cancelled.
        Your account will revert to the Free plan at the end of your current billing period.
      </p>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        Your data and evidence will be retained. You can reactivate at any time.
      </p>
      {_btn(f"{settings.app_frontend_url}/settings#billing", "Reactivate subscription")}
    """
    _send(to, subject, _layout(body))


def send_new_team_member_email(to: str, inviter_name: str, company_name: str, member_email: str) -> None:
    subject = f"{member_email} has joined {company_name} on TraceLayer"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">New team member joined</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        <strong>{member_email}</strong> has accepted their invitation and joined
        <strong>{company_name}</strong> on TraceLayer.
      </p>
      {_btn(f"{settings.app_frontend_url}/team", "View team")}
    """
    _send(to, subject, _layout(body))


def send_trial_ending_email(to: str, company_name: str, days_left: int) -> None:
    subject = f"Your TraceLayer trial ends in {days_left} day{'s' if days_left != 1 else ''}"
    body = f"""
      <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:10px;padding:12px 18px;margin:0 0 24px;">
        <p style="margin:0;font-weight:700;color:#92400e;font-size:14px;">
          ⏰ Your trial ends in {days_left} day{'s' if days_left != 1 else ''}
        </p>
      </div>
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Keep your compliance program running</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        Your free trial for <strong>{company_name}</strong> is ending soon.
        Upgrade to the Growth plan to keep automated evidence collection, AI reports,
        and all 7 compliance frameworks active.
      </p>
      {_btn(f"{settings.app_frontend_url}/settings#billing", "Upgrade to Growth →")}
    """
    _send(to, subject, _layout(body))


def send_audit_session_created_email(to: str, company_name: str, label: str, expires_at_str: str) -> None:
    subject = f"Auditor access link created for {company_name}"
    body = f"""
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Auditor access link created</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        An auditor access session has been created for <strong>{company_name}</strong>.
      </p>
      <div style="background:{_BRAND_LIGHT};border:1.5px solid {_BRAND_BORDER};border-radius:10px;padding:16px 20px;margin:0 0 24px;">
        <p style="margin:0 0 8px;font-size:12px;font-weight:700;color:{_BRAND};text-transform:uppercase;letter-spacing:0.06em;">Session details</p>
        <p style="margin:0 0 4px;font-size:14px;color:{_TEXT_BODY};"><strong>Label:</strong> {label or "Untitled session"}</p>
        <p style="margin:0;font-size:14px;color:{_TEXT_BODY};"><strong>Expires:</strong> {expires_at_str}</p>
      </div>
      <p style="color:{_TEXT_BODY};font-size:14px;margin:0 0 24px;line-height:1.6;">
        If you did not create this session, please revoke it immediately.
      </p>
      {_btn(f"{settings.app_frontend_url}/settings#audit-sessions", "Manage audit sessions")}
    """
    _send(to, subject, _layout(body))


def send_2fa_enabled_email(to: str) -> None:
    subject = "Two-factor authentication enabled on your TraceLayer account"
    body = f"""
      <div style="background:#f0fdf4;border:1.5px solid #d1fae5;border-radius:10px;padding:12px 18px;margin:0 0 24px;">
        <p style="margin:0;font-weight:700;color:#065f46;font-size:14px;">&#10003; Two-factor authentication enabled</p>
      </div>
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Your account is now more secure</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        Two-factor authentication (2FA) has been successfully enabled on your TraceLayer account.
      </p>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        You will need your authenticator app each time you sign in.
        Make sure you&rsquo;ve saved your backup codes in a safe place.
      </p>
      {_btn(f"{settings.app_frontend_url}/settings#security", "View security settings")}
      <p style="color:{_TEXT_MUTED};font-size:13px;margin-top:24px;line-height:1.5;">
        If you did not enable 2FA, contact support immediately at
        <a href="mailto:support@tracelayer.it.com" style="color:{_TEXT_MUTED};">support@tracelayer.it.com</a>
      </p>
    """
    _send(to, subject, _layout(body))


def send_2fa_disabled_email(to: str) -> None:
    subject = "Two-factor authentication disabled on your TraceLayer account"
    body = f"""
      <div style="background:{_RED_BG};border:1.5px solid {_RED_BORDER};border-radius:10px;padding:12px 18px;margin:0 0 24px;">
        <p style="margin:0;font-weight:700;color:#991b1b;font-size:14px;">&#9888; Security alert: 2FA disabled</p>
      </div>
      <h2 style="margin:0 0 10px;color:{_TEXT_HEAD};font-size:22px;">Two-factor authentication disabled</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 16px;font-size:15px;line-height:1.6;">
        Two-factor authentication has been disabled on your TraceLayer account.
        Your account is now protected only by your password.
      </p>
      <p style="color:{_TEXT_BODY};margin:0 0 28px;font-size:15px;line-height:1.6;">
        If you did not do this, your account may be compromised. Please change your password
        and re-enable 2FA immediately.
      </p>
      {_btn(f"{settings.app_frontend_url}/settings#security", "Secure your account", color=_RED)}
    """
    _send(to, subject, _layout(body))


def send_alert_digest(to: str, company_name: str, alerts: list[dict], frontend_url: str) -> None:
    """Send a compliance alert digest email."""
    # alerts format: [{"type": str, "label": str, "count": int, "items": list[str]}]
    subject = f"Compliance alerts for {company_name}"
    items_html = ""
    for alert in alerts:
        items_list = "".join(
            f"<li style='margin:2px 0;font-size:13px;color:{_TEXT_BODY};'>{item}</li>"
            for item in alert["items"][:5]
        )
        if len(alert["items"]) > 5:
            items_list += (
                f"<li style='margin:2px 0;font-size:13px;color:{_TEXT_MUTED};'>"
                f"...and {len(alert['items']) - 5} more</li>"
            )
        items_html += f"""
        <div style="margin-bottom:16px;padding:12px 16px;background:{_RED_BG};border:1.5px solid {_RED_BORDER};border-radius:10px;">
          <p style="margin:0 0 6px;font-weight:700;color:{_RED};font-size:13px;">{alert['label']} ({alert['count']})</p>
          <ul style="margin:0;padding-left:16px;">{items_list}</ul>
        </div>
        """
    body = f"""
      <h2 style="margin:0 0 6px;color:{_TEXT_HEAD};font-size:22px;">Compliance Alerts</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;font-size:14px;line-height:1.6;">
        {company_name} &mdash; {len(alerts)} issue type{'s' if len(alerts) != 1 else ''} need{'s' if len(alerts) == 1 else ''} attention
      </p>
      {items_html}
      {_btn(frontend_url + "/dashboard", "Open dashboard")}
    """
    _send(to, subject, _layout(body, footer_note=f"TraceLayer &nbsp;&middot;&nbsp; Daily compliance alerts"))


def send_weekly_compliance_report(
    to: str,
    company_name: str,
    framework_scores: list,  # [{"framework": "soc2", "label": "SOC 2", "score": 72, "controls": [...]}]
    week_label: str,  # e.g. "Mar 10 – Mar 16, 2025"
    frontend_url: str,
) -> None:
    subject = f"Weekly Compliance Briefing – {company_name} ({week_label})"

    # ------------------------------------------------------------------ helpers
    def _score_color(score: int) -> str:
        if score >= 80:
            return "#10b981"
        if score >= 50:
            return "#f59e0b"
        return "#ef4444"

    def _status_dot_color(status: str) -> str:
        return {
            "passing": "#10b981",
            "warning": "#f59e0b",
            "failing": "#ef4444",
        }.get(status, "#94a3b8")

    def _status_label(status: str) -> str:
        return {
            "passing": "Passing",
            "warning": "Warning",
            "failing": "Failing",
            "no_evidence": "No Evidence",
        }.get(status, status.replace("_", " ").title())

    # ------------------------------------------------------------------ framework scorecard columns
    def _card_colors(score: int):
        if score >= 80:
            return "#f0fdf4", "#d1fae5"
        if score >= 50:
            return "#fffbeb", "#fde68a"
        return "#fef2f2", "#fecaca"

    num_fw = len(framework_scores)
    scorecard_cells = ""
    for fw in framework_scores:
        score = fw["score"]
        color = _score_color(score)
        bg, border = _card_colors(score)
        pct = min(score, 100)
        scorecard_cells += (
            '<td class="scorecard-cell" style="width:{w}%;padding:6px 5px;vertical-align:top;">'.format(w=round(100 / max(num_fw, 1)))
            + '<div style="background:{bg};border:1.5px solid {bd};border-radius:12px;padding:18px 12px 14px;text-align:center;">'.format(bg=bg, bd=border)
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;'
            + 'letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:10px;">'
            + fw["label"]
            + "</div>"
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:40px;font-weight:800;'
            + 'line-height:1;color:{color};margin-bottom:4px;">{score}</div>'.format(color=color, score=score)
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#94a3b8;margin-bottom:12px;">/ 100</div>'
            + '<div style="background:#e2e8f0;border-radius:99px;height:6px;width:100%;overflow:hidden;">'
            + '<div style="background:{c};border-radius:99px;height:6px;width:{p}%;"></div>'.format(c=color, p=pct)
            + "</div></div>"
            + "</td>"
        )

    # Pad to 3 columns if fewer frameworks passed
    while num_fw < 3:
        scorecard_cells += '<td class="scorecard-cell" style="width:33%;padding:6px 5px;"></td>'
        num_fw += 1

    # ------------------------------------------------------------------ deduplicated controls across frameworks
    seen_names: set = set()
    all_controls: list = []
    for fw in framework_scores:
        for ctrl in fw.get("controls", []):
            name = ctrl.get("name", "")
            if name not in seen_names:
                seen_names.add(name)
                all_controls.append(ctrl)

    controls_rows = ""
    for ctrl in all_controls:
        name = ctrl.get("name", "Unknown Control")
        score = ctrl.get("score", 0)
        status = ctrl.get("status", "no_evidence")
        missing = ctrl.get("missing_types", [])
        dot_color = _status_dot_color(status)
        status_lbl = _status_label(status)
        score_color = _score_color(score)

        # Missing type pills
        pills_html = ""
        if missing:
            pills_html = (
                '<div style="margin-top:5px;">'
                + "".join(
                    '<span style="display:inline-block;background:#fef2f2;border:1px solid #fecaca;'
                    'color:#b91c1c;font-family:Arial,Helvetica,sans-serif;font-size:10px;'
                    'font-weight:600;border-radius:4px;padding:1px 6px;margin:2px 2px 0 0;'
                    'white-space:nowrap;">{}</span>'.format(m.replace("_", " "))
                    for m in missing
                )
                + "</div>"
            )

        controls_rows += (
            '<tr>'
            + '<td style="padding:10px 0;border-bottom:1px solid #f1f5f9;vertical-align:top;width:20px;">'
            + ('<div style="width:10px;height:10px;border-radius:50%;background:{dot};margin-top:3px;'
            + 'mso-border-radius:50%;display:inline-block;"></div>').format(dot=dot_color)
            + '</td>'
            + '<td style="padding:10px 8px 10px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top;">'
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:600;color:#1e293b;">'
            + name
            + '</div>'
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#64748b;margin-top:2px;">'
            + status_lbl
            + '</div>'
            + pills_html
            + '</td>'
            + '<td style="padding:10px 0;border-bottom:1px solid #f1f5f9;vertical-align:top;text-align:right;'
            + 'white-space:nowrap;width:56px;">'
            + ('<span style="font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:700;color:{sc};">'
            + '{s}%').format(sc=score_color, s=score)
            + '</span>'
            + '</td>'
            + '</tr>'
        )

    if not controls_rows:
        controls_rows = (
            '<tr><td colspan="3" style="padding:16px 0;font-family:Arial,Helvetica,sans-serif;'
            'font-size:14px;color:#94a3b8;text-align:center;">No controls found.</td></tr>'
        )

    # ------------------------------------------------------------------ top action items (non-passing, max 3)
    non_passing = [c for c in all_controls if c.get("status") != "passing"]
    # Sort by score ascending so most critical come first
    non_passing.sort(key=lambda c: c.get("score", 0))
    action_items_html = ""
    for idx, ctrl in enumerate(non_passing[:3], start=1):
        name = ctrl.get("name", "Unknown Control")
        missing = ctrl.get("missing_types", [])
        if missing:
            missing_str = ", ".join(m.replace("_", " ") for m in missing)
            detail = "Connect an integration that provides: " + missing_str
        else:
            detail = "Review and update evidence for this control."

        action_items_html += (
            '<tr>'
            + '<td style="padding:10px 0;vertical-align:top;width:28px;">'
            + '<div style="width:24px;height:24px;border-radius:50%;background:#0f766e;'
            + 'display:inline-block;text-align:center;line-height:24px;'
            + 'font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;color:#ffffff;">'
            + str(idx)
            + '</div>'
            + '</td>'
            + '<td style="padding:10px 0 10px 12px;vertical-align:top;">'
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;color:#1e293b;">'
            + name
            + '</div>'
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#475569;margin-top:3px;">'
            + detail
            + '</div>'
            + '</td>'
            + '</tr>'
        )

    if not action_items_html:
        action_items_html = (
            '<tr><td colspan="2" style="padding:12px 0;font-family:Arial,Helvetica,sans-serif;'
            'font-size:14px;color:#10b981;font-weight:600;">All controls are passing. Great work!</td></tr>'
        )

    # ------------------------------------------------------------------ assemble HTML
    html = """\
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
  <title>Weekly Compliance Briefing</title>
  <style type="text/css">
    @media screen and (max-width:600px) {{
      .email-wrapper {{ padding:16px 8px 0 8px !important; }}
      .email-container {{ width:100%% !important; max-width:100%% !important; }}
      .header-cell {{ padding:24px 20px 20px 20px !important; }}
      .body-cell {{ padding:20px 16px !important; }}
      .scorecard-cell {{ display:block !important; width:100%% !important; padding:5px 0 !important; box-sizing:border-box !important; }}
      .cta-table {{ width:100%% !important; }}
      .cta-td {{ width:100%% !important; display:block !important; }}
      .cta-link {{ display:block !important; text-align:center !important; padding:16px 20px !important; width:100%% !important; box-sizing:border-box !important; }}
      .footer-cell {{ padding:20px 12px 24px 12px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#f7f1e8;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
  <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#f7f1e8;min-width:100%%;">
    <tr>
      <td class="email-wrapper" align="center" style="padding:32px 16px 0 16px;">

        <!-- WORDMARK -->
        <table role="presentation" class="email-container" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%%;">
          <tr>
            <td align="center" style="padding-bottom:20px;">
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:22px;font-weight:800;
                          letter-spacing:-0.5px;color:#0f766e;">TraceLayer</div>
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#94a3b8;
                          margin-top:3px;letter-spacing:0.04em;">Continuous Compliance Evidence</div>
            </td>
          </tr>
        </table>

        <!-- MAIN CARD -->
        <table role="presentation" class="email-container" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%%;background:#ffffff;border-radius:16px;
                      mso-border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.08);
                      border-collapse:separate;">
          <tr>
            <td style="border-radius:16px;mso-border-radius:16px;overflow:hidden;">

              <!-- GRADIENT HEADER -->
              <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="header-cell" style="background:#0d9488;
                             background:linear-gradient(135deg,#0d9488 0%%,#134e4a 100%%);
                             padding:32px 36px 28px 36px;border-radius:16px 16px 0 0;
                             mso-border-radius:16px 16px 0 0;">
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;
                                letter-spacing:0.12em;text-transform:uppercase;color:#99f6e4;
                                margin-bottom:8px;">Weekly Compliance Briefing</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:26px;font-weight:800;
                                color:#ffffff;line-height:1.2;margin-bottom:6px;">{company_name}</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#99f6e4;">
                      {week_label}
                    </div>
                  </td>
                </tr>
              </table>

              <!-- BODY -->
              <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td class="body-cell" style="padding:28px 32px;">

                    <!-- FRAMEWORK SCORES LABEL -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:14px;">Framework Scores</div>

                    <!-- SCORECARDS — stacks to 1-col on mobile -->
                    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
                           style="border-collapse:collapse;margin-bottom:28px;">
                      <tr>
                        {scorecard_cells}
                      </tr>
                    </table>

                    <!-- DIVIDER -->
                    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:20px;">
                      <tr><td style="border-top:1px solid #e2e8f0;font-size:0;line-height:0;">&nbsp;</td></tr>
                    </table>

                    <!-- CONTROL STATUS -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:4px;">Control Status</div>
                    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:28px;">
                      {controls_rows}
                    </table>

                    <!-- DIVIDER -->
                    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:20px;">
                      <tr><td style="border-top:1px solid #e2e8f0;font-size:0;line-height:0;">&nbsp;</td></tr>
                    </table>

                    <!-- ACTION ITEMS -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:4px;">Priority Action Items</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#64748b;
                                margin-bottom:14px;">Top controls requiring attention this week.</div>
                    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:28px;">
                      {action_items_html}
                    </table>

                    <!-- CTA BUTTON -->
                    <table class="cta-table" role="presentation" cellpadding="0" cellspacing="0" border="0"
                           style="margin:0 auto 4px auto;">
                      <tr>
                        <td class="cta-td" align="center"
                            style="border-radius:10px;mso-border-radius:10px;background:#0f766e;">
                          <!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
                            href="{frontend_url}/compliance"
                            style="height:50px;v-text-anchor:middle;width:240px;"
                            arcsize="16%%" stroke="f" fillcolor="#0f766e">
                            <w:anchorlock/>
                            <center style="color:#ffffff;font-family:Arial,Helvetica,sans-serif;
                                           font-size:15px;font-weight:700;">
                              View full dashboard &rarr;
                            </center>
                          </v:roundrect><![endif]-->
                          <!--[if !mso]><!-->
                          <a class="cta-link" href="{frontend_url}/compliance"
                             style="display:inline-block;background:#0f766e;color:#ffffff;
                                    text-decoration:none;font-family:Arial,Helvetica,sans-serif;
                                    font-size:15px;font-weight:700;padding:14px 36px;
                                    border-radius:10px;mso-border-radius:10px;
                                    letter-spacing:0.01em;">
                            View full dashboard &rarr;
                          </a>
                          <!--<![endif]-->
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>

            </td>
          </tr>
        </table>

        <!-- FOOTER -->
        <table role="presentation" class="email-container" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%%;">
          <tr>
            <td class="footer-cell" align="center" style="padding:20px 16px 28px 16px;">
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#94a3b8;
                          line-height:1.6;">
                You&rsquo;re receiving this because you&rsquo;re an admin at
                <strong style="color:#64748b;">{company_name}</strong> on TraceLayer.
                &nbsp;&middot;&nbsp;
                <a href="#" style="color:#94a3b8;text-decoration:underline;">Unsubscribe</a>
              </div>
            </td>
          </tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>""".format(
        company_name=company_name,
        week_label=week_label,
        scorecard_cells=scorecard_cells,
        controls_rows=controls_rows,
        action_items_html=action_items_html,
        frontend_url=frontend_url,
    )

    _send(to, subject, html)


def send_control_owner_reminder(
    to: str,
    owner_name: str,
    company_name: str,
    controls: list[dict],
) -> None:
    """Weekly reminder to a control owner listing their pending controls."""
    count = len(controls)
    rows = "".join(
        f'<tr>'
        f'<td style="padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:13px;color:{_TEXT_BODY};">{c["name"]}</td>'
        f'<td style="padding:8px 0 8px 16px;border-bottom:1px solid #f1f5f9;font-size:11px;font-weight:600;color:{_TEXT_MUTED};text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">{c["framework"]}</td>'
        f'</tr>'
        for c in controls
    )
    subject = f"Action needed: {count} compliance control{'s' if count != 1 else ''} assigned to you"
    body = f"""
      <h2 style="margin:0 0 8px;color:{_TEXT_HEAD};font-size:22px;">Controls waiting on you</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;font-size:15px;line-height:1.6;">
        Hi {owner_name}, you have <strong>{count} pending compliance control{'s' if count != 1 else ''}</strong>
        assigned to you in <strong>{company_name}</strong>. These need to be marked compliant before your next audit.
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 28px;">
        <tr>
          <th style="text-align:left;font-size:11px;font-weight:700;color:{_TEXT_MUTED};text-transform:uppercase;letter-spacing:0.06em;padding:0 0 10px;">Control</th>
          <th style="text-align:left;font-size:11px;font-weight:700;color:{_TEXT_MUTED};text-transform:uppercase;letter-spacing:0.06em;padding:0 0 10px 16px;">Framework</th>
        </tr>
        {rows}
      </table>
      {_btn(f"{settings.app_frontend_url}/compliance", "Review my controls →")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:20px 0 0;line-height:1.6;">
        You're receiving this because you're the assigned owner of these controls in TraceLayer.
        To stop receiving these, ask your admin to reassign the controls.
      </p>
    """
    _send(to, subject, _layout(body))


def send_auto_detection_digest(
    to: str,
    company_name: str,
    risks: int,
    training: int,
    background_checks: int,
    incidents: int,
) -> None:
    """Nightly digest to admins: what auto-detection found overnight."""
    total = risks + training + background_checks + incidents
    if total == 0:
        return

    def _row(label: str, count: int, href: str) -> str:
        if count == 0:
            return ""
        return (
            f'<tr>'
            f'<td style="padding:11px 16px;border-bottom:1px solid #f1f5f9;font-size:13px;color:{_TEXT_BODY};">{label}</td>'
            f'<td style="padding:11px 16px;border-bottom:1px solid #f1f5f9;text-align:right;">'
            f'<a href="{settings.app_frontend_url}{href}" style="font-size:13px;font-weight:700;color:{_BRAND};text-decoration:none;">'
            f'{count} new →</a></td>'
            f'</tr>'
        )

    rows = (
        _row("Risks auto-detected", risks, "/risks")
        + _row("Training assignments created", training, "/training")
        + _row("Background check gaps flagged", background_checks, "/background-checks")
        + _row("Incidents auto-created", incidents, "/incidents")
    )

    subject = f"TraceLayer found {total} new item{'s' if total != 1 else ''} overnight — {company_name}"
    body = f"""
      <h2 style="margin:0 0 8px;color:{_TEXT_HEAD};font-size:22px;">Overnight detection summary</h2>
      <p style="color:{_TEXT_BODY};margin:0 0 24px;font-size:15px;line-height:1.6;">
        TraceLayer's nightly scan found <strong>{total} new item{'s' if total != 1 else ''}</strong>
        for <strong>{company_name}</strong>. Here's what was auto-created:
      </p>
      <table cellpadding="0" cellspacing="0" border="0" width="100%"
        style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:0 0 28px;">
        {rows}
      </table>
      {_btn(f"{settings.app_frontend_url}/dashboard", "Review in TraceLayer →")}
      <p style="color:{_TEXT_MUTED};font-size:12px;margin:20px 0 0;line-height:1.6;">
        These items were auto-detected from your existing data. If they're already handled,
        you can dismiss or update them in the dashboard. No action is required otherwise.
      </p>
    """
    _send(to, subject, _layout(body))
