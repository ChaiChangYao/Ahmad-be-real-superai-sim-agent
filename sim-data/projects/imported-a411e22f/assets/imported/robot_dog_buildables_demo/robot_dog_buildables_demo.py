"""Buildables Sim Sandbox industrial quadruped robot dog CAD assembly.

Units: millimeters.
Origin: center of robot stance on ground plane.
XY: ground plane, +X forward, +Y left, +Z up.

The model is intentionally original and unbranded. Parts are separated and
named for later robot-description generation.
"""

from __future__ import annotations

import json
import math
import sys
import types
from dataclasses import dataclass
from pathlib import Path


def _install_optional_ivtk_stubs() -> None:
    if "OCP.IVtkOCC" not in sys.modules:
        ivtk_occ = types.ModuleType("OCP.IVtkOCC")
        ivtk_occ.IVtkOCC_Shape = type("IVtkOCC_Shape", (), {})
        ivtk_occ.IVtkOCC_ShapeMesher = type("IVtkOCC_ShapeMesher", (), {})
        sys.modules["OCP.IVtkOCC"] = ivtk_occ

    if "OCP.IVtkVTK" not in sys.modules:
        ivtk_vtk = types.ModuleType("OCP.IVtkVTK")
        ivtk_vtk.IVtkVTK_ShapeData = type("IVtkVTK_ShapeData", (), {})
        sys.modules["OCP.IVtkVTK"] = ivtk_vtk


_install_optional_ivtk_stubs()

from build123d import Box, Color, Compound, Cylinder, Location, Rotation, Sphere, Torus, export_step, export_stl  # noqa: E402


DISPLAY_NAME = "Buildables Sim Sandbox Robot Dog Demo"

YELLOW = "matte yellow painted composite armor"
BLACK = "black anodized aluminum / carbon composite"
RUBBER = "dark textured rubber"
SENSOR = "dark smoked sensor glass"
PCB = "green PCB and black electronics"
BATTERY = "dark gray battery enclosure"

CAD_COLORS = {
    YELLOW: Color(0.95, 0.67, 0.06, 1.0),
    BLACK: Color(0.02, 0.023, 0.025, 1.0),
    RUBBER: Color(0.006, 0.006, 0.005, 1.0),
    SENSOR: Color(0.015, 0.024, 0.032, 1.0),
    PCB: Color(0.02, 0.28, 0.12, 1.0),
    BATTERY: Color(0.12, 0.12, 0.12, 1.0),
    "black flexible cable": Color(0.0, 0.0, 0.0, 1.0),
    "neutral gray removable payload placeholder": Color(0.42, 0.44, 0.43, 1.0),
}


@dataclass(frozen=True)
class Part:
    name: str
    shape: object
    dimensions: tuple[float, float, float]
    material: str
    visual_only: bool
    movable: bool
    joint_parent: str | None = None
    joint_child: str | None = None


def _axis_rotation(axis: str) -> Rotation:
    if axis == "x":
        return Rotation(0, 90, 0)
    if axis == "y":
        return Rotation(90, 0, 0)
    return Rotation(0, 0, 0)


def cyl(radius: float, depth: float, center: tuple[float, float, float], axis: str = "z"):
    return Cylinder(radius, depth).moved(_axis_rotation(axis)).moved(Location(center))


def box(size: tuple[float, float, float], center: tuple[float, float, float], rotation: Rotation | None = None):
    shape = Box(*size)
    if rotation is not None:
        shape = shape.moved(rotation)
    return shape.moved(Location(center))


def label(shape, name: str):
    shape.label = name
    return shape


def apply_part_style(part: Part):
    part.shape.label = part.name
    if part.material in CAD_COLORS:
        part.shape.color = CAD_COLORS[part.material]
    return part.shape


def beam_between(
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    *,
    width_y: float,
    height: float,
):
    dx = end[0] - start[0]
    dz = end[2] - start[2]
    length = math.hypot(dx, dz)
    angle = -math.degrees(math.atan2(dz, dx))
    center = ((start[0] + end[0]) / 2, start[1], (start[2] + end[2]) / 2)
    return box((length, width_y, height), center, Rotation(0, angle, 0))


def rounded_panel(name: str, size: tuple[float, float, float], center: tuple[float, float, float]):
    sx, sy, sz = size
    x, y, z = center
    r = min(sy, sz) * 0.10
    panel = box((sx, sy - 2 * r, sz), center)
    panel += box((sx, sy, sz - 2 * r), center)
    for yy in (-sy / 2 + r, sy / 2 - r):
        for zz in (-sz / 2 + r, sz / 2 - r):
            panel += cyl(r, sx, (x, y + yy, z + zz), "x")
    return label(panel, name)


