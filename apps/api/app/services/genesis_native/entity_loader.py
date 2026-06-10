from __future__ import annotations

from pathlib import Path
from typing import Any

from .gs_lazy import gs
from .mesh_loader import add_mesh_entity
from .urdf_mjcf_loader import add_mjcf_entity, add_urdf_entity


def add_plane(scene: Any) -> Any:
    return scene.add_entity(gs().morphs.Plane())


def add_box(scene: Any, *, pos: tuple[float, float, float], size: tuple[float, float, float], fixed: bool = False) -> Any:
    return scene.add_entity(gs().morphs.Box(pos=pos, size=size, fixed=fixed))


def add_from_robot_description(
    scene: Any, robot_path: Path | str, preferred_format: str, *, fixed: bool = False
) -> Any:
    path = Path(robot_path)
    if preferred_format == "urdf":
        return add_urdf_entity(scene, path, fixed=fixed, pos=(0.0, 0.0, 0.0), euler=(0.0, 0.0, 0.0))
    if preferred_format == "mjcf":
        return add_mjcf_entity(scene, path, pos=(0.0, 0.0, 0.0), euler=(0.0, 0.0, 0.0))
    return add_mesh_entity(scene, path)
