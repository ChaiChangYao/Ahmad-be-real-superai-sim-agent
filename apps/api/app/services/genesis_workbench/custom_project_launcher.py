from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.paths import repo_root, showcase_launcher_script
from app.services.genesis_showcase.example_script_runner import (
    _ACTIVE,
    _attach_runtime,
    _finalize_meta,
    _purge_stale_active,
    _run_dir,
    _start_log_tailer,
)
from app.services.genesis_workbench.launch_readiness import build_launch_readiness
from app.services.genesis_workbench.session_log import append_log
from app.services.project_store import load_manifest

_CUSTOM_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "imported_robot_web_demo.py"


def launch_custom_web_viewer(project_id: str, *, steps: int = 400, skeleton: bool = False) -> dict:
    readiness = build_launch_readiness(project_id)
    if skeleton:
        if not readiness.get("can_preview_skeleton_web"):
            reason = readiness.get("disabled_reason_web") or "Skeleton preview not available"
            raise RuntimeError(reason)
    elif not readiness["can_launch_web"]:
        reason = readiness.get("disabled_reason_web") or "Web viewer launch not available"
        raise RuntimeError(reason)

    load_manifest(project_id)

    _purge_stale_active()
    running = [p for p in _ACTIVE.values() if p.poll() is None]
    if running:
        raise RuntimeError(
            f"A simulation is already running (pid {running[0].pid}). Wait for it to finish before launching again."
        )

    if not _CUSTOM_SCRIPT.is_file():
        raise FileNotFoundError(f"Custom web demo script missing: {_CUSTOM_SCRIPT}")

    launch_id = f"custom-{uuid4().hex[:10]}"
    out_dir = _run_dir(project_id, launch_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    launcher = showcase_launcher_script().resolve()
    argv = [
        sys.executable,
        str(launcher),
        "--script",
        str(_CUSTOM_SCRIPT.resolve()),
        "--headless",
        "--record-web",
    ]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["BUILDABLES_SHOWCASE_LAUNCH_ID"] = launch_id
    env["BUILDABLES_RECORD_PATH"] = str(out_dir / "state_timeseries.json")
    env["BUILDABLES_PROJECT_ID"] = project_id
    env["BUILDABLES_CUSTOM_STEPS"] = str(steps)
    env["BUILDABLES_SKELETON_PREVIEW"] = "1" if skeleton else "0"
    api_dir = str(Path(__file__).resolve().parents[3])
    env["PYTHONPATH"] = api_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    stdout_path = out_dir / "stdout.txt"
    stderr_path = out_dir / "stderr.txt"
    stdout_f = stdout_path.open("w", encoding="utf-8")
    stderr_f = stderr_path.open("w", encoding="utf-8")

    creationflags = 0
    if sys.platform == "win32":
        creationflags |= subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    append_log("launch", f"Starting custom web {launch_id} project={project_id}")
    append_log("launch", f"argv={argv}")

    meta = {
        "launch_id": launch_id,
        "project_id": project_id,
        "scenario_id": "custom-imported-robot",
        "demo_name": "Imported robot (skeleton preview)" if skeleton else "Imported robot (web viewer)",
        "layer": "custom",
        "repo": "buildables",
        "script_path": str(_CUSTOM_SCRIPT),
        "argv": argv,
        "view_mode": "web",
        "headless": True,
        "started_at": datetime.now(UTC).isoformat(),
        "status": "launching",
        "lifecycle": "launching",
        "note": (
            "Running imported robot skeleton preview (meshes missing) in headless Genesis."
            if skeleton
            else "Running imported robot in headless Genesis and recording frames for the web viewer."
        ),
    }
    (out_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    proc = subprocess.Popen(
        argv,
        cwd=str(repo_root()),
        env=env,
        stdout=stdout_f,
        stderr=stderr_f,
        creationflags=creationflags,
    )
    stdout_f.close()
    stderr_f.close()
    _ACTIVE[launch_id] = proc
    _start_log_tailer(launch_id, out_dir)

    meta["pid"] = proc.pid
    meta["status"] = "running"
    meta["lifecycle"] = "running"
    (out_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return _attach_runtime(meta, out_dir)
