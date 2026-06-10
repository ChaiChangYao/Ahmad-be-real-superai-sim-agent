from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET

from app.models.manifest import BuildablesPhysicsManifest


def parse_mjcf(mjcf_path: Path) -> dict:
    root = ET.fromstring(mjcf_path.read_text(encoding="utf-8"))
    worldbody = root.find("worldbody")
    links: list[dict] = []
    joints: list[dict] = []
    mesh_refs: list[str] = []
    actuators: list[dict] = []
    sensors: list[dict] = []

    def walk_body(node: ET.Element, parent_name: str | None = None) -> None:
        body_name = node.attrib.get("name", f"body-{len(links)}")
        links.append(
            {
                "id": body_name,
                "name": body_name,
                "category": "body" if parent_name is None else "other",
                "visual_asset_id": None,
                "material_id": "imported-default-material",
                "mass_kg": 1.0,
                "center_of_mass": {"x": 0.0, "y": 0.0, "z": 0.0},
                "inertia_tensor": None,
                "transform": {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
                "collision_primitive_ids": [],
                "parent_link_id": parent_name,
                "editable": True,
                "notes": "Imported from MJCF body.",
            }
        )
        for geom in node.findall("geom"):
            if geom.attrib.get("mesh"):
                mesh_refs.append(geom.attrib["mesh"])
        for joint in node.findall("joint"):
            jid = joint.attrib.get("name", f"joint-{len(joints)}")
            joints.append(
                {
                    "id": jid,
                    "name": jid,
                    "type": "revolute",
                    "parent_link_id": parent_name or body_name,
                    "child_link_id": body_name,
                    "origin_xyz": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "origin_rpy": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "axis_xyz": {"x": 0.0, "y": 0.0, "z": 1.0},
                    "limit_lower_rad": -3.14,
                    "limit_upper_rad": 3.14,
                    "effort_limit_nm": 5.0,
                    "velocity_limit_rad_s": 2.0,
                    "damping": 0.05,
                    "friction": 0.01,
                    "auto_detected": False,
                    "user_confirmed": True,
                    "notes": "Imported from MJCF",
                }
            )
        for child in node.findall("body"):
            walk_body(child, body_name)

    if worldbody is not None:
        for body in worldbody.findall("body"):
            walk_body(body, None)

    actuator_root = root.find("actuator")
    if actuator_root is not None:
        for motor in list(actuator_root):
            name = motor.attrib.get("name", f"actuator-{len(actuators)}")
            joint_id = motor.attrib.get("joint", "")
            actuators.append(
                {
                    "id": name,
                    "name": name,
                    "type": "virtual_motor",
                    "real_component_profile_id": "imported-auto",
                    "joint_id": joint_id,
                    "control_mode": "position",
                    "max_torque_nm": float(motor.attrib.get("gear", "5")),
                    "max_velocity_rad_s": 2.0,
                    "rated_voltage_v": 24.0,
                    "stall_current_a": 3.0,
                    "mass_kg": 0.2,
                    "dimensions_m": [0.05, 0.05, 0.05],
                    "mounting_transform": {"position": {"x": 0.0, "y": 0.0, "z": 0.0}, "rotation_rpy": {"x": 0.0, "y": 0.0, "z": 0.0}},
                    "confidence": "placeholder",
                }
            )

    return {
        "robot_name": root.attrib.get("model", mjcf_path.stem),
        "links": links,
        "joints": joints,
        "actuators": actuators,
        "mesh_references": mesh_refs,
        "sensors": sensors,
    }


def mjcf_to_manifest(parsed: dict, project_id: str, project_name: str, mjcf_path: str) -> BuildablesPhysicsManifest:
    manifest = BuildablesPhysicsManifest.model_validate(
        {
            "project_id": project_id,
            "project_name": project_name,
            "project_mode": "imported_project",
            "project_type": "imported_cad_assembly",
            "materials": [
                {
                    "id": "imported-default-material",
                    "name": "Imported Default Material",
                    "density_kg_m3": 1600.0,
                    "static_friction": 0.5,
                    "dynamic_friction": 0.4,
                    "restitution": 0.1,
                    "simulation_notes": "Fallback material for imported MJCF.",
                    "confidence": "placeholder",
                }
            ],
            "links": parsed["links"],
            "joints": parsed["joints"],
            "actuators": parsed["actuators"],
            "assets": [],
            "electronics": [],
            "sensors": parsed.get("sensors", []),
            "wires": [],
            "collision_primitives": [],
            "robot_description": {"preferred_format": "mjcf", "urdf_path": None, "mjcf_path": mjcf_path, "generated_from_manifest": False},
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
