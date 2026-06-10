from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from app.models.manifest import BuildablesPhysicsManifest


def parse_urdf(urdf_path: Path) -> dict:
    root = ET.fromstring(urdf_path.read_text(encoding="utf-8"))
    links: list[dict] = []
    joints: list[dict] = []
    mesh_refs: list[str] = []
    mesh_ref_details: list[dict] = []
    mesh_usage: dict[str, set[str]] = {}
    materials: list[dict] = []
    transmissions: list[str] = []
    sensors: list[dict] = []

    for material in root.findall("material"):
        mid = material.attrib.get("name", f"material-{len(materials)}")
        materials.append(
            {
                "id": mid,
                "name": mid,
                "density_kg_m3": 1500.0,
                "static_friction": 0.5,
                "dynamic_friction": 0.4,
                "restitution": 0.1,
                "simulation_notes": "Imported from URDF material tag.",
                "confidence": "placeholder",
            }
        )

    for link in root.findall("link"):
        lid = link.attrib.get("name", f"link-{len(links)}")
        inertial = link.find("inertial")
        mass_value = 1.0
        if inertial is not None and inertial.find("mass") is not None:
            mass_value = float(inertial.find("mass").attrib.get("value", "1.0"))
        visuals = link.findall("visual")
        collisions = link.findall("collision")
        for visual in visuals:
            mesh = visual.find("geometry/mesh")
            if mesh is not None and "filename" in mesh.attrib:
                ref = mesh.attrib["filename"]
                mesh_refs.append(ref)
                mesh_usage.setdefault(ref, set()).add("visual")
        for collision in collisions:
            mesh = collision.find("geometry/mesh")
            if mesh is not None and "filename" in mesh.attrib:
                ref = mesh.attrib["filename"]
                mesh_refs.append(ref)
                mesh_usage.setdefault(ref, set()).add("collision")

        links.append(
            {
                "id": lid,
                "name": lid,
                "category": "body" if not links else "other",
                "visual_asset_id": None,
                "material_id": materials[0]["id"] if materials else "imported-default-material",
                "mass_kg": max(0.001, mass_value),
                "center_of_mass": {"x": 0.0, "y": 0.0, "z": 0.0},
                "inertia_tensor": None,
                "transform": {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
                "collision_primitive_ids": [],
                "parent_link_id": None,
                "editable": True,
                "notes": "Imported from URDF.",
            }
        )

    for joint in root.findall("joint"):
        jid = joint.attrib.get("name", f"joint-{len(joints)}")
        parent = (joint.find("parent").attrib.get("link") if joint.find("parent") is not None else "")
        child = (joint.find("child").attrib.get("link") if joint.find("child") is not None else "")
        axis_xyz = {"x": 0.0, "y": 0.0, "z": 1.0}
        axis = joint.find("axis")
        if axis is not None and axis.attrib.get("xyz"):
            parts = [float(x) for x in axis.attrib["xyz"].split()]
            if len(parts) == 3:
                axis_xyz = {"x": parts[0], "y": parts[1], "z": parts[2]}
        lower = -3.14
        upper = 3.14
        limit = joint.find("limit")
        if limit is not None:
            lower = float(limit.attrib.get("lower", lower))
            upper = float(limit.attrib.get("upper", upper))
        joints.append(
            {
                "id": jid,
                "name": jid,
                "type": joint.attrib.get("type", "fixed"),
                "parent_link_id": parent,
                "child_link_id": child,
                "origin_xyz": {"x": 0.0, "y": 0.0, "z": 0.0},
                "origin_rpy": {"x": 0.0, "y": 0.0, "z": 0.0},
                "axis_xyz": axis_xyz,
                "limit_lower_rad": lower,
                "limit_upper_rad": upper,
                "effort_limit_nm": float(limit.attrib.get("effort", "5.0")) if limit is not None else 5.0,
                "velocity_limit_rad_s": float(limit.attrib.get("velocity", "2.0")) if limit is not None else 2.0,
                "damping": 0.05,
                "friction": 0.01,
                "auto_detected": False,
                "user_confirmed": True,
                "notes": "Imported from URDF",
            }
        )

    for transmission in root.findall("transmission"):
        transmissions.append(transmission.attrib.get("name", f"transmission-{len(transmissions)}"))

    for ref, usages in mesh_usage.items():
        usage = "both" if len(usages) >= 2 else next(iter(usages))
        mesh_ref_details.append({"path": ref, "urdf_path": ref, "usage": usage, "link": None})

    return {
        "robot_name": root.attrib.get("name", urdf_path.stem),
        "links": links,
        "joints": joints,
        "materials": materials,
        "mesh_references": mesh_refs,
        "mesh_ref_details": mesh_ref_details,
        "transmissions": transmissions,
        "sensors": sensors,
    }


def urdf_to_manifest(parsed: dict, project_id: str, project_name: str, urdf_path: str) -> BuildablesPhysicsManifest:
    materials = parsed["materials"] or [
        {
            "id": "imported-default-material",
            "name": "Imported Default Material",
            "density_kg_m3": 1600.0,
            "static_friction": 0.5,
            "dynamic_friction": 0.4,
            "restitution": 0.1,
            "simulation_notes": "Fallback material for imported project.",
            "confidence": "placeholder",
        }
    ]
    links = parsed["links"]
    joints = parsed["joints"]
    actuators = []
    for joint in joints:
        if joint["type"] in {"revolute", "continuous", "prismatic"}:
            actuators.append(
                {
                    "id": f"act-{joint['id']}",
                    "name": f"Actuator {joint['name']}",
                    "type": "virtual_motor",
                    "real_component_profile_id": "imported-auto",
                    "joint_id": joint["id"],
                    "control_mode": "position",
                    "max_torque_nm": max(1.0, joint.get("effort_limit_nm", 5.0)),
                    "max_velocity_rad_s": max(0.1, joint.get("velocity_limit_rad_s", 2.0)),
                    "rated_voltage_v": 24.0,
                    "stall_current_a": 3.0,
                    "mass_kg": 0.2,
                    "dimensions_m": [0.05, 0.05, 0.05],
                    "mounting_transform": {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
                    "confidence": "placeholder",
                }
            )

    manifest = BuildablesPhysicsManifest.model_validate(
        {
            "project_id": project_id,
            "project_name": project_name,
            "project_mode": "imported_project",
            "project_type": "imported_cad_assembly",
            "materials": materials,
            "links": links,
            "joints": joints,
            "actuators": actuators,
            "assets": [],
            "electronics": [],
            "sensors": parsed.get("sensors", []),
            "wires": [],
            "collision_primitives": [],
            "robot_description": {"preferred_format": "urdf", "urdf_path": urdf_path, "mjcf_path": None, "generated_from_manifest": False},
            "environments": {"default": "flat"},
            "controls": {"mode": "joint_command_table"},
            "metadata_status": {},
            "render_cameras": [],
            "payloads": [],
            "scenarios": [
                {"id": "passive_gravity", "name": "Passive Gravity", "description": "Passive gravity stability test", "duration_s": 4.0, "config": {"command_hint": "stand"}},
                {"id": "joint_sweep_collision", "name": "Joint Sweep", "description": "Sweep all detected joints", "duration_s": 6.0, "config": {"command_hint": "walk_forward"}},
                {"id": "mechanism_motion", "name": "Mechanism Motion", "description": "Simple mechanism motion command", "duration_s": 5.0, "config": {"command_hint": "walk_forward"}},
            ],
        }
    )
    return manifest
