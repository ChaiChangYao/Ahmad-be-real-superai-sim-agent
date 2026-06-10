"""Maps test_id + fallback_mode to Jinja templates."""
from __future__ import annotations

from pathlib import Path

from app.services.agentic.codegen.schemas import GenesisTemplateSpec
from app.services.agentic.errors import TestRequirementNotMetError

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

READINESS_ONLY_TESTS = {"fea_readiness", "cfd_readiness"}

TEMPLATE_REGISTRY: list[GenesisTemplateSpec] = [
    GenesisTemplateSpec(
        template_id="gravity_stability",
        display_name="Gravity Stability",
        test_id="gravity_stability",
        category="rigid",
        template_path="gravity_stability.py.j2",
        required_context_fields=["project_root", "output_root"],
        outputs=["replay", "stability_result"],
        supports_robot=True,
        supports_rigid_mesh=True,
        notes="Passive gravity settle test.",
    ),
    GenesisTemplateSpec(
        template_id="joint_sweep",
        display_name="Joint Sweep",
        test_id="joint_sweep",
        category="robot_motion",
        template_path="joint_sweep.py.j2",
        required_context_fields=["project_root", "robot_description_path", "selected_joints"],
        outputs=["replay", "joint_range_telemetry"],
        supports_robot=True,
        supports_telemetry=True,
        notes="Sweep movable joints through limits.",
    ),
    GenesisTemplateSpec(
        template_id="skeleton_preview",
        display_name="Skeleton Preview",
        test_id="joint_sweep",
        category="robot_motion",
        template_path="skeleton_preview.py.j2",
        required_context_fields=["project_root", "robot_description_path"],
        outputs=["replay", "joint_range_telemetry"],
        supports_robot=True,
        supports_telemetry=True,
        notes="Skeleton fallback when meshes missing.",
    ),
    GenesisTemplateSpec(
        template_id="imu_sensor",
        display_name="IMU Sensor",
        test_id="imu_sensor",
        category="sensor",
        template_path="imu_sensor.py.j2",
        required_context_fields=["project_root", "robot_description_path", "sensor_config"],
        outputs=["replay", "telemetry_timeseries"],
        supports_robot=True,
        supports_sensors=True,
        supports_telemetry=True,
    ),
    GenesisTemplateSpec(
        template_id="contact_force",
        display_name="Contact Force",
        test_id="contact_force",
        category="sensor",
        template_path="contact_force.py.j2",
        required_context_fields=["project_root"],
        outputs=["replay", "contact_force_charts"],
        supports_robot=True,
        supports_sensors=True,
        supports_telemetry=True,
    ),
    GenesisTemplateSpec(
        template_id="depth_camera",
        display_name="Depth Camera",
        test_id="depth_camera",
        category="sensor",
        template_path="depth_camera.py.j2",
        required_context_fields=["project_root"],
        outputs=["replay", "depth_frames"],
        supports_robot=True,
        supports_rigid_mesh=True,
        supports_sensors=True,
        supports_telemetry=True,
    ),
    GenesisTemplateSpec(
        template_id="temperature_grid",
        display_name="Temperature Grid",
        test_id="thermal_grid_readiness",
        category="thermal",
        template_path="temperature_grid.py.j2",
        required_context_fields=["project_root"],
        outputs=["heatmap_telemetry"],
        supports_robot=True,
        supports_rigid_mesh=True,
        supports_sensors=True,
        supports_telemetry=True,
        notes="Demo/readiness thermal field — not validated engineering thermal simulation.",
    ),
    GenesisTemplateSpec(
        template_id="static_mesh_preview",
        display_name="Static Mesh Preview",
        test_id="static_mesh_preview",
        category="rigid",
        template_path="static_mesh_preview.py.j2",
        required_context_fields=["project_root", "mesh_assets"],
        outputs=["replay", "readiness_report"],
        supports_robot=False,
        supports_rigid_mesh=True,
        notes="STEP/mesh only — no robot joints.",
    ),
    GenesisTemplateSpec(
        template_id="skeleton_gravity",
        display_name="Skeleton Gravity Preview",
        test_id="gravity_stability",
        category="rigid",
        template_path="skeleton_preview.py.j2",
        required_context_fields=["project_root", "robot_description_path"],
        outputs=["replay"],
        supports_robot=True,
        notes="Gravity with skeleton fallback.",
    ),
]


def resolve_template(test_id: str, fallback_mode: str | None = None) -> GenesisTemplateSpec:
    if test_id in READINESS_ONLY_TESTS:
        raise TestRequirementNotMetError(
            f"{test_id} is a readiness check only — Genesis physics script generation is not supported.",
            suggested_actions=["Run readiness report from preflight plan.", "Provide required FEA/CFD metadata."],
        )

    if test_id == "static_mesh_preview" or fallback_mode == "static_mesh":
        return _by_id("static_mesh_preview")

    if fallback_mode == "skeleton":
        if test_id == "joint_sweep":
            return _by_id("skeleton_preview")
        if test_id == "gravity_stability":
            return _by_id("skeleton_gravity")

    for spec in TEMPLATE_REGISTRY:
        if spec.test_id == test_id and spec.template_id not in {"skeleton_preview", "skeleton_gravity", "static_mesh_preview"}:
            if fallback_mode is None or fallback_mode not in {"skeleton", "static_mesh"}:
                return spec

    raise TestRequirementNotMetError(
        f"No template registered for test_id={test_id} fallback_mode={fallback_mode}",
        suggested_actions=["Choose a supported test from the preflight plan.", "Select a valid fallback mode."],
    )


def _by_id(template_id: str) -> GenesisTemplateSpec:
    for spec in TEMPLATE_REGISTRY:
        if spec.template_id == template_id:
            return spec
    raise TestRequirementNotMetError(f"Template not found: {template_id}")


def template_file_path(spec: GenesisTemplateSpec) -> Path:
    return TEMPLATES_DIR / spec.template_path


def list_templates() -> list[GenesisTemplateSpec]:
    return list(TEMPLATE_REGISTRY)
