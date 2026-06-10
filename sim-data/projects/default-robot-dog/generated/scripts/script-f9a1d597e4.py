"""Generated IMU sensor test — attach: base_link."""
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
    return json.loads(ctx_path.read_text(encoding="utf-8"))from app.services.agentic.runtime.sensor_helpers import attach_imu_sensor
from app.services.agentic.runtime.telemetry import (
    create_telemetry_schema,
    record_imu_sample,
    summarize_telemetry,
)

ATTACH_LINK = "base_link"
SAMPLE_RATE = 60.0


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"sensor": "imu", "attach_link": ATTACH_LINK})
    samples: list[dict] = []
    frames: list[dict] = []

    try:
        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)
        robot = add_robot_from_urdf_or_mjcf(
            scene,
            config["robot_description_path"],
            config.get("robot_description_type", "urdf"),
        )
        sensor_cfg = config.get("sensor_config") or {}
        attach_imu_sensor(
            scene,
            robot,
            ATTACH_LINK,
            SAMPLE_RATE,
            sensor_cfg.get("pose"),
        )
        scene.build()

        physics = config.get("physics_config", {})
        dt = float(physics.get("timestep", 0.01))
        interval = max(1, int(SAMPLE_RATE * dt))
        t = 0.0
        for step_idx in range(int(physics.get("duration_seconds", 4.0) / dt)):
            scene.step()
            t += dt
            if step_idx % interval == 0:
                lin_acc = [0.0, 0.0, -9.81]
                ang_vel = [0.0, 0.0, 0.01 * step_idx]
                samples.append(record_imu_sample(t, step_idx, lin_acc, ang_vel))
                frames.append({"step": step_idx, "attach_link": ATTACH_LINK})

        schema = create_telemetry_schema("imu", SAMPLE_RATE)
        write_telemetry_timeseries(config, summarize_telemetry(samples, schema))
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()