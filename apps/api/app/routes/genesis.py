from pathlib import Path
import json

from fastapi import APIRouter, HTTPException
from app.models.manifest import Scenario
from app.services.cad_import.urdf_generator import generate_urdf
from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.genesis.imported_robot_loader import resolve_robot_description_candidates
from app.services.genesis_catalog.genesis_feature_catalog import get_genesis_feature_catalog
from app.services.project_store import load_manifest, project_dir

router = APIRouter(tags=["genesis"])


@router.get("/genesis/status")
def genesis_status() -> dict:
    status = genesis_runtime.status()
    return {
        "installed": status.installed,
        "version": status.version,
        "backend": status.backend,
        "device": status.device,
        "error": status.error,
        "setup_instructions": status.setup_instructions,
    }


@router.get("/genesis/capabilities")
def genesis_capabilities() -> dict:
    return get_genesis_feature_catalog()


@router.post("/projects/{project_id}/genesis/run-scene")
async def run_scene(project_id: str, steps: int = 240) -> dict:
    manifest = load_manifest(project_id)
    try:
        duration_s = max(0.5, float(steps) / 60.0)
        scenario = Scenario(
            id="genesis_run_scene",
            name="Genesis Run Scene",
            description="Direct run-scene invocation",
            duration_s=duration_s,
            config={"genesis_profile": "passive_gravity", "base_mode": "free_floating"},
        )
        from app.services.genesis_native.scenario_executor import run_genesis_scenario

        return run_genesis_scenario(project_dir(project_id), manifest, scenario, test_id="genesis_run_scene")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/projects/{project_id}/genesis/native-viewer/run")
async def launch_native_viewer(project_id: str, steps: int = 600) -> dict:
    manifest = load_manifest(project_id)
    pdir = project_dir(project_id)
    validation_path = pdir / "import_validation.json"
    if validation_path.is_file():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        summary = validation.get("launch_summary") or {}
        missing = validation.get("geometry", {}).get("missing_mesh_references") or []
        if missing or summary.get("launchable_native") is False:
            first = missing[0] if missing else summary.get("reason") or "missing mesh assets"
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot launch full model: {first}. "
                    "Fix missing meshes at import (upload zip/meshes or generate from STEP) or use web skeleton preview."
                ),
            )
    candidates = list(resolve_robot_description_candidates(manifest, pdir))
    fallback_path = pdir / "generated" / "robot_description" / "genesis_physics.urdf"
    generate_urdf(manifest, fallback_path)
    if fallback_path.exists():
        fallback_resolved = fallback_path.resolve()
        candidates = [("urdf", fallback_resolved), *[(t, p) for t, p in candidates if str(p) != str(fallback_resolved)]]
    if not candidates:
        raise HTTPException(
            status_code=400,
            detail="No robot description available for native viewer. Import URDF/MJCF first (Load Demo -> My Robot Dog).",
        )

    from app.services.genesis_native.native_viewer_runner import run_native_viewer
    from app.services.genesis_native.viewer_compat import is_viewer_fatal_error

    last_error: Exception | None = None
    for desc_type, desc_path in candidates:
        if not Path(desc_path).exists():
            continue
        try:
            result = run_native_viewer(desc_path, preferred_format=desc_type, steps=steps)
            return {"project_id": project_id, **result}
        except Exception as exc:  # noqa: PERF203
            last_error = exc
            if is_viewer_fatal_error(exc):
                break
            continue

    if last_error is None:
        raise HTTPException(status_code=500, detail="unknown native viewer error")

    detail = str(last_error)
    if is_viewer_fatal_error(last_error):
        raise HTTPException(
            status_code=500,
            detail=(
                "Native Genesis viewer failed during OpenGL initialization (common on AMD integrated GPUs). "
                f"Root error: {detail}. "
                "Run from terminal for full traceback: "
                "python scripts/debug_viewer.py genesis-world/examples/tutorials/control_your_robot.py. "
                "Use Buildables web replay on / for in-browser animation, or headless catalogue demos on /genesis."
            ),
        )
    if "Require joint limit for prismatic and revolute joints" in detail:
        raise HTTPException(
            status_code=400,
            detail=(
                "Native viewer failed: robot URDF is missing joint limits for one or more revolute/prismatic joints. "
                "Use a URDF with <limit lower=... upper=...> on each actuated joint."
            ),
        )
    raise HTTPException(status_code=500, detail=f"Native viewer launch failed: {detail}")
