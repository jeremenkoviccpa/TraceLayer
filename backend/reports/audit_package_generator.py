"""
Audit Package PDF generator — Vanta-level compliance PDF with management assertion,
system description, criteria test results, control test methodology, AI narrative,
gap analysis, risk heatmap, and all data tables.
"""
import logging
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Brand colours ──────────────────────────────────────────────────────────────
TEAL         = colors.HexColor("#0f766e")
TEAL_MID     = colors.HexColor("#0d9488")
TEAL_LIGHT   = colors.HexColor("#f0fdfa")
TEAL_BORDER  = colors.HexColor("#99f6e4")
INDIGO       = colors.HexColor("#4f46e5")
INDIGO_LIGHT = colors.HexColor("#eef2ff")
GRAY_900     = colors.HexColor("#111827")
GRAY_700     = colors.HexColor("#374151")
GRAY_500     = colors.HexColor("#6b7280")
GRAY_300     = colors.HexColor("#d1d5db")
GRAY_100     = colors.HexColor("#f3f4f6")
GREEN        = colors.HexColor("#10b981")
GREEN_LIGHT  = colors.HexColor("#d1fae5")
GREEN_DARK   = colors.HexColor("#065f46")
AMBER        = colors.HexColor("#f59e0b")
AMBER_LIGHT  = colors.HexColor("#fef3c7")
AMBER_DARK   = colors.HexColor("#92400e")
RED          = colors.HexColor("#ef4444")
RED_LIGHT    = colors.HexColor("#fee2e2")
RED_DARK     = colors.HexColor("#991b1b")
WHITE        = colors.white

RISK_COLORS = {
    "critical": (RED_LIGHT,   RED_DARK),
    "high":     (AMBER_LIGHT, AMBER_DARK),
    "medium":   (colors.HexColor("#fef9c3"), colors.HexColor("#713f12")),
    "low":      (GREEN_LIGHT, GREEN_DARK),
}

STATUS_COLORS: dict[str, tuple] = {
    "passing":     (GREEN_LIGHT,  GREEN_DARK),
    "warning":     (AMBER_LIGHT,  AMBER_DARK),
    "failing":     (RED_LIGHT,    RED_DARK),
    "no_evidence": (GRAY_100,     GRAY_500),
    "compliant":   (GREEN_LIGHT,  GREEN_DARK),
    "pending":     (AMBER_LIGHT,  AMBER_DARK),
    "completed":   (GREEN_LIGHT,  GREEN_DARK),
    "overdue":     (RED_LIGHT,    RED_DARK),
    "in_progress": (colors.HexColor("#dbeafe"), colors.HexColor("#1e40af")),
    "open":        (AMBER_LIGHT,  AMBER_DARK),
    "mitigated":   (GREEN_LIGHT,  GREEN_DARK),
    "remediated":  (GREEN_LIGHT,  GREEN_DARK),
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
        "h4": ParagraphStyle("h4", fontName="Helvetica-Bold", fontSize=10, textColor=TEAL, leading=14, spaceBefore=6, spaceAfter=4),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=15),
        "body_ai": ParagraphStyle("body_ai", fontName="Helvetica", fontSize=10, textColor=GRAY_700, leading=16, spaceAfter=6),
        "body_formal": ParagraphStyle("body_formal", fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=16, spaceAfter=4),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, textColor=GRAY_500, leading=13),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=12, spaceAfter=2),
        "label_gray": ParagraphStyle("label_gray", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_500, leading=12, spaceAfter=2),
        "cover_eyebrow": ParagraphStyle("cover_eyebrow", fontName="Helvetica-Bold", fontSize=10, textColor=TEAL, leading=14, spaceAfter=8),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontName="Helvetica", fontSize=13, textColor=GRAY_500, leading=18),
        "meta_label": ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_500, leading=12),
        "meta_value": ParagraphStyle("meta_value", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY_900, leading=16),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=11),
        "th_dark": ParagraphStyle("th_dark", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE, leading=11),
        "td": ParagraphStyle("td", fontName="Helvetica", fontSize=9, textColor=GRAY_900, leading=12),
        "td_mono": ParagraphStyle("td_mono", fontName="Courier", fontSize=8, textColor=GRAY_500, leading=11),
        "toc_title": ParagraphStyle("toc_title", fontName="Helvetica-Bold", fontSize=10, textColor=GRAY_900, leading=15),
        "toc_desc": ParagraphStyle("toc_desc", fontName="Helvetica", fontSize=9, textColor=GRAY_500, leading=13),
        "rec_num": ParagraphStyle("rec_num", fontName="Helvetica-Bold", fontSize=14, textColor=TEAL, leading=18, alignment=TA_CENTER),
        "rec_text": ParagraphStyle("rec_text", fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=14),
        "ai_badge": ParagraphStyle("ai_badge", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, backColor=TEAL_LIGHT, leading=11),
        "no_data": ParagraphStyle("no_data", fontName="Helvetica-Oblique", fontSize=10, textColor=GRAY_500, leading=14),
        "sig_label": ParagraphStyle("sig_label", fontName="Helvetica", fontSize=8, textColor=GRAY_500, leading=12),
        "sig_value": ParagraphStyle("sig_value", fontName="Helvetica-Bold", fontSize=10, textColor=GRAY_900, leading=14),
        "methodology": ParagraphStyle("methodology", fontName="Helvetica-Oblique", fontSize=9, textColor=GRAY_700, leading=13, spaceAfter=3),
        "pass_badge": ParagraphStyle("pass_badge", fontName="Helvetica-Bold", fontSize=9, textColor=GREEN_DARK, backColor=GREEN_LIGHT, leading=13),
        "fail_badge": ParagraphStyle("fail_badge", fontName="Helvetica-Bold", fontSize=9, textColor=RED_DARK, backColor=RED_LIGHT, leading=13),
        "warn_badge": ParagraphStyle("warn_badge", fontName="Helvetica-Bold", fontSize=9, textColor=AMBER_DARK, backColor=AMBER_LIGHT, leading=13),
        "na_badge": ParagraphStyle("na_badge", fontName="Helvetica-Bold", fontSize=9, textColor=GRAY_500, backColor=GRAY_100, leading=13),
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
            # Cover — teal top bar
            canvas.setFillColor(TEAL)
            canvas.rect(0, h - 72 * mm, w, 72 * mm, fill=1, stroke=0)
            # Subtle diagonal accent
            canvas.setFillColor(colors.HexColor("#0d9488"))
            canvas.rect(w - 60 * mm, h - 72 * mm, 60 * mm, 72 * mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 22)
            canvas.drawString(20 * mm, h - 46 * mm, "TraceLayer")
            canvas.setFont("Helvetica", 9)
            canvas.drawString(20 * mm, h - 54 * mm, "Continuous Compliance Intelligence")
            # AI badge
            canvas.setFillColor(WHITE)
            canvas.roundRect(w - 58 * mm, h - 30 * mm, 48 * mm, 11 * mm, 3 * mm, fill=1, stroke=0)
            canvas.setFillColor(TEAL)
            canvas.setFont("Helvetica-Bold", 7)
            canvas.drawCentredString(w - 34 * mm, h - 23 * mm, "AI AUDIT PACKAGE")
            self._first = False
        else:
            # Content pages — teal left bar
            canvas.setFillColor(TEAL)
            canvas.rect(0, 0, 4, h, fill=1, stroke=0)
            # Footer rule
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
    if not text.strip():
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    badge = Table([[Paragraph("AI GENERATED", st["ai_badge"])]], colWidths=[W])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))

    body_rows = [[Paragraph(p, st["body_ai"])] for p in paragraphs]
    body = Table(body_rows, colWidths=[W])
    body.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    wrapper = Table([[badge], [body]], colWidths=[W])
    wrapper.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 0.5, TEAL),
        ("LINEBEFORE",    (0, 0), (0, -1), 3, TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
    ]))
    return [wrapper, Spacer(1, 4 * mm)]


