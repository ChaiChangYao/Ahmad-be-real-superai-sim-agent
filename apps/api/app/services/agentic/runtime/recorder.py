"""Run output recording for generated scripts."""
from __future__ import annotations

import json
import os
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


def _run_dir(config: dict) -> Path:
    return Path(config.get("output_root", "."))


def start_run_metadata(config: dict) -> dict[str, Any]:
    meta = {
        "started_at": datetime.now(UTC).isoformat(),
        "test_id": config.get("test_id"),
        "template_id": config.get("template_id"),
        "project_id": config.get("project_id"),
        "fallback_mode": config.get("fallback_mode"),
        "status": "running",
    }
    path = _run_dir(config) / "run_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, meta)
    return meta


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _recorder_output_active(out: Path) -> bool:
    """Skip stub overwrite when showcase scene recorder already wrote replay."""
    if os.environ.get("BUILDABLES_SKIP_MANUAL_REPLAY_WRITE") == "1":
        if out.is_file() and out.stat().st_size > 200:
            return True
    record_path = os.environ.get("BUILDABLES_RECORD_PATH")
    if record_path:
        rp = Path(record_path)
        if rp.is_file() and rp.stat().st_size > 200:
            return True
        manifest = rp.parent / "replay_manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if int(data.get("frameCount") or 0) > 0:
                    return True
            except json.JSONDecodeError:
                pass
    return False


def write_state_timeseries(config: dict, frames: list[dict]) -> Path:
    out = Path(config.get("replay_config", {}).get("output_state_timeseries_path") or _run_dir(config) / "state_timeseries.json")
    if _recorder_output_active(out):
        print("[agentic_runtime] Skipping manual replay write — showcase recorder output preserved.", flush=True)
        return out
    atomic_write_json(out, {"frames": frames, "meta": {"source": "agentic_generated"}})
    return out


def write_telemetry_timeseries(config: dict, payload: dict) -> Path:
    out = Path(config.get("replay_config", {}).get("output_telemetry_timeseries_path") or _run_dir(config) / "telemetry_timeseries.json")
    atomic_write_json(out, payload)
    return out


def write_manifest(config: dict, extra: dict | None = None) -> None:
    path = _run_dir(config) / "run_manifest.json"
    data = {"status": "initialized", **(extra or {})}
    if path.is_file():
        data = {**json.loads(path.read_text(encoding="utf-8")), **data}
    atomic_write_json(path, data)


def finalize_run(config: dict) -> None:
    path = _run_dir(config) / "run_manifest.json"
    data = {"status": "completed", "completed_at": datetime.now(UTC).isoformat()}
    if path.is_file():
        data = {**json.loads(path.read_text(encoding="utf-8")), **data}
    atomic_write_json(path, data)
    print("[agentic_runtime] Run completed.", flush=True)


def fail_run(config: dict, exc: BaseException) -> None:
    path = _run_dir(config) / "run_manifest.json"
    data = {
        "status": "failed",
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "completed_at": datetime.now(UTC).isoformat(),
    }
    if path.is_file():
        data = {**json.loads(path.read_text(encoding="utf-8")), **data}
    atomic_write_json(path, data)
    err_path = _run_dir(config) / "stderr_summary.txt"
    err_path.write_text(data["traceback"], encoding="utf-8")
    print(f"[agentic_runtime] Run failed: {exc}", flush=True)


def record_visual_frame(_config: dict, _frame: dict) -> None:
    """Visual frames are captured by showcase scene recorder when BUILDABLES_RECORD_PATH is set."""
    pass


def record_telemetry_sample(config: dict, sample: dict) -> None:
    samples_path = _run_dir(config) / "telemetry_samples.partial.jsonl"
    samples_path.parent.mkdir(parents=True, exist_ok=True)
    with samples_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sample) + "\n")