def make_torso_parts() -> list[Part]:
    parts: list[Part] = []
    top = rounded_panel("torso_shell_top", (910, 330, 105), (0, 0, 570))
    top += box((800, 260, 18), (0, 0, 635))
    top -= box((210, 26, 12), (0, -78, 643))
    top -= box((210, 26, 12), (0, 78, 643))
    parts.append(Part("torso_shell_top", top, (910, 330, 105), YELLOW, False, False))

    for side, y, rot in (("left", 205, -7), ("right", -205, 7)):
        panel = box((875, 36, 185), (0, y, 505), Rotation(rot, 0, 0))
        panel += box((150, 42, 126), (318, y, 505), Rotation(rot, 0, 0))
        panel += box((150, 42, 126), (-318, y, 505), Rotation(rot, 0, 0))
        for x in (-360, -120, 120, 360):
            panel -= cyl(4.0, 60, (x, y, 545), "y")
        parts.append(Part(f"torso_shell_{side}", label(panel, f"torso_shell_{side}"), (875, 42, 185), YELLOW, False, False))

    front = box((44, 230, 128), (477, 0, 522), Rotation(0, -5, 0))
    front -= cyl(24, 54, (500, -62, 548), "x")
    front -= cyl(24, 54, (500, 62, 548), "x")
    front -= box((56, 104, 12), (500, 0, 500))
    front -= box((56, 148, 14), (500, 0, 585))
    front += cyl(28, 10, (504, 0, 520), "x")
    parts.append(Part("torso_front_sensor_panel", label(front, "torso_front_sensor_panel"), (44, 230, 128), SENSOR, False, False))

    rear = box((36, 238, 124), (-477, 0, 518), Rotation(0, 5, 0))
    rear -= box((18, 168, 78), (-494, 0, 518))
    rear += box((16, 156, 8), (-500, 0, 560))
    parts.append(Part("torso_rear_service_panel", label(rear, "torso_rear_service_panel"), (36, 238, 124), BLACK, False, False))

    tray = box((390, 210, 18), (-80, 0, 444))
    for x in (-245, 85):
        for y in (-83, 83):
            tray += cyl(9, 34, (x, y, 462), "z")
            tray -= cyl(2.8, 46, (x, y, 462), "z")
    parts.append(Part("internal_battery_tray", label(tray, "internal_battery_tray"), (390, 210, 36), BLACK, False, False))

    mount = box((160, 118, 10), (210, 0, 468))
    for x in (150, 270):
        for y in (-42, 42):
            mount += cyl(5, 18, (x, y, 482), "z")
            mount -= cyl(1.8, 26, (x, y, 482), "z")
    parts.append(Part("internal_controller_mount", label(mount, "internal_controller_mount"), (160, 118, 24), BLACK, False, False))

    for side, y in (("left", 82), ("right", -82)):
        rail = box((610, 22, 20), (0, y, 657))
        for x in (-240, -120, 0, 120, 240):
            rail -= box((48, 9, 24), (x, y, 657))
        parts.append(Part(f"top_payload_mount_rail_{side}", label(rail, f"top_payload_mount_rail_{side}"), (610, 22, 20), BLACK, False, False))

    frame = box((900, 42, 34), (0, 166, 416)) + box((900, 42, 34), (0, -166, 416))
    frame += box((58, 320, 36), (345, 0, 416)) + box((58, 320, 36), (-345, 0, 416))
    frame += box((120, 210, 20), (0, 0, 412))
    parts.append(Part("bottom_chassis_frame", label(frame, "bottom_chassis_frame"), (900, 374, 36), BLACK, False, False))

    payload = box((240, 145, 26), (30, 0, 684))
    payload += box((210, 118, 10), (30, 0, 668))
    parts.append(Part("top_payload_block_placeholder", label(payload, "top_payload_block_placeholder"), (240, 145, 42), "neutral gray removable payload placeholder", True, False))
    return parts


