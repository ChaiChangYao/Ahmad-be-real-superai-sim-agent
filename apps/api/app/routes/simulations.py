from __future__ import annotations

from pathlib import Path
from time import time
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.controls.robot_dog_controller import command_to_targets
from app.services.genesis.scenario_runner import run_interactive_segment, run_scenario_sync
from app.services.project_store import load_manifest, project_dir
from app.paths import projects_root

router = APIRouter(tags=["simulations"])

interactive_sessions: dict[str, dict] = {}


class InteractiveCommandRequest(BaseModel):
    session_id: str | None = None
    command: str
    duration_s: float = 0.35


@router.post("/projects/{project_id}/simulations/run")
async def run_default_simulation(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    if not manifest.scenarios:
        raise HTTPException(status_code=400, detail="No scenarios defined in manifest.")
    try:
        return run_scenario_sync(project_dir(project_id), manifest, manifest.scenarios[0])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/projects/{project_id}/simulations/interactive/start")
def interactive_start(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    session_id = f"{project_id}:interactive"
    interactive_sessions[session_id] = {"project_id": project_id, "active_command": "stand", "started_ts": time(), "manifest_project": manifest.project_id, "last_state": {}}
    return {"session_id": session_id, "status": "started"}


@router.post("/projects/{project_id}/simulations/interactive/command")
async def interactive_command(project_id: str, payload: InteractiveCommandRequest) -> dict:
    session_id = payload.session_id or f"{project_id}:interactive"
    session = interactive_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interactive simulation not started.")
    session["active_command"] = payload.command
    manifest = load_manifest(project_id)
    now = time()
    elapsed = now - float(session["started_ts"])
    targets = command_to_targets(payload.command, elapsed)
    segment = run_interactive_segment(manifest, payload.command, duration_s=max(0.25, min(0.5, payload.duration_s)), project_dir=project_dir(project_id))
    session["last_state"] = segment.get("state", {})
    return {
        "session_id": session_id,
        "accepted": True,
        "targets": targets,
        "state": segment.get("state", {}),
        "timeseries": segment.get("timeseries", []),
        "metrics": segment.get("metrics", {}),
        "logs": [f"[Interactive] command={payload.command}", f"[Interactive] step_count={segment.get('step_count', 0)}"],
        "genesis_used": segment.get("genesis_used", False),
        "mocked": segment.get("mocked", False),
    }


@router.post("/projects/{project_id}/simulations/interactive/stop")
def interactive_stop(project_id: str) -> dict:
    session_id = f"{project_id}:interactive"
    interactive_sessions.pop(session_id, None)
    return {"status": "stopped"}


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    result_path = _find_run_file(run_id, "result.json")
    if not result_path:
        raise HTTPException(status_code=404, detail="Run not found")
    return json.loads(result_path.read_text(encoding="utf-8"))


@router.get("/runs/{run_id}/results")
def get_run_results(run_id: str) -> dict:
    return get_run(run_id)


@router.get("/runs/{run_id}/logs")
def get_run_logs(run_id: str) -> dict:
    logs_path = _find_run_file(run_id, "logs.txt")
    if not logs_path:
        raise HTTPException(status_code=404, detail="Run logs not found")
    return {"logs": logs_path.read_text(encoding="utf-8").splitlines()}


@router.get("/runs/{run_id}/video")
def get_run_video(run_id: str) -> dict:
    video_path = _find_run_file(run_id, "video.mp4")
    return {"video_path": str(video_path) if video_path else None}


@router.get("/runs/{run_id}/artifacts")
def get_run_artifacts(run_id: str) -> dict:
    base = _find_run_dir(run_id)
    if not base:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"files": [str(p.name) for p in base.iterdir()]}


def _find_run_dir(run_id: str) -> Path | None:
    sim_root = projects_root()
    if not sim_root.exists():
        return None
    for candidate in sim_root.glob(f"*/runs/{run_id}"):
        if candidate.exists():
            return candidate
    return None


def _find_run_file(run_id: str, filename: str) -> Path | None:
    run_dir = _find_run_dir(run_id)
    if not run_dir:
        return None
    file_path = run_dir / filename
    return file_path if file_path.exists() else None
