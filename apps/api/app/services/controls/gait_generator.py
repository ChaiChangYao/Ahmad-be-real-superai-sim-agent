from __future__ import annotations

import math


def simple_walk_targets(time_s: float, turn_scale: float = 0.0, stride_scale: float = 1.0) -> dict[str, float]:
    phase = time_s * 4.0
    hip = 0.32 * stride_scale * math.sin(phase)
    knee = -0.75 + 0.3 * stride_scale * math.sin(phase + math.pi / 2.0)
    return {
        "j-hip-fl": hip - turn_scale,
        "j-knee-fl": knee,
        "j-hip-fr": -hip + turn_scale,
        "j-knee-fr": knee,
        "j-hip-rl": -hip - turn_scale,
        "j-knee-rl": knee,
        "j-hip-rr": hip + turn_scale,
        "j-knee-rr": knee,
    }
