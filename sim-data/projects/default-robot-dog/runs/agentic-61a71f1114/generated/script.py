"""Static mesh preview — no robot joints. Robot motion requires URDF/MJCF."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.agentic.runtime.recorder import (
    fail_run,
    finalize_run,
    start_run_metadata,
    write_manifest,
    write_state_timeseries,
    write_telemetry_timeseries,
)
from app.services.agentic.runtime.scene_helpers import (
    add_floor,
    add_robot_from_urdf_or_mjcf,
    create_basic_scene,
    init_genesis_web_mode,
    step_scene_for_duration,
)


def load_sidecar_config() -> dict:
    script_path = Path(__file__).resolve()
    ctx_path = script_path.parent / f"{script_path.stem}.context.json"
    return json.loads(ctx_path.read_text(encoding="utf-8"))

from app.services.agentic.runtime.scene_helpers import add_static_preview_mesh

MESH_ASSETS = [{"id": "asset-6fefd6557a29", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\base_link_collision.stl", "relative": "assets/imported/meshes/collision/base_link_collision.stl"}, {"id": "asset-a75117470e28", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_left_foot_collision.stl"}, {"id": "asset-cc734f3e7068", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_abduction_collision.stl"}, {"id": "asset-3ae0786d1190", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_pitch_housing_collision.stl"}, {"id": "asset-e4257968a0d3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_knee_housing_collision.stl"}, {"id": "asset-e64dd19c48c7", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_lower_leg_collision.stl"}, {"id": "asset-f8a8496bb82e", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_upper_leg_collision.stl"}, {"id": "asset-6b6fa76ef725", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_right_foot_collision.stl"}, {"id": "asset-41d5d8786dd5", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_abduction_collision.stl"}, {"id": "asset-7e11f2bbcd6f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_pitch_housing_collision.stl"}, {"id": "asset-d42ef37e97a9", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_knee_housing_collision.stl"}, {"id": "asset-5c72a4a803de", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_lower_leg_collision.stl"}, {"id": "asset-b8a5007323bb", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_upper_leg_collision.stl"}, {"id": "asset-177eadb6fd25", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_sensor_panel_collision.stl", "relative": "assets/imported/meshes/collision/front_sensor_panel_collision.stl"}, {"id": "asset-504c770d0850", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\internal_electronics_collision.stl", "relative": "assets/imported/meshes/collision/internal_electronics_collision.stl"}, {"id": "asset-fbd0f56ce5b1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\payload_mount_collision.stl", "relative": "assets/imported/meshes/collision/payload_mount_collision.stl"}, {"id": "asset-26df057606a1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_foot_collision.stl"}, {"id": "asset-1679671213d3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_abduction_collision.stl"}, {"id": "asset-69415da21c4f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_pitch_housing_collision.stl"}, {"id": "asset-fd2c1e58d70f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_knee_housing_collision.stl"}, {"id": "asset-f9aa0876fdff", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_lower_leg_collision.stl"}, {"id": "asset-da90178bb176", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_upper_leg_collision.stl"}, {"id": "asset-5f007d45e874", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_foot_collision.stl"}, {"id": "asset-4fdc8e000bbd", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_abduction_collision.stl"}, {"id": "asset-58e981f0932c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_pitch_housing_collision.stl"}, {"id": "asset-7c850a2e40e7", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_knee_housing_collision.stl"}, {"id": "asset-45b6771c3dc9", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_lower_leg_collision.stl"}, {"id": "asset-32bd42fcb65d", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_upper_leg_collision.stl"}, {"id": "asset-4e1dbc37d215", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_service_panel_collision.stl", "relative": "assets/imported/meshes/collision/rear_service_panel_collision.stl"}, {"id": "asset-5bb889c358e0", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\visual\\generated_robot_dog.glb", "relative": "assets/visual/generated_robot_dog.glb"}]
READINESS_NOTE = "No joints detected. Robot motion tests require URDF/MJCF. FEA/CFD need additional metadata."


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"mode": "static_mesh_preview", "readiness_note": READINESS_NOTE})
    frames: list[dict] = []

    try:
        if not MESH_ASSETS:
            raise RuntimeError("No mesh assets for static preview.")

        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)
        add_static_preview_mesh(scene, MESH_ASSETS[0]["path"])
        scene.build()
        step_scene_for_duration(scene, config)
        frames.append({"step": 0, "mode": "static", "mesh": MESH_ASSETS[0]["path"]})

        report_path = Path(config["output_root"]) / "readiness_report.json"
        report_path.write_text(
            json.dumps(
                {
                    "readiness_note": READINESS_NOTE,
                    "mesh_count": len(MESH_ASSETS),
                    "joints_detected": False,
                    "robot_motion_requires": "urdf_or_mjcf",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()