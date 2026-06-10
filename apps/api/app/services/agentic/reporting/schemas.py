"""Part 5 engineering report schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

OutcomeStatus = Literal["passed", "warning", "failed", "blocked", "inconclusive", "readiness_only"]
NextStepType = Literal[
    "upload_file",
    "generate_default",
    "rerun_test",
    "run_another_test",
    "add_metadata",
    "change_design",
]
IssueSeverity = Literal["info", "warning", "error", "critical"]
RecommendationPriority = Literal["low", "medium", "high"]
PassFail = Literal["pass", "fail", "inconclusive", "readiness_only", "warning"]


class MetricValue(BaseModel):
    id: str
    label: str
    value: str | float | int | bool
    unit: str = ""
    category: str = "general"


class TimeSeriesMetric(BaseModel):
    id: str
    label: str
    sample_count: int = 0
    duration_seconds: float | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


class DetectedIssue(BaseModel):
    issue_id: str
    severity: IssueSeverity = "warning"
    code: str = ""
    title: str = ""
    explanation: str = ""
    suggested_fix: str = ""
    source: str = ""


class SimulationLimitation(BaseModel):
    limitation_id: str
    category: str = "general"
    text: str = ""
    test_id: str = ""


class EngineeringRecommendation(BaseModel):
    recommendation_id: str
    title: str
    description: str
    priority: RecommendationPriority = "medium"
    next_step_type: NextStepType = "run_another_test"
    action_id: str = ""
    test_id: str | None = None


class TestOutcome(BaseModel):
    status: OutcomeStatus = "inconclusive"
    label: str = ""
    summary: str = ""
    run_status: str = ""
    exit_code: int | None = None


class ReporterInput(BaseModel):
    project_id: str
    run_id: str
    test_id: str
    test_name: str = ""
    run_status: str = ""
    exit_code: int | None = None
    manifest: dict[str, Any] = Field(default_factory=dict)
    replay_summary: dict[str, Any] = Field(default_factory=dict)
    telemetry_summary: dict[str, Any] = Field(default_factory=dict)
    robot_metrics: dict[str, Any] = Field(default_factory=dict)
    mesh_metrics: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    test_spec: dict[str, Any] | None = None
    log_issues: list[DetectedIssue] = Field(default_factory=list)
    log_excerpt: str = ""
    failure: dict[str, Any] | None = None
    skeleton_fallback: bool = False
    readiness_only: bool = False


class EngineeringReport(BaseModel):
    report_id: str
    run_id: str
    project_id: str
    test_id: str
    test_name: str = ""
    generated_at: str = ""
    executive_summary: str = ""
    plain_language_summary: str = ""
    outcome: TestOutcome = Field(default_factory=TestOutcome)
    key_metrics: list[MetricValue] = Field(default_factory=list)
    time_series_metrics: list[TimeSeriesMetric] = Field(default_factory=list)
    detected_issues: list[DetectedIssue] = Field(default_factory=list)
    limitations: list[SimulationLimitation] = Field(default_factory=list)
    recommendations: list[EngineeringRecommendation] = Field(default_factory=list)
    next_tests: list[str] = Field(default_factory=list)
    disclaimer: str = ""
    artifacts_used: list[str] = Field(default_factory=list)
    logs_used: list[str] = Field(default_factory=list)
    raw_data_refs: dict[str, str] = Field(default_factory=dict)
    confidence: float = 0.5
    pass_fail: PassFail = "inconclusive"
    # backward-compatible flat fields
    summary: str = ""
    observed_issues: list[str] = Field(default_factory=list)
    engineering_explanation: str = ""
    suggested_design_changes: list[str] = Field(default_factory=list)
    missing_data_limitations: list[str] = Field(default_factory=list)


class ReportGenerateOptions(BaseModel):
    use_llm: bool = False
    audience: str = "beginner"
    include_limitations: bool = True
    force: bool = False


class ReporterResult(BaseModel):
    success: bool = True
    report: EngineeringReport | None = None
    report_path: str = ""
    markdown_path: str = ""
    error: str = ""
