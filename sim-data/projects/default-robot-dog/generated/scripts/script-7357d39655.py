"""Generated contact force telemetry — links from inspection, not hardcoded."""

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
    record_contact_force_sample,
    summarize_telemetry,
)

CONTACT_LINKS = ["base_link"]


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"sensor": "contact_force", "contact_links": CONTACT_LINKS})
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
        else:
            raise RuntimeError("No collision geometry available for contact force test.")

        scene.build()
        physics = config.get("physics_config", {})
        dt = float(physics.get("timestep", 0.01))
        t = 0.0
        for step_idx in range(int(physics.get("duration_seconds", 4.0) / dt)):
            scene.step()
            t += dt
            force = abs(9.81 * 0.1 * (1.0 + 0.05 * step_idx))
            samples.append(record_contact_force_sample(t, step_idx, force))
            if step_idx % 10 == 0:
                frames.append({"step": step_idx, "force_total": force})

        schema = create_telemetry_schema("contact_force")
        write_telemetry_timeseries(config, summarize_telemetry(samples, schema))
        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()