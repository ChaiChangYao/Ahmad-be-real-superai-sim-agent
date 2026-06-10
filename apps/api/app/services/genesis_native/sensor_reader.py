from __future__ import annotations

from typing import Any


def read_entity_sensors(entity: Any) -> dict:
    # Native sensor APIs vary by Genesis version; best-effort extraction.
    output: dict = {}
    if hasattr(entity, "get_links_net_contact_force"):
        try:
            output["links_net_contact_force"] = entity.get_links_net_contact_force().tolist()
        except Exception:
            output["links_net_contact_force"] = []
    if hasattr(entity, "get_ang"):
        try:
            output["angular_velocity"] = entity.get_ang().tolist()
        except Exception:
            output["angular_velocity"] = []
    return output
