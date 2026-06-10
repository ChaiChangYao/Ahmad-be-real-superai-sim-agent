from __future__ import annotations

from pathlib import Path
import json


def write_run_artifacts(run_dir: Path, payload: dict) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "result.json"
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    state_path = run_dir / "state_timeseries.json"
    state_path.write_text(json.dumps(payload.get("state_timeseries", []), indent=2), encoding="utf-8")
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(json.dumps(payload.get("metrics", {}), indent=2), encoding="utf-8")
    logs_path = run_dir / "logs.txt"
    logs_path.write_text("\n".join(payload.get("logs", [])), encoding="utf-8")
    return {
        "result": str(result_path),
        "state_timeseries": str(state_path),
        "metrics": str(metrics_path),
        "logs": str(logs_path),
    }
