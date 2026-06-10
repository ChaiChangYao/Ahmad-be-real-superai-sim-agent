from __future__ import annotations


def read_sensor_snapshot() -> dict:
    return {
        "imu": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
        "depth": {"min_distance_m": 1.0},
        "contacts": {"fl": 1, "fr": 1, "rl": 1, "rr": 1},
    }
