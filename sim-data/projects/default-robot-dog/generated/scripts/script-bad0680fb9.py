"""Skeleton fallback preview — mesh assets missing. Not full visual simulation."""

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

from app.services.agentic.runtime.scene_helpers import add_fallback_skeleton_robot
from app.services.agentic.runtime.telemetry import create_telemetry_schema, summarize_telemetry

SELECTED_JOINTS = ["front_sensor_panel_link_fixed", "rear_service_panel_link_fixed", "internal_electronics_link_fixed", "payload_mount_link_fixed", "front_left_hip_abduction_joint", "front_left_hip_pitch_housing_fixed", "front_left_hip_pitch_joint", "front_left_knee_housing_fixed", "front_left_knee_pitch_joint", "front_left_foot_fixed", "front_right_hip_abduction_joint", "front_right_hip_pitch_housing_fixed"]
SKELETON_WARNING = "Skeleton fallback preview. Mesh assets missing."


def main() -> None:
    config = load_sidecar_config()
    config["warnings"] = list(config.get("warnings") or []) + [SKELETON_WARNING]
    start_run_metadata(config)
    write_manifest(config, {"fallback_mode": "skeleton", "warnings": config["warnings"]})
    samples: list[dict] = []
    frames: list[dict] = []

    try:
        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)
        add_fallback_skeleton_robot(scene, config["robot_description_path"])
        scene.build()

        physics = config.get("physics_config", {})
        dt = float(physics.get("timestep", 0.01))
        t = 0.0
        for step_idx in range(40):
            scene.step()
            t += dt
            if step_idx % 4 == 0:
                frames.append({"step": step_idx, "mode": "skeleton"})
                samples.append({"t": t, "step": step_idx, "joint_positions": []})

        schema = create_telemetry_schema("joint")
        write_telemetry_timeseries(config, summarize_telemetry(samples, schema))
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()