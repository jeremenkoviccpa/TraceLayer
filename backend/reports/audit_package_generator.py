"""
Audit Package PDF generator — comprehensive compliance PDF with AI narrative,
gap analysis, all data tables, and brand styling.
"""
import logging
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Brand colours ──────────────────────────────────────────────────────────────
INDIGO       = colors.HexColor("#4f46e5")
TEAL         = colors.HexColor("#0d9488")
GRAY_900     = colors.HexColor("#111827")
GRAY_700     = colors.HexColor("#374151")
GRAY_500     = colors.HexColor("#6b7280")
GRAY_300     = colors.HexColor("#d1d5db")
GRAY_100     = colors.HexColor("#f3f4f6")
GREEN        = colors.HexColor("#10b981")
AMBER        = colors.HexColor("#f59e0b")
RED          = colors.HexColor("#ef4444")
WHITE        = colors.white
TEAL_LIGHT   = colors.HexColor("#f0fdfa")
INDIGO_LIGHT = colors.HexColor("#eef2ff")

RISK_COLORS = {
    "critical": (colors.HexColor("#fee2e2"), colors.HexColor("#991b1b")),
    "high":     (colors.HexColor("#fef3c7"), colors.HexColor("#92400e")),
    "medium":   (colors.HexColor("#fef9c3"), colors.HexColor("#713f12")),
    "low":      (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
}

STATUS_COLORS: dict[str, tuple] = {
    "passing":     (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
    "warning":     (colors.HexColor("#fef3c7"), colors.HexColor("#92400e")),
    "failing":     (colors.HexColor("#fee2e2"), colors.HexColor("#991b1b")),
    "no_evidence": (GRAY_100,                   GRAY_500),
    "compliant":   (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
    "pending":     (colors.HexColor("#fef3c7"), colors.HexColor("#92400e")),
    "completed":   (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
    "overdue":     (colors.HexColor("#fee2e2"), colors.HexColor("#991b1b")),
    "in_progress": (colors.HexColor("#dbeafe"), colors.HexColor("#1e40af")),
    "open":        (colors.HexColor("#fef3c7"), colors.HexColor("#92400e")),
    "mitigated":   (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
    "remediated":  (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
    "scheduled":   (colors.HexColor("#dbeafe"), colors.HexColor("#1e40af")),
}


def _score_color(score: int):
    if score >= 80:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def _status_bg_fg(status: str) -> tuple:
    return STATUS_COLORS.get(status.lower().replace(" ", "_"), (GRAY_100, GRAY_500))


def _risk_bg_fg(risk_level: str) -> tuple:
    return RISK_COLORS.get(risk_level.lower(), (GRAY_100, GRAY_500))


def _styles() -> dict:
    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=28, textColor=GRAY_900, leading=34, spaceAfter=4),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=18, textColor=GRAY_900, leading=22, spaceBefore=16, spaceAfter=12),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY_900, leading=16, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=15),
        "body_ai": ParagraphStyle("body_ai", fontName="Helvetica", fontSize=10, textColor=GRAY_700, leading=16, spaceAfter=6),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, textColor=GRAY_500, leading=13),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=INDIGO, leading=12, spaceAfter=2),
        "label_teal": ParagraphStyle("label_teal", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=12, spaceAfter=2),
        "cover_eyebrow": ParagraphStyle("cover_eyebrow", fontName="Helvetica-Bold", fontSize=10, textColor=TEAL, leading=14, spaceAfter=8),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontName="Helvetica", fontSize=13, textColor=GRAY_500, leading=18),
        "meta_label": ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_500, leading=12),
        "meta_value": ParagraphStyle("meta_value", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY_900, leading=16),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=INDIGO, leading=11),
        "td": ParagraphStyle("td", fontName="Helvetica", fontSize=9, textColor=GRAY_900, leading=12),
        "td_mono": ParagraphStyle("td_mono", fontName="Courier", fontSize=8, textColor=GRAY_500, leading=11),
        "toc_title": ParagraphStyle("toc_title", fontName="Helvetica-Bold", fontSize=10, textColor=GRAY_900, leading=15),
        "toc_desc": ParagraphStyle("toc_desc", fontName="Helvetica", fontSize=9, textColor=GRAY_500, leading=13),
        "rec_num": ParagraphStyle("rec_num", fontName="Helvetica-Bold", fontSize=14, textColor=INDIGO, leading=18, alignment=TA_CENTER),
        "rec_text": ParagraphStyle("rec_text", fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=14),
        "ai_badge": ParagraphStyle("ai_badge", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, backColor=TEAL_LIGHT, leading=11),
        "no_data": ParagraphStyle("no_data", fontName="Helvetica-Oblique", fontSize=10, textColor=GRAY_500, leading=14),
    }


