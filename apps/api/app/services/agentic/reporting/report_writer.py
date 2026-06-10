"""Atomic report persistence."""
from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

from app.services.agentic.execution.run_store import atomic_write_json, load_run, run_dir, save_run
from app.services.agentic.reporting.markdown_exporter import export_markdown
from app.services.agentic.reporting.schemas import EngineeringReport


def write_report(project_id: str, run_id: str, report: EngineeringReport) -> tuple[str, str]:
    root = run_dir(project_id, run_id)
    if not report.report_id:
        report.report_id = f"report-{uuid4().hex[:10]}"
    if not report.generated_at:
        report.generated_at = datetime.now(UTC).isoformat()

    json_path = root / "report.json"
    md_path = root / "report.md"
    atomic_write_json(json_path, report.model_dump(mode="json"))
    md_path.write_text(export_markdown(report), encoding="utf-8")

    run = load_run(project_id, run_id)
    if run:
        run.report_path = str(json_path.resolve())
        save_run(run)

    return str(json_path.resolve()), str(md_path.resolve())


def read_report(project_id: str, run_id: str) -> EngineeringReport | None:
    path = run_dir(project_id, run_id) / "report.json"
    if not path.is_file():
        return None
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    return EngineeringReport.model_validate(data)


def read_report_markdown(project_id: str, run_id: str) -> str | None:
    path = run_dir(project_id, run_id) / "report.md"
    if not path.is_file():
        report = read_report(project_id, run_id)
        if report:
            return export_markdown(report)
        return None
    return path.read_text(encoding="utf-8")
