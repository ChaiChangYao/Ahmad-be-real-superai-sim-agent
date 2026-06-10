from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest


def validate_manifest(manifest: BuildablesPhysicsManifest) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    ids_seen: set[str] = set()
    for collection_name in ["assets", "materials", "links", "joints", "actuators", "electronics", "sensors", "wires", "collision_primitives"]:
        for item in getattr(manifest, collection_name):
            if item.id in ids_seen:
                errors.append(f"Duplicate id detected: {item.id}")
            ids_seen.add(item.id)

    asset_ids = {a.id for a in manifest.assets}
    material_ids = {m.id for m in manifest.materials}
    link_ids = {l.id for l in manifest.links}
    joint_ids = {j.id for j in manifest.joints}
    electronic_ids = {e.id for e in manifest.electronics}

    for link in manifest.links:
        if link.mass_kg <= 0:
            errors.append(f"Link {link.id} has non-positive mass.")
        if link.material_id not in material_ids:
            errors.append(f"Link {link.id} references missing material {link.material_id}.")
        if link.visual_asset_id and link.visual_asset_id not in asset_ids:
            errors.append(f"Link {link.id} references missing visual asset {link.visual_asset_id}.")

    for joint in manifest.joints:
        if joint.parent_link_id not in link_ids or joint.child_link_id not in link_ids:
            errors.append(f"Joint {joint.id} references missing links.")

    for actuator in manifest.actuators:
        if actuator.joint_id not in joint_ids:
            errors.append(f"Actuator {actuator.id} references missing joint.")
        if actuator.max_torque_nm <= 0 or actuator.max_velocity_rad_s <= 0:
            errors.append(f"Actuator {actuator.id} must have positive torque and velocity limits.")

    for sensor in manifest.sensors:
        if sensor.attach_link_id not in link_ids:
            errors.append(f"Sensor {sensor.id} references missing link {sensor.attach_link_id}.")

    for wire in manifest.wires:
        if wire.from_component_id not in electronic_ids or wire.to_component_id not in electronic_ids:
            errors.append(f"Wire {wire.id} endpoint references are invalid.")

    if any(asset.type == "step" for asset in manifest.assets) and not manifest.collision_primitives:
        warnings.append("STEP source exists but no collision primitives were generated.")

    if manifest.actuators and not any("battery" in e.component_profile_id.lower() for e in manifest.electronics):
        warnings.append("Actuators exist but no battery profile is mapped.")

    if manifest.joints and not manifest.actuators:
        warnings.append("Joints exist without actuator mapping.")

    if manifest.assets and not manifest.links:
        warnings.append("Visual assets exist without physics links.")

    if any(getattr(m, "confidence", "placeholder") == "placeholder" for m in manifest.materials):
        warnings.append("Material profiles include placeholder confidence values.")

    warnings.append(
        "This simulation is for pre-procurement robotics behavior validation and rapid iteration. It is not certified final FEA, thermal, electrical, or safety validation."
    )

    must_have = {
        "body": any(l.category == "body" for l in manifest.links),
        "legs": any(l.category == "leg" for l in manifest.links),
        "joints": len(manifest.joints) > 0,
        "actuators": len(manifest.actuators) > 0,
        "battery": any("battery" in e.component_profile_id.lower() for e in manifest.electronics),
        "controller": any("controller" in e.component_profile_id.lower() for e in manifest.electronics),
        "imu": any(s.sensor_type == "imu" for s in manifest.sensors),
    }
    missing = [k for k, present in must_have.items() if not present]
    if missing:
        warnings.append(f"Demo completeness warning: missing expected robot-dog items: {', '.join(missing)}")

    return {"valid": not errors, "errors": errors, "warnings": warnings}