class _PageTemplate:
    def __init__(self, ctx: dict, st: dict):
        self.ctx = ctx
        self.st = st
        self._first = True

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        if self._first:
            # Cover — indigo top bar
            canvas.setFillColor(INDIGO)
            canvas.rect(0, h - 75 * mm, w, 75 * mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 22)
            canvas.drawString(20 * mm, h - 50 * mm, "TraceLayer")
            # Teal AI badge
            canvas.setFillColor(TEAL)
            canvas.roundRect(w - 72 * mm, h - 57 * mm, 52 * mm, 12 * mm, 3 * mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawCentredString(w - 46 * mm, h - 49 * mm, "AI AUDIT PACKAGE")
            self._first = False
        else:
            # Content pages — indigo left bar
            canvas.setFillColor(INDIGO)
            canvas.rect(0, 0, 5, h, fill=1, stroke=0)
            # Footer
            canvas.setFillColor(GRAY_300)
            canvas.rect(15 * mm, 12 * mm, w - 30 * mm, 0.4, fill=1, stroke=0)
            canvas.setFillColor(GRAY_500)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(
                15 * mm, 8 * mm,
                f"TraceLayer · {self.ctx['company_name']} · {self.ctx['framework_label']} AI Audit Package  —  CONFIDENTIAL",
            )
            canvas.drawRightString(w - 15 * mm, 8 * mm, f"Page {doc.page}")

        canvas.restoreState()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _section_header(story: list, num: int, eyebrow: str, title: str, st: dict) -> None:
    story.append(Paragraph(f"Section {num}  ·  {eyebrow}", st["label"]))
    story.append(Paragraph(title, st["h2"]))


def _ai_block(text: str, st: dict, W: float) -> list:
    """Teal-bordered AI narrative block."""
    if not text.strip():
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    badge = Table([[Paragraph("AI GENERATED", st["ai_badge"])]], colWidths=[W])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))

    body_rows = [[Paragraph(p, st["body_ai"])] for p in paragraphs]
    body = Table(body_rows, colWidths=[W])
    body.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))

    wrapper = Table([[badge], [body]], colWidths=[W])
    wrapper.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
        ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        # Extra bottom breathing room inside body
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    return [wrapper, Spacer(1, 4 * mm)]


def _data_table(headers: list, rows: list, col_widths: list, st: dict) -> Table:
    data = [[Paragraph(h, st["th"]) for h in headers]] + rows
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), INDIGO_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, INDIGO),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.4, GRAY_100),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _stat_cell(value: str, label: str, value_color, col_w: float) -> Table:
    return Table(
        [
            [Paragraph(value, ParagraphStyle(f"sv_{label}", fontName="Helvetica-Bold", fontSize=18, textColor=value_color, alignment=TA_CENTER))],
            [Paragraph(label,  ParagraphStyle(f"sl_{label}", fontName="Helvetica", fontSize=8, textColor=GRAY_500, alignment=TA_CENTER))],
        ],
        colWidths=[col_w],
    )


def _stats_row(cells: list, col_w: float, W: float) -> Table:
    n = len(cells)
    tbl = Table([cells], colWidths=[W / n] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INDIGO_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, INDIGO),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl


