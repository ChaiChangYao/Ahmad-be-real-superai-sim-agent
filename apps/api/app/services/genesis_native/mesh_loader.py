from __future__ import annotations

from pathlib import Path
from typing import Any

from .gs_lazy import gs


def add_mesh_entity(scene: Any, mesh_path: Path, *, fixed: bool = False, pos: tuple[float, float, float] = (0.0, 0.0, 0.0), euler: tuple[float, float, float] = (0.0, 0.0, 0.0), scale: float = 1.0) -> Any:
    if not mesh_path.exists():
        raise FileNotFoundError(f"Mesh file not found: {mesh_path}")
    return scene.add_entity(gs().morphs.Mesh(file=str(mesh_path), fixed=fixed, pos=pos, euler=euler, scale=scale))
