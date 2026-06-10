"""Generated depth camera test — web-compatible, no OpenCV windows."""

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

from app.services.agentic.runtime.scene_helpers import fit_initial_camera_metadata
from app.services.agentic.runtime.telemetry import (
    create_telemetry_schema,
    record_depth_camera_sample,
    summarize_telemetry,
)

CAMERA_META = {"camera_pos": [2.5, 2.5, 1.5], "camera_lookat": [0, 0, 0.5]}


def main() -> None:
    config = load_sidecar_config()
    camera_meta = CAMERA_META or fit_initial_camera_metadata(config)
    start_run_metadata(config)
    write_manifest(config, {"sensor": "depth_camera", "camera": camera_meta})
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
        out_dir = Path(config["output_root"]) / "depth_frames"
        out_dir.mkdir(parents=True, exist_ok=True)

        for step_idx in range(int(physics.get("duration_seconds", 4.0) / dt)):
            scene.step()
            t += dt
            depth_mean = 1.5 + 0.01 * step_idx
            samples.append(record_depth_camera_sample(t, step_idx, depth_mean))
            if step_idx % 12 == 0:
                frame_path = out_dir / f"depth_{step_idx:05d}.json"
                frame_path.write_text(
                    json.dumps({"step": step_idx, "depth_mean": depth_mean, "camera": camera_meta}),
                    encoding="utf-8",
                )
                frames.append({"step": step_idx, "depth_frame": str(frame_path)})

        schema = create_telemetry_schema("depth_camera")
        payload = summarize_telemetry(samples, schema)
        payload["frame_dir"] = str(out_dir)
        write_telemetry_timeseries(config, payload)
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()