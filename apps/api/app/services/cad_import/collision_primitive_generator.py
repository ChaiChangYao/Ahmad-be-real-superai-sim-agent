from __future__ import annotations


def generate_default_collision_primitive(link_id: str, primitive_id: str) -> dict:
    return {
        "id": primitive_id,
        "link_id": link_id,
        "primitive_type": "capsule",
        "dimensions": [0.03, 0.12],
        "offset": {"x": 0.0, "y": 0.0, "z": 0.0},
        "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0},
    }
