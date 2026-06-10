"""Data-driven test requirement matrix — no hardcoded robot assumptions."""
from __future__ import annotations

from app.services.agentic.file_inventory import find_assets_by_role
from app.services.agentic.mesh_inspector import inspect_project_meshes
from app.services.agentic.schemas import SimulationTestSpec, TestReadinessResult
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions

TEST_REQUIREMENTS: list[SimulationTestSpec] = [
    SimulationTestSpec(
        test_id="gravity_stability",
        display_name="Gravity Stability",
        category="rigid",
        description="Drop or settle model under gravity; report stability and contact summary.",
        required_inputs=["geometry_or_robot_description", "collision_geometry"],
        optional_inputs=["mass_inertial_data", "friction", "restitution"],
        generatable_inputs=["default_density", "default_friction", "bounding_box_collision_fallback"],
        outputs=["replay", "contact_collision_summary", "stability_result"],
        viewer_layout="simulation_only",
        genesis_template="gravity_stability",
        supported_asset_types=["urdf", "mjcf", "stl", "obj", "glb", "step"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="joint_sweep",
        display_name="Joint Sweep",
        category="robot_motion",
        description="Sweep movable joints through limits; detect collisions and range issues.",
        required_inputs=["urdf_or_mjcf", "movable_joints", "joint_limits"],
        optional_inputs=["actuator_metadata", "control_script"],
        generatable_inputs=["default_joint_sweep_motion", "joint_limits"],
        outputs=["replay", "joint_range_telemetry", "collision_warnings"],
        viewer_layout="simulation_plus_telemetry",
        genesis_template="joint_sweep",
        supported_asset_types=["urdf", "mjcf"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="imu_sensor",
        display_name="IMU Sensor",
        category="sensor",
        description="Simulate IMU on attach link; record linear acceleration and angular velocity.",
        required_inputs=["robot_description", "attach_link", "sample_rate"],
        optional_inputs=["sensor_pose", "noise_model"],
        generatable_inputs=["default_attach_link", "identity_pose", "default_sample_rate"],
        outputs=["replay", "lin_acc", "ang_vel", "true_lin_acc", "true_ang_vel"],
        viewer_layout="simulation_plus_telemetry",
        telemetry_schema={"type": "imu", "channels": ["lin_acc", "ang_vel"]},
        genesis_template="imu_sensor",
        supported_asset_types=["urdf", "mjcf"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="contact_force",
        display_name="Contact Force",
        category="sensor",
        description="Record contact forces on collision-enabled bodies.",
        required_inputs=["collision_geometry", "contact_enabled_bodies"],
        optional_inputs=["selected_links"],
        generatable_inputs=["default_contact_links"],
        outputs=["replay", "contact_force_charts"],
        viewer_layout="simulation_plus_telemetry",
        telemetry_schema={"type": "contact_force"},
        genesis_template="contact_force",
        supported_asset_types=["urdf", "mjcf", "stl", "obj"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="depth_camera",
        display_name="Depth Camera",
        category="sensor",
        description="Render RGB and depth frames from a camera pose toward scene geometry.",
        required_inputs=["scene_geometry", "camera_pose"],
        optional_inputs=["resolution", "fov"],
        generatable_inputs=["default_camera_pose", "default_resolution"],
        outputs=["replay", "rgb_frames", "depth_frames"],
        viewer_layout="simulation_plus_telemetry",
        telemetry_schema={"type": "depth_camera"},
        genesis_template="depth_camera",
        supported_asset_types=["urdf", "mjcf", "stl", "obj", "glb"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="thermal_grid_readiness",
        display_name="Thermal Grid Readiness",
        category="thermal",
        description="Check readiness for thermal grid simulation with heat source and bounds.",
        required_inputs=["geometry", "grid_bounds", "heat_source"],
        optional_inputs=["material_thermal_properties"],
        generatable_inputs=["bounding_box_grid", "demo_heat_source"],
        cannot_fake_inputs=["real_material_thermal_conductivity"],
        outputs=["heatmap_telemetry"],
        viewer_layout="simulation_plus_telemetry",
        genesis_template="thermal_grid",
        supported_asset_types=["stl", "obj", "glb", "urdf"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="static_mesh_preview",
        display_name="Static Mesh Preview",
        category="rigid",
        description="Preview STEP/STL/OBJ/GLB when no robot description exists.",
        required_inputs=["geometry"],
        optional_inputs=["camera_pose"],
        generatable_inputs=["default_camera_pose"],
        outputs=["replay", "readiness_report"],
        viewer_layout="simulation_only",
        genesis_template="static_mesh_preview",
        supported_asset_types=["stl", "obj", "glb", "step"],
        status="available",
    ),
    SimulationTestSpec(
        test_id="fea_readiness",
        display_name="FEA Readiness",
        category="fea_readiness",
        description="Readiness check for FEA — does not run a full FEA solver in Genesis.",
        required_inputs=["watertight_geometry", "material", "constraints", "loads"],
        cannot_fake_inputs=["meaningful_material", "real_boundary_conditions"],
        outputs=["readiness_report"],
        viewer_layout="report_only",
        genesis_template="",
        supported_asset_types=["stl", "obj", "step"],
        status="readiness_only",
    ),
    SimulationTestSpec(
        test_id="cfd_readiness",
        display_name="CFD Readiness",
        category="cfd_readiness",
        description="Readiness check for CFD — does not run a full CFD solver in Genesis.",
        required_inputs=["fluid_domain", "inlet_outlet", "boundary_conditions", "watertight_geometry"],
        cannot_fake_inputs=["meaningful_cfd_boundary_conditions"],
        outputs=["readiness_report"],
        viewer_layout="report_only",
        genesis_template="",
        supported_asset_types=["stl", "obj", "step"],
        status="readiness_only",
    ),
]


def get_all_test_specs() -> list[SimulationTestSpec]:
    return list(TEST_REQUIREMENTS)


def get_test_spec(test_id: str) -> SimulationTestSpec | None:
    for spec in TEST_REQUIREMENTS:
        if spec.test_id == test_id:
            return spec
    return None


def _project_context(project_id: str) -> dict:
    from app.services.agentic.file_inventory import scan_project_assets

    assets = scan_project_assets(project_id, persist=False)
    robot_descs = inspect_all_robot_descriptions(project_id)
    mesh_inspections = inspect_project_meshes(project_id)

    has_robot = any(r.parsed for r in robot_descs)
    has_movable = any(r.movable_joints_count > 0 for r in robot_descs)
    has_limits = any(r.has_joint_limits for r in robot_descs)
    has_collision = any(r.has_collision_geometry for r in robot_descs)
    has_visual = any(r.has_visual_geometry for r in robot_descs)
    missing_meshes = sum(1 for r in robot_descs for m in r.mesh_references if m.status == "missing")
    total_mesh_refs = sum(len(r.mesh_references) for r in robot_descs)
    link_names = robot_descs[0].link_names if robot_descs and robot_descs[0].parsed else []
    root_link = robot_descs[0].root_link if robot_descs and robot_descs[0].parsed else (link_names[0] if link_names else "base_link")
    has_sensors_in_urdf = any(len(r.detected_sensors) > 0 for r in robot_descs)
    has_imu_hardware = any(
        any(str(s.get("type", "")).startswith("imu") for s in r.detected_sensors)
        for r in robot_descs
    )

    mesh_assets = find_assets_by_role(assets, "mesh")
    cad_assets = find_assets_by_role(assets, "cad")
    has_geometry = bool(mesh_assets) or has_robot or bool(cad_assets)
    watertight_count = sum(1 for m in mesh_inspections if m.watertight is True)
    parsed_mesh_count = sum(1 for m in mesh_inspections if m.parsed)

    return {
        "assets": assets,
        "robot_descs": robot_descs,
        "mesh_inspections": mesh_inspections,
        "has_robot": has_robot,
        "has_movable": has_movable,
        "has_limits": has_limits,
        "has_collision": has_collision,
        "has_visual": has_visual,
        "missing_meshes": missing_meshes,
        "total_mesh_refs": total_mesh_refs,
        "link_names": link_names,
        "root_link": root_link,
        "has_sensors_in_urdf": has_sensors_in_urdf,
        "has_imu_hardware": has_imu_hardware,
        "has_geometry": has_geometry,
        "watertight_count": watertight_count,
        "parsed_mesh_count": parsed_mesh_count,
        "mesh_asset_count": len(mesh_assets),
        "cad_asset_count": len(cad_assets),
    }


def evaluate_test_readiness(project_id: str, test_id: str) -> TestReadinessResult:
    spec = get_test_spec(test_id)
    if spec is None:
        return TestReadinessResult(
            test_id=test_id,
            blockers=[f"Unknown test: {test_id}"],
        )

    ctx = _project_context(project_id)
    missing_required: list[str] = []
    missing_optional: list[str] = []
    generatable: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    actions: list[str] = []
    questions: list[str] = []
    fallbacks: list[str] = []

    if test_id == "gravity_stability":
        if not ctx["has_geometry"]:
            missing_required.append("geometry_or_robot_description")
            blockers.append("No geometry or robot description uploaded.")
        if not ctx["has_collision"] and ctx["missing_meshes"] > 0:
            missing_required.append("collision_geometry")
            blockers.append(f"{ctx['missing_meshes']} collision/visual meshes missing.")
            generatable.append("bounding_box_collision_fallback")
            fallbacks.append("skeleton_preview")
        elif not ctx["has_collision"]:
            generatable.append("bounding_box_collision_fallback")
        if not any(r.has_inertial_data for r in ctx["robot_descs"]):
            generatable.append("default_density")

    elif test_id == "joint_sweep":
        if not ctx["has_robot"]:
            missing_required.append("urdf_or_mjcf")
            blockers.append("No URDF/MJCF robot description found.")
        if not ctx["has_movable"]:
            missing_required.append("movable_joints")
            blockers.append("Robot has no movable joints.")
        if not ctx["has_limits"]:
            missing_required.append("joint_limits")
            generatable.append("default_joint_sweep_motion")
            warnings.append("Joint limits missing — sweep may use conservative defaults.")
        if ctx["missing_meshes"] > 0:
            warnings.append(f"{ctx['missing_meshes']} meshes missing — skeleton joint sweep may still run.")
            fallbacks.append("skeleton_joint_sweep")

    elif test_id == "imu_sensor":
        if not ctx["has_robot"]:
            missing_required.append("robot_description")
            blockers.append("No robot description for IMU attachment.")
        else:
            generatable.extend(["default_attach_link", "default_sample_rate", "identity_pose"])
            default_link = ctx["root_link"]
            if ctx.get("has_imu_hardware"):
                questions.append(
                    f"IMU hardware mesh detected — attach simulated IMU to base_link or internal_electronics_link? Default: {default_link}",
                )
            else:
                questions.append(f"Which link should IMU attach to? Default: {default_link}")
                warnings.append(
                    "No IMU sensor block in URDF — simulation will attach a virtual IMU only; "
                    "no physical sensor geometry will appear in the viewer.",
                )

    elif test_id == "contact_force":
        if not ctx["has_collision"]:
            missing_required.append("collision_geometry")
            blockers.append("No collision geometry found.")
        else:
            generatable.append("default_contact_links")
        if ctx["missing_meshes"] > 0:
            warnings.append("Some mesh references missing — contact detection may be incomplete.")

    elif test_id == "depth_camera":
        if not ctx["has_geometry"]:
            missing_required.append("scene_geometry")
            blockers.append("No scene geometry for depth camera.")
        else:
            generatable.extend(["default_camera_pose", "default_resolution"])

    elif test_id == "static_mesh_preview":
        if not ctx["has_geometry"]:
            missing_required.append("geometry")
            blockers.append("No mesh or CAD geometry for static preview.")
        if ctx["has_robot"] and ctx["has_movable"]:
            warnings.append("URDF/MJCF detected — robot motion tests are available; static preview is mesh-only.")

    elif test_id == "thermal_grid_readiness":
        if not ctx["has_geometry"]:
            missing_required.append("geometry")
            blockers.append("No geometry for thermal grid.")
        generatable.extend(["bounding_box_grid", "demo_heat_source"])
        missing_optional.append("material_thermal_properties")
        warnings.append("Real material thermal conductivity cannot be faked without user input.")

    elif test_id == "fea_readiness":
        blockers.append("FEA readiness only — Genesis does not run a full FEA solver in MVP.")
        if ctx["watertight_count"] == 0 and ctx["parsed_mesh_count"] > 0:
            missing_required.append("watertight_geometry")
            blockers.append("No watertight solid geometry detected.")
        elif ctx["parsed_mesh_count"] == 0 and not ctx["has_geometry"]:
            missing_required.append("watertight_geometry")
            blockers.append("No solid geometry uploaded.")
        for req in ("material", "constraints", "loads"):
            missing_required.append(req)
            blockers.append(f"Missing {req} — cannot fake meaningful FEA inputs.")

    elif test_id == "cfd_readiness":
        blockers.append("CFD readiness only — Genesis does not run a full CFD solver in MVP.")
        if ctx["watertight_count"] == 0:
            missing_required.append("watertight_geometry")
        for req in ("fluid_domain", "inlet_outlet", "boundary_conditions"):
            missing_required.append(req)
            blockers.append(f"Missing {req} — cannot fake meaningful CFD boundary conditions.")

    non_generatable_missing = [r for r in missing_required if r not in spec.generatable_inputs]
    can_run = len(non_generatable_missing) == 0 and spec.status == "available"
    can_fallback = (
        not can_run
        and len(non_generatable_missing) == 0
        and bool(fallbacks or generatable)
        and spec.status == "available"
    )

    if missing_required:
        actions.append("Upload missing files listed in inspection report.")
    if ctx["missing_meshes"] > 0:
        actions.append("Upload missing mesh files or use STEP recovery if available.")
    if generatable:
        actions.append("Safe defaults can be generated for: " + ", ".join(generatable))

    confidence = 1.0 if can_run else (0.6 if can_fallback else 0.2)
    if spec.status == "readiness_only":
        can_run = False
        confidence = 0.3 if missing_required else 0.5

    return TestReadinessResult(
        test_id=test_id,
        can_run=can_run,
        can_run_with_fallback=can_fallback and spec.status == "available",
        confidence=confidence,
        missing_required=missing_required,
        missing_optional=missing_optional,
        generated_defaults_available=generatable,
        blockers=blockers,
        warnings=warnings,
        suggested_actions=actions,
        required_user_questions=questions,
        fallback_modes=fallbacks,
    )


def evaluate_all_tests(project_id: str) -> list[TestReadinessResult]:
    return [evaluate_test_readiness(project_id, spec.test_id) for spec in TEST_REQUIREMENTS]
