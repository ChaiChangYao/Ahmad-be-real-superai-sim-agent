from __future__ import annotations

from typing import Any


def list_dofs(entity: Any) -> dict:
    result = {"count": 0, "limits": []}
    if hasattr(entity, "get_dofs_limit"):
        limits = entity.get_dofs_limit()
        try:
            limits_list = limits.tolist()
        except Exception:
            limits_list = []
        result["limits"] = limits_list
        result["count"] = len(limits_list)
    return result


def apply_joint_targets(entity: Any, targets: list[float]) -> bool:
    if hasattr(entity, "control_dofs_position"):
        entity.control_dofs_position(targets)
        return True
    return False