def _data_table(headers: list, rows: list, col_widths: list, st: dict) -> Table:
    data = [[Paragraph(h, st["th"]) for h in headers]] + rows
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), TEAL_LIGHT),
        ("LINEBELOW",      (0, 0), (-1, 0), 1.5, TEAL),
        ("LINEBELOW",      (0, 1), (-1, -1), 0.4, GRAY_100),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _stat_cell(value: str, label: str, value_color, col_w: float) -> Table:
    return Table(
        [
            [Paragraph(value, ParagraphStyle(f"sv_{label[:12]}", fontName="Helvetica-Bold", fontSize=18, textColor=value_color, alignment=TA_CENTER))],
            [Paragraph(label, ParagraphStyle(f"sl_{label[:12]}", fontName="Helvetica", fontSize=8, textColor=GRAY_500, alignment=TA_CENTER))],
        ],
        colWidths=[col_w],
    )


def _stats_row(cells: list, col_w: float, W: float) -> Table:
    n = len(cells)
    tbl = Table([cells], colWidths=[W / n] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, TEAL),
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
            f"badge_{status_key[:20]}",
            fontName="Helvetica-Bold",
            fontSize=font_size,
            textColor=fg,
            backColor=bg,
            leading=font_size + 3,
        ),
    )


def _test_result_badge(status: str, st: dict) -> Paragraph:
    """Returns audit-style test result badge: PASS / EXCEPTION NOTED / FAIL / INSUFFICIENT EVIDENCE."""
    s = status.lower()
    if s == "passing":
        return Paragraph("PASS", st["pass_badge"])
    if s == "warning":
        return Paragraph("EXCEPTION NOTED", st["warn_badge"])
    if s == "failing":
        return Paragraph("FAIL", st["fail_badge"])
    return Paragraph("INSUFFICIENT EVIDENCE", st["na_badge"])


def _no_data(label: str, st: dict) -> Paragraph:
    return Paragraph(
        f"No {label} recorded. Add records in TraceLayer to include them in your next audit package.",
        st["no_data"],
    )


