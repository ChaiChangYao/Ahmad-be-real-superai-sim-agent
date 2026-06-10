"""Local subprocess execution of generated Genesis scripts."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

from app.paths import repo_root, showcase_launcher_script
from app.services.agentic.codegen.generator import get_generated_script
from app.services.agentic.codegen.safety import validate_script_safety
from app.services.agentic.execution.errors import RunAlreadyActiveError, UnsafeScriptError
from app.services.agentic.execution.log_stream import record_event, start_log_tailer
from app.services.agentic.execution.run_store import run_dir, save_run, update_run_status
from app.services.agentic.execution.schemas import ExecutionRequest, ExecutionRun, RunStatus
from app.services.project_store import project_dir


def _validate_script_source(project_id: str, script_id: str) -> tuple[Path, str]:
    scripts_dir = project_dir(project_id) / "generated" / "scripts"
    script_path = scripts_dir / f"{script_id}.py"
    if not script_path.is_file():
        raise FileNotFoundError(f"Generated script not found: {script_id}")
    resolved = script_path.resolve()
    root = project_dir(project_id).resolve()
    if root not in resolved.parents:
        raise UnsafeScriptError(
            "Script path escapes project directory.",
            suggested_actions=["Regenerate script from assistant"],
        )
    source = script_path.read_text(encoding="utf-8")
    errors, _warnings = validate_script_safety(source)
    if errors:
        raise UnsafeScriptError(
            errors[0],
            suggested_actions=["Regenerate script", "Fix blockers in test configuration"],
            debug_details="\n".join(errors),
        )
    return script_path, source


def _copy_script_artifacts(project_id: str, script_id: str, out_dir: Path) -> tuple[Path, Path]:
    gen_dir = out_dir / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)
    src_script = project_dir(project_id) / "generated" / "scripts" / f"{script_id}.py"
    src_ctx = project_dir(project_id) / "generated" / "scripts" / f"{script_id}.context.json"
    dst_script = gen_dir / "script.py"
    dst_ctx = gen_dir / "script.context.json"
    shutil.copy2(src_script, dst_script)

    ctx_data: dict = {}
    if src_ctx.is_file():
        ctx_data = json.loads(src_ctx.read_text(encoding="utf-8"))
    ctx_data["output_root"] = str(out_dir.resolve())
    ctx_data["script_id"] = script_id
    if "replay_config" not in ctx_data:
        ctx_data["replay_config"] = {}
    ctx_data["replay_config"]["output_state_timeseries_path"] = str((out_dir / "state_timeseries.json").resolve())
    ctx_data["replay_config"]["output_telemetry_timeseries_path"] = str((out_dir / "telemetry_timeseries.json").resolve())
    dst_ctx.write_text(json.dumps(ctx_data, indent=2), encoding="utf-8")
    return dst_script, dst_ctx


def prepare_local_run(request: ExecutionRequest, run: ExecutionRun) -> ExecutionRun:
    _validate_script_source(request.project_id, request.script_id)
    detail = get_generated_script(request.project_id, request.script_id)
    if detail:
        ctx = detail.get("context") or {}
        run.test_id = run.test_id or str(ctx.get("test_id") or "")
        run.template_id = str(ctx.get("template_id") or "")

    out = Path(run.run_dir)
    _copy_script_artifacts(request.project_id, request.script_id, out)
    run.status = RunStatus.preparing
    return save_run(run)


def build_launch_command(run_script: Path) -> list[str]:
    launcher = showcase_launcher_script().resolve()
    return [
        sys.executable,
        str(launcher),
        "--script",
        str(run_script.resolve()),
        "--headless",
        "--record-web",
    ]


def build_web_env(run: ExecutionRun, out_dir: Path, overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["BUILDABLES_WEB_MODE"] = "1"
    env["BUILDABLES_RECORD_WEB"] = "1"
    env["BUILDABLES_WEB_RECORD"] = "1"
    env["MPLBACKEND"] = "Agg"
    env["BUILDABLES_DISABLE_NATIVE_PLOTS"] = "1"
    env["BUILDABLES_SKIP_MANUAL_REPLAY_WRITE"] = "1"
    env["BUILDABLES_RECORD_PATH"] = str((out_dir / "state_timeseries.json").resolve())
    env["BUILDABLES_AGENTIC_RUN_ID"] = run.run_id
    env["BUILDABLES_AGENTIC_SCRIPT_ID"] = run.script_id
    api_dir = str(Path(__file__).resolve().parents[4])
    env["PYTHONPATH"] = api_dir + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    if overrides:
        env.update(overrides)
    return env


def spawn_local_process(
    request: ExecutionRequest,
    run: ExecutionRun,
    *,
    active_registry: dict[str, subprocess.Popen],
) -> tuple[ExecutionRun, subprocess.Popen]:
    running = [p for p in active_registry.values() if p.poll() is None]
    if running:
        raise RunAlreadyActiveError(
            f"A simulation is already running (pid {running[0].pid}). Cancel it or wait for completion.",
            suggested_actions=["Cancel the active run", "Wait for completion"],
        )

    out_dir = Path(run.run_dir)
    run_script = out_dir / "generated" / "script.py"
    cmd = build_launch_command(run_script)
    env = build_web_env(run, out_dir, request.env_overrides)

    stdout_path = out_dir / "stdout.log"
    stderr_path = out_dir / "stderr.log"
    stdout_f = stdout_path.open("w", encoding="utf-8")
    stderr_f = stderr_path.open("w", encoding="utf-8")

    creationflags = 0
    if sys.platform == "win32":
        creationflags |= subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    run.status = RunStatus.running
    run.started_at = datetime.now(UTC).isoformat()
    run.command = cmd
    save_run(run)

    record_event(run.run_id, "info", f"Starting: {' '.join(cmd)}", source="api")
    proc = subprocess.Popen(
        cmd,
        cwd=str(repo_root()),
        env=env,
        stdout=stdout_f,
        stderr=stderr_f,
        creationflags=creationflags,
    )
    stdout_f.close()
    stderr_f.close()

    run.pid = proc.pid
    run.status = RunStatus.running
    save_run(run)
    active_registry[run.run_id] = proc
    start_log_tailer(run.run_id, out_dir)
    return run, proc
