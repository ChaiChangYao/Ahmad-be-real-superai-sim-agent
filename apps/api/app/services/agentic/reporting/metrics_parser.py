"""Parse run artifacts into structured metrics and issues."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.agentic.execution.log_stream import parse_run_failure, tail_logs
from app.services.agentic.execution.run_store import run_dir
from app.services.agentic.mesh_inspector import inspect_project_meshes
from app.services.agentic.reporting.schemas import DetectedIssue, MetricValue, TimeSeriesMetric
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.genesis_showcase.replay_motion_diagnostics import analyze_replay_motion

_LOG_PATTERNS: list[tuple[str, str, str, str]] = [
    (
        r"missing mesh|filenotfounderror|no such file|asset file not found",
        "missing_asset",
        "Missing mesh or asset file",
        "Upload the missing mesh files or map STEP parts to URDF paths.",
    ),
    (
        r"--no-vis|unrecognized arguments",
        "invalid_cli",
        "Unsupported launch flag",
        "Use the web headless launcher — do not pass unsupported CLI flags.",
    ),
    (
        r"modulenotfounderror|importerror",
        "missing_dependency",
        "Missing Python dependency",
        "Install the missing package or optional Genesis extra.",
    ),
    (
        r"cpu fallback|using cpu|no cuda|no gpu",
        "cpu_fallback",
        "CPU fallback in use",
        "Simulation ran on CPU — slower but not necessarily a physics failure.",
    ),
    (
        r"timed out|timeout",
        "timeout",
        "Run timed out",
        "Increase timeout, simplify the scene, or reduce simulation duration.",
    ),
    (
        r"empty telemetry|no telemetry|0 samples",
        "empty_telemetry",
        "No telemetry recorded",
        "Check sensor attach link and sample rate configuration.",
    ),
    (
        r"unsafe|banned|subprocess",
        "unsafe_script",
        "Script safety block",
        "Regenerate the script from the assistant.",
    ),
]


def _read_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def parse_manifest(manifest: dict | None) -> tuple[list[MetricValue], dict[str, Any]]:
    if not manifest:
        return [], {}
    visual = manifest.get("visual") or {}
    telemetry = manifest.get("telemetry") or {}
    metrics = [
        MetricValue(id="manifest_status", label="Manifest status", value=str(manifest.get("status") or "unknown")),
        MetricValue(
            id="has_replay",
            label="Replay recorded",
            value=bool(visual.get("hasReplay")),
            category="visual",
        ),
        MetricValue(
            id="frame_count",
            label="Replay frames",
            value=int(visual.get("frameCount") or 0),
            category="visual",
        ),
        MetricValue(
            id="has_telemetry",
            label="Telemetry recorded",
            value=bool(telemetry.get("hasTelemetry")),
            category="telemetry",
        ),
    ]
    if telemetry.get("sampleCount") is not None:
        metrics.append(
            MetricValue(
                id="telemetry_samples",
                label="Telemetry samples",
                value=int(telemetry.get("sampleCount") or 0),
                category="telemetry",
            )
        )
    return metrics, {"visual": visual, "telemetry": telemetry, "status": manifest.get("status")}


def parse_replay_summary(project_id: str, run_id: str) -> tuple[list[MetricValue], dict[str, Any]]:
    root = run_dir(project_id, run_id)
    ts_path = root / "state_timeseries.json"
    data = _read_json(ts_path)
    if not isinstance(data, dict):
        return [MetricValue(id="replay_frames", label="Replay frames", value=0)], {"empty": True}

    frames = data.get("state_timeseries") or data.get("preview_frames") or data.get("frames") or []
    if not isinstance(frames, list):
        frames = []
    objects = data.get("objects") or []
    object_ids = [str(o.get("id")) for o in objects if isinstance(o, dict) and o.get("id")]
    motion = analyze_replay_motion(frames, object_ids or None)

    metrics = [
        MetricValue(id="replay_frames", label="Replay frames", value=motion.get("total_frames", 0), category="replay"),
        MetricValue(
            id="unique_poses",
            label="Unique poses",
            value=motion.get("unique_pose_count", 0),
            category="replay",
        ),
        MetricValue(
            id="moving_frames",
            label="Moving frames",
            value=motion.get("moving_frame_count", 0),
            category="replay",
        ),
        MetricValue(
            id="longest_freeze",
            label="Longest freeze run",
            value=motion.get("perceptual_longest_freeze_run", 0),
            category="replay",
        ),
        MetricValue(
            id="object_count",
            label="Tracked objects",
            value=len(object_ids),
            category="replay",
        ),
    ]
    if motion.get("recorder_issue") and motion["recorder_issue"] != "none":
        metrics.append(
            MetricValue(
                id="recorder_issue",
                label="Recorder note",
                value=str(motion["recorder_issue"]),
                category="replay",
            )
        )
    return metrics, {**motion, "objects": objects, "has_frames": len(frames) > 0}


def _imu_stats(samples: list[dict]) -> dict[str, Any]:
    if not samples:
        return {"sample_count": 0}
    channels = ["lin_acc", "ang_vel", "true_lin_acc", "true_ang_vel"]
    stats: dict[str, Any] = {"sample_count": len(samples)}
    for ch in channels:
        vals: list[float] = []
        for s in samples:
            v = s.get(ch)
            if isinstance(v, list) and len(v) >= 3:
                vals.extend(float(x) for x in v[:3])
        if vals:
            stats[f"{ch}_max"] = max(vals)
            stats[f"{ch}_mean"] = sum(vals) / len(vals)
    if len(samples) >= 2:
        first = samples[0]
        last = samples[-1]
        changing = any(
            first.get(k) != last.get(k) for k in channels if first.get(k) is not None
        )
        stats["signal_changing"] = changing
    return stats


def parse_telemetry_summary(test_id: str, project_id: str, run_id: str) -> tuple[list[MetricValue], list[TimeSeriesMetric], dict[str, Any]]:
    root = run_dir(project_id, run_id)
    data = _read_json(root / "telemetry_timeseries.json")
    if not isinstance(data, dict):
        return [], [], {"present": False}

    metrics: list[MetricValue] = []
    series: list[TimeSeriesMetric] = []
    summary: dict[str, Any] = {"present": True, "test_id": test_id}

    samples = data.get("samples")
    if isinstance(samples, list) and samples:
        summary["sample_count"] = len(samples)
        if test_id == "imu_sensor":
            imu = _imu_stats(samples)
            summary.update(imu)
            metrics.append(MetricValue(id="imu_samples", label="IMU samples", value=imu.get("sample_count", 0), category="imu"))
            for key in ("lin_acc_max", "ang_vel_max", "signal_changing"):
                if key in imu:
                    metrics.append(MetricValue(id=key, label=key.replace("_", " ").title(), value=imu[key], category="imu"))
            series.append(
                TimeSeriesMetric(
                    id="imu",
                    label="IMU telemetry",
                    sample_count=len(samples),
                    summary=imu,
                )
            )
        elif test_id == "contact_force":
            forces: list[float] = []
            for s in samples:
                if isinstance(s, dict):
                    f = s.get("force_magnitude") or s.get("force")
                    if isinstance(f, (int, float)):
                        forces.append(float(f))
                    elif isinstance(f, list) and f:
                        forces.append(float(f[0]))
            if forces:
                summary["peak_force"] = max(forces)
                summary["avg_force"] = sum(forces) / len(forces)
                metrics.extend(
                    [
                        MetricValue(id="contact_samples", label="Contact samples", value=len(samples), category="contact"),
                        MetricValue(id="peak_force", label="Peak force", value=round(max(forces), 4), category="contact"),
                    ]
                )
        elif test_id == "joint_sweep":
            joints: set[str] = set()
            for s in samples:
                if isinstance(s, dict) and s.get("joint"):
                    joints.add(str(s["joint"]))
            summary["joints_tested"] = sorted(joints)
            metrics.append(MetricValue(id="joints_tested", label="Joints tested", value=len(joints), category="joint"))
        elif test_id == "depth_camera":
            depth_frames = data.get("depth_frames") or []
            summary["depth_frame_count"] = len(depth_frames) if isinstance(depth_frames, list) else 0
            metrics.append(
                MetricValue(
                    id="depth_frames",
                    label="Depth frames",
                    value=summary["depth_frame_count"],
                    category="depth",
                )
            )
        elif test_id == "thermal_grid_readiness":
            grid = data.get("grid") or data.get("temperatures")
            summary["demo_field"] = bool(data.get("demo") or data.get("generated_field"))
            if isinstance(grid, list) and grid:
                flat = [float(x) for row in grid for x in (row if isinstance(row, list) else [row])]
                if flat:
                    summary["temp_min"] = min(flat)
                    summary["temp_max"] = max(flat)
                    summary["temp_mean"] = sum(flat) / len(flat)
                    metrics.extend(
                        [
                            MetricValue(id="temp_min", label="Min temp (demo)", value=round(min(flat), 2), unit="°C", category="thermal"),
                            MetricValue(id="temp_max", label="Max temp (demo)", value=round(max(flat), 2), unit="°C", category="thermal"),
                        ]
                    )

    schema = data.get("schema")
    if isinstance(schema, dict):
        summary["schema_type"] = schema.get("type")

    return metrics, series, summary


def parse_execution_logs(project_id: str, run_id: str) -> tuple[list[DetectedIssue], str]:
    root = run_dir(project_id, run_id)
    logs = tail_logs(root, tail=500)
    combined = (logs.get("combined") or "") + "\n" + (logs.get("stderr") or "") + "\n" + (logs.get("stdout") or "")
    issues: list[DetectedIssue] = []
    seen: set[str] = set()
    lower = combined.lower()

    for pattern, code, title, fix in _LOG_PATTERNS:
        if re.search(pattern, lower, re.I):
            if code in seen:
                continue
            seen.add(code)
            issues.append(
                DetectedIssue(
                    issue_id=f"log_{code}",
                    severity="error" if code in ("missing_asset", "unsafe_script", "timeout") else "warning",
                    code=code,
                    title=title,
                    explanation=f"Log pattern detected: {code.replace('_', ' ')}.",
                    suggested_fix=fix,
                    source="logs",
                )
            )

    failure = parse_run_failure(root)
    if failure:
        code = failure.get("failure_code", "unknown")
        if code not in seen:
            issues.append(
                DetectedIssue(
                    issue_id=f"failure_{code}",
                    severity="error",
                    code=code,
                    title="Run failure",
                    explanation=failure.get("failure_detail") or failure.get("failure_summary") or "Run failed.",
                    suggested_fix=failure.get("suggested_fix") or "Review logs and fix blockers.",
                    source="logs",
                )
            )

    excerpt = "\n".join(combined.splitlines()[-40:])
    return issues, excerpt


def parse_robot_metrics(project_id: str) -> dict[str, Any]:
    robots = inspect_all_robot_descriptions(project_id)
    parsed = [r for r in robots if r.parsed]
    if not parsed:
        return {"parsed": False, "missing_mesh_count": 0}
    primary = parsed[0]
    missing = sum(1 for m in primary.mesh_references if not m.exists)
    return {
        "parsed": True,
        "movable_joints": primary.movable_joints_count,
        "joint_limits": primary.has_joint_limits,
        "collision_geometry": primary.has_collision_geometry,
        "visual_geometry": primary.has_visual_geometry,
        "missing_mesh_count": missing,
        "sensors": len(primary.detected_sensors),
        "warnings": primary.warnings,
    }


def parse_mesh_metrics(project_id: str) -> dict[str, Any]:
    inspections = inspect_project_meshes(project_id)
    if not inspections:
        return {"mesh_count": 0}
    watertight = sum(1 for m in inspections if m.watertight is True)
    return {
        "mesh_count": len(inspections),
        "watertight_count": watertight,
        "parsed_count": sum(1 for m in inspections if m.parsed),
    }


def load_run_context(project_id: str, run_id: str) -> dict[str, Any]:
    root = run_dir(project_id, run_id)
    ctx = root / "generated" / "script.context.json"
    data = _read_json(ctx)
    return data if isinstance(data, dict) else {}
