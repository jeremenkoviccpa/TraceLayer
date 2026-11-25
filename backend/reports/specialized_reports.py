"""
Specialized compliance report PDF generators.

Covers: breach notification, CERT-In incident, NIS2 CSIRT, DSAR log,
management review, vendor risk, training completion, access review.
"""
import logging
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Colours ────────────────────────────────────────────────────────────────────
TEAL        = colors.HexColor("#0f766e")
TEAL_LIGHT  = colors.HexColor("#f0fdfa")
TEAL_BORDER = colors.HexColor("#99f6e4")
GRAY_900    = colors.HexColor("#111827")
GRAY_700    = colors.HexColor("#374151")
GRAY_500    = colors.HexColor("#6b7280")
GRAY_300    = colors.HexColor("#d1d5db")
GRAY_100    = colors.HexColor("#f3f4f6")
GREEN       = colors.HexColor("#10b981")
GREEN_LIGHT = colors.HexColor("#d1fae5")
GREEN_DARK  = colors.HexColor("#065f46")
AMBER       = colors.HexColor("#f59e0b")
AMBER_LIGHT = colors.HexColor("#fef3c7")
AMBER_DARK  = colors.HexColor("#92400e")
RED         = colors.HexColor("#ef4444")
RED_LIGHT   = colors.HexColor("#fee2e2")
RED_DARK    = colors.HexColor("#991b1b")
BLUE        = colors.HexColor("#3b82f6")
BLUE_LIGHT  = colors.HexColor("#dbeafe")
BLUE_DARK   = colors.HexColor("#1e40af")
WHITE       = colors.white

STATUS_BG_FG = {
    "complete":     (GREEN_LIGHT,  GREEN_DARK),
    "completed":    (GREEN_LIGHT,  GREEN_DARK),
    "compliant":    (GREEN_LIGHT,  GREEN_DARK),
    "resolved":     (GREEN_LIGHT,  GREEN_DARK),
    "closed":       (GREEN_LIGHT,  GREEN_DARK),
    "satisfactory": (GREEN_LIGHT,  GREEN_DARK),
    "low":          (GREEN_LIGHT,  GREEN_DARK),
    "passed":       (GREEN_LIGHT,  GREEN_DARK),
    "pending":      (AMBER_LIGHT,  AMBER_DARK),
    "in_progress":  (BLUE_LIGHT,   BLUE_DARK),
    "open":         (BLUE_LIGHT,   BLUE_DARK),
    "investigating":(AMBER_LIGHT,  AMBER_DARK),
    "contained":    (AMBER_LIGHT,  AMBER_DARK),
    "overdue":      (RED_LIGHT,    RED_DARK),
    "failed":       (RED_LIGHT,    RED_DARK),
    "error":        (RED_LIGHT,    RED_DARK),
    "critical":     (RED_LIGHT,    RED_DARK),
    "high":         (RED_LIGHT,    RED_DARK),
    "medium":       (AMBER_LIGHT,  AMBER_DARK),
    "needs_improvement": (AMBER_LIGHT, AMBER_DARK),
    "critical_findings": (RED_LIGHT, RED_DARK),
    "refused":      (RED_LIGHT,    RED_DARK),
}


def _status_bg_fg(status: str):
    return STATUS_BG_FG.get(str(status).lower(), (GRAY_100, GRAY_500))