def _risk_heatmap(risks: list[dict], W: float, st: dict) -> Table:
    _CELL_COLOR = {
        (1,1):"#d1fae5",(1,2):"#d1fae5",(1,3):"#d1fae5",(1,4):"#fef3c7",(1,5):"#fef3c7",
        (2,1):"#d1fae5",(2,2):"#d1fae5",(2,3):"#fef3c7",(2,4):"#fef3c7",(2,5):"#fee2e2",
        (3,1):"#d1fae5",(3,2):"#fef3c7",(3,3):"#fef3c7",(3,4):"#fee2e2",(3,5):"#fee2e2",
        (4,1):"#fef3c7",(4,2):"#fef3c7",(4,3):"#fee2e2",(4,4):"#fee2e2",(4,5):"#fca5a5",
        (5,1):"#fef3c7",(5,2):"#fee2e2",(5,3):"#fee2e2",(5,4):"#fca5a5",(5,5):"#fca5a5",
    }
    _CELL_TEXT = {
        (1,1):"Low",(1,2):"Low",(1,3):"Low",(1,4):"Medium",(1,5):"Medium",
        (2,1):"Low",(2,2):"Low",(2,3):"Medium",(2,4):"Medium",(2,5):"High",
        (3,1):"Low",(3,2):"Medium",(3,3):"Medium",(3,4):"High",(3,5):"High",
        (4,1):"Medium",(4,2):"Medium",(4,3):"High",(4,4):"High",(4,5):"Critical",
        (5,1):"Medium",(5,2):"High",(5,3):"High",(5,4):"Critical",(5,5):"Critical",
    }

    cell_risks: dict = {}
    for r in risks:
        lh = min(5, max(1, r.get("likelihood", 3)))
        i = min(5, max(1, r.get("impact", 3)))
        cell_risks.setdefault((lh, i), []).append(r["title"])

    cell_w = (W - 20 * mm) / 6

    header = [Paragraph("L \\ I", ParagraphStyle("hm_corner", fontName="Helvetica-Bold", fontSize=7, textColor=GRAY_500, alignment=TA_CENTER))]
    for j in range(1, 6):
        header.append(Paragraph(str(j), ParagraphStyle(f"hm_ih_{j}", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_700, alignment=TA_CENTER)))

    rows = [header]
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), GRAY_100),
        ("LINEBELOW",     (0, 0), (-1, 0), 0.5, GRAY_300),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("BOX",           (0, 0), (-1, -1), 0.5, GRAY_300),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, WHITE),
    ]

    for row_i, lh in enumerate(range(5, 0, -1), start=1):
        row = [Paragraph(str(lh), ParagraphStyle(f"hm_lh_{lh}", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_700, alignment=TA_CENTER))]
        for j in range(1, 6):
            bg_hex = _CELL_COLOR.get((lh, j), "#f9fafb")
            zone   = _CELL_TEXT.get((lh, j), "")
            in_cell = cell_risks.get((lh, j), [])
            if in_cell:
                names = in_cell[0][:18] + ("…" if len(in_cell[0]) > 18 else "")
                if len(in_cell) > 1:
                    names += f" +{len(in_cell)-1}"
                text_color = RED_DARK if zone in ("Critical", "High") else AMBER_DARK
                cell_p = Paragraph(names, ParagraphStyle(f"hmc_{l}_{j}", fontName="Helvetica-Bold", fontSize=6, textColor=text_color, alignment=TA_CENTER))
            else:
                cell_p = Paragraph(zone, ParagraphStyle(f"hme_{l}_{j}", fontName="Helvetica", fontSize=6, textColor=GRAY_500, alignment=TA_CENTER))
            row.append(cell_p)
            style_cmds.append(("BACKGROUND", (j, row_i), (j, row_i), colors.HexColor(bg_hex)))
        rows.append(row)

    tbl = Table(rows, colWidths=[cell_w] * 6)
    tbl.setStyle(TableStyle(style_cmds))

    x_label = Paragraph("← Impact →", ParagraphStyle("hm_xl", fontName="Helvetica", fontSize=7, textColor=GRAY_500, alignment=TA_CENTER))
    wrapper = Table([[tbl], [x_label]], colWidths=[W - 20 * mm])
    wrapper.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return wrapper


