"""Telemetry helpers for generated scripts."""
from __future__ import annotations

from typing import Any


def create_telemetry_schema(sensor_type: str, sample_rate: float = 100.0) -> dict[str, Any]:
    if sensor_type == "imu":
        return {
            "type": "imu",
            "sampleRate": sample_rate,
            "channels": ["lin_acc.x", "lin_acc.y", "lin_acc.z", "ang_vel.x", "ang_vel.y", "ang_vel.z"],
        }
    if sensor_type == "contact_force":
        return {"type": "contact_force", "sampleRate": sample_rate, "channels": ["force_total"]}
    if sensor_type == "depth_camera":
        return {"type": "depth_camera", "sampleRate": sample_rate, "channels": ["depth_mean"]}
    if sensor_type == "temperature_grid":
        return {"type": "temperature_grid", "sampleRate": sample_rate, "channels": ["grid_mean_temp"]}
    if sensor_type == "joint":
        return {"type": "joint", "sampleRate": sample_rate, "channels": ["joint_positions"]}
    return {"type": sensor_type, "sampleRate": sample_rate, "channels": []}


def record_imu_sample(t: float, step: int, lin_acc: list[float], ang_vel: list[float]) -> dict:
    return {"t": t, "step": step, "lin_acc": lin_acc, "ang_vel": ang_vel}


def record_contact_force_sample(t: float, step: int, force_total: float) -> dict:
    return {"t": t, "step": step, "force_total": force_total}


def record_depth_camera_sample(t: float, step: int, depth_mean: float) -> dict:
    return {"t": t, "step": step, "depth_mean": depth_mean}


def record_temperature_grid_sample(t: float, step: int, grid_mean: float) -> dict:
    return {"t": t, "step": step, "grid_mean_temp": grid_mean, "demo_field": True}


def summarize_telemetry(samples: list[dict], schema: dict) -> dict:
    return {"schema": schema, "sample_count": len(samples), "samples": samples[:500]}
