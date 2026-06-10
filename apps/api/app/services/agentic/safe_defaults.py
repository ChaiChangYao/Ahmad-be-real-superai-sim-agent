"""Generate safe defaults for tests — no unsafe mesh fabrication."""
from __future__ import annotations

from typing import Any

from app.services.agentic.project_state import load_agentic_state, save_agentic_state, AgenticProjectState
from app.services.agentic.test_requirements import evaluate_test_readiness, get_test_spec
from app.services.agentic.urdf_inspector import inspect_all_robot_descriptions


def generate_safe_defaults(
    project_id: str,
    test_id: str,
    selected_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = get_test_spec(test_id)
    if spec is None:
        return {"success": False, "error": f"Unknown test: {test_id}"}

    readiness = evaluate_test_readiness(project_id, test_id)
    options = dict(selected_options or {})
    defaults: dict[str, Any] = {}

    robot_descs = inspect_all_robot_descriptions(project_id)
    root_link = ""
    for desc in robot_descs:
        if desc.parsed and desc.root_link:
            root_link = desc.root_link
            break
    if not root_link and robot_descs and robot_descs[0].link_names:
        root_link = robot_descs[0].link_names[0]

    if test_id == "imu_sensor":
        defaults["attach_link"] = options.get("attach_link") or root_link or "base_link"
        defaults["sample_rate_hz"] = float(options.get("sample_rate_hz") or 100.0)
        defaults["sensor_pose"] = options.get("sensor_pose") or {"position": [0, 0, 0], "orientation": [0, 0, 0, 1]}
    elif test_id == "gravity_stability":
        defaults["collision_mode"] = options.get("collision_mode") or "bounding_box_fallback"
        defaults["default_density_kg_m3"] = float(options.get("density") or 1000.0)
        defaults["friction"] = float(options.get("friction") or 0.5)
    elif test_id == "joint_sweep":
        defaults["sweep_mode"] = options.get("sweep_mode") or "default_joint_sweep"
        defaults["use_skeleton"] = bool(options.get("use_skeleton") or readiness.fallback_modes)
    elif test_id == "depth_camera":
        defaults["resolution"] = options.get("resolution") or [640, 480]
        defaults["camera_pose"] = options.get("camera_pose") or "look_at_model_center"
    elif test_id == "contact_force":
        defaults["contact_links"] = options.get("contact_links") or "all_collision_links"
    elif test_id == "thermal_grid_readiness":
        defaults["grid_bounds"] = options.get("grid_bounds") or "model_bounding_box"
        defaults["heat_source"] = options.get("heat_source") or "demo_point_source"
    else:
        defaults = {k: v for k, v in options.items()}

    state = load_agentic_state(project_id) or AgenticProjectState(project_id=project_id)
    state.generated_defaults = {**state.generated_defaults, test_id: defaults}
    state.selected_test = test_id
    if options.get("fallback_mode"):
        state.selected_fallback_mode = str(options["fallback_mode"])
    save_agentic_state(state)

    return {
        "success": True,
        "test_id": test_id,
        "defaults": defaults,
        "readiness": readiness.model_dump(),
        "message": f"Safe defaults configured for {test_id}.",
    }
