from __future__ import annotations

from pathlib import Path
import json
from uuid import uuid4
from datetime import datetime, UTC

from fastapi import APIRouter, HTTPException

from app.paths import projects_root
from app.services.genesis.scenario_runner import run_scenario_sync
from app.services.genesis_catalog.test_availability import build_test_availability
from app.services.genesis_catalog.test_catalog import get_test_catalog
from app.services.project_store import load_manifest, project_dir
from app.services.rendering.artifact_writer import write_render_output, write_sensor_output

router = APIRouter(tags=["tests"])


def _test_lookup() -> dict[str, dict]:
    return {test["id"]: test for test in get_test_catalog()}


def _scenario_for_test(test: dict, manifest) -> str | None:
    preferred = str(test.get("scenario_id")) if test.get("scenario_id") else None
    if preferred:
        if any(s.id == preferred for s in manifest.scenarios):
            return preferred
        fallback_map = {
            "stand_balance": "passive_gravity",
            "walk_forward": "mechanism_motion",
            "joint_sweep_collision": "joint_sweep_collision",
        }
        mapped = fallback_map.get(preferred)
        if mapped and any(s.id == mapped for s in manifest.scenarios):
            return mapped
        if any(s.id == test.get("id") for s in manifest.scenarios):
            return str(test.get("id"))
    command_hint = test.get("parameters", {}).get("command_hint")
    if not command_hint:
        return None
    for scenario in manifest.scenarios:
        if scenario.config.get("command_hint") == command_hint:
            return scenario.id
    return None


def _run_result_to_test_result(project_id: str, test: dict, run_result: dict) -> dict:
    return {
        "test_id": test["id"],
        "test_name": test["name"],
        "category": test["category"],
        "status": run_result.get("status", "error"),
        "run_id": run_result.get("run_id"),
        "project_id": project_id,
        "project_mode": "imported_project" if project_id.startswith("imported-") else "default_demo",
        "robot_description_type": "urdf" if run_result.get("artifacts", {}).get("urdf_path") else "mjcf" if run_result.get("artifacts", {}).get("mjcf_path") else "generated",
        "metrics": run_result.get("metrics", {}),
        "logs": run_result.get("logs", []),
        "artifacts": run_result.get("artifacts", {}),
        "sensor_output": {
            "imu": {
                "max_pitch_deg": run_result.get("metrics", {}).get("max_pitch_deg"),
                "max_roll_deg": run_result.get("metrics", {}).get("max_roll_deg"),
            },
            "contacts": run_result.get("metrics", {}).get("foot_contact_ratio"),
        },
        "render_output": {
            "frontend_preview": True,
            "genesis_render_artifact_available": False,
        },
        "genesis_used": run_result.get("genesis_used", False),
    }


