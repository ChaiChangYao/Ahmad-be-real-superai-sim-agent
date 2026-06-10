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

MESH_ASSETS = [{"id": "asset-25bf775c23db", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\base_link_collision.stl", "relative": "assets/imported/meshes/collision/base_link_collision.stl"}, {"id": "asset-f01fc226f16f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_left_foot_collision.stl"}, {"id": "asset-ceff21025863", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_abduction_collision.stl"}, {"id": "asset-621881adb324", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_pitch_housing_collision.stl"}, {"id": "asset-323b31c06627", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_knee_housing_collision.stl"}, {"id": "asset-6f40d952d043", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_lower_leg_collision.stl"}, {"id": "asset-8529969b8935", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_upper_leg_collision.stl"}, {"id": "asset-123bac2e1d74", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_right_foot_collision.stl"}, {"id": "asset-716c9e5c5ad3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_abduction_collision.stl"}, {"id": "asset-4fc517cf82a9", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_pitch_housing_collision.stl"}, {"id": "asset-0282ff6379e3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_knee_housing_collision.stl"}, {"id": "asset-648210005e3d", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_lower_leg_collision.stl"}, {"id": "asset-b7f5283b5820", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_upper_leg_collision.stl"}, {"id": "asset-535d830874a9", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_sensor_panel_collision.stl", "relative": "assets/imported/meshes/collision/front_sensor_panel_collision.stl"}, {"id": "asset-58577450737f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\internal_electronics_collision.stl", "relative": "assets/imported/meshes/collision/internal_electronics_collision.stl"}, {"id": "asset-02f7c6827af1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\payload_mount_collision.stl", "relative": "assets/imported/meshes/collision/payload_mount_collision.stl"}, {"id": "asset-3c1b8be46198", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_foot_collision.stl"}, {"id": "asset-3ea8880c66b8", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_abduction_collision.stl"}, {"id": "asset-501920586890", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_pitch_housing_collision.stl"}, {"id": "asset-b367968b1e58", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_knee_housing_collision.stl"}, {"id": "asset-e3a419c48452", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_lower_leg_collision.stl"}, {"id": "asset-2a4bd77b747f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_upper_leg_collision.stl"}, {"id": "asset-822e64127b60", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_foot_collision.stl"}, {"id": "asset-db36c86b495c", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_abduction_collision.stl"}, {"id": "asset-21f7b14edb21", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_pitch_housing_collision.stl"}, {"id": "asset-029cf9674ab5", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_knee_housing_collision.stl"}, {"id": "asset-f1ea39297ca6", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_lower_leg_collision.stl"}, {"id": "asset-a92b555365ed", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_upper_leg_collision.stl"}, {"id": "asset-1905f33572cf", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_service_panel_collision.stl", "relative": "assets/imported/meshes/collision/rear_service_panel_collision.stl"}, {"id": "asset-98e73b854329", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\visual\\generated_robot_dog.glb", "relative": "assets/visual/generated_robot_dog.glb"}]
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