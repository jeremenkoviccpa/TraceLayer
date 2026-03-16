"""
PDF report generator using ReportLab (pure Python, no system dependencies).
"""
import logging
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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

# ── Brand colours ─────────────────────────────────────────────────────────────
INDIGO   = colors.HexColor("#4f46e5")
GRAY_900 = colors.HexColor("#111827")
GRAY_500 = colors.HexColor("#6b7280")
GRAY_300 = colors.HexColor("#d1d5db")
GRAY_100 = colors.HexColor("#f3f4f6")
GREEN    = colors.HexColor("#10b981")
AMBER    = colors.HexColor("#f59e0b")
RED      = colors.HexColor("#ef4444")
WHITE    = colors.white

FRAMEWORK_LABELS = {
    "soc2":     "SOC 2 Type II",
    "iso27001": "ISO/IEC 27001",
    "hipaa":    "HIPAA",
}

REPORTS_DIR = Path("/tmp/tracelayer_reports")


def _score_color(score: int):
    if score >= 80:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def _status_colors(status: str):
    mapping = {
        "passing":    (colors.HexColor("#d1fae5"), colors.HexColor("#065f46")),
        "warning":    (colors.HexColor("#fef3c7"), colors.HexColor("#92400e")),
        "failing":    (colors.HexColor("#fee2e2"), colors.HexColor("#991b1b")),
        "no_evidence":(GRAY_100,                   GRAY_500),
    }
    return mapping.get(status, (GRAY_100, GRAY_500))


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle("h1",  fontName="Helvetica-Bold",   fontSize=28, textColor=GRAY_900,  leading=34, spaceAfter=4),
        "h2": ParagraphStyle("h2",  fontName="Helvetica-Bold",   fontSize=18, textColor=GRAY_900,  leading=22, spaceBefore=16, spaceAfter=12),
        "h3": ParagraphStyle("h3",  fontName="Helvetica-Bold",   fontSize=12, textColor=GRAY_900,  leading=16, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="Helvetica",     fontSize=10, textColor=GRAY_900,  leading=15),
        "small": ParagraphStyle("small", fontName="Helvetica",   fontSize=9,  textColor=GRAY_500,  leading=13),
        "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=8, textColor=INDIGO,  leading=12, spaceAfter=2),
        "cover_brand": ParagraphStyle("cover_brand", fontName="Helvetica-Bold", fontSize=22, textColor=WHITE, leading=26),
        "cover_eyebrow": ParagraphStyle("cover_eyebrow", fontName="Helvetica-Bold", fontSize=10, textColor=INDIGO, leading=14, spaceAfter=8),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontName="Helvetica", fontSize=13, textColor=GRAY_500, leading=18),
        "meta_label": ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_500, leading=12),
        "meta_value": ParagraphStyle("meta_value", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY_900, leading=16),
        "th": ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=INDIGO, leading=11),
        "td": ParagraphStyle("td", fontName="Helvetica", fontSize=9, textColor=GRAY_900, leading=12),
        "td_mono": ParagraphStyle("td_mono", fontName="Courier", fontSize=8, textColor=GRAY_500, leading=11),
        "tag": ParagraphStyle("tag", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#5b21b6"), leading=11),
        "right": ParagraphStyle("right", fontName="Helvetica", fontSize=8, textColor=GRAY_500, leading=11, alignment=TA_RIGHT),
    }


class _PageTemplate:
    """Adds brand left-bar and footer to every page except the cover."""

    def __init__(self, context: dict, styles: dict):
        self.ctx = context
        self.st = styles
        self._is_first = True

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        if self._is_first:
            # Cover: solid indigo top bar
            canvas.setFillColor(INDIGO)
            canvas.rect(0, h - 75*mm, w, 75*mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 22)
            canvas.drawString(20*mm, h - 50*mm, "TraceLayer")
            self._is_first = False
        else:
            # Content pages: indigo left bar
            canvas.setFillColor(INDIGO)
            canvas.rect(0, 0, 5, h, fill=1, stroke=0)

            # Footer
            canvas.setFillColor(GRAY_300)
            canvas.rect(15*mm, 12*mm, w - 30*mm, 0.4, fill=1, stroke=0)
            canvas.setFillColor(GRAY_500)
            canvas.setFont("Helvetica", 8)
            label = f"TraceLayer · {self.ctx['company_name']} · {self.ctx['framework'].upper()} Report  —  Confidential"
            canvas.drawString(15*mm, 8*mm, label)
            canvas.drawRightString(w - 15*mm, 8*mm, f"Page {doc.page}")

        canvas.restoreState()


