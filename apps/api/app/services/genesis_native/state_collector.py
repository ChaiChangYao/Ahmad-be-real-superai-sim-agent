from __future__ import annotations

import math
from typing import Any


def quat_to_euler_deg(quat: list[float]) -> tuple[float, float, float]:
    w, x, y, z = (float(quat[0]), float(quat[1]), float(quat[2]), float(quat[3])) if len(quat) >= 4 else (1.0, 0.0, 0.0, 0.0)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    sinp = 2 * (w * y - z * x)
    pitch = math.copysign(math.pi / 2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


def _tolist(value: Any) -> list[float]:
    try:
        return [float(v) for v in value.tolist()]
    except Exception:
        if isinstance(value, (list, tuple)):
            return [float(v) for v in value]
        return []


def collect_entity_frame(entity: Any, entity_name: str = "robot") -> dict:
    pos = _tolist(entity.get_pos()) if hasattr(entity, "get_pos") else [0.0, 0.0, 0.0]
    quat = _tolist(entity.get_quat()) if hasattr(entity, "get_quat") else [1.0, 0.0, 0.0, 0.0]
    dof_pos = _tolist(entity.get_dofs_position()) if hasattr(entity, "get_dofs_position") else []
    dof_vel = _tolist(entity.get_dofs_velocity()) if hasattr(entity, "get_dofs_velocity") else []
    roll, pitch, yaw = quat_to_euler_deg(quat)
    contact_count = 0
    if hasattr(entity, "get_contacts"):
        try:
            contacts = entity.get_contacts()
            contact_count = len(contacts) if contacts is not None else 0
        except Exception:
            contact_count = 0
    return {
        "position": pos,
        "rotation_quat": quat,
        "dof_position": dof_pos,
        "dof_velocity": dof_vel,
        "pose": {"roll_deg": roll, "pitch_deg": pitch, "yaw_deg": yaw},
        "contact_count": contact_count,
    }


def build_frame(
    step: int,
    dt: float,
    tracked: dict[str, Any],
    joint_ids: list[str] | None = None,
    extras: dict | None = None,
) -> dict:
    entities: dict[str, dict] = {}
    for name, entity in tracked.items():
        entities[name] = collect_entity_frame(entity, name)

    robot = entities.get("robot") or entities.get("target") or {}
    pos = robot.get("position", [0.0, 0.0, 0.0])
    quat = robot.get("rotation_quat", [1.0, 0.0, 0.0, 0.0])
    pose = robot.get("pose", {"roll_deg": 0.0, "pitch_deg": 0.0, "yaw_deg": 0.0})
    dof_pos = robot.get("dof_position", [])

    joints: dict[str, float] = {}
    if joint_ids and dof_pos:
        for idx, joint_id in enumerate(joint_ids):
            if idx < len(dof_pos):
                joints[joint_id] = float(dof_pos[idx])

    contact_count = int(robot.get("contact_count", 0))
    frame = {
        "t": round(step * dt, 6),
        "step": step,
        "entities": entities,
        "links": {
            "body": {
                "position": pos,
                "rotation_quat": quat,
            }
        },
        "joints": joints,
        "pose": pose,
        "contacts": {"ratio": 1.0 if contact_count > 0 else 0.0, "count": contact_count},
        "collisions": contact_count,
        "events": [],
    }
    if extras:
        frame.update(extras)
    return frame
