"""Generated joint sweep — default-robot-dog / joints: 12."""

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

from app.services.agentic.runtime.telemetry import create_telemetry_schema, summarize_telemetry


SELECTED_JOINTS = ["front_sensor_panel_link_fixed", "rear_service_panel_link_fixed", "internal_electronics_link_fixed", "payload_mount_link_fixed", "front_left_hip_abduction_joint", "front_left_hip_pitch_housing_fixed", "front_left_hip_pitch_joint", "front_left_knee_housing_fixed", "front_left_knee_pitch_joint", "front_left_foot_fixed", "front_right_hip_abduction_joint", "front_right_hip_pitch_housing_fixed"]
JOINT_LIMITS = {}
DEFAULT_RANGE = (-0.35, 0.35)


def _sweep_range(joint_name: str) -> tuple[float, float]:
    lim = JOINT_LIMITS.get(joint_name)
    if lim and "lower" in lim and "upper" in lim:
        return float(lim["lower"]), float(lim["upper"])
    return DEFAULT_RANGE


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"warnings": ["53 meshes missing \u2014 skeleton joint sweep may still run."]})
    samples: list[dict] = []
    frames: list[dict] = []

    try:
        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)

        desc = config["robot_description_path"]
        desc_type = config.get("robot_description_type", "urdf")
        robot = add_robot_from_urdf_or_mjcf(scene, desc, desc_type)
        scene.build()

        physics = config.get("physics_config", {})
        dt = float(physics.get("timestep", 0.01))
        t = 0.0
        step_idx = 0

        for joint_name in SELECTED_JOINTS:
            lo, hi = _sweep_range(joint_name)
            for phase in range(20):
                target = lo + (hi - lo) * (phase / 19.0)
                samples.append({"t": t, "step": step_idx, "joint": joint_name, "position": target})
                scene.step()
                t += dt
                step_idx += 1
                if step_idx % 5 == 0:
                    frames.append({"step": step_idx, "joint": joint_name, "position": target})

        schema = create_telemetry_schema("joint", sample_rate=1.0 / dt)
        write_telemetry_timeseries(config, summarize_telemetry(samples, schema))
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()