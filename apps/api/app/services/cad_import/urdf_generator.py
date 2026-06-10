from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest


def generate_urdf(manifest: BuildablesPhysicsManifest, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'<robot name="{manifest.project_id}">']
    for link in manifest.links:
        lines.append(f'  <link name="{link.id}">')
        lines.append("    <inertial>")
        lines.append('      <origin xyz="0 0 0" rpy="0 0 0"/>')
        lines.append('      <mass value="1.0"/>')
        lines.append('      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>')
        lines.append("    </inertial>")
        lines.append("  </link>")
    for joint in manifest.joints:
        lines.append(f'  <joint name="{joint.id}" type="{joint.type}">')
        lines.append(f'    <parent link="{joint.parent_link_id}"/>')
        lines.append(f'    <child link="{joint.child_link_id}"/>')
        origin = joint.origin_xyz
        rpy = joint.origin_rpy
        lines.append(
            f'    <origin xyz="{origin.x} {origin.y} {origin.z}" rpy="{rpy.x} {rpy.y} {rpy.z}"/>'
        )
        if joint.type in {"revolute", "continuous", "prismatic"}:
            axis = joint.axis_xyz
            lines.append(f'    <axis xyz="{axis.x} {axis.y} {axis.z}"/>')
        if joint.type in {"revolute", "prismatic"}:
            lower = joint.limit_lower_rad
            upper = joint.limit_upper_rad
            effort = joint.effort_limit_nm
            velocity = joint.velocity_limit_rad_s
            lines.append(
                f'    <limit lower="{lower}" upper="{upper}" effort="{effort}" velocity="{velocity}"/>'
            )
        lines.append("  </joint>")
    lines.append("</robot>")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