def _st() -> dict:
    return {
        "h1":    ParagraphStyle("h1",    fontName="Helvetica-Bold",   fontSize=22, textColor=GRAY_900, leading=28, spaceAfter=4),
        "h2":    ParagraphStyle("h2",    fontName="Helvetica-Bold",   fontSize=14, textColor=GRAY_900, leading=18, spaceBefore=14, spaceAfter=8),
        "h3":    ParagraphStyle("h3",    fontName="Helvetica-Bold",   fontSize=11, textColor=GRAY_900, leading=15, spaceBefore=8, spaceAfter=4),
        "body":  ParagraphStyle("body",  fontName="Helvetica",        fontSize=10, textColor=GRAY_900, leading=14),
        "small": ParagraphStyle("small", fontName="Helvetica",        fontSize=9,  textColor=GRAY_500, leading=13),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold",   fontSize=8,  textColor=TEAL,     leading=11, spaceAfter=2),
        "th":    ParagraphStyle("th",    fontName="Helvetica-Bold",   fontSize=8,  textColor=WHITE,    leading=11),
        "td":    ParagraphStyle("td",    fontName="Helvetica",        fontSize=9,  textColor=GRAY_900, leading=12),
        "td_sm": ParagraphStyle("td_sm", fontName="Helvetica",        fontSize=8,  textColor=GRAY_700, leading=11),
        "badge": ParagraphStyle("badge", fontName="Helvetica-Bold",   fontSize=8,  textColor=GRAY_500, leading=11),
        "stat_n":ParagraphStyle("stat_n",fontName="Helvetica-Bold",   fontSize=20, textColor=TEAL,     leading=24),
        "stat_l":ParagraphStyle("stat_l",fontName="Helvetica",        fontSize=8,  textColor=GRAY_500, leading=11),
        "no_data":ParagraphStyle("nd",   fontName="Helvetica-Oblique",fontSize=10, textColor=GRAY_500, leading=14),
    }


class _Footer:
    def __init__(self, company: str, report_title: str):
        self.company = company
        self.title = report_title

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, _ = A4
        canvas.setFillColor(TEAL)
        canvas.rect(0, 0, 4, A4[1], fill=1, stroke=0)
        canvas.setFillColor(GRAY_300)
        canvas.rect(15 * mm, 12 * mm, w - 30 * mm, 0.4, fill=1, stroke=0)
        canvas.setFillColor(GRAY_500)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(15 * mm, 8 * mm, f"TraceLayer · {self.company} · {self.title}  —  CONFIDENTIAL")
        canvas.drawRightString(w - 15 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()


def _build_doc(title: str, ctx: dict) -> SimpleDocTemplate:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
    )
    doc._buf = buf
    doc._footer = _Footer(ctx["company_name"], title)
    return doc


def _finish(doc: SimpleDocTemplate, story: list) -> bytes:
    doc.build(story, onFirstPage=doc._footer, onLaterPages=doc._footer)
    return doc._buf.getvalue()


def _cover_strip(story: list, report_title: str, ctx: dict, color=TEAL) -> None:
    st = _st()
    story.append(Spacer(1, 4 * mm))
    w, _ = A4
    col_w = w - 40 * mm
    strip = Table(
        [[Paragraph(report_title, ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=18, textColor=WHITE, leading=22))]],
        colWidths=[col_w],
    )
    strip.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [3]),
    ]))
    story.append(strip)
    story.append(Spacer(1, 3 * mm))
    meta = Table([[
        Paragraph(f"Company: <b>{ctx['company_name']}</b>", st["small"]),
        Paragraph(f"Generated: <b>{ctx['generated_at']}</b>", st["small"]),
    ]], colWidths=[col_w / 2, col_w / 2])
    meta.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(meta)
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY_300))
    story.append(Spacer(1, 5 * mm))


def _stats_bar(story: list, stats: list[tuple[str, str]]) -> None:
    """Render a horizontal row of (label, value) stat boxes."""
    st = _st()
    w, _ = A4
    col_w = (w - 40 * mm) / len(stats)
    row = [[Paragraph(val, st["stat_n"]), Paragraph(lbl, st["stat_l"])] for lbl, val in stats]
    # flatten to one row of alternating n/l
    cells = []
    for lbl, val in stats:
        cells.append(Table([[Paragraph(val, st["stat_n"])], [Paragraph(lbl, st["stat_l"])]], colWidths=[col_w - 6]))
    tbl = Table([cells], colWidths=[col_w] * len(stats))
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("LINEAFTER",     (0, 0), (-2, -1), 0.5, TEAL_BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _data_table(story: list, headers: list[str], rows: list[list], col_widths: list[float]) -> None:
    st = _st()
    if not rows:
        story.append(Paragraph("No records found.", st["no_data"]))
        story.append(Spacer(1, 4 * mm))
        return
    header_row = [Paragraph(h, st["th"]) for h in headers]
    table_data = [header_row] + [[Paragraph(str(c), st["td"]) for c in row] for row in rows]
    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  TEAL),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRAY_300),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, GRAY_100]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ])
    tbl.setStyle(style)
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _badge_cell(status: str, st: dict) -> Paragraph:
    bg, fg = _status_bg_fg(status)
    label = status.replace("_", " ").title()
    return Paragraph(
        f'<font color="#{fg.hexval()[1:]}">{label}</font>',
        st["badge"],
    )


