"""URDF/MJCF inspection with mesh path validation — no Genesis calls."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from app.services.agentic.file_inventory import load_asset_inventory, match_asset_by_path
from app.services.agentic.schemas import MeshReference, RobotDescriptionInspection
from app.services.importers.asset_resolver import normalize_mesh_ref
from app.services.importers.mesh_validation import validate_urdf_meshes
from app.services.importers.mjcf_importer import parse_mjcf
from app.services.importers.urdf_importer import parse_urdf
from app.services.project_store import project_dir

MOVABLE_JOINT_TYPES = {"revolute", "continuous", "prismatic", "planar", "floating"}


def _detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".urdf", ".xacro"}:
        return "urdf"
    if ext == ".mjcf":
        return "mjcf"
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:512].lstrip()
        if head.startswith("<robot"):
            return "urdf"
        if head.startswith("<mujoco"):
            return "mjcf"
    except OSError:
        pass
    return "unknown"


def _extract_mesh_refs_xml(path: Path) -> tuple[list[str], list[dict]]:
    """Direct XML walk for mesh filename attributes."""
    refs: list[str] = []
    details: list[dict] = []
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return refs, details

    tag = root.tag.lower()
    if tag == "robot":
        for link in root.findall("link"):
            for usage_tag, usage in (("visual", "visual"), ("collision", "collision")):
                for geom_parent in link.findall(usage_tag):
                    mesh = geom_parent.find("geometry/mesh")
                    if mesh is not None and mesh.get("filename"):
                        ref = mesh.get("filename", "")
                        refs.append(ref)
                        details.append({"path": ref, "usage": usage, "link": link.get("name", "")})
    elif tag == "mujoco":
        for mesh in root.findall(".//mesh"):
            file_attr = mesh.get("file")
            if file_attr:
                refs.append(file_attr)
                details.append({"path": file_attr, "usage": "visual", "link": ""})

    return list(dict.fromkeys(refs)), details


def _extract_sensors_xml(path: Path) -> list[dict]:
    sensors: list[dict] = []
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return sensors
    for tag in ("sensor", "gazebo", "plugin"):
        for elem in root.findall(f".//{tag}"):
            sensors.append({"tag": tag, "name": elem.get("name", ""), "type": elem.get("type", elem.tag)})
    return sensors


def _try_urdfpy_parse(path: Path) -> dict | None:
    try:
        from urdfpy import URDF

        robot = URDF.load(str(path))
        joints = list(robot.joints)
        links = list(robot.links)
        movable = [j for j in joints if j.joint_type in MOVABLE_JOINT_TYPES]
        fixed = [j for j in joints if j.joint_type == "fixed"]
        has_limits = any(
            j.limit is not None and j.limit.lower is not None and j.limit.upper is not None
            for j in movable
        )
        has_inertial = any(link.inertial is not None for link in links)
        root_link = links[0].name if links else ""
        return {
            "links_count": len(links),
            "joints_count": len(joints),
            "movable_joints_count": len(movable),
            "fixed_joints_count": len(fixed),
            "link_names": [l.name for l in links],
            "joint_names": [j.name for j in joints],
            "root_link": root_link,
            "has_inertial_data": has_inertial,
            "has_joint_limits": has_limits,
        }
    except Exception:
        return None


def _table_to_mesh_references(
    table: list[dict],
    source_file: str,
    assets: list,
) -> list[MeshReference]:
    refs: list[MeshReference] = []
    for row in table:
        raw = str(row.get("urdf_path") or "")
        resolved = str(row.get("resolved_local_path") or "")
        status_str = str(row.get("status") or "missing")
        usage_raw = str(row.get("usage") or "visual")
        if usage_raw == "both" or "collision" in usage_raw and "visual" in usage_raw:
            usage = "both"
        elif "collision" in usage_raw:
            usage = "collision"
        else:
            usage = "visual"

        normalized = normalize_mesh_ref(raw)
        package_name = ""
        if raw.lower().startswith("package://") and "/" in raw[10:]:
            package_name = raw[10:].split("/")[0]

        status = "found" if status_str in {"found", "auto_mapped"} else ("unsupported" if status_str == "unsupported" else "missing")
        matched = match_asset_by_path(assets, resolved) if resolved else None

        refs.append(
            MeshReference(
                source_file=source_file,
                usage=usage,
                raw_path=raw,
                resolved_path=resolved,
                package_name=package_name,
                file_type=str(row.get("file_type") or "unknown"),
                exists=status == "found",
                status=status,
                matched_uploaded_asset_id=matched.id if matched else None,
                action_needed=str(row.get("action_needed") or ""),
            ),
        )
    return refs


def _find_robot_descriptions(project_id: str) -> list[Path]:
    root = project_dir(project_id)
    candidates: list[Path] = []
    for pattern in ("**/*.urdf", "**/*.xacro", "**/*.mjcf"):
        imported = root / "assets" / "imported"
        if imported.is_dir():
            candidates.extend(sorted(imported.glob(pattern)))
        gen = root / "generated" / "robot_description"
        if gen.is_dir():
            candidates.extend(sorted(gen.glob(pattern)))
    seen: set[str] = set()
    unique: list[Path] = []
    for p in candidates:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def inspect_robot_description(project_id: str, desc_path: Path) -> RobotDescriptionInspection:
    """Inspect a single robot description file. Does not call Genesis."""
    fmt = _detect_format(desc_path)
    warnings: list[str] = []
    errors: list[str] = []

    if not desc_path.is_file():
        return RobotDescriptionInspection(
            parsed=False,
            format="unknown",
            source_path=str(desc_path),
            errors=[f"Robot description not found: {desc_path}"],
        )

    assets = load_asset_inventory(project_id)
    project_files = [Path(a.stored_path) for a in assets if Path(a.stored_path).is_file()]

    try:
        if fmt == "mjcf":
            parsed = parse_mjcf(desc_path)
        else:
            parsed = parse_urdf(desc_path)
    except Exception as exc:
        return RobotDescriptionInspection(
            parsed=False,
            format=fmt if fmt != "unknown" else "urdf",
            source_path=str(desc_path),
            errors=[f"Failed to parse robot description: {exc}"],
        )

    xml_refs, xml_details = _extract_mesh_refs_xml(desc_path)
    mesh_refs = list(dict.fromkeys((parsed.get("mesh_references") or []) + xml_refs))
    mesh_details = (parsed.get("mesh_ref_details") or []) + xml_details

    _, missing, table, _ = validate_urdf_meshes(
        desc_path,
        mesh_refs,
        project_files,
        mesh_ref_details=mesh_details,
        auto_map_basenames=True,
    )

    mesh_reference_models = _table_to_mesh_references(table, str(desc_path), assets)

    joints = parsed.get("joints") or []
    links = parsed.get("links") or []
    movable = [j for j in joints if j.get("type") in MOVABLE_JOINT_TYPES]
    fixed = [j for j in joints if j.get("type") == "fixed"]

    urdfpy_data = _try_urdfpy_parse(desc_path) if fmt in {"urdf", "unknown"} else None

    has_collision = any(
        link.get("collision_primitive_ids") or any(r.usage in {"collision", "both"} for r in mesh_reference_models)
        for link in links
    )
    has_visual = any(r.usage in {"visual", "both"} for r in mesh_reference_models)

    sensors = _extract_sensors_xml(desc_path)
    if not sensors:
        parsed_sensors = parsed.get("sensors") or []
        sensors = parsed_sensors
    imu_mesh_links: list[str] = []
    for detail in mesh_details:
        path_ref = str(detail.get("path") or "").lower()
        link_ref = str(detail.get("link") or "")
        if "imu_sensor" in path_ref or "imu_block" in path_ref:
            imu_mesh_links.append(link_ref or "unknown")
            sensors.append(
                {
                    "tag": "visual_mesh",
                    "name": link_ref or "imu_sensor_block",
                    "type": "imu_hardware_block",
                    "mesh": detail.get("path"),
                },
            )
    if not sensors:
        warnings.append(
            "No IMU sensor block or sensor metadata in robot description — "
            "a simulated IMU can still attach to a link, but there is no physical sensor geometry in the URDF.",
        )
    elif imu_mesh_links:
        warnings.append(
            f"IMU hardware mesh found on link(s): {', '.join(dict.fromkeys(imu_mesh_links))}. "
            "Simulated IMU can attach there or to base_link.",
        )

    if missing:
        errors.append(
            f"URDF references {len(mesh_refs)} mesh file(s); {len(missing)} are missing or unsupported.",
        )
        for m in missing[:20]:
            errors.append(f"Missing mesh: {m}")
        if len(missing) > 20:
            errors.append(f"... and {len(missing) - 20} more missing meshes.")

    inspection = RobotDescriptionInspection(
        parsed=True,
        format=fmt if fmt != "unknown" else "urdf",
        source_path=str(desc_path.resolve()),
        links_count=urdfpy_data["links_count"] if urdfpy_data else len(links),
        joints_count=urdfpy_data["joints_count"] if urdfpy_data else len(joints),
        movable_joints_count=urdfpy_data["movable_joints_count"] if urdfpy_data else len(movable),
        fixed_joints_count=urdfpy_data["fixed_joints_count"] if urdfpy_data else len(fixed),
        root_link=urdfpy_data["root_link"] if urdfpy_data else (links[0]["id"] if links else ""),
        link_names=urdfpy_data["link_names"] if urdfpy_data else [l.get("id", "") for l in links],
        joint_names=urdfpy_data["joint_names"] if urdfpy_data else [j.get("id", "") for j in joints],
        mesh_references=mesh_reference_models,
        has_inertial_data=urdfpy_data["has_inertial_data"] if urdfpy_data else any(l.get("mass_kg", 0) > 0 for l in links),
        has_joint_limits=urdfpy_data["has_joint_limits"] if urdfpy_data else any(
            j.get("limit_lower_rad") is not None for j in movable
        ),
        has_collision_geometry=has_collision,
        has_visual_geometry=has_visual,
        detected_sensors=sensors,
        warnings=warnings,
        errors=errors,
    )
    return inspection


def inspect_all_robot_descriptions(project_id: str) -> list[RobotDescriptionInspection]:
    paths = _find_robot_descriptions(project_id)
    if not paths:
        return [
            RobotDescriptionInspection(
                parsed=False,
                warnings=["No URDF or MJCF robot description found in project assets."],
            )
        ]
    return [inspect_robot_description(project_id, p) for p in paths]
