"""URDF/Xacro generator for the Buildables Sim Sandbox robot dog.

Design ledger summary:
- Target consumer: Genesis via gs.morphs.URDF, plus CAD Explorer review.
- Units: meters, kilograms, radians, seconds.
- Frame convention: +X forward, +Y left, +Z up, matching the CAD generator.
- Base: `base_link` is the torso floating base. There is no fixed world joint.
- Kinematics: 12 actuated revolute leg joints, 3 per leg.
- Joint axes: hip ab/ad about +X, hip pitch about +Y, knee pitch about +Y.
- Visual geometry: detailed CAD OBJ meshes exported in millimeters, scaled by
  0.001 and offset into each link frame.
- Collision geometry: simplified local STL boxes/cylinders in meters.
- Inertials: coarse primitive approximations suitable for early simulation,
  not measured mass properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi
from pathlib import Path
import xml.etree.ElementTree as ET


ROBOT_NAME = "robot_dog_buildables_demo"
VISUAL_MESH_DIR = "meshes"
COLLISION_MESH_DIR = "meshes/collision"
MM_TO_M = "0.001 0.001 0.001"

BASE_FRAME_M = (0.0, 0.0, 0.520)

MATERIALS = {
    "armor_yellow": "0.95 0.67 0.06 1",
    "anodized_black": "0.02 0.023 0.025 1",
    "rubber_black": "0.006 0.006 0.005 1",
    "sensor_glass": "0.015 0.024 0.032 1",
    "pcb_green": "0.02 0.28 0.12 1",
    "battery_gray": "0.12 0.12 0.12 1",
    "payload_gray": "0.42 0.44 0.43 1",
}

JOINT_DAMPING = 0.08
JOINT_FRICTION = 0.02


@dataclass(frozen=True)
class VisualMesh:
    filename: str
    material: str


@dataclass(frozen=True)
class CollisionMesh:
    filename: str
    kind: str
    size: tuple[float, float, float] | None = None
    radius: float | None = None
    length: float | None = None
    axis: str = "z"
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class LinkSpec:
    name: str
    frame_world_m: tuple[float, float, float]
    visual_meshes: tuple[VisualMesh, ...]
    collision: CollisionMesh | None
    mass_kg: float | None
    inertial_size_m: tuple[float, float, float] | None = None
    inertial_origin_m: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class LegSpec:
    prefix: str
    hip_x_m: float
    side_y_m: float
    fore_sign: int

    @property
    def side_sign(self) -> int:
        return 1 if self.side_y_m > 0 else -1

    @property
    def hip_abd_world_m(self) -> tuple[float, float, float]:
        return (self.hip_x_m, self.side_y_m, 0.430)

    @property
    def hip_pitch_world_m(self) -> tuple[float, float, float]:
        return (self.hip_x_m, self.side_y_m + self.side_sign * 0.048, 0.430)

    @property
    def knee_world_m(self) -> tuple[float, float, float]:
        return (self.hip_x_m - self.fore_sign * 0.058, self.side_y_m + self.side_sign * 0.048, 0.238)

    @property
    def ankle_world_m(self) -> tuple[float, float, float]:
        return (self.hip_x_m + self.fore_sign * 0.014, self.side_y_m + self.side_sign * 0.048, 0.072)


LEGS = (
    LegSpec("front_left", 0.330, 0.185, 1),
    LegSpec("front_right", 0.330, -0.185, 1),
    LegSpec("rear_left", -0.330, 0.185, -1),
    LegSpec("rear_right", -0.330, -0.185, -1),
)


def fmt(values: tuple[float, float, float]) -> str:
    return " ".join(f"{value:.6g}" for value in values)


def sub(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def neg(a: tuple[float, float, float]) -> tuple[float, float, float]:
    return (-a[0], -a[1], -a[2])


def add_origin(parent: ET.Element, xyz=(0.0, 0.0, 0.0), rpy=(0.0, 0.0, 0.0)) -> None:
    ET.SubElement(parent, "origin", {"xyz": fmt(xyz), "rpy": fmt(rpy)})


def inertia_box(mass: float, size: tuple[float, float, float]) -> dict[str, str]:
    sx, sy, sz = size
    return {
        "ixx": f"{mass * (sy * sy + sz * sz) / 12:.8g}",
        "ixy": "0",
        "ixz": "0",
        "iyy": f"{mass * (sx * sx + sz * sz) / 12:.8g}",
        "iyz": "0",
        "izz": f"{mass * (sx * sx + sy * sy) / 12:.8g}",
    }


def add_inertial(link: ET.Element, spec: LinkSpec) -> None:
    if spec.mass_kg is None or spec.inertial_size_m is None:
        return
    inertial = ET.SubElement(link, "inertial")
    add_origin(inertial, spec.inertial_origin_m)
    ET.SubElement(inertial, "mass", {"value": f"{spec.mass_kg:.6g}"})
    ET.SubElement(inertial, "inertia", inertia_box(spec.mass_kg, spec.inertial_size_m))


def add_visuals(link: ET.Element, spec: LinkSpec) -> None:
    visual_origin = neg(spec.frame_world_m)
    for visual_mesh in spec.visual_meshes:
        visual = ET.SubElement(link, "visual", {"name": f"{visual_mesh.filename}_visual"})
        add_origin(visual, visual_origin)
        geometry = ET.SubElement(visual, "geometry")
        ET.SubElement(
            geometry,
            "mesh",
            {
                "filename": f"{VISUAL_MESH_DIR}/{visual_mesh.filename}.stl",
                "scale": MM_TO_M,
            },
        )
        ET.SubElement(visual, "material", {"name": visual_mesh.material})


def add_collision(link: ET.Element, spec: LinkSpec) -> None:
    if spec.collision is None:
        return
    collision = ET.SubElement(link, "collision", {"name": f"{spec.name}_collision"})
    add_origin(collision)
    geometry = ET.SubElement(collision, "geometry")
    ET.SubElement(geometry, "mesh", {"filename": f"{COLLISION_MESH_DIR}/{spec.collision.filename}.stl"})


def add_link(robot: ET.Element, spec: LinkSpec) -> None:
    link = ET.SubElement(robot, "link", {"name": spec.name})
    add_inertial(link, spec)
    add_visuals(link, spec)
    add_collision(link, spec)


def add_revolute_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float],
    axis_xyz: tuple[float, float, float],
    lower: float,
    upper: float,
    effort: float,
    velocity: float,
) -> None:
    joint = ET.SubElement(robot, "joint", {"name": name, "type": "revolute"})
    ET.SubElement(joint, "parent", {"link": parent})
    ET.SubElement(joint, "child", {"link": child})
    add_origin(joint, origin_xyz)
    ET.SubElement(joint, "axis", {"xyz": fmt(axis_xyz)})
    ET.SubElement(
        joint,
        "limit",
        {
            "lower": f"{lower:.8g}",
            "upper": f"{upper:.8g}",
            "effort": f"{effort:.6g}",
            "velocity": f"{velocity:.6g}",
        },
    )
    ET.SubElement(joint, "dynamics", {"damping": f"{JOINT_DAMPING:.6g}", "friction": f"{JOINT_FRICTION:.6g}"})


def add_fixed_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> None:
    joint = ET.SubElement(robot, "joint", {"name": name, "type": "fixed"})
    ET.SubElement(joint, "parent", {"link": parent})
    ET.SubElement(joint, "child", {"link": child})
    add_origin(joint, origin_xyz)


def body_link_specs() -> list[LinkSpec]:
    base_visuals = (
        VisualMesh("torso_shell_top", "armor_yellow"),
        VisualMesh("torso_shell_left", "armor_yellow"),
        VisualMesh("torso_shell_right", "armor_yellow"),
        VisualMesh("bottom_chassis_frame", "anodized_black"),
    )
    specs = [
        LinkSpec(
            "base_link",
            BASE_FRAME_M,
            base_visuals,
            CollisionMesh("base_link_collision", "box", size=(0.92, 0.36, 0.22), center=(0.0, 0.0, 0.0)),
            15.0,
            (0.92, 0.36, 0.22),
            (0.0, 0.0, 0.0),
        ),
        LinkSpec("front_sensor_panel_link", BASE_FRAME_M, (VisualMesh("torso_front_sensor_panel", "sensor_glass"), VisualMesh("front_depth_sensor_block", "sensor_glass")), CollisionMesh("front_sensor_panel_collision", "box", size=(0.06, 0.24, 0.13), center=(0.477, 0.0, 0.522 - BASE_FRAME_M[2])), 0.35, (0.06, 0.24, 0.13), (0.477, 0.0, 0.522 - BASE_FRAME_M[2])),
        LinkSpec("rear_service_panel_link", BASE_FRAME_M, (VisualMesh("torso_rear_service_panel", "anodized_black"),), CollisionMesh("rear_service_panel_collision", "box", size=(0.05, 0.24, 0.13), center=(-0.477, 0.0, 0.518 - BASE_FRAME_M[2])), 0.28, (0.05, 0.24, 0.13), (-0.477, 0.0, 0.518 - BASE_FRAME_M[2])),
        LinkSpec("internal_electronics_link", BASE_FRAME_M, (VisualMesh("internal_battery_tray", "anodized_black"), VisualMesh("internal_controller_mount", "anodized_black"), VisualMesh("battery_block", "battery_gray"), VisualMesh("controller_board_block", "pcb_green"), VisualMesh("imu_sensor_block", "pcb_green"), VisualMesh("power_distribution_block", "pcb_green"), VisualMesh("wire_harness_routes", "anodized_black")), CollisionMesh("internal_electronics_collision", "box", size=(0.43, 0.22, 0.12), center=(-0.04, 0.0, 0.49 - BASE_FRAME_M[2])), 2.9, (0.43, 0.22, 0.12), (-0.04, 0.0, 0.49 - BASE_FRAME_M[2])),
        LinkSpec("payload_mount_link", BASE_FRAME_M, (VisualMesh("top_payload_mount_rail_left", "anodized_black"), VisualMesh("top_payload_mount_rail_right", "anodized_black"), VisualMesh("top_payload_block_placeholder", "payload_gray")), CollisionMesh("payload_mount_collision", "box", size=(0.61, 0.18, 0.07), center=(0.03, 0.0, 0.675 - BASE_FRAME_M[2])), 1.1, (0.61, 0.18, 0.07), (0.03, 0.0, 0.675 - BASE_FRAME_M[2])),
    ]
    return specs


def leg_link_specs(leg: LegSpec) -> list[LinkSpec]:
    p = leg.prefix
    hip_abd = leg.hip_abd_world_m
    hip_pitch = leg.hip_pitch_world_m
    knee = leg.knee_world_m
    ankle = leg.ankle_world_m
    upper_span = sub(knee, hip_pitch)
    lower_span = sub(ankle, knee)
    return [
        LinkSpec(
            f"{p}_hip_abduction_link",
            hip_abd,
            (VisualMesh(f"{p}_hip_yaw_housing", "anodized_black"),),
            CollisionMesh(f"{p}_hip_abduction_collision", "cylinder", radius=0.045, length=0.11, axis="x"),
            1.25,
            (0.11, 0.08, 0.08),
        ),
        LinkSpec(
            f"{p}_hip_pitch_housing_link",
            hip_pitch,
            (VisualMesh(f"{p}_hip_pitch_housing", "anodized_black"), VisualMesh(f"{p}_hip_cable_service_loop", "anodized_black")),
            CollisionMesh(f"{p}_hip_pitch_housing_collision", "cylinder", radius=0.05, length=0.10, axis="y"),
            0.65,
            (0.08, 0.10, 0.10),
        ),
        LinkSpec(
            f"{p}_upper_leg_link",
            hip_pitch,
            (VisualMesh(f"{p}_upper_leg_link", "anodized_black"), VisualMesh(f"{p}_upper_leg_shell", "armor_yellow")),
            CollisionMesh(f"{p}_upper_leg_collision", "box", size=(0.13, 0.07, 0.22), center=tuple(v * 0.5 for v in upper_span)),
            1.15,
            (0.13, 0.07, 0.22),
            tuple(v * 0.5 for v in upper_span),
        ),
        LinkSpec(
            f"{p}_knee_housing_link",
            knee,
            (VisualMesh(f"{p}_knee_housing", "anodized_black"),),
            CollisionMesh(f"{p}_knee_housing_collision", "cylinder", radius=0.042, length=0.09, axis="y"),
            0.55,
            (0.08, 0.09, 0.08),
        ),
        LinkSpec(
            f"{p}_lower_leg_link",
            knee,
            (VisualMesh(f"{p}_lower_leg_link", "anodized_black"),),
            CollisionMesh(f"{p}_lower_leg_collision", "box", size=(0.10, 0.045, 0.20), center=tuple(v * 0.5 for v in lower_span)),
            0.75,
            (0.10, 0.045, 0.20),
            tuple(v * 0.5 for v in lower_span),
        ),
        LinkSpec(
            f"{p}_foot_link",
            ankle,
            (VisualMesh(f"{p}_foot", "anodized_black"), VisualMesh(f"{p}_foot_pad", "rubber_black")),
            CollisionMesh(f"{p}_foot_collision", "box", size=(0.16, 0.08, 0.04), center=(leg.fore_sign * 0.025, 0.0, -0.045)),
            0.32,
            (0.16, 0.08, 0.04),
            (leg.fore_sign * 0.025, 0.0, -0.045),
        ),
    ]


def all_link_specs() -> list[LinkSpec]:
    specs = body_link_specs()
    for leg in LEGS:
        specs.extend(leg_link_specs(leg))
    return specs


def add_leg_joints(robot: ET.Element, leg: LegSpec) -> None:
    p = leg.prefix
    hip_abd = leg.hip_abd_world_m
    hip_pitch = leg.hip_pitch_world_m
    knee = leg.knee_world_m
    ankle = leg.ankle_world_m

    add_revolute_joint(
        robot,
        name=f"{p}_hip_abduction_joint",
        parent="base_link",
        child=f"{p}_hip_abduction_link",
        origin_xyz=sub(hip_abd, BASE_FRAME_M),
        axis_xyz=(1.0, 0.0, 0.0),
        lower=-0.65,
        upper=0.65,
        effort=70.0,
        velocity=7.0,
    )
    add_fixed_joint(
        robot,
        name=f"{p}_hip_pitch_housing_fixed",
        parent=f"{p}_hip_abduction_link",
        child=f"{p}_hip_pitch_housing_link",
        origin_xyz=sub(hip_pitch, hip_abd),
    )
    add_revolute_joint(
        robot,
        name=f"{p}_hip_pitch_joint",
        parent=f"{p}_hip_abduction_link",
        child=f"{p}_upper_leg_link",
        origin_xyz=sub(hip_pitch, hip_abd),
        axis_xyz=(0.0, 1.0, 0.0),
        lower=-1.30,
        upper=1.35,
        effort=85.0,
        velocity=8.0,
    )
    add_fixed_joint(
        robot,
        name=f"{p}_knee_housing_fixed",
        parent=f"{p}_upper_leg_link",
        child=f"{p}_knee_housing_link",
        origin_xyz=sub(knee, hip_pitch),
    )
    add_revolute_joint(
        robot,
        name=f"{p}_knee_pitch_joint",
        parent=f"{p}_upper_leg_link",
        child=f"{p}_lower_leg_link",
        origin_xyz=sub(knee, hip_pitch),
        axis_xyz=(0.0, 1.0, 0.0),
        lower=-2.65,
        upper=-0.25,
        effort=90.0,
        velocity=8.0,
    )
    add_fixed_joint(
        robot,
        name=f"{p}_foot_fixed",
        parent=f"{p}_lower_leg_link",
        child=f"{p}_foot_link",
        origin_xyz=sub(ankle, knee),
    )


def add_fixed_body_joints(robot: ET.Element) -> None:
    for child in ("front_sensor_panel_link", "rear_service_panel_link", "internal_electronics_link", "payload_mount_link"):
        add_fixed_joint(robot, name=f"{child}_fixed", parent="base_link", child=child)


def add_ros2_control_and_transmissions(robot: ET.Element, joint_names: list[str]) -> None:
    for joint_name in joint_names:
        transmission = ET.SubElement(robot, "transmission", {"name": f"{joint_name}_transmission"})
        type_element = ET.SubElement(transmission, "type")
        type_element.text = "transmission_interface/SimpleTransmission"
        joint = ET.SubElement(transmission, "joint", {"name": joint_name})
        hardware_interface = ET.SubElement(joint, "hardwareInterface")
        hardware_interface.text = "hardware_interface/EffortJointInterface"
        actuator = ET.SubElement(transmission, "actuator", {"name": f"{joint_name}_motor"})
        actuator_interface = ET.SubElement(actuator, "hardwareInterface")
        actuator_interface.text = "hardware_interface/EffortJointInterface"
        reduction = ET.SubElement(actuator, "mechanicalReduction")
        reduction.text = "1"

    control = ET.SubElement(robot, "ros2_control", {"name": f"{ROBOT_NAME}_system", "type": "system"})
    hardware = ET.SubElement(control, "hardware")
    plugin = ET.SubElement(hardware, "plugin")
    plugin.text = "mock_components/GenericSystem"
    for joint_name in joint_names:
        joint = ET.SubElement(control, "joint", {"name": joint_name})
        ET.SubElement(joint, "command_interface", {"name": "position"})
        ET.SubElement(joint, "command_interface", {"name": "velocity"})
        ET.SubElement(joint, "command_interface", {"name": "effort"})
        ET.SubElement(joint, "state_interface", {"name": "position"})
        ET.SubElement(joint, "state_interface", {"name": "velocity"})


def gen_urdf():
    robot = ET.Element("robot", {"name": ROBOT_NAME})
    for name, rgba in MATERIALS.items():
        material = ET.SubElement(robot, "material", {"name": name})
        ET.SubElement(material, "color", {"rgba": rgba})

    for spec in all_link_specs():
        add_link(robot, spec)

    add_fixed_body_joints(robot)
    controlled_joints: list[str] = []
    for leg in LEGS:
        add_leg_joints(robot, leg)
        controlled_joints.extend(
            [
                f"{leg.prefix}_hip_abduction_joint",
                f"{leg.prefix}_hip_pitch_joint",
                f"{leg.prefix}_knee_pitch_joint",
            ]
        )

    add_ros2_control_and_transmissions(robot, controlled_joints)
    return robot


def _write_collision_meshes(root: Path) -> None:
    import trimesh

    collision_dir = root / "meshes" / "collision"
    collision_dir.mkdir(parents=True, exist_ok=True)
    for spec in all_link_specs():
        if spec.collision is None:
            continue
        collision = spec.collision
        if collision.kind == "box":
            if collision.size is None:
                raise ValueError(f"{collision.filename} missing box size")
            mesh = trimesh.creation.box(extents=collision.size)
            mesh.apply_translation(collision.center)
        elif collision.kind == "cylinder":
            if collision.radius is None or collision.length is None:
                raise ValueError(f"{collision.filename} missing cylinder dimensions")
            transform = trimesh.transformations.identity_matrix()
            if collision.axis == "x":
                transform = trimesh.transformations.rotation_matrix(pi / 2, (0, 1, 0))
            elif collision.axis == "y":
                transform = trimesh.transformations.rotation_matrix(pi / 2, (1, 0, 0))
            mesh = trimesh.creation.cylinder(radius=collision.radius, height=collision.length, sections=24, transform=transform)
            mesh.apply_translation(collision.center)
        else:
            raise ValueError(f"Unsupported collision mesh kind: {collision.kind}")
        mesh.export(collision_dir / f"{collision.filename}.stl")


def _write_xacro(root: Path) -> None:
    robot = gen_urdf()
    robot.set("xmlns:xacro", "http://www.ros.org/wiki/xacro")
    ET.indent(ET.ElementTree(robot), space="  ")
    xacro_path = root / "robot_dog_buildables_demo.xacro"
    xacro_path.write_text(
        "<?xml version='1.0'?>\n" + ET.tostring(robot, encoding="unicode"),
        encoding="utf-8",
    )


if __name__ == "__main__":
    model_root = Path(__file__).resolve().parent
    _write_collision_meshes(model_root)
    _write_xacro(model_root)
