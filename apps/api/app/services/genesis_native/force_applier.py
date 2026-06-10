from __future__ import annotations

from typing import Any


def apply_lateral_force(entity: Any, force: tuple[float, float, float]) -> bool:
    fx, fy, fz = force
    if hasattr(entity, "apply_external_force"):
        entity.apply_external_force(force)
        return True
    if hasattr(entity, "set_external_force"):
        entity.set_external_force(force)
        return True
    if hasattr(entity, "control_dofs_force"):
        try:
            n = len(entity.get_dofs_position().tolist())
            arr = [0.0] * n
            if n >= 1:
                arr[0] = fx
            if n >= 2:
                arr[1] = fy
            if n >= 3:
                arr[2] = fz
            entity.control_dofs_force(arr)
            return True
        except Exception:
            pass
    return False
