from __future__ import annotations

from app.services.controls.jump_controller import jump_targets


def generate_jump(time_s: float) -> dict[str, float]:
    return jump_targets(time_s)
