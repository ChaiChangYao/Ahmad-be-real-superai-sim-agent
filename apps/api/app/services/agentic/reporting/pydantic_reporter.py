"""Optional LLM polish for summaries — disabled by default; never overrides deterministic facts."""
from __future__ import annotations

import os

from app.services.agentic.reporting.schemas import EngineeringReport


def llm_reporter_enabled() -> bool:
    """Requires ENABLE_LLM_REPORTER=1 and optional OPENROUTER_API_KEY / provider keys for future use."""
    return os.getenv("ENABLE_LLM_REPORTER", "false").lower() in ("1", "true", "yes")


def polish_report(report: EngineeringReport) -> EngineeringReport:
    """Rewrite summaries from structured facts only. Always falls back to deterministic report on error."""
    if not llm_reporter_enabled():
        return report
    try:
        import pydantic_ai  # noqa: F401
    except ImportError:
        return report
    # MVP: no external LLM API — deterministic polish only. OpenRouter optional in a later phase.
    if not report.executive_summary:
        report.executive_summary = report.plain_language_summary[:280]
    return report
