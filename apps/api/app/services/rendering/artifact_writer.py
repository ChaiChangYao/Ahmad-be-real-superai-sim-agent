from __future__ import annotations

from pathlib import Path
import json


def write_sensor_output(run_dir: Path, payload: dict) -> str:
    out_path = run_dir / "sensor_output.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_path)


def write_render_output(run_dir: Path, payload: dict) -> str:
    out_path = run_dir / "render_output.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_path)
