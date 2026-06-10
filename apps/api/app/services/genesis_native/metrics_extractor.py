from __future__ import annotations

from typing import Any


def extract_basic_metrics(entity: Any, state_timeseries: list[dict], applied_force_n: float | None = None) -> dict:
    pos_z = [frame["entities"].get("target", {}).get("position", [0.0, 0.0, 0.0])[2] for frame in state_timeseries]
    max_h = max(pos_z) if pos_z else 0.0
    min_h = min(pos_z) if pos_z else 0.0
    try:
        contacts = entity.get_contacts()
        contact_count = len(contacts) if contacts is not None else 0
    except Exception:
        contact_count = 0
    return {
        "fall_detected": min_h < 0.05 if pos_z else False,
        "topple_detected": False,
        "max_height_m": float(max_h),
        "min_height_m": float(min_h),
        "contact_count": int(contact_count),
        "collision_count": int(contact_count),
        "applied_force_n": applied_force_n,
    }
