"""Persist execution runs to disk."""
from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

from app.services.agentic.execution.schemas import ExecutionRun, RunStatus
from app.services.project_store import project_dir


def run_dir(project_id: str, run_id: str) -> Path:
    return project_dir(project_id) / "runs" / run_id


def new_run_id() -> str:
    return f"agentic-{uuid4().hex[:10]}"


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def save_run(run: ExecutionRun) -> ExecutionRun:
    path = run_dir(run.project_id, run.run_id) / "run.json"
    atomic_write_json(path, run.model_dump(mode="json"))
    return run


def load_run(project_id: str, run_id: str) -> ExecutionRun | None:
    path = run_dir(project_id, run_id) / "run.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return ExecutionRun.model_validate(data)


def list_runs(project_id: str) -> list[ExecutionRun]:
    runs_root = project_dir(project_id) / "runs"
    if not runs_root.is_dir():
        return []
    items: list[ExecutionRun] = []
    for child in sorted(runs_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not child.is_dir() or not child.name.startswith("agentic-"):
            continue
        run = load_run(project_id, child.name)
        if run:
            items.append(run)
    return items


def create_run_record(
    project_id: str,
    script_id: str,
    test_id: str = "",
    template_id: str = "",
    backend: str = "local",
    timeout_seconds: int = 300,
) -> ExecutionRun:
    rid = new_run_id()
    rdir = run_dir(project_id, rid)
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "artifacts").mkdir(exist_ok=True)
    (rdir / "generated").mkdir(exist_ok=True)
    now = datetime.now(UTC).isoformat()
    run = ExecutionRun(
        run_id=rid,
        project_id=project_id,
        script_id=script_id,
        test_id=test_id,
        template_id=template_id,
        backend=backend,  # type: ignore[arg-type]
        status=RunStatus.queued,
        created_at=now,
        run_dir=str(rdir.resolve()),
        timeout_seconds=timeout_seconds,
        stdout_path=str((rdir / "stdout.log").resolve()),
        stderr_path=str((rdir / "stderr.log").resolve()),
        combined_log_path=str((rdir / "combined.log").resolve()),
        manifest_path=str((rdir / "manifest.json").resolve()),
        replay_path=str((rdir / "state_timeseries.json").resolve()),
        telemetry_path=str((rdir / "telemetry_timeseries.json").resolve()),
    )
    return save_run(run)


def update_run_status(project_id: str, run_id: str, **fields) -> ExecutionRun:
    run = load_run(project_id, run_id)
    if run is None:
        raise FileNotFoundError(f"Run not found: {run_id}")
    data = run.model_dump()
    data.update(fields)
    updated = ExecutionRun.model_validate(data)
    return save_run(updated)