def _control_test_card(ctrl: dict, ev_list: list, evidence_stats: dict, manual_controls: list, W: float, st: dict) -> list:
    """Audit-methodology-style card for one control domain."""
    category = ctrl["category"]
    ctrl_stats = evidence_stats.get(category, {})

    # Build test methodology statement
    if ctrl_stats:
        int_names = sorted({i for v in ctrl_stats.values() for i in v["integrations"]})
        et_names  = [et.replace("_", " ") for et in sorted(ctrl_stats.keys())]
        total_recs = sum(v["count"] for v in ctrl_stats.values())
        method_text = (
            f"TraceLayer's automated evidence collection reviewed {total_recs} records "
            f"from {', '.join(int_names)} during the assessment period. "
            f"Evidence types analyzed: {', '.join(et_names)}."
        )
        # Check freshest evidence
        freshest_dates = []
        for v in ctrl_stats.values():
            freshest_dates.append(v["freshest"][:10])
        if freshest_dates:
            method_text += f" Most recent evidence collected: {max(freshest_dates)}."
    else:
        method_text = (
            "No automated evidence was collected for this control domain during the assessment period. "
            "Manual review or additional integrations are required."
        )

    # Check manual controls for this domain
    mc_for_ctrl = [m for m in manual_controls if category in m.get("control_id", "").lower()]
    if mc_for_ctrl:
        method_text += f" Additionally, {len(mc_for_ctrl)} manual control attestation(s) were reviewed."

    status = ctrl["status"]
    sc = _score_color(ctrl["score"])
    s_bg, s_fg = _status_bg_fg(status)

    # Header row: control name + score + status badge
    inner_w = W - 20 * mm  # account for header_cell 10mm L/R padding
    header_inner = Table([[
        Paragraph(ctrl["name"], ParagraphStyle(f"cth_{category}", fontName="Helvetica-Bold", fontSize=11, textColor=GRAY_900, leading=15)),
        Table([
            [Paragraph(f"{ctrl['score']}%", ParagraphStyle(f"ctsc_{category}", fontName="Helvetica-Bold", fontSize=14, textColor=sc, alignment=TA_CENTER, leading=18))],
            [Paragraph("Score", ParagraphStyle(f"ctsl_{category}", fontName="Helvetica", fontSize=7, textColor=GRAY_500, alignment=TA_CENTER, leading=10))],
        ], colWidths=[18 * mm]),
        _test_result_badge(status, st),
    ]], colWidths=[inner_w - 46 * mm, 22 * mm, 24 * mm])
    header_inner.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))

    header_cell = Table([[header_inner]], colWidths=[W])
    header_cell.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, TEAL_BORDER),
    ]))

    # Methodology row
    meth_label = Paragraph("Test Methodology", st["label"])
    meth_text  = Paragraph(method_text, st["methodology"])
    meth_cell  = Table([[meth_label], [meth_text]], colWidths=[W])
    meth_cell.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("LINEBELOW",     (0, 1), (-1, 1), 0.4, GRAY_100),
    ]))

    parts: list = []

    # Evidence summary table
    if ctrl_stats:
        ev_label = Paragraph("Evidence Summary", st["label"])
        ev_header = [
            Paragraph("Evidence Type", st["th"]),
            Paragraph("Source Integration(s)", st["th"]),
            Paragraph("Records", st["th"]),
            Paragraph("Most Recent", st["th"]),
        ]
        ev_rows = [ev_header]
        for et, v in sorted(ctrl_stats.items()):
            ev_rows.append([
                Paragraph(et.replace("_", " ").title(), st["td"]),
                Paragraph(", ".join(v["integrations"]), st["small"]),
                Paragraph(str(v["count"]), ParagraphStyle(f"evc_{et[:10]}", fontName="Helvetica-Bold", fontSize=9, textColor=TEAL, leading=12)),
                Paragraph(v["freshest"][:10], st["small"]),
            ])
        ew = W - 20 * mm  # available content width inside ev_container (10mm L/R padding)
        ev_tbl = Table(ev_rows, colWidths=[ew * 0.30, ew * 0.38, ew * 0.14, ew * 0.18], repeatRows=1)
        ev_tbl.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), GRAY_100),
            ("LINEBELOW",      (0, 0), (-1, 0), 1, TEAL),
            ("LINEBELOW",      (0, 1), (-1, -1), 0.3, GRAY_100),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        ev_container = Table([[ev_label], [Spacer(1, 2*mm)], [ev_tbl]], colWidths=[W])
        ev_container.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))
        parts.append(ev_container)
    elif ctrl["missing_types"]:
        missing_cell = Table([[
            Paragraph(
                f"Missing evidence types: {', '.join(ctrl['missing_types'])}",
                ParagraphStyle(f"mt_{category}", fontName="Helvetica-Oblique", fontSize=9, textColor=RED_DARK, leading=13),
            )
        ]], colWidths=[W])
        missing_cell.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), RED_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ]))
        parts.append(missing_cell)

    # Assemble card
    card_rows = [[header_cell], [meth_cell]] + [[p] for p in parts]
    card = Table(card_rows, colWidths=[W])
    card.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1, TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return [KeepTogether([card]), Spacer(1, 5 * mm)]