def make_internal_parts() -> list[Part]:
    specs = [
        ("battery_block", box((320, 170, 90), (-95, 0, 505)), (320, 170, 90), BATTERY),
        ("controller_board_block", box((120, 90, 8), (214, 0, 492)) + box((32, 22, 18), (182, -25, 505)) + box((42, 28, 15), (235, 24, 504)), (120, 90, 25), PCB),
        ("imu_sensor_block", box((25, 25, 10), (128, 0, 512)), (25, 25, 10), PCB),
        ("front_depth_sensor_block", box((80, 35, 25), (430, 0, 545)), (80, 35, 25), SENSOR),
        ("power_distribution_block", box((80, 50, 25), (76, -72, 495)), (80, 50, 25), PCB),
    ]
    parts = [Part(name, label(shape, name), dims, mat, False, False) for name, shape, dims, mat in specs]

    harness = cyl(7, 312, (0, 0, 480), "x")
    harness += cyl(5, 268, (318, 0, 454), "y")
    harness += cyl(5, 268, (-318, 0, 454), "y")
    for x in (318, -318):
        for y in (-158, 158):
            harness += cyl(4, 80, (x, y, 438), "z")
            harness += Torus(42, 3).moved(Rotation(90, 0, 0)).moved(Location((x, y, 414)))
    parts.append(Part("wire_harness_routes", label(harness, "wire_harness_routes"), (720, 330, 112), "black flexible cable", False, False))
    return parts


def make_leg(prefix: str, hip_x: float, side_y: float, fore_sign: int) -> list[Part]:
    side_sign = 1 if side_y > 0 else -1
    out_y = side_y + side_sign * 48
    hip = (hip_x, out_y, 430)
    knee = (hip_x - fore_sign * 58, out_y, 238)
    ankle = (hip_x + fore_sign * 14, out_y, 72)
    parent = "bottom_chassis_frame"

    parts: list[Part] = []

    yaw = cyl(33, 92, (hip_x, side_y, 430), "x")
    yaw += box((74, 76, 58), (hip_x, side_y, 430))
    yaw -= cyl(10, 112, (hip_x, side_y, 430), "x")
    yaw += cyl(38, 9, (hip_x - 50, side_y, 430), "x") + cyl(38, 9, (hip_x + 50, side_y, 430), "x")
    parts.append(Part(f"{prefix}_hip_yaw_housing", label(yaw, f"{prefix}_hip_yaw_housing"), (110, 80, 76), BLACK, False, True, parent, f"{prefix}_hip_pitch_housing"))

    pitch = cyl(42, 84, hip, "y")
    pitch += box((58, 40, 58), (hip_x, out_y - side_sign * 36, 430))
    pitch -= cyl(9, 104, hip, "y")
    pitch += cyl(48, 8, (hip_x, out_y - side_sign * 46, 430), "y") + cyl(48, 8, (hip_x, out_y + side_sign * 46, 430), "y")
    parts.append(Part(f"{prefix}_hip_pitch_housing", label(pitch, f"{prefix}_hip_pitch_housing"), (74, 104, 96), BLACK, False, True, f"{prefix}_hip_yaw_housing", f"{prefix}_upper_leg_link"))

    shell_center = ((hip[0] + knee[0]) / 2 + fore_sign * 8, out_y, (hip[2] + knee[2]) / 2 + 18)
    shell = beam_between((hip_x + fore_sign * 6, out_y, 390), (knee[0] + fore_sign * 10, out_y, 282), width_y=56, height=58)
    shell += cyl(30, 60, hip, "y")
    shell -= cyl(11, 78, hip, "y")
    parts.append(Part(f"{prefix}_upper_leg_shell", label(shell, f"{prefix}_upper_leg_shell"), (92, 66, 168), YELLOW, True, True, f"{prefix}_hip_pitch_housing", f"{prefix}_upper_leg_link"))

    upper = beam_between(hip, knee, width_y=32, height=28)
    upper += cyl(20, 48, hip, "y") + cyl(20, 48, knee, "y")
    upper -= cyl(7, 62, hip, "y") + cyl(7, 62, knee, "y")
    parts.append(Part(f"{prefix}_upper_leg_link", label(upper, f"{prefix}_upper_leg_link"), (96, 42, 210), BLACK, False, True, f"{prefix}_hip_pitch_housing", f"{prefix}_knee_housing"))

    knee_shape = cyl(34, 72, knee, "y")
    knee_shape += box((54, 50, 44), (knee[0], knee[1], knee[2] + 2))
    knee_shape -= cyl(8, 92, knee, "y")
    knee_shape += cyl(39, 7, (knee[0], knee[1] - side_sign * 40, knee[2]), "y") + cyl(39, 7, (knee[0], knee[1] + side_sign * 40, knee[2]), "y")
    parts.append(Part(f"{prefix}_knee_housing", label(knee_shape, f"{prefix}_knee_housing"), (76, 92, 78), BLACK, False, True, f"{prefix}_upper_leg_link", f"{prefix}_lower_leg_link"))

    lower = beam_between(knee, ankle, width_y=24, height=28)
    lower += beam_between((knee[0] + fore_sign * 18, knee[1], knee[2] - 20), (ankle[0] + fore_sign * 15, ankle[1], ankle[2] + 20), width_y=14, height=16)
    lower += cyl(17, 38, ankle, "y")
    lower -= cyl(5, 50, ankle, "y")
    parts.append(Part(f"{prefix}_lower_leg_link", label(lower, f"{prefix}_lower_leg_link"), (92, 34, 188), BLACK, False, True, f"{prefix}_knee_housing", f"{prefix}_foot"))

    foot = box((132, 68, 28), (ankle[0] + fore_sign * 20, ankle[1], 42), Rotation(0, fore_sign * -4, 0))
    foot += cyl(20, 58, ankle, "y")
    foot -= cyl(5, 72, ankle, "y")
    parts.append(Part(f"{prefix}_foot", label(foot, f"{prefix}_foot"), (132, 68, 58), BLACK, False, True, f"{prefix}_lower_leg_link", f"{prefix}_foot_pad"))

    pad = box((142, 76, 18), (ankle[0] + fore_sign * 22, ankle[1], 19), Rotation(0, fore_sign * -3, 0))
    pad += cyl(18, 138, (ankle[0] - fore_sign * 45, ankle[1], 20), "y")
    pad += cyl(18, 138, (ankle[0] + fore_sign * 88, ankle[1], 20), "y")
    parts.append(Part(f"{prefix}_foot_pad", label(pad, f"{prefix}_foot_pad"), (150, 78, 22), RUBBER, False, True, f"{prefix}_foot", None))

    cable = cyl(5, 78, (hip_x, side_y + side_sign * 36, 438), "y")
    cable += cyl(4, 66, (hip_x - fore_sign * 28, out_y, 376), "z")
    parts.append(Part(f"{prefix}_hip_cable_service_loop", label(cable, f"{prefix}_hip_cable_service_loop"), (62, 84, 76), "black flexible cable", True, True, "wire_harness_routes", f"{prefix}_hip_pitch_housing"))
    return parts


