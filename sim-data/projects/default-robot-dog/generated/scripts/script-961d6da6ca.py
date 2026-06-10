"""Demo/readiness thermal field — NOT validated engineering thermal simulation."""

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

from app.services.agentic.runtime.telemetry import (
    create_telemetry_schema,
    record_temperature_grid_sample,
    summarize_telemetry,
)

GRID_RES = 16
THERMAL_LABEL = "demo/generated thermal field — readiness visualization only"


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"sensor": "temperature_grid", "label": THERMAL_LABEL})
    samples: list[dict] = []
    frames: list[dict] = []

    try:
        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)

        desc = config.get("robot_description_path", "")
        if desc:
            add_robot_from_urdf_or_mjcf(scene, desc, config.get("robot_description_type", "urdf"))
        elif config.get("mesh_assets"):
            from app.services.agentic.runtime.scene_helpers import add_static_preview_mesh

            add_static_preview_mesh(scene, config["mesh_assets"][0]["path"])

        scene.build()
        physics = config.get("physics_config", {})
        dt = float(physics.get("timestep", 0.01))
        t = 0.0
        heat_dir = Path(config["output_root"]) / "heatmap_frames"
        heat_dir.mkdir(parents=True, exist_ok=True)

        for step_idx in range(int(physics.get("duration_seconds", 4.0) / dt)):
            scene.step()
            t += dt
            temp = 20.0 + 5.0 * (step_idx / max(1, int(physics.get("duration_seconds", 4.0) / dt)))
            samples.append(record_temperature_grid_sample(t, step_idx, temp))
            if step_idx % 8 == 0:
                grid = [[temp + i * 0.1 for i in range(GRID_RES)] for _ in range(GRID_RES)]
                frame_path = heat_dir / f"heat_{step_idx:05d}.json"
                frame_path.write_text(
                    json.dumps({"step": step_idx, "grid": grid, "demo_field": True, "label": THERMAL_LABEL}),
                    encoding="utf-8",
                )
                frames.append({"step": step_idx, "heatmap": str(frame_path)})

        schema = create_telemetry_schema("temperature_grid")
        payload = summarize_telemetry(samples, schema)
        payload["label"] = THERMAL_LABEL
        payload["frame_dir"] = str(heat_dir)
        write_telemetry_timeseries(config, payload)
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()