"""Engineering reporter — thin wrapper over reporting package."""
from __future__ import annotations

from app.services.agentic.reporting.report_generator import generate_engineering_report
from app.services.agentic.reporting.schemas import EngineeringReport, ReportGenerateOptions, ReporterResult


def generate_report(
    project_id: str,
    run_id: str,
    *,
    use_llm: bool = False,
    force: bool = False,
) -> ReporterResult:
    return generate_engineering_report(
        project_id,
        run_id,
        ReportGenerateOptions(use_llm=use_llm, force=force),
    )


# backward-compatible signature
def generate_engineering_report_legacy(run_id: str, test_id: str) -> EngineeringReport:
    raise NotImplementedError("Use generate_report(project_id, run_id) instead.")
