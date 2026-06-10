"""Build typed GenesisScriptContext from project inspection."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.services.agentic.codegen.schemas import (
    GenesisScriptContext,
    PhysicsConfig,
    ReplayConfig,
    SensorConfig,
)
from app.services.agentic.codegen.template_registry import resolve_template
from app.services.agentic.errors import TestRequirementNotMetError
from app.services.agentic.file_inventory import find_assets_by_role, scan_project_assets
from app.services.agentic.project_state import load_agentic_state
from app.services.agentic.runtime.scene_helpers import fit_initial_camera_metadata
from app.services.agentic.runtime.sensor_helpers import choose_default_attach_link, configure_contact_force
from app.services.agentic.test_requirements import evaluate_test_readiness
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions
from app.services.cad_import.urdf_generator import generate_urdf
from app.services.genesis.imported_robot_loader import resolve_robot_description_candidates
from app.services.project_store import load_manifest, project_dir


def build_script_context(
    project_id: str,
    test_id: str,
    user_parameters: dict | None = None,
    fallback_mode: str | None = None,
    script_id: str | None = None,
) -> GenesisScriptContext:
    params = dict(user_parameters or {})
    readiness = evaluate_test_readiness(project_id, test_id)
    spec = resolve_template(test_id, fallback_mode)

    if test_id == "static_mesh_preview":
        fallback_mode = fallback_mode or "static_mesh"

    can_generate = readiness.can_run or readiness.can_run_with_fallback
    if not can_generate and test_id != "static_mesh_preview":
        raise TestRequirementNotMetError(
            readiness.blockers[0] if readiness.blockers else f"Test {test_id} is blocked.",
            suggested_actions=readiness.suggested_actions,
        )

    if fallback_mode == "skeleton" and not readiness.can_run:
        if not readiness.fallback_modes and test_id not in {"joint_sweep", "gravity_stability", "imu_sensor"}:
            raise TestRequirementNotMetError(
                "Skeleton fallback is not valid for this test.",
                suggested_actions=["Upload meshes or choose a different test."],
            )
    elif not readiness.can_run and fallback_mode not in {"skeleton", "static_mesh"}:
        if readiness.can_run_with_fallback and not fallback_mode:
            raise TestRequirementNotMetError(
                "Test requires a fallback mode (e.g. skeleton).",
                suggested_actions=["Set fallback_mode to 'skeleton' or upload missing assets."] + readiness.suggested_actions,
            )
        elif not readiness.can_run_with_fallback:
            raise TestRequirementNotMetError(
                readiness.blockers[0] if readiness.blockers else "Requirements not met.",
                suggested_actions=readiness.suggested_actions,
            )

    pdir = project_dir(project_id)
    assets = scan_project_assets(project_id, persist=False)
    robot_descs = inspect_all_robot_descriptions(project_id)
    robot = next((r for r in robot_descs if r.parsed), None)

    sid = script_id or f"script-{uuid4().hex[:10]}"
    out_root = pdir / "generated" / "runs" / sid
    out_root.mkdir(parents=True, exist_ok=True)

    mesh_assets = [
        {"id": a.id, "path": a.stored_path, "relative": a.relative_path}
        for a in find_assets_by_role(assets, "mesh")
    ]

    desc_path = ""
    desc_type = ""
    selected_joints: list[str] = []
    joint_limits: dict[str, dict[str, float]] = {}
    link_names: list[str] = []
    warnings: list[str] = []
    missing_mesh_count = sum(1 for r in robot_descs for m in r.mesh_references if m.status == "missing")

    if robot and robot.parsed:
        link_names = robot.link_names
        candidates = resolve_robot_description_candidates(load_manifest(project_id), pdir)
        if candidates:
            desc_type, desc_path_obj = candidates[0]
            desc_path = str(desc_path_obj)

        if fallback_mode == "skeleton":
            fallback_urdf = pdir / "generated" / "robot_description" / "genesis_physics.urdf"
            fallback_urdf.parent.mkdir(parents=True, exist_ok=True)
            generate_urdf(load_manifest(project_id), fallback_urdf)
            desc_path = str(fallback_urdf)
            desc_type = "urdf"
            warnings.append(
                f"Skeleton fallback preview. {missing_mesh_count} mesh file(s) missing — not full visual simulation.",
            )

        for jname in robot.joint_names:
            if jname in params.get("selected_joints", []):
                selected_joints.append(jname)
        if not selected_joints:
            selected_joints = [
                j for j in robot.joint_names
            ][: min(12, len(robot.joint_names))]

    elif test_id == "static_mesh_preview" or fallback_mode == "static_mesh":
        if not mesh_assets:
            step_assets = find_assets_by_role(assets, "cad")
            preview = pdir / "generated" / "step_preview" / "whole_assembly.stl"
            if preview.is_file():
                mesh_assets = [{"id": "step_preview", "path": str(preview), "relative": "generated/step_preview/whole_assembly.stl"}]
            elif not step_assets:
                raise TestRequirementNotMetError(
                    "No mesh or STEP geometry for static preview.",
                    suggested_actions=["Upload STL/OBJ/GLB or run STEP preview recovery first."],
                )
        warnings.append("Static mesh preview — robot motion requires URDF/MJCF.")
    else:
        raise TestRequirementNotMetError(
            "Robot description required for this test.",
            suggested_actions=["Upload URDF/MJCF or use static_mesh_preview for mesh-only projects."],
        )

    state = load_agentic_state(project_id)
    defaults = (state.generated_defaults.get(test_id) if state else None) or {}

    sensor = SensorConfig()
    if test_id == "imu_sensor":
        attach = params.get("attach_link") or defaults.get("attach_link") or choose_default_attach_link(link_names, robot.root_link if robot else "")
        sensor = SensorConfig(
            sensor_type="imu",
            attach_link=str(attach),
            sample_rate=float(params.get("sample_rate_hz") or defaults.get("sample_rate_hz") or 100.0),
            pose=dict(params.get("sensor_pose") or defaults.get("sensor_pose") or {}),
            defaults_used=["attach_link", "sample_rate"] if not params.get("attach_link") else [],
        )
    elif test_id == "contact_force":
        sensor = SensorConfig(
            sensor_type="contact_force",
            contact_links=configure_contact_force(link_names, params.get("contact_links")),
        )
    elif test_id == "depth_camera":
        sensor = SensorConfig(
            sensor_type="depth_camera",
            resolution=list(params.get("resolution") or [640, 480]),
            fov=float(params.get("fov") or 60.0),
        )
    elif test_id == "thermal_grid_readiness":
        sensor = SensorConfig(
            sensor_type="temperature_grid",
            grid_resolution=int(params.get("grid_resolution") or 16),
            heat_source=dict(params.get("heat_source") or {"type": "demo_point"}),
        )

    physics = PhysicsConfig(
        duration_seconds=float(params.get("duration_seconds") or 4.0),
        timestep=float(params.get("timestep") or 0.01),
        collision_mode=str(params.get("collision_mode") or defaults.get("collision_mode") or "default"),
        friction=float(params.get("friction") or 0.5),
    )

    record_telemetry = test_id in {
        "imu_sensor",
        "contact_force",
        "depth_camera",
        "thermal_grid_readiness",
        "joint_sweep",
    }

    replay = ReplayConfig(
        record_visual=True,
        record_telemetry=record_telemetry,
        output_state_timeseries_path=str(out_root / "state_timeseries.json"),
        output_telemetry_timeseries_path=str(out_root / "telemetry_timeseries.json"),
        target_fps=float(params.get("target_fps") or 24.0),
    )

    render_config = fit_initial_camera_metadata({}) if test_id == "depth_camera" else {}

    ctx = GenesisScriptContext(
        project_id=project_id,
        test_id=test_id,
        template_id=spec.template_id,
        script_id=sid,
        project_root=str(pdir.resolve()),
        asset_root=str((pdir / "assets" / "imported").resolve()),
        output_root=str(out_root.resolve()),
        robot_description_path=desc_path,
        robot_description_type=desc_type,
        mesh_assets=mesh_assets,
        selected_links=link_names,
        selected_joints=selected_joints,
        joint_limits=joint_limits,
        fallback_mode=fallback_mode,
        sensor_config=sensor,
        physics_config=physics,
        replay_config=replay,
        render_config=render_config,
        generated_defaults=defaults,
        user_parameters=params,
        safety_flags={"web_mode": True, "no_native_viewer": True},
        warnings=warnings + readiness.warnings,
        link_names=link_names,
        missing_mesh_count=missing_mesh_count,
    )
    return ctx
