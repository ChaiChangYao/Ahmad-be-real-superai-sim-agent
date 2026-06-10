from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def _mesh_references_api(mesh_table: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in mesh_table:
        status = str(row.get("status") or ("found" if row.get("found") else "missing"))
        out.append(
            {
                "source": row.get("usage") or "visual/collision",
                "path": row.get("urdf_path") or "",
                "resolvedPath": row.get("resolved_local_path") or "",
                "status": status,
                "fileType": row.get("file_type") or "unknown",
                "actionNeeded": row.get("action_needed") or "",
            }
        )
    return out


def build_launch_summary(
    parsed: dict,
    missing_meshes: list[str],
    mesh_table: list[dict],
    *,
    step_uploaded: bool,
    urdf_parsed: bool,
    auto_map_log: list[str] | None = None,
) -> dict:
    links = parsed.get("links", [])
    joints = parsed.get("joints", [])
    mesh_refs = parsed.get("mesh_references", [])
    found_count = sum(1 for row in mesh_table if row.get("status") in {"found", "auto_mapped"})
    missing_count = len(missing_meshes)
    unsupported = sum(1 for row in mesh_table if row.get("status") == "unsupported")
    launchable = urdf_parsed and missing_count == 0 and len(links) > 0

    actions: list[str] = ["upload_robot_zip"]
    if missing_count > 0:
        actions.extend(["upload_missing_meshes", "upload_zip_bundle"])
        if step_uploaded:
            actions.append("generate_from_step")
        if urdf_parsed and len(links) > 0:
            actions.append("preview_skeleton")
    if launchable:
        actions = ["launch_full_model"]

    reason = None
    if not urdf_parsed:
        reason = "No URDF or MJCF robot description was found."
    elif missing_count > 0:
        reason = (
            f"Cannot launch full model because {missing_count} mesh file(s) are missing. "
            "Upload the full meshes/ folder, a robot zip bundle, or generate meshes from STEP."
        )
        if step_uploaded and missing_count > 0:
            reason += " The STEP file may contain geometry, but it must be converted or mapped before Genesis can use the URDF visuals."

    return {
        "urdfParsed": urdf_parsed,
        "links": len(links),
        "joints": len(joints),
        "meshReferencesFound": len(mesh_refs),
        "meshesFound": found_count,
        "meshesMissing": missing_count,
        "unsupportedFormats": unsupported,
        "stepUploaded": step_uploaded,
        "launchable": launchable,
        "launchable_web": launchable,
        "launchable_native": launchable,
        "reason": reason,
        "actions": list(dict.fromkeys(actions)),
        "meshReferences": _mesh_references_api(mesh_table),
        "autoMapLog": auto_map_log or [],
    }


def build_import_validation(parsed: dict, manifest: BuildablesPhysicsManifest, missing_meshes: list[str], resolved_meshes: dict[str, str], mode: str, mesh_table: list[dict] | None = None, auto_map_log: list[str] | None = None) -> dict:
    def asset_type(asset: object) -> str:
        if isinstance(asset, dict):
            return str(asset.get("type", ""))
        return str(getattr(asset, "type", ""))

    joints = parsed.get("joints", [])
    links = parsed.get("links", [])
    movable = [joint for joint in joints if joint.get("type") in {"revolute", "continuous", "prismatic"}]
    missing_mass = [link["id"] for link in links if float(link.get("mass_kg", 0.0)) <= 0.0]
    missing_joint_limits = [joint["id"] for joint in movable if joint.get("limit_lower_rad") is None or joint.get("limit_upper_rad") is None]
    collision_missing = [link["id"] for link in links if not link.get("collision_primitive_ids")]
    has_control = bool(manifest.controls.get("control_script_path") or manifest.actuators)
    readiness = {
        "passive_simulation": len(links) > 0 and len(missing_meshes) == 0,
        "joint_simulation": len(movable) > 0,
        "controlled_motion": has_control and len(movable) > 0,
    }
    if mode == "cad_geometry_only":
        readiness["controlled_motion"] = False

    step_uploaded = any(asset_type(asset) == "step" for asset in manifest.assets)
    urdf_parsed = bool(parsed.get("urdf_path") or parsed.get("mjcf_path"))
    table = mesh_table or []

    user_messages: list[dict[str, str]] = []
    if not parsed.get("urdf_path") and not parsed.get("mjcf_path"):
        user_messages.append(
            {
                "severity": "error",
                "issue": "No robot description found",
                "fix": "Upload a URDF or MJCF file in the motion box. STEP files alone cannot drive joint motion.",
            }
        )
    elif step_uploaded and missing_meshes:
        user_messages.append(
            {
                "severity": "error",
                "issue": "URDF references STL/OBJ mesh files that were not uploaded",
                "fix": (
                    "The STEP file may contain geometry, but it must be converted or mapped before Genesis can use the URDF visuals. "
                    "Use 'Generate missing meshes from STEP', upload the meshes/ folder, or upload a zip bundle."
                ),
            }
        )
    for mesh_ref in missing_meshes[:12]:
        user_messages.append(
            {
                "severity": "error",
                "issue": f"Missing mesh file referenced by URDF: {mesh_ref}",
                "fix": "Upload the mesh folder preserving paths (e.g. meshes/link.stl), or upload a zip that includes the URDF and all mesh files.",
            }
        )
    if missing_joint_limits:
        user_messages.append(
            {
                "severity": "warning",
                "issue": f"Joints missing limits: {', '.join(missing_joint_limits[:5])}",
                "fix": "Add <limit lower=\"…\" upper=\"…\"/> to each movable joint in the URDF.",
            }
        )
    if missing_mass:
        user_messages.append(
            {
                "severity": "warning",
                "issue": f"Links missing mass: {', '.join(missing_mass[:5])}",
                "fix": "Add inertial blocks (<inertial><mass value=\"…\"/></inertial>) or collision geometry with density.",
            }
        )
    if mode == "cad_geometry_only":
        user_messages.append(
            {
                "severity": "info",
                "issue": "CAD-only import",
                "fix": "STEP/STL geometry is stored for reference. Import a URDF/MJCF with joints to run motion in Genesis.",
            }
        )
    elif not manifest.controls.get("control_script_path") and not manifest.actuators:
        user_messages.append(
            {
                "severity": "info",
                "issue": "No control script or actuators",
                "fix": "Passive gravity and joint tests still work. Add a .py control script or actuators in the manifest for commanded motion.",
            }
        )

    launch_summary = build_launch_summary(
        parsed,
        missing_meshes,
        table,
        step_uploaded=step_uploaded,
        urdf_parsed=urdf_parsed,
        auto_map_log=auto_map_log,
    )

    return {
        "launch_summary": launch_summary,
        "robot_description": {
            "urdf_found": bool(parsed.get("urdf_path")),
            "mjcf_found": bool(parsed.get("mjcf_path")),
            "links_count": len(links),
            "joints_count": len(joints),
            "movable_joints_count": len(movable),
            "fixed_joints_count": len(joints) - len(movable),
        },
        "geometry": {
            "visual_mesh_references": len(parsed.get("mesh_references", [])),
            "resolved_meshes": resolved_meshes,
            "missing_mesh_references": missing_meshes,
            "mesh_table": table,
            "step_source_found": step_uploaded,
            "step_note": (
                "STEP is stored as an optional asset and does not replace missing URDF STL/OBJ mesh files. "
                "Convert or map STEP bodies to URDF mesh paths before full launch."
            ),
            "unit_scale": "meters",
        },
        "physics_metadata": {
            "links_with_mass": len(links) - len(missing_mass),
            "links_missing_mass": missing_mass,
            "links_with_inertia": len(links),  # imported defaults if absent
            "links_missing_inertia": [],
            "materials_found": len(manifest.materials),
            "collision_geometry_missing": collision_missing,
        },
        "motion": {
            "revolute_joints": len([joint for joint in joints if joint.get("type") == "revolute"]),
            "prismatic_joints": len([joint for joint in joints if joint.get("type") == "prismatic"]),
            "continuous_joints": len([joint for joint in joints if joint.get("type") == "continuous"]),
            "joint_limits_missing": missing_joint_limits,
            "actuators_found": len(manifest.actuators),
        },
        "sensors_control": {
            "sensors_found": len(manifest.sensors),
            "control_script_found": bool(manifest.controls.get("control_script_path")),
            "message": "No control script found. You can still run passive gravity, joint sweep, and collision tests." if not manifest.controls.get("control_script_path") else "Control script detected.",
            "enabled_features": [],
            "requirements": [],
        },
        "simulation_readiness": {
            "status": "geometry_only_not_motion_ready" if mode == "cad_geometry_only" else "mechanism_imported",
            "passive": readiness["passive_simulation"],
            "joint": readiness["joint_simulation"],
            "controlled": readiness["controlled_motion"],
            "missing_metadata": not all(readiness.values()),
        },
        "user_messages": user_messages,
    }


def metadata_status_from_validation(validation: dict) -> dict:
    return {
        "missing_mass": len(validation["physics_metadata"]["links_missing_mass"]) > 0,
        "missing_material": validation["physics_metadata"]["materials_found"] == 0,
        "missing_joint": validation["robot_description"]["joints_count"] == 0,
        "missing_actuator": validation["motion"]["actuators_found"] == 0,
        "missing_sensor": validation["sensors_control"]["sensors_found"] == 0,
        "missing_collision_mesh": len(validation["geometry"]["missing_mesh_references"]) > 0,
        "missing_control_script": not validation["sensors_control"]["control_script_found"],
        "missing_environment": False,
    }


_SENSOR_DEFAULTS: dict[str, dict[str, str | float]] = {
    "imu": {
        "attach_link": "base_link",
        "sample_rate_hz": 100.0,
        "origin": "0,0,0",
    },
    "temperature_grid": {
        "attach_link": "base_link",
        "sample_rate_hz": 10.0,
        "grid_size": "8x8",
    },
    "depth_camera": {
        "attach_link": "base_link",
        "sample_rate_hz": 30.0,
        "fov_deg": 60.0,
        "resolution": "640x480",
    },
    "lidar": {
        "attach_link": "base_link",
        "sample_rate_hz": 10.0,
        "max_range_m": 30.0,
    },
    "contact_force": {
        "attach_link": "base_link",
        "sample_rate_hz": 100.0,
    },
}


def validate_sensor_feature_requirements(
    manifest: BuildablesPhysicsManifest,
    enabled_features: list[str] | None = None,
) -> dict[str, object]:
    """Structured checklist when user enables sensor features on imported projects."""
    enabled = [f.strip().lower() for f in (enabled_features or []) if f.strip()]
    errors: list[str] = []
    requirements: list[dict[str, object]] = []
    links = {link.id for link in manifest.links}

    for feature in enabled:
        defaults = _SENSOR_DEFAULTS.get(feature)
        if defaults is None:
            requirements.append(
                {
                    "feature": feature,
                    "status": "unsupported",
                    "message": f"Sensor feature '{feature}' is not yet supported in imported projects.",
                }
            )
            continue

        attach = str(defaults.get("attach_link") or "base_link")
        attach_ok = attach in links or len(links) == 0
        req = {
            "feature": feature,
            "attach_link": attach,
            "sample_rate_hz": defaults.get("sample_rate_hz"),
            "status": "ok" if attach_ok else "missing",
            "message": (
                f"Attach {feature.upper()} to link '{attach}' (default)."
                if attach_ok
                else f"Link '{attach}' not found for {feature.upper()} attachment."
            ),
        }
        requirements.append(req)
        if not attach_ok:
            errors.append(req["message"])

    return {
        "enabled_features": enabled,
        "requirements": requirements,
        "errors": errors,
        "can_launch_with_sensors": len(errors) == 0,
    }
