"""Agentic Simulation Layer preflight API — no Genesis launch."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel

from app.services.agentic.buildables_cad_bridge import (
    request_boundary_conditions,
    request_collision_mesh_generation,
    request_material_metadata,
    request_missing_mesh_generation,
    request_sensor_mount_generation,
)
from app.services.agentic.cad_recovery import (
    attempt_generate_missing_meshes_from_step,
    attempt_step_static_preview,
)
from app.services.agentic.goal_parser import parse_user_goal
from app.services.agentic.project_state import AgenticProjectState, load_agentic_state, save_agentic_state, update_agentic_state
from app.services.agentic.safe_defaults import generate_safe_defaults
from app.services.agentic.dependencies import get_optional_feature_status
from app.services.agentic.errors import AgenticError, agentic_error_to_dict
from app.services.agentic.file_inventory import scan_project_assets
from app.services.agentic.mesh_inspector import inspect_project_meshes
from app.services.agentic.planner import create_simulation_plan
from app.services.agentic.schemas import (
    MeshReference,
    ProjectInspectionReport,
    TestRequirementsResponse,
)
from app.services.agentic.test_requirements import evaluate_all_tests, get_all_test_specs
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.project_store import project_dir

router = APIRouter(tags=["agentic"])


class PlanRequest(BaseModel):
    user_goal: str | None = None


class RecoverMeshesRequest(BaseModel):
    missing_meshes: list[MeshReference] = []
    mappings: dict[str, str] | None = None


class ParseGoalRequest(BaseModel):
    user_goal: str


class GenerateDefaultsRequest(BaseModel):
    test_id: str
    selected_options: dict | None = None


class CadBridgeMeshesRequest(BaseModel):
    missing_meshes: list[MeshReference] = []


class CadBridgeSensorRequest(BaseModel):
    sensor_type: str = "imu"


class CadBridgeBoundaryRequest(BaseModel):
    test_type: str = "cfd_readiness"


def _ensure_project(project_id: str) -> None:
    if not project_dir(project_id).is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")


@router.get("/agentic/dependencies")
def agentic_dependencies() -> dict:
    return get_optional_feature_status()


@router.post("/projects/{project_id}/scan")
def scan_project(project_id: str) -> dict:
    _ensure_project(project_id)
    try:
        assets = scan_project_assets(project_id)
        return {"project_id": project_id, "assets": [a.model_dump() for a in assets], "count": len(assets)}
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.post("/projects/{project_id}/inspect")
def inspect_project(project_id: str) -> dict:
    _ensure_project(project_id)
    try:
        assets = scan_project_assets(project_id)
        robot_descs = inspect_all_robot_descriptions(project_id)
        mesh_inspections = inspect_project_meshes(project_id)
        missing_mesh_count = sum(
            1 for r in robot_descs for m in r.mesh_references if m.status == "missing"
        )
        report = ProjectInspectionReport(
            project_id=project_id,
            assets=assets,
            robot_descriptions=robot_descs,
            mesh_inspections=mesh_inspections,
            missing_mesh_count=missing_mesh_count,
            warnings=[w for r in robot_descs for w in r.warnings] + [w for m in mesh_inspections for w in m.warnings],
            errors=[e for r in robot_descs for e in r.errors] + [e for m in mesh_inspections for e in m.errors],
        )
        update_agentic_state(project_id, latest_inspection=report.model_dump())
        return report.model_dump()
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.post("/projects/{project_id}/parse-goal")
def parse_goal(project_id: str, body: ParseGoalRequest) -> dict:
    _ensure_project(project_id)
    result = parse_user_goal(body.user_goal)
    return result.model_dump()


@router.post("/projects/{project_id}/plan")
def plan_project(project_id: str, body: PlanRequest) -> dict:
    _ensure_project(project_id)
    try:
        parsed = parse_user_goal(body.user_goal)
        goal_text = body.user_goal
        if parsed.candidate_tests and body.user_goal:
            goal_text = body.user_goal
        plan = create_simulation_plan(project_id, goal_text, candidate_tests=parsed.candidate_tests or None)
        update_agentic_state(
            project_id,
            user_goal=body.user_goal,
            latest_plan=plan.model_dump(),
            candidate_tests=parsed.candidate_tests,
            selected_test=plan.selected_test,
            chat_summary=plan.agent_explanation,
        )
        return {**plan.model_dump(), "goal_parse": parsed.model_dump()}
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.get("/projects/{project_id}/test-requirements")
def test_requirements(project_id: str) -> dict:
    _ensure_project(project_id)
    try:
        specs = get_all_test_specs()
        readiness = evaluate_all_tests(project_id)
        response = TestRequirementsResponse(
            project_id=project_id,
            specs=specs,
            readiness=readiness,
        )
        return response.model_dump()
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.post("/projects/{project_id}/recover/step-preview")
def recover_step_preview(project_id: str) -> dict:
    _ensure_project(project_id)
    try:
        result = attempt_step_static_preview(project_id)
        return result.model_dump()
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.post("/projects/{project_id}/recover/missing-meshes")
def recover_missing_meshes(project_id: str, body: RecoverMeshesRequest) -> dict:
    _ensure_project(project_id)
    try:
        missing = body.missing_meshes
        if not missing:
            robot_descs = inspect_all_robot_descriptions(project_id)
            missing = [m for r in robot_descs for m in r.mesh_references if m.status == "missing"]
        result = attempt_generate_missing_meshes_from_step(
            project_id,
            missing,
            mappings=body.mappings,
        )
        return result.model_dump()
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.get("/projects/{project_id}/recover/status")
def recover_status(project_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.cad_recovery import cad_recovery_status

    return cad_recovery_status(project_id)


@router.get("/projects/{project_id}/agentic-state")
def get_agentic_state(project_id: str) -> dict:
    _ensure_project(project_id)
    state = load_agentic_state(project_id)
    if state is None:
        return {"project_id": project_id, "state": None}
    return {"project_id": project_id, "state": state.model_dump()}


@router.put("/projects/{project_id}/agentic-state")
def put_agentic_state(project_id: str, body: dict) -> dict:
    _ensure_project(project_id)
    state = AgenticProjectState(project_id=project_id, **{k: v for k, v in body.items() if k != "project_id"})
    save_agentic_state(state)
    return state.model_dump()


@router.post("/projects/{project_id}/generate-defaults")
def post_generate_defaults(project_id: str, body: GenerateDefaultsRequest) -> dict:
    _ensure_project(project_id)
    try:
        return generate_safe_defaults(project_id, body.test_id, body.selected_options)
    except AgenticError as exc:
        raise HTTPException(status_code=exc.http_status, detail=agentic_error_to_dict(exc)) from exc


@router.post("/projects/{project_id}/cad-bridge/missing-meshes")
def cad_bridge_missing_meshes(project_id: str, body: CadBridgeMeshesRequest) -> dict:
    _ensure_project(project_id)
    missing = body.missing_meshes
    if not missing:
        robot_descs = inspect_all_robot_descriptions(project_id)
        missing = [m for r in robot_descs for m in r.mesh_references if m.status == "missing"]
    return request_missing_mesh_generation(project_id, missing).model_dump()


@router.post("/projects/{project_id}/cad-bridge/collision-meshes")
def cad_bridge_collision(project_id: str) -> dict:
    _ensure_project(project_id)
    return request_collision_mesh_generation(project_id).model_dump()


@router.post("/projects/{project_id}/cad-bridge/sensor-mount")
def cad_bridge_sensor(project_id: str, body: CadBridgeSensorRequest) -> dict:
    _ensure_project(project_id)
    return request_sensor_mount_generation(project_id, body.sensor_type).model_dump()


@router.post("/projects/{project_id}/cad-bridge/material-metadata")
def cad_bridge_material(project_id: str) -> dict:
    _ensure_project(project_id)
    return request_material_metadata(project_id).model_dump()


@router.post("/projects/{project_id}/cad-bridge/boundary-conditions")
def cad_bridge_boundary(project_id: str, body: CadBridgeBoundaryRequest) -> dict:
    _ensure_project(project_id)
    return request_boundary_conditions(project_id, body.test_type).model_dump()


class GenerateScriptRequest(BaseModel):
    test_id: str
    fallback_mode: str | None = None
    user_parameters: dict | None = None


@router.post("/projects/{project_id}/generate-script")
def generate_script(project_id: str, body: GenerateScriptRequest) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.codegen.generator import generate_genesis_script

    result = generate_genesis_script(
        project_id,
        body.test_id,
        user_parameters=body.user_parameters,
        fallback_mode=body.fallback_mode,
    )
    return result.model_dump()


@router.get("/projects/{project_id}/generated-scripts")
def list_scripts(project_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.codegen.generator import list_generated_scripts

    return {"project_id": project_id, "scripts": list_generated_scripts(project_id)}


@router.get("/projects/{project_id}/generated-scripts/{script_id}")
def get_script(project_id: str, script_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.codegen.generator import get_generated_script

    data = get_generated_script(project_id, script_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
    return data


@router.delete("/projects/{project_id}/generated-scripts/{script_id}")
def delete_script(project_id: str, script_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.codegen.generator import delete_generated_script

    if not delete_generated_script(project_id, script_id):
        raise HTTPException(status_code=404, detail=f"Script not found: {script_id}")
    return {"project_id": project_id, "script_id": script_id, "deleted": True}


class StartRunRequest(BaseModel):
    script_id: str
    backend: str = "local"
    mode: str = "web"
    test_id: str = ""
    timeout_seconds: int = 300
    allow_fallback_backend: bool = False
    env_overrides: dict[str, str] | None = None


@router.post("/projects/{project_id}/runs")
def start_project_run(project_id: str, body: StartRunRequest) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.errors import ExecutionError
    from app.services.agentic.execution.runner import start_run
    from app.services.agentic.execution.schemas import ExecutionBackend, ExecutionRequest

    try:
        backend = ExecutionBackend(body.backend)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid backend: {body.backend}") from None

    request = ExecutionRequest(
        project_id=project_id,
        script_id=body.script_id,
        backend=backend,
        mode=body.mode,
        test_id=body.test_id,
        timeout_seconds=body.timeout_seconds,
        allow_fallback_backend=body.allow_fallback_backend,
        env_overrides=body.env_overrides or {},
    )
    try:
        run = start_run(request)
        return run.model_dump(mode="json")
    except ExecutionError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_failure().model_dump()) from exc


@router.get("/projects/{project_id}/runs")
def list_project_runs(project_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.run_store import list_runs

    runs = list_runs(project_id)
    return {"project_id": project_id, "runs": [r.model_dump(mode="json") for r in runs]}


@router.get("/projects/{project_id}/runs/{run_id}")
def get_project_run(project_id: str, run_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.errors import ExecutionError, RunNotFoundError
    from app.services.agentic.execution.process_manager import get_run_status

    try:
        return get_run_status(project_id, run_id).model_dump(mode="json")
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.to_failure().model_dump()) from exc
    except ExecutionError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_failure().model_dump()) from exc


@router.post("/projects/{project_id}/runs/{run_id}/cancel")
def cancel_project_run(project_id: str, run_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.errors import RunNotFoundError
    from app.services.agentic.execution.process_manager import cancel_run

    try:
        return cancel_run(project_id, run_id).model_dump(mode="json")
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.to_failure().model_dump()) from exc


@router.get("/projects/{project_id}/runs/{run_id}/logs")
def get_project_run_logs(project_id: str, run_id: str, tail: int = Query(200, ge=0, le=10000)) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.errors import RunNotFoundError
    from app.services.agentic.execution.process_manager import get_run_logs

    try:
        return get_run_logs(project_id, run_id, tail=tail)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.to_failure().model_dump()) from exc


@router.get("/projects/{project_id}/runs/{run_id}/events")
def stream_project_run_events(project_id: str, run_id: str):
    _ensure_project(project_id)
    import json
    import time

    from app.services.agentic.execution.log_stream import get_events
    from app.services.agentic.execution.process_manager import get_run_status

    def event_generator():
        idx = 0
        for _ in range(600):
            get_run_status(project_id, run_id)
            events = get_events(run_id, idx)
            for evt in events:
                idx += 1
                yield f"data: {json.dumps(evt.model_dump())}\n\n"
            run = get_run_status(project_id, run_id)
            if run.status.value in ("completed", "failed", "cancelled", "timed_out"):
                yield f"data: {json.dumps({'run_id': run_id, 'done': True, 'status': run.status.value})}\n\n"
                break
            time.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/projects/{project_id}/runs/{run_id}/manifest")
def get_project_run_manifest(project_id: str, run_id: str, partial: bool = Query(False)) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.artifact_store import read_manifest

    try:
        return read_manifest(project_id, run_id, allow_partial=partial)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/runs/{run_id}/replay")
def get_project_run_replay(project_id: str, run_id: str, partial: bool = Query(False)) -> JSONResponse:
    _ensure_project(project_id)
    from app.services.agentic.execution.artifact_store import read_replay

    try:
        data = read_replay(project_id, run_id, allow_partial=partial)
        return JSONResponse(content=data)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/runs/{run_id}/telemetry")
def get_project_run_telemetry(project_id: str, run_id: str, partial: bool = Query(False)) -> JSONResponse:
    _ensure_project(project_id)
    from app.services.agentic.execution.artifact_store import read_telemetry

    try:
        data = read_telemetry(project_id, run_id, allow_partial=partial)
        return JSONResponse(content=data)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/runs/{run_id}/artifacts")
def get_project_run_artifacts(project_id: str, run_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.artifact_store import list_artifacts

    return {
        "project_id": project_id,
        "run_id": run_id,
        "artifacts": [a.model_dump() for a in list_artifacts(project_id, run_id)],
    }


class ReportGenerateRequest(BaseModel):
    use_llm: bool = False
    audience: str = "beginner"
    include_limitations: bool = True
    force: bool = False


@router.post("/projects/{project_id}/runs/{run_id}/report")
def post_project_run_report(project_id: str, run_id: str, body: ReportGenerateRequest | None = None) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.reporting.report_generator import generate_engineering_report
    from app.services.agentic.reporting.schemas import ReportGenerateOptions

    opts = ReportGenerateOptions(**(body.model_dump() if body else {}))
    result = generate_engineering_report(project_id, run_id, opts)
    return result.model_dump(mode="json")


@router.post("/projects/{project_id}/runs/{run_id}/report/regenerate")
def regenerate_project_run_report(project_id: str, run_id: str, body: ReportGenerateRequest | None = None) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.reporting.report_generator import generate_engineering_report
    from app.services.agentic.reporting.schemas import ReportGenerateOptions

    data = body.model_dump() if body else {}
    data["force"] = True
    result = generate_engineering_report(project_id, run_id, ReportGenerateOptions(**data))
    return result.model_dump(mode="json")


@router.get("/projects/{project_id}/runs/{run_id}/report")
def get_project_run_report(project_id: str, run_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.reporting.report_writer import read_report

    report = read_report(project_id, run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated for this run")
    return report.model_dump(mode="json")


@router.get("/projects/{project_id}/runs/{run_id}/report.md")
def get_project_run_report_md(project_id: str, run_id: str) -> PlainTextResponse:
    _ensure_project(project_id)
    from app.services.agentic.reporting.report_writer import read_report_markdown

    md = read_report_markdown(project_id, run_id)
    if not md:
        raise HTTPException(status_code=404, detail="Report markdown not found")
    return PlainTextResponse(content=md, media_type="text/markdown")


@router.get("/projects/{project_id}/runs/{run_id}/summary")
def get_project_run_summary(project_id: str, run_id: str) -> dict:
    _ensure_project(project_id)
    from app.services.agentic.execution.run_store import load_run
    from app.services.agentic.reporting.report_writer import read_report

    run = load_run(project_id, run_id)
    report = read_report(project_id, run_id)
    return {
        "project_id": project_id,
        "run_id": run_id,
        "run_status": run.status.value if run else "unknown",
        "test_id": run.test_id if run else "",
        "outcome": report.outcome.model_dump() if report else None,
        "executive_summary": report.executive_summary if report else "",
        "pass_fail": report.pass_fail if report else "inconclusive",
        "report_id": report.report_id if report else None,
    }
