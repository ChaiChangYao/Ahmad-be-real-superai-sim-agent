from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def get_robot_dog_joint_ids(manifest: BuildablesPhysicsManifest) -> list[str]:
    return [j.id for j in manifest.joints if "hip" in j.name.lower() or "knee" in j.name.lower()]


def initial_pose_targets(manifest: BuildablesPhysicsManifest) -> dict[str, float]:
    targets: dict[str, float] = {}
    for joint in manifest.joints:
        if "knee" in joint.name.lower():
            targets[joint.id] = -0.7
        elif "hip" in joint.name.lower():
            targets[joint.id] = 0.2
        else:
            targets[joint.id] = 0.0
    return targets
