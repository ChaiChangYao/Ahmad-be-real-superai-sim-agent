from __future__ import annotations


def rover_drive_targets(throttle: float, steering: float) -> dict[str, float]:
    return {
        "left_wheel_velocity": float(throttle - steering * 0.5),
        "right_wheel_velocity": float(throttle + steering * 0.5),
        "steering_angle": float(steering),
    }