def _fmt(dt) -> str:
    if dt is None:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)


def _fmt_d(dt) -> str:
    if dt is None:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(dt)


# ── 1. Data Breach Notification Report ────────────────────────────────────────

def render_breach_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("Data Breach Notification Report", ctx)
    _cover_strip(story, "Data Breach Notification Report", ctx)

    breaches = ctx.get("breaches", [])
    total = len(breaches)
    notified = sum(1 for b in breaches if b.get("dpa_notified_at") or b.get("poverenik_notified_at") or b.get("dpbi_notified_at"))
    within_72h = sum(1 for b in breaches if b.get("within_72h"))
    high_sev = sum(1 for b in breaches if b.get("severity") in ("high", "critical"))

    _stats_bar(story, [
        ("Total Breaches", str(total)),
        ("Authorities Notified", str(notified)),
        ("Within 72h", str(within_72h)),
        ("High / Critical", str(high_sev)),
    ])

    story.append(Paragraph("Breach Records", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Title", "Occurred", "Severity", "Status", "DPA Notified", "Poverenik", "DPBI", "Ref #"], [
        [
            b.get("title", "")[:50],
            _fmt_d(b.get("occurred_at")),
            b.get("severity", "").title(),
            b.get("status", "").replace("_", " ").title(),
            _fmt(b.get("dpa_notified_at")),
            _fmt(b.get("poverenik_notified_at")),
            _fmt(b.get("dpbi_notified_at")),
            b.get("dpbi_ref_number") or b.get("poverenik_ref_number") or "—",
        ]
        for b in breaches
    ], [cw * 0.20, cw * 0.09, cw * 0.07, cw * 0.09, cw * 0.13, cw * 0.13, cw * 0.12, cw * 0.17])

    story.append(Paragraph("Regulatory Obligations", st["h2"]))
    story.append(Paragraph(
        "GDPR Art. 33 / Serbian LPDP Art. 53 require notification to the supervisory authority within <b>72 hours</b> "
        "of becoming aware of a breach. DPDP Act requires notification to DPBI. High-risk breaches must also be "
        "communicated to affected individuals without undue delay.",
        st["body"],
    ))

    return _finish(doc, story)


# ── 2. CERT-In 6-Hour Incident Report ─────────────────────────────────────────

def render_certin_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("CERT-In Incident Report", ctx)
    _cover_strip(story, "CERT-In Incident Reporting Log", ctx, color=RED)

    incidents = ctx.get("incidents", [])
    total = len(incidents)
    reported = sum(1 for i in incidents if i.get("certin_reported_at"))
    in_6h = sum(1 for i in incidents if i.get("within_6h"))
    unreported = sum(1 for i in incidents if not i.get("certin_reported_at"))

    _stats_bar(story, [
        ("Total Incidents", str(total)),
        ("Reported to CERT-In", str(reported)),
        ("Reported ≤ 6 Hours", str(in_6h)),
        ("Unreported", str(unreported)),
    ])

    story.append(Paragraph("Incident Records", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Title", "Detected", "Severity", "Systems", "CERT-In Reported", "Ref #", "Time to Report"], [
        [
            i.get("title", "")[:40],
            _fmt(i.get("detected_at")),
            i.get("severity", "").title(),
            (i.get("affected_systems") or "")[:30],
            _fmt(i.get("certin_reported_at")),
            i.get("certin_ref_number") or "—",
            i.get("hours_to_report") or "—",
        ]
        for i in incidents
    ], [cw * 0.22, cw * 0.11, cw * 0.07, cw * 0.16, cw * 0.14, cw * 0.14, cw * 0.16])

    story.append(Paragraph("CERT-In Reporting Obligation", st["h2"]))
    story.append(Paragraph(
        "MeitY CERT-In Directions 2022 (Section 6(a)) require all service providers, intermediaries, data centres, "
        "and government organisations to mandatorily report cyber incidents to CERT-In <b>within 6 hours</b> of "
        "noticing such incidents. Incidents include data breaches, ransomware, unauthorised access, and denial-of-service attacks.",
        st["body"],
    ))

    return _finish(doc, story)


