"""Sensor configuration helpers — no Franka/Go2 hardcoding."""
from __future__ import annotations

import re
from typing import Any  # noqa: F401 — used by scene entity types


def resolve_attach_link(user_link: str | None, link_names: list[str], root_link: str) -> str:
    if user_link and user_link in link_names:
        return user_link
    return choose_default_attach_link(link_names, root_link)


def choose_default_attach_link(link_names: list[str], root_link: str) -> str:
    if root_link and root_link in link_names:
        return root_link
    for preferred in ("base_link", "base", "torso", "body", "chassis"):
        if preferred in link_names:
            return preferred
    return link_names[0] if link_names else "base_link"


def attach_imu_sensor(
    scene: Any,
    entity: Any,
    link_name: str,
    sample_rate: float,
    pose: dict | None = None,
) -> Any:
    import genesis as gs

    link = entity.get_link(link_name)
    pos = (pose or {}).get("position", [0.0, 0.0, 0.0])
    # Genesis Scene.add_sensor accepts only sensor_options; sample_rate is paced in templates.
    _ = sample_rate
    return scene.add_sensor(
        gs.sensors.IMU(
            entity_idx=entity.idx,
            link_idx_local=link.idx_local,
            pos_offset=tuple(pos[:3]),
        ),
    )


def configure_contact_force(link_names: list[str], user_links: list[str] | None = None) -> list[str]:
    if user_links:
        return [l for l in user_links if l in link_names]
    foot_pattern = re.compile(r"(foot|toe|paw|ankle|leg|sole)", re.I)
    matched = [n for n in link_names if foot_pattern.search(n)]
    return matched if matched else link_names[: min(4, len(link_names))]


def configure_temperature_grid(bounds: list[float] | None, resolution: int = 16) -> dict:
    return {
        "bounds": bounds or [-1, -1, -1, 1, 1, 1],
        "resolution": resolution,
        "demo_field": True,
        "label": "demo/generated thermal field — readiness visualization, not validated thermal simulation",
    }


def attach_depth_camera(_scene: Any, _config: dict) -> dict:
    return {"status": "metadata_only", "note": "Depth frames recorded via scene render hooks when available"}

