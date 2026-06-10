from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def convert_manifest(manifest: BuildablesPhysicsManifest) -> dict:
    links = []
    for link in manifest.links:
        links.append(
            {
                "id": link.id,
                "mass_kg": link.mass_kg,
                "position": [link.transform.position.x, link.transform.position.y, link.transform.position.z],
                "rotation_rpy": [link.transform.rotation_rpy.x, link.transform.rotation_rpy.y, link.transform.rotation_rpy.z],
                "collision_primitive_ids": link.collision_primitive_ids,
                "material_id": link.material_id,
            }
        )
    joints = []
    for joint in manifest.joints:
        joints.append(
            {
                "id": joint.id,
                "parent": joint.parent_link_id,
                "child": joint.child_link_id,
                "axis_xyz": [joint.axis_xyz.x, joint.axis_xyz.y, joint.axis_xyz.z],
                "limits": [joint.limit_lower_rad, joint.limit_upper_rad],
                "effort_limit_nm": joint.effort_limit_nm,
                "velocity_limit_rad_s": joint.velocity_limit_rad_s,
            }
        )
    return {
        "project_id": manifest.project_id,
        "link_count": len(links),
        "joint_count": len(joints),
        "actuator_count": len(manifest.actuators),
        "links": links,
        "joints": joints,
        "actuators": [a.model_dump() for a in manifest.actuators],
        "collision_primitives": [c.model_dump() for c in manifest.collision_primitives],
    }