# ── 3. NIS2 CSIRT Incident Report ─────────────────────────────────────────────

def render_nis2_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("NIS2 CSIRT Incident Report", ctx)
    _cover_strip(story, "NIS2 3-Stage Incident Reporting Log", ctx, color=BLUE)

    incidents = ctx.get("incidents", [])
    total = len(incidents)
    early_ok = sum(1 for i in incidents if i.get("nis2_early_warning_at"))
    notified = sum(1 for i in incidents if i.get("nis2_notified_at"))
    final_ok = sum(1 for i in incidents if i.get("nis2_final_report_at"))

    _stats_bar(story, [
        ("Total Incidents", str(total)),
        ("Early Warnings (24h)", str(early_ok)),
        ("Notifications (72h)", str(notified)),
        ("Final Reports (1mo)", str(final_ok)),
    ])

    story.append(Paragraph("3-Stage NIS2 Reporting Status", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Title", "Detected", "Sev", "Early Warning", "Notification (72h)", "Final Report", "CSIRT Ref"], [
        [
            i.get("title", "")[:35],
            _fmt(i.get("detected_at")),
            i.get("severity", "").title(),
            _fmt(i.get("nis2_early_warning_at")),
            _fmt(i.get("nis2_notified_at")),
            _fmt(i.get("nis2_final_report_at")),
            i.get("nis2_ref_number") or "—",
        ]
        for i in incidents
    ], [cw * 0.20, cw * 0.11, cw * 0.05, cw * 0.15, cw * 0.16, cw * 0.16, cw * 0.17])

    story.append(Paragraph("NIS2 Reporting Obligations (Art. 23)", st["h2"]))
    story.append(Paragraph(
        "NIS2 Directive Art. 23 imposes a three-stage reporting obligation for significant incidents: "
        "<b>Stage 1</b> — early warning to national CSIRT or competent authority within 24 hours of becoming aware. "
        "<b>Stage 2</b> — incident notification within 72 hours including initial assessment of severity and indicators of compromise. "
        "<b>Stage 3</b> — final report within one month with a full description, root cause, and mitigation measures applied.",
        st["body"],
    ))

    return _finish(doc, story)


# ── 4. DSAR / Subject Request Log ─────────────────────────────────────────────

def render_dsar_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("DSAR Response Log", ctx)
    _cover_strip(story, "Data Subject Access Request Log", ctx)

    requests = ctx.get("requests", [])
    total = len(requests)
    completed = sum(1 for r in requests if r.get("status") == "completed")
    on_time = sum(1 for r in requests if r.get("on_time"))
    pending = sum(1 for r in requests if r.get("status") in ("pending", "in_progress"))
    refused = sum(1 for r in requests if r.get("status") == "refused")

    _stats_bar(story, [
        ("Total Requests", str(total)),
        ("Completed On Time", str(on_time)),
        ("Pending", str(pending)),
        ("Refused", str(refused)),
    ])

    story.append(Paragraph("Request Log", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Requester", "Type", "Regulation", "Received", "Due", "Status", "Completed", "Days Taken"], [
        [
            r.get("requester_name", "")[:25],
            r.get("request_type", "").replace("_", " ").title(),
            r.get("regulation", "").upper(),
            _fmt_d(r.get("received_at")),
            _fmt_d(r.get("due_at")),
            r.get("status", "").replace("_", " ").title(),
            _fmt_d(r.get("completed_at")),
            r.get("days_taken") or "—",
        ]
        for r in requests
    ], [cw * 0.16, cw * 0.10, cw * 0.09, cw * 0.10, cw * 0.10, cw * 0.10, cw * 0.10, cw * 0.09])

    by_reg: dict[str, int] = {}
    for r in requests:
        by_reg[r.get("regulation", "gdpr")] = by_reg.get(r.get("regulation", "gdpr"), 0) + 1
    if by_reg:
        story.append(Paragraph("Requests by Regulation", st["h2"]))
        _data_table(story, ["Regulation", "Total Requests"], [
            [reg.upper(), str(count)] for reg, count in sorted(by_reg.items())
        ], [cw * 0.5, cw * 0.5])

    story.append(Paragraph("Regulatory SLA", st["h2"]))
    story.append(Paragraph(
        "GDPR Art. 12 requires responses within <b>30 days</b> (extendable to 60 days for complex requests). "
        "Indian DPDP Act requires responses within <b>30 days</b>. Serbian LPDP Art. 26-39 also mandates a 30-day response window. "
        "CCPA requires responses within <b>45 days</b>.",
        st["body"],
    ))

    return _finish(doc, story)


