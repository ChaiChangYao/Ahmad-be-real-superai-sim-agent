from __future__ import annotations

import math


def jump_targets(time_s: float, jump_height: float = 0.08) -> dict[str, float]:
    # Conservative crouch-extend cycle for stable local execution.
    phase = min(1.0, max(0.0, time_s / 0.4))
    crouch = -0.9 + 0.25 * math.sin(phase * math.pi)
    hip = 0.3 * math.sin(phase * math.pi)
    return {
        "j-hip-fl": hip,
        "j-knee-fl": crouch,
        "j-hip-fr": hip,
        "j-knee-fr": crouch,
        "j-hip-rl": hip,
        "j-knee-rl": crouch,
        "j-hip-rr": hip,
        "j-knee-rr": crouch,
        "_jump_height_hint": jump_height,
    }
