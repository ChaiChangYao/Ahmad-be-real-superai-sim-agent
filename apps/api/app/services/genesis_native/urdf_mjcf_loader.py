from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from .gs_lazy import gs


def _urdf_load_path(urdf_path: Path) -> Path:
    ext = urdf_path.suffix.lower()
    if ext in {".urdf", ".xacro"}:
        return urdf_path
    # Genesis URDF loader requires .urdf/.xacro extension even for URDF XML content.
    tmp = Path(tempfile.gettempdir()) / f"{urdf_path.stem}_genesis.urdf"
    shutil.copy2(urdf_path, tmp)
    return tmp


def add_urdf_entity(
    scene: Any,
    urdf_path: Path | str,
    *,
    fixed: bool,
    pos: tuple[float, float, float],
    euler: tuple[float, float, float],
    scale: float = 1.0,
) -> Any:
    urdf_path = Path(urdf_path)
    if not urdf_path.exists():
        raise FileNotFoundError(f"URDF path not found: {urdf_path}")
    load_path = _urdf_load_path(urdf_path)
    return scene.add_entity(
        gs().morphs.URDF(file=str(load_path), fixed=fixed, pos=pos, euler=euler, scale=scale)
    )


def add_mjcf_entity(
    scene: Any,
    mjcf_path: Path | str,
    *,
    pos: tuple[float, float, float],
    euler: tuple[float, float, float],
    scale: float = 1.0,
) -> Any:
    mjcf_path = Path(mjcf_path)
    if not mjcf_path.exists():
        raise FileNotFoundError(f"MJCF path not found: {mjcf_path}")
    return scene.add_entity(gs().morphs.MJCF(file=str(mjcf_path), pos=pos, euler=euler, scale=scale))
