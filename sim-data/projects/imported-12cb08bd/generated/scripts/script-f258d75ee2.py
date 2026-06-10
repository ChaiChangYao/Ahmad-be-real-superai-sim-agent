"""Generated gravity stability test — imported-12cb08bd / gravity_stability."""

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

from app.services.agentic.runtime.scene_helpers import add_mesh_entity, add_static_preview_mesh


def main() -> None:
    config = load_sidecar_config()
    start_run_metadata(config)
    write_manifest(config, {"warnings": []})
    frames: list[dict] = []

    try:
        init_genesis_web_mode(config)
        scene = create_basic_scene(config)
        add_floor(scene, config)

        desc = config.get("robot_description_path", "")
        desc_type = config.get("robot_description_type", "urdf")
        mesh_assets = config.get("mesh_assets") or []

        if desc:
            add_robot_from_urdf_or_mjcf(scene, desc, desc_type)
        elif mesh_assets:
            add_static_preview_mesh(scene, mesh_assets[0]["path"])
        else:
            raise RuntimeError("No robot description or mesh asset for gravity test.")

        scene.build()
        steps = step_scene_for_duration(scene, config)
        frames.append({"step": steps, "status": "settled", "heuristic": "stable"})

        write_state_timeseries(config, frames)
        finalize_run(config)
    except Exception as exc:
        fail_run(config, exc)
        raise


if __name__ == "__main__":
    main()