def build_parts() -> list[Part]:
    parts = make_torso_parts()
    parts.extend(make_internal_parts())
    leg_specs = [
        ("front_left", 330, 185, 1),
        ("front_right", 330, -185, 1),
        ("rear_left", -330, 185, -1),
        ("rear_right", -330, -185, -1),
    ]
    for spec in leg_specs:
        parts.extend(make_leg(*spec))
    return parts


def gen_step():
    children = [apply_part_style(part) for part in build_parts()]
    assembly = Compound(children=children)
    assembly.label = "robot_dog_buildables_demo"
    return {"shape": assembly}


def export_auxiliary_files(root: Path) -> None:
    import trimesh

    parts = build_parts()
    mesh_dir = root / "meshes"
    step_dir = root / "step_parts"
    mesh_dir.mkdir(exist_ok=True)
    step_dir.mkdir(exist_ok=True)

    manifest = []
    for idx, part in enumerate(parts, start=1):
        apply_part_style(part)
        step_path = step_dir / f"{part.name}.step"
        stl_path = mesh_dir / f"{part.name}.stl"
        obj_path = mesh_dir / f"{part.name}.obj"
        export_step(part.shape, str(step_path))
        export_stl(part.shape, str(stl_path), tolerance=0.6, angular_tolerance=0.35)
        mesh = trimesh.load_mesh(stl_path, force="mesh")
        mesh.export(obj_path)
        manifest.append(
            {
                "part_id": f"bdog_{idx:03d}",
                "part_name": part.name,
                "parent_assembly": "robot_dog_buildables_demo",
                "approximate_dimensions_mm": {
                    "x": part.dimensions[0],
                    "y": part.dimensions[1],
                    "z": part.dimensions[2],
                },
                "suggested_material": part.material,
                "visual_only": part.visual_only,
                "physics_link": not part.visual_only,
                "movable": part.movable,
                "suggested_joint_parent": part.joint_parent,
                "suggested_joint_child": part.joint_child,
            }
        )

    (root / "robot_dog_parts_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    export_auxiliary_files(Path(__file__).resolve().parent)
