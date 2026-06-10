"""Run status transitions and manifest building."""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from app.services.agentic.execution.run_store import atomic_write_json
from app.services.agentic.execution.schemas import ExecutionRun, RunStatus
from app.services.agentic.execution.log_stream import parse_run_failure
from app.services.genesis_showcase.replay_atomic_io import read_manifest as read_replay_manifest


def build_manifest(run: ExecutionRun, out_dir: Path) -> dict:
    replay_manifest = read_replay_manifest(out_dir) or {}
    ts_path = out_dir / "state_timeseries.json"
    telemetry_path = out_dir / "telemetry_timeseries.json"

    frame_count = int(replay_manifest.get("frameCount") or 0)
    has_replay = ts_path.is_file() and frame_count > 0
    if not frame_count and ts_path.is_file():
        try:
            data = json.loads(ts_path.read_text(encoding="utf-8"))
            frames = data.get("frames") or []
            frame_count = len(frames)
            has_replay = frame_count > 0
        except json.JSONDecodeError:
            pass

    has_telemetry = telemetry_path.is_file()
    sample_count = 0
    sensor_types: list[str] = []
    if has_telemetry:
        try:
            tel = json.loads(telemetry_path.read_text(encoding="utf-8"))
            samples = tel.get("samples") or []
            sample_count = len(samples)
            schema = tel.get("schema") or {}
            stype = schema.get("type")
            if stype:
                sensor_types.append(str(stype))
        except json.JSONDecodeError:
            pass

    if run.status == RunStatus.completed:
        mstatus = "complete"
    elif run.status in (RunStatus.failed, RunStatus.cancelled, RunStatus.timed_out):
        mstatus = "failed"
    elif run.status == RunStatus.recording:
        mstatus = "recording"
    else:
        mstatus = "recording"

    errors: list[str] = []
    warnings: list[str] = []
    if run.error_summary:
        errors.append(run.error_summary)
    if run.warning_summary:
        warnings.append(run.warning_summary)

    failure = parse_run_failure(out_dir)
    if failure:
        errors.append(failure.get("failure_detail") or failure.get("failure_summary", ""))

    manifest = {
        "runId": run.run_id,
        "projectId": run.project_id,
        "testId": run.test_id,
        "scriptId": run.script_id,
        "templateId": run.template_id,
        "status": mstatus,
        "startedAt": run.started_at,
        "completedAt": run.completed_at,
        "backend": str(run.backend),
        "visual": {
            "hasReplay": has_replay,
            "frameCount": frame_count,
            "fps": float(replay_manifest.get("fps") or 24.0),
            "path": "state_timeseries.json",
        },
        "telemetry": {
            "hasTelemetry": has_telemetry and sample_count > 0,
            "sampleCount": sample_count,
            "sensorTypes": sensor_types,
            "path": "telemetry_timeseries.json" if has_telemetry else "",
        },
        "errors": [e for e in errors if e],
        "warnings": warnings,
        "exitCode": run.exit_code,
    }
    atomic_write_json(out_dir / "manifest.json", manifest)
    return manifest


def finalize_run(run: ExecutionRun, out_dir: Path, exit_code: int | None) -> ExecutionRun:
    run.exit_code = exit_code
    run.completed_at = datetime.now(UTC).isoformat()
    if exit_code == 0:
        run.status = RunStatus.completed
    elif run.status == RunStatus.cancelled:
        pass
    elif run.status == RunStatus.timed_out:
        pass
    else:
        run.status = RunStatus.failed
        if not run.error_summary:
            from app.services.agentic.execution.log_stream import read_failure_excerpt

            run.error_summary = read_failure_excerpt(out_dir)[:2000]
    build_manifest(run, out_dir)
    return run
