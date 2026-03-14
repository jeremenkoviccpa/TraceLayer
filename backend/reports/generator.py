"""
PDF report generator.

Requires system dependencies for WeasyPrint:
  macOS:   brew install pango
  Ubuntu:  apt-get install libpango-1.0-0 libpangoft2-1.0-0
"""
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
REPORTS_DIR = Path("/tmp/tracelayer_reports")

_jinja = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def render_pdf(context: dict) -> bytes:
    """Render the compliance report HTML template and convert to PDF bytes."""
    try:
        from weasyprint import HTML
    except ImportError:
        raise RuntimeError(
            "WeasyPrint is not installed or missing system dependencies. "
            "Run: pip install weasyprint  and install pango/cairo for your OS."
        )

    template = _jinja.get_template("report.html.j2")
    html_string = template.render(**context)
    return HTML(string=html_string).write_pdf()


def save_pdf(report_id: str, pdf_bytes: bytes) -> Path:
    """Save PDF bytes to disk and return the file path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report_id}.pdf"
    path.write_bytes(pdf_bytes)
    logger.info("Saved PDF report: %s (%d bytes)", path, len(pdf_bytes))
    return path


def load_pdf(report_id: str) -> bytes | None:
    """Load a previously saved PDF. Returns None if not found."""
    path = REPORTS_DIR / f"{report_id}.pdf"
    if not path.exists():
        return None
    return path.read_bytes()
