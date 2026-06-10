from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.genesis_workbench.requirements import ensure_launch_project_id
from app.services.genesis_showcase.example_script_runner import (
    get_launch_logs,
    get_launch_mesh_path,
    get_launch_replay,
    get_launch_status,
    get_launch_telemetry,
    get_launch_timeseries,
    launch_showcase_demo,
    list_showcase_entries,
)
from app.services.genesis_showcase.showcase_script_catalog import get_showcase_entry
from app.services.project_store import load_manifest

router = APIRouter(tags=["genesis-showcase"])


@router.get("/genesis/showcase/catalog")
def showcase_catalog() -> dict:
    entries = list_showcase_entries()
    available_count = sum(1 for e in entries if e["available"])
    return {
        "total": len(entries),
        "available": available_count,
        "entries": entries,
        "setup": {
            "genesis_world_root_env": "GENESIS_WORLD_ROOT",
            "genesis_nyx_root_env": "GENESIS_NYX_ROOT",
            "genesis_world_clone": "git clone https://github.com/Genesis-Embodied-AI/genesis-world.git",
            "genesis_nyx_clone": "git clone https://github.com/Genesis-Embodied-AI/genesis-nyx.git",
            "nyx_install": "pip install gs-nyx-plugin",
            "ipc_install": "pip install pyuipc",
        },
    }


@router.post("/projects/{project_id}/genesis/showcase/{scenario_id}/launch")
def launch_showcase(
    project_id: str,
    scenario_id: str,
    view_mode: str | None = Query(default=None, description="web=in-browser replay (default), native=OS window"),
    headless: bool | None = Query(default=None, description="Deprecated: use view_mode=web instead"),
) -> dict:
    if project_id == "genesis-workbench":
        ensure_launch_project_id()
    load_manifest(project_id)  # ensure project exists
    if get_showcase_entry(scenario_id) is None:
        raise HTTPException(status_code=404, detail=f"Showcase scenario not in catalogue: {scenario_id}")
    try:
        return launch_showcase_demo(project_id, scenario_id, view_mode=view_mode, headless=headless)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/showcase/launch/{launch_id}")
def showcase_launch_status(project_id: str, launch_id: str) -> dict:
    try:
        return get_launch_status(project_id, launch_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/showcase/launch/{launch_id}/timeseries")
def showcase_launch_timeseries(project_id: str, launch_id: str) -> dict:
    try:
        data = get_launch_replay(project_id, launch_id)
        frames = data["frames"]
        meta = data.get("meta") or {}
        manifest = data.get("replay_manifest")
        if manifest:
            meta = {**meta, "replay_manifest": manifest, "replay_fps": manifest.get("fps")}
        return {
            "launch_id": launch_id,
            "frames": len(frames),
            "state_timeseries": frames,
            "raw_frames": data.get("raw_frames") or [],
            "preview_frames": data.get("preview_frames") or [],
            "telemetry": data.get("telemetry"),
            "scene": data.get("scene") or {},
            "objects": data.get("objects") or [],
            "meta": meta,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/showcase/launch/{launch_id}/telemetry")
def showcase_launch_telemetry(project_id: str, launch_id: str) -> dict:
    try:
        telemetry = get_launch_telemetry(project_id, launch_id)
        if telemetry is None:
            raise HTTPException(status_code=404, detail=f"No telemetry for launch: {launch_id}")
        return {"launch_id": launch_id, "telemetry": telemetry}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/showcase/launch/{launch_id}/mesh/{mesh_path:path}")
def showcase_launch_mesh(project_id: str, launch_id: str, mesh_path: str):
    try:
        path = get_launch_mesh_path(project_id, launch_id, mesh_path)
        return FileResponse(path, media_type="application/json")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/showcase/launch/{launch_id}/logs")
def showcase_launch_logs(project_id: str, launch_id: str) -> dict:
    try:
        return get_launch_logs(project_id, launch_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
