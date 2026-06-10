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

MESH_ASSETS = [{"id": "asset-cc337bbd9674", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\base_link_collision.stl", "relative": "assets/imported/meshes/collision/base_link_collision.stl"}, {"id": "asset-daac9ea0c14a", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_left_foot_collision.stl"}, {"id": "asset-259f51d78bca", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_abduction_collision.stl"}, {"id": "asset-e530e3c6ce7b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_pitch_housing_collision.stl"}, {"id": "asset-b4217549be4c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_knee_housing_collision.stl"}, {"id": "asset-422d063f5ee7", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_lower_leg_collision.stl"}, {"id": "asset-7522e9296c23", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_upper_leg_collision.stl"}, {"id": "asset-c6163ade79f1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_right_foot_collision.stl"}, {"id": "asset-57a23821cbd5", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_abduction_collision.stl"}, {"id": "asset-ac7e7170ad18", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_pitch_housing_collision.stl"}, {"id": "asset-df8af2787846", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_knee_housing_collision.stl"}, {"id": "asset-fbc4e3cb2883", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_lower_leg_collision.stl"}, {"id": "asset-4e0f1ac09dd2", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_upper_leg_collision.stl"}, {"id": "asset-4897cf841abb", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_sensor_panel_collision.stl", "relative": "assets/imported/meshes/collision/front_sensor_panel_collision.stl"}, {"id": "asset-cdabd7204369", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\internal_electronics_collision.stl", "relative": "assets/imported/meshes/collision/internal_electronics_collision.stl"}, {"id": "asset-f2b8a2d31ac3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\payload_mount_collision.stl", "relative": "assets/imported/meshes/collision/payload_mount_collision.stl"}, {"id": "asset-d5ff19b1579c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_foot_collision.stl"}, {"id": "asset-d063d2767fb3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_abduction_collision.stl"}, {"id": "asset-7148af659594", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_pitch_housing_collision.stl"}, {"id": "asset-ec494206e780", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_knee_housing_collision.stl"}, {"id": "asset-33dbfebc19f4", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_lower_leg_collision.stl"}, {"id": "asset-3d74c4d2b31c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_upper_leg_collision.stl"}, {"id": "asset-146781a2110d", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_foot_collision.stl"}, {"id": "asset-9be18af5b734", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_abduction_collision.stl"}, {"id": "asset-cbf3337138ae", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_pitch_housing_collision.stl"}, {"id": "asset-6635414da3ec", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_knee_housing_collision.stl"}, {"id": "asset-6a13f361ab82", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_lower_leg_collision.stl"}, {"id": "asset-c0781b213238", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_upper_leg_collision.stl"}, {"id": "asset-2f31bafa6449", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_service_panel_collision.stl", "relative": "assets/imported/meshes/collision/rear_service_panel_collision.stl"}, {"id": "asset-d604082d9fca", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\visual\\generated_robot_dog.glb", "relative": "assets/visual/generated_robot_dog.glb"}]
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