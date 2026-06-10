from __future__ import annotations

import time
from pathlib import Path

from .entity_loader import add_from_robot_description, add_plane
from .genesis_runtime import GenesisRunConfig, genesis_lock, shared_runtime
from .viewer_compat import viewer_vis_options
from .viewer_diagnostics import ViewerDiagnosticsSampler, collect_viewer_diagnostics
from .viewer_options import native_viewer_options


def run_native_viewer(robot_path: Path, preferred_format: str, steps: int = 600) -> dict:
    import genesis as gs

    runtime = shared_runtime()
    config = GenesisRunConfig(show_viewer=True, dt=1.0 / 60.0)
    sampler = ViewerDiagnosticsSampler()
    step_count = 0
    started = time.perf_counter()
    with genesis_lock():
        runtime.init(config)
        sim_options = gs.options.SimOptions(dt=config.dt, substeps=config.substeps)
        scene = gs.Scene(
            sim_options=sim_options,
            show_viewer=True,
            vis_options=viewer_vis_options(),
            viewer_options=native_viewer_options(),
        )
        add_plane(scene)
        add_from_robot_description(scene, robot_path=robot_path, preferred_format=preferred_format, fixed=False)
        runtime.build_scene(scene)
        try:
            while True:
                t0 = time.perf_counter()
                scene.step()
                sampler.record_step(time.perf_counter() - t0)
                step_count += 1
        except KeyboardInterrupt:
            pass
    duration_s = time.perf_counter() - started
    diagnostics = collect_viewer_diagnostics(config.backend, sampler.summary())
    return {
        "viewer_started": True,
        "step_count": step_count,
        "duration_s": round(duration_s, 3),
        "robot_path": str(robot_path),
        "format": preferred_format,
        **diagnostics,
    }