def _criteria_test_table(framework: str, control_scores: list, W: float, st: dict) -> list:
    """Auditor-ready criteria test results table (pass/fail per criterion)."""
    try:
        from reports.generator import FRAMEWORK_CRITERIA
    except ImportError:
        return []

    criteria = FRAMEWORK_CRITERIA.get(framework, [])
    if not criteria:
        return []

    # Build score lookup by control category
    score_by_cat = {c["category"]: c for c in control_scores}

    headers = ["Criterion", "Name", "Control Domain", "Test Result", "Evidence"]
    col_widths = [W * 0.10, W * 0.32, W * 0.20, W * 0.16, W * 0.22]

    rows = [[Paragraph(h, st["th"]) for h in headers]]
    for crit in criteria:
        ctrl_data = score_by_cat.get(crit["control"])
        if ctrl_data:
            status = ctrl_data["status"]
            ev_count = ctrl_data["evidence_count"]
        else:
            status = "no_evidence"
            ev_count = 0

        result_badge = _test_result_badge(status, st)
        ev_text = f"{ev_count} records" if ev_count else "None collected"

        rows.append([
            Paragraph(crit["id"], ParagraphStyle(f"crit_id_{crit['id']}", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=12)),
            Paragraph(crit["name"], st["td"]),
            Paragraph(crit["control"].replace("_", " ").title(), st["small"]),
            result_badge,
            Paragraph(ev_text, st["small"]),
        ])

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), TEAL_LIGHT),
        ("LINEBELOW",      (0, 0), (-1, 0), 1.5, TEAL),
        ("LINEBELOW",      (0, 1), (-1, -1), 0.4, GRAY_100),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ]))

    passing = sum(1 for c in criteria if score_by_cat.get(c["control"], {}).get("status") == "passing")
    failing = sum(1 for c in criteria if score_by_cat.get(c["control"], {}).get("status") == "failing")
    warning = sum(1 for c in criteria if score_by_cat.get(c["control"], {}).get("status") == "warning")

    summary = _stats_row([
        _stat_cell(str(len(criteria)), "Total Criteria", GRAY_900, W / 4),
        _stat_cell(str(passing),       "Passing",        GREEN,    W / 4),
        _stat_cell(str(warning),       "Exception Noted",AMBER,    W / 4),
        _stat_cell(str(failing),       "Failing",        RED,      W / 4),
    ], W / 4, W)

    return [summary, Spacer(1, 4 * mm), tbl, Spacer(1, 2 * mm)]


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
    story.append(Spacer(1, 78 * mm))

    story.append(Paragraph("AI-Powered Compliance Audit Package", st["cover_eyebrow"]))
    story.append(Paragraph(context["framework_label"], st["h1"]))
    story.append(Paragraph(
        "Comprehensive compliance evidence, management assertion, criteria test results, "
        "AI-generated executive narrative, and prioritised gap analysis",
        st["cover_subtitle"],
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 6 * mm))

    meta = [
        ("Organization",     context["company_name"]),
        ("Framework",        context["framework_label"]),
        ("Assessment Period", f"{context.get('period_start', '')} – {context.get('period_end', '')}"),
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
        ("1",  "Management's Assertion",            "Formal management statement of control responsibility and operating effectiveness"),
        ("2",  "System Description",                "Scope, infrastructure, connected integrations, and assessment period"),
        ("3",  "AI Executive Summary",              "AI-generated compliance posture narrative for board presentation"),
        ("4",  "Compliance Score & Criteria Tests", "Overall score, control breakdown, and per-criterion pass/fail test results"),
        ("5",  "Control Test Results",              "Per-control audit methodology, evidence summary, and test conclusions"),
        ("6",  "Gap Analysis & Recommendations",    "AI-identified gaps and prioritised remediation actions"),
        ("7",  "Manual Controls",                   "Manually attested compliance controls and their status"),
        ("8",  "Policy Library",                    "Adopted compliance and security policies"),
        ("9",  "Risk Register",                     "Risk heat map and identified risks by likelihood, impact, and status"),
        ("10", "Penetration Testing",               "Security testing history and findings by severity"),
        ("11", "Security Training",                 "Employee security awareness training completion rate"),
        ("12", "Vendor Risk Management",            "Third-party vendor security assessments and certifications"),
        ("13", "Access Reviews",                    "Periodic access control review records"),
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

    story.append(Spacer(1, 6 * mm))
    stat_defs = [
        (str(context["total_evidence"]),             "Evidence Records", TEAL),
        (str(len(context["control_scores"])),         "Controls Assessed", GRAY_900),
        (str(len(context["risks"])),                  "Risks Tracked",    RED),
        (str(len(context["vendors"])),                "Vendors",          AMBER),
        (str(len(context["policies"])),               "Policies",         GREEN),
        (str(len(context["training"])),               "Training Records", GRAY_700),
    ]
    n = len(stat_defs)
    story.append(_stats_row(
        [_stat_cell(v, lbl, c, W / n) for v, lbl, c in stat_defs],
        W / n, W,
    ))
    story.append(PageBreak())

    # ── SECTION 1: MANAGEMENT'S ASSERTION ─────────────────────────────────────
    _section_header(story, 1, "Governance", "Management's Assertion", st)
    story.append(Paragraph(
        "Management of the organization described in this report is responsible for "
        "establishing and maintaining effective internal controls. The following assertion "
        "has been prepared based on automated evidence collection and management review.",
        st["small"],
    ))
    story.append(Spacer(1, 4 * mm))

    assertion_text = context.get("ai_management_assertion", "")
    if assertion_text.strip():
        # Formal bordered box for the assertion
        badge = Table([[Paragraph("MANAGEMENT ASSERTION", st["label"])]], colWidths=[W])
        badge.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        body_assertion = Table([[Paragraph(assertion_text, st["body_formal"])]], colWidths=[W])
        body_assertion.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), WHITE),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ]))
        assertion_wrapper = Table([[badge], [body_assertion]], colWidths=[W])
        assertion_wrapper.setStyle(TableStyle([
            ("BOX",           (0, 0), (-1, -1), 1.5, TEAL),
            ("LINEBEFORE",    (0, 0), (0, -1), 4, TEAL),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        story.append(assertion_wrapper)
    else:
        story.append(Paragraph(
            f"{context['company_name']} management asserts that controls are designed and "
            f"operating effectively for {context['framework_label']} compliance.",
            st["body_formal"],
        ))

    # Signature block
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("Authorized Signatory", st["label_gray"]))
    story.append(Spacer(1, 2 * mm))

    sig_cols = [W / 4 - 2 * mm] * 4
    sig_data = [[
        Table([
            [HRFlowable(width=W / 4 - 6 * mm, color=GRAY_500)],
            [Paragraph("Chief Executive Officer", st["sig_label"])],
        ], colWidths=[W / 4 - 2 * mm]),
        Table([
            [HRFlowable(width=W / 4 - 6 * mm, color=GRAY_500)],
            [Paragraph("Chief Information Security Officer", st["sig_label"])],
        ], colWidths=[W / 4 - 2 * mm]),
        Table([
            [HRFlowable(width=W / 4 - 6 * mm, color=GRAY_500)],
            [Paragraph("Date of Assertion", st["sig_label"])],
        ], colWidths=[W / 4 - 2 * mm]),
        Table([
            [Paragraph(context.get("period_end", context["generated_at"]), st["sig_value"])],
            [Paragraph("Assessment Period End", st["sig_label"])],
        ], colWidths=[W / 4 - 2 * mm]),
    ]]
    sig_tbl = Table(sig_data, colWidths=sig_cols)
    sig_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_tbl)
    story.append(PageBreak())

    # ── SECTION 2: SYSTEM DESCRIPTION ─────────────────────────────────────────
    _section_header(story, 2, "Scope & Infrastructure", "System Description", st)

    # Assessment period callout
    period_info = Table([[
        Table([
            [Paragraph("Assessment Period", st["label"])],
            [Paragraph(f"{context.get('period_start', 'N/A')} through {context.get('period_end', 'N/A')}", st["h3"])],
        ], colWidths=[W / 2 - 4 * mm]),
        Table([
            [Paragraph("Framework", st["label"])],
            [Paragraph(context["framework_label"], st["h3"])],
        ], colWidths=[W / 4 - 4 * mm]),
        Table([
            [Paragraph("Engagement Type", st["label"])],
            [Paragraph("Continuous Monitoring", st["h3"])],
        ], colWidths=[W / 4 - 4 * mm]),
    ]], colWidths=[W / 2, W / 4, W / 4])
    period_info.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, TEAL),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(period_info)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Scope Statement", st["h3"]))
    story.append(Paragraph(
        f"This audit package covers the {context['framework_label']} compliance posture of "
        f"{context['company_name']} for the period {context.get('period_start', 'N/A')} through "
        f"{context.get('period_end', 'N/A')}. Evidence was collected automatically via "
        f"TraceLayer's integration platform from {len(context.get('connected_integrations_detail', []))} "
        f"active integrations, producing {context['total_evidence']} total evidence records across "
        f"{len(context['control_scores'])} compliance control domains.",
        st["body"],
    ))
    story.append(Spacer(1, 5 * mm))

    # Connected integrations table
    story.append(Paragraph("Connected Integrations", st["h3"]))
    int_detail = context.get("connected_integrations_detail", [])
    if int_detail:
        int_rows = []
        for intg in int_detail:
            et_display = ", ".join(t.replace("_", " ") for t in intg["evidence_types"][:4])
            if len(intg["evidence_types"]) > 4:
                et_display += f" +{len(intg['evidence_types'])-4} more"
            int_rows.append([
                Paragraph(intg["label"], ParagraphStyle(f"il_{intg['name']}", fontName="Helvetica-Bold", fontSize=9, textColor=TEAL, leading=12)),
                Paragraph(str(intg["evidence_count"]), ParagraphStyle(f"ic_{intg['name']}", fontName="Helvetica-Bold", fontSize=9, textColor=GRAY_900, leading=12)),
                Paragraph(et_display or "—", st["small"]),
            ])
        story.append(_data_table(
            ["Integration", "Evidence Records", "Evidence Types Collected"],
            int_rows,
            [W * 0.25, W * 0.18, W * 0.57],
            st,
        ))
    else:
        story.append(Paragraph(
            "No active integrations. Connect integrations in TraceLayer to automate evidence collection.",
            st["no_data"],
        ))

    # Score history if available
    score_history = context.get("score_history", [])
    if len(score_history) >= 2:
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph("Score History (90-day period)", st["h3"]))
        hist_rows = []
        for snap in score_history[-10:]:
            sc = _score_color(snap["score"])
            hist_rows.append([
                Paragraph(snap["date"], st["small"]),
                Paragraph(f"{snap['score']}%", ParagraphStyle(f"hs_{snap['date']}", fontName="Helvetica-Bold", fontSize=9, textColor=sc, leading=12)),
            ])
        hist_tbl = _data_table(
            ["Date", "Score"],
            hist_rows,
            [W * 0.40, W * 0.60],
            st,
        )
        story.append(hist_tbl)

    story.append(PageBreak())

    # ── SECTION 3: AI EXECUTIVE SUMMARY ───────────────────────────────────────
    _section_header(story, 3, "AI Narrative", "Executive Summary", st)
    story.extend(_ai_block(context.get("ai_executive_summary", ""), st, W))
    story.append(PageBreak())

    # ── SECTION 4: COMPLIANCE SCORE & CRITERIA TEST RESULTS ───────────────────
    _section_header(story, 4, "Compliance Overview", "Score & Criteria Test Results", st)

    score = context["overall_score"]
    sc    = _score_color(score)
    passing = sum(1 for c in context["control_scores"] if c["status"] == "passing")
    failing = sum(1 for c in context["control_scores"] if c["status"] == "failing")
    warning = sum(1 for c in context["control_scores"] if c["status"] == "warning")

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
                _stat_cell(str(context["total_evidence"]), "Evidence",  GRAY_900, 28 * mm),
                _stat_cell(str(passing),                  "Passing",   GREEN,    28 * mm),
                _stat_cell(str(warning),                  "Warning",   AMBER,    28 * mm),
                _stat_cell(str(failing),                  "Failing",   RED,      28 * mm),
            ]], colWidths=[28 * mm] * 4)],
        ], colWidths=[W - 38 * mm]),
    ]], colWidths=[38 * mm, W - 38 * mm])
    score_card.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("BOX",            (0, 0), (0, 0), 2, sc),
        ("BACKGROUND",     (0, 0), (0, 0), TEAL_LIGHT),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 8),
    ]))
    story.append(score_card)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Control Domain Summary", st["h3"]))
    ctrl_rows = []
    for c in context["control_scores"]:
        missing = ", ".join(c["missing_types"]) if c["missing_types"] else "All covered"
        ctrl_rows.append([
            Paragraph(c["name"], st["td"]),
            _test_result_badge(c["status"], st),
            Paragraph(f"{c['score']}%", ParagraphStyle("cscore", fontName="Helvetica-Bold", fontSize=9, textColor=_score_color(c["score"]), leading=12)),
            Paragraph(str(c["evidence_count"]), st["td"]),
            Paragraph(missing, st["small"]),
        ])
    story.append(_data_table(
        ["Control Domain", "Test Result", "Score", "Evidence", "Missing Types"],
        ctrl_rows,
        [W * 0.28, W * 0.18, W * 0.10, W * 0.10, W * 0.34],
        st,
    ))
    story.append(Spacer(1, 6 * mm))

    # Criteria test results
    crit_elements = _criteria_test_table(context["framework"], context["control_scores"], W, st)
    if crit_elements:
        story.append(Paragraph("Criteria Test Results", st["h3"]))
        story.append(Paragraph(
            "Each criterion maps to a control domain. Test result reflects automated evidence coverage and recency.",
            st["small"],
        ))
        story.append(Spacer(1, 3 * mm))
        story.extend(crit_elements)

    story.append(PageBreak())

    # ── SECTION 5: CONTROL TEST RESULTS ───────────────────────────────────────
    _section_header(story, 5, "Audit Evidence", "Control Test Results", st)
    story.append(Paragraph(
        "Each control domain below details the audit test methodology, the automated evidence "
        "collected during the assessment period, and the resulting test conclusion.",
        st["small"],
    ))
    story.append(Spacer(1, 4 * mm))

    evidence_stats = context.get("evidence_stats", {})
    manual_controls = context.get("manual_controls", [])

    for ctrl in context["control_scores"]:
        story.extend(_control_test_card(ctrl, [], evidence_stats, manual_controls, W, st))

    story.append(PageBreak())

    # ── SECTION 6: GAP ANALYSIS & RECOMMENDATIONS ─────────────────────────────
    _section_header(story, 6, "AI Analysis", "Gap Analysis & Recommendations", st)
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
                ("BACKGROUND",    (0, 0), (0, 0), TEAL_LIGHT),
                ("BOX",           (0, 0), (-1, -1), 0.5, TEAL),
                ("TOPPADDING",    (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(card)
            story.append(Spacer(1, 2 * mm))
    story.append(PageBreak())

    # ── SECTION 7: MANUAL CONTROLS ────────────────────────────────────────────
    _section_header(story, 7, "Attestations", "Manual Controls", st)
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

    # ── SECTION 8: POLICY LIBRARY ─────────────────────────────────────────────
    _section_header(story, 8, "Governance", "Policy Library", st)
    policies = context["policies"]
    if policies:
        adopted = sum(1 for p in policies if p["has_content"])
        story.append(_stats_row([
            _stat_cell(str(len(policies)), "Total Policies",   GRAY_900, W / 3),
            _stat_cell(str(adopted),       "Adopted",          GREEN,    W / 3),
            _stat_cell(str(len(policies) - adopted), "Draft", AMBER,    W / 3),
        ], W / 3, W))
        story.append(Spacer(1, 4 * mm))
        pol_rows = []
        for p in policies:
            ad = p["has_content"]
            bg, fg = (GREEN_LIGHT, GREEN_DARK) if ad else (GRAY_100, GRAY_500)
            pol_rows.append([
                Paragraph(p["name"], st["td"]),
                Paragraph("Adopted" if ad else "Draft", ParagraphStyle(
                    f"polb_{p['slug'][:10]}", fontName="Helvetica-Bold", fontSize=8,
                    textColor=fg, backColor=bg, leading=11,
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

    # ── SECTION 9: RISK REGISTER ───────────────────────────────────────────────
    _section_header(story, 9, "Risk Management", "Risk Register", st)
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

        story.append(Paragraph("Risk Heat Map", st["h3"]))
        story.append(Paragraph(
            "Likelihood (1=rare → 5=almost certain) × Impact (1=negligible → 5=catastrophic). "
            "Green = Low · Amber = Medium · Red = High · Dark red = Critical.",
            st["small"],
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(_risk_heatmap(risks, W, st))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("Risk Register Detail", st["h3"]))
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
                Paragraph(r["status"].title(), ParagraphStyle(f"rsb_{r['status'][:8]}", fontName="Helvetica-Bold", fontSize=8, textColor=sfg, backColor=sbg, leading=11)),
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

    # ── SECTION 10: PENETRATION TESTING ───────────────────────────────────────
    _section_header(story, 10, "Security Testing", "Penetration Testing", st)
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
                    f"ptb_{pt['vendor_name'][:8]}", fontName="Helvetica-Bold", fontSize=8,
                    textColor=sfg, backColor=sbg, leading=11,
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

    # ── SECTION 11: SECURITY TRAINING ─────────────────────────────────────────
    _section_header(story, 11, "People", "Security Training", st)
    training = context["training"]
    if training:
        total_t   = len(training)
        completed = sum(1 for t in training if t["status"] == "completed")
        overdue   = sum(1 for t in training if t["status"] == "overdue")
        pending   = total_t - completed - overdue
        rate      = round(completed / total_t * 100) if total_t else 0
        rate_color = GREEN if rate >= 80 else (AMBER if rate >= 50 else RED)

        story.append(_stats_row([
            _stat_cell(f"{rate}%",     "Completion Rate", rate_color, W / 4),
            _stat_cell(str(completed), "Completed",       GREEN,      W / 4),
            _stat_cell(str(overdue),   "Overdue",         RED,        W / 4),
            _stat_cell(str(pending),   "Pending",         AMBER,      W / 4),
        ], W / 4, W))
        story.append(Spacer(1, 4 * mm))

        tr_rows = []
        for t in training[:100]:
            tr_rows.append([
                Paragraph(t["title"],          st["td"]),
                Paragraph(t["assignee_email"], st["small"]),
                _badge_para(t["status"].title(), t["status"]),
                Paragraph(t["due_date"]      or "—", st["small"]),
                Paragraph(t["completed_at"]  or "—", st["small"]),
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

    # ── SECTION 12: VENDOR RISK ────────────────────────────────────────────────
    _section_header(story, 12, "Third-Party Risk", "Vendor Risk Management", st)
    vendors = context["vendors"]
    if vendors:
        high_risk = sum(1 for v in vendors if v["risk_level"] in ("critical", "high"))
        certified = sum(1 for v in vendors if v["soc2_certified"] or v["iso27001_certified"])
        story.append(_stats_row([
            _stat_cell(str(len(vendors)), "Total Vendors",      GRAY_900, W / 3),
            _stat_cell(str(high_risk),    "High/Critical Risk", RED,      W / 3),
            _stat_cell(str(certified),    "Security Certified", GREEN,    W / 3),
        ], W / 3, W))
        story.append(Spacer(1, 4 * mm))
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
                Paragraph(v["name"],             st["td"]),
                Paragraph(v["category"].title(), st["small"]),
                Paragraph(rl.title(), ParagraphStyle(f"vb_{rl}_{v['name'][:6]}", fontName="Helvetica-Bold", fontSize=8, textColor=rfg, backColor=rbg, leading=11)),
                Paragraph(", ".join(certs) or "None", st["small"]),
                Paragraph(v["review_date"],      st["small"]),
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

    # ── SECTION 13: ACCESS REVIEWS ─────────────────────────────────────────────
    _section_header(story, 13, "Access Control", "Access Reviews", st)
    access_reviews = context["access_reviews"]
    if access_reviews:
        total_ar   = len(access_reviews)
        completed_ar = sum(1 for ar in access_reviews if ar["status"] == "completed")
        total_users  = sum(ar["users_reviewed"] for ar in access_reviews)
        total_changes = sum(ar["access_changes"] for ar in access_reviews)
        story.append(_stats_row([
            _stat_cell(str(total_ar),      "Total Reviews",   GRAY_900, W / 4),
            _stat_cell(str(completed_ar),  "Completed",       GREEN,    W / 4),
            _stat_cell(str(total_users),   "Users Reviewed",  TEAL,     W / 4),
            _stat_cell(str(total_changes), "Access Changes",  AMBER,    W / 4),
        ], W / 4, W))
        story.append(Spacer(1, 4 * mm))
        ar_rows = []
        for ar in access_reviews:
            ar_rows.append([
                Paragraph(ar["title"],               st["td"]),
                Paragraph(ar["period"],              st["small"]),
                _badge_para(ar["status"].replace("_", " ").title(), ar["status"]),
                Paragraph(str(ar["users_reviewed"]), st["td"]),
                Paragraph(str(ar["access_changes"]), st["td"]),
                Paragraph(ar["completed_at"],         st["small"]),
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
