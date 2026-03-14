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


def send_verification_email(to: str, verify_url: str) -> None:
    subject = "Verify your TraceLayer email address"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px">Verify your email</h2>
      <p style="color:#555;margin:0 0 24px">
        Click the button below to verify your email address and activate your TraceLayer account.
        This link expires in 24 hours.
      </p>
      <a href="{verify_url}"
         style="display:inline-block;background:#4f46e5;color:#fff;text-decoration:none;
                padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px">
        Verify email address
      </a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        If you didn't create a TraceLayer account, you can safely ignore this email.
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
    num_fw = len(framework_scores)
    # Build one <td> per framework scorecard
    scorecard_cells = ""
    for fw in framework_scores:
        score = fw["score"]
        color = _score_color(score)
        pct = min(score, 100)
        scorecard_cells += (
            '<td width="{w}%" style="width:{w}%;padding:6px 8px;vertical-align:top;">'.format(w=round(100 / max(num_fw, 1)))
            + '<table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">'
            + "<tr><td>"
            + '<div style="background:#f0fdf4;border:1.5px solid #d1fae5;border-radius:12px;padding:18px 14px 14px 14px;text-align:center;">'
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;'
            + 'letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:10px;">'
            + fw["label"]
            + "</div>"
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:42px;font-weight:800;'
            + 'line-height:1;color:{color};margin-bottom:4px;">{score}</div>'.format(color=color, score=score)
            + '<div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#94a3b8;margin-bottom:12px;">/ 100</div>'
            # progress bar background
            + '<div style="background:#e2e8f0;border-radius:99px;height:6px;width:100%;overflow:hidden;">'
            + '<div style="background:{color};border-radius:99px;height:6px;width:{pct}%;'
            + 'mso-border-radius:99px;"></div>'.format(color=color, pct=pct)
            + "</div>"
            + "</div>"
            + "</td></tr>"
            + "</table>"
            + "</td>"
        )

    # Pad to 3 columns if fewer frameworks passed
    while num_fw < 3:
        scorecard_cells += '<td width="33%" style="width:33%;padding:6px 8px;"></td>'
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
            + '<div style="width:10px;height:10px;border-radius:50%;background:{dot};margin-top:3px;'
            + 'mso-border-radius:50%;display:inline-block;"></div>'.format(dot=dot_color)
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
            + '<span style="font-family:Arial,Helvetica,sans-serif;font-size:15px;font-weight:700;color:{sc};">'
            + '{s}%'.format(sc=score_color, s=score)
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
</head>
<body style="margin:0;padding:0;background-color:#f7f1e8;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#f7f1e8;min-width:100%;">
    <tr>
      <td align="center" style="padding:32px 16px 0 16px;">

        <!-- TOP BAR: wordmark -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;">
          <tr>
            <td align="center" style="padding-bottom:24px;">
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:22px;font-weight:800;
                          letter-spacing:-0.5px;color:#0f766e;">TraceLayer</div>
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;color:#94a3b8;
                          margin-top:3px;letter-spacing:0.04em;">Continuous Compliance Evidence</div>
            </td>
          </tr>
        </table>

        <!-- MAIN WHITE CARD -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;
                      mso-border-radius:16px;
                      box-shadow:0 4px 24px rgba(0,0,0,0.08);
                      border-collapse:separate;">
          <tr>
            <td style="border-radius:16px;mso-border-radius:16px;overflow:hidden;">

              <!-- GRADIENT HEADER -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="background:#0d9488;
                             background:linear-gradient(135deg,#0d9488 0%%,#134e4a 100%%);
                             padding:36px 40px 32px 40px;border-radius:16px 16px 0 0;
                             mso-border-radius:16px 16px 0 0;">
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:11px;font-weight:700;
                                letter-spacing:0.12em;text-transform:uppercase;color:#99f6e4;
                                margin-bottom:10px;">Weekly Compliance Briefing</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:28px;font-weight:800;
                                color:#ffffff;line-height:1.2;margin-bottom:8px;">{company_name}</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#99f6e4;">
                      {week_label}
                    </div>
                  </td>
                </tr>
              </table>

              <!-- BODY PADDING WRAPPER -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding:32px 40px;">

                    <!-- FRAMEWORK SCORECARDS HEADING -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:16px;">Framework Scores</div>

                    <!-- SCORECARD 3-COLUMN TABLE -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="border-collapse:collapse;margin-bottom:32px;">
                      <tr>
                        {scorecard_cells}
                      </tr>
                    </table>

                    <!-- DIVIDER -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:24px;">
                      <tr>
                        <td style="border-top:1px solid #e2e8f0;font-size:0;line-height:0;">&nbsp;</td>
                      </tr>
                    </table>

                    <!-- CONTROL STATUS HEADING -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:4px;">Control Status</div>

                    <!-- CONTROLS TABLE -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:32px;">
                      {controls_rows}
                    </table>

                    <!-- DIVIDER -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:24px;">
                      <tr>
                        <td style="border-top:1px solid #e2e8f0;font-size:0;line-height:0;">&nbsp;</td>
                      </tr>
                    </table>

                    <!-- ACTION ITEMS HEADING -->
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;
                                letter-spacing:0.1em;text-transform:uppercase;color:#94a3b8;
                                margin-bottom:4px;">Priority Action Items</div>
                    <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#64748b;
                                margin-bottom:16px;">Top controls requiring attention this week.</div>

                    <!-- ACTION ITEMS TABLE -->
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                           style="margin-bottom:32px;">
                      {action_items_html}
                    </table>

                    <!-- CTA BUTTON -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0"
                           style="margin:0 auto 8px auto;">
                      <tr>
                        <td align="center" style="border-radius:8px;mso-border-radius:8px;
                                                  background:#0f766e;">
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
                          <a href="{frontend_url}/compliance"
                             style="display:inline-block;background:#0f766e;color:#ffffff;
                                    text-decoration:none;font-family:Arial,Helvetica,sans-serif;
                                    font-size:15px;font-weight:700;padding:14px 32px;
                                    border-radius:8px;mso-border-radius:8px;
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
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
               style="max-width:600px;width:100%;">
          <tr>
            <td align="center" style="padding:24px 16px 32px 16px;">
              <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#94a3b8;
                          line-height:1.6;">
                You&rsquo;re receiving this because you&rsquo;re an admin at
                <strong style="color:#64748b;">{company_name}</strong> on TraceLayer.
                &middot;
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
