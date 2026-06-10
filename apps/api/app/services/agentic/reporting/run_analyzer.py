"""Analyze run artifacts into ReporterInput and TestOutcome."""
from __future__ import annotations

from typing import Any

from app.services.agentic.execution.artifact_store import read_manifest
from app.services.agentic.execution.run_store import load_run
from app.services.agentic.reporting.metrics_parser import (
    load_run_context,
    parse_execution_logs,
    parse_manifest,
    parse_mesh_metrics,
    parse_replay_summary,
    parse_robot_metrics,
    parse_telemetry_summary,
)
from app.services.agentic.reporting.schemas import ReporterInput, TestOutcome
from app.services.agentic.test_requirements import get_test_spec

_MOTION_TESTS = {"gravity_stability", "joint_sweep"}
_SENSOR_TESTS = {"imu_sensor", "contact_force", "depth_camera", "thermal_grid_readiness"}
_STATIC_OK = {"static_mesh_preview", "skeleton_preview"}
_READINESS_ONLY = {"fea_readiness", "cfd_readiness"}


def build_reporter_input(project_id: str, run_id: str) -> ReporterInput:
    run = load_run(project_id, run_id)
    test_id = run.test_id if run else ""
    run_status = run.status.value if run else "unknown"
    exit_code = run.exit_code if run else None
    failure = run.failure if run else None

    manifest: dict[str, Any] = {}
    try:
        manifest = read_manifest(project_id, run_id, allow_partial=True)
    except FileNotFoundError:
        manifest = {}

    _, manifest_summary = parse_manifest(manifest)
    _, replay_summary = parse_replay_summary(project_id, run_id)
    _, _, telemetry_summary = parse_telemetry_summary(test_id, project_id, run_id)
    log_issues, log_excerpt = parse_execution_logs(project_id, run_id)
    context = load_run_context(project_id, run_id)
    spec = get_test_spec(test_id)

    skeleton = bool(
        context.get("fallback_mode") == "skeleton"
        or context.get("skeleton_fallback")
        or context.get("use_skeleton")
    )
    readiness_only = test_id in _READINESS_ONLY or (spec and spec.status == "readiness_only")

    return ReporterInput(
        project_id=project_id,
        run_id=run_id,
        test_id=test_id,
        test_name=spec.display_name if spec else test_id,
        run_status=run_status,
        exit_code=exit_code,
        manifest=manifest,
        replay_summary=replay_summary,
        telemetry_summary=telemetry_summary,
        robot_metrics=parse_robot_metrics(project_id),
        mesh_metrics=parse_mesh_metrics(project_id),
        context=context,
        test_spec=spec.model_dump() if spec else None,
        log_issues=log_issues,
        log_excerpt=log_excerpt,
        failure=failure,
        skeleton_fallback=skeleton,
        readiness_only=readiness_only,
    )


def analyze_test_outcome(inp: ReporterInput) -> TestOutcome:
    status = inp.run_status
    test_id = inp.test_id
    visual = (inp.manifest.get("visual") or {}) if inp.manifest else {}
    tele = (inp.manifest.get("telemetry") or {}) if inp.manifest else {}
    has_replay = bool(visual.get("hasReplay") or inp.replay_summary.get("has_frames"))
    has_telemetry = bool(tele.get("hasTelemetry") or inp.telemetry_summary.get("present"))
    moving = int(inp.replay_summary.get("moving_frame_count") or 0)
    frames = int(inp.replay_summary.get("total_frames") or 0)
    error_issues = [i for i in inp.log_issues if i.severity in ("error", "critical")]

    if status in ("failed", "cancelled", "timed_out"):
        label = "Failed" if status == "failed" else status.replace("_", " ").title()
        return TestOutcome(
            status="failed" if status == "failed" else "blocked",
            label=label,
            summary=f"Run ended with status {status}.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    if inp.readiness_only:
        missing = inp.robot_metrics.get("missing_mesh_count", 0)
        summary = "Input readiness evaluated — no solver execution."
        if missing > 0:
            summary += f" {missing} mesh reference(s) still missing."
        return TestOutcome(
            status="readiness_only",
            label="Readiness check",
            summary=summary,
            run_status=status,
            exit_code=inp.exit_code,
        )

    if error_issues and not has_replay and not has_telemetry:
        return TestOutcome(
            status="failed",
            label="Failed",
            summary=error_issues[0].explanation,
            run_status=status,
            exit_code=inp.exit_code,
        )

    if test_id in _STATIC_OK:
        return TestOutcome(
            status="passed" if has_replay or frames > 0 else "warning",
            label="Preview",
            summary="Static or skeleton preview — motion not required.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    if test_id in _MOTION_TESTS:
        if not has_replay or frames == 0:
            return TestOutcome(
                status="failed",
                label="No motion data",
                summary="Expected motion replay but no frames were recorded.",
                run_status=status,
                exit_code=inp.exit_code,
            )
        if moving <= 1 and frames > 3:
            return TestOutcome(
                status="warning",
                label="Little motion",
                summary="Replay recorded but little meaningful motion was detected.",
                run_status=status,
                exit_code=inp.exit_code,
            )
        if inp.skeleton_fallback:
            return TestOutcome(
                status="passed",
                label="Passed (skeleton)",
                summary="Joint motion observed under skeleton fallback — not full visual validation.",
                run_status=status,
                exit_code=inp.exit_code,
            )
        return TestOutcome(
            status="passed",
            label="Passed",
            summary="Motion replay recorded with meaningful movement.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    if test_id in _SENSOR_TESTS:
        if not has_telemetry:
            return TestOutcome(
                status="failed" if test_id != "thermal_grid_readiness" else "warning",
                label="Missing telemetry",
                summary="Sensor test expected telemetry samples but none were found.",
                run_status=status,
                exit_code=inp.exit_code,
            )
        return TestOutcome(
            status="passed",
            label="Passed",
            summary="Telemetry samples recorded for sensor test.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    if inp.exit_code not in (None, 0):
        return TestOutcome(
            status="warning",
            label="Non-zero exit",
            summary=f"Process exited with code {inp.exit_code}.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    if not has_replay and not has_telemetry:
        return TestOutcome(
            status="inconclusive",
            label="Inconclusive",
            summary="Run completed but produced limited artifacts.",
            run_status=status,
            exit_code=inp.exit_code,
        )

    return TestOutcome(
        status="passed",
        label="Passed",
        summary="Run completed with expected artifacts.",
        run_status=status,
        exit_code=inp.exit_code,
    )


def outcome_to_pass_fail(outcome: TestOutcome) -> str:
    mapping = {
        "passed": "pass",
        "warning": "warning",
        "failed": "fail",
        "blocked": "fail",
        "inconclusive": "inconclusive",
        "readiness_only": "readiness_only",
    }
    return mapping.get(outcome.status, "inconclusive")
