"""Non-blocking run lifecycle management."""
from __future__ import annotations

import subprocess
import threading
import time
from datetime import datetime, UTC
from pathlib import Path

from app.services.agentic.execution.cancellation import terminate_process
from app.services.agentic.execution.errors import RunNotFoundError
from app.services.agentic.execution.local_runner import prepare_local_run, spawn_local_process
from app.services.agentic.execution.log_stream import get_events, record_event, stop_log_tailer, tail_logs
from app.services.agentic.execution.run_store import load_run, save_run
from app.services.agentic.execution.schemas import ExecutionRequest, ExecutionRun, RunStatus
from app.services.agentic.execution.status import build_manifest, finalize_run
from app.services.agentic.execution.artifact_store import list_artifacts

_ACTIVE: dict[str, subprocess.Popen] = {}
_WATCHERS: dict[str, threading.Thread] = {}


def _watch_process(project_id: str, run_id: str, proc: subprocess.Popen, timeout_seconds: int) -> None:
    out_dir = Path(load_run(project_id, run_id).run_dir)  # type: ignore[union-attr]
    deadline = time.monotonic() + timeout_seconds
    while proc.poll() is None:
        if time.monotonic() > deadline:
            record_event(run_id, "error", f"Run timed out after {timeout_seconds}s", source="worker")
            run = load_run(project_id, run_id)
            if run:
                run.status = RunStatus.timed_out
                run.error_summary = f"Simulation exceeded {timeout_seconds} second limit."
                save_run(run)
            terminate_process(proc)
            break
        time.sleep(0.5)

    stop_log_tailer(run_id, out_dir)
    code = proc.poll()
    _ACTIVE.pop(run_id, None)

    run = load_run(project_id, run_id)
    if run is None:
        return
    if run.status == RunStatus.cancelled:
        run.exit_code = code if code is not None else -1
        run.completed_at = datetime.now(UTC).isoformat()
    else:
        run = finalize_run(run, out_dir, code)
    run.artifacts = list_artifacts(project_id, run_id)
    save_run(run)
    record_event(run_id, "info", f"Run finished exit_code={code} status={run.status}", source="worker")


def start_run_async(request: ExecutionRequest, run: ExecutionRun) -> ExecutionRun:
    run = prepare_local_run(request, run)
    run.status = RunStatus.validating
    save_run(run)
    run, proc = spawn_local_process(request, run, active_registry=_ACTIVE)
    thread = threading.Thread(
        target=_watch_process,
        args=(request.project_id, run.run_id, proc, request.timeout_seconds),
        name=f"agentic-watch-{run.run_id}",
        daemon=True,
    )
    _WATCHERS[run.run_id] = thread
    thread.start()
    return run


def get_run_status(project_id: str, run_id: str) -> ExecutionRun:
    run = load_run(project_id, run_id)
    if run is None:
        raise RunNotFoundError(f"Run not found: {run_id}")

    proc = _ACTIVE.get(run_id)
    out_dir = Path(run.run_dir)
    if proc is not None and proc.poll() is None:
        run.status = RunStatus.running
        run.pid = proc.pid
        if out_dir.joinpath("state_timeseries.partial.json").is_file():
            run.status = RunStatus.recording
    elif proc is not None:
        code = proc.poll()
        run = finalize_run(run, out_dir, code)
        _ACTIVE.pop(run_id, None)

    if out_dir.joinpath("manifest.json").is_file():
        try:
            build_manifest(run, out_dir)
        except Exception:
            pass

    run.artifacts = list_artifacts(project_id, run_id)
    return save_run(run)


def cancel_run(project_id: str, run_id: str) -> ExecutionRun:
    run = load_run(project_id, run_id)
    if run is None:
        raise RunNotFoundError(f"Run not found: {run_id}")

    proc = _ACTIVE.get(run_id)
    if proc is not None and proc.poll() is None:
        run.status = RunStatus.cancelled
        save_run(run)
        record_event(run_id, "warning", "Run cancelled by user", source="api")
        terminate_process(proc)
        stop_log_tailer(run_id, Path(run.run_dir))
        _ACTIVE.pop(run_id, None)
        run = finalize_run(run, Path(run.run_dir), proc.poll())
        return save_run(run)

    if run.status in (RunStatus.running, RunStatus.recording, RunStatus.queued, RunStatus.preparing):
        run.status = RunStatus.cancelled
        run.completed_at = datetime.now(UTC).isoformat()
        return save_run(run)
    return run


def get_run_logs(project_id: str, run_id: str, *, tail: int = 200) -> dict:
    run = load_run(project_id, run_id)
    if run is None:
        raise RunNotFoundError(f"Run not found: {run_id}")
    logs = tail_logs(Path(run.run_dir), tail=tail)
    logs["run_id"] = run_id
    logs["events"] = [e.model_dump() for e in get_events(run_id)]
    return logs


def is_run_active(run_id: str) -> bool:
    proc = _ACTIVE.get(run_id)
    return proc is not None and proc.poll() is None