# ── 5. Management Review Summary ──────────────────────────────────────────────

def render_mgmt_review_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("Management Review Summary", ctx)
    _cover_strip(story, "Management Review Summary", ctx)

    reviews = ctx.get("reviews", [])
    total = len(reviews)
    sat = sum(1 for r in reviews if r.get("outcome") == "satisfactory")
    needs = sum(1 for r in reviews if r.get("outcome") == "needs_improvement")
    critical = sum(1 for r in reviews if r.get("outcome") == "critical_findings")

    _stats_bar(story, [
        ("Total Reviews", str(total)),
        ("Satisfactory", str(sat)),
        ("Needs Improvement", str(needs)),
        ("Critical Findings", str(critical)),
    ])

    story.append(Paragraph("Review Records", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Date", "Attendees", "Outcome", "Next Review", "Open Action Items"], [
        [
            _fmt_d(r.get("review_date")),
            (r.get("attendees") or "")[:40],
            r.get("outcome", "").replace("_", " ").title(),
            _fmt_d(r.get("next_review_date")),
            str(r.get("open_action_items", 0)),
        ]
        for r in reviews
    ], [cw * 0.12, cw * 0.30, cw * 0.18, cw * 0.14, cw * 0.12])

    for r in reviews:
        if r.get("decisions") or r.get("inputs_summary"):
            story.append(KeepTogether([
                Paragraph(f"Review — {_fmt_d(r.get('review_date'))}", st["h3"]),
                Paragraph(f"<b>Inputs reviewed:</b> {r.get('inputs_summary') or '—'}", st["body"]),
                Spacer(1, 2 * mm),
                Paragraph(f"<b>Decisions:</b> {r.get('decisions') or '—'}", st["body"]),
                Spacer(1, 3 * mm),
            ]))

    return _finish(doc, story)


# ── 6. Vendor Risk Report ─────────────────────────────────────────────────────

def render_vendor_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("Vendor Risk Report", ctx)
    _cover_strip(story, "Vendor Risk Assessment Report", ctx)

    vendors = ctx.get("vendors", [])
    total = len(vendors)
    high_risk = sum(1 for v in vendors if v.get("risk_level") in ("high", "critical"))
    certified = sum(1 for v in vendors if v.get("soc2_certified") or v.get("iso27001_certified"))
    unreviewed = sum(1 for v in vendors if not v.get("review_date"))

    _stats_bar(story, [
        ("Total Vendors", str(total)),
        ("High / Critical Risk", str(high_risk)),
        ("Security Certified", str(certified)),
        ("Never Reviewed", str(unreviewed)),
    ])

    story.append(Paragraph("Vendor Risk Register", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Vendor", "Category", "Risk Level", "SOC 2", "ISO 27001", "HIPAA", "Last Review"], [
        [
            v.get("name", "")[:30],
            v.get("category", "").title(),
            v.get("risk_level", "").title(),
            "✓" if v.get("soc2_certified") else "—",
            "✓" if v.get("iso27001_certified") else "—",
            "✓" if v.get("hipaa_certified") else "—",
            _fmt_d(v.get("review_date")),
        ]
        for v in sorted(vendors, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.get("risk_level", "low"), 4))
    ], [cw * 0.22, cw * 0.12, cw * 0.10, cw * 0.08, cw * 0.10, cw * 0.08, cw * 0.10])

    cats: dict[str, int] = {}
    for v in vendors:
        cats[v.get("category", "other")] = cats.get(v.get("category", "other"), 0) + 1
    if cats:
        story.append(Paragraph("Vendors by Category", st["h2"]))
        _data_table(story, ["Category", "Count"], [
            [cat.title(), str(n)] for cat, n in sorted(cats.items())
        ], [cw * 0.5, cw * 0.5])

    return _finish(doc, story)


# ── 7. Training Completion Report ─────────────────────────────────────────────

