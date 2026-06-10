from __future__ import annotations

from typing import Any

from .gs_lazy import gs

from .genesis_runtime import GenesisNativeRuntime, GenesisRunConfig


def create_scene(runtime: GenesisNativeRuntime, show_viewer: bool = False, dt: float = 1.0 / 60.0) -> Any:
    config = GenesisRunConfig(show_viewer=show_viewer, dt=dt)
    return runtime.create_scene(config)


def add_default_floor(scene: Any, friction: float = 0.8) -> Any:
    _ = friction  # current Plane morph does not require friction parameter at creation.
    return scene.add_entity(gs().morphs.Plane())
