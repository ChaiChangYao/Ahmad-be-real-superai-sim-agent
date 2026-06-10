"""Procedural Franka Panda link visuals for web replay when mesh export is unavailable."""
from __future__ import annotations

FRANKA_LINK_VISUALS: dict[str, dict] = {
    "link0": {"kind": "cylinder", "radius": 0.08, "height": 0.08, "color": "#e8e8e8"},
    "link1": {"kind": "capsule", "radius": 0.06, "length": 0.28, "color": "#e8e8e8"},
    "link2": {"kind": "capsule", "radius": 0.055, "length": 0.24, "color": "#d8d8d8"},
    "link3": {"kind": "capsule", "radius": 0.05, "length": 0.26, "color": "#e8e8e8"},
    "link4": {"kind": "capsule", "radius": 0.045, "length": 0.22, "color": "#d0d0d0"},
    "link5": {"kind": "capsule", "radius": 0.04, "length": 0.24, "color": "#e8e8e8"},
    "link6": {"kind": "capsule", "radius": 0.035, "length": 0.12, "color": "#d8d8d8"},
    "link7": {"kind": "capsule", "radius": 0.03, "length": 0.14, "color": "#e8e8e8"},
    "hand": {"kind": "box", "size": [0.08, 0.06, 0.1], "color": "#cccccc"},
    "left_finger": {"kind": "box", "size": [0.018, 0.02, 0.06], "color": "#555555"},
    "right_finger": {"kind": "box", "size": [0.018, 0.02, 0.06], "color": "#555555"},
}


def franka_link_visual(link_name: str) -> dict | None:
    key = link_name.split("/")[-1]
    return FRANKA_LINK_VISUALS.get(key)


def attach_franka_fallback_assets(scene: dict, objects: list[dict]) -> bool:
    """Attach procedural visuals to Franka links missing meshPath."""
    attached = False
    assets = scene.setdefault("assets", [])
    for obj in objects:
        if obj.get("type") != "robot_link":
            continue
        robot_model = obj.get("robot_model") or obj.get("parent_robot")
        link_name = obj.get("link_name") or obj.get("id", "").split("/")[-1]
        if robot_model != "franka_panda" and "franka" not in str(obj.get("parent", "")).lower():
            morph = str(obj.get("morph_file", ""))
            if "franka" not in morph.lower():
                continue
        visual = obj.setdefault("visual", {})
        if visual.get("meshPath"):
            continue
        fallback = franka_link_visual(link_name)
        if fallback is None:
            fallback = {"kind": "capsule", "radius": 0.04, "length": 0.1, "color": "#e8e8e8"}
        visual.update({"kind": "procedural", **fallback})
        assets.append({"id": obj["id"], "type": "franka_procedural", "link": link_name})
        attached = True
    scene["robot_model"] = scene.get("robot_model") or "franka_panda"
    scene["franka_fallback"] = attached
    return attached
