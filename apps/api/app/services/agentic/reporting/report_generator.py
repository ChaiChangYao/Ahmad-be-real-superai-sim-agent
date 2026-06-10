"""Orchestrate engineering report generation."""
from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4

from app.services.agentic.project_state import update_agentic_state
from app.services.agentic.reporting.limitations import limitations_for_test, standard_disclaimer
from app.services.agentic.reporting.metrics_parser import parse_manifest, parse_replay_summary, parse_telemetry_summary
from app.services.agentic.reporting.pydantic_reporter import polish_report
from app.services.agentic.reporting.recommendations import (
    build_recommendations,
    issues_to_observed_strings,
    suggest_next_tests,
)
from app.services.agentic.reporting.report_writer import read_report, write_report
from app.services.agentic.reporting.run_analyzer import (
    analyze_test_outcome,
    build_reporter_input,
    outcome_to_pass_fail,
)
from app.services.agentic.reporting.schemas import (
    EngineeringReport,
    MetricValue,
    ReportGenerateOptions,
    ReporterResult,
)
from app.services.agentic.execution.run_store import run_dir


def _confidence_score(inp, outcome, metrics_count: int) -> float:
    score = 0.35
    if inp.manifest:
        score += 0.15
    if inp.replay_summary.get("has_frames"):
        score += 0.2
    if inp.telemetry_summary.get("present"):
        score += 0.15
    if outcome.status == "passed":
        score += 0.1
    if metrics_count >= 4:
        score += 0.05
    return min(1.0, round(score, 2))


def _executive_summary(inp, outcome) -> str:
    name = inp.test_name or inp.test_id
    frames = inp.replay_summary.get("total_frames", 0)
    samples = inp.telemetry_summary.get("sample_count", 0)
    parts = [f"{name} finished with outcome {outcome.label} ({outcome.status})."]
    if frames:
        parts.append(f"Replay captured {frames} frames.")
    if samples:
        parts.append(f"Telemetry recorded {samples} samples.")
    if inp.skeleton_fallback:
        parts.append("Skeleton fallback was active — visual validation is limited.")
    if inp.log_issues:
        parts.append(f"{len(inp.log_issues)} issue(s) noted in logs.")
    return " ".join(parts)


def _plain_language(inp, outcome) -> str:
    lines = [
        f"I finished {inp.test_name or inp.test_id}. Outcome: {outcome.status}.",
        "",
        "Key results:",
    ]
    for m in [
        MetricValue(id="run", label="Run status", value=inp.run_status),
        MetricValue(
            id="frames",
            label="Replay frames",
            value=inp.replay_summary.get("total_frames", 0),
        ),
    ]:
        lines.append(f"- {m.label}: {m.value}")
    if inp.telemetry_summary.get("present"):
        lines.append(f"- Telemetry samples: {inp.telemetry_summary.get('sample_count', 'recorded')}")
    lines.append("")
    lines.append("Limitations:")
    for lim in limitations_for_test(
        inp.test_id,
        skeleton_fallback=inp.skeleton_fallback,
        readiness_only=inp.readiness_only,
        telemetry_demo=bool(inp.telemetry_summary.get("demo_field")),
    )[:3]:
        lines.append(f"- {lim.text}")
    recs = build_recommendations(inp, outcome.status)
    if recs:
        lines.append("")
        lines.append("Recommended next step:")
        lines.append(f"- {recs[0].title}: {recs[0].description}")
    return "\n".join(lines)


def generate_engineering_report(
    project_id: str,
    run_id: str,
    options: ReportGenerateOptions | None = None,
) -> ReporterResult:
    opts = options or ReportGenerateOptions()
    if not opts.force:
        existing = read_report(project_id, run_id)
        if existing:
            root = run_dir(project_id, run_id)
            return ReporterResult(
                success=True,
                report=existing,
                report_path=str((root / "report.json").resolve()),
                markdown_path=str((root / "report.md").resolve()),
            )

    inp = build_reporter_input(project_id, run_id)
    outcome = analyze_test_outcome(inp)

    manifest_metrics, _ = parse_manifest(inp.manifest)
    replay_metrics, _ = parse_replay_summary(project_id, run_id)
    tele_metrics, tele_series, _ = parse_telemetry_summary(inp.test_id, project_id, run_id)
    key_metrics = manifest_metrics + replay_metrics + tele_metrics

    limitations = limitations_for_test(
        inp.test_id,
        skeleton_fallback=inp.skeleton_fallback,
        readiness_only=inp.readiness_only,
        telemetry_demo=bool(inp.telemetry_summary.get("demo_field")),
    ) if opts.include_limitations else []

    recommendations = build_recommendations(inp, outcome.status)
    next_tests = suggest_next_tests(inp.project_id, inp.test_id, outcome.status)
    issues = list(inp.log_issues)

    executive = _executive_summary(inp, outcome)
    plain = _plain_language(inp, outcome)
    pass_fail = outcome_to_pass_fail(outcome)

    report = EngineeringReport(
        report_id=f"report-{uuid4().hex[:10]}",
        run_id=run_id,
        project_id=project_id,
        test_id=inp.test_id,
        test_name=inp.test_name,
        generated_at=datetime.now(UTC).isoformat(),
        executive_summary=executive,
        plain_language_summary=plain,
        outcome=outcome,
        key_metrics=key_metrics,
        time_series_metrics=tele_series,
        detected_issues=issues,
        limitations=limitations,
        recommendations=recommendations,
        next_tests=next_tests,
        disclaimer=standard_disclaimer(inp.test_id),
        artifacts_used=[
            p for p in ("manifest.json", "state_timeseries.json", "telemetry_timeseries.json", "combined.log")
            if (run_dir(project_id, run_id) / p).is_file()
        ],
        logs_used=[n for n in ("stdout.log", "stderr.log", "combined.log") if (run_dir(project_id, run_id) / n).is_file()],
        raw_data_refs={
            "run_dir": str(run_dir(project_id, run_id).resolve()),
            "manifest": str(run_dir(project_id, run_id) / "manifest.json"),
        },
        confidence=_confidence_score(inp, outcome, len(key_metrics)),
        pass_fail=pass_fail,  # type: ignore[arg-type]
        summary=executive,
        observed_issues=issues_to_observed_strings(issues),
        engineering_explanation=plain,
        suggested_design_changes=[r.title for r in recommendations if r.next_step_type == "change_design"],
        missing_data_limitations=[lim.text for lim in limitations],
    )

    if opts.use_llm:
        report = polish_report(report)

    json_path, md_path = write_report(project_id, run_id, report)
    update_agentic_state(
        project_id,
        latest_report_id=report.report_id,
        latest_report_summary=report.executive_summary,
        latest_run_id=run_id,
    )

    return ReporterResult(
        success=True,
        report=report,
        report_path=json_path,
        markdown_path=md_path,
    )
