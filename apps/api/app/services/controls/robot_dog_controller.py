from __future__ import annotations

from app.services.controls.gait_generator import simple_walk_targets


def command_to_targets(command: str, time_s: float) -> dict[str, float]:
    if command in {"walk_forward", "forward"}:
        return simple_walk_targets(time_s, turn_scale=0.0, stride_scale=1.0)
    if command in {"walk_backward", "backward"}:
        out = simple_walk_targets(time_s, turn_scale=0.0, stride_scale=1.0)
        return {k: -v for k, v in out.items()}
    if command in {"turn_left", "left"}:
        return simple_walk_targets(time_s, turn_scale=0.16, stride_scale=0.8)
    if command in {"turn_right", "right"}:
        return simple_walk_targets(time_s, turn_scale=-0.16, stride_scale=0.8)
    if command in {"stand", "stop", "emergency_stop"}:
        return {
            "j-hip-fl": 0.2,
            "j-knee-fl": -0.8,
            "j-hip-fr": 0.2,
            "j-knee-fr": -0.8,
            "j-hip-rl": 0.2,
            "j-knee-rl": -0.8,
            "j-hip-rr": 0.2,
            "j-knee-rr": -0.8,
        }
    if command == "reset":
        return {joint_id: 0.0 for joint_id in ["j-hip-fl", "j-knee-fl", "j-hip-fr", "j-knee-fr", "j-hip-rl", "j-knee-rl", "j-hip-rr", "j-knee-rr"]}
    return {}
