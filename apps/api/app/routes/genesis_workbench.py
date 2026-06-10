from fastapi import APIRouter, HTTPException, Query
from starlette.concurrency import run_in_threadpool

from app.services.genesis_workbench.custom_project_launcher import launch_custom_web_viewer
from app.services.genesis_workbench.launch_readiness import build_launch_readiness
from app.services.genesis_workbench.requirements import (
    build_readiness,
    build_upload_requirements,
    ensure_launch_project_id,
)
from app.services.importers.import_validation import validate_sensor_feature_requirements
from app.services.project_store import load_manifest, project_dir

router = APIRouter(tags=["genesis-workbench"])


@router.get("/genesis/workbench/readiness")
async def workbench_readiness() -> dict:
    # build_readiness imports torch on first call — run off the event loop so /health stays responsive.
    return await run_in_threadpool(build_readiness)


@router.get("/genesis/workbench/upload-requirements")
def workbench_upload_requirements(
    context: str = Query(..., pattern="^(environment|demo|custom)$"),
    scenario_id: str | None = None,
    project_id: str | None = None,
) -> dict:
    return build_upload_requirements(context=context, scenario_id=scenario_id, project_id=project_id)


@router.get("/genesis/workbench/launch-project")
def workbench_launch_project() -> dict:
    pid = ensure_launch_project_id()
    return {"project_id": pid, "project_name": "Buildables Workbench"}


@router.get("/genesis/workbench/projects")
def list_workbench_projects() -> dict:
    root = project_dir("genesis-workbench").parent
    projects = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        manifest_path = path / "manifest.buildables.physics.json"
        if not manifest_path.exists():
            continue
        projects.append({"project_id": path.name, "path": str(path)})
    return {"projects": projects}


@router.get("/projects/{project_id}/genesis/workbench/launch-readiness")
def project_launch_readiness(project_id: str) -> dict:
    try:
        load_manifest(project_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_launch_readiness(project_id)


@router.post("/projects/{project_id}/genesis/workbench/launch-web")
def project_launch_web(
    project_id: str,
    steps: int = Query(default=400, ge=60, le=2000),
    skeleton: bool = Query(default=False),
) -> dict:
    try:
        load_manifest(project_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        return launch_custom_web_viewer(project_id, steps=steps, skeleton=skeleton)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/projects/{project_id}/genesis/workbench/sensor-validation")
def project_sensor_validation(project_id: str, test: str = Query(default="simulation")) -> dict:
    try:
        manifest = load_manifest(project_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    normalized = test.strip().lower()
    if normalized in ("simulation", "gui", "normal"):
        return {
            "enabled_features": [],
            "requirements": [],
            "errors": [],
            "can_launch_with_sensors": True,
            "test_type": normalized,
        }
    return validate_sensor_feature_requirements(manifest, [normalized])