def _badge_para(text: str, status_key: str, font_size: int = 8) -> Paragraph:
    bg, fg = _status_bg_fg(status_key)
    return Paragraph(
        text,
        ParagraphStyle(
            f"badge_{status_key}",
            fontName="Helvetica-Bold",
            fontSize=font_size,
            textColor=fg,
            backColor=bg,
            leading=font_size + 3,
        ),
    )


def _no_data(label: str, st: dict) -> Paragraph:
    return Paragraph(
        f"No {label} recorded. Add records in TraceLayer to include them in your next audit package.",
        st["no_data"],
    )


# ── Main renderer ──────────────────────────────────────────────────────────────

def render_audit_package_pdf(context: dict) -> bytes:
    buf = BytesIO()
    st  = _styles()
    pt  = _PageTemplate(context, st)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm,  bottomMargin=22 * mm,
        onPage=pt,
    )

    story = []
    W = A4[0] - 40 * mm

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 80 * mm))

    story.append(Paragraph("AI-Powered Compliance Audit Package", st["cover_eyebrow"]))
    story.append(Paragraph(context["framework_label"], st["h1"]))
    story.append(Paragraph(
        "Comprehensive compliance evidence, AI-generated executive narrative, gap analysis & prioritised recommendations",
        st["cover_subtitle"],
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 6 * mm))

    meta = [
        ("Organization",    context["company_name"]),
        ("Framework",       context["framework_label"]),
        ("Date Generated",  context["generated_at"]),
        ("Compliance Score", f"{context['overall_score']}%"),
    ]
    meta_data = [[
        Table(
            [[Paragraph(lbl, st["meta_label"])], [Paragraph(val, st["meta_value"])]],
            colWidths=[W / 4 - 4 * mm],
        )
        for lbl, val in meta
    ]]
    meta_tbl = Table(meta_data, colWidths=[W / 4] * 4)
    meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        f"Report ID: {context['report_id']}    ·    Generated: {context['generated_at_full']}    ·    CONFIDENTIAL",
        st["small"],
    ))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    story.append(Paragraph("Contents", st["label"]))
    story.append(Paragraph("Audit Package Contents", st["h2"]))
    story.append(Spacer(1, 3 * mm))

    toc = [
        ("1",  "AI Executive Summary",         "AI-generated compliance posture narrative for board presentation"),
        ("2",  "Compliance Score Overview",    "Overall score, passing/failing controls breakdown"),
        ("3",  "Gap Analysis & Recommendations", "AI-identified gaps and prioritised remediation actions"),
        ("4",  "Evidence Records",             "Automated evidence collected per control"),
        ("5",  "Manual Controls",              "Manually attested compliance controls and their status"),
        ("6",  "Policy Library",               "Adopted compliance and security policies"),
        ("7",  "Risk Register",                "Identified risks with likelihood, impact, and status"),
        ("8",  "Penetration Testing",          "Security testing history and findings by severity"),
        ("9",  "Security Training",            "Employee security awareness training completion"),
        ("10", "Vendor Risk Management",       "Third-party vendor security assessments and certifications"),
        ("11", "Access Reviews",               "Periodic access control review records"),
    ]
    for num, title, desc in toc:
        row = Table(
            [[Paragraph(f"{num}.", st["label"]), Paragraph(title, st["toc_title"]), Paragraph(desc, st["toc_desc"])]],
            colWidths=[8 * mm, W * 0.38, W - 8 * mm - W * 0.38],
        )
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW",     (0, 0), (-1, -1), 0.3, GRAY_100),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ]))
        story.append(row)

    # Package summary stats
    story.append(Spacer(1, 6 * mm))
    stat_defs = [
        (str(context["total_evidence"]),             "Evidence Records",   INDIGO),
        (str(len(context["control_scores"])),         "Controls",           INDIGO),
        (str(len(context["risks"])),                  "Risks Tracked",      RED),
        (str(len(context["vendors"])),                "Vendors",            AMBER),
        (str(len(context["policies"])),               "Policies",           GREEN),
        (str(len(context["training"])),               "Training Records",   GRAY_700),
    ]
    n = len(stat_defs)
    story.append(_stats_row(
        [_stat_cell(v, lbl, c, W / n) for v, lbl, c in stat_defs],
        W / n, W,
    ))
    story.append(PageBreak())

    # ── SECTION 1: AI EXECUTIVE SUMMARY ──────────────────────────────────────
    _section_header(story, 1, "AI Narrative", "Executive Summary", st)
    story.extend(_ai_block(context.get("ai_executive_summary", ""), st, W))
    story.append(PageBreak())

    # ── SECTION 2: COMPLIANCE SCORE OVERVIEW ─────────────────────────────────
    _section_header(story, 2, "Compliance Overview", "Score Overview", st)

    score = context["overall_score"]
    sc    = _score_color(score)

    passing = sum(1 for c in context["control_scores"] if c["status"] == "passing")
    failing = sum(1 for c in context["control_scores"] if c["status"] == "failing")

    score_card = Table([[
        Table([
            [Paragraph(str(score), ParagraphStyle("sc_n", fontName="Helvetica-Bold", fontSize=32, textColor=sc, alignment=TA_CENTER))],
            [Paragraph("/ 100",   ParagraphStyle("sc_s", fontName="Helvetica", fontSize=9, textColor=GRAY_500, alignment=TA_CENTER))],
        ], colWidths=[30 * mm]),
        Table([
            [Paragraph("Overall Compliance Score", st["h3"])],
            [Paragraph(f"Evaluated across {len(context['control_scores'])} controls for {context['framework_label']}.", st["small"])],
            [Spacer(1, 2 * mm)],
            [Table([[
                _stat_cell(str(context["total_evidence"]), "Evidence",  GRAY_900, 30 * mm),
                _stat_cell(str(passing),                  "Passing",   GREEN,    30 * mm),
                _stat_cell(str(failing),                  "Failing",   RED,      30 * mm),
            ]], colWidths=[30 * mm, 30 * mm, 30 * mm])],
        ], colWidths=[W - 38 * mm]),
    ]], colWidths=[38 * mm, W - 38 * mm])
    score_card.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("BOX",            (0, 0), (0, 0), 2, sc),
        ("BACKGROUND",     (0, 0), (0, 0), INDIGO_LIGHT),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(score_card)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("Control Breakdown", st["h3"]))

    ctrl_rows = []
    for c in context["control_scores"]:
        missing = ", ".join(c["missing_types"]) if c["missing_types"] else "All covered"
        ctrl_rows.append([
            Paragraph(c["name"], st["td"]),
            _badge_para(c["status"].replace("_", " ").title(), c["status"]),
            Paragraph(f"{c['score']}%", ParagraphStyle("cscore", fontName="Helvetica-Bold", fontSize=9, textColor=_score_color(c["score"]), leading=12)),
            Paragraph(str(c["evidence_count"]), st["td"]),
            Paragraph(missing, st["small"]),
        ])
    story.append(_data_table(
        ["Control", "Status", "Score", "Evidence", "Missing Types"],
        ctrl_rows,
        [W * 0.27, W * 0.15, W * 0.10, W * 0.10, W * 0.38],
        st,
    ))
    story.append(PageBreak())

    # ── SECTION 3: GAP ANALYSIS & RECOMMENDATIONS ─────────────────────────────
    _section_header(story, 3, "AI Analysis", "Gap Analysis & Recommendations", st)
    story.extend(_ai_block(context.get("ai_gap_analysis", ""), st, W))

    recs = context.get("ai_recommendations", [])
    if recs:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("Prioritised Recommendations", st["h3"]))
        story.append(Spacer(1, 2 * mm))
        for i, rec in enumerate(recs, 1):
            card = Table([[
                Table([[Paragraph(str(i), st["rec_num"])]], colWidths=[14 * mm]),
                Paragraph(rec, st["rec_text"]),
            ]], colWidths=[20 * mm, W - 20 * mm])
            card.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND",    (0, 0), (0, 0), INDIGO_LIGHT),
                ("BOX",           (0, 0), (-1, -1), 0.5, INDIGO),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(card)
            story.append(Spacer(1, 2 * mm))
    story.append(PageBreak())

    # ── SECTION 4: EVIDENCE RECORDS ───────────────────────────────────────────
    _section_header(story, 4, "Automated Evidence", "Evidence Records by Control", st)

    by_cat = context["controls_by_category"]
    for ctrl in context["control_scores"]:
        story.append(Paragraph(ctrl["name"], st["h3"]))
        ev_list = by_cat.get(ctrl["category"], [])
        if ev_list:
            ev_rows = []
            for rec in ev_list[:50]:
                src = rec["source_id"]
                if len(src) > 45:
                    src = src[:45] + "…"
                ts = rec["timestamp"][:19].replace("T", " ")
                ev_rows.append([
                    Paragraph(rec["integration"],   ParagraphStyle("itag", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#5b21b6"), leading=11)),
                    Paragraph(rec["evidence_type"], st["td"]),
                    Paragraph(src,                  st["td_mono"]),
                    Paragraph(ts,                   st["small"]),
                ])
            story.append(_data_table(
                ["Integration", "Evidence Type", "Source ID", "Collected At"],
                ev_rows,
                [W * 0.15, W * 0.24, W * 0.38, W * 0.23],
                st,
            ))
            if len(ev_list) > 50:
                story.append(Paragraph(f"… and {len(ev_list) - 50} more records.", st["small"]))
        else:
            missing = ", ".join(ctrl["missing_types"]) if ctrl["missing_types"] else "all types"
            story.append(Paragraph(
                f"No automated evidence collected. Missing evidence types: {missing}.",
                st["no_data"],
            ))
        story.append(Spacer(1, 4 * mm))
    story.append(PageBreak())

    # ── SECTION 5: MANUAL CONTROLS ────────────────────────────────────────────
    _section_header(story, 5, "Attestations", "Manual Controls", st)
    mc_list = context["manual_controls"]
    if mc_list:
        mc_rows = []
        for m in mc_list:
            note = m["notes"]
            if len(note) > 80:
                note = note[:80] + "…"
            mc_rows.append([
                Paragraph(m["control_id"],  st["td"]),
                Paragraph(m["framework"].upper(), st["small"]),
                _badge_para(m["status"].title(), m["status"]),
                Paragraph(note or "—",     st["small"]),
                Paragraph(m["updated_at"], st["small"]),
            ])
        story.append(_data_table(
            ["Control ID", "Framework", "Status", "Notes", "Last Updated"],
            mc_rows,
            [W * 0.22, W * 0.10, W * 0.12, W * 0.40, W * 0.16],
            st,
        ))
    else:
        story.append(_no_data("manual controls", st))
    story.append(PageBreak())

    # ── SECTION 6: POLICY LIBRARY ─────────────────────────────────────────────
    _section_header(story, 6, "Governance", "Policy Library", st)
    policies = context["policies"]
    if policies:
        pol_rows = []
        for p in policies:
            adopted = p["has_content"]
            bg, fg = (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")) if adopted else (GRAY_100, GRAY_500)
            pol_rows.append([
                Paragraph(p["name"], st["td"]),
                Paragraph("Adopted" if adopted else "Draft", ParagraphStyle(
                    "polb", fontName="Helvetica-Bold", fontSize=8, textColor=fg, backColor=bg, leading=11,
                )),
                Paragraph(p["updated_at"], st["small"]),
            ])
        story.append(_data_table(
            ["Policy Name", "Status", "Last Updated"],
            pol_rows,
            [W * 0.60, W * 0.20, W * 0.20],
            st,
        ))
    else:
        story.append(_no_data("policies", st))
    story.append(PageBreak())

    # ── SECTION 7: RISK REGISTER ───────────────────────────────────────────────
    _section_header(story, 7, "Risk Management", "Risk Register", st)
    risks = context["risks"]
    if risks:
        risk_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for r in risks:
            risk_counts[r["risk_level"]] = risk_counts.get(r["risk_level"], 0) + 1
        open_count = sum(1 for r in risks if r["status"] == "open")

        story.append(_stats_row([
            _stat_cell(str(risk_counts["critical"]), "Critical", RED,   W / 4),
            _stat_cell(str(risk_counts["high"]),     "High",     AMBER, W / 4),
            _stat_cell(str(risk_counts["medium"]),   "Medium",   colors.HexColor("#d97706"), W / 4),
            _stat_cell(str(open_count),              "Open",     GRAY_900, W / 4),
        ], W / 4, W))
        story.append(Spacer(1, 4 * mm))

        risk_rows = []
        for r in risks:
            rl = r["risk_level"]
            rbg, rfg = _risk_bg_fg(rl)
            sbg, sfg = _status_bg_fg(r["status"])
            risk_rows.append([
                Paragraph(r["title"],    st["td"]),
                Paragraph(r["category"], st["small"]),
                Paragraph(rl.title(), ParagraphStyle(f"rlb_{rl}", fontName="Helvetica-Bold", fontSize=8, textColor=rfg, backColor=rbg, leading=11)),
                Paragraph(f"{r['likelihood']} × {r['impact']}", st["small"]),
                Paragraph(r["status"].title(), ParagraphStyle("rsb", fontName="Helvetica-Bold", fontSize=8, textColor=sfg, backColor=sbg, leading=11)),
            ])
        story.append(_data_table(
            ["Risk Title", "Category", "Risk Level", "L × I", "Status"],
            risk_rows,
            [W * 0.32, W * 0.20, W * 0.14, W * 0.14, W * 0.20],
            st,
        ))
    else:
        story.append(_no_data("risks", st))
    story.append(PageBreak())

    # ── SECTION 8: PENETRATION TESTING ────────────────────────────────────────
    _section_header(story, 8, "Security Testing", "Penetration Testing", st)
    pen_tests = context["pen_tests"]
    if pen_tests:
        pt_rows = []
        for pt in pen_tests:
            sbg, sfg = _status_bg_fg(pt["status"])
            has_critical = pt["critical_count"] > 0
            findings_color = RED if has_critical else (AMBER if pt["high_count"] > 0 else GRAY_900)
            total = pt["critical_count"] + pt["high_count"] + pt["medium_count"] + pt["low_count"]
            pt_rows.append([
                Paragraph(pt["vendor_name"],   st["td"]),
                Paragraph(pt["conducted_at"],  st["small"]),
                Paragraph(pt["status"].replace("_", " ").title(), ParagraphStyle(
                    "ptb", fontName="Helvetica-Bold", fontSize=8, textColor=sfg, backColor=sbg, leading=11,
                )),
                Paragraph(
                    f"{pt['critical_count']}C / {pt['high_count']}H / {pt['medium_count']}M / {pt['low_count']}L",
                    ParagraphStyle("findings", fontName="Helvetica-Bold", fontSize=8, textColor=findings_color, leading=11),
                ),
                Paragraph(str(total), st["td"]),
            ])
        story.append(_data_table(
            ["Vendor", "Date", "Status", "Findings (C/H/M/L)", "Total"],
            pt_rows,
            [W * 0.25, W * 0.16, W * 0.18, W * 0.30, W * 0.11],
            st,
        ))
        for pt in pen_tests:
            if pt["summary"]:
                story.append(Spacer(1, 3 * mm))
                story.append(Paragraph(f"{pt['vendor_name']} — Summary", st["h3"]))
                story.append(Paragraph(pt["summary"][:500], st["body"]))
    else:
        story.append(_no_data("penetration tests", st))
    story.append(PageBreak())

    # ── SECTION 9: SECURITY TRAINING ──────────────────────────────────────────
    _section_header(story, 9, "People", "Security Training", st)
    training = context["training"]
    if training:
        total_t    = len(training)
        completed  = sum(1 for t in training if t["status"] == "completed")
        overdue    = sum(1 for t in training if t["status"] == "overdue")
        pending    = total_t - completed - overdue
        rate       = round(completed / total_t * 100) if total_t else 0
        rate_color = GREEN if rate >= 80 else (AMBER if rate >= 50 else RED)

        story.append(_stats_row([
            _stat_cell(f"{rate}%",        "Completion Rate", rate_color, W / 4),
            _stat_cell(str(completed),    "Completed",       GREEN,      W / 4),
            _stat_cell(str(overdue),      "Overdue",         RED,        W / 4),
            _stat_cell(str(pending),      "Pending",         AMBER,      W / 4),
        ], W / 4, W))
        story.append(Spacer(1, 4 * mm))

        tr_rows = []
        for t in training[:100]:
            tr_rows.append([
                Paragraph(t["title"],           st["td"]),
                Paragraph(t["assignee_email"],  st["small"]),
                _badge_para(t["status"].title(), t["status"]),
                Paragraph(t["due_date"]       or "—", st["small"]),
                Paragraph(t["completed_at"]   or "—", st["small"]),
            ])
        story.append(_data_table(
            ["Training", "Assignee", "Status", "Due", "Completed"],
            tr_rows,
            [W * 0.32, W * 0.27, W * 0.13, W * 0.14, W * 0.14],
            st,
        ))
        if len(training) > 100:
            story.append(Paragraph(f"… and {len(training) - 100} additional records.", st["small"]))
    else:
        story.append(_no_data("training records", st))
    story.append(PageBreak())

    # ── SECTION 10: VENDOR RISK ────────────────────────────────────────────────
    _section_header(story, 10, "Third-Party Risk", "Vendor Risk Management", st)
    vendors = context["vendors"]
    if vendors:
        v_rows = []
        for v in vendors:
            rl = v["risk_level"]
            rbg, rfg = _risk_bg_fg(rl)
            certs = [
                c for flag, c in [
                    (v["soc2_certified"],     "SOC 2"),
                    (v["iso27001_certified"], "ISO 27001"),
                    (v["hipaa_certified"],    "HIPAA"),
                ] if flag
            ]
            v_rows.append([
                Paragraph(v["name"],            st["td"]),
                Paragraph(v["category"].title(), st["small"]),
                Paragraph(rl.title(), ParagraphStyle(f"vb_{rl}", fontName="Helvetica-Bold", fontSize=8, textColor=rfg, backColor=rbg, leading=11)),
                Paragraph(", ".join(certs) or "None", st["small"]),
                Paragraph(v["review_date"],     st["small"]),
            ])
        story.append(_data_table(
            ["Vendor", "Category", "Risk Level", "Certifications", "Last Reviewed"],
            v_rows,
            [W * 0.26, W * 0.16, W * 0.14, W * 0.28, W * 0.16],
            st,
        ))
    else:
        story.append(_no_data("vendors", st))
    story.append(PageBreak())

    # ── SECTION 11: ACCESS REVIEWS ─────────────────────────────────────────────
    _section_header(story, 11, "Access Control", "Access Reviews", st)
    access_reviews = context["access_reviews"]
    if access_reviews:
        ar_rows = []
        for ar in access_reviews:
            ar_rows.append([
                Paragraph(ar["title"],              st["td"]),
                Paragraph(ar["period"],             st["small"]),
                _badge_para(ar["status"].replace("_", " ").title(), ar["status"]),
                Paragraph(str(ar["users_reviewed"]), st["td"]),
                Paragraph(str(ar["access_changes"]), st["td"]),
                Paragraph(ar["completed_at"],        st["small"]),
            ])
        story.append(_data_table(
            ["Title", "Period", "Status", "Users", "Changes", "Completed"],
            ar_rows,
            [W * 0.26, W * 0.12, W * 0.14, W * 0.10, W * 0.10, W * 0.28],
            st,
        ))
    else:
        story.append(_no_data("access reviews", st))

    doc.build(story)
    return buf.getvalue()
