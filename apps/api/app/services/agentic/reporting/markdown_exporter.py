"""Render EngineeringReport as Markdown."""
from __future__ import annotations

from app.services.agentic.reporting.schemas import EngineeringReport


def export_markdown(report: EngineeringReport) -> str:
    lines = [
        f"# Engineering Report — {report.test_name or report.test_id}",
        "",
        f"**Run:** `{report.run_id}` · **Project:** `{report.project_id}`",
        f"**Outcome:** {report.outcome.label} ({report.outcome.status})",
        f"**Generated:** {report.generated_at}",
        "",
        "## Executive summary",
        report.executive_summary,
        "",
        "## Plain language",
        report.plain_language_summary,
        "",
    ]

    if report.key_metrics:
        lines.append("## Key metrics")
        for m in report.key_metrics:
            unit = f" {m.unit}" if m.unit else ""
            lines.append(f"- **{m.label}:** {m.value}{unit}")
        lines.append("")

    if report.time_series_metrics:
        lines.append("## Time series")
        for ts in report.time_series_metrics:
            lines.append(f"- **{ts.label}:** {ts.sample_count} samples")
        lines.append("")

    if report.detected_issues:
        lines.append("## Detected issues")
        for issue in report.detected_issues:
            lines.append(f"### {issue.title} ({issue.severity})")
            lines.append(issue.explanation)
            if issue.suggested_fix:
                lines.append(f"- *Suggested fix:* {issue.suggested_fix}")
        lines.append("")

    if report.limitations:
        lines.append("## Limitations")
        for lim in report.limitations:
            lines.append(f"- {lim.text}")
        lines.append("")

    if report.recommendations:
        lines.append("## Recommendations")
        for rec in report.recommendations:
            lines.append(f"- **{rec.title}** — {rec.description}")
        lines.append("")

    if report.next_tests:
        lines.append("## Suggested next tests")
        for t in report.next_tests:
            lines.append(f"- `{t}`")
        lines.append("")

    if report.disclaimer:
        lines.append("## Disclaimer")
        lines.append(report.disclaimer)

    return "\n".join(lines)
