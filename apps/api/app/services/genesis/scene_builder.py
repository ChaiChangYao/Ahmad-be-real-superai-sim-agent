from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest
from app.services.genesis.manifest_to_genesis import convert_manifest


def build_scene_summary(manifest: BuildablesPhysicsManifest, scenario_config: dict | None = None) -> dict:
    scenario_config = scenario_config or {}
    converted = convert_manifest(manifest)
    return {
        "project_id": manifest.project_id,
        "links": len(converted["links"]),
        "joints": len(converted["joints"]),
        "actuators": len(converted["actuators"]),
        "sensors": len(manifest.sensors),
        "wires": len(manifest.wires),
        "terrain": scenario_config.get("terrain", "flat"),
        "payload_kg": scenario_config.get("payload_kg", 0.0),
        "robot_description": {
            "urdf_path": manifest.robot_description.urdf_path,
            "mjcf_path": manifest.robot_description.mjcf_path,
        },
    }


def build_initial_state(manifest: BuildablesPhysicsManifest) -> dict:
    links = {}
    for link in manifest.links:
        links[link.id] = {
            "position": [link.transform.position.x, link.transform.position.y, link.transform.position.z],
            "rotation_quat": [1.0, 0.0, 0.0, 0.0],
            "mass_kg": link.mass_kg,
        }
    joints = {joint.id: 0.0 for joint in manifest.joints}
    return {"links": links, "joints": joints, "sensors": {}, "events": []}