@router.get("/projects/{project_id}/tests/catalog")
def get_project_test_catalog(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    tests = get_test_catalog()
    return {"project_id": project_id, "project_type": manifest.project_type, "tests": tests}


@router.get("/projects/{project_id}/tests/available")
def get_project_test_availability(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    return {"project_id": project_id, "project_type": manifest.project_type, "tests": build_test_availability(manifest)}


@router.post("/projects/{project_id}/tests/{test_id}/run")
async def run_selected_test(project_id: str, test_id: str) -> dict:
    aliases = {
        "passive-gravity": "stand_balance",
        "joint-slider": "joint_sweep",
        "joint-sweep": "joint_sweep",
        "mechanism-motion": "mechanism_motion",
        "lateral-push": "stand_balance",
        "payload-load": "payload_carry",
        "torque-limit": "torque_margin",
        "moment-stability": "stand_balance",
        "contact-collision": "joint_sweep_collision",
        "sensor-readout": "sensor_visibility",
        "render-camera": "sensor_visibility",
        "deformation": "component_fit",
        "control-script": "control_script",
        "visual-collision-alignment": "imported_cad_validation",
    }
    test_id = aliases.get(test_id, test_id)
    manifest = load_manifest(project_id)
    availability = {item["id"]: item for item in build_test_availability(manifest)}
    selected = availability.get(test_id)
    if not selected:
        raise HTTPException(status_code=404, detail=f"Test not found: {test_id}")
    if selected["status"] != "available":
        raise HTTPException(status_code=400, detail={"status": selected["status"], "reasons": selected.get("reasons", [])})

    test = _test_lookup()[test_id]
    scenario_id = _scenario_for_test(test, manifest)
    if not scenario_id:
        raise HTTPException(status_code=501, detail="Selected test has no runnable scenario binding yet.")
    scenario = next((s for s in manifest.scenarios if s.id == scenario_id), None)
    if not scenario:
        raise HTTPException(status_code=404, detail=f"Scenario binding not found: {scenario_id}")

    try:
        run_result = run_scenario_sync(project_dir(project_id), manifest, scenario, test_id=test_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    test_result = _run_result_to_test_result(project_id, test, run_result)
    run_dir = project_dir(project_id) / "runs" / run_result["run_id"]
    sensor_path = write_sensor_output(run_dir, test_result["sensor_output"])
    render_path = write_render_output(run_dir, test_result["render_output"])
    test_result["artifacts"]["sensor_output_path"] = sensor_path
    test_result["artifacts"]["render_output_path"] = render_path
    return test_result


@router.post("/projects/{project_id}/tests/run-suite")
async def run_test_suite(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    available = [item for item in build_test_availability(manifest) if item["status"] == "available" and item["id"] != "full_project_suite"]
    results: list[dict] = []
    for test in available:
        scenario_id = _scenario_for_test(test, manifest)
        if not scenario_id:
            continue
        scenario = next((s for s in manifest.scenarios if s.id == scenario_id), None)
        if not scenario:
            continue
        run_result = run_scenario_sync(project_dir(project_id), manifest, scenario, test_id=test["id"])
        results.append(_run_result_to_test_result(project_id, test, run_result))

    suite_run_id = f"suite-{uuid4().hex[:10]}"
    suite_dir = project_dir(project_id) / "runs" / suite_run_id
    suite_dir.mkdir(parents=True, exist_ok=True)
    pass_count = sum(1 for result in results if result["status"] == "pass")
    payload = {
        "suite_run_id": suite_run_id,
        "project_id": project_id,
        "started_at": datetime.now(UTC).isoformat(),
        "results": results,
        "summary": {
            "total": len(results),
            "pass": pass_count,
            "fail": sum(1 for result in results if result["status"] == "fail"),
            "warning": sum(1 for result in results if result["status"] == "warning"),
            "error": sum(1 for result in results if result["status"] == "error"),
            "suite_pass_rate": round((pass_count / max(1, len(results))) * 100.0, 2),
        },
    }
    (suite_dir / "suite_result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


@router.get("/runs/{run_id}/sensor-output")
def get_run_sensor_output(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/sensor_output.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Sensor output not found")


@router.get("/runs/{run_id}/render-output")
def get_run_render_output(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/render_output.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Render output not found")


@router.get("/runs/{run_id}")
def get_run_result(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/result.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/runs/{run_id}/state-timeseries")
def get_run_state_timeseries(run_id: str) -> list:
    for path in projects_root().glob(f"*/runs/{run_id}/state_timeseries.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="State timeseries not found")


@router.get("/runs/{run_id}/metrics")
def get_run_metrics(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/metrics.json"):
        return json.loads(path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Metrics not found")


@router.get("/runs/{run_id}/logs")
def get_run_logs(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/logs.txt"):
        return {"run_id": run_id, "logs": path.read_text(encoding="utf-8").splitlines()}
    raise HTTPException(status_code=404, detail="Logs not found")


@router.get("/runs/{run_id}/artifacts")
def get_run_artifacts(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/result.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {"run_id": run_id, "artifacts": payload.get("artifacts", {})}
    raise HTTPException(status_code=404, detail="Artifacts not found")


@router.get("/runs/{run_id}/video")
def get_run_video(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/result.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        video = payload.get("artifacts", {}).get("video_path")
        if video:
            return {"run_id": run_id, "video": video}
        raise HTTPException(status_code=404, detail="Video artifact unavailable for this run")
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/runs/{run_id}/frames")
def get_run_frames(run_id: str) -> dict:
    for path in projects_root().glob(f"*/runs/{run_id}/result.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        frames = payload.get("artifacts", {}).get("frames_path")
        if frames:
            return {"run_id": run_id, "frames": frames}
        raise HTTPException(status_code=404, detail="Frame artifacts unavailable for this run")
    raise HTTPException(status_code=404, detail="Run not found")


@router.post("/projects/{project_id}/tests/passive-gravity/run")
async def run_passive_gravity(project_id: str) -> dict:
    return await run_selected_test(project_id, "stand_balance")


@router.post("/projects/{project_id}/tests/joint-sweep/run")
async def run_joint_sweep(project_id: str) -> dict:
    return await run_selected_test(project_id, "joint_sweep")


@router.post("/projects/{project_id}/tests/joint-slider/run")
async def run_joint_slider(project_id: str) -> dict:
    return await run_selected_test(project_id, "joint_sweep")


@router.post("/projects/{project_id}/tests/mechanism-motion/run")
async def run_mechanism_motion(project_id: str) -> dict:
    return await run_selected_test(project_id, "mechanism_motion")


@router.post("/projects/{project_id}/tests/control-script/run")
async def run_control_script(project_id: str) -> dict:
    return await run_selected_test(project_id, "control_script")


@router.post("/projects/{project_id}/tests/lateral-push/run")
async def run_lateral_push(project_id: str) -> dict:
    return await run_selected_test(project_id, "lateral-push")


@router.post("/projects/{project_id}/tests/payload-load/run")
async def run_payload_load(project_id: str) -> dict:
    return await run_selected_test(project_id, "payload-load")


@router.post("/projects/{project_id}/tests/torque-limit/run")
async def run_torque_limit(project_id: str) -> dict:
    return await run_selected_test(project_id, "torque-limit")


@router.post("/projects/{project_id}/tests/moment-stability/run")
async def run_moment_stability(project_id: str) -> dict:
    return await run_selected_test(project_id, "moment-stability")


@router.post("/projects/{project_id}/tests/contact-collision/run")
async def run_contact_collision(project_id: str) -> dict:
    return await run_selected_test(project_id, "contact-collision")


@router.post("/projects/{project_id}/tests/sensor-readout/run")
async def run_sensor_readout(project_id: str) -> dict:
    return await run_selected_test(project_id, "sensor-readout")


@router.post("/projects/{project_id}/tests/render-camera/run")
async def run_render_camera(project_id: str) -> dict:
    return await run_selected_test(project_id, "render-camera")


@router.post("/projects/{project_id}/tests/deformation/run")
async def run_deformation(project_id: str) -> dict:
    return await run_selected_test(project_id, "deformation")


@router.post("/projects/{project_id}/tests/visual-collision-alignment/run")
async def run_visual_collision_alignment(project_id: str) -> dict:
    return await run_selected_test(project_id, "imported_cad_validation")
