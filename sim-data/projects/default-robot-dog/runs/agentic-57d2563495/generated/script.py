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

MESH_ASSETS = [{"id": "asset-ab1954d58117", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\base_link_collision.stl", "relative": "assets/imported/meshes/collision/base_link_collision.stl"}, {"id": "asset-8d8c05a02f77", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_left_foot_collision.stl"}, {"id": "asset-dc285d8990fa", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_abduction_collision.stl"}, {"id": "asset-d285c619d0e4", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_hip_pitch_housing_collision.stl"}, {"id": "asset-d58494e6a308", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_left_knee_housing_collision.stl"}, {"id": "asset-3a10dde55223", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_lower_leg_collision.stl"}, {"id": "asset-2777295301fe", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_left_upper_leg_collision.stl"}, {"id": "asset-953c37ccc881", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/front_right_foot_collision.stl"}, {"id": "asset-1a0873991806", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_abduction_collision.stl"}, {"id": "asset-8d178655ff8b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_hip_pitch_housing_collision.stl"}, {"id": "asset-eb0ec13a3ae3", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/front_right_knee_housing_collision.stl"}, {"id": "asset-9b64bf9a5bdb", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_lower_leg_collision.stl"}, {"id": "asset-462d77e84e6f", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/front_right_upper_leg_collision.stl"}, {"id": "asset-98f86375b20a", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\front_sensor_panel_collision.stl", "relative": "assets/imported/meshes/collision/front_sensor_panel_collision.stl"}, {"id": "asset-88f139aa777d", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\internal_electronics_collision.stl", "relative": "assets/imported/meshes/collision/internal_electronics_collision.stl"}, {"id": "asset-7e539533a7bc", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\payload_mount_collision.stl", "relative": "assets/imported/meshes/collision/payload_mount_collision.stl"}, {"id": "asset-dae7686a990a", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_foot_collision.stl"}, {"id": "asset-214154aad84b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_abduction_collision.stl"}, {"id": "asset-cba5a663a6bc", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_hip_pitch_housing_collision.stl"}, {"id": "asset-4542dc0981b4", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_knee_housing_collision.stl"}, {"id": "asset-83d44870a26a", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_lower_leg_collision.stl"}, {"id": "asset-3155054d0f57", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_left_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_left_upper_leg_collision.stl"}, {"id": "asset-75d0f60e5543", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_foot_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_foot_collision.stl"}, {"id": "asset-c206e7bb3e7b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_abduction_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_abduction_collision.stl"}, {"id": "asset-2e509c4b0f21", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_hip_pitch_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_hip_pitch_housing_collision.stl"}, {"id": "asset-80fa5695e05b", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_knee_housing_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_knee_housing_collision.stl"}, {"id": "asset-342ce8226bb9", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_lower_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_lower_leg_collision.stl"}, {"id": "asset-9b088115b1a1", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_right_upper_leg_collision.stl", "relative": "assets/imported/meshes/collision/rear_right_upper_leg_collision.stl"}, {"id": "asset-bd8e996eb219", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\imported\\meshes\\collision\\rear_service_panel_collision.stl", "relative": "assets/imported/meshes/collision/rear_service_panel_collision.stl"}, {"id": "asset-ef8733b896c8", "path": "C:\\Users\\user\\Physics Sim Buildables\\PhysicsSimBuildables\\sim-data\\projects\\default-robot-dog\\assets\\visual\\generated_robot_dog.glb", "relative": "assets/visual/generated_robot_dog.glb"}]
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