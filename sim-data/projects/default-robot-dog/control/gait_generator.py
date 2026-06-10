from __future__ import annotations

from app.services.controls.gait_generator import simple_walk_targets


def generate_walk(time_s: float, turn_scale: float = 0.0) -> dict[str, float]:
    return simple_walk_targets(time_s, turn_scale=turn_scale, stride_scale=1.0)
