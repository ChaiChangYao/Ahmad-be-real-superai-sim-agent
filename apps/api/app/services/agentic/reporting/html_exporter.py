"""Optional HTML export — stub for future PDF pipeline."""
from __future__ import annotations

from app.services.agentic.reporting.markdown_exporter import export_markdown
from app.services.agentic.reporting.schemas import EngineeringReport


def export_html(report: EngineeringReport) -> str:
    md = export_markdown(report)
    escaped = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<html><body><pre>{escaped}</pre></body></html>"
