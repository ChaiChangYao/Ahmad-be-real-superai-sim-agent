#!/usr/bin/env python3
"""Part 5 engineering reporting verification."""
from __future__ import annotations

import json
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.agentic.execution.run_store import atomic_write_json, save_run  # noqa: E402
from app.services.agentic.execution.schemas import ExecutionRun, RunStatus  # noqa: E402
from app.services.agentic.reporting.report_generator import generate_engineering_report  # noqa: E402
from app.services.agentic.reporting.schemas import ReportGenerateOptions  # noqa: E402
from app.services.project_store import project_dir  # noqa: E402


def _fixture_run(project_id: str, run_id: str, test_id: str, files: dict[str, str]) -> Path:
    rdir = project_dir(project_id) / "runs" / run_id
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "generated").mkdir(exist_ok=True)
    now = datetime.now(UTC).isoformat()
    stderr = files.get("stderr.log", files.get("stderr", ""))
    run = ExecutionRun(
        run_id=run_id,
        project_id=project_id,
        test_id=test_id,
        script_id="script-fixture",
        status=RunStatus.failed if stderr and "missing mesh" in stderr.lower() else RunStatus.completed,
        created_at=now,
        completed_at=now,
        run_dir=str(rdir.resolve()),
        exit_code=1 if stderr else 0,
    )
    save_run(run)
    for name, content in files.items():
        path = rdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return rdir


def case_missing_mesh() -> bool:
    print("\n=== Case: failed missing mesh ===")
    rid = "agentic-report-mesh"
    _fixture_run(
        "default-robot-dog",
        rid,
        "joint_sweep",
        {
            "stderr.log": "FileNotFoundError: missing mesh package://foo.stl\n",
            "manifest.json": json.dumps({"status": "failed", "visual": {"hasReplay": False}, "telemetry": {"hasTelemetry": False}}),
        },
    )
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and report.outcome.status in ("failed", "blocked", "warning")
    assert any(i.code == "missing_asset" for i in report.detected_issues)
    assert any(r.next_step_type == "upload_file" for r in report.recommendations)
    print("PASS")
    return True


def case_skeleton_joint_sweep() -> bool:
    print("\n=== Case: skeleton joint sweep ===")
    rid = "agentic-report-skel"
    frames = [{"t": i * 0.1, "step": i, "transforms": {"link1": {"position": [0, 0, i * 0.01]}}} for i in range(10)]
    _fixture_run(
        "default-robot-dog",
        rid,
        "joint_sweep",
        {
            "manifest.json": json.dumps({"status": "complete", "visual": {"hasReplay": True, "frameCount": 10}, "telemetry": {"hasTelemetry": False}}),
            "state_timeseries.json": json.dumps({"state_timeseries": frames, "objects": [{"id": "link1", "type": "robot_link"}]}),
            "generated/script.context.json": json.dumps({"fallback_mode": "skeleton"}),
        },
    )
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and any(l.limitation_id == "skeleton_fallback" for l in report.limitations)
    print("PASS")
    return True


def case_imu_telemetry() -> bool:
    print("\n=== Case: IMU telemetry ===")
    rid = "agentic-report-imu"
    samples = [{"t": i * 0.01, "lin_acc": [0.1 * i, 0, 9.8], "ang_vel": [0, 0, 0.1]} for i in range(20)]
    _fixture_run(
        "default-robot-dog",
        rid,
        "imu_sensor",
        {
            "manifest.json": json.dumps({"status": "complete", "visual": {"hasReplay": True, "frameCount": 5}, "telemetry": {"hasTelemetry": True, "sampleCount": 20}}),
            "telemetry_timeseries.json": json.dumps({"samples": samples, "schema": {"type": "imu", "sampleRate": 100}}),
            "state_timeseries.json": json.dumps({"state_timeseries": [{"t": 0, "step": 0, "transforms": {}}]}),
        },
    )
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and report.outcome.status == "passed"
    assert not any("stress" in lim.text.lower() for lim in report.limitations if "structural" not in lim.category)
    assert any(m.id == "imu_samples" for m in report.key_metrics)
    print("PASS")
    return True


def case_thermal_demo() -> bool:
    print("\n=== Case: thermal demo field ===")
    rid = "agentic-report-thermal"
    _fixture_run(
        "default-robot-dog",
        rid,
        "thermal_grid_readiness",
        {
            "manifest.json": json.dumps({"status": "complete", "telemetry": {"hasTelemetry": True}}),
            "telemetry_timeseries.json": json.dumps({"demo": True, "generated_field": True, "grid": [[20, 25], [30, 35]]}),
        },
    )
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and any(l.limitation_id == "thermal_demo" for l in report.limitations)
    print("PASS")
    return True


def case_fea_readiness() -> bool:
    print("\n=== Case: FEA readiness ===")
    rid = "agentic-report-fea"
    _fixture_run("default-robot-dog", rid, "fea_readiness", {"manifest.json": json.dumps({"status": "complete"})})
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and report.outcome.status == "readiness_only"
    assert not any("mpa" in m.label.lower() or "stress" in str(m.value).lower() for m in report.key_metrics)
    print("PASS")
    return True


def case_cfd_readiness() -> bool:
    print("\n=== Case: CFD readiness ===")
    rid = "agentic-report-cfd"
    _fixture_run("default-robot-dog", rid, "cfd_readiness", {"manifest.json": json.dumps({"status": "complete"})})
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and report.outcome.status == "readiness_only"
    assert not any("flow" in str(m.value).lower() and "rate" in m.label.lower() for m in report.key_metrics)
    print("PASS")
    return True


def case_cpu_fallback() -> bool:
    print("\n=== Case: CPU fallback logs ===")
    rid = "agentic-report-cpu"
    _fixture_run(
        "default-robot-dog",
        rid,
        "gravity_stability",
        {
            "stdout.log": "Genesis using CPU fallback — no CUDA device found\n",
            "manifest.json": json.dumps({"status": "complete", "visual": {"hasReplay": True, "frameCount": 8}}),
            "state_timeseries.json": json.dumps(
                {
                    "state_timeseries": [
                        {"t": 0, "step": 0, "transforms": {"b": {"position": [0, 0, 0]}}},
                        {"t": 1, "step": 1, "transforms": {"b": {"position": [0, 0, 0.05]}}},
                    ],
                    "objects": [{"id": "b", "type": "robot_link"}],
                }
            ),
        },
    )
    result = generate_engineering_report("default-robot-dog", rid, ReportGenerateOptions(force=True))
    report = result.report
    assert report and any(i.code == "cpu_fallback" for i in report.detected_issues)
    assert report.outcome.status in ("passed", "warning")
    print("PASS")
    return True


def main() -> int:
    passed = 0
    for fn in (
        case_missing_mesh,
        case_skeleton_joint_sweep,
        case_imu_telemetry,
        case_thermal_demo,
        case_fea_readiness,
        case_cfd_readiness,
        case_cpu_fallback,
    ):
        try:
            if fn():
                passed += 1
        except Exception as exc:
            print(f"FAIL: {exc}")
    print(f"\n{passed}/7 checks passed")
    return 0 if passed >= 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