def render_pdf(context: dict) -> bytes:
    buf = BytesIO()
    st  = _styles()
    pt  = _PageTemplate(context, st)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm,  bottomMargin=22*mm,
        onPage=pt,
    )

    story = []
    W = A4[0] - 40*mm   # usable width

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 75*mm))   # space below the indigo band

    fw_label = FRAMEWORK_LABELS.get(context["framework"], context["framework"].upper())
    story.append(Paragraph("Compliance Evidence Report", st["cover_eyebrow"]))
    story.append(Paragraph(f"{fw_label} Audit Report", st["h1"]))
    story.append(Paragraph(f"{context['report_type'].title()} — Continuous Evidence Collection", st["cover_subtitle"]))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 6*mm))

    # Meta grid
    meta = [
        ("Organization",    context["company_name"]),
        ("Framework",       fw_label),
        ("Date Generated",  context["generated_at"]),
        ("Compliance Score",f"{context['overall_score']}%"),
    ]
    meta_data = [[
        Table([[Paragraph(lbl, st["meta_label"])], [Paragraph(val, st["meta_value"])]],
              colWidths=[W/4 - 4*mm])
        for lbl, val in meta
    ]]
    meta_tbl = Table(meta_data, colWidths=[W/4]*4)
    meta_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"Report ID: {context['report_id']}    ·    Generated: {context['generated_at_full']}    ·    CONFIDENTIAL", st["small"]))

    story.append(PageBreak())

    # ── EXECUTIVE SUMMARY ────────────────────────────────────────────────────
    story.append(Paragraph("Section 1", st["label"]))
    story.append(Paragraph("Executive Summary", st["h2"]))

    # Score card
    score = context["overall_score"]
    sc    = _score_color(score)
    score_tbl = Table(
        [[
            Table([
                [Paragraph(f"{score}", ParagraphStyle("sc_num", fontName="Helvetica-Bold", fontSize=32, textColor=sc, alignment=TA_CENTER))],
                [Paragraph("/ 100", ParagraphStyle("sc_sub", fontName="Helvetica", fontSize=9, textColor=GRAY_500, alignment=TA_CENTER))],
            ], colWidths=[30*mm]),
            Table([
                [Paragraph("Overall Compliance Score", st["h3"])],
                [Paragraph("Based on evidence coverage, recency, and volume across all monitored controls.", st["small"])],
                [Spacer(1, 2*mm)],
                [Table([[
                    Table([[Paragraph(str(context["total_records"]), ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=18, textColor=GRAY_900, alignment=TA_CENTER))],
                           [Paragraph("Evidence records", ParagraphStyle("sl", fontName="Helvetica", fontSize=8, textColor=GRAY_500, alignment=TA_CENTER))]],
                          colWidths=[30*mm]),
                    Table([[Paragraph(str(len(context["control_scores"])), ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=18, textColor=GRAY_900, alignment=TA_CENTER))],
                           [Paragraph("Controls monitored", ParagraphStyle("sl", fontName="Helvetica", fontSize=8, textColor=GRAY_500, alignment=TA_CENTER))]],
                          colWidths=[30*mm]),
                    Table([[Paragraph(str(sum(1 for c in context["control_scores"] if c["status"]=="passing")),
                                      ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=18, textColor=GREEN, alignment=TA_CENTER))],
                           [Paragraph("Passing", ParagraphStyle("sl", fontName="Helvetica", fontSize=8, textColor=GRAY_500, alignment=TA_CENTER))]],
                          colWidths=[30*mm]),
                ]], colWidths=[30*mm, 30*mm, 30*mm])],
            ], colWidths=[W - 38*mm]),
        ]],
        colWidths=[38*mm, W - 38*mm],
    )
    score_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOX",    (0,0), (0,0), 2, sc),
        ("ROUNDEDCORNERS", [5]),
        ("BACKGROUND", (0,0), (0,0), colors.HexColor("#f0f4ff")),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING",(0,0), (-1,-1), 8),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 6*mm))

    # Control breakdown table
    story.append(Paragraph("Control Breakdown", st["h3"]))
    tbl_header = [
        Paragraph("Control", st["th"]),
        Paragraph("Status", st["th"]),
        Paragraph("Score", st["th"]),
        Paragraph("Evidence", st["th"]),
        Paragraph("Missing types", st["th"]),
    ]
    tbl_rows = [tbl_header]
    for c in context["control_scores"]:
        bg, fg = _status_colors(c["status"])
        status_label = c["status"].replace("_", " ").title()
        missing = ", ".join(c["missing_types"]) if c["missing_types"] else "All covered"
        tbl_rows.append([
            Paragraph(c["name"], st["td"]),
            Paragraph(status_label, ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=8, textColor=fg, backColor=bg, leading=11)),
            Paragraph(f"{c['score']}%", ParagraphStyle("score_td", fontName="Helvetica-Bold", fontSize=9, textColor=_score_color(c["score"]), leading=12)),
            Paragraph(str(c["evidence_count"]), st["td"]),
            Paragraph(missing, st["small"]),
        ])

    col_w = [W*0.26, W*0.15, W*0.10, W*0.10, W*0.39]
    tbl = Table(tbl_rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f3ff")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, INDIGO),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.5, GRAY_100),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ── CONTROL DETAIL SECTIONS ───────────────────────────────────────────────
    for i, c in enumerate(context["control_scores"], start=2):
        story.append(Paragraph(f"Section {i}", st["label"]))
        story.append(Paragraph(c["name"], st["h2"]))

        # Control header card
        bg, fg = _status_colors(c["status"])
        status_label = c["status"].replace("_", " ").title()
        last = (c["last_collected"] or "")[:10] or "Never"
        missing_str = ", ".join(c["missing_types"]) if c["missing_types"] else "All covered"

        card_left = Table([
            [Paragraph(c["name"], st["h3"])],
            [Paragraph(f"Category: {c['category'].replace('_',' ').title()}  ·  {c['evidence_count']} evidence records  ·  Last collected: {last}", st["small"])],
            [Paragraph(f"Missing: {missing_str}" if c["missing_types"] else "All evidence types covered", ParagraphStyle("miss", fontName="Helvetica", fontSize=9, textColor=RED if c["missing_types"] else GREEN, leading=12))],
        ], colWidths=[W - 28*mm])

        card_right = Table([
            [Paragraph(status_label, ParagraphStyle("badge2", fontName="Helvetica-Bold", fontSize=8, textColor=fg, backColor=bg, leading=11))],
            [Paragraph(f"{c['score']}%", ParagraphStyle("cscore", fontName="Helvetica-Bold", fontSize=20, textColor=INDIGO, alignment=TA_CENTER, leading=24))],
        ], colWidths=[22*mm])

        card = Table([[card_left, card_right]], colWidths=[W - 28*mm, 28*mm])
        card.setStyle(TableStyle([
            ("BACKGROUND",   (0,0), (-1,-1), colors.HexColor("#f9fafb")),
            ("BOX",          (0,0), (-1,-1), 0.5, GRAY_300),
            ("LINEBEFORE",   (0,0), (0,-1), 3, INDIGO),
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 10),
            ("LEFTPADDING",  (0,0), (-1,-1), 12),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(KeepTogether([card, Spacer(1, 4*mm)]))

        # Evidence table
        ev_list = context["controls"].get(c["category"], [])
        if ev_list:
            ev_header = [
                Paragraph("Integration", st["th"]),
                Paragraph("Evidence type", st["th"]),
                Paragraph("Source ID", st["th"]),
                Paragraph("Collected at", st["th"]),
            ]
            ev_rows = [ev_header]
            for rec in ev_list:
                src = rec["source_id"]
                if len(src) > 48:
                    src = src[:48] + "…"
                ts = rec["timestamp"][:19].replace("T", " ")
                ev_rows.append([
                    Paragraph(rec["integration"], st["tag"]),
                    Paragraph(rec["evidence_type"], st["td"]),
                    Paragraph(src, st["td_mono"]),
                    Paragraph(ts, st["small"]),
                ])
            ev_col_w = [W*0.15, W*0.25, W*0.37, W*0.23]
            ev_tbl = Table(ev_rows, colWidths=ev_col_w, repeatRows=1)
            ev_tbl.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f5f3ff")),
                ("LINEBELOW",     (0, 1), (-1, -1), 0.3, GRAY_100),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ]))
            story.append(ev_tbl)
        else:
            story.append(Paragraph(
                f"No evidence collected for this control. Connect an integration that provides: {missing_str}.",
                ParagraphStyle("no_ev", fontName="Helvetica-Oblique", fontSize=10, textColor=GRAY_500, leading=14),
            ))

        if i < len(context["control_scores"]) + 1:
            story.append(PageBreak())

    doc.build(story)
    return buf.getvalue()


def save_pdf(report_id: str, pdf_bytes: bytes) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report_id}.pdf"
    path.write_bytes(pdf_bytes)
    logger.info("Saved PDF report: %s (%d bytes)", path, len(pdf_bytes))
    return path


def load_pdf(report_id: str) -> bytes | None:
    path = REPORTS_DIR / f"{report_id}.pdf"
    if not path.exists():
        return None
    return path.read_bytes()
