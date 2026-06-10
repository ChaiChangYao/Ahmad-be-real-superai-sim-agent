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

MESH_ASSETS = [{"id": "asset-b0ba607ef3ef", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\base_link_collision.stl", "relative": "assets/imported/meshes/collision/base_link_collision.stl"}, {"id": "asset-d38a1c7dbff5", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_left_foot_collision.stl"}, {"id": "asset-ae849f41c973", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_abduction_collision.stl"}, {"id": "asset-5882a460cdfa", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_pitch_housing_collision.stl"}, {"id": "asset-793a131f805f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_knee_housing_collision.stl"}, {"id": "asset-986aa805f805", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_lower_leg_collision.stl"}, {"id": "asset-c8fae56e7105", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_upper_leg_collision.stl"}, {"id": "asset-87a8e7a24054", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_right_foot_collision.stl"}, {"id": "asset-a6586abc53bd", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_abduction_collision.stl"}, {"id": "asset-36782e9f7eb0", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_pitch_housing_collision.stl"}, {"id": "asset-e522b31cfdb6", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_knee_housing_collision.stl"}, {"id": "asset-ce2b9bec909d", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_lower_leg_collision.stl"}, {"id": "asset-f8d42c84ce8c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_upper_leg_collision.stl"}, {"id": "asset-f74d21202ee1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_sensor_panel_collision.stl", "relative": "assets/imported/meshes/collision/front_sensor_panel_collision.stl"}, {"id": "asset-1ebfc207d8b4", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\internal_electronics_collision.stl", "relative": "assets/imported/meshes/collision/internal_electronics_collision.stl"}, {"id": "asset-d65e9ca94249", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\payload_mount_collision.stl", "relative": "assets/imported/meshes/collision/payload_mount_collision.stl"}, {"id": "asset-2ff3054ab650", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_foot_collision.stl"}, {"id": "asset-4a0c1997236b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_abduction_collision.stl"}, {"id": "asset-c32c3a36d117", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_pitch_housing_collision.stl"}, {"id": "asset-10ea10c28528", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_knee_housing_collision.stl"}, {"id": "asset-1e540d63e3ab", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_lower_leg_collision.stl"}, {"id": "asset-28b77e9b40d0", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_upper_leg_collision.stl"}, {"id": "asset-beb67716f886", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_foot_collision.stl"}, {"id": "asset-a468969a26fc", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_abduction_collision.stl"}, {"id": "asset-1c0ca7c754fa", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_pitch_housing_collision.stl"}, {"id": "asset-45451df53871", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_knee_housing_collision.stl"}, {"id": "asset-eab3bc439bb7", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_lower_leg_collision.stl"}, {"id": "asset-fafb3f2278a0", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_upper_leg_collision.stl"}, {"id": "asset-16a26e7ee840", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_service_panel_collision.stl", "relative": "assets/imported/meshes/collision/rear_service_panel_collision.stl"}, {"id": "asset-7a712f19d7f7", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\visual\\generated_robot_dog.glb", "relative": "assets/visual/generated_robot_dog.glb"}]
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