def render_training_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("Training Completion Report", ctx)
    _cover_strip(story, "Security Training Completion Report", ctx)

    records = ctx.get("records", [])
    total = len(records)
    completed = sum(1 for r in records if r.get("status") == "completed")
    overdue = sum(1 for r in records if r.get("status") == "overdue")
    passed = sum(1 for r in records if r.get("quiz_passed"))
    rate = f"{int(completed/total*100)}%" if total else "—"

    _stats_bar(story, [
        ("Total Assigned", str(total)),
        ("Completed", str(completed)),
        ("Overdue", str(overdue)),
        ("Completion Rate", rate),
    ])

    story.append(Paragraph("Training Records", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Assignee", "Training", "Status", "Due", "Completed", "Score", "Passed"], [
        [
            r.get("assignee_email", "")[:28],
            r.get("title", "")[:30],
            r.get("status", "").replace("_", " ").title(),
            _fmt_d(r.get("due_date")),
            _fmt_d(r.get("completed_at")),
            f"{r['quiz_score']}%" if r.get("quiz_score") is not None else "—",
            "Yes" if r.get("quiz_passed") else ("No" if r.get("completed_at") else "—"),
        ]
        for r in records
    ], [cw * 0.20, cw * 0.22, cw * 0.09, cw * 0.09, cw * 0.11, cw * 0.07, cw * 0.07])

    titles: dict[str, dict] = {}
    for r in records:
        t = r.get("title", "Unknown")
        if t not in titles:
            titles[t] = {"total": 0, "completed": 0, "passed": 0}
        titles[t]["total"] += 1
        if r.get("status") == "completed":
            titles[t]["completed"] += 1
        if r.get("quiz_passed"):
            titles[t]["passed"] += 1
    if titles:
        story.append(Paragraph("Completion by Training Module", st["h2"]))
        _data_table(story, ["Training Module", "Assigned", "Completed", "Passed", "Completion %"], [
            [name, str(d["total"]), str(d["completed"]), str(d["passed"]),
             f"{int(d['completed']/d['total']*100)}%" if d["total"] else "—"]
            for name, d in titles.items()
        ], [cw * 0.40, cw * 0.12, cw * 0.12, cw * 0.12, cw * 0.14])

    return _finish(doc, story)


# ── 8. Access Review Report ───────────────────────────────────────────────────

def render_access_review_report(ctx: dict) -> bytes:
    story: list = []
    st = _st()
    doc = _build_doc("Access Review Report", ctx)
    _cover_strip(story, "Access Review Report", ctx)

    reviews = ctx.get("reviews", [])
    total = len(reviews)
    completed = sum(1 for r in reviews if r.get("status") == "completed")
    in_prog = sum(1 for r in reviews if r.get("status") == "in_progress")
    total_users = sum(r.get("users_reviewed", 0) for r in reviews)
    total_changes = sum(r.get("access_changes", 0) for r in reviews)

    _stats_bar(story, [
        ("Total Reviews", str(total)),
        ("Completed", str(completed)),
        ("Users Reviewed", str(total_users)),
        ("Access Changes", str(total_changes)),
    ])

    story.append(Paragraph("Access Review Records", st["h2"]))
    w, _ = A4
    cw = w - 40 * mm
    _data_table(story, ["Period", "Title", "Status", "Due", "Completed", "Users Reviewed", "Access Changes"], [
        [
            r.get("period", "")[:15],
            r.get("title", "")[:30],
            r.get("status", "").replace("_", " ").title(),
            _fmt_d(r.get("due_date")),
            _fmt_d(r.get("completed_at")),
            str(r.get("users_reviewed", 0)),
            str(r.get("access_changes", 0)),
        ]
        for r in reviews
    ], [cw * 0.12, cw * 0.22, cw * 0.10, cw * 0.10, cw * 0.10, cw * 0.12, cw * 0.12])

    story.append(Paragraph("About Access Reviews", st["h2"]))
    story.append(Paragraph(
        "Periodic access reviews verify that user permissions remain appropriate and least-privilege principles are enforced. "
        "SOC 2 CC6.3 requires that organisations use a process to remove access once it is no longer needed. "
        "ISO 27001 A.9.2.5 requires formal user access review at regular intervals. "
        "Access changes identified during reviews should be actioned and evidenced.",
        st["body"],
    ))

    return _finish(doc, story)
