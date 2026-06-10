from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def infer_project_type(manifest: BuildablesPhysicsManifest) -> str:
    if manifest.project_type and manifest.project_type != "generic":
        return manifest.project_type
    project_name = manifest.project_name.lower()
    if "dog" in project_name:
        return "robot_dog"
    if "arm" in project_name:
        return "robot_arm"
    if "rover" in project_name:
        return "wheeled_rover"
    if "gripper" in project_name:
        return "gripper"
    if "drone" in project_name:
        return "drone"
    if any(asset.type == "step" for asset in manifest.assets):
        return "imported_cad_assembly"
    return "generic"


def project_supports_remote_control(project_type: str) -> bool:
    return project_type == "robot_dog"
