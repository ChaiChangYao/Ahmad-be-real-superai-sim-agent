"""Genesis scene setup for generated scripts."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.services.agentic.runtime.safe_plotting import patch_plt_show_for_web, suppress_native_matplotlib


def init_genesis_web_mode(config: dict) -> None:
    suppress_native_matplotlib()
    patch_plt_show_for_web()
    import genesis as gs

    backend = gs.cpu if os.environ.get("BUILDABLES_GENESIS_BACKEND", "cpu") == "cpu" else gs.gpu
    gs.init(backend=backend, logging_level="warning")


def create_basic_scene(config: dict) -> Any:
    import genesis as gs

    physics = config.get("physics_config", {})
    dt = float(physics.get("timestep", 0.01))
    return gs.Scene(show_viewer=False, sim_options=gs.options.SimOptions(dt=dt))


def add_floor(scene: Any, _config: dict | None = None) -> None:
    import genesis as gs

    from app.services.genesis_native.entity_loader import add_plane

    add_plane(scene)


def add_robot_from_urdf_or_mjcf(scene: Any, desc_path: str, desc_type: str) -> Any:
    from app.services.genesis_native.entity_loader import add_from_robot_description

    return add_from_robot_description(scene, desc_path, preferred_format=desc_type)


def add_mesh_entity(scene: Any, mesh_path: str) -> Any:
    import genesis as gs

    return scene.add_entity(gs.morphs.Mesh(file=mesh_path))


def add_fallback_skeleton_robot(scene: Any, desc_path: str) -> Any:
    """Load mesh-free generated URDF for skeleton preview."""
    return add_robot_from_urdf_or_mjcf(scene, desc_path, "urdf")


def add_static_preview_mesh(scene: Any, mesh_path: str) -> Any:
    return add_mesh_entity(scene, mesh_path)


def step_scene_for_duration(scene: Any, config: dict) -> int:
    physics = config.get("physics_config", {})
    dt = float(physics.get("timestep", 0.01))
    duration = float(physics.get("duration_seconds", 4.0))
    steps = max(1, int(duration / dt))
    for i in range(steps):
        scene.step()
        if i % 50 == 0:
            print(f"[agentic_runtime] step {i}/{steps}", flush=True)
    return steps


def fit_initial_camera_metadata(_config: dict) -> dict:
    return {"camera_pos": [2.5, 2.5, 1.5], "camera_lookat": [0, 0, 0.5]}
