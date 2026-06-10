from fastapi import APIRouter, HTTPException
from app.services.genesis.scenario_runner import run_scenario_sync
from app.services.genesis.demo_project_setup import sync_genesis_showcase_scenarios
from app.services.project_store import load_manifest, project_dir

router = APIRouter(tags=["scenarios"])


@router.get("/projects/{project_id}/scenarios")
def list_scenarios(project_id: str) -> list[dict]:
    manifest = load_manifest(project_id)
    return [s.model_dump() for s in manifest.scenarios]


@router.post("/projects/{project_id}/scenarios/{scenario_id}/run")
def run_scenario(project_id: str, scenario_id: str) -> dict:
    manifest = load_manifest(project_id)
    scenario = next((s for s in manifest.scenarios if s.id == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")
    try:
        return run_scenario_sync(project_dir(project_id), manifest, scenario)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/projects/{project_id}/scenarios/sync-genesis-showcase")
def sync_showcase_scenarios(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    changed = sync_genesis_showcase_scenarios(manifest)
    if changed:
        from app.services.project_store import save_manifest

        save_manifest(project_id, manifest)
    return {"updated": changed, "scenario_count": len(manifest.scenarios)}
